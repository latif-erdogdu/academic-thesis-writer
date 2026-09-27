# -*- coding: utf-8 -*-
"""ASCII yazilmis satirlardaki *tum* farkli kelimeleri listeler.

Girdi: yalnizca diakritiksiz yazilmis Turkce metin satirlari.
Cikti: farkli token listesi + gecis sayisi.

Amac: duzeltme tablosunu *kanita* dayandirmak. Tabloya yalnizca
bu listede gecen, Turkce olup diakritik gerektiren token'lar girer.
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

KUTU = Path(__file__).resolve().parent
DOSYALAR = ["content_a", "content_b", "content_c", "content_d"]

DIAK = set("\u00e7\u0131\u0130\u00f6\u015f\u00fc\u00c7\u011e\u00d6\u015e\u00dc\u00e2\u00ee\u00fb")
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
    sayac: Counter[str] = Counter()
    for ad in DOSYALAR:
        yol = KUTU / f"{ad}.py"
        if not yol.exists():
            continue
        for satir in yol.read_text(encoding="utf-8").splitlines():
            if not _metin_satiri_mi(satir) or (DIAK & set(satir)):
                continue
            for tok in TOKEN.findall(satir):
                sayac[tok] += 1

    sirali = sorted(sayac, key=lambda t: (-sayac[t], t))
    print(f"# farkli token: {len(sirali)}   toplam gecis: {sum(sayac.values())}")
    print("# gecis sayisiyla birlikte, 6'li sutun")
    for i in range(0, len(sirali), 6):
        hucre = [f"{t}({sayac[t]})" for t in sirali[i : i + 6]]
        print("  ".join(f"{h:<18}" for h in hucre))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
