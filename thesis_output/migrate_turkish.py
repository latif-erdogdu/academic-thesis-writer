# -*- coding: utf-8 -*-
"""Turkce diakritik duzeltmesini KAYNAK dosyalara bir kez uygular.

Neden kaynaga uyguluyoruz?
-------------------------
Metin, belge uretim aninda degil, **kaynakta** duzeltilir. Boylece
belgeyi ureten kodde gizli bir "duzeltme" adimi kalmaz; cikti dosyasi tek
basina okundugunda da metin dogru yazimdadir. Bir kez calistirilir, sonra
silinebilir.

Neden yalnizca dize sabitlerinin icine?
--------------------------------------
`tr_diacritics.ESLESME` icinde `"is": "is"` turu Turkce kelimeler var
("is" -> "iş", "in" -> "için"). Bunlar Python **anahtar kelimeleri** ve
**tanimlayicilariyla** da carpisir:

    TESEKKUR = [...]          # content_d.py:145

Dosyanin tamamini duzeltmek bu tanimlayiciyi "TEŞEKKÜR" yapar ve modulu
bozar. Bu yuzden yalnizca `tokenize` ile tespit edilen STRING token'larinin
**ic govdeleri** duzeltilir; kod, yorum, tanimlayici ve import satirlari
harf harf korunur.

Guvence
-------
* Uygulama **idempotenttir**: ikinci calistirmada degisiklik olmaz.
* `--denetle` yalnizca raporlar, dosyaya yazmaz.
* Islemden sonra dosyalar Python'da derlenir (ast.parse) ve guncellenmis
  metin esit metinle karsilastirilir (bkz. `dogrula`).
"""
from __future__ import annotations

import argparse
import ast
import io
import sys
import tokenize
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tr_diacritics as td  # noqa: E402

BURADA = Path(__file__).resolve().parent
HEDEFLER = ("content_a.py", "content_b.py", "content_c.py", "content_d.py")


# --------------------------------------------------------------------------
# STRING token'larinin tam (satir, sutun) araligini bul
# --------------------------------------------------------------------------
def _string_araliklari(kaynak: str) -> list[tuple[int, int, int, int, str]]:
    """Kaynaktaki STRING token'larini ham govde metniyle birlikte dondurur.

    Donus listesi: ``(satir, bas_sutun, bitis_satir, bitis_sutun, ham)``.
    """
    araliklar: list[tuple[int, int, int, int, str]] = []
    with io.StringIO(kaynak) as akis:
        for tok in tokenize.generate_tokens(akis.readline):
            if tok.type != tokenize.STRING:
                continue
            bas_sat, bas_sut = tok.start
            bit_sat, bit_sut = tok.end
            # tokenize bazi durumlarda satir sonunu (sat+1, 0) olarak verir
            if bit_sat == bas_sat:
                ham = kaynak.splitlines(keepends=True)[bas_sat - 1][bas_sut:bit_sut]
            else:
                satirlar = kaynak.splitlines(keepends=True)
                parcalar = [satirlar[bas_sat - 1][bas_sut:]]
                parcalar.extend(satirlar[bas_sat: bit_sat - 1])
                parcalar.append(satirlar[bit_sat - 1][:bit_sut])
                ham = "".join(parcalar)
            araliklar.append((bas_sat, bas_sut, bit_sat, bit_sut, ham))
    return araliklar


def _dize_uzerinde(kaynak: str) -> str:
    """Yalnizca STRING token'larinin ic govdelerine ``duzelt`` uygular."""
    satirlar = kaynak.splitlines(keepends=True)
    araliklar = _string_araliklari(kaynak)
    # Sondan basa isle: sutun kaymalari diger token'lari etkilemesin.
    for bas_sat, bas_sut, bit_sat, bit_sut, ham in reversed(araliklar):
        yeni = td.duzelt(ham)
        if yeni == ham:
            continue
        if bas_sat == bit_sat:
            satir = satirlar[bas_sat - 1]
            satirlar[bas_sat - 1] = satir[:bas_sut] + yeni + satir[bit_sut:]
        else:
            ilk = satirlar[bas_sat - 1]
            son = satirlar[bit_sat - 1]
            satirlar[bas_sat - 1] = ilk[:bas_sut] + yeni + son[bit_sut:]
            # aradaki satirlar token'a dahil oldugu icin silinir
            del satirlar[bas_sat: bit_sat]
    return "".join(satirlar)


# --------------------------------------------------------------------------
# Dogrulama
# --------------------------------------------------------------------------
def dogrula(eski: str, yeni: str, dosya_adi: str) -> list[str]:
    """Donusumun guvenligini dogrular; sorun listesi dondurur."""
    sorunlar: list[str] = []

    # 1) Yeni dosya Python olarak derlenmeli.
    try:
        ast.parse(yeni)
    except SyntaxError as e:
        sorunlar.append(f"{dosya_adi}: sozdizimi hatasi -> {e}")
        return sorunlar

    # 2) Kod (STRING disi) aynen korunmali. Butun dize sabitleri tek bir
    #    isaretciyle degistirilip agaclar karsilastirilir; boylece tanimlayici,
    #    operator, sayi ve yapi aynen korunurken metin icerikleri goz ardinda
    #    kalir. (Duz "ast.dump" karsilastirmasi calismaz: dump, listelerin
    #    icine dize *degerlerini* de gomdugu icin her metin degisikligini
    #    "kod degisti" diye bildirirdi.)
    def yaprak(kaynak: str) -> str:
        """Dize degerleri yerine isaretci konmus agacin tek satirlik imzasi."""
        kopya = ast.parse(kaynak)
        for dugum in ast.walk(kopya):
            if isinstance(dugum, ast.Constant) and isinstance(dugum.value, str):
                dugum.value = "<dize>"
        return ast.dump(kopya, annotate_fields=False)

    if yaprak(eski) != yaprak(yeni):
        sorunlar.append(f"{dosya_adi}: STRING disi kod degisti (KRITIK)")
    return sorunlar


# --------------------------------------------------------------------------
# Giris noktasi
# --------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ay = argparse.ArgumentParser(description=__doc__)
    ay.add_argument(
        "--denetle",
        action="store_true",
        help="yalnizca raporla, dosyaya yazma (kuru calisma)",
    )
    args = ay.parse_args(argv)

    tum_sorunlar: list[str] = []
    toplam_degisiklik = 0

    for ad in HEDEFLER:
        yol = BURADA / ad
        eski = yol.read_text(encoding="utf-8")
        yeni = _dize_uzerinde(eski)

        sorunlar = dogrula(eski, yeni, ad)
        tum_sorunlar.extend(sorunlar)

        adet = 0
        degisti = yeni != eski
        if degisti:
            # Asagidaki sayim, gercekten duzeltilen dize adedidir.
            adet = sum(
                1
                for a, b in zip(_string_araliklari(eski), _string_araliklari(yeni))
                if a[4] != b[4]
            )
            toplam_degisiklik += adet
            if not args.denetle:
                yol.write_text(yeni, encoding="utf-8")

        durum = "degisti" if degisti else "ayni   "
        print(f"  {ad:16s} {durum}  ({adet} dize)")

    print()
    if tum_sorunlar:
        for s in tum_sorunlar:
            print(f"  [HATA] {s}")
        return 1
    print(f"  Toplam {toplam_degisiklik} dize duzeltildi. Dogrulama temiz.")
    if args.denetle:
        print("  (kuru calisma: dosyalara YAZILMADI)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
