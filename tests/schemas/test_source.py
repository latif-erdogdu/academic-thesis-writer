# tests/schemas/test_source.py
import json, jsonschema, pathlib

SCHEMA_PATH = pathlib.Path(".opencode/skill/academic-thesis-writer/schemas/source.json")

def test_source_schema_exists_and_valid():
    assert SCHEMA_PATH.exists(), "Schema file missing"
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)

def test_source_validates_minimal_instance():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    minimal = {
        "id": "SRC-2026-001",
        "doi": "10.1234/example.2026.001",
        "title": "Example Study on BCI",
        "authors": ["Doe, J.", "Smith, A."],
        "year": 2026,
        "type": "journal-article",
        "journal": "Journal of Neural Engineering",
        "venue": "J. Neural Eng.",
        "volume": "19",
        "issue": "4",
        "pages": "046001",
        "url": "https://doi.org/10.1234/example.2026.001",
        "verification_status": "verified",
        "verification_sources": ["crossref", "openalex"],
        "verification_score": 0.85,
        "retracted": False,
        "retraction_notice": None,
        "created_at": "2026-09-26T10:00:00+00:00",
        "updated_at": "2026-09-26T10:00:00+00:00"
    }
    validator.validate(minimal)