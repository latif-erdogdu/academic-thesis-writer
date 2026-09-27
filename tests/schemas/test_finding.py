# tests/schemas/test_finding.py
"""Bulgu semasının varlığını ve en küçük örneği doğrulayan testler."""
import json
import pathlib

import jsonschema

SCHEMA_PATH = pathlib.Path(".opencode/skill/academic-thesis-writer/schemas/finding.json")


def _schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_finding_schema_exists_and_valid():
    assert SCHEMA_PATH.exists(), "Sema dosyasi eksik"
    jsonschema.Draft202012Validator.check_schema(_schema())


def test_finding_validates_minimal_instance():
    validator = jsonschema.Draft202012Validator(_schema())
    minimal = {
        "id": "FND-2026-001",
        "text": "CSP tabanlı yöntemlere kıyasla derin öğrenme %15 daha yüksek doğruluk sağlar.",
        "hypothesis_id": "HYP-001",
        "evidence_ids": ["EVD-2026-001", "EVD-2026-002"],
        "direction": "supported",
        "effect_size": 0.15,
        "statistical_significance": "p < 0.01",
        "confidence": "high",
        "status": "established",
        "created_at": "2026-09-26T10:00:00+00:00",
        "updated_at": "2026-09-26T10:00:00+00:00"
    }
    validator.validate(minimal)
