"""Referans dosyalarinin varligi, icerigi ve sema uyumu."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DIR = REPO_ROOT / "references"

REFERANSLAR = [
    "citation_rules", "source_verification", "evidence_rules",
    "research_gap", "academic_integrity", "systematic_review_protocol",
    "methodology_rules",
]


@pytest.mark.parametrize("referans", REFERANSLAR)
def test_referans_dosyasi_var(referans):
    yol = REFERENCE_DIR / f"{referans}.md"
    assert yol.is_file(), f"Eksik referans: {yol}"


@pytest.mark.parametrize("referans", REFERANSLAR)
def test_referans_dosyasi_bos_degil(referans):
    metin = (REFERENCE_DIR / f"{referans}.md").read_text(encoding="utf-8")
    assert len(metin.strip()) > 500, f"{referans}.md çok kısa"


@pytest.mark.parametrize("referans", REFERANSLAR)
def test_referans_turkce_harf_iceriyor(referans):
    """En az bir Turkce harf bulunmali; saf Ingilizce kalmamali."""
    metin = (REFERENCE_DIR / f"{referans}.md").read_text(encoding="utf-8")
    assert re.search(r"[çğıöşüÇĞİÖŞÜ]", metin), f"{referans}.md Turkce icerik icermiyor"


def test_sistematik_derleme_prisma_akisini_kapsar():
    metin = (REFERENCE_DIR / "systematic_review_protocol.md").read_text(encoding="utf-8")
    for adim in ["search_strategy", "inclusion", "exclusion", "deduplication",
                 "screening", "quality_assessment", "extraction", "synthesis"]:
        assert adim in metin.lower(), adim


def test_sistematik_derleme_arama_kaydi_semasiyla_uyumlu():
    metin = (REFERENCE_DIR / "systematic_review_protocol.md").read_text(encoding="utf-8")
    for alan in ["prisma_flow", "records_identified", "studies_included",
                 "exclusion_reasons"]:
        assert alan in metin, alan


def test_sistematik_derleme_yakin_llvm_degistir():
    metin = (REFERENCE_DIR / "systematic_review_protocol.md").read_text(encoding="utf-8")
    assert "deneme yayın" in metin.lower() or "yayın öncesi" in metin.lower()


def test_yontem_kurallari_nicel_danisi_bos_degil():
    metin = (REFERENCE_DIR / "methodology_rules.md").read_text(encoding="utf-8")
    assert "nicel" in metin.lower()
    assert "nitel" in metin.lower()


def test_yontem_kurallari_istatistik_kontrolu_iceriyor():
    metin = (REFERENCE_DIR / "methodology_rules.md").read_text(encoding="utf-8")
    for kavram in ["etki büyüklüğü", "güven aralığı", "varsayım", "örneklem büyüklüğü"]:
        assert kavram.lower() in metin.lower(), kavram


def test_yontem_kurallari_tek_sablon_kullanmaz():
    """Nitel ve nicel icin ayri denetim olcekleri tanimlanmali."""
    metin = (REFERENCE_DIR / "methodology_rules.md").read_text(encoding="utf-8")
    assert "denetim ölçeği" in metin.lower() or "denetim olcegi" in metin.lower()
    assert metin.lower().count("|") > 40, "Yontem kurallari tablo icermeli"
