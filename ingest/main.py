"""
SentinelAI Ingestion Orchestrator
Launches flights, maritime ships, and earthquake ingestion workers concurrently.
"""
import os
import sys
import asyncio
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ingest.fetch_flights import run_flight_ingestion
from ingest.fetch_ships import run_ship_ingestion
from ingest.fetch_quakes import run_quake_ingestion

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("IngestMaster")

async def main():
    mode = os.getenv("INGEST_MODE", "replay")
    logger.info(f"[IngestMaster] Launching multimodal ingestion in mode: {mode}")
    
    await asyncio.gather(
        run_flight_ingestion(mode=mode),
        run_ship_ingestion(mode=mode),
        run_quake_ingestion(mode=mode)
    )

if __name__ == "__main__":
    asyncio.run(main())
