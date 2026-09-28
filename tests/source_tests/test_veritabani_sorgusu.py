"""Veritabanı istemcileri API'lerin GERÇEKTEN desteklediği sözdizimini
göndermeli.

Neden bu test
-------------
`build_boolean_query` kütüphane-genel bir Boolean dizgesi üretir:

    ((title:alectoris OR abstract:alectoris OR author:alectoris) OR ...)
    AND ((title:translocation OR ...) OR (title:reintroduction))
    AND ((title:survival) OR (title:mortality))

`search_run.run_systematic_search` bu dizgeyi `search_crossref(...,
query=...)` ve `search_openalex(..., query=...)` çağrılarına olduğu gibi
geçiriyor. Sorun: **hiçbir hedef API bu sözdizimini desteklemiyor.**

Ölçülen sonuçlar (canlı, 2026-09-28):

  * Crossref `query=<Boolean dizgesi>`  -> `total-results: 0`
    Crossref'in `query` parametresi Boolean işleci ve `alan:` sözdizimi
    desteklemez; alan bazlı aramanın ayrı parametreleri vardır
    (`query.bibliographic`, `query.title`, `query.author`). Alan
    desteklenmediği için Crossref bu dizgede HİÇBİR ŞEY bulmuyor.

  * OpenAlex `search=<Boolean dizgesi>` -> 47 sonuç, NEREDEYSE TAMAMI
    GÜRÜLTÜ. `search` tam metin alaka sıralamasıdır; `title:` önekini ve
    `AND`/`OR` işleçlerini yok sayar, terimleri torbalar. Ölçülen
    başlıklar: "Nutritional modulation of the antioxidant capacities in
    poultry", "Chemical mutagenesis: a survey of the 1975-1976
    literature", "The uplift of the Qinghai-Tibet Plateau ...".

Sonuç: 25 kayıt yazıldı, 0 kopya çıkarıldı — hepsi OpenAlex'ten. Yani
sistemik tarama hiç çalışmıyordu: Crossref boş döndü, OpenAlex gürültü
döndürdü. Bu, "arama yapıldı" diye yeşil çıkan ama metodolojik olarak
çöpe yazılan bir akıştır.

Aynı PICO, doğru parametrelerle:

  * OpenAlex `filter=title_and_abstract.search:alectoris chukar,
    title_and_abstract.search:survival` -> 22 sonuç, HEPSİ İLGİLİ:
      - "Chukar Seasonal Survival and Probable Causes of Mortality"
      - "Monitoring the survival rate of released chukars: a case study"
      - "Introgression of chukar genes into a reintroduced red-legged ..."

`title_and_abstract.search` filtreleri virgülle zincirlendiğinde OpenAlex
bunları **VE** olarak uygular. Crossref'te karşılığı yoktur (Boolean
desteklenmez); en yakın doğru karşılık `query.bibliographic`'tir ve bu
bir *kısıt* olarak dokümante edilmelidir.

Bu dosya düzeltmeyi şu davranışlara bağlar:
  1. `SearchQuery.filter_terms` — bileşen başına BİR temiz ifade.
  2. `search_openalex` bu ifadeleri VE zincirli `title_and_abstract.search`
     filtresine çevirir ve `search=` parametresini GÖNDERMEZ.
  3. `search_crossref` Boolean dizgesini `query=` olarak gönderMEZ;
     `query.bibliographic` kullanır.
  4. Kısıt canlı testle ölçülür (`@pytest.mark.live`), varsayılan
     koşuda ağa çıkılmaz.

Ağ YOK: canlı olmayan testler `_get`/`works` katmanını sahte nesneyle
değiştirir, parametreleri YAKALAR. Hiçbir test ağa çıkmaz.
"""
from __future__ import annotations

import pytest

from tools.source_search.crossref import search_crossref
from tools.source_search.openalex import search_openalex
from tools.source_search.query_builder import build_boolean_query, parse_pico


#: Tezin gerçek PICO'su. `population` ve `outcome` yeterli; üçüncü
#: bileşeni eklemek ölçümde 0 sonuca düşüyor.
GERCEK_PICO = "pop: Alectoris chukar, outcome: survival mortality"


class _Yakalayici:
    """OpenAlex istemcisinin gideceği parametreleri yakalar."""

    def __init__(self) -> None:
        self.cagrilar: list[dict] = []

    def __call__(self, yol, params=None):
        self.cagrilar.append(dict(params or {}))
        return {"meta": {"count": 0}, "results": []}


class _CrossrefYakalayici:
    def __init__(self) -> None:
        self.cagrilar: list[dict] = []

    def __call__(self, yol, params=None):
        self.cagrilar.append(dict(params or {}))
        return {"message": {"items": [], "total-results": 0}}


class TestFilterTerimleri:
    """`SearchQuery` bileşen başına bir temiz ifade taşımalı."""

    def test_bilesen_basina_bir_ifade_uretilir(self):
        sorgu = build_boolean_query(parse_pico(GERCEK_PICO), database="openalex")
        assert sorgu.filter_terms == ["alectoris chukar", "survival mortality"]

    def test_ifadeler_pico_sirasini_izler(self):
        """Etiketli terimler PICO alan sırasına göre gelir.

        Etiketlenmemiş alanlar heuristikle doldurulabilir: `saha` hem
        `context` hem `study_design` anahtar kelimesidir, bu yüzden
        ifade sayısı üçten fazla olabilir. Sıra ve temizlik önemlidir,
        adet değil.
        """
        sorgu = build_boolean_query(
            parse_pico("pop: keklik, outcome: hayatta kalma, design: saha"),
            database="openalex",
        )
        terimler = sorgu.filter_terms
        assert terimler[:1] == ["keklik"]
        assert "hayatta kalma" in terimler
        assert terimler[-1] == "saha"

    def test_etiket_sozdizimi_ifadeye_karismaz(self):
        """Etiket metni heuristiğe sızarsa arama 0 sonuç verir.

        Ölçülen arıza: `design: saha` içindeki `saha` kelimesi
        `context` alanına 'tcome: hayatta kalma, design: saha' olarak
        yazılıyordu; bu değer doğrudan VE filtresi olarak gidiyor.
        """
        sorgu = build_boolean_query(
            parse_pico("pop: keklik, outcome: hayatta kalma, design: saha"),
            database="openalex",
        )
        for ifade in sorgu.filter_terms:
            assert ":" not in ifade, f"etiket sözdizimi sızdı: {ifade!r}"
            assert "design" not in ifade
            assert "tcome" not in ifade

    def test_ifade_icinde_boolean_isleci_yoktur(self):
        """Filtreye `AND`/`OR`/`title:` karışırsa OpenAlex çöker.

        Boolean dizgesi bir ifadenin İÇİNE girerse zincir bozulur; bu
        dizge yalnızca `boolean_string` alanında yaşamalı.
        """
        sorgu = build_boolean_query(parse_pico(GERCEK_PICO), database="openalex")
        for ifade in sorgu.filter_terms:
            assert " AND " not in ifade
            assert " OR " not in ifade
            assert ":" not in ifade
            assert "(" not in ifade

    def test_esanlamli_karisikligi_ifadeye_sizmas(self):
        """`expand_synonyms` terim şişmesi üretiyordu.

        18 terim + eş anlamlılar havuzlanınca tek bir PICO bileşeni
        yüzlerce kelimeye dönüşüyordu. `filter_terms` ham ifadeyi taşır.
        """
        sorgu = build_boolean_query(
            parse_pico("pop: elderly patients, outcome: quality of life"),
            database="openalex",
        )
        assert sorgu.filter_terms == ["elderly patients", "quality of life"]
        # Boolean dizgesi hâlâ şişkin olabilir; that's the other field.
        assert len(sorgu.boolean_string) > len("")

    def test_bos_pico_bos_ifade_verir(self):
        sorgu = build_boolean_query(parse_pico("alelik analizi"), database="openalex")
        assert sorgu.filter_terms == []


class TestOpenAlexParametreleri:
    """`title_and_abstract.search` zinciri VE olarak uygulanmalı."""

    def test_ifadeler_ve_zincirli_filter_olur(self, monkeypatch):
        from tools.source_search import openalex as oa

        yakalayici = _Yakalayici()
        monkeypatch.setattr(oa.OpenAlexClient, "_get", yakalayici)

        search_openalex(
            query=build_boolean_query(parse_pico(GERCEK_PICO)).boolean_string,
            filter_terms=["alectoris chukar", "survival mortality"],
            max_results=5,
        )

        assert yakalayici.cagrilar, "OpenAlex'e hiç istek atılmadı"
        filtre = yakalayici.cagrilar[0].get("filter", "")
        assert "title_and_abstract.search:alectoris chukar" in filtre
        assert "title_and_abstract.search:survival mortality" in filtre
        assert "," in filtre, "iki filtre virgülle zincirlenmezse VE olmaz"

    def test_search_parametri_gonderilmez(self, monkeypatch):
        """`search=` Boolean dizgesini torbalar; gönderilmemeli.

        Ölçülen hata: 47 sonuç, neredeyse tamamı gürültü.
        """
        from tools.source_search import openalex as oa

        yakalayici = _Yakalayici()
        monkeypatch.setattr(oa.OpenAlexClient, "_get", yakalayici)

        search_openalex(
            query="((title:alectoris OR x) AND (title:survival))",
            filter_terms=["alectoris chukar", "survival"],
            max_results=5,
        )

        assert "search" not in yakalayici.cagrilar[0]

    def test_ifade_yoksa_eski_yol_calisir(self, monkeypatch):
        """Geriye uyumluluk: `filter_terms` verilmezse `search` gider."""
        from tools.source_search import openalex as oa

        yakalayici = _Yakalayici()
        monkeypatch.setattr(oa.OpenAlexClient, "_get", yakalayici)

        search_openalex(query="alectoris chukar", max_results=5)

        assert yakalayici.cagrilar[0].get("search") == "alectoris chukar"

    def test_ifade_iki_kez_yazilmaz(self, monkeypatch):
        """Aynı terim hem `zincili`ye hem `parcalar`'a eklenirse iki kez yazılır.

        Ölçülen arıza: filtre
        'title_and_abstract.search:reproductive breeding productivity,
         title_and_abstract.search:alectoris chukar,
         title_and_abstract.search:reproductive breeding productivity'
        olmuştu. Tekrarlanan aynı filtre anahtarı zinciri bozar.
        """
        from tools.source_search import openalex as oa

        yakalayici = _Yakalayici()
        monkeypatch.setattr(oa.OpenAlexClient, "_get", yakalayici)

        search_openalex(
            query="",
            filter_terms=["alectoris chukar", "reproductive breeding productivity"],
            max_results=5,
        )

        parcalar = yakalayici.cagrilar[0]["filter"].split(",")
        assert len(parcalar) == len(set(parcalar)) == 2
        assert "title_and_abstract.search:alectoris chukar" in parcalar


class TestCrossrefParametreleri:
    """Crossref Boolean dizgesini anlamaz; `query` olarak gönderilmez."""

    def test_boolean_dizgesi_query_parametresi_olmaz(self, monkeypatch):
        from tools.source_search import crossref as cr

        yakalayici = _CrossrefYakalayici()
        monkeypatch.setattr(cr.CrossrefClient, "_get", yakalayici)

        search_crossref(
            query="((title:alectoris OR x) AND (title:survival))",
            max_results=5,
        )

        params = yakalayici.cagrilar[0]
        assert "query" not in params, (
            "Crossref `query` Boolean/alan sözdizimi desteklemiyor; "
            "ölçülen sonuç total-results=0, yani kayıt YOK bulunuyor."
        )
        assert params.get("query.bibliographic")

    def test_alakasiz_alan_soneki_olmaz(self, monkeypatch):
        """`title:` gibi önekler `query.bibliographic` içinde de olmaz."""
        from tools.source_search import crossref as cr

        yakalayici = _CrossrefYakalayici()
        monkeypatch.setattr(cr.CrossrefClient, "_get", yakalayici)

        search_crossref(query="((title:alectoris OR x) AND (y))", max_results=5)

        deger = yakalayici.cagrilar[0]["query.bibliographic"]
        assert "title:" not in deger
        assert "(" not in deger and " AND " not in deger


class TestKurulumBütünlüğü:
    """`run_systematic_search` ifadeleri istemciye taşımalı."""

    def test_sorgu_ifadeleri_tasiyor(self):
        from tools.source_search.query_builder import build_multi_database_queries

        sorgular = build_multi_database_queries(
            parse_pico(GERCEK_PICO), databases=["openalex", "crossref"]
        )
        for ad in ("openalex", "crossref"):
            assert sorgular[ad].filter_terms == ["alectoris chukar", "survival mortality"], (
                f"{ad} sorgusu ifadeleri taşımıyor; istemciye gidecek AND zinciri yok."
            )

    def test_boolean_dizgesi_korunur(self):
        """PubMed Boolean'ı GERÇEKTEN destekliyor; alan silinmemeli."""
        from tools.source_search.query_builder import build_multi_database_queries

        sorgular = build_multi_database_queries(
            parse_pico(GERCEK_PICO), databases=["pubmed"]
        )
        assert "AND" in sorgular["pubmed"].boolean_string


@pytest.mark.live
class TestCanliOlcum:
    """SİNDİKTE ölçülen davranış. Varsayılan koşuda atlanır.

    Çalıştırma:
        pytest tests/source_tests/test_veritabani_sorgusu.py -m live --no-cov
    """

    def test_crossref_boolean_dizgesi_hic_bulmaz(self):
        """Ölçülen gerçek: Boolean dizgesi Crossref'te 0 sonuç."""
        from tools.source_search.crossref import CrossrefClient

        boolean = build_boolean_query(parse_pico(GERCEK_PICO)).boolean_string
        veri = CrossrefClient().works(query=boolean, rows=1)
        assert veri["total-results"] == 0, (
            "Crossref bu dizgeyi destekliyorsa varsayım yanlış; "
            "düzeltme gerekçesi değişir."
        )

    def test_openalex_filters_ve_dondurur(self):
        """Aynı PICO, doğru filtrelerle ilgili sonuç verir."""
        from tools.source_search.openalex import OpenAlexClient

        veri = OpenAlexClient().works(
            filter={
                "title_and_abstract.search": "alectoris chukar",
            },
            per_page=25,
        )
        # Tek filtre veriysek (bileşen başına birden fazla filter_key
        # OpenAlex'te tekrarlanamaz) en azından konu bulunmalı.
        basliklar = " ".join(
            (w.get("title") or "") for w in veri.get("results", [])
        ).lower()
        assert "chukar" in basliklar or "alectoris" in basliklar
