# tests/schemas/test_claim.py
import json, jsonschema, pathlib

SCHEMA_PATH = pathlib.Path(".opencode/skill/academic-thesis-writer/schemas/claim.json")

def test_claim_schema_exists_and_valid():
    assert SCHEMA_PATH.exists(), "Schema file missing"
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)

def test_claim_validates_minimal_instance():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    minimal = {
        "id": "CLM-2026-001",
        "text": "Deep learning improves EEG classification accuracy by 15% over CSP.",
        "type": "empirical",
        "certainty": "high",
        "rq_id": "RQ-001",
        "hypothesis_id": "HYP-001",
        "evidence_ids": ["EVD-2026-001", "EVD-2026-002"],
        "source_ids": ["SRC-2026-001"],
        "status": "supported",
        "created_at": "2026-09-26T10:00:00+00:00",
        "updated_at": "2026-09-26T10:00:00+00:00"
    }
    validator.validate(minimal)