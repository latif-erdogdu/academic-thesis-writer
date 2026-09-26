"""S2: Şema delikleri — yeni şemalar, desenler, formatlar, fulltext_available."""
from __future__ import annotations

import json
import pathlib

import pytest
from jsonschema import Draft202012Validator

from tools.atw.ids import ID_PREFIXES, format_id
from tools.atw.state import SCHEMA_DIR, load_schema, schema_registry, _state_validator


REGISTRY = schema_registry()


def load_sema(adi: str) -> dict:
    return load_schema(f"{adi}.json")


def test_ch_ve_var_onleri_uretilebiliyor():
    """ID_PREFIXES'e eklenen CH/VAR önekleri format_id ile üretilebilmeli."""
    assert format_id("CH", 1) == "CH-001"
    assert format_id("CH", 2) == "CH-002"
    assert format_id("VAR", 1) == "VAR-001"
    assert format_id("VAR", 42) == "VAR-042"


def test_id_prefixes_yirmi_tane():
    """ID_PREFIXES 20 önek içermeli (eski 18 + CH + VAR)."""
    assert len(ID_PREFIXES) == 20
    assert ID_PREFIXES["CH"] == "chapter"
    assert ID_PREFIXES["VAR"] == "variable"
    # HYP zaten vardı (18'in içinde)
    assert ID_PREFIXES["HYP"] == "hypothesis"


def test_yeni_semalar_var_ve_gecerli():
    """chapter.json, variable.json, hypothesis.json dosyaları var ve geçerli JSON Schema."""
    for adi in ["chapter.json", "variable.json", "hypothesis.json"]:
        yol = SCHEMA_DIR / adi
        assert yol.exists(), f"{adi} yok"
        sema = json.loads(yol.read_text(encoding="utf-8"))
        assert "$schema" in sema, f"{adi}: $schema yok"
        Draft202012Validator.check_schema(sema)


def test_chapter_alanlari_kimlik_biciminde():
    """paragraph.chapter ve research_question.chapter: ^CH-\d{3,}$ deseni."""
    for adi in ["paragraph", "research_question"]:
        sema = load_sema(adi)
        alan = sema["properties"]["chapter"]
        assert alan.get("pattern") == "^CH-\\d{3,}$", f"{adi}.chapter deseni yanlış: {alan.get('pattern')}"
        # type string veya [string, null]
        tip = alan.get("type")
        assert tip in ("string", ["string", "null"], ["null", "string"]), f"{adi}.chapter tip yanlış: {tip}"


def test_chapter_sema_alanlari():
    """chapter.json: id, number, title, goal, paragraphs[$ref:paragraph.json]."""
    sema = load_sema("chapter")
    oz = sema["properties"]
    assert oz["id"]["pattern"] == "^CH-\\d{3,}$"
    assert oz["number"]["type"] == "integer"
    assert oz["title"]["type"] == "string"
    assert oz["goal"]["type"] in (["string", "null"], ["null", "string"])
    par = oz["paragraphs"]
    assert par["type"] == "array"
    assert par["items"]["$ref"] == "paragraph.json"


def test_variable_sema_alanlari():
    """variable.json: id, name, operationalization, dataset_ids, claim_ids."""
    sema = load_sema("variable")
    oz = sema["properties"]
    assert oz["id"]["pattern"] == "^VAR-\\d{3,}$"
    assert oz["name"]["type"] == "string"
    assert oz["operationalization"]["type"] == "string"
    # dataset_ids: ^DS-\d{3,}$
    ds = oz["dataset_ids"]
    assert ds["type"] == "array"
    assert ds["items"]["pattern"] == "^DS-\\d{3,}$"
    # claim_ids: ^CLM-\d{3,}$
    clm = oz["claim_ids"]
    assert clm["type"] == "array"
    assert clm["items"]["pattern"] == "^CLM-\\d{3,}$"


def test_hypothesis_sema_alanlari():
    """hypothesis.json: id, text, status, related_research_questions, finding_ids."""
    sema = load_sema("hypothesis")
    oz = sema["properties"]
    assert oz["id"]["pattern"] == "^HYP-\\d{3,}$"
    assert oz["text"]["type"] == "string"
    assert oz["status"]["type"] == "string"
    rq = oz["related_research_questions"]
    assert rq["type"] == "array"
    assert rq["items"]["pattern"] == "^RQ-\\d{3,}$"
    fnd = oz["finding_ids"]
    assert fnd["type"] == "array"
    assert fnd["items"]["pattern"] == "^FND-\\d{3,}$"


def test_thesis_state_ref_yamalari():
    """thesis_state.json chapters/variables/hypotheses -> $ref."""
    sema = load_sema("thesis_state")
    oz = sema["properties"]
    for alan in ["chapters", "variables"]:
        assert oz[alan]["items"]["$ref"] == f"{alan[:-1]}.json", f"{alan} $ref yanlış"
    assert oz["hypotheses"]["items"]["$ref"] == "hypothesis.json"


def test_format_date_access_date():
    """source.access_date: format: date."""
    sema = load_sema("source")
    alan = sema["properties"]["access_date"]
    assert alan.get("format") == "date", f"access_date format: {alan.get('format')}"


def test_format_date_time_verified_at():
    """source.verification.verified_at: format: date-time."""
    sema = load_sema("source")
    alan = sema["properties"]["verification"]["properties"]["verified_at"]
    assert alan.get("format") == "date-time", f"verified_at format: {alan.get('format')}"


def test_format_date_time_search_run_timestamp():
    """search_run.timestamp: format: date-time."""
    sema = load_sema("search_run")
    alan = sema["properties"]["timestamp"]
    assert alan.get("format") == "date-time", f"timestamp format: {alan.get('format')}"


def test_thesis_state_created_updated_date_time():
    """thesis_state.created_at / updated_at: format: date-time."""
    sema = load_sema("thesis_state")
    for alan_adi in ["created_at", "updated_at"]:
        alan = sema["properties"][alan_adi]
        assert alan.get("format") == "date-time", f"{alan_adi} format: {alan.get('format')}"


def test_fulltext_available_nullable_boolean_kok():
    """source.json kök düzeyde fulltext_available: nullable boolean (required DEĞIL)."""
    sema = load_sema("source")
    alan = sema["properties"].get("fulltext_available")
    assert alan is not None, "fulltext_available alanı yok"
    # nullable boolean: ["boolean", "null"] veya {"type": ["boolean", "null"]}
    tip = alan.get("type")
    assert tip in (["boolean", "null"], ["null", "boolean"]), f"tip: {tip}"
    # required DEĞIL
    assert "fulltext_available" not in sema.get("required", []), "fulltext_available required olmamalı"


def test_fulltext_available_null_gecerli():
    """source.json fulltext_available: null / true / false kabul, yok sayılmalı."""
    from tools.atw.state import _state_validator
    dogrulayici = _state_validator()
    sema = load_sema("source")
    temel = {
        "id": "SRC-001",
        "title": "Kurgusal örnek",
        "source_type": "article",
        "verification": {
            "status": "pending",
            "bibliographic_match": 0.0,
            "verified_at": "2026-09-26T10:12:00+00:00",
            "verification_sources": ["manual"],
        },
    }
    # yok
    dogrulayici.evolve(schema=sema).validate(temel)
    # null
    dogrulayici.evolve(schema=sema).validate({**temel, "fulltext_available": None})
    # true
    dogrulayici.evolve(schema=sema).validate({**temel, "fulltext_available": True})
    # false
    dogrulayici.evolve(schema=sema).validate({**temel, "fulltext_available": False})


def test_sema_sayisi_yirmi_bir():
    """Toplam 21 şema (eski 18 + 3 yeni)."""
    dosyalar = list(SCHEMA_DIR.glob("*.json"))
    assert len(dosyalar) == 21, f"Beklenen 21, bulunan {len(dosyalar)}: {[d.name for d in dosyalar]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-p", "no:cacheprovider"])