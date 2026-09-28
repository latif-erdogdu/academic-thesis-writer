"""`kayit.sema_uyumlu`, kayitlardaki bos yazar girdilerini temizlemeli.

Neden bu test
-------------
Gercek bir arama kosusunda (crossref+openalex, RQ-001) durum kapisi bir
kayitta `authors: [""]` yakaladi:

    ValueError: sources/12/authors/0: '' should be non-empty
    (source.json `authors.items` -> `minLength: 1`)

Kaynak: API'ler isimsiz yazar girdisi dondurebiliyor — Crossref'te
`family` ve `given` birlikte bos (`name = ""`), OpenAlex'te
`author.display_name` bos. Bes istemcinin `to_source_dict` ciktisi
`kayit.sema_uyumlu`'dan gectigi icin temizlik burada yapilir:
merkezde tek duzeltme, istemci basina bes kopya degil.

`thesis:search` su durumda kapinin onunde takiliyor: arama sonucu
uretiyor ama yazamiyor. Bu test, sema_uyumlu'dan gecen hicbir kaydin
sema-gecersiz yazar girdisi tasiyamayacagini baglar.
"""
from __future__ import annotations

import pytest

from tools.source_search.kayit import sema_uyumlu

_SIMDI = "2026-09-27T10:00:00+00:00"


def _taban() -> dict:
    return {
        "id": "",
        "title": "Kurgusal kaynak",
        "authors": ["Doe, J."],
        "year": 2020,
        "journal": "",
        "publisher": "",
        "doi": "",
        "url": "",
        "source_type": "article",
        "publication_status": "published",
        "retraction_status": "not_retracted",
        "correction_status": "none",
        "supersedes_source_id": None,
        "verified": False,
        "verification": {
            "status": "pending",
            "bibliographic_match": 0.0,
            "verified_at": _SIMDI,
            "verification_sources": ["crossref"],
        },
    }


def test_bos_yazar_girdileri_atilir() -> None:
    """Bos / yalniz bosluk yazar girdileri listeden dusurer, gerisi kalir."""
    kayit = _taban()
    kayit["authors"] = ["", "   ", "Doe, J.", "Kaya, A."]

    cikti = sema_uyumlu(kayit, simdi=_SIMDI)

    assert cikti["authors"] == ["Doe, J.", "Kaya, A."]


def test_tumu_bos_ise_bos_liste_yazilir() -> None:
    """Tumu bos girdiyse liste bos olur — `[]` semada gecerlidir."""
    kayit = _taban()
    kayit["authors"] = ["", ""]

    cikti = sema_uyumlu(kayit, simdi=_SIMDI)

    assert cikti["authors"] == []


def test_yazar_alan_yoksa_eklenmez() -> None:
    """`authors` anahtari yoksa zorla eklenmemeli (semada zorunlu degil)."""
    kayit = _taban()
    kayit.pop("authors", None)

    cikti = sema_uyumlu(kayit, simdi=_SIMDI)

    assert "authors" not in cikti


def test_sema_uyumlu_ciktisi_semaya_uyar() -> None:
    """Temizlenmis kayit, kapinin (validate_state) gectigi semaya uymali."""
    from tools.atw.state import empty_state, validate_state

    kayit = _taban()
    kayit["authors"] = ["", "Doe, J."]
    cikti = sema_uyumlu(kayit, simdi=_SIMDI)

    durum = empty_state("THESIS-TEST-0001", "Test")
    cikti["id"] = "SRC-001"  # gercek akista next_id atar; sema_uyumlu bos birakir
    durum["sources"] = [cikti]
    hatalar = validate_state(durum)
    assert not hatalar, hatalar