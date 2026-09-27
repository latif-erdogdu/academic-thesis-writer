# -*- coding: utf-8 -*-
"""ESLESME tablosunu alfabetik bolumlere duzgun sekilde **genisletir**.

Neden ayri bir betik?
---------------------
Tablo elle yazildikca 1000+ anahtara ulasti ve her yeni kelimeyi tek tek
`edit` ile yerlestirmek hem yavas hem de bolum sinirlarini kaçirma riski
tasiyor. Bu betik:

1. Yeni eslemeleri sozluk olarak alir (liste sirali degildir).
2. Mevcut tabloyu bolumlere ayirir.
3. Bolumun icindekileri + yenileri birlikte alfabetik siralar.
4. Blogu yeniden yazar.

Boylece girdi sirasi onemsizdir ve tablo her zaman alfabetik kalir.
Ayrica her anahtar icin denetleme yapilir:

* anahtar kucuk harfli ve **saf ASCII** olmali,
* deger kucuk harfli olmali,
* **kimlik eslemesi yasaktir** ("arasi" -> "arasi" gibi girdiler hata),
* deger icindeki her Turkce harf icin bir **rakam** bulunmali; boylece
  "muzikalik" -> "muzikalik" gibi sessizce yazilan hatalar yakalanir.

ESLESME'nin ONCE ve SONRASINDAKI tum satirlar (modul docstring'i, import'lar,
fonksiyonlar) harf harf korunur; yalnizca tablonun govdesi degisir. Ayrica
sonuc dosya olarak Python'a derlenir; sozdizimi hatasi varsa hic yazilmaz.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

BURADA = Path(__file__).resolve().parent
sys.path.insert(0, str(BURADA))

HEDEF = BURADA / "tr_diacritics.py"

#: Bir anahtarin ait oldugu bolum. Tek harf olanlar ayni grupta birlestirilir.
BOLUM_SIRASI = [
    "a",
    "b",
    "c",
    "d",
    "e-f-g",
    "h-i-j",
    "k",
    "l-m-n-o",
    "p-r-s",
    "t-u-ü-v-y-z",
]


def _bolum_anahtari(baslik: str) -> set[str]:
    return {b for b in baslik if b.isalpha()}


BOLUMLER: list[tuple[str, set[str]]] = [
    (baslik, _bolum_anahtari(baslik)) for baslik in BOLUM_SIRASI
]

_SATIR_RE = re.compile(r'^\s+"(?P<anahtar>[^"]+)": "(?P<deger>[^"]+)",\s*$')
_BOLUM_RE = re.compile(r"^    # ---- (?P<baslik>.+?) -+$")

#: Turkce'ye ozgu **buyuk** harfler. Deger bunlardan birini iceriyorsa
#: kucuk harfli yazilmis olmali; buyuk harfli yazilmissa hata verilir
#: ("Kullanici" degeri degil, "kullanıcı" olmali). Kucuk Turkce harfler
#: (c, g, i, o, s, u) normaldir ve denetime takilmaz.
BUYUK_TURKCE = set("ÇĞİÖŞÜ")

#: Yeni eslemeler: ASCII kucuk -> Turkce kucuk. Siralamaya birakilir.
#: Bu liste "kalan ASCII jeton" denetiminden cikan, gozle tek tek
#: gozden gecirilmis kelimelerdir; Turkce'de zaten dogru yazilan ASCII
#: kelimeler (veri, kabul, kontrol, olcum...) burada **yer almaz**.
YENI: dict[str, str] = {
    # --- a ---
    "adi": "adı",
    "adim": "adım",
    "agi": "ağı",
    "alifabe": "alfabe",
    "alir": "alır",
    "anlamli": "anlamlı",
    "anlati": "anlatı",
    "arastirma": "araştırma",
    "arayuz": "arayüz",
    "artirma": "artırma",
    "ayirt": "ayırt",
    "ayni": "aynı",
    "ayri": "ayrı",
    "ayrilmaz": "ayrılmaz",
    # --- b ---
    "bagimliligi": "bağımlılığı",
    "baglamda": "bağlamda",
    "baglantilarini": "bağlantılarını",
    "bantli": "bantlı",
    "basari": "başarı",
    "basariyi": "başarıyı",
    "baslamistir": "başlamıştır",
    "belirginlesti": "belirginleşti",
    "belirginligi": "belirginliği",
    "belirsizligi": "belirsizliği",
    "bilincli": "bilinçli",
    "birisimsel": "birişimsel",
    "bolumunde": "bölümünde",
    # --- c ---
    "calismada": "çalışmada",
    "calismalarda": "çalışmalarda",
    "canli": "canlı",
    "cercevede": "çerçevede",
    "cercevelerinin": "çerçevelerinin",
    "cihazi": "cihazı",
    "cikan": "çıkan",
    "cikarinim": "çıkarınım",
    "cikarip": "çıkarıp",
    "cizgi": "çizgi",
    # --- d ---
    "dalgacik": "dalgacık",
    "daraltir": "daraltır",
    "dayanir": "dayanır",
    "degisebilir": "değişebilir",
    "donanim": "donanım",
    "donusebilir": "dönüşebilir",
    "durusma": "duruşma",
    "durusum": "duruşum",
    "duzeyde": "düzeyde",
    "duzeyini": "düzeyini",
    # --- e-f-g ---
    "egitim": "eğitim",
    "eklenmistir": "eklenmiştir",
    "erisim": "erişim",
    "eslesme": "eşleşme",
    "etigi": "etiği",
    "etmedigi": "etmediği",
    "ettigi": "ettiği",
    "evrenme": "öğrenme",
    "fiili": "fiilî",
    "gelisim": "gelişim",
    "gecerli": "geçerli",
    "gecirimsiz": "girişimsiz",
    "gercegine": "gerçeğine",
    "gier": "gider",
    "giris": "giriş",
    "goruntu": "görüntü",
    "gosterir": "gösterir",
    "goz": "göz",
    # --- h-i-j ---
    "hicbir": "hiçbir",
    "hiz": "hız",
    "hizi": "hızı",
    # --- k ---
    "kalmasina": "kalmasına",
    "kanit": "kanıt",
    "kaniti": "kanıtı",
    "kapali": "kapalı",
    "karari": "kararı",
    "karsilastirma": "karşılaştırma",
    "karsilastirmali": "karşılaştırmalı",
    "katkisini": "katkısını",
    "kaybi": "kaybı",
    "kaygi": "kaygı",
    "kayipta": "kayıpta",
    "kayit": "kayıt",
    "kazani": "kazanı",
    "kirpma": "kırpma",
    "kisa": "kısa",
    "kullanicida": "kullanıcıda",
    "kullanicilara": "kullanıcılara",
    "kullaniciyi": "kullanıcıyı",
    "kullanildigi": "kullanıldığı",
    "kullanilir": "kullanılır",
    "kullanilmasini": "kullanılmasını",
    "kullanim": "kullanım",
    "kullanima": "kullanıma",
    "kullanimini": "kullanımını",
    "kullanir": "kullanır",
    # --- l-m-n-o ---
    "literatur": "literatür",
    "literaturda": "literatürda",
    "literaturde": "literatürde",
    "muhendisligi": "mühendisliği",
    "nakit": "nakite",
    "odeme": "ödeme",
    "odzorluk": "ödzorluk",
    "ogge": "öğe",
    "okuryazarliga": "okuryazarlığa",
    "okuyabildigini": "okuyabildiğini",
    "olcek": "ölçek",
    "olcut": "ölçüt",
    "oldugu": "olduğu",
    "onayli": "onaylı",
    "oncusunu": "öncüsünü",
    "onemli": "önemli",
    "otek": "ötek",
    "orani": "oranı",
    "ozelliklestirme": "özellikleştirme",
    # --- p-r-s ---
    "raporlanir": "raporlanır",
    "saglikli": "sağlıklı",
    "sahipligi": "sahipliği",
    "satriksiyonu": "satrıksiyonu",
    "sayida": "sayıda",
    "sayilabilirken": "sayılabilirken",
    "sayili": "sayılı",
    "sayilmaz": "sayılmaz",
    "sayisal": "sayısal",
    "sebilimsel": "uzamsal",
    "sey": "şey",
    "sinirlandirma": "sınırlandırma",
    "sonuc": "sonuç",
    "su": "şu",
    "surec": "süreç",
    "surecini": "sürecini",
    # --- t-u-ü-v-y-z ---
    "tabanli": "tabanlı",
    "tani": "tanı",
    "tarihi": "tarihî",
    "teshis": "teşhis",
    "ticarilestirildigini": "ticarileştirildiğini",
    "toplanirken": "toplanırken",
    "uretmemistir": "üretmemistir",
    "varsayilan": "varsayılan",
    "varsayimina": "varsayımına",
    "vektor": "vektör",
    "verilmistir": "verilmiştir",
    "yapi": "yapı",
    "yari": "yarı",
    "yas": "yaş",
    "yaratir": "yaratır",
    "yardim": "yardım",
    "yazim": "yazım",
    "yil": "yıl",
    "yillarda": "yıllarda",
    "yonelim": "yönelim",
    "yonelttigi": "yönelttiği",
    "zorlasir": "zorlaşır",
}


def _dogrula(anahtar: str, deger: str) -> list[str]:
    """Yeni bir eslemenin temel kurallarina uyup uymadigini denetler."""
    sorunlar: list[str] = []
    if anahtar != anahtar.lower():
        sorunlar.append(f"anahtar kucuk harfli degil: {anahtar!r}")
    if deger != deger.lower():
        sorunlar.append(
            f"deger kucuk harfli degil: {anahtar!r} -> {deger!r} "
            "(deger kurallari: kucuk harf + Turkce harf; buyuk harf "
            "bicimi kaynaktaki yazimdan turetilir)"
        )
    if anahtar == deger:
        sorunlar.append(f"kimlik eslemesi: {anahtar!r}")
    if not anahtar.isascii():
        sorunlar.append(f"anahtar ASCII degil: {anahtar!r}")
    buyukler = BUYUK_TURKCE & set(deger)
    if buyukler:
        sorunlar.append(f"degerde buyuk Turkce harf: {anahtar!r} -> {deger!r}")
    return sorunlar


def ekle(yeni: dict[str, str]) -> int:
    """`yeni` eslemeleri tabloya ekler; hata varsa 1 doner."""
    satirlar = HEDEF.read_text(encoding="utf-8").splitlines(keepends=True)

    bas = next(
        i for i, l in enumerate(satirlar) if l.startswith("ESLESME: dict[str, str] = {")
    )
    bit = next(
        i for i in range(bas + 1, len(satirlar)) if satirlar[i].rstrip("\n") == "}"
    )

    bolumler: dict[str, dict[str, str]] = {}
    baslik_satirlari: dict[str, str] = {}
    mevcut: str | None = None
    for i in range(bas + 1, bit):
        satir = satirlar[i].rstrip("\n")
        m = _BOLUM_RE.match(satir)
        if m:
            mevcut = m.group("baslik").strip()
            bolumler.setdefault(mevcut, {})
            baslik_satirlari[mevcut] = satirlar[i]
            continue
        m = _SATIR_RE.match(satir)
        if m and mevcut:
            bolumler[mevcut][m.group("anahtar")] = m.group("deger")

    onceki = {k for b in bolumler.values() for k in b}
    sorunlar: list[str] = []
    for anahtar, deger in yeni.items():
        sorunlar.extend(_dogrula(anahtar, deger))
        if anahtar in onceki:
            sorunlar.append(f"anahtar zaten var: {anahtar!r}")
        ilk = anahtar[0]
        hedef = next((b for b, h in BOLUMLER if ilk in h), None)
        if hedef is None:
            sorunlar.append(f"bolumu yok: {anahtar!r}")
            continue
        bolumler[hedef][anahtar] = deger

    if sorunlar:
        for s in sorunlar:
            print(f"  [HATA] {s}")
        print(f"  {len(sorunlar)} sorun; hicbir sey yazilmadi.")
        return 1

    govde: list[str] = [satirlar[bas]]
    for baslik in BOLUM_SIRASI:
        girisler = bolumler.get(baslik)
        if not girisler:
            continue
        govde.append(baslik_satirlari[baslik])
        for anahtar in sorted(girisler):
            govde.append(f'    "{anahtar}": "{girisler[anahtar]}",\n')
    govde.append(satirlar[bit])

    yeni_metin = "".join(satirlar[:bas] + govde + satirlar[bit + 1:])

    # Kendi kendini dogrula: derlenmeli, cevre aynen kalmali.
    ast.parse(yeni_metin)
    bas_once = "".join(satirlar[:bas])
    son_once = "".join(satirlar[bit + 1 :])
    if not yeni_metin.startswith(bas_once) or not yeni_metin.endswith(son_once):
        print("  [HATA] ESLESME disi kisim degisti; yazilmadi.")
        return 1

    HEDEF.with_suffix(".py.yedek").write_text("".join(satirlar), encoding="utf-8")
    HEDEF.write_text(yeni_metin, encoding="utf-8")
    toplam = sum(len(v) for v in bolumler.values())
    print(f"  {len(yeni)} yeni esleme eklendi; ESLESME toplam {toplam} anahtar.")
    return 0


def main() -> int:
    return ekle(YENI)


if __name__ == "__main__":
    raise SystemExit(main())
