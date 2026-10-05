"""
SentinelAI Unit Tests: REST Gateway & WebSocket API Endpoints
Verifies health, metrics, entity feeds, upstream God's Eye compatibility routes,
and multimodal RAG explanation synthesis.
"""
import pytest
from fastapi.testclient import TestClient
from api.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_api_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "sentinel-api"
    assert "db_stats" in data

def test_api_metrics(client):
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "msgs_per_sec" in data
    assert "e2e_lag_p50_ms" in data
    assert "e2e_lag_p95_ms" in data
    assert "total_messages" in data

def test_api_entities_all(client):
    response = client.get("/api/entities")
    assert response.status_code == 200
    data = response.json()
    assert "flights" in data
    assert "ships" in data
    assert "quakes" in data

def test_api_entities_filtered(client):
    res_flights = client.get("/api/entities?entity_type=flights")
    assert res_flights.status_code == 200
    assert "flights" in res_flights.json()

    res_ships = client.get("/api/entities?entity_type=ships")
    assert res_ships.status_code == 200
    assert "ships" in res_ships.json()

def test_api_events(client):
    response = client.get("/api/events?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert "count" in data

def test_api_gods_eye_flights_compatibility(client):
    """Verifies that /api/flights formats state vectors matching God's Eye schema."""
    response = client.get("/api/flights")
    assert response.status_code == 200
    data = response.json()
    assert "time" in data
    assert "states" in data
    assert isinstance(data["states"], list)

def test_api_gods_eye_vessels_compatibility(client):
    """Verifies that /api/vessels formats objects matching God's Eye vessel schema."""
    response = client.get("/api/vessels")
    assert response.status_code == 200
    data = response.json()
    assert "vessels" in data
    assert "count" in data
    assert isinstance(data["vessels"], list)

def test_api_explain(client):
    """Verifies multimodal RAG explanation synthesis."""
    payload = {"question": "What is the status of airborne threats near San Francisco?"}
    response = client.post("/api/explain", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert "citations" in data
    assert "retrieved_count" in data
    assert isinstance(data["citations"], list)
