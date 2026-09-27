"""Tez durumu dosyasi KULLANICININ calisma dizininde olmali, skill deposunda degil.

Bulgu
-----
`main.py` durum dosyasi yolunu `REPO_ROOT` uzerinden kuruyordu:

    REPO_ROOT = Path(__file__).resolve().parents[3]   # skill'in kurulu oldugu depo
    state_file = REPO_ROOT / "thesis_state.json"

Bu, CLI'yi hangi dizinden calistirirsaniz calistirin hep skill'in kendi
deposuna yaziyor/okuyor. Olculebilir sonuc (gecici dizinden calistirilmis):

    $ cd gecici_dizin && python -m tools.atw.cli status
    ❌ thesis_state.json bulunamadı: D:\\...\\academic-thesis-writer\\thesis_state.json

CWD'de gecici_dizin/thesis_state.json olmamasina ragmen, CLI orada degil
skill deposunu aradi. Yani:

  1. Kullanici tezini skill'in bulundugu dizinde degil, kendi proje
     dizininde yazmak istiyor; CLI baska yere yaziyor.
  2. `thesis:new` calistirmak skill'in GIT DEPOSUNU kirletir — skill'i
     guncellediginizde veri gitmisse (ya da stash/checkout ile) tez kaybolur.
  3. `thesis_state.json` izlenen bir dosya olmadigi icin bu veri
     versiyon kontrolunden hicbir yerde kurtarilamaz.

Ayrica bu, isimlendirme hatasiydi: `main.py` icinde `REPO_ROOT` yalnizca
veri yolu icin kullaniliyordu. Skill'in kurulum kokune hicbir sey ihtiyac
var (semalar `tools.atw.state.SCHEMA_DIR`'den gelir). Yani sabit dogru
isaret ediyor, yanlis ise yariyordu.

Duzeltme
--------
Tek dogruluk kaynagi `veri_koku()`: varsayilan `Path.cwd()`, testler ve
ileride `--state` icin modul seviyesinde `VERI_KOKU` uzerinden
ayrilabilir. Hicbir komut dogrudan `REPO_ROOT` kullanmaz.

Bu bir sozlesme degisikligidir: 5 test dosyasi `cli.REPO_ROOT`'a
monkeypatch ile veri kokunu yonlendiriyordu, artik `cli.VERI_KOKU`
 kullanir. Testlerin IDDIALARI degismedi — yalnizca veri yazma noktasi
degistigi icin yonlendirme hedefi degisti. Atlanan test sayisi degismedi.
"""
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from tools.atw.cli import main as cli
from tools.atw.state import empty_state


# --- 1) tek dogruluk kaynagi ------------------------------------------------

def test_veri_koku_calisma_dizini(tmp_path, monkeypatch):
    """Varsayilan veri koku calisma dizini olmali."""
    monkeypatch.chdir(tmp_path)
    assert cli.veri_koku() == tmp_path


def test_veri_koku_cagri_aninda_cozulur(tmp_path, monkeypatch):
    """Yol modul yuklenirken degil, CAGRI ANINDA cozumlenmeli.

    Yoksa `os.chdir` calisma aninda yapildiginda yanlis yere yazilir.
    """
    diger = tmp_path / "diger"
    diger.mkdir()
    monkeypatch.chdir(diger)
    assert cli.veri_koku() == diger


def test_veri_koku_ayri_ayrilabilir(tmp_path, monkeypatch):
    """VERI_KOKU verildiginde calisma dizini yoksayilmali (test/ileri kullanim)."""
    monkeypatch.chdir(tmp_path)
    hedef = tmp_path / "tez"
    hedef.mkdir()
    monkeypatch.setattr(cli, "VERI_KOKU", hedef)
    assert cli.veri_koku() == hedef


def test_durum_dosyasi_adi_sabit():
    """Dosya adi tek yerde tanimli olmali (sihirli metin dagilmasin)."""
    assert cli.DURUM_DOSYASI == "thesis_state.json"
    assert cli.durum_yolu().name == cli.DURUM_DOSYASI


def test_durum_yolu_veri_kokunun_icine_duser():
    """durum_yolu = veri_koku + dosya adi."""
    assert cli.durum_yolu() == cli.veri_koku() / cli.DURUM_DOSYASI


# --- 2) hicbir komut REPO_ROOT'u veri yolu olarak kullanmamali ------------

def test_durum_yolu_uzerine_repo_root_yazmiyor(tmp_path, monkeypatch):
    """GUVENLIK: cozumleme skill'in kurulum kokunu ADRESLEMESIN.

    Adreslesiydi, CWD degistiginde bile hep skill deposuna yazardi —
    yani bu testin konusu olan hata aynen surerdi.
    """
    monkeypatch.chdir(tmp_path)
    skill_koku = Path(cli.__file__).resolve().parents[3]
    assert cli.durum_yolu() != skill_koku / cli.DURUM_DOSYASI or tmp_path == skill_koku


# --- 3) uctan uca: gecici dizinde calisiyor mu? ----------------------------

def test_new_gecici_dizine_yazar(tmp_path, monkeypatch, capsys):
    """thesis:new calisma dizinindeki thesis_state.json'u yazmali."""
    monkeypatch.chdir(tmp_path)
    assert cli.cmd_new(Namespace(id="THESIS-2026-001", title="Deneme")) == 0
    assert (tmp_path / "thesis_state.json").is_file()


def test_status_gecici_dizindeki_tezi_okur(tmp_path, monkeypatch, capsys):
    """status, calisma dizinindeki tezi okumali (skill deposunu degil)."""
    monkeypatch.chdir(tmp_path)
    cli.cmd_new(Namespace(id="THESIS-2026-001", title="Deneme Tezi"))
    capsys.readouterr()

    assert cli.cmd_status(Namespace()) == 0
    cikti = capsys.readouterr().out
    assert "Deneme Tezi" in cikti, f"dogru tez okunmadi: {cikti.strip()!r}"


def test_save_state_calisma_dizinine_yazar(tmp_path, monkeypatch):
    """save_state dogrudan cagrilsa da calisma dizinini kullanmali."""
    monkeypatch.chdir(tmp_path)
    cli.save_state(empty_state("THESIS-2026-001", "Tez"))
    assert (tmp_path / "thesis_state.json").is_file()


def test_iki_dizin_ayri_ayri_calisiyor(tmp_path, monkeypatch):
    """Iki farkli calisma dizini birbirinin verisini GORMEMELI.

    CWD'ye baglanmanin asil nedeni bu: iki proje ayni anda birbirinden
    bagimsiz olmali.
    """
    proje_a = tmp_path / "a"
    proje_b = tmp_path / "b"
    proje_a.mkdir()
    proje_b.mkdir()

    monkeypatch.chdir(proje_a)
    cli.cmd_new(Namespace(id="THESIS-A-001", title="Proje A"))
    monkeypatch.chdir(proje_b)
    cli.cmd_new(Namespace(id="THESIS-B-001", title="Proje B"))

    a = json.loads((proje_a / "thesis_state.json").read_text(encoding="utf-8"))
    b = json.loads((proje_b / "thesis_state.json").read_text(encoding="utf-8"))
    assert a["thesis_id"] == "THESIS-A-001"
    assert b["thesis_id"] == "THESIS-B-001"


def test_teyit_tez_durumunu_gormez(tmp_path, monkeypatch):
    """Baska dizindeki tez, calisma dizininden gorunmemeli."""
    teyit = tmp_path / "teyit"
    teyit.mkdir()
    (teyit / "thesis_state.json").write_text(
        json.dumps({"thesis_id": "THESIS-TEYIT", "title": "Teyit", "sources": []}),
        encoding="utf-8",
    )

    calisma = tmp_path / "calisma"
    calisma.mkdir()
    monkeypatch.chdir(calisma)

    with pytest.raises(cli.TezYok):
        cli.load_state()


# --- 4) --pdf yolu da calisma dizinine gore cozumlenmeli -------------------

def test_nispi_yol_calisma_dizinine_cozulur(tmp_path, monkeypatch):
    """--pdf gibi nispi yollar skill deposuna degil calisma dizinine baglanir."""
    monkeypatch.chdir(tmp_path)
    assert cli._cozumle("makale.pdf") == tmp_path / "makale.pdf"


def test_mutlak_yola_dokunulmaz(tmp_path, monkeypatch):
    """Mutlak yol oldugu gibi birakilmali (cwd'den bagimsiz)."""
    monkeypatch.chdir(tmp_path)
    mutlak = tmp_path / "makale.pdf"
    assert cli._cozumle(str(mutlak)) == mutlak
