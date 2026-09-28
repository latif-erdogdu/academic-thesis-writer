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
from pathlib import Path
from typing import Any

DESTEKLENEN_BICIMLER = ("md", "docx", "pdf")

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

# Turkce alfabetik siralama. Iki gercek tuzak var:
#
# 1. Kod noktasi sirasi Turkce siralamayi BOZAR: `ç` (U+00E7) `d` (U+0064)
#    sonra gelir ama `ğ` (U+011F) `ı` (U+0131) ve `ş` (U+015F) `ö` (U+00F6)
#    ONUNCE gelir. Yani alfabetik degil, kod birligi sirasi olur.
# 2. `ı` (U+0131) Turkce alfabede `i`'den ONCE gelir (h ı i j). Ilk deneme
#    `ı` -> "i{" eslemesiyle bunu ters cevirmisti ve "i" her zaman once
#    geliyordu. Testler o an yalnizca aksansiz harfleri sinadigi icin
#    hata gecmisti.
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
# casefold() kullanilmaz: 'İ'.casefold() iki kod noktali 'i' + U+0307
# uretir ve sira tablosuna girmeyen bir karakter birakiyordu. Turkce
# buyuk harfler tek tek eslenir.
_KUCULTME = str.maketrans("ABCÇFGĞHIİÖŞÜ", "abcçfgğhıiöşü")


class ExportHatasi(RuntimeError):
    """Disa aktarma yapilamadi: bicim hatasi veya veri butunlugu.

    `RuntimeError` alt sinifi: cagiran kod hatayi yakalayip kullanicya
    acik bir mesaj gosterebilir.
    """


# --- siralama ---------------------------------------------------------------

def turkce_siralamasi(metin: str) -> str:
    """Turkce alfabetik siralama anahtari dondurur.

    Turkce alfabetinde `c` ardindan gelenler `c, cc, cci, ccik, ccil`
    sirasiyla gelir; ayni durum `g/ğ`, `s/ş`, `u/ü` ailelerinde de
    gecerlidir. Ayrica `ı` `i`'den, `ö` `o`'dan, `ü` `u`'dan ONCE gelmez
    ama once `ı` vardir: h ı i j.

    Buyuk/kucuk harf duyarsizdir; yerel ayara bagli DEGILDIR.
    Alfabet disi karakterler (rakam, noktalama) en sona duser.
    """
    metin = (metin or "").translate(_KUCULTME)
    return "".join(_HARF_SIRASI.get(harf, "99") for harf in metin)


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


def _kaynak_siralamasi(kaynak: dict[str, Any]) -> tuple[str, str, str]:
    """Ilk yazar soyadi, sonra baslik, sonra kimlik.

    Son iki anahtar TEKRAR EDEN yazarlarda siranin kararli (deterministik)
    olmasini saglar. Yazar yoksa `~` isareti alfabetik sona dusurur.
    """
    yazarlar = kaynak.get("authors") or []
    ilk = turkce_siralamasi(yazarlar[0]) if yazarlar else "~"
    return (
        ilk,
        turkce_siralamasi(kaynak.get("title") or ""),
        turkce_siralamasi(kaynak.get("id") or ""),
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


def _metinler(bolum: dict[str, Any]) -> list[str]:
    """Bolumdeki bos olmayan paragraf metinleri.

    Bos paragraf ATLANIR: metni olmayan paragraf ciktiya bosluk birakir ve
    `P-999` gibi bir kimlik tasimaz, cunku kimlikler okuyucuya gosterilmez.
    """
    return [
        (paragraf.get("text") or "").strip()
        for paragraf in bolum.get("paragraphs") or []
        if (paragraf.get("text") or "").strip()
    ]


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
    """Tezi Markdown metnine cevirir."""
    _dogrula(durum)
    satirlar: list[str] = ["# {}".format(durum.get("title") or "Başlıksız Tez"), ""]

    for bolum in _sirali_bolumler(durum):
        numara = bolum.get("number")
        baslik = (bolum.get("title") or "").strip()
        satirlar.append("## {}. {}".format(numara, baslik))
        satirlar.append("")
        for metin in _metinler(bolum):
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


def docx_uret(durum: dict[str, Any], yol: Path) -> Path:
    """Tezi Word (.docx) belgesine yazar.

    OOXML Unicode'tur; Turkce harfler icin ek kodlama gerekmez.
    """
    from docx import Document  # iceri aktarma: yalnizca bu bicimde gerekir

    belge = Document()
    belge.add_heading(durum.get("title") or "Başlıksız Tez", level=0)

    for bolum in _sirali_bolumler(durum):
        baslik = "{} {}".format(bolum.get("number"), (bolum.get("title") or "").strip())
        belge.add_heading(baslik, level=1)
        for metin in _metinler(bolum):
            belge.add_paragraph(metin)

    belge.add_heading("Kaynakça", level=1)
    girisler = kaynakca_satirlari(durum)
    if girisler:
        for giris in girisler:
            belge.add_paragraph(giris)
    else:
        belge.add_paragraph("Kaynakça boş: metinde atıf gösteren kaynak yok.")
    belge.add_paragraph(EKLER_NOTU)

    belge.save(str(yol))
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
    bicim: str,
    dizin: Path,
) -> tuple[Path, list[str]]:
    """Tezi `dizin` icine yazar; (dosya yolu, notlar) dondurur.

    Bicim desteklenmiyorsa, veri butunlugu bozuksa veya PDF icin yazi tipi
    yoksa `ExportHatasi` firlatir ve HICBIR dosya yazmaz.
    """
    if bicim not in DESTEKLENEN_BICIMLER:
        raise ExportHatasi(
            "Desteklenmeyen biçim: {0!r}. Desteklenen biçimler: {1}.".format(
                bicim, ", ".join(sorted(DESTEKLENEN_BICIMLER))
            )
        )

    _dogrula(durum)

    uzanti = {"md": "md", "docx": "docx", "pdf": "pdf"}[bicim]
    govde = _dosya_adi_govdesi(durum.get("thesis_id"))
    yol = Path(dizin) / "tez_{0}.{1}".format(govde, uzanti)

    notlar = [
        "Ekler (appendix) bu sürümde dışa aktarılmıyor: durum şemasında "
        "`appendices` alanı yok.",
        "Kaynakça yalnızca metinde atıf gösterilen {0} kaynağı içerir.".format(
            len(atiflanan_kaynak_kimlikleri(durum))
        ),
    ]
    if bicim == "pdf":
        notlar.append(
            "PDF, sistemdeki Unicode yazı tipiyle üretildi: {0}".format(
                yazi_tipi_yolu()
            )
        )

    if bicim == "md":
        yol.write_text(markdown_uret(durum), encoding="utf-8")
    elif bicim == "docx":
        docx_uret(durum, yol)
    else:
        pdf_uret(durum, yol)

    return yol, notlar
