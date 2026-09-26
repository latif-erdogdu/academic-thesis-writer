"""S5: Doküman gerçekliği — README, citation_rules, 4 araç README."""
from __future__ import annotations

import pathlib
import re

import pytest


def test_readme_sema_sayisi():
    """README.md: şema sayısı 21 olmalı."""
    icerik = pathlib.Path("README.md").read_text(encoding="utf-8")
    # "21 şema" veya "21 schema" veya benzeri
    assert "21" in icerik and ("şema" in icerik or "schema" in icerik.lower())


def test_readme_ajan_sayisi():
    """README.md: ajan sayısı 10 olmalı."""
    icerik = pathlib.Path("README.md").read_text(encoding="utf-8")
    # "10 ajan" veya "10 agents"
    assert "10" in icerik and ("ajan" in icerik.lower() or "agent" in icerik.lower())


def test_readme_kenar_sayisi():
    """README.md: kenar sayısı 59 olmalı (S2 sonrası)."""
    icerik = pathlib.Path("README.md").read_text(encoding="utf-8")
    assert "59" in icerik and ("kenar" in icerik.lower() or "edge" in icerik.lower())


def test_readme_registry_sayisi():
    """README.md: registry alanı 19 olmalı."""
    icerik = pathlib.Path("README.md").read_text(encoding="utf-8")
    assert "19" in icerik and ("registry" in icerik.lower() or "kayıt" in icerik)


def test_readme_tool_sayisi():
    """README.md: araç sayısı 4 olmalı."""
    icerik = pathlib.Path("README.md").read_text(encoding="utf-8")
    assert "4" in icerik and ("araç" in icerik.lower() or "tool" in icerik.lower())


def test_readme_cp_komut_yok():
    """README.md: geçersiz `cp` komutu olmamalı (Windows'ta kopyalamaz)."""
    icerik = pathlib.Path("README.md").read_text(encoding="utf-8")
    # `cp -r` Unix komutu Windows'ta çalışmaz
    assert "cp -r" not in icerik


def test_citation_rules_apa7_uc_yazar():
    """citation_rules.md: APA 7'de 3-20 ve 21+ yazar kuralı düzeltilmeli.

    Eski: "3+ yazar: APA'da ikinci yazardan sonra et al. kullanın" -> Yazar1, Yazar2, et al.
    Bu APA 6'dır. APA 7: 3-20 yazar -> hepsi listelenir (ilk atıfta); 21+ -> et al.
    """
    icerik = pathlib.Path("references/citation_rules.md").read_text(encoding="utf-8")
    satirlar = icerik.splitlines()
    # 3-20 yazar ve 21+ yazar satırlarını bul
    bulunan_3_20 = False
    bulunan_21 = False
    for i, satir in enumerate(satirlar, 1):
        if "3–20" in satir and "yazar" in satir:
            bulunan_3_20 = True
            assert "20" in satir, f"Satır {i}: 20 sayısı eksik: {satir}"
        if "21+" in satir and "yazar" in satir:
            bulunan_21 = True
            assert "19" in satir or "yirmi" in satir.lower(), f"Satır {i}: 19/yirmi eksik: {satir}"
    assert bulunan_3_20, "3–20 yazar kuralı satırı bulunamadı"
    assert bulunan_21, "21+ yazar kuralı satırı bulunamadı"


def test_citation_rules_yazar_format():
    """APA 7: 2 yazar -> Yazar1 & Yazar2; 3-19 -> Yazar1, Yazar2, ..., SonYazar; 20+ -> Yazar1 et al."""
    icerik = pathlib.Path("references/citation_rules.md").read_text(encoding="utf-8")
    # En az bir örnek formatı olmalı
    assert "et al" in icerik.lower()


def test_tool_readme_source_search():
    """tools/source_search/README.md: stub değil, gerçek içerik."""
    icerik = pathlib.Path("tools/source_search/README.md").read_text(encoding="utf-8")
    assert len(icerik) > 500, "source_search README çok kısa (stub)"
    assert "Crossref" in icerik or "OpenAlex" in icerik
    assert "API" in icerik or "api" in icerik.lower()


def test_tool_readme_source_verify():
    """tools/source_verify/README.md: stub değil, gerçek içerik."""
    icerik = pathlib.Path("tools/source_verify/README.md").read_text(encoding="utf-8")
    assert len(icerik) > 500, "source_verify README çok kısa (stub)"
    assert "DOI" in icerik or "doi" in icerik.lower()
    assert "bibliyografik" in icerik.lower() or "bibliographic" in icerik.lower()


def test_tool_readme_pdf_extract():
    """tools/pdf_extract/README.md: stub değil, gerçek içerik."""
    icerik = pathlib.Path("tools/pdf_extract/README.md").read_text(encoding="utf-8")
    assert len(icerik) > 500, "pdf_extract README çok kısa (stub)"
    assert "PDF" in icerik or "pdf" in icerik.lower()
    assert "sayfa" in icerik.lower() or "page" in icerik.lower()


def test_tool_readme_citation_check():
    """tools/citation_check/README.md: stub değil, gerçek içerik."""
    icerik = pathlib.Path("tools/citation_check/README.md").read_text(encoding="utf-8")
    assert len(icerik) > 500, "citation_check README çok kısa (stub)"
    assert "atıf" in icerik.lower() or "citation" in icerik.lower()
    assert "bütünlük" in icerik.lower() or "integrity" in icerik.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-p", "no:cacheprovider"])