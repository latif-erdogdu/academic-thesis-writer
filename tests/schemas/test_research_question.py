# tests/schemas/test_research_question.py
# Bu test, research_question.json şemasının varlığını ve geçerliliğini doğrular.
import json
import jsonschema
import pathlib

SCHEMA_PATH = pathlib.Path(".opencode/skill/academic-thesis-writer/schemas/research_question.json")


def test_rq_schema_exists_and_valid():
    """Şema dosyasının varlığını ve JSON Schema Draft 2020-12 geçerliliğini test eder."""
    assert SCHEMA_PATH.exists(), f"Şema dosyası bulunamadı: {SCHEMA_PATH}"
    schema_content = SCHEMA_PATH.read_text(encoding="utf-8")
    schema = json.loads(schema_content)
    jsonschema.Draft202012Validator.check_schema(schema)


def test_rq_validates_minimal_instance():
    """Minimum geçerli bir research question örneğinin şema ile doğrulanmasını test eder."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    minimal = {
        "id": "RQ-001",
        "text": "How does deep learning affect EEG classification accuracy?",
        "type": "explanatory",
        "linked_hypothesis_ids": ["HYP-001"],
        "status": "active",
        "created_at": "2026-09-26T10:00:00+00:00",
        "updated_at": "2026-09-26T10:00:00+00:00"
    }
    validator.validate(minimal)
