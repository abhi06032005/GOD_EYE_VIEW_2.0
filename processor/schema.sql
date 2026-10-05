-- SentinelAI Spatial & Relational Schema
-- PostGIS enabled

CREATE EXTENSION IF NOT EXISTS postgis;

-- Flights Table
CREATE TABLE IF NOT EXISTS flights (
    id BIGSERIAL PRIMARY KEY,
    entity_id VARCHAR(64) NOT NULL,
    source VARCHAR(32) NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    alt DOUBLE PRECISION DEFAULT 0.0,
    speed DOUBLE PRECISION DEFAULT 0.0,
    heading DOUBLE PRECISION DEFAULT 0.0,
    ts DOUBLE PRECISION NOT NULL,
    meta JSONB DEFAULT '{}'::jsonb,
    geom geometry(Point, 4326)
);

CREATE INDEX IF NOT EXISTS idx_flights_ts ON flights (ts DESC);
CREATE INDEX IF NOT EXISTS idx_flights_entity_id ON flights (entity_id);
CREATE INDEX IF NOT EXISTS idx_flights_geom ON flights USING GIST (geom);

-- Ships / Maritime Vessels Table
CREATE TABLE IF NOT EXISTS ships (
    id BIGSERIAL PRIMARY KEY,
    entity_id VARCHAR(64) NOT NULL,
    source VARCHAR(32) NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    alt DOUBLE PRECISION DEFAULT 0.0,
    speed DOUBLE PRECISION DEFAULT 0.0,
    heading DOUBLE PRECISION DEFAULT 0.0,
    ts DOUBLE PRECISION NOT NULL,
    meta JSONB DEFAULT '{}'::jsonb,
    geom geometry(Point, 4326)
);

CREATE INDEX IF NOT EXISTS idx_ships_ts ON ships (ts DESC);
CREATE INDEX IF NOT EXISTS idx_ships_entity_id ON ships (entity_id);
CREATE INDEX IF NOT EXISTS idx_ships_geom ON ships USING GIST (geom);

-- Earthquakes Table
CREATE TABLE IF NOT EXISTS quakes (
    id BIGSERIAL PRIMARY KEY,
    entity_id VARCHAR(64) NOT NULL,
    source VARCHAR(32) NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    alt DOUBLE PRECISION DEFAULT 0.0,
    speed DOUBLE PRECISION DEFAULT 0.0,
    heading DOUBLE PRECISION DEFAULT 0.0,
    ts DOUBLE PRECISION NOT NULL,
    meta JSONB DEFAULT '{}'::jsonb,
    geom geometry(Point, 4326)
);

CREATE INDEX IF NOT EXISTS idx_quakes_ts ON quakes (ts DESC);
CREATE INDEX IF NOT EXISTS idx_quakes_entity_id ON quakes (entity_id);
CREATE INDEX IF NOT EXISTS idx_quakes_geom ON quakes USING GIST (geom);

-- Computer Vision Detections Table
CREATE TABLE IF NOT EXISTS detections (
    id BIGSERIAL PRIMARY KEY,
    camera_id VARCHAR(64) NOT NULL,
    source VARCHAR(32) NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    class_counts JSONB DEFAULT '{}'::jsonb,
    bboxes JSONB DEFAULT '[]'::jsonb,
    ts DOUBLE PRECISION NOT NULL,
    geom geometry(Point, 4326)
);

CREATE INDEX IF NOT EXISTS idx_detections_ts ON detections (ts DESC);
CREATE INDEX IF NOT EXISTS idx_detections_camera_id ON detections (camera_id);

-- Anomalies Table
CREATE TABLE IF NOT EXISTS anomalies (
    id VARCHAR(64) PRIMARY KEY,
    entity_id VARCHAR(64) NOT NULL,
    entity_type VARCHAR(32) NOT NULL,
    rule_name VARCHAR(64) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    description TEXT NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    alt DOUBLE PRECISION DEFAULT 0.0,
    ts DOUBLE PRECISION NOT NULL,
    meta JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_anomalies_ts ON anomalies (ts DESC);
CREATE INDEX IF NOT EXISTS idx_anomalies_entity_id ON anomalies (entity_id);

-- Correlated Events Table (for Globe alerts and RAG)
CREATE TABLE IF NOT EXISTS events (
    id VARCHAR(64) PRIMARY KEY,
    event_type VARCHAR(32) NOT NULL,
    entity_id VARCHAR(64) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    title VARCHAR(256) NOT NULL,
    summary TEXT NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    ts DOUBLE PRECISION NOT NULL,
    meta JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_events_ts ON events (ts DESC);
CREATE INDEX IF NOT EXISTS idx_events_severity ON events (severity);
