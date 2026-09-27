# tests/schemas/test_hypothesis.py
# Bu test, hypothesis.json şemasının varlığını ve geçerliliğini doğrular.
import json
import jsonschema
import pathlib

SCHEMA_PATH = pathlib.Path(".opencode/skill/academic-thesis-writer/schemas/hypothesis.json")


def test_hyp_schema_exists_and_valid():
    """Şema dosyasının varlığını ve JSON Schema Draft 2020-12 geçerliliğini test eder."""
    assert SCHEMA_PATH.exists(), f"Şema dosyası bulunamadı: {SCHEMA_PATH}"
    schema_content = SCHEMA_PATH.read_text(encoding="utf-8")
    schema = json.loads(schema_content)
    jsonschema.Draft202012Validator.check_schema(schema)


def test_hyp_validates_minimal_instance():
    """Minimum geçerli bir hypothesis örneğinin şema ile doğrulanmasını test eder."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    minimal = {
        "id": "HYP-001",
        "text": "Deep learning models achieve higher EEG classification accuracy than CSP.",
        "direction": "positive",
        "rq_id": "RQ-001",
        "test_method": "cross-validation",
        "status": "tested",
        "created_at": "2026-09-26T10:00:00+00:00",
        "updated_at": "2026-09-26T10:00:00+00:00"
    }
    validator.validate(minimal)