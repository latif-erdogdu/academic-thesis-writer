"""`thesis:export` CIKTI DUZENI — kolasyon, alt baslik, akademik Word olcusu.

Kanonik sozlesme: `references/approval_gates.md` (kapilar) ve
`references/citation_rules.md` (kaynakca sirasi). Bu dosya bir bicim
TERCIHI degil, bir HATA sinifini kovar:

    "Metin dogru ama BELGE yanlis uretiliyorsa, cikti denetimden gecmis
     sayilir. En kotu durum budur: sistem kendini dogru gosteriyor."

Uc gercek kusur burada kilitlenir (her biri teslim edilmis bir tezde
gozlemlenmistir):

  1. Turkce kolasyon ASCII buyuk harfleri kucultmez. `Ewers` anahtari
     "99..." olur, `Farkas` "05..." olur; sonuc: Ewers, KELT, Parmesan...
     hepsi alfabetik SONUNA dusar.
  2. Kaynak sirasi yazarinin TAM adini kullanir, soyadini degil.
     "Riana Gardiner" -> "ri", "Gian-Reto Walther" -> "gi": alfabetik
     siralamada Gardiner once cikmamasi gerekirken once geliyor.
  3. `paragraph.section` hic okunmaz. 52 adet "1.1" / "2.3" alt basligi
     ciktiya hic girmez; bolum ici yapisi kaybolur.

Bir digeri bu dosyada degil, `test_export_coklu_bicim` altinda: `--format`
verilmediginde yalniz Markdown uretiliyordu. Teslim edilebilir bicim Word'du;
"calisti" diye cikti uretmeyen bir komut, teslim edilebilir cikti
uretmiyor demektir.
"""
from __future__ import annotations

import copy
from pathlib import Path

import pytest

from tools.atw.export import (
    DEFAULT_BICIMLER,
    disa_aktar,
    docx_uret,
    kaynakca_girdileri,
    markdown_uret,
    turkce_siralamasi,
)
from tools.atw.state import empty_state

# --------------------------------------------------------------------------
# fixture yardimcilari
# --------------------------------------------------------------------------

_DOGRULAMA = {
    "status": "verified",
    "bibliographic_match": 1.0,
    "verified_at": "2026-09-30T09:00:00+00:00",
    "verification_sources": ["crossref"],
}


def _kaynak(kimlik: str, yazarlar: list[str] | None = None, **ek) -> dict:
    kaynak = {
        "id": kimlik,
        "title": ek.pop("baslik", "Kurgusal başlık"),
        "source_type": "article",
        "verification": copy.deepcopy(_DOGRULAMA),
    }
    if yazarlar is not None:
        kaynak["authors"] = list(yazarlar)
    kaynak.update(ek)
    return kaynak


def _atif(kimlik: str, kaynak_id: str) -> dict:
    return {
        "id": kimlik,
        "paragraph_id": "P-001",
        "source_id": kaynak_id,
        "style": "apa7",
    }


def _paragraf(kimlik: str, metin: str, *, bolum_basligi: str | None = None) -> dict:
    paragraf = {"id": kimlik, "type": "text", "text": metin}
    if bolum_basligi is not None:
        paragraf["section"] = bolum_basligi
    return paragraf


def _bolum(kimlik: str, numara: int, baslik: str, paragraflar: list[dict]) -> dict:
    return {"id": kimlik, "number": numara, "title": baslik, "paragraphs": paragraflar}


def _tez(*bolumler: dict, **ek) -> dict:
    """Tek bolumlu, kaynakcasi bos ama yazilabilir bir tez durumu."""
    durum = empty_state("THESIS-2026-002", "Sınama Tezi")
    if not bolumler:
        bolumler = (
            _bolum(
                "CH-001",
                1,
                "Giriş",
                [_paragraf("P-001", "Bu bölüm teze giriş yapar.")],
            ),
        )
    durum["chapters"] = list(bolumler)
    durum["citations"] = ek.pop("citations", [])
    durum["sources"] = ek.pop("sources", [])
    durum.update(ek)
    return durum


def _yazarlarla(yazarlar: list[tuple[str, list[str]]]) -> list[dict]:
    """[(kaynak_id, [yazar, ...]), ...] -> atiflanmis ve sirali kaynaklar."""
    durum = _tez()
    durum["sources"] = [_kaynak(kimlik, yazarlar) for kimlik, yazarlar in yazarlar]
    durum["citations"] = [
        _atif("CIT-%03d" % sira, kimlik)
        for sira, (kimlik, _) in enumerate(yazarlar, start=1)
    ]
    return kaynakca_girdileri(durum)


# --------------------------------------------------------------------------
# 1. Turkce kolasyon
# --------------------------------------------------------------------------

class TestTurkceKolasyon:
    """`turkce_siralamasi` her alfabet icin GECERLI bir anahtar uretmeli.

    Anahtar, alfabet disi karakter icin "99" uretiyordu. Bu, ASCII buyuk
    harflerin kucultulmedigi icin butun latin yazarlarin sona dustugu
    anlamina geliyordu. Anahtar, alfabet disi karakteri olmayan BIR
    metnin karsilastirilabilir olmasini garanti etmelidir.
    """

    def test_ascii_buyuk_harfler_kucukler(self):
        # `E` tabloya girmezse "99" + "21..." olur ve `Farkas`'in once
        # gelmesine yol acar. Dogru sonuc: Ewers once.
        assert turkce_siralamasi("Ewers") < turkce_siralamasi("Farkas")

    def test_karisilastirilabilir_anahtar_uretir(self):
        """Alfabet disi karakter anahtari bozmamali.

        "Zorlu" icinde nokta olmamali; nokta "99" olsaydi "Zorlu" her
        seyden sonra gecer ve alfabet icinde yerini yitirirdi.
        """
        assert "99" not in turkce_siralamasi("Zorlu")

    def test_aksanli_latin_harf_indirgenir(self):
        """`é` Turkce alfabesinde yok; kod noktasi sirasi alfabetik degil.

        `Andrén` -> `andren` olmali, boylece `Andzic` oncesinde gelir.
        """
        assert turkce_siralamasi("Andrén") < turkce_siralamasi("Andzic")

    def test_birlestirilen_isaretler_silinir(self):
        """NFD ayrisimi olmadan `é` "a + birlesik isaret" kalir ve
        tabloya giremez."""
        import unicodedata

        nfd = unicodedata.normalize("NFD", "Andrén")
        assert turkce_siralamasi(nfd) == turkce_siralamasi("Andrén")

    def test_turkce_buyuk_harfler_kucukler(self):
        """Turkce BUYUK harf kurali: `i` -> `İ`, `ı` -> `I`.

        Anahtar `ÇELİK` ile `Çelik`i eslestirmelidir.
        """
        assert turkce_siralamasi("ÇELİK") == turkce_siralamasi("Çelik")

    def test_noktasiz_i_buyuk_harf_turkce_kuralina_uyar(self):
        """`I` Turkce kuralina gore `ı`ya iner, `i`ye degil.

        Bu kural `IŞIK` / `ışık` eslesmesini mumkun kilar. Bedeli:
        Turkce disi bir aracla buyutulmus `ÇELIK` (noktasiz I) `çelık`
        olur ve `Çelik` ile ayni anahtari vermez. Bu bir yazim hatasidir;
        arac duzeltmez, yalniz yerinde durur.
        """
        assert turkce_siralamasi("IŞIK") == turkce_siralamasi("ışık")
        assert turkce_siralamasi("ÇELIK") != turkce_siralamasi("Çelik")

    def test_yerel_ayara_bagimli_degil(self):
        """Windows Turkce yerel ayari her zaman bulunamaz. Anahtar
        `locale`/LC_COLLATE UZERINDE kurulmamalidir."""
        assert turkce_siralamasi("Öztürk") < turkce_siralamasi("Özyurt")
        assert turkce_siralamasi("Şahin") < turkce_siralamasi("Şimşek")

    def test_alfabet_disi_sonra_duser(self):
        assert turkce_siralamasi("Öztürk") < turkce_siralamasi("100 Öztürk")

    def test_bos_metin_hata_vermez(self):
        assert turkce_siralamasi("") == ""
        assert turkce_siralamasi(None) == ""


# --------------------------------------------------------------------------
# 2. Kaynak sirasi: SOYAD
# --------------------------------------------------------------------------

class TestKaynakSirasiSoyad:
    """Siralama anahtari yazarinin soyadi olmali.

    APA 7 ve `references/citation_rules.md` ikisi de soyada gore alfabetik
    ister. Onceki kod `authors[0]`'in TAM string'ini anahtar aliyordu:
    "Camille Parmesan" -> "c", "Gian-Reto Walther" -> "gi",
    "Riana Gardiner" -> "ri". Gardiner ilk cikiyordu.
    """

    def test_verilen_ad_soyad_yalniz_soyada_gore_siralanir(self):
        # Siralama: Gardiner, Parmesan, Walther
        sirali = _yazarlarla([
            ("SRC-001", ["Camille Parmesan"]),
            ("SRC-002", ["Gian-Reto Walther"]),
            ("SRC-003", ["Riana Gardiner"]),
        ])
        assert [k["id"] for k in sirali] == ["SRC-003", "SRC-001", "SRC-002"]

    def test_soyad_once_gelen_bicim_degistirmez(self):
        """`Aydın, A.` ve `A. Aydın` AYNI kisiyi anlatir; soyad ayni
        oldugu icin ayni sirada durmalilar ve aralarina giren
        `Boz` onlari one gecmemeli."""
        sirali = _yazarlarla([
            ("SRC-001", ["Aydın, A."]),
            ("SRC-002", ["A. Aydın"]),
            ("SRC-003", ["Boz, B."]),
        ])
        # Aydın < Boz; iki Aydın ayni anahtarda ve kimlige gore ayrilir.
        assert [k["id"] for k in sirali] == ["SRC-001", "SRC-002", "SRC-003"]

    def test_soyad_ilk_parca_comma_once(self):
        sirali = _yazarlarla([
            ("SRC-001", ["Yılmaz, Zeynep, ve Demir, Kaan"]),
            ("SRC-002", ["Alkan, Ayhan"]),
        ])
        assert [k["id"] for k in sirali] == ["SRC-002", "SRC-001"]

    def test_hyphenli_verilen_ad_soyadi_etkilemez(self):
        sirali = _yazarlarla([
            ("SRC-001", ["Jean-Pierre Dubois"]),
            ("SRC-002", ["Ayşe Kaya"]),
        ])
        assert [k["id"] for k in sirali] == ["SRC-001", "SRC-002"]

    def test_parcacik_soyad_dahil_edilir(self):
        """Felemenkce/Latince parcaciklar soyadin bir parcasidir
        (`van der Berg`, `von Humboldt`). Ana anahtar `Berg` degil
        `van der Berg` olmali."""
        sirali = _yazarlarla([
            ("SRC-001", ["Jan van der Berg"]),
            ("SRC-002", ["Ayşe Kaya"]),
            ("SRC-003", ["Wilhelm von Humboldt"]),
        ])
        assert [k["id"] for k in sirali] == ["SRC-002", "SRC-001", "SRC-003"]

    def test_yazar_yoksa_basliga_gore_siralanir(self):
        sirali = _yazarlarla([
            ("SRC-001", []),
            ("SRC-002", ["Zeynep Yılmaz"]),
        ])
        durum = _tez()
        durum["sources"] = [
            _kaynak("SRC-001", None, baslik="Zeyrek biçimi"),
            _kaynak("SRC-002", ["Zeynep Yılmaz"]),
        ]
        durum["citations"] = [_atif("CIT-001", "SRC-001"), _atif("CIT-002", "SRC-002")]
        # Yazarsiz kaynak basliga dusar: "Yılmaz" < "Zeyrek" (Y < Z).
        assert [k["id"] for k in kaynakca_girdileri(durum)] == ["SRC-002", "SRC-001"]
        # `_yazarlarla` yardimcisi SRC-001'i YAZARSIZ uretir; varsayilan
        # basligi "Kurgusal başlık" (K), "Yılmaz"dan (Y) once gelir.
        assert sirali[0]["id"] == "SRC-001"

    def test_yazarlar_turkce_kolasyonla_siralanir(self):
        sirali = _yazarlarla([
            ("SRC-001", ["Zeynep Çelik"]),
            ("SRC-002", ["Ayşe Doğan"]),
        ])
        assert [k["id"] for k in sirali] == ["SRC-001", "SRC-002"]

    def test_kimlik_anahtari_rakamlari_ayirt_eder(self):
        """Kimlik anahtari Turkce kolasyonundan GECMELIDIR.

        `SRC-001` ve `SRC-002` kolasyonda ayni anahtara duser (rakam ve
        tire "99"); ayni soyad + ayni yil + ayni baslikta iki kayit
        varsa sirayı yalniz bu ayirt edici belirler.
        """
        durum = _tez()
        durum["sources"] = [
            _kaynak("SRC-002", ["Smith, Ann"], yil=2020, baslik="Aynı başlık"),
            _kaynak("SRC-001", ["Smith, Ann"], yil=2020, baslik="Aynı başlık"),
        ]
        durum["citations"] = [_atif("CIT-001", "SRC-002"), _atif("CIT-002", "SRC-001")]
        ilk = [k["id"] for k in kaynakca_girdileri(durum)]
        # Her calistirmada ayni sonuc: girdi sirasi degisse de kararli.
        for _ in range(5):
            assert [k["id"] for k in kaynakca_girdileri(durum)] == ilk
        assert ilk == ["SRC-001", "SRC-002"]

    def test_ayni_soyatta_yil_ve_basliga_gore_ayrilir(self):
        """Ayni soyadli iki kayit siranin kararli (deterministik)
        olmasini gerektirir; aksi halde her calistirmada sira degisebilir."""
        durum = _tez()
        durum["sources"] = [
            _kaynak("SRC-002", ["Smith, Ann"], yil=2020, baslik="Zeta"),
            _kaynak("SRC-001", ["Smith, Bob"], yil=2019, baslik="Alfa"),
        ]
        durum["citations"] = [_atif("CIT-001", "SRC-002"), _atif("CIT-002", "SRC-001")]
        assert [k["id"] for k in kaynakca_girdileri(durum)] == ["SRC-001", "SRC-002"]


# --------------------------------------------------------------------------
# 3. Bolum ici alt basliklar
# --------------------------------------------------------------------------

class TestAltBasliklar:
    """`paragraph.section` ciktiya GIRMELI.

    Alan semada var, yazim komutu dolduruyor, `export` okumuyordu. Sonuc:
    "1.1 Kapsam" gibi 52 alt baslik ciktiya hic girmiyordu; bolum ici
    yapisiz, okunmaz bir duz metin blogu olarak cikiyordu.
    """

    def test_markdown_alt_basligi_yazar(self):
        durum = _tez(_bolum("CH-001", 1, "Giriş", [
            _paragraf("P-001", "Giriş paragrafı.", bolum_basligi="1.1 Kapsam"),
            _paragraf("P-002", "Kapsam paragrafı."),
        ]))
        assert "### 1.1 Kapsam" in markdown_uret(durum)

    def test_markdown_alt_baslik_bolum_basligindan_kucuktur(self):
        """`###` (h3) `##` (h2) altinda olmali; ayni seviye olursa
        icindekiler duzeni bozulur."""
        durum = _tez(_bolum("CH-001", 1, "Giriş", [
            _paragraf("P-001", "Metin.", bolum_basligi="1.1 Kapsam"),
        ]))
        md = markdown_uret(durum)
        assert md.index("## 1. Giriş") < md.index("### 1.1 Kapsam")

    def test_markdown_ardisik_ayni_bolum_basligi_tekrar_etmez(self):
        durum = _tez(_bolum("CH-001", 1, "Giriş", [
            _paragraf("P-001", "A.", bolum_basligi="1.1 Kapsam"),
            _paragraf("P-002", "B.", bolum_basligi="1.1 Kapsam"),
            _paragraf("P-003", "C."),
        ]))
        assert markdown_uret(durum).count("### 1.1 Kapsam") == 1

    def test_markdown_bolum_basligi_degisince_yeniden_yazar(self):
        """Ayni baslik araya girip donerse yeniden yazilmalidir."""
        durum = _tez(_bolum("CH-001", 1, "Giriş", [
            _paragraf("P-001", "A.", bolum_basligi="1.1 Kapsam"),
            _paragraf("P-002", "B.", bolum_basligi="1.2 Sınırlar"),
            _paragraf("P-003", "C.", bolum_basligi="1.1 Kapsam"),
        ]))
        assert markdown_uret(durum).count("### 1.1 Kapsam") == 2

    def test_markdown_bolum_basligi_yoksa_alt_baslik_yok(self):
        durum = _tez(_bolum("CH-001", 1, "Giriş", [
            _paragraf("P-001", "A."),
        ]))
        assert "###" not in markdown_uret(durum)

    def test_markdown_alt_basliktan_sonra_paragraf_meti_gelir(self):
        durum = _tez(_bolum("CH-001", 1, "Giriş", [
            _paragraf("P-001", "Kapsam paragrafı.", bolum_basligi="1.1 Kapsam"),
        ]))
        md = markdown_uret(durum)
        assert md.index("### 1.1 Kapsam") < md.index("Kapsam paragrafı.")

    def test_her_bolum_kendi_alt_basligindan_baslar(self):
        """Alt baslik takibi bolumler arasi TASINMAMALIDIR."""
        durum = _tez(
            _bolum("CH-001", 1, "Giriş", [
                _paragraf("P-001", "A.", bolum_basligi="1.1 Kapsam"),
            ]),
            _bolum("CH-002", 2, "Yöntem", [
                _paragraf("P-002", "B.", bolum_basligi="2.1 Tasarım"),
            ]),
        )
        md = markdown_uret(durum)
        assert "### 1.1 Kapsam" in md and "### 2.1 Tasarım" in md

    def test_bolum_basligi_tekrarlanmaz_her_bolumde(self):
        """Iki bolumde ayni baslik metni olsa bile iki ayri baslik yazilir."""
        durum = _tez(
            _bolum("CH-001", 1, "Giriş", [
                _paragraf("P-001", "A.", bolum_basligi="Sınırlamalar"),
            ]),
            _bolum("CH-002", 2, "Yöntem", [
                _paragraf("P-002", "B.", bolum_basligi="Sınırlamalar"),
            ]),
        )
        assert markdown_uret(durum).count("### Sınırlamalar") == 2

    def test_docx_alt_basligi_baslik_2_stiliyle_yazar(self, tmp_path):
        from docx import Document

        durum = _tez(_bolum("CH-001", 1, "Giriş", [
            _paragraf("P-001", "A.", bolum_basligi="1.1 Kapsam"),
        ]))
        belge = Document(str(docx_uret(durum, tmp_path / "tez.docx")))
        assert "Heading 2" in [p.style.name for p in belge.paragraphs]
        assert "1.1 Kapsam" in [
            p.text for p in belge.paragraphs if p.style.name == "Heading 2"
        ]


# --------------------------------------------------------------------------
# 4. Akademik Word duzeni
# --------------------------------------------------------------------------

class TestAkademikWordDuzeni:
    """`docx_uret` bir metin dosyasi degil, teslim edilebilir bir belge
    uretmeli. Bicim ogeleri ayri ayri denetlenir; hepsi tek "bicimli
    mi?" testiyle kapsanamaz cunku hangi ogenin bozuldugu anlasilmaz.
    """

    @pytest.fixture()
    def belge(self, tmp_path: Path):
        from docx import Document

        durum = _tez(
            _bolum("CH-001", 1, "Giriş", [
                _paragraf("P-001", "Giriş paragrafı.", bolum_basligi="1.1 Kapsam"),
                _paragraf("P-002", "Kapsam paragrafı."),
            ]),
            sources=[
                _kaynak("SRC-001", ["Ayşe Kaya"], yil=2024, baslik="Kurgusal başlık"),
            ],
            citations=[_atif("CIT-001", "SRC-001")],
        )
        yol = docx_uret(durum, tmp_path / "tez.docx")
        belge = Document(str(yol))
        belge._atw_yol = yol  # type: ignore[attr-defined]
        yield belge

    def test_bes_bolum_olusturulur(self, belge):
        """kapak / ozet / abstract / icindekiler / govde.

        Sayfa numarasi duzeni (numarasiz -> roma -> arap) bolumler
        arasinda gecis yapar; tek bolumde yapilamaz.
        """
        assert len(belge.sections) == 5

    def test_kapak_sayfa_numarasi_tasımaz(self, belge):
        from docx.oxml.ns import qn

        ilk = belge.sections[0]._sectPr
        assert ilk.find(qn("w:pgNumType")) is None
        assert "PAGE" not in (ilk.xml or "")

    def test_ozet_bolumu_roma_numaradan_bir_baslar(self, belge):
        from docx.oxml.ns import qn

        pnt = belge.sections[1]._sectPr.find(qn("w:pgNumType"))
        assert pnt is not None
        assert pnt.get(qn("w:fmt")) == "lowerRoman"
        assert pnt.get(qn("w:start")) == "1"

    def test_govde_bolumu_arap_birden_baslar(self, belge):
        """Kapali devamli sayfalar (ozet/abstract/icindekiler) 1'den
        baslayan arap rakamla devam etmemelidir."""
        from docx.oxml.ns import qn

        pnt = belge.sections[4]._sectPr.find(qn("w:pgNumType"))
        assert pnt is not None
        assert pnt.get(qn("w:fmt")) == "decimal"
        assert pnt.get(qn("w:start")) == "1"

    def test_devam_bolumleri_sayfa_baslangici_tasimaz(self, belge):
        """python-docx `add_section()` onceki `sectPr`'yi kopyalar.

        Kopyalanan `w:start` silinmezse abstract ve icindekiler de 1'den
        baslar; numaralar i, ii, iii yerine hep i olur.
        """
        from docx.oxml.ns import qn

        for bolum in belge.sections[2:4]:
            pnt = bolum._sectPr.find(qn("w:pgNumType"))
            if pnt is not None:
                assert pnt.get(qn("w:start")) is None, (
                    "devam bolumu sayfa numarasini bastan baslatmamali"
                )

    def test_sayfa_buyuklugu_a4(self, belge):
        from docx.shared import Cm

        for bolum in belge.sections:
            assert abs(bolum.page_width.cm - 21.0) < 0.05
            assert abs(bolum.page_height.cm - 29.7) < 0.05

    def test_sol_kenar_cilt_payi_icin_genis(self, belge):
        from docx.shared import Cm

        for bolum in belge.sections:
            assert abs(bolum.left_margin.cm - 3.0) < 0.05
            assert abs(bolum.right_margin.cm - 2.0) < 0.05

    def test_normal_stil_times_new_roman_12pt(self, belge):
        from docx.shared import Pt

        normal = belge.styles["Normal"]
        assert normal.font.name == "Times New Roman"
        assert normal.font.size == Pt(12)

    def test_govde_paragrafi_iki_yana_ve_bir_bes_satir(self, belge):
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.shared import Cm

        govde = [
            p for p in belge.paragraphs
            if p.text.strip() == "Giriş paragrafı."
        ]
        assert govde, "govde paragrafi bulunamadi"
        pf = govde[0].paragraph_format
        assert pf.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY
        assert abs(pf.first_line_indent.cm - 1.25) < 0.02
        assert pf.line_spacing == 1.5

    def test_bolum_basligi_baslik_1_stiliyle(self, belge):
        h1 = [p.text for p in belge.paragraphs if p.style.name == "Heading 1"]
        assert "1. Giriş" in h1
        assert "KAYNAKÇA" in h1

    def test_kapak_basligi_baslik_1_degildir(self, belge):
        """Tez basligi kapak sayfasindadir; `Heading 1` olsaydi icindekiler
        alaninda 'tez basligi ... 1' olarak gorunurdu."""
        h1 = [p.text for p in belge.paragraphs if p.style.name == "Heading 1"]
        assert "Sınama Tezi" not in h1

    def test_on_bilgiler_yer_tutucu_icerir(self, belge):
        metinler = [p.text for p in belge.paragraphs]
        birlestir = "\n".join(metinler)
        assert "ÖZET" in birlestir
        assert "ABSTRACT" in birlestir
        assert "İÇİNDEKİLER" in birlestir

    def test_ozet_ve_anahtar_kelimeler_yer_tutucu_olur(self, belge):
        """Skill ilkesi: uydurulamayan bilgi `[...]` yer tutucu olarak
        birakilir; ozet ve anahtar kelimeler TEZ tarafindan uretilmez."""
        birlestir = "\n".join(p.text for p in belge.paragraphs)
        assert "[ÖZET" in birlestir
        assert "[Abstract" in birlestir
        assert "Anahtar kelimeler:" in birlestir

    def test_kapak_kisisel_bilgi_uydurmaz(self, belge):
        birlestir = "\n".join(p.text for p in belge.paragraphs)
        assert "[Ad Soyad]" in birlestir
        assert "[Danışman Unvan, Ad Soyad]" in birlestir

    def test_kapak_tez_basligini_yazar(self, belge):
        assert "Sınama Tezi" in "\n".join(p.text for p in belge.paragraphs)

    def test_icindekiler_word_alani_olarak_yazilir(self, belge):
        """`updateFields` olmadan alan dosya acildiginda BOSTUR; kullanici
        "icindekiler yok" sanir."""
        govde_xml = belge.element.body.xml
        assert 'TOC \\o "1-2"' in govde_xml
        assert 'w:dirty="true"' in govde_xml
        assert "w:updateFields" in belge.settings.element.xml

    def _kaynakca_girdileri(self, belge):
        """Kaynakca bolumundeki girdi paragraflari.

        APA girdisi yazarin GIRDI haliyle baslar ("Ayşe Kaya (2024)..."),
        bu yuzden bastan SOYAD aranmaz; KAYNAKÇA basligindan sonraki
        paragraflar alinir.
        """
        metinler = [p.text for p in belge.paragraphs]
        bas = metinler.index("KAYNAKÇA")
        return [p for p in belge.paragraphs[metinler.index("KAYNAKÇA") + 1:]
                if p.text.strip()]

    def test_kaynakca_asiili_girdi_indentli(self, belge):
        kaynakca = self._kaynakca_girdileri(belge)
        assert kaynakca, "kaynakca girdisi bulunamadi"
        pf = kaynakca[0].paragraph_format
        assert abs(pf.left_indent.cm - 1.25) < 0.02
        assert abs(pf.first_line_indent.cm + 1.25) < 0.02

    def test_kaynakca_girdisi_asili_girintide_ama_tek_satir_degil(self, belge):
        """Kaynakca girintisi sola 1.25 cm, ilk satir -1.25 cm: birlikte
        1.25 cm olmamali (bu asili girinti degil, blok girinti olurdu)."""
        kaynakca = self._kaynakca_girdileri(belge)
        assert kaynakca, "kaynakca girdisi bulunamadi"
        pf = kaynakca[0].paragraph_format
        assert abs(pf.left_indent.cm + pf.first_line_indent.cm) < 0.02

    def test_her_bolum_yeni_sayfada_baslar(self, belge):
        bolum_basligi = [
            p for p in belge.paragraphs
            if p.style.name == "Heading 1" and p.text.startswith("1. Giriş")
        ]
        assert bolum_basligi[0].paragraph_format.page_break_before is True

    def test_ekler_olmadigi_belgede_acikca_yazilir(self, belge):
        """Ekler desteklenmiyor; bu durum CIKTA ACIKCA yazilir.

        Sessizce birakmak, cikida eksik oldugu gorunmeyen bir belge
        uretmek olurdu.
        """
        from tools.atw.export import EKLER_NOTU

        birlestir = "\n".join(p.text for p in belge.paragraphs)
        assert EKLER_NOTU in birlestir

    def test_turkce_karakterler_belgede_korunur(self, belge):
        birlestir = "\n".join(p.text for p in belge.paragraphs)
        assert "Giriş" in birlestir
        assert "İÇİNDEKİLER" in birlestir
        assert "KAYNAKÇA" in birlestir

    def test_kaynakca_tertibi_turkce_kolasyonludur(self, tmp_path):
        from docx import Document

        durum = _tez(
            _bolum("CH-001", 1, "Giriş", [_paragraf("P-001", "Metin.")]),
            sources=[
                _kaynak("SRC-001", ["Zeynep Çelik"], yil=2024, baslik="Z bir başlık"),
                _kaynak("SRC-002", ["Ayşe Doğan"], yil=2023, baslik="B bir başlık"),
                _kaynak("SRC-003", ["Mert Şahin"], yil=2022, baslik="S bir başlık"),
            ],
            citations=[
                _atif("CIT-001", "SRC-001"),
                _atif("CIT-002", "SRC-002"),
                _atif("CIT-003", "SRC-003"),
            ],
        )
        belge = Document(str(docx_uret(durum, tmp_path / "k.docx")))
        metinler = [p.text for p in belge.paragraphs]
        # APA girdisi yazarin GIRDI haliyle basar ("Zeynep Çelik"), bu
        # yuzden soyadin BASINA bakilir; metin bastan soyad degildir.
        sira = [i for i, t in enumerate(metinler)
                if t.startswith(("Zeynep Çelik", "Ayşe Doğan", "Mert Şahin"))]
        assert len(sira) == 3, "kaynakca girdileri bulunamadi: %r" % metinler[-4:]
        assert sira == sorted(sira)
        assert metinler[sira[0]].startswith("Zeynep Çelik")


# --------------------------------------------------------------------------
# 5. Coklu bicim
# --------------------------------------------------------------------------

class TestCokluBicim:
    """`--format` verilmediginde Markdown uretiliyordu.

    Markdown INSAYA UYGUN degildir: sayfa duzeni, baslik hiyerarsisi,
    asili girinti ve sayfa numarasi yoktur. Teslim edilebilir bicim
    Word'du. "Basarili" donup Word ciktisi uretmeyen bir export, teslim
    edilemeyen bir cikti uretmis sayilir.
    """

    def test_tek_bicim_tek_yol_dondurur(self, tmp_path):
        yollar, notlar = disa_aktar(_tez(), ["md"], tmp_path)
        assert len(yollar) == 1
        assert yollar[0].suffix == ".md"
        assert yollar[0].is_file()
        assert notlar

    def test_coklu_bicim_hepsini_ureter(self, tmp_path):
        yollar, notlar = disa_aktar(_tez(), ["md", "docx"], tmp_path)
        assert [y.suffix for y in yollar] == [".md", ".docx"]
        assert all(y.is_file() for y in yollar)
        assert len(notlar) >= 2

    def test_tekil_bicim_metni_geriye_uyumlu(self, tmp_path):
        """Eski cagri imzasi (`"md"`) calismaya devam etmeli."""
        yollar, _ = disa_aktar(_tez(), "md", tmp_path)
        assert [y.suffix for y in yollar] == [".md"]

    def test_bicim_listesi_tekrarsiz_kabul_edilir(self, tmp_path):
        yollar, _ = disa_aktar(_tez(), ["md", "md"], tmp_path)
        assert len(yollar) == 1

    def test_bicim_siralamasi_korunur(self, tmp_path):
        yollar, _ = disa_aktar(_tez(), ["docx", "md"], tmp_path)
        assert [y.suffix for y in yollar] == [".docx", ".md"]

    def test_bilinmeyen_bicim_hicbir_dosya_yazmaz(self, tmp_path):
        with pytest.raises(Exception):
            disa_aktar(_tez(), ["md", "rtf"], tmp_path)
        assert list(tmp_path.iterdir()) == []

    def test_bir_bicim_basarisiz_olursa_hicbiri_yazilmaz(self, tmp_path, monkeypatch):
        """Yari teslim bir teslim degildir: kullanici "export calisti"
        sanip eksik dosyayi aramaz."""
        import tools.atw.export as export_modul

        def patlayan(durum):
            raise export_modul.ExportHatasi("Word üretilemedi (test)")

        monkeypatch.setattr(export_modul, "docx_belgesi", patlayan)
        with pytest.raises(export_modul.ExportHatasi):
            disa_aktar(_tez(), ["md", "docx"], tmp_path)
        assert list(tmp_path.iterdir()) == []


class TestVarsayilanCikti:
    def test_bicim_verilmezse_md_ve_docx_uretilir(self, tmp_path):
        """CLI varsayilani: kullanici bir bicim soylemezse teslim edilebilir
        ikilisi (okunabilir metin + Word) uretilir."""
        from tools.atw.cli.main import build_parser

        args = build_parser().parse_args(["export", "--out", str(tmp_path)])
        assert args.format is None, "varsayilan argparse'da degil, export katmaninda"
        yollar, _ = disa_aktar(_tez(), args.format or DEFAULT_BICIMLER, tmp_path)
        assert [y.suffix for y in yollar] == [".md", ".docx"]

    def test_acikca_bicim_verilirse_yalniz_oca_uretilir(self, tmp_path):
        from tools.atw.cli.main import build_parser

        args = build_parser().parse_args(["export", "--format", "pdf"])
        assert args.format == ["pdf"]
        yollar, _ = disa_aktar(_tez(), args.format, tmp_path)
        assert [y.suffix for y in yollar] == [".pdf"]

    def test_coklu_bicim_argumana_alinir(self, tmp_path):
        """`--format docx md` sirali bir liste verir; `nargs="+"` olmadan
        argparse bunu reddederdi."""
        from tools.atw.cli.main import build_parser

        args = build_parser().parse_args(["export", "--format", "docx", "md"])
        assert args.format == ["docx", "md"]
        yollar, _ = disa_aktar(_tez(), args.format, tmp_path)
        assert [y.suffix for y in yollar] == [".docx", ".md"]

    def test_bilinmeyen_bicim_argparse_da_elenir(self):
        from tools.atw.cli.main import build_parser

        with pytest.raises(SystemExit):
            build_parser().parse_args(["export", "--format", "rtf"])
