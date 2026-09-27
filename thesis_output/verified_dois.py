# -*- coding: utf-8 -*-
"""Doğrulanmış DOI kayıtları.

Bu dosya, ``resolve_references.py`` + ``classify.py`` çalıştırıldıktan sonra
gerçekten araç doğrulamasından geçen kaynakları içerir. Kural:

  * araç durumu ``verified`` (eşik 0.60, en az 2 bağımsız kaynak)
  * başlık puanı >= 0.85 ve yıl puanı >= 0.50 (her iki kaynakta)
  * yazar puanı >= 0.60 ve dergi puanı >= 0.25 (her iki kaynakta)

Listede olmayan bir kaynağın DOI'si kaynakçada yazılmaz. Elle yazılmış
ve doğrulanmamış DOI'ler, hiç DOI yazmamaktan daha tehlikelidir; varlıkları
kanıtlanmış görünürler.

Anahtar biçimi: (ilk yazarın soyadı, yıl) -> DOI
"""
from __future__ import annotations

# (soyad, yil) -> doi
DOGRULANMIS: dict[tuple[str, int], str] = {
    ("Altaheri", 2021): "10.1007/s00521-021-06352-5",
    ("Berger", 1929): "10.1007/bf01797193",
    ("Blankertz", 2006): "10.7551/mitpress/7493.003.0008",
    ("Gama", 2014): "10.1145/2523813",
    ("Hochberg", 2006): "10.1038/nature04970",
    ("Hochberg", 2012): "10.1038/nature11076",
    ("Ienca", 2017): "10.1186/s40504-017-0050-1",
    ("Kairouz", 2021): "10.1561/2200000083",
    ("Lawhern", 2019): "10.1088/1741-2552/aace8c",
    ("Mitchell", 2019): "10.1145/3287560.3287596",
    ("Schirrmeister", 2017): "10.1002/hbm.23730",
    ("Shen", 2019): "10.1371/journal.pcbi.1006633",
    ("Vidal", 1973): "10.1146/annurev.bb.02.060173.001105",
}

# Türkçe/aksanlı soyadlar için normalize karşılıklar
_NORMALIZE = str.maketrans({
    "ı": "i", "İ": "I", "ş": "s", "Ş": "S", "ğ": "g", "Ğ": "G",
    "ü": "u", "Ü": "U", "ö": "o", "Ö": "O", "ç": "c", "Ç": "C",
})


def anahtar(referans: str) -> tuple[str, int] | None:
    """Bir kaynakça satırından (soyad, yıl) anahtarını çıkarır."""
    import re

    baslik = re.match(r"^(?P<authors>.+?)\s*\((?P<year>\d{4})\)\.", referans)
    if not baslik:
        return None
    soyad = baslik.group("authors").split(",")[0].strip()
    return (soyad.translate(_NORMALIZE), int(baslik.group("year")))


def doi_al(referans: str) -> str | None:
    """Kaynakça satırına ait doğrulanmış DOI'yi döndürür, yoksa None."""
    a = anahtar(referans)
    if a is None:
        return None
    return DOGRULANMIS.get(a)
