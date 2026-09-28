"""`thesis:search` çıktısı: veritabanı başına kayıt VE kaynak bağlantısı.

Neden bu test
-------------
Gerçek tez koşusunda (D:\\tezler\\chukar-keklik-tez, 3 arama)
`search_runs` kayıtları incelendiğinde iki örtük kusur göründü:

  * `cmd_search` `result.to_dict()` yazıyor — o yalnızca İLK
    veritabanının kaydını döndürür. `--databases crossref,openalex`
    ile çalışan koşulda OpenAlex kaydı SESSİZCE kayboldu: state'te 6
    yerine 3 arama kaydı vardı, üçü de `database: "crossref"` idi.
  * `to_state_records` `included_source_ids`'i her zaman `[]` yazıyor.
    Arama kaydı `studies_included: 30` diyor ama hangi kaynaklar
    dahil, listesi yok. `exclude` (PRISMA tarama kararı) bu bağ
    olmadan çalışamadı: "Hiçbir arama kaydı bu kaynakları dahil
    etmemişti."

Tekilleştirme kaynak nesnelerini korur (`deduplicate_sources` unique'e
REFERANS ekler, kopya üretmez); `record["id"] = SRC-...` ataması o
nesneye işler. Yani dedup'lanmış `included_records` ile ham
`database_results[*].records` listelerinde AYNI dict nesnesi bulunur.
Bu sayede her SRC kimliği doğru veritabanına atfedilebilir (ilk
görüldüğü veritabanına) — per-DB `included_source_ids` ve tutarlı
PRISMA akışı üretilebilir.

Ağ YOK: sahte `run_systematic_search` gerçek bir `SearchRunResult`
döndürür; hiçbir canlı veritabanı çağrısı yapılmaz.
"""
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from tools.atw.cli import main as cli
from tools.atw.state import empty_state, validate_state
from tools.source_search.search_run import (
    DatabaseSearchResult,
    SearchRunResult,
)

DOLAR = chr(36)

#: `parse_pico` yalnızca İngilizce anahtar kelimelere bakar; bu metin
#: boş OLMAYAN PICO üretir (test_search_cli.py ile aynı sabit).
_ARANABILIR_RQ_METNI = (
    "Do released chukar partridges (Alectoris chukar) survive as well as "
    "resident birds during the first three years after release?"
)


@pytest.fixture
def depo(tmp_path, monkeypatch):
    """CLI'nin veri kökünü geçici bir dizine bağlar (şemaları dahtan kopyalar)."""
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


def _kaynak(kimlik: str, doi: str) -> dict:
    return {
        "id": kimlik,
        "title": f"Kurgusal Kaynak {kimlik}",
        "source_type": "article",
        "doi": doi,
        "verification": {
            "status": "pending",
            "bibliographic_match": 0.0,
            "verified_at": "2026-09-28T10:00:00+00:00",
            "verification_sources": ["openalex"],
        },
    }


def _sorgu():
    from tools.source_search.query_builder import build_boolean_query, parse_pico

    pico = parse_pico("pop: Alectoris chukar, outcome: survival")
    return build_boolean_query(pico, database="openalex")


def _bos_dedup():
    from tools.source_search.deduplicate import DedupResult

    return DedupResult(
        unique=[],
        duplicates=[],
        stats={
            "input": 4, "unique": 3, "removed": 1, "by_doi": 1,
            "by_title_author_year": 0, "by_title_only": 0,
        },
    )


def _sonuc() -> SearchRunResult:
    """İki veritabanlı gerçek şekilli bir arama sonucu.

    openalex `k1`, `k2`'yi; crossref `k1KOPYA` (tekilleştirmede düşen
    kopya nesne) ve `k3`'ü döndürür. Dedup açık kopyayı eler:
    `included_records = [k1, k2, k3]`, kimlikler SRC-001..003.
    """
    sorgu = _sorgu()
    k1 = _kaynak("SRC-001", "10.1111/orn.2020.001")
    k2 = _kaynak("SRC-002", "10.1111/orn.2020.002")
    k1_kopya = dict(k1)  # crossref'teki AYNI çalışma (farklı nesne)
    k3 = _kaynak("SRC-003", "10.1111/orn.2020.003")

    return SearchRunResult(
        search_run_id="SEARCH-0002",
        query=sorgu,
        timestamp="2026-09-28T10:00:00+00:00",
        databases_searched=["crossref", "openalex"],
        database_results=[
            DatabaseSearchResult(
                database="crossref", query=sorgu, records_found=2,
                records_returned=2, records=[k1_kopya, k3],
                execution_time_ms=4,
            ),
            DatabaseSearchResult(
                database="openalex", query=sorgu, records_found=2,
                records_returned=2, records=[k1, k2],
                execution_time_ms=5,
            ),
        ],
        prisma_flow={
            "records_identified": 4, "duplicates_removed": 1,
            "records_screened": 3, "records_excluded": 0,
            "reports_sought": 3, "reports_not_retrieved": 0,
            "reports_excluded": 0, "studies_included": 3,
        },
        deduplication=_bos_dedup(),
        included_source_ids=["SRC-001", "SRC-002", "SRC-003"],
        included_records=[k1, k2, k3],
    )


def _durum(depo: Path) -> dict:
    durum = empty_state("THESIS-2026-001", "Deneme Tezi")
    durum["research_questions"] = [{
        "id": "RQ-001",
        "text": _ARANABILIR_RQ_METNI,
        "type": "main",
        "status": "pending",
    }]
    _yaz(depo, durum)
    return durum


def _ns(veritabanlari="crossref,openalex") -> Namespace:
    return Namespace(
        rq="RQ-001", pico=None, databases=veritabanlari,
        year_from=None, year_to=None, max_results=10,
    )


# --- kayıt düzeyi ------------------------------------------------------------

def test_her_veritabani_kaydi_kendi_kimliklerini_tasir():
    """Per-DB kayıt yalnızca O veritabanına atfedilen kimlikleri listemeli.

    `k1` openalex'in ham listesindeki nesnedir (crossref'teki aynı
    çalışmanın kopyası değil) — kimlik ilk görülen veritabanına yazılır.
    """
    kayitlar = {k["database"]: k for k in _sonuc().to_state_records()}

    assert kayitlar["crossref"]["included_source_ids"] == ["SRC-003"]
    assert kayitlar["openalex"]["included_source_ids"] == ["SRC-001", "SRC-002"]


def test_per_db_akis_sayilari_ve_baglanti_ortusur():
    """`studies_included` her kayıtta kendi `included_source_ids` kadar olmalı.

    PRISMA akışı: `records_screened = duplicates_removed + studies_included`
    ve `reports_sought = reports_excluded + studies_included` denklikleri
    ayri ayri tutar; aksi durumda `exclude`'un yeniden türetimi kesirli
    kalır. Kopya nesne (k1_kopya) hiçbir yerde çift sayılmaz.
    """
    kayitlar = {k["database"]: k for k in _sonuc().to_state_records()}
    toplam = 0

    for db in ("crossref", "openalex"):
        kayit = kayitlar[db]
        akis = kayit["prisma_flow"]
        dahil = len(kayit["included_source_ids"])

        assert akis["studies_included"] == dahil
        assert akis["records_screened"] == dahil, (
            f"{db}: tarama sonrası dahil sayısı listedekilerle uyuşmuyor"
        )
        assert akis["reports_sought"] == dahil
        assert (
            akis["records_identified"]
            == akis["duplicates_removed"] + akis["records_screened"]
        ), f"{db}: tanımlanan = elenen + taranan bozuldu"

        toplam += dahil

    assert toplam == len(_sonuc().included_source_ids), (
        "kopya nesneler çift sayıldı ya da bir kayıt hiçbir veritabanına "
        "atfedilmedi"
    )


# --- CLI düzeyi --------------------------------------------------------------

def test_cmd_search_per_db_kayitlarini_ve_kaynagi_yazar(depo, monkeypatch, capsys):
    """`to_dict` (ilk DB) yerine TÜM DB kayıtları ve dedup'lu kaynaklar yazılmalı.

    Ölçülen kusur: 3 arama -> 3 kayıt, hepsi crossref; OpenAlex'in
    kayıtları yoktu. Ayrıca kaynak kümesi yalnızca `included_records`'u
    (tekilleştirilmiş) içermeli — ham liste kopya taşır.
    """
    _durum(depo)
    monkeypatch.setattr(
        "tools.source_search.run_systematic_search", lambda **kwargs: _sonuc()
    )

    assert cli.cmd_search(_ns()) == 0

    durum = _oku(depo)
    kayitlar = durum["search_runs"]
    assert [k["database"] for k in kayitlar] == ["crossref", "openalex"], (
        "iki veritabanlı koşu yalnızca ilk veritabanının kaydını taşıyor"
    )
    assert sorted(
        kimlik for k in kayitlar for kimlik in k["included_source_ids"]
    ) == ["SRC-001", "SRC-002", "SRC-003"], (
        "arama kayıtları kaynaklarla bağlantılı değil"
    )
    assert sorted(k["id"] for k in durum["sources"]) == [
        "SRC-001", "SRC-002", "SRC-003"
    ], "kopya kayıt kaynak kümesine yazıldı"
    assert not validate_state(durum), "durum şemaya uymuyor"
    capsys.readouterr()


def test_cmd_search_kimlik_cakismasinda_yazmaz(depo, monkeypatch, capsys):
    """Kimlik çakışması sessiz veri kaybıdır; hiçbir şey yazılmamalı.

    Arama, durumdaki kimlikleri görmezse `next_id` SRC-001'den başlar;
    kimlik anahtarlı eşleme yalnızca son kaydı tutar. Durum önceden
    SRC-001 içeriyorsa çakışma vardır — yazmadan reddet.
    """
    durum = _durum(depo)
    durum["sources"] = [_kaynak("SRC-001", "10.9999/mevcut.001")]
    _yaz(depo, durum)
    onceki = _oku(depo)
    monkeypatch.setattr(
        "tools.source_search.run_systematic_search", lambda **kwargs: _sonuc()
    )

    assert cli.cmd_search(_ns()) == 1

    cikti = capsys.readouterr().out
    assert "SRC-001" in cikti
    assert _oku(depo) == onceki, "çakışmada durum değiştirildi"