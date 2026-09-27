# tests/schemas/test_evidence.py
import json, jsonschema, pathlib

SCHEMA_PATH = pathlib.Path(".opencode/skill/academic-thesis-writer/schemas/evidence.json")

def test_evidence_schema_exists_and_valid():
    assert SCHEMA_PATH.exists(), "Schema file missing"
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)

def test_evidence_validates_minimal_instance():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    minimal = {
        "id": "EVD-2026-001",
        "source_id": "SRC-2026-001",
        "claim_id": "CLM-2026-001",
        "quote": "The CNN architecture achieved 85% accuracy on the BCI dataset.",
        "location": {
            "type": "page",
            "value": "4",
            "context": "Results section, Table 2"
        },
        "supports": True,
        "certainty": "high",
        "extracted_by": "evidence-extractor",
        "created_at": "2026-09-26T10:00:00+00:00",
        "updated_at": "2026-09-26T10:00:00+00:00"
    }
    validator.validate(minimal)