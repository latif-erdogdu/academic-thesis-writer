# tests/schemas/test_chapter.py
# Bu test, chapter.json şemasının varlığını ve geçerliliğini doğrular.
import json
import jsonschema
import pathlib

SCHEMA_PATH = pathlib.Path(".opencode/skill/academic-thesis-writer/schemas/chapter.json")


def test_ch_schema_exists_and_valid():
    """Şema dosyasının varlığını ve JSON Schema Draft 2020-12 geçerliliğini test eder."""
    assert SCHEMA_PATH.exists(), f"Şema dosyası bulunamadı: {SCHEMA_PATH}"
    schema_content = SCHEMA_PATH.read_text(encoding="utf-8")
    schema = json.loads(schema_content)
    jsonschema.Draft202012Validator.check_schema(schema)


def test_ch_validates_minimal_instance():
    """Minimum geçerli bir chapter örneğinin şema ile doğrulanmasını test eder."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    minimal = {
        "id": "CH-01",
        "title": "Giriş",
        "level": 1,
        "order": 1,
        "content_refs": [],
        "status": "draft",
        "created_at": "2026-09-26T10:00:00+00:00",
        "updated_at": "2026-09-26T10:00:00+00:00"
    }
    validator.validate(minimal)