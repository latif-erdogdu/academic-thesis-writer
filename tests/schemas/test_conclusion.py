# tests/schemas/test_conclusion.py
"""Sonuc semasinin varligini ve en kucuk ornegi dogrulayan testler."""
import json
import pathlib

import jsonschema

SCHEMA_PATH = pathlib.Path(".opencode/skill/academic-thesis-writer/schemas/conclusion.json")


def _schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_conclusion_schema_exists_and_valid():
    assert SCHEMA_PATH.exists(), "Sema dosyasi eksik"
    jsonschema.Draft202012Validator.check_schema(_schema())


def test_conclusion_validates_minimal_instance():
    validator = jsonschema.Draft202012Validator(_schema())
    minimal = {
        "id": "CON-2026-001",
        "rq_ids": ["RQ-001"],
        "finding_ids": ["FND-2026-001"],
        "answers": {
            "RQ-001": "Derin ogrenme, CSP tabanli yontemlere gore belirgin sekilde daha yuksek dogruluk saglar."
        },
        "contributions": ["Yeni bir mimari onerildi", "Capraz dogrulama protokolü tanimlandi"],
        "future_work": ["Farkli cozunurluklerde dogrulama"],
        "limitations_acknowledged": True,
        "status": "draft"
    }
    validator.validate(minimal)
