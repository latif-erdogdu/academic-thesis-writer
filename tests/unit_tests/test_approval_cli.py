"""Onay kapilarinin CLI'da GERCEKTEN gecerli olmasi.

Bu katman olmadan kapilar tanimli olur ama hicbir yerde sorgulanmazdi —
Gorev 6'nin asil boslugu buydu. `cmd_write` ve `cmd_export` kapisiz
ilerlememeli, `cmd_status` akisi gostermeli.
"""
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from tools.atw.cli import main as cli
from tools.atw.state import empty_state

DOLAR = chr(36)


@pytest.fixture
def depo(tmp_path, monkeypatch):
    (tmp_path / "schemas").mkdir()
    for sema in Path("schemas").glob("*.json"):
        (tmp_path / "schemas" / sema.name).write_text(
            sema.read_text(encoding="utf-8"), encoding="utf-8"
        )
    monkeypatch.setattr(cli, "VERI_KOKU", tmp_path)
    return tmp_path


def _yaz(depo: Path, durum: dict) -> None:
    (depo / "thesis_state.json").write_text(
        json.dumps(durum, ensure_ascii=False), encoding="utf-8"
    )


def _oku(depo: Path) -> dict:
    return json.loads((depo / "thesis_state.json").read_text(encoding="utf-8"))


def _kapili(depo: Path) -> dict:
    durum = empty_state("THESIS-2026-001", "Deneme Tezi")
    _yaz(depo, durum)
    return durum


def _onayli(depo: Path) -> dict:
    """Tüm kapıları açık ve içlikleri dolu bir tez."""
    durum = empty_state("THESIS-2026-001", "Deneme Tezi")
    for kapi in durum["human_approvals"]:
        durum["human_approvals"][kapi] = True
    durum["research_questions"] = [{"id": "RQ-001", "text": "Soru"}]
    durum["search_runs"] = [{"id": "SR-001"}]
    durum["sources"] = [{"id": "SRC-001", "doi": "10.1/x"}]
    durum["gap_registry"] = [{"id": "GAP-001"}]
    durum["chapters"] = [{"id": "CH-001", "title": "B"}]
    durum["findings_registry"] = [{"id": "FND-001", "statement": "S"}]
    _yaz(depo, durum)
    return durum


# --- cmd_write -------------------------------------------------------------

def test_write_kapaliyken_engellenir(depo, capsys):
    """Onay yoksa yazım yapılmamalı — stub'a bile girilmemeli."""
    _kapili(depo)
    assert cli.cmd_write(Namespace(chapter="CH-001", rq="RQ-001")) == 1

    cikti = capsys.readouterr().out
    assert "methodology" in cikti
    assert "Henüz implemente edilmedi" not in cikti, (
        "kapı kapalıyken stub'a düşülmemeli"
    )


def test_write_onayliyken_stuba_gecer(depo, capsys):
    """Kapı açıkken komut kendi işine devam eder."""
    _onayli(depo)
    assert cli.cmd_write(Namespace(chapter="CH-001", rq="RQ-001")) == 0
    assert "Henüz implemente edilmedi" in capsys.readouterr().out


def test_write_engel_mesaji_hangi_kapiyi_soyluyor(depo, capsys):
    """Hata mesajı eksik olan şeyi ADIYLA söyler."""
    durum = _kapili(depo)
    durum["chapters"] = [{"id": "CH-001", "title": "B"}]  # veri var, onay yok
    _yaz(depo, durum)

    assert cli.cmd_write(Namespace(chapter="CH-001", rq="RQ-001")) == 1
    cikti = capsys.readouterr().out
    assert "human_approvals" in cikti, cikti


# --- cmd_export ------------------------------------------------------------

def test_export_final_kapisi_kapaliyken_engellenir(depo, capsys):
    _kapili(depo)
    assert cli.cmd_export(Namespace(format="md")) == 1
    cikti = capsys.readouterr().out
    assert "final_thesis" in cikti
    assert "Henüz implemente edilmedi" not in cikti


def test_export_kayitli_ama_butunluk_bozukken_engellenir(depo, capsys):
    """En katı kapı: tüm onaylar açık, ama tez bütünlüğü bozuk.

    Bu, onay motorunun var olma nedeni: onaylı tez de bozuk olabilir ve
    paylaşılmamalıdır.
    """
    durum = _onayli(depo)
    durum["claims_registry"] = [
        {"id": "CLM-001", "text": "x", "verification_status": "verified"}
    ]  # kanıtı yok
    _yaz(depo, durum)

    assert cli.cmd_export(Namespace(format="md")) == 1
    assert "kanıtsız" in capsys.readouterr().out


def test_export_her_şey_hazirken_dosya_doker(depo, capsys):
    """Onayli VE metni olan tez gercekten disa aktarilir.

    DRIFT NOTU: bu test once `test_export_her_şey_hazirken_stuba_gecer`
    idi ve yalnizca `== 0` dogruluyordu. Komut o haliyle "Henuz implemente
    edilmedi" yazip 0 donuyor, YANI hicbir sey uretmeden basari
    bildiriyordu. Sarti bilerek degistirildi: simdi cikti dosyasi dogrulanir.
    """
    durum = _onayli(depo)
    durum["chapters"] = [{
        "id": "CH-001",
        "number": 1,
        "title": "B",
        "paragraphs": [{
            "id": "P-001",
            "type": "introduction",
            "text": "Deneme giris metni.",
            "chapter": "CH-001",
        }],
    }]
    _yaz(depo, durum)

    assert cli.cmd_export(Namespace(format="md")) == 0

    cikti = capsys.readouterr().out
    assert "Dışa aktarıldı" in cikti
    dokumler = list(depo.glob("tez_*.md"))
    assert len(dokumler) == 1, f"tek dosya beklenirken: {dokumler}"
    assert "Deneme giris metni." in dokumler[0].read_text(encoding="utf-8")


def test_export_metni_olmayan_tez_reddedilir(depo, capsys):
    """Onayli ama govdesi bos tez BASARILI sayilmaz.

    Onceki surumde bu durum 0 donuyordu ve cikti uretilmiyordu. Kullanicı
    "basarili" ciktisini gorup tesin yayinlanmis sanardi; ortaya cikan
    dosya yalnizca basliklardan ibaret olurdu.
    """
    _onayli(depo)  # bolum var, ama paragraf metni YOK

    assert cli.cmd_export(Namespace(format="md")) == 1
    assert "paragraf" in capsys.readouterr().out
    assert list(depo.glob("tez_*")) == [], "reddedilen export dosya birakti"


# --- cmd_status ------------------------------------------------------------

def test_status_yedi_kapiyi_listeler(depo, capsys):
    """Durum raporu akışı göstermeli; daha önce yalnız sayı yazıyordu."""
    _onayli(depo)
    cli.cmd_status(Namespace())
    cikti = capsys.readouterr().out
    for kapi in ("research_question", "search_strategy", "source_set",
                 "research_gap", "methodology", "findings", "final_thesis"):
        assert kapi in cikti, f"{kapi} raporda yok"
    assert "7/7" in cikti


def test_status_kapili_kapilari_isaretler(depo, capsys):
    _kapili(depo)
    cli.cmd_status(Namespace())
    cikti = capsys.readouterr().out
    assert "0/7" in cikti
    assert "⬜" in cikti


def test_status_ondan_ileri_kapiyi_uyariyle_gosterir(depo, capsys):
    """Bir kapıyı atlarsa akış bozuk; status bunu görünür kılmalı."""
    durum = _kapili(depo)
    durum["human_approvals"]["final_thesis"] = True
    _yaz(depo, durum)

    cli.cmd_status(Namespace())
    cikti = capsys.readouterr().out
    assert "1/7" in cikti
    assert "final_thesis" in cikti
