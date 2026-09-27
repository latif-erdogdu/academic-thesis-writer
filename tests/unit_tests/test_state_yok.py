"""Durum dosyasi YOKSA CLI uydurma icerik uretmemeli.

Gorev 7'nin bulgusu
-------------------
`load_state()` dosya yoksa `empty_state(...)` donduruyordu. Bunun dort
somut sonucu vardi:

  1. `status` hic tez olmadigi halde "Tez: THESIS-2026-001 — Yeni Tez" ve
     0/7 kapili diye saglikli bir tez basti.
  2. `audit` bu hayali durumu `save_state()` ile DISKE YAZDI: hic tez
     olmayan bir dizinde `thesis:audit` calistirmak thesis_state.json
     uydurup icine 4 denetim kaydi koyuyordu.
  3. `search` ve `extract` de ayni hayali durum uzerinde calisip dosyayi
     olusturuyordu.
  4. "Tez var ama 0 kaynak" ile "tez dosyasi hic yok" ayirt edilemiyordu.

Ikinci hata, ilkinin tuzagi
---------------------------
Dosya YOK ile dosya BOZUK ayni sey degildir ve tavsiyeleri tam ters:

  yok   -> "thesis:new calistir"      (dogru, veri kaybi yok)
  bozuk -> "DOSYAYI ONARMA, thesis:new CALISTIRMA" (yanlis, veri silinir)

Tek bir hata ile ikisi de "tez yok" sayilsaydi, bozuk dosyasi olan bir
kullaniciya veri kaybiettiren bir komut onerilirdi. Iki durum ayri
sinif olarak ayrilir ve farkli mesaj verir.

Cikis kodlari
-------------
  0  basarili
  1  calisti, sorun buldu (kapali kapı, kritik denetim bulgusu)
  2  hic baslayamadi — tez durumu yok ya da okunamıyor
"""
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from tools.atw.cli import main as cli
from tools.atw.cli.main import BozukTezDurumu, TezYok, load_state
from tools.atw.state import empty_state

# Durum okuyan 7 komut. `cmd_new` listede yok: o durum dosyasini
# YARATTIGI icin once var olmamasi beklenir.
DURUM_OKUYAN = ["search", "verify", "extract", "write", "audit", "status", "export"]


@pytest.fixture
def depo(tmp_path, monkeypatch):
    """CLI'nin depo kokunu gecici bir dizine baglar (semalari dahtan kopyalar)."""
    (tmp_path / "schemas").mkdir()
    for sema in Path("schemas").glob("*.json"):
        (tmp_path / "schemas" / sema.name).write_text(
            sema.read_text(encoding="utf-8"), encoding="utf-8"
        )
    monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
    return tmp_path


def _durum_yaz(depo: Path, durum: dict) -> None:
    (depo / "thesis_state.json").write_text(
        json.dumps(durum, ensure_ascii=False), encoding="utf-8"
    )


def _temsilci(komut: str) -> Namespace:
    """Komutun gercekten ihtiyac duydugu argumanlarla bir Namespace."""
    return {
        "search": Namespace(pico=None, rq="RQ-001", databases="pubmed",
                            year_from=2015, year_to=2026, max_results=5),
        "verify": Namespace(),
        "extract": Namespace(source="SRC-001", claim="CLM-001", pdf="x.pdf"),
        "write": Namespace(chapter="CH-001", rq="RQ-001"),
        "audit": Namespace(type="all"),
        "status": Namespace(),
        "export": Namespace(format="md"),
    }[komut]


# --- load_state sarti ------------------------------------------------------

def test_load_state_dosya_yoksa_tez_yok_hatasi_verir(depo):
    with pytest.raises(TezYok):
        load_state()


def test_tez_yok_dosya_not_found_alt_sinifidir(depo):
    """Jenerik FileNotFoundError yakalayan cagiranlar bozulmamali."""
    assert issubclass(TezYok, FileNotFoundError)


def test_tez_yok_mesaji_yolu_ve_kurulumu_soyler(depo, capsys):
    """Hata mesaji YOLU ve NASIL baslanacagini soylemeli."""
    with pytest.raises(TezYok) as hata:
        load_state()
    mesaj = str(hata.value)
    assert "thesis_state.json" in mesaj
    assert "thesis:new" in mesaj


def test_bozuk_dosya_tez_yok_sayilmaz(depo):
    """BOZUK dosya "tez yok" DEGILDIR: veri orada, sadece okunmuyor.

    Bu ayrim kritik: ikisi birlestirilirse, bozuk dosyasi olan bir
    kullaniciya verisini silen bir komut onerilir.
    """
    (depo / "thesis_state.json").write_text("{bozuk json", encoding="utf-8")
    with pytest.raises(BozukTezDurumu):
        load_state()


def test_bozuk_dosya_mesaji_tei_onarmayi_soyler(depo, capsys):
    """Bozuk dosya icin mesaj ONARMA ister, thesis:new ONERMEZ."""
    (depo / "thesis_state.json").write_text("{bozuk", encoding="utf-8")
    with pytest.raises(BozukTezDurumu) as hata:
        load_state()
    mesaj = str(hata.value)
    assert "thesis:new" not in mesaj, (
        "bozuk dosyada thesis:new onermek veri kaybi yaratir"
    )
    assert "bozuk" in mesaj.lower()


def test_json_olmayan_icerik_bozuk_sayilir(depo):
    """Duzey JSON skemasi degil, tez durumu da olmaz."""
    (depo / "thesis_state.json").write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(BozukTezDurumu):
        load_state()


# --- hicbir komut uydurma icerik uretmemeli -------------------------------

@pytest.mark.parametrize("komut", DURUM_OKUYAN)
def test_durum_yokken_komut_hata_kodu_2_doner(depo, komut):
    """Durum yoksa 2; 0 (basardim) veya 1 (sorun buldum) DEGIL."""
    sonuc = getattr(cli, f"cmd_{komut}")(_temsilci(komut))
    assert sonuc == 2, f"cmd_{komut} durum yokken {sonuc} dondu"


@pytest.mark.parametrize("komut", DURUM_OKUYAN)
def test_durum_yokken_traceback_yok(depo, komut, capsys):
    """Kullaniciya Python yigini gosterilmemeli, mesaj gosterilmeli."""
    getattr(cli, f"cmd_{komut}")(_temsilci(komut))
    cikti = capsys.readouterr().out
    assert "Traceback" not in cikti
    assert "thesis_state.json" in cikti, cikti


def test_durum_yokken_dosya_olusmaz(depo):
    """EN ONEMLI TEST: hicbir komut tez dosyasini UYDURMAMALI.

    Once `cmd_audit` bunu yapiyordu: uydurma durumu save_state() ile
    diske yaziliyor, icine de 4 denetim kaydi konuyordu.
    """
    for komut in DURUM_OKUYAN:
        try:
            getattr(cli, f"cmd_{komut}")(_temsilci(komut))
        except SystemExit:
            pass
    assert not (depo / "thesis_state.json").exists(), (
        "durum yokken thesis_state.json yazildi — CLI tez uydurdu"
    )


def test_status_tez_olmadigini_soyler(depo, capsys):
    """Eski davranis: hic tez yokken 'Tez: THESIS-2026-001 — Yeni Tez' basardi."""
    cli.cmd_status(Namespace())
    cikti = capsys.readouterr().out
    assert "Yeni Tez" not in cikti, cikti
    assert "0/7" not in cikti, cikti


def test_durum_yokken_kapi_denetimi_calismaz(depo, capsys):
    """Onay motoru hayali durum uzerinde calisip kapilari gostermemeli."""
    cli.cmd_status(Namespace())
    assert "kapısı" not in capsys.readouterr().out


# --- normal akis bozulmamali -----------------------------------------------

def test_yeni_tez_dosyasi_olusturunca_status_calisir(depo, capsys):
    """new -> status yolu uçtan uca çalışmalı."""
    assert cli.cmd_new(Namespace(id="THESIS-2026-001", title="Deneme Tezi")) == 0
    assert cli.cmd_status(Namespace()) == 0
    cikti = capsys.readouterr().out
    assert "Deneme Tezi" in cikti
    assert "0/7" in cikti


def test_durum_bozukken_status_2_doner(depo, capsys):
    (depo / "thesis_state.json").write_text("{bozuk", encoding="utf-8")
    assert cli.cmd_status(Namespace()) == 2
    assert "bozuk" in capsys.readouterr().out.lower()


def test_saglam_durum_status_0_doner(depo):
    _durum_yaz(depo, empty_state("THESIS-2026-001", "Deneme Tezi"))
    assert cli.cmd_status(Namespace()) == 0


def test_audit_durum_varken_calisir(depo):
    """Gorev 5'teki denetim motoru bozulmamali."""
    _durum_yaz(depo, empty_state("THESIS-2026-001", "Deneme Tezi"))
    assert cli.cmd_audit(Namespace(type="all")) == 0
    kayitlar = json.loads(
        (depo / "thesis_state.json").read_text(encoding="utf-8")
    )["audit_registry"]
    assert len(kayitlar) == 4


# --- giris noktasi ---------------------------------------------------------

def test_main_durum_yokken_2_doner(depo, monkeypatch):
    """main() hatayi yakalayip 2 donmeli (traceback degil)."""
    monkeypatch.setattr("sys.argv", ["thesis", "status"])
    assert cli.main() == 2


def test_hata_kodu_2_ayri_bir_kodtur():
    """2, hem basari(0) hem sorun(1) kodundan farkli olmali."""
    assert 2 not in (0, 1)
