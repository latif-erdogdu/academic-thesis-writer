# -*- coding: utf-8 -*-
"""Arama adaptörlerinin kaydettiği meta veri kalitesi.

Neden bu test
-------------
Canlı koşuda ölçüldü (2026-09-28): 72 kaynağın 54'ünde `journal` boş,
43'ünde yazar adları `"Ad Soyad (ORCID: xxxx)"` biçimine bulaşmıştı.
İki kusur da doğrulama puanlarını eşiğin ALTINA çekiyordu:

  * ``OpenAlexWork.from_api`` dergiyi yalnızca ``host_venue`` alanından
    okuyor; OpenAlex bu alanı KALDIRDI (belge: verify.py ``_openalex_journal``).
    Yerine ``primary_location.source.display_name`` (ve boşsa ``locations``)
    geliyor. Sonuç: dergi her kayıtta boş → ``journal_match=0.0`` (−0.10).
  * Her iki adaptör de yazar adına ``(ORCID: ...)`` ekliyor; bu string
    bibliyografik normalizasyonu bozuyor (``author_match=0.0``, −0.30) ve
    tez kaynakçasına da yanlış biçimde yansır.

Doğrulama motoru (source_verify) temiz karşılaştırıyor; kirlilik yalnızca
arama adaptörlerinin KAYDETTİĞİ tarafta — düzeltme orada.
"""
from __future__ import annotations

from tools.source_search.crossref import CrossrefWork
from tools.source_search.openalex import OpenAlexWork


def _openalex_item(journal_konum: dict | None = None) -> dict:
    """Kurumsal (canonical biçimdeki) OpenAlex çalışma yanıtı."""
    item = {
        "id": "https://openalex.org/W1234567890",
        "doi": "https://doi.org/10.1234/oznek.2020.001",
        "display_name": "Kekliklerin Hayatta Kalma Orani Uzerine Bir Inceleme",
        "publication_year": 2020,
        "authorships": [
            {"author": {"display_name": "Ayse Yilmaz", "orcid": "https://orcid.org/0000-0001-2345-6789"}}
        ],
        "biblio": {},
    }
    if journal_konum is not None:
        item["primary_location"] = journal_konum
    return item


def test_openalex_journal_primary_locationdan_okunur():
    """`primary_location.source.display_name` dergiye yazılmalı (host_venue değil)."""
    kayit = OpenAlexWork.from_api(_openalex_item(
        {"source": {"display_name": "Biyoloji Dergisi"}}
    )).to_source_dict()

    assert kayit["journal"] == "Biyoloji Dergisi"


def test_openalex_journal_locations_listesine_duser():
    """`primary_location` yoksa `locations` listesindeki ilk kaynak kullanılır."""
    item = _openalex_item(None)
    item["locations"] = [{"source": {"display_name": "Yedek Dergisi"}}]

    kayit = OpenAlexWork.from_api(item).to_source_dict()

    assert kayit["journal"] == "Yedek Dergisi"


def test_openalex_journal_hicbir_konumda_yoksa_bos_kalir():
    """Kurumsal alanların tamamı yoksa dergi boş kalır (uydurma yok)."""
    kayit = OpenAlexWork.from_api(_openalex_item(None)).to_source_dict()

    assert kayit["journal"] == ""


def test_openalex_yazar_adina_orcid_eklenmez():
    """`Ad Soyad (ORCID: ...)` yerine yalnızca temiz görünen ad."""
    kayit = OpenAlexWork.from_api(_openalex_item(
        {"source": {"display_name": "Biyoloji Dergisi"}}
    )).to_source_dict()

    assert kayit["authors"] == ["Ayse Yilmaz"]


def test_crossref_yazar_adina_orcid_eklenmez():
    """`Soyad, Ad (ORCID: ...)` yerine yalnızca temiz `Soyad, Ad`."""
    kayit = CrossrefWork.from_api({
        "DOI": "10.1234/oznek.2020.001",
        "title": ["Kekliklerin Hayatta Kalma Orani Uzerine Bir Inceleme"],
        "author": [{"given": "Ayse", "family": "Yilmaz", "ORCID": "https://orcid.org/0000-0001-2345-6789"}],
        "issued": {"date-parts": [[2020]]},
        "type": "journal-article",
    }).to_source_dict()

    assert kayit["authors"] == ["Yilmaz, Ayse"]