"""Görev 2: thesis:extract komutunun pdf_extract'e baglanmasi.

Ayrıca tools/atw/cli/main.py'de kanonik empty_state yerine gecen bir
kopyanin varligini denetler (onay kapilari {} olarak yaziliyordu).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import jsonschema
import pytest

from tools.atw import state as kanonik_state
from tools.atw.cli import main as cli
from tools.pdf_extract import ExtractedEvidence

SEMA_DIZIN = Path("schemas")


def _sema_yukle(ad: str) -> dict:
    return json.loads((SEMA_DIZIN / f"{ad}.json").read_text(encoding="utf-8"))


def _ornek_kanit() -> ExtractedEvidence:
    return ExtractedEvidence(
        text="Kurgusal alinti metni.",
        page=17,
        section="3.2",
        subsection=None,
        paragraph_index=2,
        char_start=0,
        char_end=100,
        evidence_type="literature",
        strength="direct",
        supports_claim="CLM-001",
        confidence=0.82,
    )


def _args(source: str = "SRC-001", claim: str = "CLM-001", pdf: str | None = None) -> argparse.Namespace:
    return argparse.Namespace(source=source, claim=claim, pdf=pdf)


def _durum_yaz(tmp_path: Path, durum: dict) -> Path:
    (tmp_path / "thesis_state.json").write_text(
        json.dumps(durum, ensure_ascii=False), encoding="utf-8"
    )
    return tmp_path / "thesis_state.json"


def _temel_durum() -> dict:
    durum = kanonik_state.empty_state("THESIS-2026-001", "Ornek Tez")
    durum["sources"] = [
        {"id": "SRC-001", "title": "Kurgusal A", "source_type": "article",
         "verification": {"status": "verified", "bibliographic_match": 0.95,
                          "verified_at": "2026-09-26T10:12:00+00:00",
                          "verification_sources": ["crossref"]},
         "retraction_status": "not_retracted"},
    ]
    durum["claims_registry"] = [
        {"id": "CLM-001", "text": "Yontem basari oranini artirir.",
         "importance": "high", "verification_status": "unverified",
         "sources": ["SRC-001"], "evidence_ids": []},
    ]
    return durum


@pytest.fixture
def kurulum(tmp_path, monkeypatch):
    """CLI'nin gecici dizini ve sahte bir PDF kullanan ortam hazirlar."""
    pdf = tmp_path / "kaynak.pdf"
    pdf.write_bytes(b"%PDF-1.4 kurgusal")
    monkeypatch.setattr(cli, "VERI_KOKU", tmp_path)
    return tmp_path, pdf


# --- empty_state kopyasi ----------------------------------------------------

def test_cli_kanonik_empty_state_kullanir():
    """CLI kendi empty_state'ini tanimlamaz, kanonik olani kullanir."""
    assert cli.empty_state is kanonik_state.empty_state


def test_cli_ile_acilan_tezde_onay_kapilari_var():
    """cmd_new'in yazdigi durum 7 onay kapisini icermelidir."""
    durum = cli.empty_state("THESIS-2026-001", "Ornek")
    assert len(durum["human_approvals"]) == len(kanonik_state.APPROVAL_GATES)
    assert all(v is False for v in durum["human_approvals"].values())


# --- cmd_extract ------------------------------------------------------------

def test_extract_kanit_bulup_duruma_ekler(kurulum, monkeypatch):
    """Bulunan kanit evidence_registry'ye EVD kimligiyle eklenir."""
    tmp_path, pdf = kurulum
    _durum_yaz(tmp_path, _temel_durum())
    monkeypatch.setattr(
        "tools.pdf_extract.find_evidence_for_claim",
        lambda *a, **k: [_ornek_kanit()],
    )
    assert cli.cmd_extract(_args(pdf=str(pdf))) == 0

    durum = json.loads((tmp_path / "thesis_state.json").read_text(encoding="utf-8"))
    assert len(durum["evidence_registry"]) == 1
    kanit = durum["evidence_registry"][0]
    assert kanit["id"] == "EVD-001"
    assert kanit["source_id"] == "SRC-001"
    assert kanit["supports_claim"] == "CLM-001"


def test_extract_kayit_evidence_semasina_uyar(kurulum, monkeypatch):
    """Uretilen kanit kaydi evidence.json semasina uymalidir."""
    tmp_path, pdf = kurulum
    _durum_yaz(tmp_path, _temel_durum())
    monkeypatch.setattr(
        "tools.pdf_extract.find_evidence_for_claim",
        lambda *a, **k: [_ornek_kanit()],
    )
    cli.cmd_extract(_args(pdf=str(pdf)))
    durum = json.loads((tmp_path / "thesis_state.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(_sema_yukle("evidence")).validate(
        durum["evidence_registry"][0]
    )


def test_extract_kanit_idleri_saymayla_ilerler(kurulum, monkeypatch):
    """Ikinci cagrida EVD-002 kimligi uretilmelidir."""
    tmp_path, pdf = kurulum
    durum = _temel_durum()
    durum["evidence_registry"] = [
        {"id": "EVD-001", "source_id": "SRC-001",
         "location": {"page": 1, "section": "", "paragraph": None},
         "text": "Kurgusal", "evidence_type": "literature", "strength": "direct"},
    ]
    _durum_yaz(tmp_path, durum)
    monkeypatch.setattr(
        "tools.pdf_extract.find_evidence_for_claim",
        lambda *a, **k: [_ornek_kanit()],
    )
    cli.cmd_extract(_args(pdf=str(pdf)))
    durum = json.loads((tmp_path / "thesis_state.json").read_text(encoding="utf-8"))
    assert durum["evidence_registry"][-1]["id"] == "EVD-002"


def test_extract_kanit_bulamazsa_durum_degismez(kurulum, monkeypatch):
    """Kanit bulunamazsa hata verilir ve duruma kayit eklenmez."""
    tmp_path, pdf = kurulum
    _durum_yaz(tmp_path, _temel_durum())
    monkeypatch.setattr(
        "tools.pdf_extract.find_evidence_for_claim", lambda *a, **k: []
    )
    assert cli.cmd_extract(_args(pdf=str(pdf))) == 1
    durum = json.loads((tmp_path / "thesis_state.json").read_text(encoding="utf-8"))
    assert durum["evidence_registry"] == []


def test_extract_bilinmeyen_kaynak_hata_verir(kurulum, monkeypatch):
    """sources icinde olmayan SRC kimligi hata vermelidir."""
    tmp_path, pdf = kurulum
    _durum_yaz(tmp_path, _temel_durum())
    monkeypatch.setattr(
        "tools.pdf_extract.find_evidence_for_claim", lambda *a, **k: [_ornek_kanit()]
    )
    assert cli.cmd_extract(_args(source="SRC-999", pdf=str(pdf))) == 1


def test_extract_bilinmeyen_iddia_hata_verir(kurulum, monkeypatch):
    """claims_registry icinde olmayan CLM kimligi hata vermelidir."""
    tmp_path, pdf = kurulum
    _durum_yaz(tmp_path, _temel_durum())
    monkeypatch.setattr(
        "tools.pdf_extract.find_evidence_for_claim", lambda *a, **k: [_ornek_kanit()]
    )
    assert cli.cmd_extract(_args(claim="CLM-999", pdf=str(pdf))) == 1


def test_extract_pdf_dosyasi_yoksa_hata_verir(kurulum):
    """Var olmayan PDF yolu hata vermelidir."""
    tmp_path, _ = kurulum
    _durum_yaz(tmp_path, _temel_durum())
    assert cli.cmd_extract(_args(pdf=str(tmp_path / "yok.pdf"))) == 1


def test_extract_pdf_argumani_zorunlu(kurulum, monkeypatch):
    """--pdf verilmediginde hata verilir (source.json'da yol alani yok)."""
    tmp_path, _ = kurulum
    _durum_yaz(tmp_path, _temel_durum())
    assert cli.cmd_extract(_args(pdf=None)) == 1
