"""`thesis:export` tezi gercekten dosyaya dokumali.

Bulgu
-----
`cmd_export` stub idi: `final_thesis` kapisini sorup

    print("Henuz implemente edilmedi")
    return 0

yaziyordu. Yani komut "basarili" donup HICBIR sey uretmuyordu. `skill.yaml`
ise "Final tez metnini birlestir (bolumler + kaynakca + ekler)" diye
tanimliyordu.

Ayni anda iki veri modeli boslugu vardi:

  1. `citation.reference_entry` hicbir yerde URETILMIYORDU. `style.py` yalnizca
     `in_text_form`'u DOGRULUYOR; kaynakca girdisi ureten kod yok. Yani
     kaynakca uretilemiyordu.
  2. `authors` alaninin bicimi belirsizdi. Fixture'lar olcmeyerek
     cozuldu: "Orman, A." (APA-hazir, soyad once). Yani ayristirmaya
     GEREK YOK; girdi zaten APA biciminde.

Politika uydurmamak icin kaynakca kurali mevcut denetimden alindi:
`citation_check.audit_citations` bir kaynagin metinde atiflanmamis olmasini
`orphaned_citations` (major) olarak sayiyor ve bulgu konumunu "Kaynakca"
diye yaziyor. Demek ki kaynakca TAM OLARAK atiflanan kaynak kumesidir —
atananlar haricinde bir sey eklemek, mevcut denetimle celisirdi.

Ekler (appendix): durum semasinda `appendices` alani YOK. Bu surumde
disa aktarilmiyor ve bu durum CIKTIDA ACIKCA yaziliyor; sessizce
birakmak, ciktida eksik oldugu gorunmeyen bir belge uretmek olurdu.
"""
from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

import pytest

from tools.atw.export import (
    DESTEKLENEN_BICIMLER,
    ExportHatasi,
    atiflanan_kaynak_kimlikleri,
    apa_kaynak_girdisi,
    disa_aktar,
    docx_uret,
    kaynakca_girdileri,
    markdown_uret,
    turkce_siralamasi,
)
from tools.atw.state import empty_state


# --- yardimcilar ------------------------------------------------------------

def _kaynak(kimlik: str, **ek) -> dict:
    """Gecerli bir minimum source kaydi uretir."""
    kaynak = {
        "id": kimlik,
        "title": "Kurgusal Bir Yontemin Etkinligi Uzerine Bir Inceleme",
        "authors": ["Orman, A."],
        "year": 2023,
        "source_type": "article",
        "verification": {
            "status": "verified",
            "bibliographic_match": 1.0,
            "verified_at": "2026-01-15T10:00:00Z",
            "verification_sources": ["crossref"],
        },
    }
    kaynak.update(ek)
    return kaynak


def _atif(kimlik: str, kaynak_id: str, **ek) -> dict:
    atif = {
        "id": kimlik,
        "source_id": kaynak_id,
        "paragraph_id": "P-001",
        "style": "apa7",
    }
    atif.update(ek)
    return atif


def _paragraf(kimlik: str, metin: str, **ek) -> dict:
    p = {
        "id": kimlik,
        "type": "literature_synthesis",
        "text": metin,
        "chapter": "CH-001",
    }
    p.update(ek)
    return p


def _bolum(kimlik: str, numara: int, baslik: str, paragraflar: list) -> dict:
    return {
        "id": kimlik,
        "number": numara,
        "title": baslik,
        "paragraphs": paragraflar,
    }


def _tez(*bolumler, **ek) -> dict:
    """final_thesis kapisi acilmis, butunlugu temiz bir tez durumu."""
    durum = empty_state("THESIS-2026-001", "Ornek Tez")
    durum["chapters"] = list(bolumler)
    durum["human_approvals"] = {
        "research_question": True,
        "search_strategy": True,
        "source_set": True,
        "research_gap": True,
        "methodology": True,
        "findings": True,
        "final_thesis": True,
    }
    durum.update(ek)
    return durum


@pytest.fixture
def dolu_tez():
    """Iki bolum, uc paragraf, iki atiflanan kaynak."""
    return _tez(
        _bolum("CH-001", 1, "Giris", [
            _paragraf("P-001", "Bu tez konunun onemini tartisir.", sources=["SRC-001"]),
        ]),
        _bolum("CH-002", 2, "Yontem", [
            _paragraf("P-002", "Yontem olarak sistematik tarama kullanildi."),
            _paragraf("P-003", "Bulgular onceki calismalarla tutarlidir.",
                      sources=["SRC-002"]),
        ]),
        sources=[_kaynak("SRC-001"), _kaynak("SRC-002", authors=["Kaya, B.", "Demir, C."],
                                              year=2021, title="Yontem tartismasi",
                                              journal="Kurgusal Dergi", volume="9",
                                              issue="2", pages="10-20",
                                              doi="10.5555/kurgusal.002")],
        citations=[_atif("CIT-001", "SRC-001"), _atif("CIT-002", "SRC-002")],
    )


# --- 1) kaynakca kumesi: YALNIZCA atiflananlar ------------------------------

def test_kaynakca_yalnizca_atiflananlari_icerir(dolu_tez):
    """Atiflanmayan kaynak kaynakcada GORUNMEMELI.

    `citation_check.audit_citations` ayni kurali `orphaned_citations` olarak
    sayiyor; burada tersine uygulanmasi ayni kaynagi iki yerde farkli
    muameleye sokardi.
    """
    dolu_tez["sources"].append(_kaynak("SRC-003", title=" hic atiflanmadi"))
    kimlikler = {k["id"] for k in kaynakca_girdileri(dolu_tez)}
    assert kimlikler == {"SRC-001", "SRC-002"}, (
        "kaynakta var ama metinde atiflanmayan kaynak kaynakca girdi"
    )


def test_atiflanan_kaynak_kimlikleri(dolu_tez):
    assert atiflanan_kaynak_kimlikleri(dolu_tez) == {"SRC-001", "SRC-002"}


def test_dogrula_paragraf_atifini_kaynaga_cozer(dolu_tez):
    """Paragraf citations (CIT-XXX) kaynak kimligine (SRC-XXX) cozulmelidir.

    Regresyon: _dogrula, paragraf citations ID'lerini (CIT-XXX) kaynak kimlikleri
    kumesine ekleyip hepsini sources sozlugune karsi kontrol ediyordu; CIT ID'leri
    hicbir zaman sources'de olmadigi icin gercek bir atif iceren her bolum
    'kaynak uydurulamaz' hatasiyla reddediliyordu.
    """
    from tools.atw.export import _dogrula

    # P-001'e gercek bir atif ekle (CIT-001 -> SRC-001, sources'de var)
    dolu_tez["chapters"][0]["paragraphs"][0]["citations"] = ["CIT-001"]

    # _dogrula hata vermemeli: CIT-001'in kaynagi SRC-001 sources'de mevcut
    _dogrula(dolu_tez)


def test_kaynakca_yoksa_bos_liste():
    assert kaynakca_girdileri(_tez()) == []


# --- 2) APA 7 kaynakca girdisi --------------------------------------------

def test_apa_makale_girdisi(dolu_tez):
    giri = apa_kaynak_girdisi(dolu_tez["sources"][1])
    assert giri.startswith("Kaya, B., & Demir, C. (2021)."), giri
    assert "Yontem tartismasi" in giri
    assert "Kurgusal Dergi" in giri
    assert "9" in giri and "2" in giri
    assert "10-20" in giri
    assert "https://doi.org/10.5555/kurgusal.002" in giri


def test_apa_cok_yazarli_yazar_birligi():
    """Uc yazar: virgulle ayrilir, sonuncudan once & gelir."""
    kaynak = _kaynak("SRC-001", authors=["Aydin, A.", "Boz, B.", "Cetin, C."])
    giri = apa_kaynak_girdisi(kaynak)
    assert giri.startswith("Aydin, A., Boz, B., & Cetin, C. (2023)."), giri


def test_apa_tek_yazar_ve_ampersandsiz():
    giri = apa_kaynak_girdisi(_kaynak("SRC-001", authors=["Orman, A."]))
    assert giri.startswith("Orman, A. (2023)."), giri
    assert "&" not in giri


def test_apa_yazar_yoksa_acikca_belirtilir():
    """Yazar yoksa sessizce ATILMAMALI; giriste gorunmeli.

    Yoksa kaynakca girdisinde ne oldugu bilinmez ve kaynak kaybolur.
    """
    giri = apa_kaynak_girdisi(_kaynak("SRC-001", authors=[]))
    assert "Yazar belirtilmemiş" in giri, giri


def test_apa_yil_yoksa_turkce_karsiligi():
    """Yil yoksa APA'da 'n.d.'; Turkce metinde 't.y.' (tarih yok)."""
    giri = apa_kaynak_girdisi(_kaynak("SRC-001", year=None))
    assert "t.y." in giri, giri
    assert "(n.d.)" not in giri


def test_apa_kitap_girdisi_publisher_kullanir():
    giri = apa_kaynak_girdisi(_kaynak(
        "SRC-001", source_type="book", title="Bir Kitap",
        journal="", publisher="Anadolu Yayinlari", year=2020))
    assert "Bir Kitap" in giri
    assert "Anadolu Yayinlari" in giri
    assert "Kurgusal Dergi" not in giri, "kitapta dergi alani basilmamali"


def test_apa_doi_url_halinde_basilir():
    giri = apa_kaynak_girdisi(_kaynak("SRC-001", doi="10.1234/abc"))
    assert giri.rstrip().endswith("https://doi.org/10.1234/abc"), giri


def test_apa_doi_yoksa_url_da_yoksa_sonda_nokta_kalmaz():
    giri = apa_kaynak_girdisi(_kaynak("SRC-001", doi="", url="")).rstrip()
    assert not giri.endswith(".."), giri
    assert giri.endswith("."), giri


def test_hazir_reference_entry_tercih_edilir(dolu_tez):
    """Citation'da hazir reference_entry varsa o kullanilmali.

    Alan semada var ve hicbir kod uretmiyor. Alan doluysa hazirlanmis
    (insan/ajan tarafindan bicimlenmis) olabilir; yeniden uretmek onu
    degistirirdi.
    """
    dolu_tez["citations"][0]["reference_entry"] = "Elle yazilmis ozel giris."
    girisler = [g for g in markdown_uret(dolu_tez).splitlines()
                if "Elle yazilmis ozel giris." in g]
    assert girisler, "hazir reference_entry kullanilmadi"
    assert "Elle yazilmis ozel giris." in markdown_uret(dolu_tez)


def test_reference_entry_uretilmis_girdiyle_eslesir():
    """Hazir giri yoksa kaynaktan uretilir ve buyuk harf degistirilmez.

    Baslikta kucuk-buyuk HARF DEGISTIRILMEZ: Turkce'de I/i ve ı/I
    ciftleri Python'un upper()/capitalize() ile bozulur; APA da metni
    oldugu gibi ister.
    """
    kaynak = _kaynak("SRC-001", title="bir kucuk baslik testi")
    assert "bir kucuk baslik testi" in apa_kaynak_girdisi(kaynak)


# --- 3) Turkce alfabetik siralama -----------------------------------------

def test_turkce_siralama_cesit_c_harfleri():
    """Turkce alfabetik: c, cc, cci, ccik, ccil ... (ayni 'c' kumesinde).

    Turkcede 'c' ardindan gelenler alfabetik sirada cc -> cci -> ccik ->
    ccil. Kod noktasi sirasi bunu VERSIYE BIRAKIR ve Turkce kaynakca yanlis
    siralanir.
    """
    kelimeler = ["cekirdek", "civik", "cocuk", "cam", "cekim", "can"]
    assert sorted(kelimeler, key=turkce_siralamasi) == [
        "cam", "can", "cekim", "cekirdek", "civik", "cocuk"
    ]


def test_turkce_siralama_cesit_g_i_harfleri():
    kelimeler = ["gocuk", "gibi", "ganimet", "guler", "gece", "gol"]
    assert sorted(kelimeler, key=turkce_siralamasi) == [
        "ganimet", "gece", "gibi", "gocuk", "gol", "guler"
    ]


def test_turkce_siralama_cesit_s_u_harfleri():
    kelimeler = ["sirma", "sut", "ses", "saf", "sofa", "saray"]
    assert sorted(kelimeler, key=turkce_siralamasi) == [
        "saf", "saray", "ses", "sirma", "sofa", "sut"
    ]


# --- 3b) AKsanli harfler: asil test edilen durum ---------------------------
# Yukaridaki uc test YALNIZCA aksansiz harfleri sinadi. Oysa
# `turkce_siralamasi`nin tek iselevi aksanli harflerde sirayi duzeltmektir.
# Bu blok o bosluk kapar; ilk yazimda burasi hic dolu degildi ve `ı`/`i`
# hatasinin gecmesine yol acti.


def test_turkce_siralama_nokta_i_once_gelir():
    """Turkce alfabetede `ı`, `i`'den ONCE gelir (h ı i j)."""
    kelimeler = ["iyi", "iplik", "ısı", "ıkıl", "jenerasyon"]
    assert sorted(kelimeler, key=turkce_siralamasi) == [
        "ıkıl", "ısı", "iplik", "iyi", "jenerasyon"
    ]


def test_turkce_siralama_c_kumesi_cesim_sonra_gelir():
    """`ç`, ayni ailedeki tum `c` kelimelerinden SONRA gelir."""
    kelimeler = ["derin", "çocuk", "can", "çekim", "cekirdek", "cam"]
    assert sorted(kelimeler, key=turkce_siralamasi) == [
        "cam", "can", "cekirdek", "çekim", "çocuk", "derin"
    ]


def test_turkce_siralama_g_kumesi_breve_sonra_gelir():
    """`ğ`, ayni ailedeki tum `g` kelimelerinden SONRA gelir."""
    kelimeler = ["hayat", "göğüs", "gocuk", "gül", "gece", "gibi"]
    assert sorted(kelimeler, key=turkce_siralamasi) == [
        "gece", "gibi", "gocuk", "göğüs", "gül", "hayat"
    ]


def test_turkce_siralama_s_kumesi_cedil_sonra_gelir():
    """`ş`, ayni ailedeki tum `s` kelimelerinden SONRA gelir."""
    kelimeler = ["sistem", "şüphe", "saf", "sırla", "sonra", "söyle"]
    assert sorted(kelimeler, key=turkce_siralamasi) == [
        "saf", "sırla", "sistem", "sonra", "söyle", "şüphe"
    ]


def test_turkce_siralama_u_kumesi_u_umlaut_sonra_gelir():
    """`ü`, ayni ailedeki tum `u` kelimelerinden SONRA gelir."""
    kelimeler = ["veri", "ürün", "uyku", "ulaşım", "uzman", "üniversite"]
    assert sorted(kelimeler, key=turkce_siralamasi) == [
        "ulaşım", "uyku", "uzman", "üniversite", "ürün", "veri"
    ]


def test_turkce_siralama_o_kumesi_umlaut_sonra_gelir():
    """`ö`, ayni ailedeki tum `o` kelimelerinden SONRA gelir."""
    kelimeler = ["pazar", "öğrenci", "orman", "okul", "önce", "olası"]
    assert sorted(kelimeler, key=turkce_siralamasi) == [
        "okul", "olası", "orman", "öğrenci", "önce", "pazar"
    ]


def test_turkce_siralamasi_buyuk_kucuk_harf_duyarsiz():
    """Turkce buyuk/kucuk esleşmesi, ASCII varsayimi DEGILDIR.

    Turkce'de ASCII `I` (U+0049) noktasiz `ı` ile eslesir, `i` ile
    DEGILDIR. `i`'nin buyugu `İ` (U+0130)'dur. `lower()`/`.lower()` gibi
    varsayilanlar bu ikisini yanlis eslestirir.
    """
    assert turkce_siralamasi("Ç") == turkce_siralamasi("ç")
    assert turkce_siralamasi("Ş") == turkce_siralamasi("ş")
    assert turkce_siralamasi("Ğ") == turkce_siralamasi("ğ")
    assert turkce_siralamasi("Ö") == turkce_siralamasi("ö")
    assert turkce_siralamasi("Ü") == turkce_siralamasi("ü")
    # ASCII buyuk I -> noktasiz kucuk ı
    assert turkce_siralamasi("I") == turkce_siralamasi("ı")
    # Turkce buyuk I -> noktali kucuk i
    assert turkce_siralamasi("İ") == turkce_siralamasi("i")
    # Ikisi AYRI harftir; noktali/noktasiz karismaz.
    assert turkce_siralamasi("I") != turkce_siralamasi("İ")


def test_kaynakca_turkce_alphabetik_sirali_gelir(dolu_tez):
    """Kaynakca girdileri Turkce alfabetik sirada olmali.

    Yazarlar 'Demir' ve 'Orman' ise 'Demir' once gelmeli; alfabetik olmayan
    bir kaynakca tes incelemesinde hemen yakalanir.
    """
    dolu_tez["sources"] = [
        _kaynak("SRC-001", authors=["Orman, A."], title="z basligi"),
        _kaynak("SRC-002", authors=["Aydin, A."], title="a basligi"),
    ]
    giris = markdown_uret(dolu_tez)
    assert giris.index("Aydin") < giris.index("Orman"), "kaynakca alfabetik degil"


# --- 4) markdown uretimi ---------------------------------------------------

def test_markdown_tez_basligini_icerir(dolu_tez):
    md = markdown_uret(dolu_tez)
    assert md.startswith("# Ornek Tez"), md[:80]


def test_markdown_bolumleri_numarali_basar(dolu_tez):
    md = markdown_uret(dolu_tez)
    assert "## 1. Giris" in md
    assert "## 2. Yontem" in md


def test_markdown_paragraf_metinlerini_icerir(dolu_tez):
    md = markdown_uret(dolu_tez)
    assert "Bu tez konunun onemini tartisir." in md
    assert "Bulgular onceki calismalarla tutarlidir." in md


def test_markdown_kaynakca_bolumu_var(dolu_tez):
    assert "## Kaynakça" in markdown_uret(dolu_tez)


def test_markdown_ekler_olmadigini_acikca_yazar(dolu_tez):
    """Ekler (appendix) bu surumde yok; bu CIKTIDA yazmali.

    Sessizce birakmak, ciktida eksik oldugu gorunmeyen bir belge uretmek
    olurdu.
    """
    md = markdown_uret(dolu_tez)
    assert "ekler" in md.lower()
    assert "appendix" in md.lower(), "hangi bolumun eksik oldugu belirtilmeli"


def test_markdown_bos_paragraf_metni_atlanir(dolu_tez):
    dolu_tez["chapters"][0]["paragraphs"].append(_paragraf("P-999", ""))
    assert "P-999" not in markdown_uret(dolu_tez)


# --- 5) disa aktarma: gercek dosya -----------------------------------------

def test_markdown_dosyasi_yazilir(dolu_tez, tmp_path):
    yol, _ = disa_aktar(dolu_tez, "md", tmp_path)
    assert yol.is_file()
    assert yol.suffix == ".md"
    assert yol.parent == tmp_path
    assert "Ornek Tez" in yol.read_text(encoding="utf-8")


def test_docx_dosyasi_gecerli_soz_belgesidir(dolu_tez, tmp_path):
    yol, _ = disa_aktar(dolu_tez, "docx", tmp_path)
    assert yol.suffix == ".docx"
    assert zipfile.is_zipfile(yol), "docx zip tabanli OOXML olmali"
    with zipfile.ZipFile(yol) as z:
        adlar = z.namelist()
        assert "word/document.xml" in adlar
        govde = z.read("word/document.xml").decode("utf-8")
    assert "Ornek Tez" in govde
    assert "Kaynak" in govde


def test_docx_turkce_karakterler_korunur(dolu_tez, tmp_path):
    """Word ciktisinda Turkce harfler BOZULMAMALI.

    OOXML Unicode'tur; bir kodlama hatasi ciktiyi sessizce bozardi.
    """
    dolu_tez["title"] = "Şiddet ve Çelişki Gözden Geçirmesi"
    yol, _ = disa_aktar(dolu_tez, "docx", tmp_path)
    with zipfile.ZipFile(yol) as z:
        govde = z.read("word/document.xml").decode("utf-8")
    assert "Şiddet ve Çelişki" in govde


def test_pdf_dosyasi_yazilir(dolu_tez, tmp_path):
    yol, _ = disa_aktar(dolu_tez, "pdf", tmp_path)
    assert yol.suffix == ".pdf"
    ham = yol.read_bytes()
    assert ham.startswith(b"%PDF-"), "PDF imzasi yok"
    assert len(ham) > 800, f"PDF beklenenden kucuk: {len(ham)} bayt"


def test_pdf_turkce_harfleri_kapsar(dolu_tez, tmp_path):
    """fpdf2'nin latin-1 fontu cp1252 kodlamasindadir.

    Turkcenin butun harfleri (c, g, i, o, s, u ve buyukleri) cp1252'de
    vardir. Kapsam disina duserse PDF sessizce '?' basardi.
    """
    kaynak = _kaynak(
        "SRC-001",
        title=(
            "Örnek İlk Çalışma: GÖĞÜS, Işık, Şüphe, Üzere, acı çatışma, "
            "ağaç, öğüt, İşık"
        ),
    )
    for harf in "cğışöüÇĞİÖŞÜ":
        assert harf in kaynak["title"], f"test metni {harf} icermiyor"
    durum = _tez(
        _bolum("CH-001", 1, "Giriş", [
            _paragraf("P-001", "Örnek sosyal yapı çalışması göğüş ışık şüphe üzere."),
        ]),
        sources=[kaynak],
        citations=[_atif("CIT-001", "SRC-001")],
    )
    yol, _ = disa_aktar(durum, "pdf", tmp_path)
    assert yol.is_file() and yol.stat().st_size > 800


# --- 6) reddedilen durumlar ------------------------------------------------

def test_bicim_desteklenmiyorsa_hata():
    with pytest.raises(ExportHatasi, match="docx"):
        disa_aktar(_tez(), "rtf", Path("."))


def test_atanmayan_kaynak_reddedilir(dolu_tez, tmp_path):
    """Metinde atiflanan ama kaynakta OLMAYAN kaynak: sessizce gecmez."""
    dolu_tez["citations"].append(_atif("CIT-003", "SRC-999"))
    with pytest.raises(ExportHatasi, match="SRC-999"):
        disa_aktar(dolu_tez, "md", tmp_path)
    assert not list(tmp_path.iterdir()), "reddedildigi halde dosya yazildi"


def test_retraksiyonlu_kaynak_reddedilir(dolu_tez, tmp_path):
    """Geri cekilmis kaynakla atif final tezde kabul edilmez.

    `citation_check` bunu `retracted_sources_in_use` (critical) sayiyor;
    policy burada UYDURULMADI, mevcut karar yansitildi.
    """
    dolu_tez["sources"][0]["retraction_status"] = "retracted"
    with pytest.raises(ExportHatasi, match="retraksiyon"):
        disa_aktar(dolu_tez, "md", tmp_path)


def test_bos_govde_reddedilir(tmp_path):
    """Paragraf metni olmayan tez disa aktarilmaz.

    Ciktida yalnizca baslik olan bir belge, basarili gorunurdu.
    """
    durum = _tez(_bolum("CH-001", 1, "Giris", [_paragraf("P-001", "")]))
    with pytest.raises(ExportHatasi, match="paragraf"):
        disa_aktar(durum, "md", tmp_path)


def test_bolum_olmayan_tez_reddedilir(tmp_path):
    with pytest.raises(ExportHatasi, match="bölüm"):
        disa_aktar(_tez(), "md", tmp_path)


# --- 7) dosya adi guvenligi ------------------------------------------------

def test_tez_kimligi_yol_kacisi_uretmez(dolu_tez, tmp_path):
    """thesis_id kullanici girdisidir; dizin disina cikilamaz.

    `thesis new` id'yi dogrulamadan kabul ediyor; `../../kötü` gibi bir
    deger dosyayi hedef disinin disina yazardi.
    """
    dolu_tez["thesis_id"] = "../../kotu"
    yol, _ = disa_aktar(dolu_tez, "md", tmp_path)
    assert yol.parent == tmp_path, f"hedef disina cikildi: {yol}"
    assert ".." not in yol.name


def test_tez_kimligi_ayirici_karakterler_temizlenir(dolu_tez, tmp_path):
    dolu_tez["thesis_id"] = "THESIS/2026:001 *v2?"
    yol, _ = disa_aktar(dolu_tez, "md", tmp_path)
    assert yol.parent == tmp_path
    for kotu in '/\\:*?"<>|':
        assert kotu not in yol.name, f"dosya adinda kotu karakter: {yol.name}"


def test_ayni_bicim_ikinci_kez_yazilir(dolu_tez, tmp_path):
    """Ayni bicim tekrar calistirilirsa ustune yazmali, cogaltmamali."""
    ilk, _ = disa_aktar(dolu_tez, "md", tmp_path)
    ikinci, _ = disa_aktar(dolu_tez, "md", tmp_path)
    assert ilk == ikinci
    assert len(list(tmp_path.glob("*.md"))) == 1


# --- 8) sözlesme: desteklenen bicimler -------------------------------------

def test_uc_bicim_destekleniyor():
    assert set(DESTEKLENEN_BICIMLER) == {"md", "docx", "pdf"}


def test_parser_pdf_formatini_kabul_eder():
    from tools.atw.cli.main import build_parser
    args = build_parser().parse_args(["export", "--format", "pdf"])
    assert args.format == "pdf"


# --- 9) CLI baglantisi ----------------------------------------------------
# Yukaridakiler `disa_aktar` FONKSIYONUNU dener. Burada soru farkli: komut
# gercekten cagirildiginda dosya duser mi, kapi reddedince HICBIR dosya
# yazilir mi? `cmd_export` `@_durum_gerekir` ile sarili oldugu icin
# durumu diskten okur; bu yuzden gecici dizine gercek durum yazilir.


@pytest.fixture
def cli_tesi(tmp_path, monkeypatch):
    """Gecici dizinde calisan CLI: durum dosyasi + calisma koku ayarli."""
    from tools.atw.cli import main as cli

    monkeypatch.setattr(cli, "VERI_KOKU", tmp_path)
    return cli


def _cli_durumunu_yaz(durum: dict, dizin: Path) -> None:
    (dizin / "thesis_state.json").write_text(
        json.dumps(durum, ensure_ascii=False), encoding="utf-8"
    )


def test_cli_export_dosyayi_dokumus_dondurur(cli_tesi, dolu_tez, tmp_path, capsys):
    """Gercek kapiyi gecen tez icin dosya yazilir ve cikis kodu CIKIS_OK'tur.

    Kapi burada YAMILANMAZ: `dolu_tez` butunlugu temiz ve tum onaylari
    acik. Boylece test yalnizca export kablolamasini degil, kapi -> uretim
    zincirinin tamamini dener.
    """
    _cli_durumunu_yaz(dolu_tez, tmp_path)
    args = cli_tesi.build_parser().parse_args(["export", "--format", "md"])

    cikis = cli_tesi.cmd_export(args)

    assert cikis == cli_tesi.CIKIS_OK, capsys.readouterr().out
    dokumler = list(tmp_path.glob("tez_*.md"))
    assert len(dokumler) == 1, f"beklenen tek dosya, bulunan: {dokumler}"
    metin = dokumler[0].read_text(encoding="utf-8")
    assert "# Ornek Tez" in metin
    # Konsola mutlak yol basilir; ekran goruntusu icin gereken budur.
    assert str(dokumler[0].resolve()) in capsys.readouterr().out


def test_cli_export_kapi_reddederse_dosya_yazmaz(cli_tesi, dolu_tez, tmp_path, capsys):
    """Kapi gecmezse cikis kodu SORUN'dur ve dizin BOS kalir.

    `cmd_export` stub'i kapidan sonra `return 0` idi; burada reddedilen
    bir disa aktarim da basarili gorunmemeli.
    """
    dolu_tez["human_approvals"]["final_thesis"] = False
    _cli_durumunu_yaz(dolu_tez, tmp_path)
    args = cli_tesi.build_parser().parse_args(["export", "--format", "md"])

    cikis = cli_tesi.cmd_export(args)

    assert cikis == cli_tesi.CIKIS_SORUN
    assert list(tmp_path.glob("tez_*")) == [], "kapidan gecemeden dosya yazildi"


def test_cli_export_hedef_dizini_olusturur(cli_tesi, dolu_tez, tmp_path):
    """`--out` verilen dizin yoksa olusturulur."""
    _cli_durumunu_yaz(dolu_tez, tmp_path)
    var_mayan = tmp_path / "cikti" / "alt"
    args = cli_tesi.build_parser().parse_args(
        ["export", "--format", "md", "--out", str(var_mayan)]
    )

    cikis = cli_tesi.cmd_export(args)

    assert cikis == cli_tesi.CIKIS_OK
    assert var_mayan.is_dir()
    assert len(list(var_mayan.glob("tez_*.md"))) == 1


def test_cli_export_veri_butunlugu_bozuk_hicbir_dosya_yazmaz(
    cli_tesi, dolu_tez, tmp_path, capsys
):
    """Uydurma kaynak atifi: export reddeder ve cikti dizini bos kalir."""
    dolu_tez["citations"].append(_atif("CIT-003", "SRC-999"))
    _cli_durumunu_yaz(dolu_tez, tmp_path)
    args = cli_tesi.build_parser().parse_args(["export", "--format", "md"])

    cikis = cli_tesi.cmd_export(args)

    assert cikis == cli_tesi.CIKIS_SORUN
    assert list(tmp_path.glob("tez_*")) == [], "reddedilmis export dosya birakti"
    assert "SRC-999" in capsys.readouterr().out


# --- 10) kenar durumlar ----------------------------------------------------


def test_apa_makale_cilt_var_sayi_yok():
    """Sayi yoksa APA bicimi `Dergi, 9` der; parantez acmaz."""
    kaynak = _kaynak("SRC-001", source_type="article", journal="Dergi",
                     volume="9", issue="", pages="10-20")
    giri = apa_kaynak_girdisi(kaynak)
    assert "Dergi, 9, 10-20" in giri, giri
    assert "()" not in giri, giri


def test_apa_baslik_sondaki_noktalar_temizlenir():
    """Baslikta art arda nokta varsa tek noktaya iner."""
    giri = apa_kaynak_girdisi(_kaynak("SRC-001", title="Bir Baslik..."))
    assert "..," not in giri and ".." not in giri.split("(2023)")[-1], giri
    assert giri.rstrip().endswith("."), giri


def test_apa_doi_yoksa_url_kullanilir():
    """DOI yoksa `url` alani baglanti olarak basilir."""
    giri = apa_kaynak_girdisi(
        _kaynak("SRC-001", source_type="website", url="https://ornek.gov.tr/rapor")
    )
    assert giri.rstrip().endswith("https://ornek.gov.tr/rapor"), giri


def _kaynakcasiz_lastir(dolu_tez: dict) -> dict:
    """Atiflanan hicbir kaynak kalmasin: atiflar, kaynaklar, paragraf baglari."""
    dolu_tez["citations"] = []
    dolu_tez["sources"] = []
    for bolum in dolu_tez["chapters"]:
        for paragraf in bolum.get("paragraphs") or []:
            paragraf.pop("sources", None)
    return dolu_tez


def test_markdown_kaynakca_bosken_acikca_yazar(dolu_tez):
    """Atiflanan kaynak yoksa kaynakca BOS birakilmaz, nedeni yazilir."""
    metin = markdown_uret(_kaynakcasiz_lastir(dolu_tez))
    assert "## Kaynakça" in metin
    assert "Kaynakça boş" in metin


def test_docx_kaynakca_bosken_acikca_yazar(dolu_tez, tmp_path):
    yol = tmp_path / "cikti.docx"
    docx_uret(_kaynakcasiz_lastir(dolu_tez), yol)
    with zipfile.ZipFile(yol) as z:
        govde = z.read("word/document.xml").decode("utf-8")
    assert "Kaynakça boş" in govde


def test_pdf_yazi_tipi_yoksa_acik_hata(dolu_tez, tmp_path, monkeypatch):
    """Unicode yazi tipi yoksa sessizce '?' basilmaz, ACIK hata verilir.

    fpdf2'nin gomulu fontu Turkcenin yarisini basamadigi icin bu sessiz
    bir veri kaybi olurdu; kullanici hatayi gorup cozebilmeli.
    """
    from tools.atw import export as mod

    monkeypatch.setattr(mod, "yazi_tipi_yolu", lambda: None)
    with pytest.raises(ExportHatasi, match="Unicode"):
        disa_aktar(dolu_tez, "pdf", tmp_path)
    assert list(tmp_path.iterdir()) == [], "hata verilmisken dosya yazildi"


def test_yazi_tipi_bulunamazsa_none_doner(monkeypatch):
    """Aday hicbiri yoksa `None`; cift yazi tipi uydurulmaz."""
    from tools.atw import export as mod

    monkeypatch.setattr(mod, "YAZI_TIPI_ADAYLARI", ("/yok/bir.ttf",))
    assert mod.yazi_tipi_yolu() is None


def test_tez_kimligi_bos_ise_yedek_ad(dolu_tez, tmp_path):
    """Kimlik bos/ayirici ise dosya yine de uretilir."""
    dolu_tez["thesis_id"] = "///"
    yol, _ = disa_aktar(dolu_tez, "md", tmp_path)
    assert yol.name == "tez_tez.md", yol.name
    assert yol.parent == tmp_path


def test_tez_kimligi_cift_alt_cizgi_birlesir(dolu_tez, tmp_path):
    """Girdideki `__` tek `_` olur; isim okunur kalir.

    Ayirici OLMAYAN karakterler (`_`, `-`) regex'i gecirdigi icin_once
    `__` uretilmez; kaynakta zaten var olan cift alt cizgi birlestirilir.
    """
    dolu_tez["thesis_id"] = "A__B"
    yol, _ = disa_aktar(dolu_tez, "md", tmp_path)
    assert yol.name == "tez_A_B.md", yol.name


def test_ayirici_dizileri_tek_karaktere_indirgenir(dolu_tez, tmp_path):
    """Ardisik ayiricilar regex `+` sayesinde TEK `_` olur."""
    dolu_tez["thesis_id"] = "A   B///C"
    yol, _ = disa_aktar(dolu_tez, "md", tmp_path)
    assert yol.name == "tez_A_B_C.md", yol.name


def test_nokta_temizleme_sonu_tek_nokta_yapar():
    """`_nokta_temizle` sozlesmesi: sonda tam olarak bir nokta.

    Dogrudan yardimci birimi: `apa_kaynak_girdisi` govdeyi her zaman
    noktayla bitirdigi icin bu dal genel API'den erisilemez, ama
    yardimcinin SOZLESMESI budur ve gevsek birakilinca bir sonraki
    cagrida sessizce bozulur.

    KAPSAMI: yalnizca ARDISIK noktalar birlestirilir. "A. . ." gibi
    aralikli bir yazim metnin parcasi olabilir; onu bozmak dogru olmaz.
    """
    from tools.atw.export import _nokta_temizle

    assert _nokta_temizle("A...") == "A."
    assert _nokta_temizle("A..") == "A."
    assert _nokta_temizle("A") == "A."
    assert _nokta_temizle("A.") == "A."
    assert _nokta_temizle("  A  ") == "A."
    assert _nokta_temizle("A. . .") == "A. . .", "aralikli nokta bozulmamali"
    assert _nokta_temizle("") == ""
