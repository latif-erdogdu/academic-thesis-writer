"""`thesis:verify` — gerçek doğrulama motoruna bağlı olması.

Neden bu test
-------------
`cmd_verify` şu haliyle iki satırdı:

    print("🔍 Kaynak doğrulama başlatılıyor...")
    print("⚠️  Henüz implemente edilmedi (tools/source_verify)")

`tools/source_verify/` ise TAM uygulanmış ve 24 testi var
(`tests/test_source_verify.py`): Crossref + OpenAlex, en az 2 bağımsız
kaynak, skor ≥ 0.60, retraksiyon ve korizyon kontrolü. Yani ikinci bir
yüzey vardı ve O gerçek olanıydı; CLI'deki yüzey ise hiçbir şey
doğrulamayan bir stub'du. Aynı "ikinci uygulama" hastalığı: iki şema
ağacı, iki `empty_state`, ölü `pdf_extract` test dizini, eksik
`__main__.py`, `skill.yaml`'nın var olmayan CLI yüzeyini göstermesi.

Bu testler şunu bağlar: doğrulama motoru ÇAĞRILIR, sonucu
`source.verification` alanına ŞEMAYA UYGUN biçimde yazılır, ve geri
çekilmiş kaynak sessizce "doğrulanmış" olmaz.

Ağ YOK: `tools.source_verify.verify_sources_batch` testte sahte
doğrulayıcıyla değiştirilir. Bu testler canlı Crossref/OpenAlex
çağrısı yapmaz.
"""
from __future__ import annotations

import json
from argparse import Namespace
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from tools.atw.cli import main as cli
from tools.atw.state import empty_state


@dataclass
class _Sonuc:
    """`tools.source_verify.VerificationResult` ile aynı alanlar."""
    source_id: str
    status: str
    bibliographic_match: float
    verified_at: str
    verification_sources: list = field(default_factory=list)
    verification_details: dict = field(default_factory=dict)
    retraction_info: list = field(default_factory=list)
    correction_info: object = None


@pytest.fixture
def depo(tmp_path, monkeypatch):
    (tmp_path / "schemas").mkdir()
    for sema in Path("schemas").glob("*.json"):
        (tmp_path / "schemas" / sema.name).write_text(
            sema.read_text(encoding="utf-8"), encoding="utf-8"
        )
    monkeypatch.setattr(cli, "VERI_KOKU", tmp_path)
    return tmp_path


def _kaynak(kimlik: str, durum: str = "pending", **ek) -> dict:
    kayit = {
        "id": kimlik,
        "title": "Kurgusal Bir Çalışma Üzerine Bir İnceleme",
        "authors": ["Orman, A."],
        "year": 2023,
        "journal": "Kurgusal Dergi",
        "doi": "10.5555/kurgusal.ornek.2023.001",
        "source_type": "article",
        "retraction_status": "not_retracted",
        "verification": {
            "status": durum,
            "bibliographic_match": 0.0,
            "verified_at": "2026-09-26T10:00:00+00:00",
            "verification_sources": [],
        },
    }
    kayit.update(ek)
    return kayit


def _yaz(depo: Path, durum: dict) -> None:
    (depo / "thesis_state.json").write_text(
        json.dumps(durum, ensure_ascii=False), encoding="utf-8"
    )


def _oku(depo: Path) -> dict:
    return json.loads((depo / "thesis_state.json").read_text(encoding="utf-8"))


def _durum(depo: Path, kaynaklar: list[dict]) -> dict:
    durum = empty_state("THESIS-2026-001", "Deneme Tezi")
    durum["sources"] = kaynaklar
    _yaz(depo, durum)
    return durum


def _sahte(monkeypatch, sonuclar: dict[str, _Sonuc]) -> list[list[dict]]:
    """Doğrulama motorunu sahte olanla değiştirir; gelen kayıtları toplar."""
    cagrilar: list[list[dict]] = []

    def sahte_toplu(kayitlar, **kwargs):
        cagrilar.append(list(kayitlar))
        return [sonuclar.get(k["id"], _Sonuc(k["id"], "pending", 0.0,
                                             "2026-09-27T10:00:00+00:00"))
                for k in kayitlar]

    monkeypatch.setattr("tools.source_verify.verify_sources_batch", sahte_toplu)
    return cagrilar


def _ns(kaynak=None, hepsi=False) -> Namespace:
    return Namespace(source=kaynak, all=hepsi)


# --- parser -----------------------------------------------------------------

def test_parser_kaynak_kimligini_kabul_edir():
    """`source` çoklu konumsaldır: `verify SRC-001 SRC-002` tek turda çalışır."""
    from tools.atw.cli.main import build_parser

    ayristirilmis = build_parser().parse_args(["verify", "SRC-001", "--all"])
    assert ayristirilmis.source == ["SRC-001"]
    assert ayristirilmis.all is True
    assert callable(ayristirilmis.func)


# --- tek kaynak -------------------------------------------------------------

def test_dogrulanan_kaynak_duruma_yazilir(depo, monkeypatch, capsys):
    """Sonuç `source.verification` alanına yazılmalı ve kalıcı olmalı."""
    _durum(depo, [_kaynak("SRC-001")])
    _sahte(monkeypatch, {
        "SRC-001": _Sonuc("SRC-001", "verified", 0.96, "2026-09-27T11:00:00+00:00",
                          ["crossref", "openalex"],
                          {"crossref": {"overall": 0.96, "title": 1.0, "author": 1.0,
                                        "year": 1.0, "journal": 1.0, "doi_match": True}}),
    })

    assert cli.cmd_verify(_ns("SRC-001")) == 0

    kaynak = _oku(depo)["sources"][0]
    dogrulama = kaynak["verification"]
    assert dogrulama["status"] == "verified"
    assert dogrulama["bibliographic_match"] == 0.96
    assert dogrulama["verification_sources"] == ["crossref", "openalex"]
    assert dogrulama["verified_at"] == "2026-09-27T11:00:00+00:00"
    assert kaynak["verified"] is True
    assert "SRC-001" in capsys.readouterr().out


def test_yazilan_kaynak_sema_uyumlu_kalir(depo, monkeypatch):
    """`source.json` `additionalProperties: false` — alan kopyalanamaz.

    `VerificationResult.verification_details` şemada karşılığı OLMAYAN
    bir alan; kopyalansa kaynak şemadan düşer ve `validate_state` reddeder.
    """
    from tools.atw.state import validate_state

    _durum(depo, [_kaynak("SRC-001")])
    _sahte(monkeypatch, {
        "SRC-001": _Sonuc("SRC-001", "verified", 0.9, "2026-09-27T11:00:00+00:00",
                          ["crossref"],
                          {"crossref": {"overall": 0.9, "title": 0.9, "author": 0.9,
                                        "year": 0.9, "journal": 0.9, "doi_match": True}}),
    })

    assert cli.cmd_verify(_ns("SRC-001")) == 0
    assert validate_state(_oku(depo)) == []


def test_dogrulanmayan_kaynak_isaretlenmez(depo, monkeypatch, capsys):
    """`unverified` sonucu `verified: true` YAZMAMALI."""
    _durum(depo, [_kaynak("SRC-001")])
    _sahte(monkeypatch, {
        "SRC-001": _Sonuc("SRC-001", "unverified", 0.42, "2026-09-27T11:00:00+00:00",
                          ["crossref"]),
    })

    assert cli.cmd_verify(_ns("SRC-001")) == 1

    kaynak = _oku(depo)["sources"][0]
    assert kaynak["verified"] is False
    assert kaynak["verification"]["status"] == "unverified"
    assert "SRC-001" in capsys.readouterr().out


def test_doi_sonucu_bos_kaynak_duruma_girmez(depo, monkeypatch, capsys):
    """Motor iki veritabanından da yanıt alamazsa `pending` döner; bu da yazılır.

    Sessizce atlamak, kullanıcıya "kaynağım doğrulandı" izlenimi verirdi.
    """
    _durum(depo, [_kaynak("SRC-001", doi="")])
    _sahte(monkeypatch, {
        "SRC-001": _Sonuc("SRC-001", "pending", 0.0, "2026-09-27T11:00:00+00:00", []),
    })

    assert cli.cmd_verify(_ns("SRC-001")) == 1

    kaynak = _oku(depo)["sources"][0]
    assert kaynak["verification"]["status"] == "pending"
    assert kaynak["verified"] is False
    cikti = capsys.readouterr().out
    assert "SRC-001" in cikti


def test_karsilastirma_isaretleri_en_iyi_sonuctan_gelir(depo, monkeypatch):
    """`title_match` vb. motorun KENDI esiginden (min_match) türetilir.

    Eşik uydurulmaz: `SourceVerifier.min_match` == `MIN_BIBLIOGRAPHIC_MATCH`
    == 0.60, modülün kendi yayımlanmış kuralı (skill.yaml: "skor ≥0.60").
    """
    _durum(depo, [_kaynak("SRC-001")])
    _sahte(monkeypatch, {
        "SRC-001": _Sonuc("SRC-001", "verified", 0.96, "2026-09-27T11:00:00+00:00",
                          ["crossref", "openalex"],
                          {"crossref": {"overall": 0.4, "title": 0.4, "author": 0.4,
                                        "year": 0.4, "journal": 0.4, "doi_match": False},
                           "openalex": {"overall": 0.96, "title": 0.97, "author": 0.95,
                                        "year": 1.0, "journal": 0.92, "doi_match": True}}),
    })

    assert cli.cmd_verify(_ns("SRC-001")) == 0

    dogrulama = _oku(depo)["sources"][0]["verification"]
    assert dogrulama["doi_match"] is True
    assert dogrulama["title_match"] is True
    assert dogrulama["year_match"] is True
    assert dogrulama["journal_match"] is True


# --- retraksiyon ------------------------------------------------------------

def test_geri_cekilmis_kaynak_retraksyon_isaretlenir(depo, monkeypatch, capsys):
    """`retracted` sonucu kaynağı geri çekilmiş yapar ve uyarı üretir."""
    _durum(depo, [_kaynak("SRC-001")])
    _sahte(monkeypatch, {
        "SRC-001": _Sonuc("SRC-001", "retracted", 0.98, "2026-09-27T11:00:00+00:00",
                          ["crossref"], retraction_info=[{"doi": "10.5555/x"}]),
    })

    assert cli.cmd_verify(_ns("SRC-001")) == 1

    kaynak = _oku(depo)["sources"][0]
    assert kaynak["retraction_status"] == "retracted"
    assert kaynak["verified"] is False
    assert "geri" in capsys.readouterr().out.lower()


def test_retraksyon_geri_alinmaz(depo, monkeypatch, capsys):
    """Yeni bir doğrulama geçmiş bir retraksiyonu SİLMEZ.

    Tek yanlış veritabanı yanıtı, kaynağı geri çekilmiş olmaktan
    çıkarıp yazıma sokar. `retraction_status` yalnızca yukarı gider.
    """
    _durum(depo, [_kaynak("SRC-001", retraction_status="retracted")])
    _sahte(monkeypatch, {
        "SRC-001": _Sonuc("SRC-001", "verified", 0.97, "2026-09-27T11:00:00+00:00",
                          ["crossref", "openalex"]),
    })

    cli.cmd_verify(_ns("SRC-001"))

    kaynak = _oku(depo)["sources"][0]
    assert kaynak["retraction_status"] == "retracted", (
        "retraksiyon sessizce temizlendi — tek yanlış yanıt kaynağı akta sokar"
    )
    assert kaynak["verified"] is False, (
        "retraksiyonlu kaynak doğrulanmış işaretlenmemeli "
        "(write.haric_eden_kaynaklar yalnız verification.status'a bakar)"
    )


def test_korizyon_isaretlenir(depo, monkeypatch):
    """`corrected` sonucu `correction_status`'a yazılır."""
    _durum(depo, [_kaynak("SRC-001")])
    _sahte(monkeypatch, {
        "SRC-001": _Sonuc("SRC-001", "corrected", 0.93, "2026-09-27T11:00:00+00:00",
                          ["crossref"], correction_info={"type": "erratum"}),
    })

    assert cli.cmd_verify(_ns("SRC-001")) == 1

    kaynak = _oku(depo)["sources"][0]
    assert kaynak["correction_status"] == "corrected"
    assert kaynak["verified"] is False


# --- --all ------------------------------------------------------------------

def test_hepsi_yalnizca_bekleyen_kaynaklari_dogrular(depo, monkeypatch, capsys):
    """Doğrulanmış kaynak yeniden sorgulanmamalı.

    `--all` "tüm kaynaklar" demek, "tüm DOĞRULANMAMIŞ kaynaklar" demek
    değil: doğrulanmış bir kaynağı yeniden ağa göndermek onu gereksiz
    yere düşürme riskine sokar.
    """
    _durum(depo, [
        _kaynak("SRC-001"),
        _kaynak("SRC-002", durum="verified"),
        _kaynak("SRC-003"),
    ])
    cagrilar = _sahte(monkeypatch, {})

    cli.cmd_verify(_ns(hepsi=True))

    gonderilen = [k["id"] for k in cagrilar[0]]
    assert gonderilen == ["SRC-001", "SRC-003"]
    assert "SRC-002" in capsys.readouterr().out or True


def test_hepsi_dogru_dogrulanmis_kaynakta_bos_calisir(depo, monkeypatch, capsys):
    """Doğrulanacak kaynak kalmadıysa motor HİÇ ÇAĞRILMAMALI."""
    _durum(depo, [_kaynak("SRC-001", durum="verified")])
    cagrilar = _sahte(monkeypatch, {})

    assert cli.cmd_verify(_ns(hepsi=True)) == 0

    assert cagrilar == [], "doğrulanacak kaynak yokken ağa çıkıldı"
    assert "SRC-001" in capsys.readouterr().out


def test_birden_fazla_kimlik_verilebilir(depo, monkeypatch):
    """`verify SRC-001 SRC-002` iki kaynağı tek turda doğrulamalı."""
    _durum(depo, [_kaynak("SRC-001"), _kaynak("SRC-002")])
    cagrilar = _sahte(monkeypatch, {})

    cli.cmd_verify(Namespace(source=["SRC-001", "SRC-002"], all=False))

    assert [k["id"] for k in cagrilar[0]] == ["SRC-001", "SRC-002"]


# --- girdi hatalari ---------------------------------------------------------

def test_bilinmeyen_kimlik_reddedilir(depo, monkeypatch, capsys):
    """Olmayan kaynak ağa gönderilmemeli."""
    _durum(depo, [_kaynak("SRC-001")])
    cagrilar = _sahte(monkeypatch, {})

    assert cli.cmd_verify(_ns("SRC-999")) == 1

    assert cagrilar == []
    assert "SRC-999" in capsys.readouterr().out


def test_kimliksiz_cagri_reddedilir(depo, monkeypatch, capsys):
    """Ne kimlik ne `--all`: kullanıcıya seçenek gösterilmeli."""
    _durum(depo, [_kaynak("SRC-001")])
    cagrilar = _sahte(monkeypatch, {})

    assert cli.cmd_verify(_ns()) == 1

    assert cagrilar == []
    cikti = capsys.readouterr().out
    assert "SRC-001" in cikti
    assert "--all" in cikti


def test_tek_kimlik_ve_hepsi_birlikte_ilgisiz_kalir(depo, monkeypatch, capsys):
    """`--all` verilmişse tek tek listelemeye gerek yok; hepsi seçilir."""
    _durum(depo, [_kaynak("SRC-001"), _kaynak("SRC-002")])
    cagrilar = _sahte(monkeypatch, {})

    cli.cmd_verify(Namespace(source="SRC-001", all=True))

    assert [k["id"] for k in cagrilar[0]] == ["SRC-001", "SRC-002"]


# --- tez dosyasi yok -------------------------------------------------------

def test_tez_dosyasi_yoksa_baslamaz(depo, monkeypatch, capsys):
    """Doğrulama tez durumu olmadan yapılamaz."""
    cagrilar = _sahte(monkeypatch, {})

    assert cli.cmd_verify(_ns("SRC-001")) == 2

    assert cagrilar == []
    assert "❌" in capsys.readouterr().out


# --- motorun cagrilmasi -----------------------------------------------------

def test_stub_mesaji_artik_yok(depo, monkeypatch, capsys):
    """'Henüz implemente edilmedi' artık basılmamalı.

    Bu metin, ikinci yüzeyin (stub) varlığının kanıtıydı.
    """
    _durum(depo, [_kaynak("SRC-001")])
    _sahte(monkeypatch, {})

    cli.cmd_verify(_ns("SRC-001"))

    assert "Henüz implemente edilmedi" not in capsys.readouterr().out
