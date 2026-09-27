# -*- coding: utf-8 -*-
"""Diyakritiksiz yazilmis Turkce cumlelerin blok dagilimini olcer.

Kriter: satir Turkce'ye ozgu diakritik icermiyor VE icinde en az
iki ard arda gelen 4+ harfli kucuk kelime var (yani bir cumle ya da
cume parcasi). Yorum satirlari, import/def ve URL satirlari elenir.
"""
from __future__ import annotations

import re
from pathlib import Path

KUTU = Path(__file__).resolve().parent
DOSYALAR = ["content_a", "content_b", "content_c", "content_d"]

DIAK = set("\u00e7\u0131\u0130\u00f6\u015f\u00fc\u00c7\u011e\u0130\u00d6\u015e\u00dc\u00e2\u00ee\u00fb")

TOKEN = re.compile(r"[A-Za-z\u00e7\u0131\u0130\u00f6\u015f\u00fc\u00c7\u011e\u00d6\u015e\u00dc]{2,}")


def _kod_satiri_mi(s: str) -> bool:
    s = s.strip()
    return s.startswith(("#", "def ", "class ", "import ", "from ", "@")) or "http" in s or "doi.org" in s


def _metin_satiri_mi(s: str) -> bool:
    s = s.strip()
    if not s or _kod_satiri_mi(s):
        return False
    return bool(re.search(r"[a-z]{4,}\s+[a-z]{4,}", s))


def main() -> int:
    toplam = 0
    for ad in DOSYALAR:
        yol = KUTU / f"{ad}.py"
        if not yol.exists():
            continue
        satirlar = yol.read_text(encoding="utf-8").splitlines()
        hit = [i for i, s in enumerate(satirlar) if _metin_satiri_mi(s) and not (DIAK & set(s))]
        toplam += len(hit)
        print(f"=== {ad}.py : {len(satirlar)} satir, {len(hit)} ASCII metin satiri")
        # Bloklari birlestir (1 satirlik bosluklar ayni blok sayilir)
        bloklar: list[list[int]] = []
        for no in hit:
            if bloklar and no - bloklar[-1][-1] <= 3:
                bloklar[-1].append(no)
            else:
                bloklar.append([no])
        for b in bloklar:
            print(f"    satir {b[0]+1}-{b[-1]+1}  ({len(b)} satir)")
        print(f"    blok sayisi: {len(bloklar)}")
    print()
    print(f"TOPLAM ASCII metin satiri: {toplam}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
