"""Iddia -> bulgu -> tartisma -> sonuc zinciri semalari."""
from __future__ import annotations

import json

from jsonschema import Draft202012Validator

from tools.atw.state import SCHEMA_DIR, schema_registry

ZINCIR = {
    "finding.json": "FND",
    "discussion.json": "DSC",
    "conclusion.json": "CON",
    "research_gap.json": "GAP",
    "citation.json": "CIT",
}

# Planda bibliyografik veri yalnizca source.json'da yasar. Atif, bulgu,
# tartisma ve sonuc kayitlari yalnizca kimliklerle bag kurar; kopyalanmis
# alanlar normalizasyon ihlali yaratir.
_KAYNAK_VERISI_ALANLARI = {
    "title", "author", "authors", "year", "journal", "publisher",
    "doi", "url", "isbn", "volume", "issue", "pages", "edition",
}


def _yukle(dosya_adi: str) -> dict:
    return json.loads((SCHEMA_DIR / dosya_adi).read_text(encoding="utf-8"))


def _dogrulayici(dosya_adi: str) -> Draft202012Validator:
    return Draft202012Validator(_yukle(dosya_adi), registry=schema_registry())


def _ornek(dosya_adi: str) -> dict:
    ornekler = _yukle(dosya_adi)["examples"]
    assert ornekler, f"{dosya_adi} ornek icermiyor"
    return ornekler[0]


def test_bes_zincir_semasilari_var():
    for dosya_adi in ZINCIR:
        assert (SCHEMA_DIR / dosya_adi).is_file(), dosya_adi


def test_her_semanin_kimlik_prefiksi_dogru():
    for dosya_adi, prefiks in ZINCIR.items():
        sema = _yukle(dosya_adi)
        desen = sema["properties"]["id"]["pattern"]
        assert desen.startswith(f"^{prefiks}-"), f"{dosya_adi}: {desen}"


def test_ornek_kayitlar_ilgili_semayi_gecer():
    for dosya_adi in ZINCIR:
        dogrulayici = _dogrulayici(dosya_adi)
        hatalar = list(dogrulayici.iter_errors(_ornek(dosya_adi)))
        assert hatalar == [], f"{dosya_adi}: {hatalar[0].message if hatalar else ''}"


def test_bulgu_arastirma_sorusuna_bagli():
    dogrulayici = _dogrulayici("finding.json")
    kayit = _ornek("finding.json")
    assert kayit["rq_id"] == "RQ-001"
    kayit["rq_id"] = "soru1"
    assert list(dogrulayici.iter_errors(kayit)) != []


def test_bulgu_kanit_baglantisi_zorunlu():
    sema = _yukle("finding.json")
    assert "evidence_ids" in sema["required"]


def test_bulgu_istatistik_baglantisi_tasiyor():
    sema = _yukle("finding.json")
    assert "statistic_ids" in sema["properties"]


def test_tartisma_bulgulari_bagli():
    sema = _yukle("discussion.json")
    assert "finding_ids" in sema["required"]
    ornek = _ornek("discussion.json")
    assert ornek["finding_ids"] == ["FND-001"]


def test_sonuc_arastirma_sorularini_kapsar():
    dogrulayici = _dogrulayici("conclusion.json")
    ornek = _ornek("conclusion.json")
    assert ornek["rq_ids"] == ["RQ-001"]
    ornek["rq_ids"] = []
    assert list(dogrulayici.iter_errors(ornek)) != []


def test_sonuc_sinirliliklari_zorunlu():
    sema = _yukle("conclusion.json")
    assert "limitations" in sema["required"]


def test_arastirma_boslugu_kaniti_zorunlu():
    dogrulayici = _dogrulayici("research_gap.json")
    ornek = _ornek("research_gap.json")
    assert ornek["evidence_ids"] == ["EVD-001"]
    ornek["evidence_ids"] = []
    assert list(dogrulayici.iter_errors(ornek)) != []


def test_arastirma_boslugu_konu_yoklugu_ile_karisitirilir():
    dogrulayici = _dogrulayici("research_gap.json")
    ornek = _ornek("research_gap.json")
    assert ornek["gap_type"] == "unanswered_question"
    ornek["gap_type"] = "yok_duyulan_bolge"
    assert list(dogrulayici.iter_errors(ornek)) != []


def test_atif_kaynagi_ve_sayfasi_bagli():
    dogrulayici = _dogrulayici("citation.json")
    ornek = _ornek("citation.json")
    assert ornek["source_id"] == "SRC-001"
    assert ornek["page"] == 17
    ornek["page"] = "on yedi"
    assert list(dogrulayici.iter_errors(ornek)) != []


def test_atif_paragraf_kimligi_zorunlu():
    sema = _yukle("citation.json")
    assert "paragraph_id" in sema["required"]


def test_atif_stili_desteklenenler_arasi():
    """Desteklenmeyen atif stili reddedilmeli.

    `vancouver` enum'da **vardir**; reddedilmesi beklenemez.
    """
    dogrulayici = _dogrulayici("citation.json")
    ornek = _ornek("citation.json")
    ornek["style"] = "oslo"
    assert list(dogrulayici.iter_errors(ornek)) != []


def test_atif_stili_enum_kapsiyor():
    sema = _yukle("citation.json")
    for stil in ["apa7", "mla9", "chicago", "ieee", "harvard", "vancouver", "turkish"]:
        assert stil in sema["properties"]["style"]["enum"], stil
    ornek = _ornek("citation.json")
    assert ornek["style"] == "apa7"


def test_bulgu_tartisma_sonuc_zinciri_uyumlu():
    """Ayni ornek kayitlar birbirini gercekten gosteriyor mu?"""
    bulgu = _ornek("finding.json")
    tartisma = _ornek("discussion.json")
    sonuc = _ornek("conclusion.json")
    bulgu_id = bulgu["id"]
    assert bulgu_id in tartisma["finding_ids"]
    assert bulgu_id in sonuc["finding_ids"]
    assert tartisma["id"] in sonuc["discussion_ids"]


def test_bosluk_kaniti_bulgu_kanitiyla_tutarli():
    bosluk = _ornek("research_gap.json")
    bulgu = _ornek("finding.json")
    for kanit_id in bosluk["evidence_ids"]:
        assert kanit_id in bulgu["evidence_ids"] or kanit_id.startswith("EVD-")


# --- Normalizasyon regresyon korumalari -------------------------------------
# Asagidaki uc test, Task 5'teki semalarin baska varliklarin verisini
# kopyalamasini ve ogrenilmis alan kabul etmesini engeller. Planin tasarimi
# zaten bu kosullari varsayiyor; testler acikca kilitliyor.

def test_zincir_semalari_kaynak_verisi_kopyalamiyor():
    for dosya_adi in ZINCIR:
        karsilan = _KAYNAK_VERISI_ALANLARI & set(_yukle(dosya_adi).get("properties", {}))
        assert karsilan == set(), f"{dosya_adi} kaynak verisini kopyaliyor: {karsilan}"


def test_zincir_semalari_ogrenilmis_alan_reddediyor():
    for dosya_adi in ZINCIR:
        sema = _yukle(dosya_adi)
        assert sema.get("additionalProperties") is False, dosya_adi
        kayit = _ornek(dosya_adi)
        kayit["uydurma_alan"] = "deger"
        hatalar = list(_dogrulayici(dosya_adi).iter_errors(kayit))
        assert hatalar != [], f"{dosya_adi} ogrenilmis alani kabul etti"
        assert any("uydurma_alan" in hata.message for hata in hatalar), dosya_adi


def test_zincir_semalari_yanlis_kimlik_bicimini_reddediyor():
    for dosya_adi, prefiks in ZINCIR.items():
        kayit = _ornek(dosya_adi)
        kayit["id"] = f"{prefiks.lower()}1"
        assert list(_dogrulayici(dosya_adi).iter_errors(kayit)) != [], dosya_adi


def test_turkce_diyakritikli_metin_kabul_edilir():
    """Turkce diyakritikli serbest metin reddedilmemeli.

    Bibliyografik baslik planin tasariminda ``source.json`` kaydinda yasar
    (``test_core_schemas.py`` bunu ayrica dogruluyor). Zincir semalarinda
    denetlenecek husus, serbest metnin Turkce karakterleri korumasidir.
    """
    dogrulayici = _dogrulayici("research_gap.json")
    kayit = _ornek("research_gap.json")
    kayit["statement"] = "Kurgusal ornek: Turkiye'de bu olgu olculmemistir."
    assert list(dogrulayici.iter_errors(kayit)) == []
