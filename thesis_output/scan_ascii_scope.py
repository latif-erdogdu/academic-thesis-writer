# -*- coding: utf-8 -*-
"""Yalnizca ASCII yazilmis satirlardaki kelimeleri listele.

Bu, gercekten Turkce diakritigi gerektiren kelimelerin kapsamini
olcer; 257 satirlik bolge disinda kalan Turkce metin zaten
diyakritikli.
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

KUTU = Path(__file__).resolve().parent
DOSYALAR = ["content_a", "content_b", "content_c", "content_d"]

DIAK = set("çğıöşüÇĞİÖŞÜâîû")
TOKEN = re.compile(r"[A-Za-zçğıöşüÇĞİÖŞÜâîû]{2,}")
SINYAL = re.compile(
    r"\b(lar|ler|leri|lari|nin|dan|den|ile|ci|si|in|inde|"
    r"unu|ildi|ecek|acak|malı|mısı|gibi|olan|olarak|"
    r"ancak|fakat|veya|ise|idi|edil|var|yok|sonra|"
    r"arası|için|degil|oldu|olur|bulun|eden|ederek|"
    r"nasıl|neden|hangi|tüm|bütün|göre|üzere|"
    r"sonuç|kadar|beri|mu|mi|ya|da|ve)\b"
)


def main() -> int:
    sayac: Counter[str] = Counter()
    for ad in DOSYALAR:
        yol = KUTU / f"{ad}.py"
        if not yol.exists():
            continue
        for satir in yol.read_text(encoding="utf-8").splitlines():
            s = satir.strip()
            if not s or DIAK & set(s):
                continue
            if "http" in s or "doi.org" in s or s.startswith(("#", "def ", "class ", "import ", "from ")):
                continue
            if not re.search(r"[a-z]{3,}\s+[a-z]{3,}", s):
                continue
            if not SINYAL.search(s):
                continue
            for tok in TOKEN.findall(s):
                sayac[tok] += 1

    # Yalnizca tamamen ASCII olanlar: bunlar duzeltme adayi olabilir
    ascii_tok = {t: n for t, n in sayac.items() if not (DIAK & set(t))}
    print(f"Bu 257 satirda farkli token: {len(sayac)}")
    print(f"Bunlarin saf ASCII olani  : {len(ascii_tok)}")
    print(f"Toplam gecis (ASCII)     : {sum(ascii_tok.values())}")
    print()
    sirali = sorted(ascii_tok, key=lambda t: (-ascii_tok[t], t))
    print("--- 8'li sutun ---")
    for i in range(0, len(sirali), 8):
        print("  ".join(sirali[i : i + 8]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
