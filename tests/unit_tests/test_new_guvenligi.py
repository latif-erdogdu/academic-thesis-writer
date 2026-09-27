"""`thesis:new` mevcut bir tezi SESSIZCE EZMEMELI.

Bulgu
-----
`cmd_new` hicbir varlik kontrolu yapmadan `save_state(state)` cagriyordu.
`save_state` de `state_file.write_text(...)` ile yaziyor, yani dosya varsa
ustune yaziliyor. Sonuc:

    python -m tools.atw.cli new THESIS-2026-002 "Yeni Baslik"

komutu, kullanici tezini yanlislikla calistirdiginda (mesela "durumu sifirla"
sekaniyle, ya da ard arda iki kez new yazdiginda) mevcut thesis_state.json'i
sessizce eziyor. Kaynaklar, iddialar, atiflar, onay kayitlari — hepsi gidiyor.
Geri alma yolu yok: `thesis_state.json` izlenen bir dosya degil, ve
uretimde her sey uzerine yaziliyor.

Duzeltme: dosya varsa `thesis:new` reddeder ve hicbir sey yazmaz. Icererek
devam etmek icin `--force` gerekir. Boylece veri kaybi kaza ile olmaz,
kasitli bir kararla olur.

Ayrica BozukTezDurumu ayrimi burada da gecerli: dosya BOZUK olsa bile
`thesis:new` ile ezilmemelidir — bozuk dosyayi onarmak, veriyi silmekten
iyidir.
"""
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from tools.atw.cli import main as cli


@pytest.fixture
def depo(tmp_path, monkeypatch):
    """CLI'nin durum dosyasini gecici bir dizine baglar."""
    monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
    return tmp_path


def _var_tez(depo: Path, kaynak_sayisi: int = 3) -> Path:
    """Dizinde gercek bir tez durumu yazar (kaynaklari olan).

    Sekil `empty_state()` ile ayni olmali: duz yapi, `thesis_id` ve `title`
    ust duzeyde (ic ice `thesis` nesnesi YOK).
    """
    durum = {
        "thesis_id": "THESIS-2026-001",
        "title": "Var olan Tez",
        "sources": [{"id": f"SRC-{i:03d}"} for i in range(1, kaynak_sayisi + 1)],
        "version": 7,
    }
    yol = depo / "thesis_state.json"
    yol.write_text(json.dumps(durum, ensure_ascii=False), encoding="utf-8")
    return yol


def _yeni_args(**ek) -> Namespace:
    return Namespace(id="THESIS-2026-002", title="Yeni Tez", **ek)


# --- 1) ekleme: dosya yoksa calisir ----------------------------------------

def test_tez_yoksa_new_olusturur(depo, capsys):
    """Duz tez durumu yoksa thesis:new calismali (mevcut davranis)."""
    assert cli.cmd_new(_yeni_args()) == 0
    assert (depo / "thesis_state.json").is_file()


def test_olusan_dosya_gecerli_tez_iceriyor(depo):
    """Yeni tez bos ama gecerli olmali (kaynak sayisi 0)."""
    cli.cmd_new(_yeni_args())
    veri = json.loads((depo / "thesis_state.json").read_text(encoding="utf-8"))
    assert veri["thesis_id"] == "THESIS-2026-002"
    assert veri["sources"] == []


# --- 2) EZME KORUMASI: dosya varsa reddet ----------------------------------

def test_tez_varsa_new_reddeder(depo, capsys):
    """Mevcut tez varsa thesis:new SESSIZCE EZMEMELI."""
    _var_tez(depo)
    assert cli.cmd_new(_yeni_args()) != 0, (
        "mevcut tez ezildi; thesis:new veri kaybi uretiyor"
    )


def test_ezme_reddi_veriyi_birakir(depo):
    """En onemli test: reddedildikten sonra dosya BIT BIT ayni kalmali.

    Sadece cikis koduna bakmak yetmez; komut dosyayi hic degistirmemeli.
    """
    yol = _var_tez(depo)
    onceki = yol.read_text(encoding="utf-8")

    cli.cmd_new(_yeni_args())

    assert yol.read_text(encoding="utf-8") == onceki, (
        "thesis:new reddettigi halde dosya degisti"
    )


def test_ezme_reddinde_kaynaklar_korunur(depo):
    """Ezme sonucu olsaydi kaynaklar giderdi; korunmasi gerekir."""
    yol = _var_tez(depo, kaynak_sayisi=5)
    cli.cmd_new(_yeni_args())
    veri = json.loads(yol.read_text(encoding="utf-8"))
    assert len(veri["sources"]) == 5, "kaynaklar silindi"
    assert veri["thesis_id"] == "THESIS-2026-001", "tez degisti"


def test_ezme_reddinde_hata_mesaji_hazir_olmayi_soruyor(depo, capsys):
    """Kullaniciya ne yapacagi soylenmeli: --force."""
    _var_tez(depo)
    cli.cmd_new(_yeni_args())
    cikti = capsys.readouterr().out
    assert "--force" in cikti, (
        f"kullaniciya kacis yolu soylenmedi: {cikti.strip()!r}"
    )


def test_bozuk_dosya_da_ezilmemeli(depo, capsys):
    """BOZUK tez durumu da ezilmemeli.

    Bozuk dosya onarilabilir; uzerine yazmak tek geri alinamaz cozum.
    """
    yol = depo / "thesis_state.json"
    yol.write_text("{bozuk", encoding="utf-8")
    onceki = yol.read_text(encoding="utf-8")

    assert cli.cmd_new(_yeni_args()) != 0, "bozuk tez durumu ezildi"
    assert yol.read_text(encoding="utf-8") == onceki


# --- 3) --force: kasitli ezme ----------------------------------------------

def test_force_ile_ezme_calisir(depo):
    """--force ile kasti ezme yapilabilmeli (cikis yolu kapali olmamali)."""
    _var_tez(depo)
    assert cli.cmd_new(_yeni_args(force=True)) == 0
    veri = json.loads((depo / "thesis_state.json").read_text(encoding="utf-8"))
    assert veri["thesis_id"] == "THESIS-2026-002", "force ezmedi"


def test_force_ile_eski_kaynaklar_gider(depo):
    """--force gercekten yeni durumu yazmali (eski veri kalmamali)."""
    yol = _var_tez(depo, kaynak_sayisi=4)
    cli.cmd_new(_yeni_args(force=True))
    veri = json.loads(yol.read_text(encoding="utf-8"))
    assert veri["sources"] == []


def test_force_yoksa_ozelligi_olsaydi_ve_her_zaman_ezseydi(depo):
    """Tuzak testi: force OLMADAN ezme olmuyorsa burasi gecer."""
    _var_tez(depo)
    # force verilmeden: ezme olmamali
    cli.cmd_new(_yeni_args())
    veri = json.loads((depo / "thesis_state.json").read_text(encoding="utf-8"))
    assert veri["thesis_id"] == "THESIS-2026-001", (
        "force olmadan ezildi — koruma calismiyor"
    )


def test_force_argumani_parserda_tanimli():
    """`--force` komut satirindan da gelebilmeli."""
    parser = cli.build_parser()
    args = parser.parse_args(["new", "THESIS-2026-002", "Yeni Tez", "--force"])
    assert args.force is True, "--force tanimli degil"

    args2 = parser.parse_args(["new", "THESIS-2026-002", "Yeni Tez"])
    assert args2.force is False, "--force varsayilani True olmamali"


def test_force_argumani_temel_olarak_calisir(depo):
    """`--force` verilmeden de komut calismali (geriye donuk uyum)."""
    _var_tez(depo)
    # Namespace'te force hic yok — getattr varsayilani kullanmali
    assert cli.cmd_new(Namespace(id="THESIS-2026-003", title="Baska")) != 0
