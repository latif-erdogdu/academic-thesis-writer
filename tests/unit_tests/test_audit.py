"""tools.atw.audit — denetim kayitlarinin semaya uygunlugu ve dogru bulmasi.

Kapsam ilkesi: bir denetim yalnizca veriden turen bir bulgu yazabilir.
"Şüpheli görünüyor" diye uyarı üretmek, denetimi karartır; bu yüzden her
test bir SOMUT bozuk kaydi kurar ve tam olarak o bozukluğun raporlandığını
ister.
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from tools.atw.audit import (
    DENETIMLER,
    DESTEKLENEN_TURLER,
    UYARILACAK_TURLER,
    denetim_calistir,
    denetim_kimligi_ata,
    tum_denetimler,
)
from tools.atw.state import empty_state

REPO_ROOT = Path(__file__).resolve().parents[2]
SEMA = json.loads(
    (REPO_ROOT / "schemas" / "audit.json").read_text(encoding="utf-8")
)
DOGRULAYICI = jsonschema.Draft202012Validator(SEMA)


def _temiz_durum() -> dict:
    """Hicbir bulgu uretmemesi beklenen, butunluklu bir durum."""
    durum = empty_state("THESIS-2026-001", "Deneme Tezi")
    durum["sources"] = [
        {"id": "SRC-001", "doi": "10.1/x", "retraction_status": "not_retracted"}
    ]
    durum["claims_registry"] = [
        {
            "id": "CLM-001",
            "text": "Bir iddia",
            "verification_status": "verified",
            "evidence_ids": ["EVD-001"],
        }
    ]
    durum["evidence_registry"] = [
        {
            "id": "EVD-001",
            "source_id": "SRC-001",
            "supports_claim": "CLM-001",
            "verified": True,
        }
    ]
    durum["paragraphs"] = [
        {"id": "P-001", "type": "finding", "text": "Bir paragraf"}
    ]
    durum["citations"] = [
        {
            "id": "CIT-001",
            "source_id": "SRC-001",
            "paragraph_id": "P-001",
            "style": "apa7",
            "in_text_form": "(Yazar, 2020, s. 15)",
            "page": 15,
            "reference_entry": "Yazar, A. (2020). Ornek kaynak. Dergi, 1(1), 1-20.",
        }
    ]
    return durum


def _bulgu_metinleri(kayit: dict) -> list[str]:
    return [b["message"] for b in kayit["findings"]]


# --- sema uyumu -------------------------------------------------------------

@pytest.mark.parametrize("tur", sorted(DENETIMLER))
def test_her_denetim_semaya_gecer(tur: str):
    """Uretilen kayit schemas/audit.json'a gecmeli."""
    kayit = denetim_calistir(_temiz_durum(), tur)
    DOGRULAYICI.validate(kayit)


@pytest.mark.parametrize("tur", sorted(DENETIMLER))
def test_her_denetim_tur_alanini_dogru_yazar(tur: str):
    """audit_type istenen turle ayni olmali."""
    assert denetim_calistir(_temiz_durum(), tur)["audit_type"] == tur


@pytest.mark.parametrize("tur", sorted(DENETIMLER))
def test_her_denetim_bes_sayaci_doldurur(tur: str):
    """integrity_checks yalnizca semadaki bes sayaci icermeli."""
    sayaclar = denetim_calistir(_temiz_durum(), tur)["integrity_checks"]
    assert set(sayaclar) == {
        "fabricated_sources",
        "unsupported_claims",
        "retracted_sources_in_use",
        "orphaned_citations",
        "unverifiable_claims",
    }
    assert all(isinstance(v, int) and v >= 0 for v in sayaclar.values())


def test_temiz_durumde_bulgu_cikmaz():
    """Butunluklu bir durum denetimden gecmelidir (yanlis pozitif yok)."""
    for tur in DENETIMLER:
        kayit = denetim_calistir(_temiz_durum(), tur)
        assert kayit["findings"] == [], f"{tur}: {kayit['findings']}"


# --- butunluk denetimi ------------------------------------------------------

def test_butunluk_kaydi_olmayan_kaynagi_bulur():
    """Kaynaklarda olmayan bir kaynagi gosteren atif bulunmali."""
    durum = _temiz_durum()
    durum["citations"].append(
        {
            "id": "CIT-002",
            "source_id": "SRC-999",
            "paragraph_id": "P-002",
            "style": "apa7",
        }
    )
    kayit = denetim_calistir(durum, "integrity")
    assert kayit["integrity_checks"]["fabricated_sources"] == 1
    assert any("SRC-999" in m for m in _bulgu_metinleri(kayit))


def test_butunluk_kaynagsiz_atifi_bulur():
    """source_id olmayan atif 'orphan' sayilmali."""
    durum = _temiz_durum()
    durum["citations"].append(
        {"id": "CIT-003", "paragraph_id": "P-003", "style": "apa7"}
    )
    kayit = denetim_calistir(durum, "integrity")
    assert kayit["integrity_checks"]["orphaned_citations"] == 1


def test_butunluk_kanitsiz_iddiayi_bulur():
    """Kaniti olmayan iddia bulunmali."""
    durum = _temiz_durum()
    durum["claims_registry"].append(
        {"id": "CLM-002", "text": "Kanitsiz", "verification_status": "verified"}
    )
    kayit = denetim_calistir(durum, "integrity")
    assert kayit["integrity_checks"]["unsupported_claims"] == 1
    assert any("CLM-002" in m for m in _bulgu_metinleri(kayit))


def test_butunluk_retraksiyonlu_kaynagi_bulur():
    """Geri cekilmis kaynaga dayanan iddia bulunmali."""
    durum = _temiz_durum()
    durum["sources"][0]["retraction_status"] = "retracted"
    durum["claims_registry"][0]["sources"] = ["SRC-001"]
    kayit = denetim_calistir(durum, "integrity")
    assert kayit["integrity_checks"]["retracted_sources_in_use"] == 1
    assert any("geri cekilmis" in m for m in _bulgu_metinleri(kayit))


def test_butunluk_dogrulanmamis_iddiayi_bulur():
    """verification_status 'verified' olmayan iddia sayilmali."""
    durum = _temiz_durum()
    durum["claims_registry"][0]["verification_status"] = "pending"
    kayit = denetim_calistir(durum, "integrity")
    assert kayit["integrity_checks"]["unverifiable_claims"] == 1


def test_butunluk_kayitli_paragrafa_olan_atif_kusur_sayilmaz():
    """paragraph_id'si KAYITLI bir paragrafa isaret eden atif kopuk sayilmaz.

    Regresyon: `citation.paragraph_id -> paragraph` kenari vardi ama durumda
    paragraf registry'si YOKTU. Sonuc: gercek bir tezde HER atif kalici
    olarak "kopuk referans" sayiliyor, butunluk denetimi her zaman kritik
    veriyor ve gate olarak kullanilamaz oluyordu. `paragraphs` registry'si
    semaya eklendi.
    """
    durum = _temiz_durum()
    kayit = denetim_calistir(durum, "integrity")
    assert not any("P-001" in m for m in _bulgu_metinleri(kayit)), kayit["findings"]


def test_butunluk_kayitli_olmayan_paragrafa_olan_atifi_bulur():
    """Kayitli olmayan paragraf yine de kopuk referanstir (duyarli kalir)."""
    durum = _temiz_durum()
    durum["citations"][0]["paragraph_id"] = "P-999"
    kayit = denetim_calistir(durum, "integrity")
    assert any("P-999" in m for m in _bulgu_metinleri(kayit))


def test_butunluk_kopuk_rafi_bulur():
    """Varliklar arasi kopuk referans (bulgu -> kanit) bulunmali.

    Bu denetim semalardaki 53 referans alaninin tamamini tarar; yalnizca
    citation alanina bakan bir denetim bunu gormezdi.
    """
    durum = _temiz_durum()
    durum["findings_registry"] = [
        {
            "id": "FND-001",
            "statement": "Bir bulgu",
            "supported_claim_ids": ["CLM-999"],
        }
    ]
    kayit = denetim_calistir(durum, "integrity")
    assert any("CLM-999" in m for m in _bulgu_metinleri(kayit))
    assert kayit["critical_issues"], "kopuk referans critical olmali"


def test_butunluk_celiskiyi_bulgu_olarak_yazar():
    """Celiskili iddialar sayac tablosunda yer almaz, bulgu olarak raporlanir."""
    durum = _temiz_durum()
    durum["claims_registry"][0]["contradicted_by"] = ["CLM-002"]
    durum["claims_registry"].append(
        {
            "id": "CLM-002",
            "text": "Celiskili",
            "verification_status": "verified",
            "evidence_ids": ["EVD-001"],
            "contradicted_by": ["CLM-001"],
        }
    )
    kayit = denetim_calistir(durum, "integrity")
    assert any("celiskeli" in m for m in _bulgu_metinleri(kayit))


# --- kanit denetimi ---------------------------------------------------------

def test_kanit_dogrulanmamis_kaniti_bulur():
    """verified:false olan kanit raporlanmali (cmd_extract bunu uretiyor)."""
    durum = _temiz_durum()
    durum["evidence_registry"][0]["verified"] = False
    kayit = denetim_calistir(durum, "evidence")
    assert kayit["integrity_checks"]["unverifiable_claims"] == 1
    assert any("EVD-001" in m for m in _bulgu_metinleri(kayit))


def test_kanit_iddisiz_kaniti_bulur():
    """supports_claim olmayan kanit raporlanmali."""
    durum = _temiz_durum()
    durum["evidence_registry"][0].pop("supports_claim")
    kayit = denetim_calistir(durum, "evidence")
    assert kayit["integrity_checks"]["orphaned_citations"] == 1


def test_kanit_kopuk_iddiyayi_bulur():
    """supports_claim var olmayan bir iddiyiyi gosteriyorsa critical olmali."""
    durum = _temiz_durum()
    durum["evidence_registry"][0]["supports_claim"] = "CLM-999"
    kayit = denetim_calistir(durum, "evidence")
    assert kayit["integrity_checks"]["unsupported_claims"] == 1
    assert kayit["critical_issues"]


# --- yontem denetimi --------------------------------------------------------

def test_metodoloji_cevaplanmis_ama_bulgusuz_soruyu_bulur():
    """status 'answered' ama finding_ids bos ise bulgu uretilmeli."""
    durum = _temiz_durum()
    durum["research_questions"] = [
        {"id": "RQ-001", "text": "Soru", "method": "gorsel", "status": "answered"}
    ]
    kayit = denetim_calistir(durum, "methodology")
    assert any("RQ-001" in m for m in _bulgu_metinleri(kayit))


def test_metodoloji_pending_ama_bulgusu_olan_soruyu_bulur():
    """status 'pending' ama finding_ids varsa bulgu uretilmeli."""
    durum = _temiz_durum()
    durum["research_questions"] = [
        {
            "id": "RQ-001",
            "text": "Soru",
            "method": "gorsel",
            "status": "pending",
            "finding_ids": ["FND-001"],
        }
    ]
    durum["findings_registry"] = [
        {"id": "FND-001", "statement": "Bulgu", "rq_id": "RQ-001"}
    ]
    kayit = denetim_calistir(durum, "methodology")
    assert any("RQ-001" in m for m in _bulgu_metinleri(kayit))


def test_metodoloji_tutarli_soru_sessiz_gecer():
    """finding_ids ile status uyumluysa bulgu olmamali."""
    durum = _temiz_durum()
    durum["research_questions"] = [
        {
            "id": "RQ-001",
            "text": "Soru",
            "method": "gorsel",
            "status": "answered",
            "finding_ids": ["FND-001"],
        }
    ]
    durum["findings_registry"] = [
        {"id": "FND-001", "statement": "Bulgu", "rq_id": "RQ-001"}
    ]
    assert denetim_calistir(durum, "methodology")["findings"] == []


# --- kapsam disi turler -----------------------------------------------------

def test_consistency_denetimi_yoktur_ve_ilan_eder():
    """consistency icin sahte denetim YAZILMAZ; uyari listesinde olur."""
    assert "consistency" in UYARILACAK_TURLER
    assert "consistency" not in DENETIMLER


def test_tum_denetimler_tum_turleri_kapsar():
    """'all' denetimi desteklenen her turu calistirmali."""
    durum = _temiz_durum()
    turler = {k["audit_type"] for k in tum_denetimler(durum)}
    assert turler == set(DENETIMLER)


def test_tum_denetimler_desteklenmeyen_turu_sessizce_atlar():
    """consistency istenirse atlanmali, sahte bulgu uretilmemeli."""
    kayitlar = tum_denetimler(_temiz_durum(), ["citation", "consistency"])
    assert [k["audit_type"] for k in kayitlar] == ["citation"]


def test_yok_edilebilir_tur_hata_verir():
    """Bilinmeyen tur sessizce gecmemeli, hata vermeli."""
    with pytest.raises(ValueError, match="desteklenmeyen"):
        denetim_calistir(_temiz_durum(), "uydurma")


# --- kimlik atama -----------------------------------------------------------

def test_kimlikler_tekrarsiz():
    """Ayni anda calisan denetimler ayni AUD kimligini almamali."""
    durum = _temiz_durum()
    kayitlar = tum_denetimler(durum)
    denetim_kimligi_ata(durum, kayitlar)
    kimlikler = [k["audit_id"] for k in kayitlar]
    assert len(kimlikler) == len(set(kimlikler)), kimlikler
    assert all(k.startswith("AUD-") for k in kimlikler)


def test_kimlik_atama_mevcut_kayitlari_ezmez():
    """Var olan bir AUD kimligi yeniden kullanilmamali."""
    durum = _temiz_durum()
    durum["audit_registry"] = [{"audit_id": "AUD-001"}, {"audit_id": "AUD-002"}]
    kayitlar = denetim_kimligi_ata(durum, tum_denetimler(durum))
    assert {k["audit_id"] for k in kayitlar} == {"AUD-003", "AUD-004", "AUD-005", "AUD-006"}


def test_kimlik_atama_sema_dogrular():
    """Kimlik atandiktan sonra kayit yine semaya gecmeli."""
    durum = _temiz_durum()
    kayitlar = denetim_kimligi_ata(durum, tum_denetimler(durum))
    for kayit in kayitlar:
        DOGRULAYICI.validate(kayit)


# --- CLI ile uyum -----------------------------------------------------------

def test_cli_denetim_turleri_modul_ile_ayni():
    """CLI'nin --type secenekleri, modulun destekledigi turlerle uyumlu olmali.

    CLI bir turu kabul edip modul sessizce atliyorsa kullanici "denetim
    yapildi" sanir; bu bir sessizlik hatasi olurdu.
    """
    from tools.atw.cli.main import build_parser

    import argparse

    alt = None
    for action in build_parser()._actions:
        if isinstance(action, argparse._SubParsersAction):
            alt = action.choices["audit"]
    # CLI ayrica "all" sentinelini sunar; o bir denetim turu degil.
    secenekler = set(alt._option_string_actions["--type"].choices) - {"all"}
    assert secenekler == set(DESTEKLENEN_TURLER)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
