"""
SentinelAI Unit Tests: Replay Determinism & Datasets
Verifies offline replay files (flights, ships, quakes, traffic cameras)
exist, are non-empty, and can be deterministically streamed.
"""
import os
import json
import pytest

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "replay")

@pytest.mark.parametrize("filename, min_records", [
    ("flights.jsonl", 100),
    ("ships.jsonl", 50),
    ("quakes.jsonl", 20),
    ("traffic_cams.jsonl", 3),
])
def test_replay_file_validity(filename, min_records):
    filepath = os.path.join(DATA_DIR, filename)
    assert os.path.isfile(filepath), f"Replay file {filename} missing at {filepath}"

    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            records.append(data)

    assert len(records) >= min_records, f"Replay file {filename} contains {len(records)} records, expected >= {min_records}"

    # Verify deterministic fields on first 10 records
    for r in records[:10]:
        assert "entity_id" in r or "id" in r or "camera_id" in r
        assert "lat" in r
        assert "lon" in r

def test_replay_determinism_consistency():
    """Verify that multiple reads yield identical record order and contents."""
    filepath = os.path.join(DATA_DIR, "flights.jsonl")
    
    pass1 = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                pass1.append(json.loads(line))

    pass2 = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                pass2.append(json.loads(line))

    assert len(pass1) == len(pass2)
    assert pass1[0]["entity_id"] == pass2[0]["entity_id"]
    assert pass1[-1]["entity_id"] == pass2[-1]["entity_id"]
