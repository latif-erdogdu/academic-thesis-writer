"""PRISMA akisi ve veri kokeni semalari."""
from __future__ import annotations

import pytest
from jsonschema import Draft202012Validator

from tools.atw.state import SCHEMA_DIR, schema_registry, validate_prisma_flow

DOSYALAR = [
    "search_run.json", "dataset.json", "analysis.json",
    "statistic.json", "table.json", "figure.json",
]


def _yukle(dosya_adi: str) -> dict:
    import json
    return json.loads((SCHEMA_DIR / dosya_adi).read_text(encoding="utf-8"))


def _dogrulayici(dosya_adi: str):
    return Draft202012Validator(_yukle(dosya_adi), registry=schema_registry())


def _ornek(dosya_adi: str) -> dict:
    return _yukle(dosya_adi)["examples"][0]


def test_alti_koken_semalar_var():
    for dosya_adi in DOSYALAR:
        assert (SCHEMA_DIR / dosya_adi).is_file(), dosya_adi


def test_ornek_kayitlar_gecer():
    for dosya_adi in DOSYALAR:
        hatalar = list(_dogrulayici(dosya_adi).iter_errors(_ornek(dosya_adi)))
        assert hatalar == [], f"{dosya_adi}: {hatalar[0].message if hatalar else ''}"


def test_arama_kaydi_veritabani_ve_zaman_damgasi_tasiyor():
    sema = _yukle("search_run.json")
    for alan in ["database", "query", "timestamp", "results_returned"]:
        assert alan in sema["required"], alan


def test_prisma_sayimlari_tutarli_hazir():
    ornek = _ornek("search_run.json")
    akis = ornek["prisma_flow"]
    assert akis["records_identified"] == 482
    assert akis["duplicates_removed"] == 57
    assert akis["records_screened"] == 425
    assert akis["reports_sought"] == 113
    assert akis["reports_not_retrieved"] == 3
    assert akis["reports_excluded"] == 73
    assert akis["studies_included"] == 37


def test_prisma_akisi_bilinmeyen_alan_reddedilir():
    """Sema katmaninda ifade edilebilen PRISMA kurallari yalnizca bunlar.
    Aritmetik tutarlilik JSON Schema ile ifade edilemez; adim 5'te
    `tools.atw/state.py:validate_prisma_flow` fonksiyonuna tasinir.
    """
    dogrulayici = _dogrulayici("search_run.json")
    ornek = _ornek("search_run.json")
    ornek["prisma_flow"]["uydurma_sayi"] = 1
    assert list(dogrulayici.iter_errors(ornek)) != []


def test_prisma_sayisi_negatif_olamaz():
    dogrulayici = _dogrulayici("search_run.json")
    ornek = _ornek("search_run.json")
    ornek["prisma_flow"]["records_screened"] = -1
    assert list(dogrulayici.iter_errors(ornek)) != []


def test_dahil_edilen_calsma_listesi_kosul_tasiyor():
    sema = _yukle("search_run.json")
    assert "inclusion_criteria" in sema["required"]
    assert "exclusion_criteria" in sema["required"]


def test_veri_kumesi_ham_islenmis_ayri():
    sema = _yukle("dataset.json")
    for alan in ["raw_path", "cleaned_path", "provenance"]:
        assert alan in sema["required"], alan


def test_veri_kumesi_uygulanan_islemleri_sayar():
    ornek = _ornek("dataset.json")
    assert isinstance(ornek["provenance"]["operations"], list)
    assert ornek["provenance"]["operations"], "islem gecmeleri bos olmamali"


def test_analiz_veri_kumesine_bagli():
    dogrulayici = _dogrulayici("analysis.json")
    ornek = _ornek("analysis.json")
    assert ornek["dataset_id"] == "DS-001"
    ornek["dataset_id"] = "veri1"
    assert list(dogrulayici.iter_errors(ornek)) != []


def test_analiz_arac_ve_yontem_kaydeder():
    sema = _yukle("analysis.json")
    for alan in ["method", "software", "parameters", "run_at"]:
        assert alan in sema["required"], alan


def test_istatistik_etki_boyutu_tasiyor():
    """Etki buyutugu hem duz `value` alaninda hem `effect_size`
    nesnesinde bulunur; guven araligi duz `ci_lower`/`ci_upper`
    alanlarindadir (ic ice nesne degil)."""
    sema = _yukle("statistic.json")
    for alan in ["effect_size", "value", "ci_lower", "ci_upper"]:
        assert alan in sema["properties"], alan
    ornek = _ornek("statistic.json")
    assert ornek["ci_lower"] <= ornek["value"] <= ornek["ci_upper"], (
        "ornek kayitta guven araligi degeri icinde degil"
    )


def test_istatistik_etki_olcerisi_enum_disi_reddedilir():
    """Sema katmaninda ifade edilebilen kural: olcu adi enum'da olmali.

    Etki buyulugunun degeri icin bilincli olarak ust sinir yok:
    Cohen's d 3'u asabilir, odds ratio 100'u asabilir, r-squared 1'i
    asamaz. Tek bir blanket sinir akademiktir yanlis olurdu.
    Aralik siralamasi (ci_lower <= value <= ci_upper) da JSON Schema
    ile ifade edilemedigi icin arac katmanina birakilir; bu iliski
    P0-3'te `tools/evidence/validate.py` tarafindan denetlenecektir.
    P0-1'de bu denetim YOKTUR.
    """
    dogrulayici = _dogrulayici("statistic.json")
    ornek = _ornek("statistic.json")
    assert ornek["effect_size"]["value"] == 0.42
    assert list(dogrulayici.iter_errors(ornek)) == []
    ornek["effect_size"]["measure"] = "uydurma_olcu"
    assert list(dogrulayici.iter_errors(ornek)) != []


def test_istatistik_olasilik_degerleri_sinirli():
    dogrulayici = _dogrulayici("statistic.json")
    for alan in ["p_value", "significance_level"]:
        ornek = _ornek("statistic.json")
        ornek[alan] = 1.5
        assert list(dogrulayici.iter_errors(ornek)) != [], alan
        ornek = _ornek("statistic.json")
        ornek[alan] = -0.1
        assert list(dogrulayici.iter_errors(ornek)) != [], alan


def test_istatistik_bulguya_bagli():
    sema = _yukle("statistic.json")
    assert "finding_id" in sema["required"]


def test_istatistik_ornegi_etiketler_tasiyor():
    ornek = _ornek("statistic.json")
    for alan in ["n", "test_name", "p_value", "value", "ci_lower", "ci_upper"]:
        assert alan in ornek, alan


def test_tablo_istatistikleri_bagli():
    sema = _yukle("table.json")
    assert "statistic_ids" in sema["properties"]
    assert "caption" in sema["required"]


def test_tablo_icin_veri_kaynagi_zorunlu():
    dogrulayici = _dogrulayici("table.json")
    ornek = _ornek("table.json")
    del ornek["source"]
    assert list(dogrulayici.iter_errors(ornek)) != []


def test_sekil_gorsel_yolu_ve_basligi_tasiyor():
    sema = _yukle("figure.json")
    for alan in ["image_path", "caption", "source"]:
        assert alan in sema["required"], alan


def test_sekil_dosya_uzantisi_gecerli():
    dogrulayici = _dogrulayici("figure.json")
    ornek = _ornek("figure.json")
    ornek["image_path"] = "sekil/ozet.exe"
    assert list(dogrulayici.iter_errors(ornek)) != []


def test_prisma_akisi_aritmetik_tutarli():
    """PRISMA akisi aritmetik tutarliligi validate_prisma_flow ile denetlenir."""
    ornek = _ornek("search_run.json")
    hatalar = validate_prisma_flow(ornek["prisma_flow"])
    assert hatalar == [], f"Tutarli akis icin hata bulunduk: {hatalar}"


def test_prisma_akisi_tutarsizlik_yakalanir():
    """Aritmetik tutarsizlik her uc asamada da yakalanmali."""
    from tools.atw.state import validate_prisma_flow
    akis = dict(_ornek("search_run.json")["prisma_flow"])
    test_cases = [
        ("records_screened", 999),      # 1. iliski
        ("reports_sought", 999),        # 2. iliski
        ("studies_included", 999),      # 3. iliski
        ("reports_not_retrieved", 99),  # 3. iliski
    ]
    for alan, deger in test_cases:
        akis[alan] = deger
        hatalar = validate_prisma_flow(akis)
        assert hatalar != [], f"{alan}={deger} ile tutarsizlik beklenirdi, hatalar: {hatalar}"


def test_prisma_dahil_edilen_sifir_olabilir():
    """Hiç calisma dahil edilmeyen bir derleme de gecerli olmali."""
    from tools.atw.state import validate_prisma_flow
    akis = dict(_ornek("search_run.json")["prisma_flow"])
    akis["reports_excluded"] = akis["reports_sought"] - akis["reports_not_retrieved"]
    akis["studies_included"] = 0
    hatalar = validate_prisma_flow(akis)
    assert hatalar == [], f"Sifir studies_included icin hata bulunduk: {hatalar}"