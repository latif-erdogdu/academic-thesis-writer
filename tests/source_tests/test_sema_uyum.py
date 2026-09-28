"""Arama katmanının ürettiği kayıtlar `schemas/` ile UYUMLU olmalı.

Neden bu test
-------------
`CrossrefWork.to_source_dict` docstring'i şunu vaat ediyor:

    \"\"\"source.json şemasına uygun dict'e dönüştür.\"\"\"

Vaat yanlıştı. Gerçek tez verisinde ölçüldü — `thesis:search` üç kez
çağrıldıktan sonra `validate_state` **312 hata** döndürdü:

    153 ×  None is not of type 'string'      (journal/volume/issue/pages)
     72 ×  '' is not of type 'date'          (access_date)
     72 ×  '' is not of type 'date-time'     (verification.verified_at)
     12 ×  search_run kaydı (4 ayrı ihlal)

Ve bu hatalar **sessizce** yazıldı: `tools/atw/cli/main.py:213` içindeki
`save_state` düz `write_text` ile yazıyor, doğrulama yapmıyor. Kütüphane
yolundaki `tools/atw/state.py:238 save_state` ise doğruluyor ve
`ValueError` fırlatıyor. Yani CLI kendi şemasını atlayan tek yol.

Sonuç: tez durumu 312 hatalıydı ve kimse bilmiyordu. `audit` bunu
görmez çünkü kayıtlar diske çoktan yazılmıştı.

Kök neden `source.json` alan sözleşmesiyle `to_source_dict` arasındaki
uyumsuzluk:

  * `journal`, `volume`, `issue`, `pages` şemada **`string`**; kod
    `None` yazıyordu.
  * `access_date` şemada `date` ya da `null`; kod `""` yazıyordu.
  * `verification.verified_at` şemada **zorunlu** `date-time`; kod `""`
    yazıyordu.

Beş istemcinin (`crossref`, `openalex`, `semantic_scholar`, `pubmed`,
`google_scholar`) `to_source_dict` metodu aynı hataları aynı biçimde
üretiyor; bu yüzden düzeltme ortak bir yardımcıda yapılır.

Ağ YOK: `from_api` yalnızca verilen sözlüğü okur.
"""
from __future__ import annotations

import pytest

from tools.atw.state import load_schema, schema_registry, _FORMAT_CHECKER

CROSSREF_ITEM = {
    "DOI": "10.1234/oznek.2020.001",
    "title": ["Kekliklerin Hayatta Kalma Orani Uzerine Bir Inceleme"],
    "author": [{"given": "Ayse", "family": "Yilmaz"}],
    "issued": {"date-parts": [[2020]]},
    "type": "journal-article",
    "URL": "https://doi.org/10.1234/oznek.2020.001",
    # volume / issue / page / container-title YOK: en sık görülen durum
    # (salt metin kaydı) ve asıl hata yeri. `journal` bu yüzden None.
}

OPENALEX_ITEM = {
    "id": "https://openalex.org/W1234567890",
    "doi": "https://doi.org/10.1234/oznek.2020.001",
    "title": "Kekliklerin Hayatta Kalma Orani Uzerine Bir Inceleme",
    "publication_year": 2020,
    "type": "article",
    "authorships": [
        {"author": {"display_name": "Ayse Yilmaz"}}
    ],
    "primary_location": {"source": {"display_name": "Test Dergisi"}},
    "biblio": {},  # volume/issue/first_page yok
}


def _dogrucuyu_uret(sema_adi: str):
    from jsonschema import Draft202012Validator

    return Draft202012Validator(
        load_schema(sema_adi),
        registry=schema_registry(),
        format_checker=_FORMAT_CHECKER,
    )


def _hatalar(sozdegecici, kayit: dict) -> list[str]:
    return [
        f"{'/'.join(str(p) for p in hata.path) or '<kok>'}: {hata.message}"
        for hata in sorted(sozdegecici.iter_errors(kayit), key=lambda h: list(h.path))
    ]


class TestKayitSemayaUygun:
    """Her istemcinin `to_source_dict` çıktısı `source.json`'a uymalı.

    `to_source_dict` kimliksiz (öncü) bir kayıt döndürür; `id` alanını
    arama koordinatörü doldurur. Bu yüzden sözleşme "kimlik atandıktan
    SONRA geçerli"dir — `id: ''` deseniyle zaten eşleşmez.
    """

    def test_crossref_kaydi_gecerli(self):
        from tools.source_search.crossref import CrossrefWork

        kayit = CrossrefWork.from_api(dict(CROSSREF_ITEM)).to_source_dict()
        kayit["id"] = "SRC-001"

        assert _hatalar(_dogrucuyu_uret("source.json"), kayit) == []

    def test_openalex_kaydi_gecerli(self):
        from tools.source_search.openalex import OpenAlexWork

        kayit = OpenAlexWork.from_api(dict(OPENALEX_ITEM)).to_source_dict()
        kayit["id"] = "SRC-001"

        assert _hatalar(_dogrucuyu_uret("source.json"), kayit) == []

    def test_doi_ciplak_bicimde_yazilir(self):
        """OpenAlex DOI'yi URL olarak döndürür; şema çıplak form ister.

        Önek kalırsa kayıt geçersiz olur ve `verify` (DOI eşleşmesi
        yapar) hedefi bulamaz — sessizce "eşleşmedi" sonucu doğar.
        """
        from tools.source_search.openalex import OpenAlexWork

        kayit = OpenAlexWork.from_api(dict(OPENALEX_ITEM)).to_source_dict()

        assert kayit["doi"] == "10.1234/oznek.2020.001"
        assert not kayit["doi"].startswith("http")

    def test_eksik_alanlar_yok_edilmez(self):
        """`journal`/`volume`/... gelmediyse anahtar KALIR, `None` olmaz.

        Semada bu alanlar zorunlu değil; `None` yazmak "bilinmiyor" ile
        "boş" arasında yanlış tip üretiyordu. Anahtarı düşürmek yerine
        boş dize yazılır, çünkü `edition`/`isbn`/`publisher` zaten bu
        geleneği kullanıyor ve `record` yolu da aynı şekli üretiyor.
        """
        from tools.source_search.crossref import CrossrefWork

        kayit = CrossrefWork.from_api(dict(CROSSREF_ITEM)).to_source_dict()

        for alan in ("journal", "volume", "issue", "pages"):
            assert alan in kayit, f"{alan} anahtarı kayboldu"
            assert kayit[alan] == "", f"{alan} None yerine boş dize olmalı"

    def test_access_date_bos_dize_degil(self):
        """`''` `date` formatını sağlamaz; erişim yoksa `null`."""
        from tools.source_search.crossref import CrossrefWork

        kayit = CrossrefWork.from_api(dict(CROSSREF_ITEM)).to_source_dict()

        assert kayit["access_date"] is None

    def test_dogrulanma_zamani_gecerli(self):
        """`verified_at` zorunlu ve `date-time` olmalı; `''` değil."""
        from tools.source_search.crossref import CrossrefWork

        kayit = CrossrefWork.from_api(dict(CROSSREF_ITEM)).to_source_dict()

        assert kayit["verification"]["verified_at"], "verified_at bos olamaz"

    def test_bilinmeyen_anahtar_yok(self):
        """`additionalProperties: false` — sızan anahtar kaydı geçersiz kılar."""
        from tools.source_search.crossref import CrossrefWork

        kayit = CrossrefWork.from_api(dict(CROSSREF_ITEM)).to_source_dict()
        izinli = set(load_schema("source.json")["properties"])

        fazla = sorted(set(kayit) - izinli)
        assert not fazla, f"semada olmayan anahtarlar: {fazla}"


class TestAramaKaydiSemayaUygun:
    """`SearchRunResult` -> durum kaydı `search_run.json`'a uymalı."""

    def _sonuc(self):
        from tools.source_search.query_builder import parse_pico
        from tools.source_search.search_run import (
            DatabaseSearchResult,
            SearchRunResult,
        )
        from tools.source_search.query_builder import build_boolean_query

        pico = parse_pico("pop: Alectoris chukar, outcome: survival")
        sorgu = build_boolean_query(pico, database="openalex")
        kayit = {
            "id": "SRC-001",
            "title": "Ornek Kayit",
            "authors": ["Yazar, A."],
            "year": 2020,
            "source_type": "article",
            "verification": {
                "status": "pending",
                "bibliographic_match": 0.0,
                "verified_at": "2026-09-28T00:00:00+00:00",
                "verification_sources": ["openalex"],
            },
        }
        return SearchRunResult(
            search_run_id="SEARCH-001",
            query=sorgu,
            timestamp="2026-09-28T00:00:00+00:00",
            databases_searched=["openalex", "crossref"],
            database_results=[
                DatabaseSearchResult(
                    database="openalex", query=sorgu, records_found=10,
                    records_returned=10, records=[kayit], execution_time_ms=5,
                ),
                DatabaseSearchResult(
                    database="crossref", query=sorgu, records_found=8,
                    records_returned=8, records=[dict(kayit)], execution_time_ms=4,
                ),
            ],
            prisma_flow={
                "records_identified": 18, "duplicates_removed": 1,
                "records_screened": 17, "records_excluded": 0,
                "reports_sought": 17, "reports_not_retrieved": 0,
                "reports_excluded": 0, "studies_included": 17,
            },
            deduplication=_bos_dedup(),
            included_source_ids=["SRC-001"],
        )

    def test_her_veritabani_icin_kayit_uretilir(self):
        """Şema tanımı: 'Tek bir veritabanında çalıştırılan tek bir arama'.

        İki veritabanlı bir koşu tek kayda sıkıştırılırsa hangi
        veritabanının kaç kayıt döndürdüğü denetlenemez. Kayıtlar
        veritabanı başına ayrılmalı.
        """
        kayitlar = self._sonuc().to_state_records()

        assert [k["database"] for k in kayitlar] == ["openalex", "crossref"]

    def test_kayitlar_gecerli(self):
        dogrulayici = _dogrucuyu_uret("search_run.json")

        for kayit in self._sonuc().to_state_records():
            hatalar = _hatalar(dogrulayici, kayit)
            assert hatalar == [], f"{kayit.get('database')}: {hatalar}"

    def test_sonuc_sayisi_veritabanindan_gelir(self):
        """`results_returned` toplam değil, o veritabanının kendi sayısı."""
        kayitlar = {k["database"]: k for k in self._sonuc().to_state_records()}

        assert kayitlar["openalex"]["results_returned"] == 10
        assert kayitlar["crossref"]["results_returned"] == 8

    def test_eski_tek_kayit_yontemi_kullanilmiyor(self):
        """`deduplication_stats` şemada yok; `to_dict` sürdürmemeli."""
        assert "deduplication_stats" not in self._sonuc().to_dict()

    def test_tek_veritabanli_kosuda_kayit_sayisi_bir(self):
        """Kayıt sayısı `database_results` uzunluğudur.

        `databases_searched` İSTEĞİ kaydeder (hangi veritabanları
        soruldu), `database_results` ise gerçekte ne döndüğü. Arama
        bir veritabanında hata verse bile sonuç kaydı üretildiği için
        ikisi ayrışabilir; kayıt sayısı GERÇEKTEN döneni izlemelidir.
        """
        sonuc = self._sonuc()
        sonuc.database_results = sonuc.database_results[:1]
        sonuc.databases_searched = ["openalex"]

        assert len(sonuc.to_state_records()) == 1


def _bos_dedup():
    from tools.source_search.deduplicate import DedupResult

    return DedupResult(
        unique=[],
        duplicates=[],
        stats={
            "input": 0, "unique": 0, "removed": 0,
            "by_doi": 0, "by_title_author_year": 0, "by_title_only": 0,
        },
    )
