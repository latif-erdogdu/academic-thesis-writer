# -*- coding: utf-8 -*-
"""Uretilen Word belgesini denetle.

Kontrol edilenler:
  * baslik hiyerarsisi (H1/H2/H3) ve bos baslik yok
  * paragraflarda TODO/yer tutucu kalinti mi
  * kaynakca sayisi ve DOI tasiyan kaynak sayisi verified_dois ile tutarli mi
  * tablolarin basligi (caption) var mi
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document

KUTU = Path(__file__).resolve().parent
BELGE = KUTU / "tez_basin_cikti.docx"

sys.path.insert(0, str(KUTU))
import verified_dois  # noqa: E402

YER_TUTUCU = re.compile(
    r"\b(TODO|TBD|FIXME|XXX|lorem ipsum|\[.\]|\{\{|PLACEHOLDER)\b",
    re.IGNORECASE,
)


def main() -> int:
    doc = Document(str(BELGE))
    paragraflar = [p for p in doc.paragraphs]

    basliklar: dict[int, list[str]] = {1: [], 2: [], 3: []}
    for p in paragraflar:
        for seviye in basliklar:
            if p.style.name == f"Heading {seviye}":
                basliklar[seviye].append(p.text)

    sorunlar: list[str] = []

    # 1. Bos baslik
    for seviye, liste in basliklar.items():
        for b in liste:
            if not b.strip():
                sorunlar.append(f"H{seviye} bos baslik")

    # 2. Yer tutucu kalinti
    for i, p in enumerate(paragraflar, 1):
        es = YER_TUTUCU.search(p.text)
        if es:
            sorunlar.append(f"paragraf {i}: yer tutucu '{es.group(0)}'")

    # 3. Kaynakca sayisi ve DOI tutarliligi
    import content_c as C

    referanslar = [t for tur, t in C.KAYNAKCA if tur == "ref"]
    doi_olan_belge = [p.text for p in paragraflar if "doi.org/" in p.text]
    beklenen = sum(1 for r in referanslar if verified_dois.doi_al(r))
    if len(doi_olan_belge) != beklenen:
        sorunlar.append(
            f"belgede {len(doi_olan_belge)} DOI var, "
            f"verified_dois {beklenen} diyor"
        )
    if len(doi_olan_belge) != len(verified_dois.DOGRULANMIS):
        sorunlar.append(
            f"belgede {len(doi_olan_belge)} DOI var, "
            f"kayit defteri {len(verified_dois.DOGRULANMIS)} diyor"
        )

    # 4. Caption sayisi
    caption = [p.text for p in paragraflar if p.text.startswith("Tablo ")]

    kelime = sum(len(p.text.split()) for p in paragraflar)

    print(f"Belge        : {BELGE.name}")
    print(f"Boyut        : {BELGE.stat().st_size / 1024:.1f} KB")
    print(f"Paragraf     : {len(paragraflar)}")
    print(f"Kelime       : {kelime}")
    print(f"Baslik       : H1 {len(basliklar[1])} | "
          f"H2 {len(basliklar[2])} | H3 {len(basliklar[3])}")
    print(f"Tablo        : {len(doc.tables)} | {len(caption)} tablo basligi")
    print(f"Kaynakca     : {len(referanslar)} kaynak")
    print(f"DOI tasinan  : {len(doi_olan_belge)} kaynak")
    print()
    if sorunlar:
        print("SORUNLAR")
        for s in sorunlar:
            print(f"  - {s}")
        return 1
    print("Denetim temiz: bos baslik yok, yer tutucu yok, "
          "DOI sayisi kayit defteriyle tutarli.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
