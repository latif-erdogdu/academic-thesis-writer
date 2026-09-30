"""tools.atw.approval — 7 onay kapisinin gercekten zorlanmasi.

Kapsam ilkesi: bu modul "onay var" ile "onay uygulanabilir" ayrımını
test eder. Onaylanmis ama icligi bos bir asama, onaylanmamis bir asama
kadar engeldir.
"""
from __future__ import annotations

import copy

import pytest

from tools.atw.approval import (
    GATE_ASAMALARI,
    OnayHatasi,
    acik_olanlar,
    kapali_olanlar,
    kapi_acik_mi as acik_mi,
    kontrol_yaz,
    onay_geri_al,
    onay_ver,
    ozet,
    yazim_hazir_mi,
)
from tools.atw.state import APPROVAL_GATES, empty_state


def _kapili_durum() -> dict:
    return empty_state("THESIS-2026-001", "Deneme Tezi")


#: `final_thesis` kapısı beş denetim turunun da geçmiş olmasını ister
#: (spec §1: "denetim geçmesi onay değildir, ikisi de sağlanmalıdır").
#: Test fixture'ları gerçekçi olsun diye burada temiz kayıtlar bulunur.
#: Kurgusal danisman adi. `onay_ver` onaylayan zorunlu kildigi icin
#: testler de bir insan adi gecmek ZORUNDA; kimliksiz onay uretmek
#: icin ozel bir yol birakilmaz (bkz. `test_kapi_guvenligi.py` 11b).
DANISMAN = "Dr. Danışman Adı"

_DENETIM_TURLERI = ("citation", "methodology", "consistency", "integrity", "evidence")


def _temiz_denetimler() -> list[dict]:
    return [
        {
            "audit_id": f"AUD-{indeks:03d}",
            "thesis_id": "THESIS-2026-001",
            "audit_type": tur,
            "date": "2026-09-30",
            "findings": [],
        }
        for indeks, tur in enumerate(_DENETIM_TURLERI, start=1)
    ]


#: On kosul denetimi kayit duzeyinde calistigi icin fixture kayitlari
#: kendi SEMALARINA UYGUN olmak ZORUNDA. `{"id": "SR-001"}` gibi yarim
#: kayitlar uretimde yazilamaz; testte kullanilmamalari da ayni sebeple
#: yanlistir.
_ORNEK_KAYITLAR: dict[str, list[dict]] = {
    "research_questions": [
        {"id": "RQ-001", "text": "Araştırma sorusu?", "type": "main", "status": "pending"},
    ],
    "search_runs": [
        {
            "id": "SEARCH-001", "database": "crossref", "query": "kurgusal sorgu",
            "timestamp": "2026-09-30T09:00:00+00:00", "results_returned": 1,
            "inclusion_criteria": ["akademik makale"], "exclusion_criteria": ["derleme"],
            "prisma_flow": {
                "records_identified": 1, "duplicates_removed": 0, "records_screened": 1,
                "records_excluded": 0, "reports_sought": 1, "reports_excluded": 0,
                "studies_included": 1,
            },
        },
    ],
    "sources": [
        {
            "id": "SRC-001", "title": "Kurgusal kaynak", "doi": "10.1234/ornek",
            "source_type": "article", "verified": True, "retraction_status": "not_retracted",
            "verification": {
                "status": "verified", "bibliographic_match": 1.0,
                "verified_at": "2026-09-30T09:00:00+00:00",
                "verification_sources": ["crossref"],
            },
        },
    ],
    "evidence_registry": [
        {
            "id": "EVD-001", "source_id": "SRC-001",
            "location": {"page": 1, "section": "3.1", "paragraph": None},
            "text": "Kurgusal alıntı.", "evidence_type": "literature", "strength": "direct",
        },
    ],
    "gap_registry": [
        {
            "id": "GAP-001", "statement": "Kurgusal boşluk beyanı.",
            "gap_type": "unanswered_question", "evidence_ids": ["EVD-001"],
            "supporting_source_ids": ["SRC-001"], "confidence": "high",
        },
    ],
    "findings_registry": [
        {
            "id": "FND-001", "rq_id": "RQ-001", "statement": "Kurgusal bulgu.",
            "evidence_ids": ["EVD-001"],
        },
    ],
    "chapters": [
        {
            "id": "CH-001", "number": 1, "title": "Giriş",
            "paragraphs": [
                {"id": "P-001", "type": "introduction", "text": "Bu bölüm teze giriş yapar."},
            ],
        },
    ],
}

#: `ek` ile verilen alan kisaltmalari. Anahtar eski testlerle uyumlu.
_KISALTMA = {
    "rq": "research_questions",
    "sr": "search_runs",
    "src": "sources",
    "gap": "gap_registry",
    "fnd": "findings_registry",
    "ch": "chapters",
    "evd": "evidence_registry",
}


def _acik_durum(**ek) -> dict:
    """Tum kapilari acik, on kosullari saglanmis, denetimleri temiz bir durum."""
    durum = _kapili_durum()
    for kapi in APPROVAL_GATES:
        durum["human_approvals"][kapi] = True
    for alan, kayitlar in _ORNEK_KAYITLAR.items():
        durum[alan] = copy.deepcopy(kayitlar)
    for kisaltma, alan in _KISALTMA.items():
        if kisaltma in ek:
            durum[alan] = copy.deepcopy(ek[kisaltma])
    if "audit" in ek:
        durum["audit_registry"] = copy.deepcopy(ek["audit"])
    else:
        durum["audit_registry"] = _temiz_denetimler()
    return durum


def _akis_durumu() -> dict:
    """Kapilari sirayla acmak icin gereken on kosullari tasiyan durum.

    `onay_ver` artik on kosulu KENDISI denetler; test de ayni sirayi
    takip etmelidir. Yoksa "yedi kapi sirayla acilabilir" testi, gecmeyi
    bir kapi atlama sanirdi.
    """
    return _acik_durum()


# --- temel davranis -------------------------------------------------------

def test_bos_durumda_tum_kapilar_kapali():
    durum = _kapili_durum()
    assert kapali_olanlar(durum) == list(APPROVAL_GATES)
    assert acik_olanlar(durum) == []


def test_yedi_kapi_tanimli():
    """skill.yaml 7 asamali PRISMA akisi ilan ediyor; motor da 7 olmali."""
    assert len(GATE_ASAMALARI) == 7
    assert list(GATE_ASAMALARI) == APPROVAL_GATES


def test_kapi_acma_durumu_degistirir():
    durum = _akis_durumu()
    for kapi in APPROVAL_GATES:
        durum["human_approvals"][kapi] = False
    onay_ver(durum, "research_question", onaylayan=DANISMAN)
    assert acik_mi(durum, "research_question")
    assert kapali_olanlar(durum) == list(APPROVAL_GATES[1:])


# --- akis sirasi -----------------------------------------------------------

def test_onceki_kapi_kapaliyken_sonraki_kapi_ilan_edilemez():
    durum = _akis_durumu()
    for kapi in APPROVAL_GATES:
        durum["human_approvals"][kapi] = False
    # Onaylayan bilincli olarak VERILMEZ: bu test denetim SIRASINI
    # sabitler. Kimlik denetimi bagimlilik denetiminden sonra gelir,
    # dolayisiyla beklenen hata bagimlilik hatasi olmalidir; erken
    # konulsaydi bu test 'sira atlandi' yerine 'kim onayladi' olardi
    # ve gercek atlatma yolunu olcmeyi kaybederdi.
    with pytest.raises(OnayHatasi, match="research_question"):
        onay_ver(durum, "search_strategy")


def test_sirayla_acilabilir():
    durum = _akis_durumu()
    for kapi in APPROVAL_GATES:
        if kapi == "final_thesis":
            # Teslim kapisi oncesinde bes denetim de calismis olmali.
            durum["audit_registry"] = _temiz_denetimler()
        onay_ver(durum, kapi, onaylayan=DANISMAN)
    assert acik_olanlar(durum) == list(APPROVAL_GATES)


def test_geri_alma_sonraki_kapilari_da_kapatir():
    """methodology geri alinirsa final_thesis onayli kalamaz.

    Aksi halde "methodology iptal ama tez onayli" gibi tutarsiz durum olusur.
    """
    durum = _acik_durum()
    onay_geri_al(durum, "methodology")
    assert not acik_mi(durum, "methodology")
    assert not acik_mi(durum, "final_thesis")


def test_geri_alma_onesindekileri_etkilemez():
    durum = _acik_durum()
    onay_geri_al(durum, "findings")
    assert acik_mi(durum, "research_question")
    assert acik_mi(durum, "search_strategy")
    assert acik_mi(durum, "source_set")


# --- onay != uygulanabilirlik ---------------------------------------------

def test_onayli_ama_veri_bos_kapi_yazima_hazir_degil():
    """En kritik ayrim: kapı ACILMIS ama iclik bossa yazim yapilamaz."""
    durum = _acik_durum()
    durum["sources"] = []  # onayli, ama kaynak yok
    assert acik_mi(durum, "source_set")
    assert not yazim_hazir_mi(durum, "source_set")
    assert any("source" in e for e in kontrol_yaz(durum, "source_set"))


def test_kapali_kapi_yazima_hazir_degil():
    durum = _kapili_durum()
    assert not yazim_hazir_mi(durum, "methodology")


# --- methodology kilitlenmesi ----------------------------------------------

def _yazima_hazir_ama_bolumsuz() -> dict:
    """Önceki kapılar açık, `methodology` onaylı, ama HİÇ bölüm yok."""
    durum = _acik_durum(ch=[])
    assert durum["chapters"] == []
    return durum


def test_methodology_kapisi_bos_bolumle_yazilabilir():
    """`chapters` doluluğu yazımın ÖNCÜLÜ olamaz: bölümü yazım üretir.

    Bulgu
    -----
    `GATE_HAZIRLIK["methodology"]`, `chapters` boşken yazıma izin
    vermiyordu (`_registry_dolu(d, "chapters")`). Ama tez durumundaki
    `chapters` kaydını dolduran TEK kod yolu `bolumu_kaydet`, o da tam
    bu kapının arkasında: `tools/atw/cli/main.py` `cmd_write` başında
    `if not _kapi_raporu(durum, "methodology"): return CIKIS_SORUN`.

    Yani kapının ön koşulu, kapının açtığı işin çıktısıydı. Sonuç:
    **ilk bölüm hiç yazılamazdı.** `thesis:write` yalnızca
    "henüz implemente edilmedi" değil, mimari olarak kullanılamazdı.

    Aynı desenin tersi `state["methodology"]` alanında da geçerliydi:
    `empty_state()` onu `{}` ile kuruyor ve hiçbir komut doldurmuyor.
    Yani hazırlık şartını oraya taşımak da kilitlenmeyi kaldırmazdı;
    çözüm, mantıksal olarak imkânsız şartı KALDIRMAKTIR.
    """
    durum = _yazima_hazir_ama_bolumsuz()
    assert yazim_hazir_mi(durum, "methodology")
    assert kontrol_yaz(durum, "methodology") == []


def test_methodology_kapisi_hazirligi_bos_oldugu_icin_engel_uretmez():
    """`GATE_HAZIRLIK` bu kapıda artık ek şart aramamalı.

    Kapının ADI hazırlık denetimi taşıması, insan onayını ve akış
    sırasını ortadan kaldırmaz; sadece "onaylanabilir mi?" sorusunu
    yanıtlar.
    """
    from tools.atw.approval import GATE_HAZIRLIK

    assert "methodology" not in GATE_HAZIRLIK


def test_methodology_kapisi_insan_onayini_zorunlu_tutar():
    """Hazırlık şartı kalkınca kapı BOŞALMAMALI: onay yine de şart."""
    durum = _acik_durum()
    durum["human_approvals"]["methodology"] = False
    assert not yazim_hazir_mi(durum, "methodology")
    assert any("onay" in e for e in kontrol_yaz(durum, "methodology"))


def test_baska_kapilarin_hazirligi_korunur():
    """Bu düzeltme TEK kapıya sınırlı olmamalı.

    `research_question`, `search_strategy`, `source_set`, `research_gap`
    ve `findings` kapılarının hazırlık denetimleri durmalı: onların
    registry'lerini bir ÖNCEKİ komut üretiyor, döngü yok.
    """
    from tools.atw.approval import GATE_HAZIRLIK

    for kapi in ("research_question", "search_strategy", "source_set",
                 "research_gap", "findings"):
        assert kapi in GATE_HAZIRLIK, f"{kapi} hazırlık denetimini kaybetti"
        durum = _kapili_durum()
        assert kontrol_yaz(durum, kapi), f"{kapi} boş durumda engel üretmiyor"


def test_tam_durum_yazima_hazir():
    durum = _acik_durum()
    assert yazim_hazir_mi(durum, "methodology")


# --- final_thesis butunluk denetimi ---------------------------------------

def test_final_thesis_kopuk_referansta_yazilamaz():
    durum = _acik_durum()
    durum["claims_registry"] = [{"id": "CLM-001", "text": "x",
                                  "evidence_ids": ["EVD-999"]}]
    durum["evidence_registry"] = [{"id": "EVD-001", "source_id": "SRC-001",
                                    "supports_claim": "CLM-001", "verified": True}]
    engeller = kontrol_yaz(durum, "final_thesis")
    assert engeller, "kopuk referans var ama yazima izin verildi"
    assert any("kopuk" in e for e in engeller)


def test_final_thesis_kanitsiz_iddiada_yazilamaz():
    durum = _acik_durum()
    durum["claims_registry"] = [{"id": "CLM-001", "text": "x",
                                  "verification_status": "verified"}]
    durum["evidence_registry"] = [{"id": "EVD-001", "source_id": "SRC-001",
                                    "supports_claim": "CLM-001", "verified": True}]
    assert any("kanıtsız" in e for e in kontrol_yaz(durum, "final_thesis"))


def test_final_thesis_retraksiyonlu_kaynakta_yazilamaz():
    durum = _acik_durum()
    durum["sources"][0]["retraction_status"] = "retracted"
    durum["claims_registry"] = [{"id": "CLM-001", "text": "x",
                                  "sources": ["SRC-001"],
                                  "evidence_ids": ["EVD-001"]}]
    durum["evidence_registry"] = [{"id": "EVD-001", "source_id": "SRC-001",
                                    "supports_claim": "CLM-001", "verified": True}]
    assert any("çekilmiş" in e for e in kontrol_yaz(durum, "final_thesis"))


def test_final_thesis_temiz_durumda_gecer():
    durum = _acik_durum()
    assert kontrol_yaz(durum, "final_thesis") == []


# --- ozet ------------------------------------------------------------------

def test_ozet_yedi_satir_dondurur():
    """CLI raporu bu listeyi basar; satir sayisi atlanmamali."""
    assert len(ozet(_kapili_durum())) == 7


def test_ozet_sirali_ve_durum_tasiyor():
    satirlar = ozet(_acik_durum())
    assert [s[0] for s in satirlar] == list(APPROVAL_GATES)
    assert all(durum for _, durum, _ in satirlar)


# --- hata durumu -----------------------------------------------------------

def test_bilinmeyen_kapi_hata_verir():
    """Yeni eklenen ama burada unutulan kapi sessizce gecmemeli."""
    durum = _kapili_durum()
    with pytest.raises(ValueError, match="bilinmeyen"):
        acik_mi(durum, "yeni_kapi")
    with pytest.raises(ValueError, match="bilinmeyen"):
        kontrol_yaz(durum, "yeni_kapi")
    with pytest.raises(ValueError, match="bilinmeyen"):
        onay_ver(durum, "yeni_kapi")
    with pytest.raises(ValueError, match="bilinmeyen"):
        onay_geri_al(durum, "yeni_kapi")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
