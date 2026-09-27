# -*- coding: utf-8 -*-
"""Hangi tablonun basligi (caption) yok?"""
from __future__ import annotations

import sys
from pathlib import Path

from docx import Document

KUTU = Path(__file__).resolve().parent
BELGE = KUTU / "tez_basin_cikti.docx"
sys.path.insert(0, str(KUTU))

import content_a as A  # noqa: E402
import content_b as B  # noqa: E402
import content_c as C  # noqa: E402

doc = Document(str(BELGE))
print(f"Belgede tablo sayisi: {len(doc.tables)}")

# Blok tanimlarindaki tablo/caption sirasini cikar
sira = []
for blok_adi, blok in (
    ("content_a", A.B1), ("content_a", A.B2), ("content_b", B.B3),
    ("content_b", B.B4), ("content_c", C.B5), ("content_c", C.B6),
    ("content_c", C.SONUC), ("content_c", C.KAYNAKCA), ("content_c", C.EKLER),
):
    for i, el in enumerate(blok):
        if el[0] in ("table", "caption"):
            sira.append((blok_adi, i, el[0],
                         (el[1][0][0] if el[0] == "table" else el[1])[:52]))

print(f"Blok tanimlarinda tablo+caption girdisi: {len(sira)}")
print()
for kaynak, i, tur, ozet in sira:
    print(f"  {tur:<8} {kaynak}[{i:>3}]  {ozet}")

# Her tablonun ardindan caption var mi?
print()
print("Sirayla: her 'table' girdisinden sonraki 'caption' aranir.")
for n, (kaynak, i, tur, ozet) in enumerate(sira):
    if tur != "table":
        continue
    sonraki = sira[n + 1] if n + 1 < len(sira) else None
    ok = sonraki is not None and sonraki[2] == "caption"
    print(f"  {'OK ' if ok else 'EKSIK'}  {ozet[:46]}")
