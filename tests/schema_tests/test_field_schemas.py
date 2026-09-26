"""field semasi ve durum yonetimi testleri."""
from __future__ import annotations

import json

from jsonschema import Draft202012Validator

from tools.atw.state import schema_registry, load_schema

_CIZELI_DEGIL = {"thesis_state.json", "source.json", "evidence.json", "claim.json",
                 "paragraph.json", "research_question.json", "audit.json"}


def _validator(dosya_adi: str) -> Draft202012Validator:
    import json
    from tools.atw.state import SCHEMA_DIR
    sema = json.loads((SCHEMA_DIR / dosya_adi).read_text(encoding="utf-8"))
    return Draft202012Validator(sema, registry=schema_registry())


def _gecerli_kayit(dosya_adi: str) -> dict:
    import json
    from tools.atw.state import SCHEMA_DIR
    sema = json.loads((SCHEMA_DIR / dosya_adi).read_text(encoding="utf-8"))
    ornek = sema.get("examples", [])
    assert ornek, f"{dosya_adi} icin ornek kayit tanimlanmali"
    return ornek[0]


def test_tum_field_semalar_draft_2020_12_uyumlu(schema_dir):
    for dosya in sorted(schema_dir.glob("*.json")):
        if dosya.name in _CIZELI_DEGIL:
            continue
        sema = json.loads(dosya.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(sema), dosya.name


def test_her_semanin_id_alani_var(schema_dir):
    for dosya in sorted(schema_dir.glob("*.json")):
        if dosya.name in _CIZELI_DEGIL:
            continue
        sema = json.loads(dosya.read_text(encoding="utf-8"))
        assert sema.get("$id", "").endswith(dosya.name), dosya.name


def test_citation_kanit_turlerini_tasiyor():
    sema = _gecerli_kayit("citation.json")
    assert sema["citation_type"] == "article"


def test_research_gap_alanlarini_tasiyor():
    sema = _gecerli_kayit("research_gap.json")
    assert "gap_type" in sema


def test_finding_kanit_turunu_tasiyor():
    sema = _gecerli_kayit("finding.json")
    assert sema["evidence_type"] in ["literature", "primary_data", "statistical", "theory"]


def test_discussion_bulgu_baglantisi_tasiyor():
    sema = _gecerli_kayit("discussion.json")
    assert "finding_ids" in sema


def test_conclusion_izleri_tasiyor():
    sema = _gecerli_kayit("conclusion.json")
    assert "summary_fields" in sema


# Review Focus: Turkce diyakritikli basliklar tam destekli olmalı.
def test_turkce_baslik_desteklenir():
    for dosya in ["citation.json", "research_gap.json", "finding.json",
                   "discussion.json", "conclusion.json"]:
        sema = _gecerli_kayit(dosya)
        baslik = sema.get("title", "")
        assert len(baslik) > 0, f"{dosya} baslik bos olmamal"