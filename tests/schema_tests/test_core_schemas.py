"""Cekirdek varlik semalarinin dogrulama testleri."""
from __future__ import annotations

import pytest
from jsonschema import Draft202012Validator

from tools.atw.state import schema_registry

_KAYIT_DEGIL = {"thesis_state.json"}


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


def test_kayit_olmayan_semalar_ornek_tasiyor(schema_dir):
    import json
    for yol in sorted(schema_dir.glob("*.json")):
        if yol.name == "thesis_state.json":
            continue
        sema = json.loads(yol.read_text(encoding="utf-8"))
        assert sema.get("examples"), f"{yol.name} ornek kayit icermiyor"
        assert sema["examples"][0].get("$comment"), f"{yol.name} ornegi aciklamali"


def test_tum_ornek_kayitlar_ilgili_semayi_geceriyor(schema_dir):
    import json
    for yol in sorted(schema_dir.glob("*.json")):
        if yol.name in _KAYIT_DEGIL:
            continue
        dogrulayici = _validator(yol.name)
        for indeks, ornek in enumerate(json.loads(
                yol.read_text(encoding="utf-8"))["examples"]):
            hatalar = list(dogrulayici.iter_errors(ornek))
            assert hatalar == [], f"{yol.name} ornek[{indeks}]: {hatalar[0].message}"


def test_source_retraksiyon_alanlarini_tasiyor():
    sema = _gecerli_kayit("source.json")
    for alan in ["publication_status", "retraction_status",
                 "correction_status", "verification"]:
        assert alan in sema, alan


def test_source_retraksiyon_enum_degerleri():
    sema = _gecerli_kayit("source.json")
    assert sema["retraction_status"] == "not_retracted"


def test_source_geri_caledilen_kayit_reddedilir():
    dogrulayici = _validator("source.json")
    kayit = _gecerli_kayit("source.json")
    kayit["retraction_status"] = "belirsiz"
    assert list(dogrulayici.iter_errors(kayit)) != []


@pytest.mark.parametrize("bozuk_doi", [
    "bozuk-doi",            # kayit oneki (10.NNNN/) yok
    "10.5555/bozuk doi",    # son ekte bosluk var
    "10.555",              # onek eksik
    "doi:10.5555/ornek",   # bicim oneki karistirilmis
])
def test_source_doi_bicimsizse_reddedilir(bozuk_doi):
    r"""Geçersiz DOI reddedilmeli.

    Dikkat: `10.5555/` oneki fixture öneki olarak tanimli ve `^10\.\d{4,9}/\S+$` deseniyle **eslesir**.
    Bu yuzden "gecersiz" ornegi `10.5555/` onekiyle kurulamaz.
    """
    dogrulayici = _validator("source.json")
    kayit = _gecerli_kayit("source.json")
    kayit["doi"] = bozuk_doi
    assert list(dogrulayici.iter_errors(kayit)) != []


def test_source_kurgusal_doi_oneki_gecerli():
    """10.5555/ oneki fixture'lar icin gecerli olmasi (yasak yalnizca
    gercek yayin temsil etmesinde)."""
    dogrulayici = _validator("source.json")
    kayit = _gecerli_kayit("source.json")
    assert kayit["doi"].startswith("10.5555/")
    assert list(dogrulayici.iter_errors(kayit)) == []


# Review Focus 1: Turkce diyakritikli baslik semada sorunsuz kabul edilmeli.
def test_source_turkce_baslik_ve_yazari_gecer():
    dogrulayici = _validator("source.json")
    kayit = _gecerli_kayit("source.json")
    kayit["title"] = "Türkiye'de Yükseköğretim ve Öğrenci Başarısı: Çobanoğlu Örneği"
    kayit["authors"] = ["Çobanoğlu, A.", "Yılmaz, B.", "Öztürk, Ç."]
    assert list(dogrulayici.iter_errors(kayit)) == []


def test_evidence_tipi_literature_ve_primary_data_ayirt_edir():
    sema = _gecerli_kayit("evidence.json")
    assert sema["evidence_type"] == "literature"
    dogrulayici = _validator("evidence.json")
    kayit = _gecerli_kayit("evidence.json")
    kayit["evidence_type"] = "primary_data"
    assert list(dogrulayici.iter_errors(kayit)) == []


def test_evidence_kanit_kaynagi_zorunlu():
    dogrulayici = _validator("evidence.json")
    kayit = _gecerli_kayit("evidence.json")
    del kayit["source_id"]
    assert list(dogrulayici.iter_errors(kayit)) != []


def test_claim_kanit_kimlikleri_dizisi_tasiyor():
    sema = _gecerli_kayit("claim.json")
    assert sema["evidence_ids"] == ["EVD-001"]
    dogrulayici = _validator("claim.json")
    kayit = _gecerli_kayit("claim.json")
    kayit["evidence_ids"] = ["EVD-001", "EVD-002"]
    assert list(dogrulayici.iter_errors(kayit)) == []


def test_claim_kanit_kimligi_bicimini_dogrular():
    dogrulayici = _validator("claim.json")
    kayit = _gecerli_kayit("claim.json")
    kayit["evidence_ids"] = ["kanit1"]
    assert list(dogrulayici.iter_errors(kayit)) != []


def test_paragraph_bos_denetimi():
    sema = _gecerli_kayit("paragraph.json")
    for alan in ["claims", "evidence", "sources", "research_questions"]:
        assert alan in sema, alan


def test_research_question_bulgu_baglantisi_tasiyor():
    sema = _gecerli_kayit("research_question.json")
    assert "finding_ids" in sema


def test_audit_butunluk_kontrolu_alani_tasiyor():
    sema = _gecerli_kayit("audit.json")
    assert "integrity_checks" in sema


def test_audit_gecersiz_tip_reddedilir():
    dogrulayici = _validator("audit.json")
    kayit = _gecerli_kayit("audit.json")
    kayit["audit_type"] = "integrity_audit"
    assert list(dogrulayici.iter_errors(kayit)) != []


def test_audit_gecerli_tip_kabul_edilir():
    dogrulayici = _validator("audit.json")
    kayit = _gecerli_kayit("audit.json")
    assert kayit["audit_type"] == "integrity"
    assert list(dogrulayici.iter_errors(kayit)) == []


# Review Focus 2: Tek alanlikli sema reddedilir.
def test_tek_alanlik_sema_yok():
    """Yalnizca 'id' alani olan sema kabul edilmez."""
    import json
    from tools.atw.state import SCHEMA_DIR
    for yol in sorted(SCHEMA_DIR.glob("*.json")):
        if yol.name in _KAYIT_DEGIL:
            continue
        sema = json.loads(yol.read_text(encoding="utf-8"))
        alanlar = sema.get("properties", {})
        assert len(alanlar) >= 3, f"{yol.name} en az 3 alan tasimali, {len(alanlar)} var"