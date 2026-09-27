"""tools.atw.approval — 7 onay kapisinin gercekten zorlanmasi.

Kapsam ilkesi: bu modul "onay var" ile "onay uygulanabilir" ayrımını
test eder. Onaylanmis ama icligi bos bir asama, onaylanmamis bir asama
kadar engeldir.
"""
from __future__ import annotations

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


def _acik_durum(**ek) -> dict:
    """Tum kapiları açık, gerekli registry'ler dolu bir durum."""
    durum = _kapili_durum()
    for kapi in APPROVAL_GATES:
        durum["human_approvals"][kapi] = True
    durum["research_questions"] = ek.get("rq", [{"id": "RQ-001", "text": "Soru"}])
    durum["search_runs"] = ek.get("sr", [{"id": "SR-001"}])
    durum["sources"] = ek.get("src", [{"id": "SRC-001", "doi": "10.1/x"}])
    durum["gap_registry"] = ek.get("gap", [{"id": "GAP-001"}])
    durum["chapters"] = ek.get("ch", [{"id": "CH-001", "title": "Bölüm"}])
    durum["findings_registry"] = ek.get("fnd", [{"id": "FND-001", "statement": "B"}])
    return durum


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
    durum = _kapili_durum()
    onay_ver(durum, "research_question")
    assert acik_mi(durum, "research_question")
    assert kapali_olanlar(durum) == list(APPROVAL_GATES[1:])


# --- akis sirasi -----------------------------------------------------------

def test_onceki_kapi_kapaliyken_sonraki_kapi_ilan_edilemez():
    durum = _kapili_durum()
    with pytest.raises(OnayHatasi, match="research_question"):
        onay_ver(durum, "search_strategy")


def test_sirayla_acilabilir():
    durum = _kapili_durum()
    for kapi in APPROVAL_GATES:
        onay_ver(durum, kapi)
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
