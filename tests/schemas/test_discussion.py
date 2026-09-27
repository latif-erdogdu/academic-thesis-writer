# tests/schemas/test_discussion.py
"""Tartisma semasinin varligini ve en kucuk ornegi dogrulayan testler."""
import json
import pathlib

import jsonschema

SCHEMA_PATH = pathlib.Path(".opencode/skill/academic-thesis-writer/schemas/discussion.json")


def _schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_discussion_schema_exists_and_valid():
    assert SCHEMA_PATH.exists(), "Sema dosyasi eksik"
    jsonschema.Draft202012Validator.check_schema(_schema())


def test_discussion_validates_minimal_instance():
    validator = jsonschema.Draft202012Validator(_schema())
    minimal = {
        "id": "DSC-2026-001",
        "finding_ids": ["FND-2026-001"],
        "interpretation": "Sonuclar, derin ogrenmenin ozellik temsili ogrenme avantaji sagladigini gostermektedir.",
        "limitations": ["Orneklem buyuklugu sinirli", "Yalnizca bir veri seti kullanildi"],
        "implications": ["Gelecekte capraz dogrulama gerekir"],
        "relation_to_prior_work": "Diger calismalarla uyumlu",
        "alternative_explanations": ["Veri sizintisi olasiligi"],
        "status": "draft"
    }
    validator.validate(minimal)
