# -*- coding: utf-8 -*-
"""Kaynak dosyalardaki ASCII Turkce kelime envanterini cikar.

Yalnizca tumuyle kucuk harfli, saf ASCII token'leri toplar; boylece
ozel adlar, kisaltmalar ve teknik terimler elenir. Cikan liste
kucuk oldugu icin gozle denetlenebilir.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

KUTU = Path(__file__).resolve().parent
DOSYALAR = ["content_a", "content_b", "content_c", "content_d"]

TOKEN = re.compile(r"\b[a-z]{3,}\b")
KORUNAN = re.compile(r"https?://|doi\.org|10\.\d{4,9}/|\bRQ-\d{3}\b|\bS-\d{4}\b")


def main() -> int:
    sayac: Counter[str] = Counter()
    dosya_neresi: dict[str, set[str]] = {}
    for ad in DOSYALAR:
        yol = KUTU / f"{ad}.py"
        if not yol.exists():
            continue
        for satir in yol.read_text(encoding="utf-8").splitlines():
            if KORUNAN.search(satir):
                continue
            for tok in TOKEN.findall(satir):
                sayac[tok] += 1
                dosya_neresi.setdefault(tok, set()).add(ad)

    print(f"Toplam farkli saf-kucuk ASCII token: {len(sayac)}")
    print(f"Toplam gecis: {sum(sayac.values())}")
    print()
    for tok, adet in sayac.most_common():
        print(f"{tok}\t{adet}\t{','.join(sorted(dosya_neresi[tok]))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
