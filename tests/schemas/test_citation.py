# tests/schemas/test_citation.py
"""Atif semasının varlığını ve en küçük örneği doğrulayan testler."""
import json
import pathlib

import jsonschema

SCHEMA_PATH = pathlib.Path(".opencode/skill/academic-thesis-writer/schemas/citation.json")


def _schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_citation_schema_exists_and_valid():
    assert SCHEMA_PATH.exists(), "Sema dosyasi eksik"
    jsonschema.Draft202012Validator.check_schema(_schema())


def test_citation_validates_minimal_instance():
    validator = jsonschema.Draft202012Validator(_schema())
    minimal = {
        "id": "CIT-2026-001",
        "source_id": "SRC-2026-001",
        "location": "Bölüm 2, s. 45",
        "page": "45",
        "quote": "the CNN architecture achieved 85% accuracy",
        "context": "Deneysel sonuçlar",
        "supports_claim_id": "CLM-2026-001",
        "style": "apa7",
        "created_at": "2026-09-26T10:00:00+00:00",
        "updated_at": "2026-09-26T10:00:00+00:00"
    }
    validator.validate(minimal)
