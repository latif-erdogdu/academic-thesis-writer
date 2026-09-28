"""Kaynak kimlikleri aramalar arasında ÇAKIŞMAMALI.

Neden bu test
-------------
`SystematicSearchOrchestrator.run_systematic_search` dahil edilen
kayıtlara kimlik atarken ARAMA İÇİ SIFIRDAN BAŞLIYORDU:

    for i, record in enumerate(included):
        src_id = format_id("SRC", i + 1)      # search_run.py:219

`format_id` yalnızca numarayı biçimlendirir; mevcut durumu görmez. Oysa
`tools/atw/record.py:231` aynı işi doğru yapar:

    kayit["id"] = next_id(kimlikler + [...], onek)

Ölçülen sonuç (gerçek tez verisi, 3 arama):
  * `sources` içinde 72 kayıt var
  * ayrı (benzersiz) kimlik sayısı **24**
  * her kimlik tam **3** kez geçiyor
  * aynı kimliğin 3 kaydı FARKLI kaynaklar:
        SRC-001 -> 1994 10.2737/feis-species-review-alch
                -> 2024 10.15641/bo.1573
                -> 2016 10.1111/1749-4877.12195

Bunun sonucu sessiz bir veri kaybıdır. Kimlik anahtarlı her eşleme
(`write.py` içindeki `_kimlikle_esles`, `graph.kenar_tablosu`, `verify`
CLI) sözlük kurarken çakışanları üstüne yazar, yalnızca SON kaydı tutar.
Yani 72 kayıt yazıldı, `Dahil edilen: 24` raporlandı, doğrulama ve atıf
yaparken 24'ün son 8'i görünür oldu — hiçbir hata üretilmedi.

Bu test üç aramanın da tek bir durum dosyasına yazdığı gerçek yolu
sürer ve kimliklerin benzersiz kaldığını doğrular.

Ağ YOK: `search_run.search_crossref` / `search_run.search_openalex`
sabit kayıtlarla değiştirilir.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.atw.state import load_state
from tools.source_search import search_run as sr


class _StubWork:
    """`CrossrefWork`/`OpenAlexWork` arayüzünün yeterli taklidi."""

    def __init__(self, doi: str, baslik: str, yil: int, yazar: str = "Yazar, A.") -> None:
        self._d = {
            "id": "",
            "title": baslik,
            "authors": [yazar],
            "year": yil,
            "journal": "Test Dergi",
            "publisher": "Test Yayin",
            "doi": doi,
            "url": f"https://doi.org/{doi}",
            "source_type": "article",
            "publication_status": "published",
            "retraction_status": "not_retracted",
            "correction_status": "none",
            "supersedes_source_id": None,
            "verified": False,
            "verification": {
                "status": "pending",
                "bibliographic_match": 0.0,
                "doi_match": True,
                "author_match": None,
                "title_match": None,
                "year_match": None,
                "journal_match": None,
                "verified_at": "2026-09-28T00:00:00+00:00",
                "verification_sources": ["crossref"],
            },
            "verification_notes": "",
            "supports_claims": [],
            "evidence_ids": [],
            "page_numbers": None,
            "volume": "",
            "issue": "",
            "pages": "",
            "edition": "",
            "isbn": "",
            "location_verified": True,
            "access_date": None,
            "language": "en",
            "peer_reviewed": True,
        }

    def to_source_dict(self) -> dict:
        return dict(self._d)


def _kayitlar(baslangic: int, adet: int) -> list[_StubWork]:
    return [
        _StubWork(f"10.9999/stub.{baslangic + i}", f"Stub Kayit {baslangic + i}", 2000 + i)
        for i in range(adet)
    ]


@pytest.fixture
def sahte_istemciler(monkeypatch):
    """Her çağrıda farklı kayıtlar döndürür (yoksa tekrar dedup olur)."""
    sayac = {"n": 0}

    def _crossref(**kwargs):
        sayac["n"] += 1
        return _kayitlar(sayac["n"] * 100, 3)

    def _openalex(**kwargs):
        sayac["n"] += 1
        return _kayitlar(sayac["n"] * 100 + 50, 3)

    monkeypatch.setattr(sr, "search_crossref", _crossref)
    monkeypatch.setattr(sr, "search_openalex", _openalex)
    return sayac


@pytest.fixture
def bos_durum(tmp_path: Path) -> Path:
    """Geçerli ama boş tez durumu yazar.

    `save_state` semayı DOĞRULAR (state.py:238) — elle yazılan kısmi
    durum reddedilir. Bu yüzden üretici kullanılır.
    """
    from tools.atw.state import empty_state

    yol = tmp_path / "thesis_state.json"
    sr.save_state(str(yol), empty_state("THESIS-TEST-001", "Sinif Testi"))
    return yol


def _kaydet(yol: Path, sonuc: sr.SearchRunResult) -> None:
    sr.SystematicSearchOrchestrator().save_search_run(sonuc, str(yol))


def _ara(yol: Path) -> sr.SearchRunResult:
    sonuc = sr.run_systematic_search(
        pico="pop: Alectoris chukar, outcome: survival mortality",
        databases=["crossref", "openalex"],
        max_results_per_db=10,
        thesis_state_path=str(yol),
    )
    _kaydet(yol, sonuc)
    return sonuc


class TestKimlikCakismasi:
    def test_ucte_arama_kimligi_tekrar_etmez(self, sahte_istemciler, bos_durum):
        """Ölçülen arıza: 3 arama -> 72 kayıt, 24 kimlik, her biri 3 kez."""
        for _ in range(3):
            _ara(bos_durum)

        durum = load_state(str(bos_durum))
        kimlikler = [k["id"] for k in durum["sources"]]

        assert len(kimlikler) == len(set(kimlikler)), (
            f"{len(kimlikler)} kayıtta yalnızca {len(set(kimlikler))} ayrı "
            "kimlik var; kimlik anahtarlı eşleme kayıtların bir kısmını "
            "sessizce yok sayar."
        )

    def test_raporlanan_sayi_yazilan_sayiyle_ortusur(self, sahte_istemciler, bos_durum):
        """`Dahil edilen: N` ile gerçekten eklenen kayıt sayısı aynı olmalı.

        `cmd_search` dahil edilen kümeyi değil, veritabanı başına ham
        kayıtları yazıyordu; fark yalnızca kopya kayıtların boş `id`
        alanı sayesinde görünmüyordu (kazara doğru davranış).
        """
        sonuc = _ara(bos_durum)
        durum = load_state(str(bos_durum))

        assert len(durum["sources"]) == len(sonuc.included_source_ids)
        assert len(durum["sources"]) == sonuc.prisma_flow["studies_included"]

    def test_her_kaydin_kimligi_doludur(self, sahte_istemciler, bos_durum):
        durum = load_state(str(bos_durum))
        bos = [k for k in durum["sources"] if not k.get("id")]
        assert not bos, f"{len(bos)} kayıt kimliksiz yazıldı"


class TestMevcutDurumDevam:
    def test_varolan_kimlikler_yeniden_kullanilmaz(self, sahte_istemciler, bos_durum):
        """Yeni arama mevcut en yüksek numaranın DEVAMI olmalı."""
        durum = load_state(str(bos_durum))
        elle = _StubWork("10.1234/elle", "Elle eklenmis", 2015)._d
        elle["id"] = "SRC-001"
        durum["sources"].append(elle)
        sr.save_state(str(bos_durum), durum)

        _ara(bos_durum)

        durum = load_state(str(bos_durum))
        kimlikler = [k["id"] for k in durum["sources"]]
        assert len(kimlikler) == len(set(kimlikler))
        assert "SRC-001" in kimlikler, "mevcut kayıt silinmemeli"
        assert max(kimlikler, key=lambda k: int(k.split("-")[1])) != "SRC-001", (
            "yeni kayıtlar SRC-001'i tekrar kullanmamalı"
        )

    def test_kimlikler_araya_bolunmez(self, sahte_istemciler, bos_durum):
        """İkinci arama SRC-002..'den başlamamalı, en sonda devam etmeli."""
        _ara(bos_durum)
        ilk = load_state(str(bos_durum))
        onceki_en_yuksek = max(int(k["id"].split("-")[1]) for k in ilk["sources"])

        _ara(bos_durum)
        ikinci = load_state(str(bos_durum))
        yeni = [
            int(k["id"].split("-")[1]) for k in ikinci["sources"]
            if int(k["id"].split("-")[1]) > onceki_en_yuksek
        ]

        assert yeni == list(range(onceki_en_yuksek + 1, onceki_en_yuksek + 1 + len(yeni))), (
            "kimlikler araya bolundu; bosluk bir sonraki kaydi yanlis "
            "numaralandirir"
        )


class TestDahilEdilenKume:
    def test_dahil_edilen_kayitlar_sonucta_tasinir(self, sahte_istemciler, bos_durum):
        """Yazma yolu `included` kümesini kullanmalı, ham listeyi değil.

        Ham liste veritabanı başına kopya içerir; bugün bu kopyalar boş
        `id` alanı yüzünden sessizce düşüyor. Kuralın koda bağlanması,
        ileride bir `id` atanmaya başlarsa kopyaların geri gelmemesini
        sağlar.
        """
        sonuc = _ara(bos_durum)

        assert hasattr(sonuc, "included_records")
        assert len(sonuc.included_records) == len(sonuc.included_source_ids)
        for kayit in sonuc.included_records:
            assert kayit["id"] in sonuc.included_source_ids

    def test_kopya_kayitlar_dahil_edilmez(self, sahte_istemciler, monkeypatch, bos_durum):
        """Aynı kaynak iki veritabanından gelirse BİR kez yazılmalı."""

        ayni = _StubWork("10.1234/ayni", "Ayni Kayit", 2010)

        monkeypatch.setattr(sr, "search_crossref", lambda **kw: [ayni])
        monkeypatch.setattr(sr, "search_openalex", lambda **kw: [ayni])

        sonuc = sr.run_systematic_search(
            pico="pop: Alectoris chukar, outcome: survival",
            databases=["crossref", "openalex"],
            thesis_state_path=str(bos_durum),
        )
        _kaydet(bos_durum, sonuc)

        durum = load_state(str(bos_durum))
        assert len(durum["sources"]) == 1, (
            f"aynı kaynak {len(durum['sources'])} kez yazıldı; PRISMA "
            "'duplicates_removed' diyor ama durumda tekrar var"
        )
