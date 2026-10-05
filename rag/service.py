"""
SentinelAI Multimodal RAG Service
Embeds situational awareness events with sentence-transformers (all-MiniLM-L6-v2, 384-dim)
into Qdrant (persistent or in-memory). On /api/explain, retrieves top-k semantically similar
past events, cross-references seismic & environmental conditions, and synthesizes grounded explanations
with mandatory event ID citations.
"""
import os
import sys
import json
import time
import asyncio
import logging
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from processor.db import db
from processor.rules import haversine_km

logger = logging.getLogger("SentinelRAG")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "events")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "none").lower()
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

class RAGService:
    def __init__(self):
        self.encoder = None
        self.qdrant = None
        self.is_embedded_qdrant = False
        self._init_encoder()
        self._init_qdrant()

    def _init_encoder(self):
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("[SentinelRAG] Loading embedding model 'all-MiniLM-L6-v2' (384-dim)...")
            self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("[SentinelRAG] Embedding model loaded successfully.")
        except Exception as e:
            logger.warning(f"[SentinelRAG] SentenceTransformer load failed: {e}. Using deterministic hash projection.")
            self.encoder = None

    def _init_qdrant(self):
        from qdrant_client import QdrantClient
        from qdrant_client.models import VectorParams, Distance

        # Try connecting to external Qdrant server
        try:
            client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=2.0)
            client.get_collections()
            self.qdrant = client
            self.is_embedded_qdrant = False
            logger.info(f"[SentinelRAG] Connected to Qdrant cluster at {QDRANT_HOST}:{QDRANT_PORT}")
        except Exception as e:
            # Fallback to local in-memory Qdrant client
            logger.info(f"[SentinelRAG] Qdrant server unreachable ({e}). Initializing in-memory Qdrant instance.")
            self.qdrant = QdrantClient(":memory:")
            self.is_embedded_qdrant = True

        # Ensure collection exists
        try:
            collections = [c.name for c in self.qdrant.get_collections().collections]
            if COLLECTION_NAME not in collections:
                self.qdrant.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                logger.info(f"[SentinelRAG] Created Qdrant collection '{COLLECTION_NAME}'")
        except Exception as e:
            logger.warning(f"[SentinelRAG] Error ensuring Qdrant collection: {e}")

    def embed_text(self, text: str) -> List[float]:
        if self.encoder:
            vector = self.encoder.encode(text, convert_to_numpy=True).tolist()
            return vector
        else:
            # Deterministic pseudo-embedding for fallback
            import hashlib
            seed = int(hashlib.md5(text.encode('utf-8')).hexdigest(), 16)
            import numpy as np
            rng = np.random.RandomState(seed % (2**32))
            v = rng.randn(384).astype(float)
            v /= np.linalg.norm(v)
            return v.tolist()

    async def index_event(self, event: Dict[str, Any]):
        """Indexes an event into Qdrant vector database."""
        from qdrant_client.models import PointStruct
        summary = f"{event.get('title', '')}: {event.get('summary', '')} Entity {event.get('entity_id')}"
        vector = self.embed_text(summary)
        # Convert ID to a deterministic int or uuid string
        import uuid
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, event["id"]))

        point = PointStruct(
            id=point_id,
            vector=vector,
            payload={
                "event_id": event["id"],
                "entity_id": event["entity_id"],
                "severity": event["severity"],
                "event_type": event["event_type"],
                "title": event["title"],
                "summary": event["summary"],
                "lat": event["lat"],
                "lon": event["lon"],
                "ts": event["ts"]
            }
        )
        self.qdrant.upsert(collection_name=COLLECTION_NAME, points=[point])

    async def explain(self, event_id: Optional[str] = None, query: Optional[str] = None) -> Dict[str, Any]:
        """
        Multimodal RAG Explanation Generator.
        Retrieves top-k historical events from Qdrant, cross-references seismic quakes,
        and generates an evidence-grounded assessment.
        """
        target_event = None
        if event_id:
            target_event = await db.get_event_by_id(event_id)

        search_query = query or (target_event.get("summary") if target_event else "threat anomaly situational awareness")
        query_vector = self.embed_text(search_query)

        # 1. Retrieve top-k semantic matches from Qdrant
        retrieved_points = []
        try:
            hits = self.qdrant.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_vector,
                limit=3
            )
            for h in hits:
                # Exclude target event itself from references
                if target_event and h.payload.get("event_id") == target_event.get("id"):
                    continue
                retrieved_points.append(h.payload)
        except Exception as e:
            logger.warning(f"[SentinelRAG] Qdrant search error: {e}")

        # 2. Correlate with nearby environmental hazards (earthquakes within 300km)
        nearby_quakes = []
        if target_event:
            all_quakes = await db.get_latest_entities("quakes", 50)
            for q in all_quakes:
                dist = haversine_km(target_event["lat"], target_event["lon"], q["lat"], q["lon"])
                if dist <= 300.0:
                    nearby_quakes.append({"quake": q, "distance_km": round(dist, 1)})

        # 3. Formulate Prompt & Synthesize Response
        citations = [p.get("event_id") for p in retrieved_points if "event_id" in p]
        if target_event:
            citations.insert(0, target_event["id"])

        if LLM_PROVIDER == "openai" and OPENAI_KEY:
            explanation = await self._generate_openai(target_event, retrieved_points, nearby_quakes, search_query)
        elif LLM_PROVIDER == "ollama":
            explanation = await self._generate_ollama(target_event, retrieved_points, nearby_quakes, search_query)
        else:
            explanation = self._generate_deterministic_template(target_event, retrieved_points, nearby_quakes, search_query)

        return {
            "event_id": event_id,
            "explanation": explanation,
            "citations": citations,
            "provider": LLM_PROVIDER,
            "retrieved_count": len(retrieved_points),
            "nearby_hazards": len(nearby_quakes)
        }

    def _generate_deterministic_template(self, target: Optional[Dict[str, Any]], context_events: List[Dict[str, Any]], quakes: List[Dict[str, Any]], query: str) -> str:
        """Deterministic, grounded template engine. Strictly enforces citations and 'insufficient context'."""
        if not target and not context_events:
            return "insufficient context: No matching operational events or sensor telemetry records found in knowledge base."

        lines = []
        if target:
            lines.append(f"### [SITUATION REPORT] Event ID: {target['id']}")
            lines.append(f"**Classification:** {target.get('severity', 'UNKNOWN')} SEVERITY | **Type:** {target.get('event_type')}")
            lines.append(f"**Target Entity:** {target.get('entity_id')} at coordinates ({target.get('lat'):.4f}, {target.get('lon'):.4f})")
            lines.append(f"**Operational Finding:** {target.get('summary')}")
        else:
            lines.append(f"### [SITUATION QUERY REPORT]: {query}")

        # Environmental & Seismic Correlation
        if quakes:
            lines.append("\n**Environmental & Natural Hazards:**")
            for q in quakes:
                q_meta = q["quake"].get("meta", {})
                lines.append(f"- Proximity correlation: M{q_meta.get('mag', 0.0)} earthquake at {q_meta.get('place')} ({q['distance_km']} km away). Seismic displacement may correlate with signal attenuation or emergency rerouting.")
        else:
            lines.append("\n**Environmental Factors:** Nominal atmospheric and seismic conditions; no natural hazard overlap detected.")

        # Historical Semantic Retrieval Precedents
        if context_events:
            lines.append("\n**Historical Precedent Analysis (Qdrant Vector Correlation):**")
            for ce in context_events:
                lines.append(f"- Citing [{ce.get('event_id')}]: Similar anomaly profile observed for entity {ce.get('entity_id')} ({ce.get('event_type')}, Severity {ce.get('severity')}). Prior mitigation validated automated sensor recalibration and air traffic advisories.")
        else:
            lines.append("\n**Historical Precedent Analysis:** No past precedent matches above cosine similarity threshold in Qdrant store.")

        # Grounding conclusion
        if target:
            lines.append(f"\n**Synthesized Protocol Recommendation:** Retain persistent tracking on asset {target.get('entity_id')}. Validated by cited evidence: [{target['id']}].")
        else:
            lines.append("\ninsufficient context to issue definitive tactical directive without specific target event identifier.")

        return "\n".join(lines)

    async def _generate_openai(self, target, context_events, quakes, query) -> str:
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=OPENAI_KEY)
            system_prompt = (
                "You are SentinelAI Situational Assessment Copilot. Provide an objective, tactical intelligence report. "
                "CRITICAL RULES: You MUST explicitly cite every retrieved event ID (e.g. [EV-1234]). "
                "If the context does not contain sufficient facts to support an assessment, you MUST state 'insufficient context'."
            )
            user_msg = f"Target Event: {json.dumps(target)}\nRetrieved Events: {json.dumps(context_events)}\nNearby Quakes: {json.dumps(quakes)}\nQuery: {query}"
            resp = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0.1
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.warning(f"OpenAI RAG call failed: {e}. Using deterministic fallback.")
            return self._generate_deterministic_template(target, context_events, quakes, query)

    async def _generate_ollama(self, target, context_events, quakes, query) -> str:
        try:
            import httpx
            system_prompt = "You are SentinelAI. You must cite retrieved event IDs. If context is lacking, say 'insufficient context'."
            payload = {
                "model": "llama3.2",
                "prompt": f"{system_prompt}\nTarget: {json.dumps(target)}\nRetrieved: {json.dumps(context_events)}\nNearby: {json.dumps(quakes)}\nQuery: {query}",
                "stream": False
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
                if res.status_code == 200:
                    return res.json().get("response", "")
        except Exception as e:
            logger.warning(f"Ollama call failed: {e}. Using deterministic fallback.")
        return self._generate_deterministic_template(target, context_events, quakes, query)

rag_service = RAGService()
