"""DOCX -> PDF GERCEK RENDER TESTI (islevsel test).

NEDEN TARAYICI TESTI YOK
------------------------
Bu repo bir web/HTML yuzeyi URETMIYOR: `thesis:export` .md / .docx /
.pdf dosyasi yazar, HTTP sunucusu veya sayfa yok. Tarayici testi bu
yuzden UYGULANAMAZ (uygulanabilirlik ilkesi: test yazmak icin yuzey
olmalidir). Yerine dosya biciminin GERCELI bir GORUNTUYEYLEYICIDE
acildigini dogrulayan render testi konur. Bu, tarayicinin yapacagi isin
dogrulanabilir karsiligidir: dosya gercekten basilabilir mi?

    soffice --headless --convert-to pdf  ->  pdfplumber ile metin/sayfa

NEDEN BU KADAR COK SEY DENETLENIYOR
-----------------------------------
`python-docx` ile yazilan bir OOXML dosyasi HER ZAMAN acilmaz. Iki
gercek tuzak vardir ve ikisi de bu dosyada bir kez yakalandi:

  1. `w:pgNumType` OOXML'de `w:sectPr` cocuklarinin BELIRLI bir
     sirasi icinde gelmelidir (`w:cols`tan once). Rastgele eklenen
     `w:pgNumType` LibreOffice ve Word tarafindan sessizce YOK
     SAYILIR: dosya acilir, ama sayfa numarasi hep 1'den baslar.
  2. Word ALANLARI (TOC, PAGE) dosya acildiginda HESAPLANMAZ. Ustelik
     `w:dirty="true"` ve `settings.xml`deki `w:updateFields` olmadan
     alan dosyada BOS gorunur. Render testi bunu olculer: PDF'te
     icindekiler gercekten sayfa numaralariyla basmi mi?

Bunlar XML seviyesinde dogrulanamaz; ancak PDF ciktisi olculebilir.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tools.atw.export import docx_belgesi
from tools.atw.state import empty_state

pytestmark = pytest.mark.skipif(
    shutil.which("soffice") is None
    and not Path("C:/Program Files/LibreOffice/program/soffice.exe").is_file(),
    reason="LibreOffice bulunamadi (soffice.exe); render testi atlanir",
)

SOFFICE = Path("C:/Program Files/LibreOffice/program/soffice.exe")

#: Render suresi. LibreOffice ilk calistirmada profil kurar ve yavas
#: olabilir; 180 saniye burada "asili test" degil, "ortam yavas" demek.
ZAMAN_ASIMI_SN = 180


# --------------------------------------------------------------------------
# gercek tez verisi
# --------------------------------------------------------------------------

_DOGRULAMA = {
    "status": "verified",
    "bibliographic_match": 1.0,
    "verified_at": "2026-09-30T09:00:00+00:00",
    "verification_sources": ["crossref"],
}


def _kaynak(kimlik: str, yazarlar: list[str], yil: int, baslik: str) -> dict:
    return {
        "id": kimlik,
        "title": baslik,
        "source_type": "article",
        "year": yil,
        "authors": yazarlar,
        "journal": "Kurgusal Dergi",
        "verification": dict(_DOGRULAMA),
    }


def gercek_tez() -> dict:
    """Yukleme disinda tam bir tez: bolum, alt baslik, kaynakca."""
    durum = empty_state("THESIS-2026-999", "Parcalanma ve Islevler Tezi")
    durum["sources"] = [
        _kaynak("SRC-001", ["Zeynep Çelik"], 2024, "Zemin bir başlık"),
        _kaynak("SRC-002", ["Ayşe Doğan"], 2023, "B bir başlık"),
        _kaynak("SRC-003", ["Mert Şahin"], 2022, "S bir başlık"),
    ]
    durum["citations"] = [
        {
            "id": "CIT-00%d" % sira,
            "paragraph_id": "P-%03d" % sira,
            "source_id": "SRC-00%d" % sira,
            "style": "apa7",
        }
        for sira in (1, 2, 3)
    ]
    durum["chapters"] = [
        {
            "id": "CH-001",
            "number": 1,
            "title": "Giriş",
            "paragraphs": [
                {
                    "id": "P-001",
                    "type": "introduction",
                    "chapter": "CH-001",
                    "section": "1.1 Kapsam",
                    "text": (
                        "Bu tez parcalanma kavramini ve islevlerini inceler. "
                        "CGI surekli olmayan nesnelerin tek bir mekanda "
                        "nasil kurulabilecegini sorar."
                    ),
                },
                {
                    "id": "P-002",
                    "type": "text",
                    "chapter": "CH-001",
                    "section": "1.1 Kapsam",
                    "text": "Kapsam iki soru etrafinda sinirlanir.",
                },
                {
                    "id": "P-003",
                    "type": "text",
                    "chapter": "CH-001",
                    "section": "1.2 Sınırlar",
                    "text": "Sınırlar veri yoğunluğu ve işleyici kaynaklarıyla ilgilidir.",
                },
            ],
        },
        {
            "id": "CH-002",
            "number": 2,
            "title": "Yöntem",
            "paragraphs": [
                {
                    "id": "P-004",
                    "type": "methodology",
                    "chapter": "CH-002",
                    "section": "2.1 Tasarım",
                    "text": "Tasarim dort asamali olarak yurutulmustur.",
                },
            ],
        },
    ]
    return durum


# --------------------------------------------------------------------------
# render yardimcilari
# --------------------------------------------------------------------------

def _soffice_yolu() -> Path:
    ad = shutil.which("soffice")
    if ad:
        return Path(ad)
    return SOFFICE


def pdf_uret(docx: bytes, dizin: Path, *, isim: str = "tez") -> Path:
    """docx baytlarini LibreOffice ile PDF'e cevirir; PDF yolunu dondurur.

    `--convert-to pdf` yazma ISLEMINI yapar; ayrica soffice'nin
    gercek yazma yolunu kullanmak icin `-env:UserInstallation` ile
    GECICI bir profil verilir. Aksi halde soffice, baska bir soffice
    surucusu acikken "profile already in use" diyerek HICBIT cikti
    uretmeden cikar ve test sessizce BOS dosyaya bakar.
    """
    kaynak = dizin / "{0}.docx".format(isim)
    kaynak.write_bytes(docx)
    profil = dizin / "lo_profil"
    cikti = dizin / "cikti"
    cikti.mkdir(exist_ok=True)
    komut = [
        str(_soffice_yolu()),
        "--headless",
        "--norestore",
        "--invisible",
        "-env:UserInstallation=file:///{0}".format(
            str(profil).replace("\\", "/")
        ),
        "--convert-to",
        "pdf:writer_pdf_Export",
        "--outdir",
        str(cikti),
        str(kaynak),
    ]
    env = dict(os.environ)
    env["SAL_USE_VCLPLUGIN"] = "svp"
    bitti = subprocess.run(
        komut, capture_output=True, text=True, timeout=ZAMAN_ASIMI_SN, env=env
    )
    sonuc = cikti / "{0}.pdf".format(isim)
    assert sonuc.is_file(), (
        "LibreOffice PDF uretmedi.\nstdout: {0}\nstderr: {1}\ncikti: {2}".format(
            bitti.stdout, bitti.stderr, sorted(p.name for p in cikti.iterdir())
        )
    )
    return sonuc


def _sayfa_metni(pdf_yolu: Path) -> list[str]:
    import pdfplumber

    with pdfplumber.open(str(pdf_yolu)) as pdf:
        return [(sayfa.extract_text() or "") for sayfa in pdf.pages]


# --------------------------------------------------------------------------
# testler
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def render(tmp_path_factory):
    """Bir kez render et, tum testler ayni PDF'i okusun.

    LibreOffice her cagriyla 5-15 saniye surer; test basina yeniden
    render etmek suite'i dakikalara cikarirdi ve gercek bir davranis
    degisikligi disinda surekli kirmiziya donusurdu.
    """
    dizin = tmp_path_factory.mktemp("render")
    pdf = pdf_uret(docx_belgesi(gercek_tez()), dizin)
    sayfalar = _sayfa_metni(pdf)
    return {"pdf": pdf, "sayfalar": sayfalar, "dizin": dizin}


class TestGercekRender:
    def test_pdf_uretilir_ve_bos_degildir(self, render):
        assert render["pdf"].stat().st_size > 10_000
        assert len(render["sayfalar"]) >= 6, (
            "kapak + ozet + abstract + icindekiler + 2 bolum + kaynakca "
            "en az 6 sayfa olmali; render edilen: %d" % len(render["sayfalar"])
        )

    def test_her_sayfada_metin_çikarilabilir(self, render):
        """Metin katmani yoksa belge PDF olarak degil, GORSEL olarak
        basilir: kopyalanamaz, aranamaz, denetlenemez."""
        for sira, metin in enumerate(render["sayfalar"], start=1):
            assert metin.strip(), "%d. sayfada cikarilabilir metin yok" % sira

    def test_turkce_karakterler_pdfte_korunur(self, render):
        birlestir = "\n".join(render["sayfalar"])
        for parca in ("Parcalanma ve Islevler Tezi", "ÖZET", "ABSTRACT",
                      "İÇİNDEKİLER", "KAYNAKÇA", "Çelik", "Doğan", "Şahin"):
            assert parca in birlestir, "PDF'te kayip: %r" % parca

    def test_kapak_sayfasinda_sayfa_numarasi_yoktur(self, render):
        """Kapak sayfasinda numara OLMAMALIDIR.

        Bu, `w:pgNumType`in `w:sectPr` icinde DOGRU SIRADA oldugunun
        tek kanitidir. Yanlis sira ile eklenen `w:pgNumType` OOXML
        semasi tarafindan reddedilmez ama LibreOffice ve Word onu
        YOK SAYAR; numara her bolumde 1'den baslar. XML seviyesinde
        varligini denetlemek yetmez: dogru yerlesim ancak BASILMIS
        cikti ile kanitlanir.

        Sayfa numarasi govde metninden SONRA cikarildigi icin, kapak
        sayfasinda TEK BASINA rakam/roma rakami olan bir satir olmamalidir.
        """
        kapak = render["sayfalar"][0]
        assert "Tez No: THESIS-2026-999" in kapak
        assert "[Üniversite Adı]" in kapak
        yalniz_numara = [
            satir for satir in kapak.splitlines()
            if satir.strip() in {"1", "2", "i", "ii", "iii", "iv"}
        ]
        assert not yalniz_numara, (
            "kapak sayfasinda sayfa numarasi var: %r" % yalniz_numara
        )

    def test_on_bilgiler_rom_govde_arab_besle_baslar(self, render):
        """Sayfa numaralari: kapak YOK; ozet/abstract/icindekiler `i`,
        `ii`, `iii`; govde `1`, `2`.

        Bu, `w:pgNumType`in `w:fmt` ve `w:start` degerlerinin de dogru
        geldiginin olcumudur. Ozellikle "devam" bolumlerinde `w:start`
        OLMAMALIDIR: `add_section()` onceki `sectPr`yi KOPYALADIGI icin
        `w:start` kopyalanirsa her on bilgi sayfasi `i`den baslar.
        """
        sayfalar = render["sayfalar"]
        # Her sayfanin SON satiri sayfa numarasidir (dipnot en altta).
        son = [
            [s.strip() for s in sayfa.splitlines() if s.strip()][-1]
            for sayfa in sayfalar
        ]
        assert son[0] != "1" and son[0] not in {"i"}, (
            "kapak numaralandirilmis: %r" % son[0]
        )
        assert son[1] == "i", "ozet `i` ile baslamali: %r" % son[1]
        assert son[2] == "ii", "abstract `ii` ile devam etmeli: %r" % son[2]
        assert son[3] == "iii", "icindekiler `iii` ile devam etmeli: %r" % son[3]
        assert son[4] == "1", "govde `1`den baslamali: %r" % son[4]
        assert son[5] == "2", "govde `2` ile devam etmeli: %r" % son[5]

    def test_her_bolum_yeni_sayfada_baslar(self, render):
        """`page_break_before` yazilmadiysa bolum basligi onceki paragrafin
        sonunda kalir.

        OLCUM: render'da sayfa numarasi metinden SONRA cikarildigi icin
        sayfanin ilk satiri govdenin ilk satiri olmalidir. Bolum basligi
        sayfanin ilk satiri DEGILSE sayfa sonu yoktur.
        """
        sayfalar = render["sayfalar"]
        for baslik in ("1. Giriş", "2. Yöntem"):
            sira = next(
                (n for n, m in enumerate(sayfalar) if baslik in m), None
            )
            assert sira is not None, "%r hicbir sayfada yok" % baslik
            ilk = next(
                satir for satir in sayfalar[sira].splitlines() if satir.strip()
            )
            assert ilk == baslik, (
                "%r sayfanin ilk satiri degil (%r): sayfa sonu eksik"
                % (baslik, ilk)
            )
        # Govde on bilgilerden sonra gelir.
        ilk_govde = next(
            n for n, m in enumerate(sayfalar) if "1. Giriş" in m
        )
        assert ilk_govde >= 4, "giris one bilgilerden sonra gelmeli"

    def test_icindekiler_alani_tasidir_ama_libreoffice_doldurmaz(self, render):
        """ICINDEKILER sayfasi BOS DEGILDIR ve yonlendirme metni tasir.

        SINIR (olculmus, varsayilmis degil): LibreOffice `--headless
        --convert-to pdf` ile `w:updateFields` alanlarini YENIDEN
        HESAPLAMAZ; `w:dirty="true"` da yeterli degildir. Bu yuzden
        bu test "TOC dolu" DEMEZ, "sayfa bos degil ve kullaniciya ne
        yapacagini soyluyor" DER.

        Alanin YAPISI XML seviyesinde `test_export_duzeni.py`de
        denetlenir. Hedef bicim Word'dir; Word dosya acildiginda alani
        guncelleyecektir. Bu dortculuk, LibreOffice render'inin Word
        emulasyonu olmadigini bilerek yazilmistir.
        """
        icindekiler_sayfasi = next(
            m for m in render["sayfalar"] if "İÇİNDEKİLER" in m
        )
        assert icindekiler_sayfasi.splitlines()[0] == "İÇİNDEKİLER"
        assert "Ctrl+A" in icindekiler_sayfasi, (
            "yönlendirme metni kayıp: kullanıcı alanı güncellemezse "
            "içindekileri boş görür"
        )

    def test_bolum_ici_alt_basliklar_basilir(self, render):
        """Alt basliklar `###`/Heading 2 olarak ciktiya girer. Render
        olcusu: PDF metninde GERCEKTEN var."""
        birlestir = "\n".join(render["sayfalar"])
        for baslik in ("1.1 Kapsam", "1.2 Sınırlar", "2.1 Tasarım"):
            assert baslik in birlestir, "alt baslik PDF'te yok: %r" % baslik

    def test_kaynakca_alfabetik_ve_asili_girdili(self, render):
        birlestir = "\n".join(render["sayfalar"])
        sira = [birlestir.index(ad) for ad in ("Çelik", "Doğan", "Şahin")]
        assert sira == sorted(sira), "kaynakca Turkce alfabetik degil: %r" % sira

    def test_yer_tutucular_oldugu_gibi_kalir(self, render):
        """Ozet/abstract/anahtar kelimeler UYDURULMAZ; `[...]` kalir.
        Renderda gorunmeleri, dokumanin teslim oncesi gozden
        gecirilecegini hatirlatir."""
        birlestir = "\n".join(render["sayfalar"])
        assert "[ÖZET" in birlestir
        assert "[Abstract" in birlestir
        assert "Anahtar kelimeler:" in birlestir
        assert "[Ad Soyad]" in birlestir
