# -*- coding: utf-8 -*-
"""Diyakritiksiz yazilmis Turkce cumleleri tespit et.

Kriter: satir icinde Turkce'ye ozgu ASCII karakterlerden biri
var (c, g, o, s, u, i, h, r, k, l, a, d, e, m, n, t, b, y, z, p, v, f)
ve satirda HICBIR Turkce diakritigi (c-g-i-o-s-u + buyukleri)
bulunmuyor. Boylece hem diakritikli hem ASCII yazilan serbest
karmalarla degil, tamamen ASCII yazilmis satirlarla ilgileniriz.
"""
from __future__ import annotations

import re
from pathlib import Path

KUTU = Path(__file__).resolve().parent
DOSYALAR = ["content_a", "content_b", "content_c", "content_d"]

DIAK = set("çğıöşüÇĞİÖŞÜâîû")
# Turkce metin sinyalleri: buyuk harfli baslangicli ozel ad degil,
# cümle ortasinda gorulen ve neredeyse sadece Turkce'de bulunan
# ek/olayim yapilari.
SINYAL = re.compile(
    r"\b(lar|ler|leri|lari|nin|dan|den|ile|ci|ci|si|s[iı]\b|"
    r"inde|indan|unu|unu|ildi|ildi\b|ecek|acak|malı|mısı|"
    r"gibi|olan|olarak|ancak|fakat|veya|ise|idi|edil|"
    r"var|yok|sonra|önce|arası|için|değil|oldu|olur|"
    r"bulun|eden|ederek|nasıl|neden|hangi|kaç|"
    r"tüm|bütün|ancak|olarak|göre|üzere|sonuç|"
    r"kadar|beri|mu|mi|ya|da|ve)\b"
)


def main() -> int:
    toplam = 0
    for ad in DOSYALAR:
        yol = KUTU / f"{ad}.py"
        if not yol.exists():
            continue
        satirlar = yol.read_text(encoding="utf-8").splitlines()
        for no, satir in enumerate(satirlar, 1):
            s = satir.strip()
            if not s or DIAK & set(s):
                continue
            if "http" in s or "doi.org" in s or s.startswith(("#", "def ", "class ", "import ", "from ")):
                continue
            # Yalnizca metin parcalarini ele al
            if not re.search(r"[a-z]{3,}\s+[a-z]{3,}", s):
                continue
            if not SINYAL.search(s):
                continue
            toplam += 1
            print(f"--- {ad}.py:{no}")
            print(s)
    print()
    print(f"TOPLAM: {toplam} satir")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
