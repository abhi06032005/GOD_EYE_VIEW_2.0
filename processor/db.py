"""
SentinelAI Persistent Storage Layer
Supports PostgreSQL + PostGIS (primary) and SQLite (embedded fallback for standalone/eval).
"""
import os
import json
import sqlite3
import asyncio
import time
from typing import Dict, Any, List, Optional

DB_TYPE = os.getenv("DB_TYPE", "auto") # "postgres", "sqlite", or "auto"
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = int(os.getenv("POSTGRES_PORT", 5432))
PG_DB = os.getenv("POSTGRES_DB", "sentinel_db")
PG_USER = os.getenv("POSTGRES_USER", "sentinel")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "sentinel_secret")

SQLITE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sentinel.db")

class SentinelDB:
    def __init__(self):
        self.is_pg = False
        self.pg_pool = None
        self.sqlite_conn = None
        self._lock = asyncio.Lock()
        self._insert_count = 0

    async def initialize(self):
        # Try connecting to PostgreSQL if requested or auto
        if DB_TYPE in ("postgres", "auto"):
            try:
                import asyncpg
                self.pg_pool = await asyncio.wait_for(
                    asyncpg.create_pool(
                        host=PG_HOST,
                        port=PG_PORT,
                        database=PG_DB,
                        user=PG_USER,
                        password=PG_PASSWORD,
                        min_size=1,
                        max_size=10
                    ),
                    timeout=2.0
                )
                self.is_pg = True
                print(f"[SentinelDB] Connected to PostgreSQL at {PG_HOST}:{PG_PORT}/{PG_DB}")
                return
            except Exception as e:
                if DB_TYPE == "postgres":
                    raise ConnectionError(f"PostgreSQL connection failed: {e}")
                # Fallback to SQLite in auto mode
                print(f"[SentinelDB] PostgreSQL not reachable ({e}). Initializing SQLite fallback at {SQLITE_PATH}")

        # Initialize SQLite fallback
        self.is_pg = False
        os.makedirs(os.path.dirname(SQLITE_PATH), exist_ok=True)
        self.sqlite_conn = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
        self.sqlite_conn.row_factory = sqlite3.Row
        self._init_sqlite_schema()

    def _init_sqlite_schema(self):
        cur = self.sqlite_conn.cursor()
        cur.executescript("""
        PRAGMA journal_mode = WAL;
        PRAGMA synchronous = NORMAL;
        PRAGMA temp_store = MEMORY;
        PRAGMA cache_size = -64000;
        CREATE TABLE IF NOT EXISTS flights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id TEXT NOT NULL,
            source TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            alt REAL DEFAULT 0.0,
            speed REAL DEFAULT 0.0,
            heading REAL DEFAULT 0.0,
            ts REAL NOT NULL,
            meta TEXT DEFAULT '{}'
        );
        CREATE INDEX IF NOT EXISTS idx_flights_ts ON flights(ts DESC);
        CREATE INDEX IF NOT EXISTS idx_flights_entity ON flights(entity_id);

        CREATE TABLE IF NOT EXISTS ships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id TEXT NOT NULL,
            source TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            alt REAL DEFAULT 0.0,
            speed REAL DEFAULT 0.0,
            heading REAL DEFAULT 0.0,
            ts REAL NOT NULL,
            meta TEXT DEFAULT '{}'
        );
        CREATE INDEX IF NOT EXISTS idx_ships_ts ON ships(ts DESC);
        CREATE INDEX IF NOT EXISTS idx_ships_entity ON ships(entity_id);

        CREATE TABLE IF NOT EXISTS quakes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id TEXT NOT NULL,
            source TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            alt REAL DEFAULT 0.0,
            speed REAL DEFAULT 0.0,
            heading REAL DEFAULT 0.0,
            ts REAL NOT NULL,
            meta TEXT DEFAULT '{}'
        );
        CREATE INDEX IF NOT EXISTS idx_quakes_ts ON quakes(ts DESC);

        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id TEXT NOT NULL,
            source TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            class_counts TEXT DEFAULT '{}',
            bboxes TEXT DEFAULT '[]',
            ts REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_detections_ts ON detections(ts DESC);

        CREATE TABLE IF NOT EXISTS anomalies (
            id TEXT PRIMARY KEY,
            entity_id TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            rule_name TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            alt REAL DEFAULT 0.0,
            ts REAL NOT NULL,
            meta TEXT DEFAULT '{}'
        );
        CREATE INDEX IF NOT EXISTS idx_anomalies_ts ON anomalies(ts DESC);

        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            severity TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            ts REAL NOT NULL,
            meta TEXT DEFAULT '{}'
        );
        CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts DESC);
        """)
        self.sqlite_conn.commit()

    async def insert_telemetry(self, table: str, rec: Dict[str, Any]):
        meta_json = json.dumps(rec.get("meta", {}))
        if self.is_pg:
            query = f"""
                INSERT INTO {table} (entity_id, source, lat, lon, alt, speed, heading, ts, meta, geom)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, ST_SetSRID(ST_MakePoint($4, $3), 4326))
            """
            async with self.pg_pool.acquire() as conn:
                await conn.execute(
                    query,
                    rec["entity_id"],
                    rec["source"],
                    rec["lat"],
                    rec["lon"],
                    rec.get("alt", 0.0),
                    rec.get("speed", 0.0),
                    rec.get("heading", 0.0),
                    rec["ts"],
                    meta_json
                )
            async with self._lock:
                cur = self.sqlite_conn.cursor()
                cur.execute(
                    f"INSERT INTO {table} (entity_id, source, lat, lon, alt, speed, heading, ts, meta) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (rec["entity_id"], rec["source"], rec["lat"], rec["lon"], rec.get("alt", 0.0), rec.get("speed", 0.0), rec.get("heading", 0.0), rec["ts"], meta_json)
                )
                self._insert_count += 1
                if self._insert_count % 50 == 0:
                    self.sqlite_conn.commit()


    async def insert_detection(self, rec: Dict[str, Any]):
        class_counts_json = json.dumps(rec.get("class_counts", {}))
        bboxes_json = json.dumps(rec.get("bboxes", []))
        if self.is_pg:
            query = """
                INSERT INTO detections (camera_id, source, lat, lon, class_counts, bboxes, ts, geom)
                VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7, ST_SetSRID(ST_MakePoint($4, $3), 4326))
            """
            async with self.pg_pool.acquire() as conn:
                await conn.execute(
                    query,
                    rec["camera_id"],
                    rec.get("source", "cctv"),
                    rec["lat"],
                    rec["lon"],
                    class_counts_json,
                    bboxes_json,
                    rec["ts"]
                )
        else:
            async with self._lock:
                cur = self.sqlite_conn.cursor()
                cur.execute(
                    "INSERT INTO detections (camera_id, source, lat, lon, class_counts, bboxes, ts) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (rec["camera_id"], rec.get("source", "cctv"), rec["lat"], rec["lon"], class_counts_json, bboxes_json, rec["ts"])
                )
                self.sqlite_conn.commit()

    async def insert_anomaly(self, anomaly: Dict[str, Any]):
        meta_json = json.dumps(anomaly.get("meta", {}))
        if self.is_pg:
            query = """
                INSERT INTO anomalies (id, entity_id, entity_type, rule_name, severity, description, lat, lon, alt, ts, meta)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::jsonb)
                ON CONFLICT (id) DO UPDATE SET ts = EXCLUDED.ts, description = EXCLUDED.description
            """
            async with self.pg_pool.acquire() as conn:
                await conn.execute(
                    query,
                    anomaly["id"],
                    anomaly["entity_id"],
                    anomaly["entity_type"],
                    anomaly["rule_name"],
                    anomaly["severity"],
                    anomaly["description"],
                    anomaly["lat"],
                    anomaly["lon"],
                    anomaly.get("alt", 0.0),
                    anomaly["ts"],
                    meta_json
                )
        else:
            async with self._lock:
                cur = self.sqlite_conn.cursor()
                cur.execute(
                    """INSERT OR REPLACE INTO anomalies (id, entity_id, entity_type, rule_name, severity, description, lat, lon, alt, ts, meta)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (anomaly["id"], anomaly["entity_id"], anomaly["entity_type"], anomaly["rule_name"], anomaly["severity"],
                     anomaly["description"], anomaly["lat"], anomaly["lon"], anomaly.get("alt", 0.0), anomaly["ts"], meta_json)
                )
                self.sqlite_conn.commit()

    async def insert_event(self, event: Dict[str, Any]):
        meta_json = json.dumps(event.get("meta", {}))
        if self.is_pg:
            query = """
                INSERT INTO events (id, event_type, entity_id, severity, title, summary, lat, lon, ts, meta)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb)
                ON CONFLICT (id) DO UPDATE SET ts = EXCLUDED.ts, summary = EXCLUDED.summary
            """
            async with self.pg_pool.acquire() as conn:
                await conn.execute(
                    query,
                    event["id"],
                    event["event_type"],
                    event["entity_id"],
                    event["severity"],
                    event["title"],
                    event["summary"],
                    event["lat"],
                    event["lon"],
                    event["ts"],
                    meta_json
                )
        else:
            async with self._lock:
                cur = self.sqlite_conn.cursor()
                cur.execute(
                    """INSERT OR REPLACE INTO events (id, event_type, entity_id, severity, title, summary, lat, lon, ts, meta)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (event["id"], event["event_type"], event["entity_id"], event["severity"], event["title"],
                     event["summary"], event["lat"], event["lon"], event["ts"], meta_json)
                )
                self.sqlite_conn.commit()

    async def get_latest_entities(self, table: str, limit: int = 200) -> List[Dict[str, Any]]:
        # Return latest unique entities by entity_id
        if self.is_pg:
            query = f"""
                SELECT DISTINCT ON (entity_id) entity_id, source, lat, lon, alt, speed, heading, ts, meta
                FROM {table}
                ORDER BY entity_id, ts DESC
                LIMIT $1
            """
            async with self.pg_pool.acquire() as conn:
                rows = await conn.fetch(query, limit)
                return [dict(r) for r in rows]
        else:
            async with self._lock:
                cur = self.sqlite_conn.cursor()
                query = f"""
                    SELECT entity_id, source, lat, lon, alt, speed, heading, ts, meta
                    FROM {table}
                    GROUP BY entity_id
                    ORDER BY ts DESC
                    LIMIT ?
                """
                cur.execute(query, (limit,))
                results = []
                for row in cur.fetchall():
                    item = dict(row)
                    if isinstance(item.get("meta"), str):
                        try:
                            item["meta"] = json.loads(item["meta"])
                        except:
                            item["meta"] = {}
                    results.append(item)
                return results

    async def get_recent_events(self, limit: int = 50, min_severity: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.is_pg:
            clause = "WHERE severity = $2" if min_severity else ""
            params = [limit, min_severity] if min_severity else [limit]
            query = f"SELECT id, event_type, entity_id, severity, title, summary, lat, lon, ts, meta FROM events {clause} ORDER BY ts DESC LIMIT $1"
            async with self.pg_pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [dict(r) for r in rows]
        else:
            async with self._lock:
                cur = self.sqlite_conn.cursor()
                if min_severity:
                    cur.execute("SELECT * FROM events WHERE severity = ? ORDER BY ts DESC LIMIT ?", (min_severity, limit))
                else:
                    cur.execute("SELECT * FROM events ORDER BY ts DESC LIMIT ?", (limit,))
                results = []
                for row in cur.fetchall():
                    item = dict(row)
                    if isinstance(item.get("meta"), str):
                        try:
                            item["meta"] = json.loads(item["meta"])
                        except:
                            item["meta"] = {}
                    results.append(item)
                return results

    async def get_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        if self.is_pg:
            async with self.pg_pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM events WHERE id = $1", event_id)
                return dict(row) if row else None
        else:
            async with self._lock:
                cur = self.sqlite_conn.cursor()
                cur.execute("SELECT * FROM events WHERE id = ?", (event_id,))
                row = cur.fetchone()
                if not row:
                    return None
                item = dict(row)
                if isinstance(item.get("meta"), str):
                    try:
                        item["meta"] = json.loads(item["meta"])
                    except:
                        item["meta"] = {}
                return item

    async def get_stats(self) -> Dict[str, Any]:
        stats = {}
        tables = ["flights", "ships", "quakes", "detections", "anomalies", "events"]
        if self.is_pg:
            async with self.pg_pool.acquire() as conn:
                for t in tables:
                    val = await conn.fetchval(f"SELECT COUNT(*) FROM {t}")
                    stats[t] = val
        else:
            async with self._lock:
                cur = self.sqlite_conn.cursor()
                for t in tables:
                    cur.execute(f"SELECT COUNT(*) FROM {t}")
                    stats[t] = cur.fetchone()[0]
        stats["backend"] = "postgresql" if self.is_pg else "sqlite"
        return stats

    async def close(self):
        if self.pg_pool:
            await self.pg_pool.close()
        if self.sqlite_conn:
            self.sqlite_conn.close()

# Global database singleton
db = SentinelDB()
