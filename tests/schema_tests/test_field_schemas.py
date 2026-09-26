"""Alan semalarinin dogrulama testleri."""
from __future__ import annotations

import json

from jsonschema import Draft202012Validator

from tools.atw.state import SCHEMA_DIR, schema_registry

_CIZELI_DEGIL = {"thesis_state.json", "source.json", "evidence.json", "claim.json",
                 "paragraph.json", "research_question.json", "audit.json"}

# Planin tasariminda bibliyografik veri yalnizca source.json'da yasar.
# Atif, bulgu, tartisma ve sonuc kayitlari yalnizca kimliklerle bag kurar.
_KAYNAK_VERISI_ALANLARI = {
    "title", "author", "authors", "year", "journal", "publisher",
    "doi", "url", "isbn", "volume", "issue", "pages", "edition",
}

_ALAN_SEMALARI = ["citation.json", "research_gap.json", "finding.json",
                  "discussion.json", "conclusion.json"]


def _validator(dosya_adi: str) -> Draft202012Validator:
    sema = json.loads((SCHEMA_DIR / dosya_adi).read_text(encoding="utf-8"))
    return Draft202012Validator(sema, registry=schema_registry())


def _gecerli_kayit(dosya_adi: str) -> dict:
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


def test_citation_bicim_stili_ve_bag_tasiyor():
    """Atif kaydinda bicim stili ve paragraf/kaynak baglari bulunmali.

    Planda atif kaydi kaynagin kopyasi degil, atif edis yeridir; kaynak
    verisi ``source.json``'da yasar. Bu yuzden kayit yalnizca kimliklerle
    bag kurar.
    """
    sema = _gecerli_kayit("citation.json")
    assert sema["style"] == "apa7"
    assert sema["source_id"].startswith("SRC-")
    assert sema["paragraph_id"].startswith("P-")
    assert list(_validator("citation.json").iter_errors(sema)) == []


def test_research_gap_alanlarini_tasiyor():
    sema = _gecerli_kayit("research_gap.json")
    assert "gap_type" in sema
    assert sema["gap_type"] in [
        "unanswered_question", "methodological", "population", "geographical",
        "temporal", "theoretical", "measurement", "measurement_instrument",
        "sample", "contradictory_findings", "unjustified_assumption",
        "unexamined_implication",
    ], sema["gap_type"]


def test_finding_tipi_ve_soru_bagi_tasiyor():
    """Bulgu kaydi kendi tipini ve bagli oldugu arastirma sorusunu tasimali.

    ``evidence_type`` alani bulguda degil kanit kaydinda yasar; bulgu kanita
    ``evidence_ids`` ile baglanir.
    """
    sema = _gecerli_kayit("finding.json")
    assert sema["finding_type"] in [
        "quantitative", "qualitative", "mixed", "theoretical", "descriptive"
    ]
    assert sema["rq_id"].startswith("RQ-")
    assert sema["evidence_ids"], "bulgu en az bir kanita baglanmali"
    assert sema["direction"] in [
        "supported", "refuted", "mixed", "inconclusive"
    ]
    assert list(_validator("finding.json").iter_errors(sema)) == []


def test_discussion_bulgu_baglantisi_tasiyor():
    sema = _gecerli_kayit("discussion.json")
    assert "finding_ids" in sema
    assert sema["interpretation"]
    assert list(_validator("discussion.json").iter_errors(sema)) == []


def test_conclusion_katki_ve_sinirlilik_tasiyor():
    """Sonuc kaydi soru/bulgu baglarini, katkisini ve sinirliklarini tasimali.

    Serbest ``summary_fields`` alani yerine planin zorunlu ``contribution``
    ve ``limitations`` alanlari denetlenir.
    """
    sema = _gecerli_kayit("conclusion.json")
    assert sema["contribution"], "sonuc katkisi bos olmamali"
    assert sema["limitations"], "sonuc en az bir sinirlilik tasimali"
    assert sema["rq_ids"] and sema["finding_ids"]
    assert list(_validator("conclusion.json").iter_errors(sema)) == []


# Review Focus: Turkce diyakritikli metin semada sorunsuz kabul edilmeli.
def test_turkce_diyakritikli_metin_kabul_edilir():
    """Turkce diyakritikli serbest metni reddetmemeli.

    Bibliyografik baslik planin tasariminda ``source.json`` kaydinda yasar
    (``test_core_schemas.py`` bunu ayrica dogruluyor). Alan semalarinda
    denetlenecek husus, serbest metin alanlarinin Turkce karakterleri
    kaldirmadan kabul edilmesidir.
    """
    dogrulayici = _validator("research_gap.json")
    kayit = _gecerli_kayit("research_gap.json")
    kayit["statement"] = "Kurgusal ornek: Turkiye'de bu olgu olculmemistir."
    assert list(dogrulayici.iter_errors(kayit)) == []


def test_alan_semalari_kaynak_verisi_kopyalamiyor():
    """Alan semalari bibliyografik veriyi kopyalamamali.

    Kopyalanmis alanlar normalizasyon ihlali yaratir: ayni kaynak iki
    yerde tutuldugu icin biri guncellendiginde digeri bayatlar.
    """
    for dosya_adi in _ALAN_SEMALARI:
        sema = json.loads((SCHEMA_DIR / dosya_adi).read_text(encoding="utf-8"))
        karsilan = _KAYNAK_VERISI_ALANLARI & set(sema.get("properties", {}))
        assert karsilan == set(), f"{dosya_adi} kaynak verisini kopyaliyor: {karsilan}"


def test_alan_semalari_ogrenilmis_alan_reddediyor():
    """Alan semalari da kaynak semalari kadar siki olmali.

    Task 4'te ``additionalProperties: false`` butun semalardan kaldirilip
    sonra geri kondu; bu sozlesme her kayit semasi icin gecerli olmali.
    """
    for dosya_adi in _ALAN_SEMALARI:
        sema = json.loads((SCHEMA_DIR / dosya_adi).read_text(encoding="utf-8"))
        assert sema.get("additionalProperties") is False, dosya_adi
        kayit = _gecerli_kayit(dosya_adi)
        kayit["uydurma_alan"] = "deger"
        hatalar = list(_validator(dosya_adi).iter_errors(kayit))
        assert hatalar != [], f"{dosya_adi} ogrenilmis alani kabul etti"
        assert any("uydurma_alan" in hata.message for hata in hatalar), dosya_adi


def test_alan_semalari_kimlik_deseni_uyguluyor():
    """Her alan semasi kendi kimlik onekini zorunlu kilmali."""
    for dosya_adi, onek in [
        ("citation.json", "CIT"),
        ("research_gap.json", "GAP"),
        ("finding.json", "FND"),
        ("discussion.json", "DSC"),
        ("conclusion.json", "CON"),
    ]:
        sema = json.loads((SCHEMA_DIR / dosya_adi).read_text(encoding="utf-8"))
        desen = sema["properties"]["id"]["pattern"]
        assert desen == f"^{onek}-\\d{{3,}}$", f"{dosya_adi} id deseni: {desen}"
        kayit = _gecerli_kayit(dosya_adi)
        kayit["id"] = f"{onek.lower()}1"
        assert list(_validator(dosya_adi).iter_errors(kayit)) != [], dosya_adi
