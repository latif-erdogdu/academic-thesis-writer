# -*- coding: utf-8 -*-
"""tr_diacritics tablosunu ve duzelt() ciktisini denetler.

Denetimler
----------
1. Tablo butunlugu: olu girdi, kimlik eslemesi, buyuk harfli anahtar/deger,
   "dogru yazilan" kelimenin tabloya girmesi.
2. duzelt() idempotentligi: duzelt(duzelt(x)) == duzelt(x).
3. Buyuk harf kuralinin **fikri degistirdigi** her token listelenir; bu liste
   gozle denetlenir (Ingilizce/Roma rakami/yabanci oz ad olmamali).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tr_diacritics as td  # noqa: E402

KAYNAKLAR = ("content_a", "content_b", "content_c", "content_d")


def _metinleri() -> dict[str, str]:
    """Kaynak dosyaların **ham metnini** okur (sadece blok listesi degil)."""
    burada = Path(__file__).resolve().parent
    return {ad: (burada / f"{ad}.py").read_text(encoding="utf-8") for ad in KAYNAKLAR}


def main() -> int:
    metinler = _metinleri()

    print("=" * 72)
    print("1) TABLO BUTUNLUGU")
    print("=" * 72)
    sorunlar = td.denetle_tablo(metinler)
    if sorunlar:
        for s in sorunlar:
            print(f"  [HATA] {s}")
    else:
        print(f"  OK - {len(td.ESLESME)} anahtar, sorun yok.")

    print()
    print("=" * 72)
    print("2) IDEMPOTENS")
    print("=" * 72)
    bozuk = []
    for ad, metin in metinler.items():
        bir = td.duzelt(metin)
        iki = td.duzelt(bir)
        if bir != iki:
            # farkli olan ilk kelimeyi goster
            for a, b in zip(bir.split(), iki.split()):
                if a != b:
                    bozuk.append(f"{ad}: {a!r} -> {b!r}")
                    break
    if bozuk:
        for b in bozuk:
            print(f"  [HATA] idempotent degil: {b}")
    else:
        print("  OK - duzelt(duzelt(x)) == duzelt(x)")

    print()
    print("=" * 72)
    print("3) BUYUK HARF KURALININ DEGISTIRDIGI TOKEN'LAR")
    print("=" * 72)
    # ESLESME'ye girmeyen, yalnizca bas-harf kuraliyla degisen token'lar.
    degisen: dict[str, int] = {}
    for metin in metinler.values():
        korumali = td._KORUNAN_RE.sub("\x00\x00", metin)
        for jeton in td._KELIME_RE.findall(korumali):
            kucuk = jeton.lower()
            if kucuk in td.ESLESME or len(jeton) < 2:
                continue
            hedef = td._jeton_duzelt(jeton)
            if hedef != jeton:
                degisen[jeton] = degisen.get(jeton, 0) + 1
    for jeton, adet in sorted(degisen.items(), key=lambda kv: kv[0].lower()):
        print(f"  {jeton} ({adet})  ->  {td._jeton_duzelt(jeton)}")
    print(f"  toplam: {len(degisen)} farkli jeton")

    return 1 if sorunlar or bozuk else 0


if __name__ == "__main__":
    raise SystemExit(main())
