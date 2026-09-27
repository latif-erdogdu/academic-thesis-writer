"""cmd_audit'un durumu gercekten yazdigi ve dogru cikis kodu verdigi.

tools/atw/cli/main.py kapsam disi oldugu icin (bkz. .coveragerc) buradaki
denetim mantigi test edilemez; burada yalnizca CLI KATMANI sinanir:
kayitlari duruma yaziyor mu, desteklenmeyen turu acikca bildiriyor mu,
kritik bulgu varsa hata kodu donuyor mu.
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
    """CLI'nin veri kokunu gecici bir dizine baglar (semalari dahtan kopyalar)."""
    (tmp_path / "schemas").mkdir()
    for sema in Path("schemas").glob("*.json"):
        (tmp_path / "schemas" / sema.name).write_text(
            sema.read_text(encoding="utf-8"), encoding="utf-8"
        )
    monkeypatch.setattr(cli, "VERI_KOKU", tmp_path)
    return tmp_path


def _bos_durum(depo: Path) -> dict:
    durum = empty_state("THESIS-2026-001", "Deneme Tezi")
    (depo / "thesis_state.json").write_text(
        json.dumps(durum, ensure_ascii=False), encoding="utf-8"
    )
    return durum


def _oku(depo: Path) -> dict:
    return json.loads((depo / "thesis_state.json").read_text(encoding="utf-8"))


def test_audit_denetim_kayitlarini_duruma_yazar(depo, capsys):
    """Denetim sonucu audit_registry'ye eklenmeli (yazilmazsa denetim kaybolur)."""
    _bos_durum(depo)
    assert cli.cmd_audit(Namespace(type="all")) == 0

    kayitlar = _oku(depo)["audit_registry"]
    assert kayitlar, "denetim calisti ama hicbir kayit yazilmadi"
    assert {k["audit_type"] for k in kayitlar} == {
        "citation",
        "integrity",
        "evidence",
        "methodology",
    }


def test_audit_kayitlari_semaya_gecer(depo):
    """Yazilan kayitlar schemas/audit.json'a uymali."""
    _bos_durum(depo)
    cli.cmd_audit(Namespace(type="all"))

    import jsonschema

    sema = json.loads((depo / "schemas" / "audit.json").read_text(encoding="utf-8"))
    dogrulayici = jsonschema.Draft202012Validator(sema)
    for kayit in _oku(depo)["audit_registry"]:
        dogrulayici.validate(kayit)


def test_audit_tek_tur_secilir(depo):
    """--type verildiginde YALNIZCA o tur calismali."""
    _bos_durum(depo)
    cli.cmd_audit(Namespace(type="integrity"))
    assert [k["audit_type"] for k in _oku(depo)["audit_registry"]] == ["integrity"]


def test_audit_tekrarlanan_calistirmada_kimlik_cakismaz(depo):
    """Ayni denetimi iki kez calistirmak ayni AUD kimligini uretmemeli."""
    _bos_durum(depo)
    cli.cmd_audit(Namespace(type="integrity"))
    cli.cmd_audit(Namespace(type="integrity"))

    kimlikler = [k["audit_id"] for k in _oku(depo)["audit_registry"]]
    assert len(kimlikler) == len(set(kimlikler)), kimlikler


def test_audit_kritik_bulgu_durumda_hata_kodu_doner(depo, capsys):
    """Kopuk referans varsa cikis kodu 1 olmali (CI gate'i olarak calisabilmeli)."""
    durum = _bos_durum(depo)
    durum["citations"] = [
        {"id": "CIT-001", "source_id": "SRC-999", "style": "apa7",
         "in_text_form": "(Yazar, 2020)"}
    ]
    (depo / "thesis_state.json").write_text(
        json.dumps(durum, ensure_ascii=False), encoding="utf-8"
    )

    assert cli.cmd_audit(Namespace(type="integrity")) == 1
    assert "kritik" in capsys.readouterr().out.lower()


def test_audit_temiz_durumde_sifir_kodu_doner(depo):
    """Bulgu yoksa cikis kodu 0 olmali (sessizce gecmis sayilmamali)."""
    _bos_durum(depo)
    assert cli.cmd_audit(Namespace(type="all")) == 0


def test_audit_desteklenmeyen_turu_sessizce_atlamaz(depo, capsys):
    """consistency desteklenmiyor; kullaniciya acikca bildirilmeli.

    Sessizce gecmek, denetlenmemis bir alani denetlenmis gosterirdi.
    """
    _bos_durum(depo)
    assert cli.cmd_audit(Namespace(type="consistency")) == 0

    cikti = capsys.readouterr().out
    assert "consistency" in cikti
    assert not _oku(depo)["audit_registry"], "denetlenmeyen tur icin kayit yazilmamali"


def test_audit_tur_yoksa_tum_denetimler_calisir(depo):
    """--type verilmediginde her sey denetlenmeli."""
    _bos_durum(depo)
    cli.cmd_audit(Namespace(type=None))
    assert len(_oku(depo)["audit_registry"]) == 4
