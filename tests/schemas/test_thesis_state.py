# tests/schemas/test_thesis_state.py
import json, jsonschema, pathlib

SCHEMA_PATH = pathlib.Path(".opencode/skill/academic-thesis-writer/schemas/thesis_state.json")

def test_thesis_state_schema_exists_and_valid():
    assert SCHEMA_PATH.exists(), "Schema file missing"
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    # Meta-validation: schema itself must be valid JSON Schema Draft 2020-12
    jsonschema.Draft202012Validator.check_schema(schema)

def test_thesis_state_validates_minimal_instance():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    minimal = {
        "thesis_id": "THESIS-2026-001",
        "title": "Test Tez",
        "language": "tr",
        "style_profile": "apa7",
        "schema_version": "1.0",
        "version": 1,
        "created_at": "2026-09-26T10:00:00+00:00",
        "updated_at": "2026-09-26T10:00:00+00:00",
        "methodology": {},
        "human_approvals": {},
        "definitions": [],
        "conceptual_framework": [],
        "open_questions": [],
        "quality_issues": [],
        "research_questions": [],
        "hypotheses": [],
        "chapters": [],
        "variables": [],
        "evidence_registry": [],
        "claims_registry": [],
        "findings_registry": [],
        "discussion_registry": [],
        "conclusion_registry": [],
        "gap_registry": [],
        "audit_registry": [],
        "search_runs": [],
        "sources": [],
        "citations": [],
        "datasets": [],
        "analyses": [],
        "statistics": [],
        "tables": [],
        "figures": []
    }
    validator.validate(minimal)  # must not raise