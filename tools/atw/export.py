"""`thesis:export` tezi md / docx / pdf olarak dosyaya dokar.

Bulgu
-----
`cmd_export` stub idi: `final_thesis` kapisini sorup "Henuz implemente
edilmedi" yaziyor, `0` donuyordu. Komut BASARILI gorunup HICBIR sey
uretmuyordu. `skill.yaml` ise "Final tez metnini birlestir (bolumler +
kaynakca + ekler)" diye tanimliyordu.

Ayni anda iki veri modeli boslugu vardi:

  1. `citation.reference_entry` hicbir yerde URETILMIYORDU. `citation_check`
     yalnizca `in_text_form`'u DOGRULUYOR; kaynakca girdisi ureten kod
     yoktu.
  2. `authors` alaninin bicimi belirsizdi. Fixture'lar olcmeyerek cozdu:
     "Orman, A." (soyad once, APA-hazir). Yani girdiyi ayristirmak
     GEREKMIYOR; olduğu gibi kullanilir. Bu, seyirligin en ucuz yolu:
     sözlesme zaten APA biciminde girdi istiyor.

Politika uydurmamak icin kaynakca kurali mevcut denetimden alindi
------------------------------------------------------------------
`citation_check.audit_citations`, metinde atiflanmamis bir kaynagi
`orphaned_citations` (major) olarak sayiyor ve bulgu konumunu "Kaynakca"
diye yaziyor. Demek ki kaynakca TAM OLARAK atiflanan kaynak kumesidir.
Atanmayanlari eklemek, ayni kaynagi iki yerde farkli muameleye sokardi.

Ekler (appendix): durum semasinda `appendices` alani YOK. Bu surumde
disa aktarilmaz ve bu durum CIKTIDA ACIKCA yazilir. Sessizce birakmak,
ciktida eksik oldugu gorunmeyen bir belge uretmek olurdu.

PDF ve Turkce
-------------
fpdf2'nin varsayilan `latin-1` core fontu cp1252 kodlamasini kullanir.
cp1252'de Turkcenin harflerinden yalnizca c, o, u ve buyukleri vardir;
g, i, s ve buyukleri (cekimli/dotsuz i) YOKTUR. Turkce bir tezde bunlar
her sayfada gecer. Bu yuzden PDF uretimi sistemdeki bir Unicode TTF
yazi tipini kaydeder. Bulunamazsa sessizce '?' basmak yerine acik bir
hata verilir.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

DESTEKLENEN_BICIMLER = ("md", "docx", "pdf")

#: `--format` verilmediginde uretilen bicimler.
#:
#: Markdown INSAYA teslim bicimi DEGILDIR: sayfa duzeni, baslik
#: hiyerarsisi, asili girinti ve sayfa numarasi yoktur. Yalniz Markdown
#: uretmek, kullanici "export calisti" gorup teslim edilebilir bicimi
#: aramak zorunda birakti. Ikili uretilir: `md` okunabilir ve farki
#: incelenebilir (kodla karsilastirilabilir), `docx` teslim edilebilir.
DEFAULT_BICIMLER = ("md", "docx")

#: Govde yazi tipi ve alt baslik puntolari. Universite tez kilavuzlarinin
#: tamami Times New Roman 12 pt ister; baska bir secim teslim kontrolunde
#: "bicim hatasi" sayilir. `docx_belgesi` bunlari kullanir.
GOVDE_PT = 12
BOLUM_PT = 14

#: Ekler bu surumde disa aktarilmiyor; her ciktida acikca belirtilir.
EKLER_NOTU = (
    "> Not: Bu dışa aktarımda ekler (appendix) yer almıyor. Durum şemasında "
    "`appendices` alanı bulunmadığı için ek verisi taşınmıyor."
)

YAZAR_YOK = "Yazar belirtilmemiş"

#: Unicode yazi tipi aranacak standart konumlar. Sirali: once isletim
#: sisteminin garanti ettigi, sonra yaygin Linux/macOS konumlari.
YAZI_TIPI_ADAYLARI = (
    r"C:\Windows\Fonts\times.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\calibri.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\verdana.ttf",
    r"C:\Windows\Fonts\tahoma.ttf",
    r"C:\Windows\Fonts\georgia.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSerif.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/usr/share/fonts/liberation/LiberationSerif-Regular.ttf",
    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
)

class ExportHatasi(RuntimeError):
    """Disa aktarma yapilamadi: bicim hatasi veya veri butunlugu.

    `RuntimeError` alt sinifi: cagiran kod hatayi yakalayip kullanicya
    acik bir mesaj gosterebilir. `docx_belgesi` PDF gibi dosyaya
    yazmak zorunda olan bicimlerde de bu sinifi kullanir; boylece
    "yari teslim" durumu olusmaz.
    """


# Turkce alfabetik siralama.
# =============================================================================
# Buradaki HER karar bir siralama hatasini onler. Uc gercek tuzak var;
# ucu de TESLIM EDILMIS bir tezde gozlemlenmistir.
#
# Tuzak 1 — Kod noktasi sirasi Turkce siralamayi BOZAR.
#   `ç` (U+00E7) `d` (U+0064) sonra gelir ama `ğ` (U+011F) `ı` (U+0131)
#   ve `ş` (U+015F) `ö` (U+00F6) ONUNCE gelir. Yani alfabetik degil,
#   kod birligi sirasi olur.
#
# Tuzak 2 — `ı` (U+0131) Turkce alfabede `i`den ONCE gelir (h ı i j).
#   Ilk deneme `ı` -> "i{" eslemesiyle bunu ters cevirmisti ve "i" her
#   zaman once geliyordu. Testler o an yalnizca aksansiz harfleri
#   sinadigi icin hata gecmisti.
#
# Tuzak 3 — Turkce harflerin KANONIK ayrisimi vardir ve NFKD onlari
#   YUTAR:
#       ç -> c + U+0327 COMBINING CEDILLA
#       ş -> s + U+0327
#       ğ -> g + U+0306 COMBINING BREVE
#       İ -> I + U+0307 COMBINING DOT ABOVE
#   Ayirip birlesik isareti silmek `ç`yi `c`ye indirir. Gozlemlenen
#   sonuc: `Çoban` `Corba`dan once, `Çınar` `Ceylan`dan once gidiyordu;
#   Turkce kurali (`ç` > `c`) tam TERSINE donmus tu. Cozum: ayrisim
#   TEK TEK karakterde yapilir ve `c` gibi taban harfleri ATLANIR
#   (`_tek_harfi_indir`).
#
# Cozumlem: Turkce alfabesini acikca yazip her harfi iki haneli sirasina
# baglamak. Iki hane sabit oldugu icin birlestirme belirsiz degildir.
# Yerel ayara bagimli DEGILDIR (Windows'ta Turkce yerel ayari her zaman
# bulunamaz), bu yuzden ayni sonuc her platformda verir.
_TURKCE_ALFABES = "abcçdefgğhıijklmnoöprsştuüvyz"
_HARF_SIRASI = {
    harf: "{:02d}".format(sira)
    for sira, harf in enumerate(_TURKCE_ALFABES)
}

#: Turkce BUYUK -> kucuk. `I` -> `ı` ve `İ` -> `i` kurali Turkce
#: alfabeye uygundur: `I` ASCII kuralina gore `i`ye INMEZ.
_TURKCE_BUYUK = "ABCÇDEFGĞHIİÖŞÜ"
_TURKCE_KUCUK = "abcçdefgğhıiöşü"

#: ASCII buyuk -> kucuk. `I` her iki tabloda da gecir ve `str.maketrans`
#: yinelenen anahtarlarda SON KAZANANI birakir. Bu yuzden Turkce tablo
#: SONDA durur: `I` -> `ı` Turkce kurali korunur. ASCII tablo basa
#: konulsaydi `IŞIK` ile `ışık` farkli anahtar uretirdi.
_AZ = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_az = "abcdefghijklmnopqrstuvwxyz"
_KUCULTME = str.maketrans(_AZ + _TURKCE_BUYUK, _az + _TURKCE_KUCUK)

#: Turkce alfabesi disinda kalan Latin harfler. NFKD bunlari AYRIŞTIRMAZ
#: (`ø` oldugu gibi kalir), bu yuzden acik esleme gerekir. Liste
#: sinirlidir ve sinirli olmak ZARARDIR: kapsanmayan harf sessizce
#: alfabet sonuna duser, sessiz bir hata fildisi degil. Gozden
#: gecilenler: `ø` (Danca/Norvece), `ß` (Almanca), `æ`/`œ`
#: (Iskandinavca/Fransizca), `ł` (Lehce), `đ`/`ð` (Keltce),
#: `þ` (Iskandinavca).
_TABAN_HARF = str.maketrans({
    "ø": "o", "Ø": "O",
    "ß": "ss",
    "æ": "ae", "Æ": "AE",
    "œ": "oe", "Œ": "OE",
    "ł": "l", "Ł": "L",
    "đ": "d", "Đ": "D",
    "ð": "d", "Ð": "D",
    "þ": "th", "Þ": "TH",
})

#: Alfabet disi karakterlerin anahtardaki yeri. `99` secildi: gercek
#: sira degerleri 00-28 arasinda, iki haneli degerler 29'dan sonra
#: baslamaz; boylece anahtar hem sabit uzunlukta hem de alfabet disi
#: karakterler icin gercek bir "sonra" konumu tasir.
_ALFABET_DISI = "99"

#: Birlestirilmis diyakritik isaretler (U+0300-U+036F).
_BIRLESIK_ISARET = re.compile(r"[\u0300-\u036f]")


def _tek_harfi_indir(harf: str) -> str:
    """Tek karakteri, alfabet disi degilse taban harfine indirger.

    Turkce alfabesi disindaki bir karakter icin NFKD ayrisimi + birlesik
    isaret temizligi yapar: `é` -> `e`, `n` + U+0303 -> `n`.

    Turkce alfabesi `c` taban harfi ATLANIR. Gerekce yukarida: `ç`nin
    kanonik ayrisimi `c` + U+0327'dir; ayirip isareti silmek `ç`yi
    `c`ye indirger ve `c`/`ç` sirasini tersine cevirir.
    """
    if harf in _HARF_SIRASI:
        return harf
    return _BIRLESIK_ISARET.sub("", unicodedata.normalize("NFKD", harf))


def turkce_siralamasi(metin: str) -> str:
    """Turkce alfabetik siralama anahtari dondurur.

    Turkce alfabesi `a b c ç d e f g ğ h ı i j k l m n o ö p r s ş t u ü
    v y z` sirasidir. Buradan uc kural cikar:

      1. `c`/`ç`, `g`/`ğ`, `s`/`ş`, `u`/`ü` ailelerinde kesik isaretli
         harf, duz harften SONRA gelir.
      2. `ı` `i`den ONCE gelir (h ı i j).
      3. Turkce alfabede `q w x` yoktur; yabanci adlarda bu harfler
         alfabet disidir ve alfabetin en sonuna duser.

    Buyuk/kucuk duyarsizdir ve yerel ayara bagimli DEGILDIR. Aksanli
    Latin harfleri taban harfine indirilir; Turkce harfler KORUNUR.
    Rakam ve noktalama gibi alfabet disi karakterler en sona duser.
    """
    # SIRALI ONEMLI: once taban harf, sonra kucultme. Tersi olursa
    # `_TABAN_HARF` urettigi buyuk harf (`Ł` -> `L`) bir daha kucultulmez
    # ve `Lukasiewicz` alfabetin en basina duser.
    metin = (metin or "").translate(_TABAN_HARF).translate(_KUCULTME)
    parcalar = (_tek_harfi_indir(harf) for harf in metin)
    # `_tek_harfi_indir` birlesik isaret icin BOS string doner. Bos
    # parca tabloya girmez ama `get("", "99")` "99" uretir; yani once
    # normalize edilmis bir `é` (e + U+0301) tum anahtari bir karakter
    # kaydirir. Bos parcalar elenmelidir.
    return "".join(
        _HARF_SIRASI.get(harf, _ALFABET_DISI)
        for harf in parcalar
        if harf
    )


# --- kaynakca girdileri ----------------------------------------------------

def atiflanan_kaynak_kimlikleri(durum: dict[str, Any]) -> set[str]:
    """Metinde atif gosterilen kaynak kimlikleri.

    Kaynakca kumesi budur; `citation_check.audit_citations` ile ayni
    olcutu kullanir (`orphaned_citations`).
    """
    return {
        atif.get("source_id")
        for atif in durum.get("citations") or []
        if atif.get("source_id")
    }


def _hazir_girdi_haritasi(durum: dict[str, Any]) -> dict[str, str]:
    """Kaynak kimligi -> hazir `reference_entry` (citation uzerinden).

    Alan semada var ama hicbir kod uretmiyor; doluysa insani/ajani
    bicimlendigi icin yeniden uretilmez.
    """
    harita: dict[str, str] = {}
    for atif in durum.get("citations") or []:
        kaynak_id = atif.get("source_id")
        giris = (atif.get("reference_entry") or "").strip()
        if kaynak_id and giris and kaynak_id not in harita:
            harita[kaynak_id] = giris
    return harita


#: Soyadin bir parcasi olan on ekler. Turkceye girmez (`Kaya`, `Demir`),
#: Felemenkce/Latince/Almanca'da ise soyada aittir: `van der Berg`,
#: `von Humboldt`, `della Rossa`. APA 7 bu ekleri soyadin icinde tutar.
#: Ek, soyadin BIRAKILIRSA `Berg` < `Humboldt` yanlis siralanir ve
#: alfabet kayar.
SOYAD_EKLERI = frozenset({
    "van", "von", "de", "del", "della", "der", "den", "di", "da",
    "du", "la", "le", "ter", "ten", "af", "av", "zu", "al",
})


def soyad_ayir(yazar: str) -> str:
    """Tek yazar adindan SOYADI ayiklar.

    Iki bicim desteklenir; veri modeli ikisini de kabul eder:

      * ``Family, Given``  -> ``Family``   (virgul ilk parca soyaddir)
      * ``Given Family``   -> ``Family``   (son parca soyaddir)

    Parcaciklar soyada dahil edilir: ``Jan van der Berg`` -> ``van der
    Berg``, ``Wilhelm von Humboldt`` -> ``von Humboldt``.

    ``Gian-Reto Walther`` -> ``Walther``: tire bir VERILEN adin parcasi
    olsa bile son token soyadir.

    Soyad bulunamazsa girdi oldugu gibi dondurulur. Anahtar uretirken
    girdiye duserek veri kaybi olmaz; yalniz siralama anahtari daha
    zayif olur.
    """
    metin = (yazar or "").strip()
    if not metin:
        return ""

    if "," in metin:
        # `Aydin, A.` -> `Aydin`. Virgulden once her zaman soyaddir.
        soyad = metin.split(",", 1)[0].strip()
        return soyad or metin

    parcalar = metin.split()
    if len(parcalar) == 1:
        return parcalar[0]

    bas = len(parcalar) - 1
    # Sondan geriye dogru parcaciklari topla: `van der Berg` icin
    # once `Berg` (son token), sonra `der` parcacik oldugu icin alinir,
    # sonra `van`.
    while bas > 0 and parcalar[bas - 1].lower() in SOYAD_EKLERI:
        bas -= 1
    return " ".join(parcalar[bas:])


def _kaynak_siralamasi(kaynak: dict[str, Any]) -> tuple[str, str, str, str]:
    """Ilk yazarin SOYADI, sonra yil, sonra baslik, sonra kimlik.

    Onceki surum `authors[0]`in TAM string'ini anahtar aliyordu:
    "Camille Parmesan" -> "c", "Gian-Reto Walther" -> "gi",
    "Riana Gardiner" -> "ri". Sonuc: alfabet "Gardiner, Parmesan,
    Walther" degil "Parmesan, Walther, Gardiner" idi.

    Son anahtar KIMLIKTIR ve BILINCLI OLARAK kolasyondan GECER. Kimlik
    `SRC-001` icin `turkce_siralamasi` rakam ve tireyi "99" yapar; butun
    `SRC-00N` kimlikleri ayni anahtara duser ve ayirt edici olmaktan
    cikar. Bozuk ayirt edici, kararli (deterministik) siralamadan
    kotudur: `sorted` kararli olsa da girdi sirasi `set`ten geldigi
    icin her calistirmada degisebilir.
    """
    yazarlar = [y for y in (kaynak.get("authors") or []) if (y or "").strip()]
    if yazarlar:
        ilk = turkce_siralamasi(soyad_ayir(yazarlar[0]))
    else:
        # Yazar yoksa basliga dus. "~" alfabet disi; anahtar sona duser.
        ilk = turkce_siralamasi(kaynak.get("title") or "") or "~"
    return (
        ilk,
        str(kaynak.get("year") or ""),
        turkce_siralamasi(kaynak.get("title") or ""),
        # Ham kimlik: kolasyon burada ayirt edici olmaktan cikar.
        str(kaynak.get("id") or ""),
    )


def kaynakca_girdileri(durum: dict[str, Any]) -> list[dict[str, Any]]:
    """Kaynakca girdileri: YALNIZCA atiflanan kaynaklar, Turkce alfabetik.

    Atiflanmayan kaynak burada yer almaz; `orphaned_citations` denetimi
    zaten onu ayri bir bulgu olarak bildirir.
    """
    kaynaklar = {
        kaynak.get("id"): kaynak
        for kaynak in durum.get("sources") or []
        if kaynak.get("id")
    }
    secili = [
        kaynaklar[kimlik]
        for kimlik in atiflanan_kaynak_kimlikleri(durum)
        if kimlik in kaynaklar
    ]
    return sorted(secili, key=_kaynak_siralamasi)


def _yazar_birligi(yazarlar: list[str]) -> str:
    """APA yazar birligi: 1 yazar; 2+ yazar sonuncudan once `, &` ile.

    Oxford virgulu kullanilir (`Aydin, A., Boz, B., & Cetin, C.`).
    """
    temiz = [yazar.strip() for yazar in yazarlar if (yazar or "").strip()]
    if not temiz:
        return YAZAR_YOK
    if len(temiz) == 1:
        return temiz[0]
    return "{}, & {}".format(", ".join(temiz[:-1]), temiz[-1])


def _kaynak_bilgisi(kaynak: dict[str, Any]) -> str:
    """Kaynak tipine gore basliktan sonra gelen bilgi.

    Yalnizca `article` dergi/sayfa alanlarini kullanir; diger tiplerde
    `publisher` basilir. `source.json`da `book_chapter` icin kitap basligi,
    `legislation` icin gazete sayisi alani YOKTUR; bu alanlar uydurulmaz,
    eksikleri modul dokumanda not edilir.
    """
    tur = kaynak.get("source_type") or "other"
    if tur == "article":
        dergi = (kaynak.get("journal") or "").strip()
        if not dergi:
            return ""
        parcalar = [dergi]
        cilt = (kaynak.get("volume") or "").strip()
        sayi = (kaynak.get("issue") or "").strip()
        if cilt and sayi:
            parcalar.append("{}({})".format(cilt, sayi))
        elif cilt:
            parcalar.append(cilt)
        sayfa = (kaynak.get("pages") or "").strip()
        if sayfa:
            parcalar.append(sayfa)
        return ", ".join(parcalar)
    return (kaynak.get("publisher") or "").strip()


def _nokta_temizle(metin: str) -> str:
    """Sondaki coklu noktalari teke indirir, tek nokta olmazsa ekler.

    Yalnizca GOVDEye uygulanir. DOI/URL bir baglantidir ve APA 7'ye gore
    sonunda nokta OLMAMALIDIR; nokta eklemek baglantiyi bozardi.
    """
    temiz = (metin or "").strip()
    while temiz.endswith(".."):
        temiz = temiz[:-1].rstrip()
    if temiz and not temiz.endswith("."):
        temiz += "."
    return temiz


def apa_kaynak_girdisi(kaynak: dict[str, Any]) -> str:
    """Tek bir kaynak icin APA 7 kaynakca girdisi uretir.

    Baslik ve yazar adlari OLDUGU GIBI basilir: buyuk/kucuk harf
    DEGISTIRILMEZ. Turkce'de `I`/`i` ve `ı`/`I` ciftleri Python'un
    `upper()`/`capitalize()` ile bozulur, APA da metni oldugu gibi ister.
    """
    yazarlar = _yazar_birligi(kaynak.get("authors") or [])
    yil = str(kaynak.get("year")).strip() if kaynak.get("year") else "t.y."
    baslik = (kaynak.get("title") or "").strip()

    parcalar = ["{0} ({1}). {2}.".format(yazarlar, yil, baslik)]
    bilgi = _kaynak_bilgisi(kaynak)
    if bilgi:
        parcalar.append(bilgi + ".")

    govde = _nokta_temizle(" ".join(parca for parca in parcalar if parca))

    doi = (kaynak.get("doi") or "").strip()
    url = (kaynak.get("url") or "").strip()
    if doi:
        return "{0} https://doi.org/{1}".format(govde, doi)
    if url:
        return "{0} {1}".format(govde, url)
    return govde


def kaynakca_satirlari(durum: dict[str, Any]) -> list[str]:
    """Kaynakca satirlari; hazir `reference_entry` varsa o kullanilir."""
    hazir = _hazir_girdi_haritasi(durum)
    return [
        hazir.get(kaynak["id"]) or apa_kaynak_girdisi(kaynak)
        for kaynak in kaynakca_girdileri(durum)
    ]


# --- govde ------------------------------------------------------------------

def _sirali_bolumler(durum: dict[str, Any]) -> list[dict[str, Any]]:
    """Bolumler numaraya gore sirali; numara yoksa sirayla konum."""
    bolumler = list(durum.get("chapters") or [])
    return [
        bolum
        for _, bolum in sorted(
            enumerate(bolumler),
            key=lambda c: (
                c[1].get("number") if isinstance(c[1].get("number"), int) else c[0],
                turkce_siralamasi(c[1].get("id") or ""),
            ),
        )
    ]


def _metinli_paragraflar(bolum: dict[str, Any]) -> list[tuple[str, str]]:
    """Bolumdeki bos olmayan paragraflar: ``(alt_baslik, metin)``.

    `paragraph.section` alani semada var ve `thesis:write` dolduruyor,
    ama cikti URETIMI hic okumuyordu. Sonuc: "1.1 Kapsam", "2.3 Yontem"
    gibi yuzlerce alt baslik teslim edilen metne hic girmiyordu; bolum
    ici yapisiz, duz metin blogu olarak cikiyordu. Alan bos birakilirsa
    cifti `("", metin)` olur ve cikti dogrudan `metin`e gider.

    Bos paragraf ATLANIR: metni olmayan paragraf bosluk birakir ve
    `P-999` gibi bir kimlik tasimaz, cunku kimlikler okuyucuya
    gosterilmez.
    """
    ciftler: list[tuple[str, str]] = []
    for paragraf in bolum.get("paragraphs") or []:
        metin = (paragraf.get("text") or "").strip()
        if not metin:
            continue
        ciftler.append(((paragraf.get("section") or "").strip(), metin))
    return ciftler


def _metinler(bolum: dict[str, Any]) -> list[str]:
    """Bolumdeki bos olmayan paragraf metinleri (alt basliksiz)."""
    return [metin for _, metin in _metinli_paragraflar(bolum)]


def _metinli_paragraf_var_mi(durum: dict[str, Any]) -> bool:
    return any(_metinler(bolum) for bolum in _sirali_bolumler(durum))


# --- butunluk ---------------------------------------------------------------

def _dogrula(durum: dict[str, Any]) -> None:
    """Disa aktarilabilirlik on kontrolleri.

    Bu kontroller KAPI DEGILDIR; `final_thesis` kapisi zaten ayri bir
    onay denetimi. Buradaki kontroller, onay alinmis olsa bile ciktida
    sessizce eksik/bozuk bir belge uretilmesini engeller:

      * bölüm yoksa / paragraf metni yoksa belge gövdesiz olurdu;
      * metinde atıf gösterilen ama kaynakta olmayan kaynak UYDURMA
        atıftır (`citation_check`: `fabricated_sources`, critical);
      * geri çekilmiş kaynakla atıf `retracted_sources_in_use`
        (critical) sayılır — politika burada yeniden konmaz, mevcut
        karar yansıtılır.
    """
    if not durum.get("chapters"):
        raise ExportHatasi(
            "Dışa aktarılacak bölüm yok. Önce bölüm tanımla."
        )
    if not _metinli_paragraf_var_mi(durum):
        raise ExportHatasi(
            "Hiçbir paragraf metni yok. Metni olan en az bir paragraf "
            "gerekir; aksi halde çıktıda yalnızca başlık bulunur."
        )

    kaynaklar = {
        kaynak.get("id"): kaynak
        for kaynak in durum.get("sources") or []
        if kaynak.get("id")
    }

    atiflanan: set[str] = set(atiflanan_kaynak_kimlikleri(durum))
    # Paragraf atiflari (CIT-XXX) kaynak kimliklerine (SRC-XXX) cozulmeli;
    # CIT ID'leri sources sozlugunde bulunmaz. (Regresyon: cozum yapilmadigi
    # icin gercek atif iceren her bolum 'kaynak uydurulamaz' hatasiyla
    # reddediliyordu.)
    cit_to_src = {
        c.get("id"): c.get("source_id")
        for c in durum.get("citations") or []
        if c.get("id") and c.get("source_id")
    }
    for bolum in durum.get("chapters") or []:
        for paragraf in bolum.get("paragraphs") or []:
            atiflanan.update(paragraf.get("sources") or [])
            for cit in paragraf.get("citations") or []:
                src = cit_to_src.get(cit)
                if src:
                    atiflanan.add(src)

    for kimlik in sorted(atiflanan):
        if kimlik not in kaynaklar:
            raise ExportHatasi(
                "Metinde gösterilen {0} kaynağı `sources` içinde yok. "
                "Kaynak uydurulamaz; önce kaydı ekle.".format(kimlik)
            )
    for kimlik in sorted(atiflanan):
        kaynak = kaynaklar[kimlik]
        if kaynak.get("retraction_status") == "retracted":
            raise ExportHatasi(
                "Metinde gösterilen {0} kaynağı retraksiyona uğramış. "
                "Geri çekilmiş bir çalışmaya atıf yapılamaz; `thesis:audit` "
                "ile denetle.".format(kimlik)
            )


# --- yazi tipi --------------------------------------------------------------

def yazi_tipi_yolu() -> Path | None:
    """Unicode iceren sistem yazi tipi yolunu dondurur, yoksa `None`.

    fpdf2'nin core fontlari Turkcenin yarısini basamaz (`g`, `ı`, `ş`,
    `İ` cp1252'de yoktur), bu yuzden PDF icin TTF gerekir.
    """
    for aday in YAZI_TIPI_ADAYLARI:
        yol = Path(aday)
        if yol.is_file():
            return yol
    return None


# --- cikti uretimi ---------------------------------------------------------

def markdown_uret(durum: dict[str, Any]) -> str:
    """Tezi Markdown metnine cevirir.

    Bolum ici alt basliklar `###` seviyesinde yazilir. `##` (bolum) ile
    `###` (alt baslik) ayrimi bilincli: icindekiler araci ve Markdown
    gosterimleri bu hiyerarsiyi bekler. Ayni alt baslik ardisik
    paragraflarda tekrarliyorsa BIR KEZ yazilir; araya girip donerse
    yeniden yazilir.
    """
    _dogrula(durum)
    satirlar: list[str] = ["# {}".format(durum.get("title") or "Başlıksız Tez"), ""]

    for bolum in _sirali_bolumler(durum):
        numara = bolum.get("number")
        baslik = (bolum.get("title") or "").strip()
        satirlar.append("## {}. {}".format(numara, baslik))
        satirlar.append("")

        # Her bolum kendi alt basligindan baslar: takip bolumler arasi
        # TASINMAZ, yoksa "2.1" basligi once gelen "1.9"un devami
        # sanilir ve metin yanlis yere yerlestirilir.
        son_baslik = ""
        for alt_baslik, metin in _metinli_paragraflar(bolum):
            if alt_baslik and alt_baslik != son_baslik:
                satirlar.extend(["### {}".format(alt_baslik), ""])
                son_baslik = alt_baslik
            satirlar.extend([metin, ""])

    satirlar.extend(["## Kaynakça", ""])
    girisler = kaynakca_satirlari(durum)
    if girisler:
        for giris in girisler:
            satirlar.extend([giris, ""])
    else:
        satirlar.extend([
            "> Kaynakça boş: metinde atıf gösteren kaynak yok.", ""
        ])

    satirlar.extend(["---", "", EKLER_NOTU, ""])
    return "\n".join(satirlar)


#: `w:sectPr` cocuklarinin OOXML sira duzeni. `w:pgNumType` bu sirada
#: `w:cols`tan ONCE gelmelidir; rastgele eklenen bir `w:pgNumType`
#: LibreOffice ve Word tarafindan YOK SAYILIR ve sayfa numarasi sessizce
#: bozulur. Sirayi bilmek bu yuzden gerekli.
_SECTPR_SIRA = (
    "w:footnotePr", "w:endnotePr", "w:type", "w:pgSz", "w:pgMar",
    "w:paperSrc", "w:pgBorders", "w:lnNumType", "w:pgNumType", "w:cols",
    "w:formProt", "w:vAlign", "w:noEndnote", "w:titlePg", "w:textDirection",
    "w:bidi", "w:rtlGutter", "w:docGrid", "w:printerSettings",
    "w:sectPrChange",
)


def _sayfa_numarasi_ayarla(bolum, bicim: str | None = None, baslangic: int | None = None) -> None:
    """Bolumun sayfa numarasi bicimini ve baslangicini ayarlar.

    `baslangic=None` "baslangici koru" demek DEGILDIR: olmayan
    `w:start` OLMASI gerekir, yoksa numara 1'den bastan baslar.
    `python-docx` `add_section()` ile onceki `sectPr`'yi KOPYALAR; bu
    yuzden "devam" bolumlerinde `w:start` bilerek silinir.
    """
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    sect = bolum._sectPr
    pnt = sect.find(qn("w:pgNumType"))
    if pnt is None and bicim is None and baslangic is None:
        # Kapak sayfasi numarasizdir. `w:pgNumType` YOK olmali; bos bir
        # `w:pgNumType` eklemek "belki numara yoktur" degil, "numara
        # ayari var ama degeri yok" demektir ve okuyucu bunu varsayilan
        # numaralandirma sanabilir.
        return
    if pnt is None:
        pnt = OxmlElement("w:pgNumType")
        bas_sira = _SECTPR_SIRA.index("w:pgNumType")
        for etiket in _SECTPR_SIRA[bas_sira + 1:]:
            sonraki = sect.find(qn(etiket))
            if sonraki is not None:
                sonraki.addprevious(pnt)
                break
        else:
            sect.append(pnt)
    if bicim is not None:
        pnt.set(qn("w:fmt"), bicim)
    if baslangic is not None:
        pnt.set(qn("w:start"), str(baslangic))
    else:
        pnt.attrib.pop(qn("w:start"), None)


def _alan_yaz(paragraf, talimat: str, onizleme: str = "", kirli: bool = False) -> None:
    """Word ALANI (field) yazar: begin / instrText / separate / end.

    Alan, duz metinden farklidir: Word dosyayi acarken degeri hesaplar.
    Bu yuzden `w:dirty="true"` eklenir ve `settings.xml`e
    `w:updateFields` yazilir; aksi halde kullanici dosyayi actiginda alan
    BOS gorunur ve "icindekilerim yok" sanir.
    """
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    def _kosu(el):
        paragraf._p.append(el)

    bas = OxmlElement("w:r")
    fld = OxmlElement("w:fldChar")
    fld.set(qn("w:fldCharType"), "begin")
    if kirli:
        fld.set(qn("w:dirty"), "true")
    bas.append(fld)
    _kosu(bas)

    tal = OxmlElement("w:r")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " {}".format(talimat)
    tal.append(instr)
    _kosu(tal)

    ayir = OxmlElement("w:r")
    ayir_fld = OxmlElement("w:fldChar")
    ayir_fld.set(qn("w:fldCharType"), "separate")
    ayir.append(ayir_fld)
    _kosu(ayir)

    if onizleme:
        on = OxmlElement("w:r")
        metin = OxmlElement("w:t")
        metin.text = onizleme
        on.append(metin)
        _kosu(on)

    bit = OxmlElement("w:r")
    bit_fld = OxmlElement("w:fldChar")
    bit_fld.set(qn("w:fldCharType"), "end")
    bit.append(bit_fld)
    _kosu(bit)


def _dipnot_sayfa_no(belge, bolum_no: int) -> None:
    """Bolumun dipnotuna PAGE alani yazar (kapak haric)."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    bolum = belge.sections[bolum_no]
    bolum.footer.is_linked_to_previous = False
    paragraf = bolum.footer.paragraphs[0] if bolum.footer.paragraphs else bolum.footer.add_paragraph()
    paragraf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _alan_yaz(paragraf, "PAGE", "1")


def _sayfa_olculeri_ayarla(belge) -> None:
    """A4 + cilt payi icin sol 3 cm, sag/ust/alt 2 cm.

    Cilt payi (binding margin) sol kenarda genistir; sagda daralmaz.
    A4 degil A5/Letter kullanmak universite teslim kontrolunde
    dogrudan red sebebidir.
    """
    from docx.shared import Cm

    for bolum in belge.sections:
        bolum.page_width = Cm(21.0)
        bolum.page_height = Cm(29.7)
        bolum.left_margin = Cm(3.0)
        bolum.right_margin = Cm(2.0)
        bolum.top_margin = Cm(2.0)
        bolum.bottom_margin = Cm(2.0)


def _govde_stili_ayarla(belge) -> None:
    """Normal stil: Times New Roman 12 pt, 1.5 satir, iki yana, 1.25 girinti.

    Yazi tipi yalniz `w:ascii`/`w:hAnsi` ile degil `w:cs` ve
    `w:eastAsia` ile de yazilir; aksi halde Word/Turkce harfler icin
    baska bir yazi tipine duser.
    """
    from docx.oxml.ns import qn
    from docx.shared import Pt

    normal = belge.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(GOVDE_PT)
    rfonts = normal.element.rPr.rFonts
    for nitelik in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(nitelik), "Times New Roman")
    pf = normal.paragraph_format
    pf.line_spacing = 1.5
    pf.space_after = Pt(0)


def docx_belgesi(durum: dict[str, Any]) -> bytes:
    """Tezi akademik Word duzeninde BELGE olarak uretir (dosyaya yazmaz).

    Dosyaya yazmadan once uretilmesi bilincli: `disa_aktar` birden fazla
    bicim isteyebilir ve YARI teslim bir teslim degildir. Tum icerik
    once bellekte hazirlanir, hepsi basarili olursa dosyaya yazilir.

    DUZEN (TR universite tez olcusu)
    -------------------------------
    A4; sol 3.0 cm (cilt payi), sag/ust/alt 2.0 cm.
    Govde: Times New Roman 12 pt, 1.5 satir araligi, iki yana, 1.25 cm
    girinti.
    Bolum basligi: 14 pt kalin, ortalI, her bolum yeni sayfada.
    Alt baslik: 12 pt kalin, sol.
    On bilgiler: kapak + ozet + abstract + icindekiler; roma rakam.
    Govde: arabic rakam, 1'den baslar.
    Kaynakca: asili girinti 1.25 cm, Turkce alfabetik.

    KISIT: `add_section()` ile bolum sayisi 5'tir. Capraz referans ve
    sekil/tablo gosterimi bu surumde YOKTUR; `appendix` alani da durum
    semasinda bulunmaz. Ikisinin yoklugu ciktiya acikca yazilir.
    """
    _dogrula(durum)
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt
    import io as _io

    belge = Document()
    _sayfa_olculeri_ayarla(belge)
    _govde_stili_ayarla(belge)

    govde_girinti = Cm(1.25)

    # --- 1. kapak: sayfa numarasi YOK ---------------------------
    kapak = belge.sections[0]
    _sayfa_numarasi_ayarla(kapak, None, None)
    kapak.footer.is_linked_to_previous = True

    baslik = belge.add_paragraph(durum.get("title") or "Başlıksız Tez", style="Title")
    baslik.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for satir in (
        "",
        "Tez No: {0}".format(durum.get("thesis_id") or "[Tez No]"),
        "",
        "[Üniversite Adı]",
        "[Fakülte Adı] / [Anabilim Dalı]",
        "",
        "[Ad Soyad]",
        "",
        "Danışman: [Danışman Unvan, Ad Soyad]",
        "",
        "[Şehir], [Yıl]",
    ):
        p = belge.add_paragraph(satir)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # --- 2. ozet: roma rakam, 1'den baslar ----------------------
    belge.add_section()
    _sayfa_numarasi_ayarla(belge.sections[1], "lowerRoman", 1)
    _dipnot_sayfa_no(belge, 1)
    belge.add_heading("ÖZET", level=1)
    belge.add_paragraph("[ÖZET metni: tez yazari tarafindan yazilir.]")
    p = belge.add_paragraph("Anahtar kelimeler: [anahtar kelime 1, anahtar kelime 2]")

    # --- 3. abstract: devam ------------------------------------
    belge.add_section()
    _sayfa_numarasi_ayarla(belge.sections[2], "lowerRoman", None)
    _dipnot_sayfa_no(belge, 2)
    belge.add_heading("ABSTRACT", level=1)
    belge.add_paragraph("[Abstract text: written by the thesis author.]")
    p = belge.add_paragraph("Keywords: [keyword 1, keyword 2]")

    # --- 4. icindekiler: devam + TOC alani ---------------------
    belge.add_section()
    _sayfa_numarasi_ayarla(belge.sections[3], "lowerRoman", None)
    _dipnot_sayfa_no(belge, 3)
    belge.add_heading("İÇİNDEKİLER", level=1)
    _alan_yaz(
        belge.add_paragraph(),
        'TOC \\o "1-2" \\h \\z \\u',
        "İçindekileri güncellemek için: Word'de Ctrl+A, sonra F9.",
        kirli=True,
    )
    # Word dosya acildiginda alanlari hesaplasin; aksi halde TOC BOS
    # gorunur ve kullanici "icindekiler yok" sanir.
    ayarlar = belge.settings.element
    guncelle = OxmlElement("w:updateFields")
    guncelle.set(qn("w:val"), "true")
    ayarlar.append(guncelle)

    # --- 5. govde: arabic rakam, 1'den baslar ------------------
    belge.add_section()
    _sayfa_numarasi_ayarla(belge.sections[4], "decimal", 1)
    _dipnot_sayfa_no(belge, 4)

    for bolum in _sirali_bolumler(durum):
        numara = bolum.get("number")
        bas = belge.add_heading(
            "{}. {}".format(numara, (bolum.get("title") or "").strip()), level=1
        )
        bas.alignment = WD_ALIGN_PARAGRAPH.CENTER
        bas.paragraph_format.page_break_before = True

        son_baslik = ""
        for alt_baslik, metin in _metinli_paragraflar(bolum):
            if alt_baslik and alt_baslik != son_baslik:
                alt = belge.add_heading(alt_baslik, level=2)
                alt.alignment = WD_ALIGN_PARAGRAPH.LEFT
                alt.paragraph_format.keep_with_next = True
                son_baslik = alt_baslik
            p = belge.add_paragraph(metin)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            pf = p.paragraph_format
            pf.first_line_indent = govde_girinti
            # Satir araligi `Normal` stilinde de var ama burada ACIKCA
            # yazilir: stil degistirilse veya bir arac duz (direct)
            # bicimle yuklense paragraf yine 1.5 kalsin. Miras alinan
            # deger `paragraph_format.line_spacing` icin `None` doner;
            # yani yazmazsak etkin deger okunmaz olur.
            pf.line_spacing = 1.5

    belge.add_heading("KAYNAKÇA", level=1)
    girisler = kaynakca_satirlari(durum)
    if not girisler:
        girisler = ["Kaynakça boş: metinde atıf gösteren kaynak yok."]
    for giris in girisler:
        p = belge.add_paragraph(giris)
        # Asili girinti: sola 1.25 cm, ilk satir -1.25 cm. APA 7 ve
        # TR universite kilavuzlari ikisini birlikte ister; yalniz sola
        # girinti verilirse ikinci satir hizalanir, asili girinti olmaz.
        p.paragraph_format.left_indent = govde_girinti
        p.paragraph_format.first_line_indent = -govde_girinti
        p.paragraph_format.line_spacing = 1.5

    belge.add_paragraph(EKLER_NOTU)

    tampon = _io.BytesIO()
    belge.save(tampon)
    return tampon.getvalue()


def docx_uret(durum: dict[str, Any], yol: Path) -> Path:
    """Tezi Word (.docx) belgesine yazar.

    OOXML Unicode'tur; Turkce harfler icin ek kodlama gerekmez.
    """
    yol = Path(yol)
    yol.write_bytes(docx_belgesi(durum))
    return yol


def pdf_uret(durum: dict[str, Any], yol: Path) -> Path:
    """Tezi PDF olarak yazar.

    Turkce harfler icin sistemdeki bir Unicode TTF kullanilir; bulunamazsa
    sessizce '?' basmak yerine hata verilir.
    """
    from fpdf import FPDF

    yazi_tipi = yazi_tipi_yolu()
    if yazi_tipi is None:
        raise ExportHatasi(
            "PDF için Unicode yazı tipi bulunamadı. fpdf2'nin gömülü "
            "fontu cp1252 kodlamasını kullanır ve Türkçenin 'ğ ı ş İ Ğ Ş' "
            "harflerini basamaz. Şunlardan birini kurun ya da yolunu "
            "`YAZI_TIPI_ADAYLARI` listesine ekleyin: " + ", ".join(
                Path(a).name for a in YAZI_TIPI_ADAYLARI[:3]
            )
        )

    _dogrula(durum)

    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("tez", "", str(yazi_tipi))

    pdf.set_font("tez", size=16)
    pdf.multi_cell(
        w=0, h=10, text=durum.get("title") or "Başlıksız Tez", align="C"
    )
    pdf.ln(4)

    pdf.set_font("tez", size=12)
    for bolum in _sirali_bolumler(durum):
        baslik = "{} {}".format(bolum.get("number"), (bolum.get("title") or "").strip())
        pdf.multi_cell(w=0, h=8, text=baslik)
        pdf.ln(2)
        for metin in _metinler(bolum):
            pdf.multi_cell(w=0, h=6, text=metin)
            pdf.ln(3)
        pdf.ln(2)

    pdf.multi_cell(w=0, h=8, text="Kaynakça")
    pdf.ln(2)
    girisler = kaynakca_satirlari(durum)
    for giris in girisler or ["> Kaynakça boş: metinde atıf gösteren kaynak yok."]:
        pdf.multi_cell(w=0, h=6, text=giris)
        pdf.ln(2)

    pdf.multi_cell(w=0, h=6, text=EKLER_NOTU)
    pdf.output(str(yol))
    return yol


# --- dosya adi --------------------------------------------------------------

_KOTU_KARAKTER = re.compile(r"[^0-9A-Za-z_-]+")


def _dosya_adi_govdesi(tez_kimligi: str) -> str:
    """`thesis_id` degerini guvenli dosya adi govdesine cevirir.

    `thesis new` kimligi DOGRULAMADAN kabul ediyor. `../../kotu` gibi bir
    deger dosyayi hedef disinin disina yazardi. Burada nokta dahil her
    ayirici karakter `_` olur, ardlik `_` teke indirilir ve bastaki
    `_` kirpilir; boylece dizin disina cikilamaz.
    """
    govde = _KOTU_KARAKTER.sub("_", (tez_kimligi or "").strip())
    while "__" in govde:
        govde = govde.replace("__", "_")
    govde = govde.strip("_")[:60].strip("_")
    return govde or "tez"


# --- genel giris noktasi ----------------------------------------------------

def disa_aktar(
    durum: dict[str, Any],
    bicimler,
    dizin: Path,
) -> tuple[list[Path], list[str]]:
    """Tezi `dizin` icine yazar; (dosya yollari, notlar) dondurur.

    `bicimler` tek bir bicim adi (`"md"`) ya da sirali bicim listesi
    (`["md", "docx"]`) olabilir. Tekil yazim geriye uyumludur.

    HEP YA HIC
    ----------
    Tum bicimler ONCE bellekte uretilir; hepsi basarili olmadan
    HICBIR dosya yazilmaz. Gerekce: yari teslim bir teslim degildir.
    Kullanici "export calisti" gorup eksik dosyayi aramaz; sonra
    hatayi gordugunde ciktinin hangi cikti oldugu belirsizdir.

    Bicim desteklenmiyorsa, veri butunlugu bozuksa veya PDF icin yazi
    tipi yoksa `ExportHatasi` firlatir ve dizin BOS kalir.
    """
    istek = [bicimler] if isinstance(bicimler, str) else list(bicimler)
    # Sirasi korunur, tekrarlar dusurulur: ayni bicim iki kez istenmisse
    # iki dosya yazilmaz.
    sirali: list[str] = []
    for bicim in istek:
        if bicim not in DESTEKLENEN_BICIMLER:
            raise ExportHatasi(
                "Desteklenmeyen biçim: {0!r}. Desteklenen biçimler: {1}.".format(
                    bicim, ", ".join(sorted(DESTEKLENEN_BICIMLER))
                )
            )
        if bicim not in sirali:
            sirali.append(bicim)
    if not sirali:
        raise ExportHatasi("Hiçbir çıktı biçimi istenmedi.")

    _dogrula(durum)

    govde = _dosya_adi_govdesi(durum.get("thesis_id"))
    dizin = Path(dizin)
    uzanti = {"md": "md", "docx": "docx", "pdf": "pdf"}

    notlar = [
        "Ekler (appendix) bu sürümde dışa aktarılmıyor: durum şemasında "
        "`appendices` alanı yok.",
        "Kaynakça yalnızca metinde atıf gösterilen {0} kaynağı içerir.".format(
            len(atiflanan_kaynak_kimlikleri(durum))
        ),
        "Kapak, özet, abstract ve anahtar kelimeler `[...]` yer tutucu "
        "olarak bırakıldı: tez yazarı tarafından doldurulur.",
    ]

    # 1) HEPSINI bellekte uret
    icerikler: list[tuple[Path, object]] = []
    for bicim in sirali:
        yol = dizin / "tez_{0}.{1}".format(govde, uzanti[bicim])
        if bicim == "md":
            icerikler.append((yol, markdown_uret(durum)))
        elif bicim == "docx":
            icerikler.append((yol, docx_belgesi(durum)))
        else:
            if yazi_tipi_yolu() is None:
                raise ExportHatasi(
                    "PDF için Unicode yazı tipi bulunamadı. Markdown/Word "
                    "çıktısı için `--format md docx` kullanın."
                )
            # fpdf2 dosyaya yazmak zorunda; gecici dosyaya yazip okunur.
            gecici = dizin / "tez_{0}.pdf.gecici".format(govde)
            try:
                pdf_uret(durum, gecici)
                icerikler.append((yol, gecici.read_bytes()))
            finally:
                gecici.unlink(missing_ok=True)
            notlar.append(
                "PDF, sistemdeki Unicode yazı tipiyle üretildi: {0}".format(
                    yazi_tipi_yolu()
                )
            )

    # 2) hepsi basarili: yaz
    dizin.mkdir(parents=True, exist_ok=True)
    yollar: list[Path] = []
    for yol, icerik in icerikler:
        if isinstance(icerik, bytes):
            yol.write_bytes(icerik)
        else:
            yol.write_text(icerik, encoding="utf-8")
        yollar.append(yol)

    return yollar, notlar
    return yol, notlar
