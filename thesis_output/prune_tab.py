# -*- coding: utf-8 -*-
"""tr_diacritics.ESLESME'den olu girdileri ve kimlik eslemelerini siler.

Girdi: tr_diacritics.py, cikti: ayni dosya (yedek alinir).
Silme listesi tr_diacritics.denetle_tablo() tarafindan uretilir; boylece
"elle hangi kelime silinir" karari verilmez, kurallar belirler.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

BURADA = Path(__file__).resolve().parent
sys.path.insert(0, str(BURADA))

import tr_diacritics as td  # noqa: E402

KAYNAKLAR = ("content_a", "content_b", "content_c", "content_d")
HEDEF = BURADA / "tr_diacritics.py"

_SATIR_RE = re.compile(r'^(?P<bosluk>\s+)"(?P<anahtar>[^"]+)": "(?P<deger>[^"]+)",\s*$')


def main() -> int:
    metinler = {a: (BURADA / f"{a}.py").read_text(encoding="utf-8") for a in KAYNAKLAR}
    sorunlar = td.denetle_tablo(metinler)

    silinecek: set[str] = set()
    for s in sorunlar:
        m = re.search(r"'([^']+)'", s)
        if m is None:
            print(f"  [UYARI] ayristirilamadi: {s}")
            continue
        silinecek.add(m.group(1))

    kaynak = HEDEF.read_text(encoding="utf-8")
    yeni_satirlar: list[str] = []
    silinen = 0
    baslangic = kaynak.index("ESLESME: dict[str, str] = {")
    bitis = kaynak.index("\n}\n", baslangic)
    satirlar = kaynak.splitlines(keepends=True)
    icinde = False
    for i, satir in enumerate(satirlar):
        if satir.startswith("ESLESME: dict[str, str] = {"):
            icinde = True
            yeni_satirlar.append(satir)
            continue
        if icinde and satir.rstrip("\n") == "}":
            icinde = False
            yeni_satirlar.append(satir)
            continue
        if icinde:
            m = _SATIR_RE.match(satir.rstrip("\n"))
            if m and m.group("anahtar") in silinecek:
                silinen += 1
                continue
        yeni_satirlar.append(satir)
    assert not icinde, "ESLESME blogu kapatilmadi"

    yeni = "".join(yeni_satirlar)
    HEDEF.with_suffix(".py.bak").write_text(kaynak, encoding="utf-8")
    HEDEF.write_text(yeni, encoding="utf-8")

    print(f"  {silinen} satir silindi (istenen: {len(silinecek)} anahtar).")
    print(f"  ESLESME: {len(td.ESLESME)} -> {len(td.ESLESME) - silinen} anahtar")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
