"""pdf_extract modülü testleri."""
from __future__ import annotations

import pytest
import tempfile
import os
import argparse
from pathlib import Path

from tools.pdf_extract import (
    extract_text_from_pdf,
    extract_text_from_pdf_with_pages,
    detect_sections,
    find_evidence_for_claim,
    PDFExtractor,
    PDFPage,
    PDFSection,
    ExtractedEvidence,
    download_pdf,
    check_unpaywall_oa,
    compute_tfidf_similarity,
    rank_evidence_for_claim,
)


def test_imports():
    """Modüller import edilebiliyor mu?"""
    from tools.pdf_extract import extractor, downloader, similarity
    assert extractor is not None
    assert downloader is not None
    assert similarity is not None


def test_compute_tfidf_similarity():
    """TF-IDF benzerlik hesaplama testi."""
    text1 = "mindfulness based cognitive therapy reduces depression relapse"
    text2 = "mindfulness based cognitive therapy prevents depression relapse in adults"
    text3 = "exercise improves cardiovascular health"

    sim12 = compute_tfidf_similarity(text1, text2)
    sim13 = compute_tfidf_similarity(text1, text3)

    assert 0 <= sim12 <= 1
    assert 0 <= sim13 <= 1
    # Benzer metinler daha yüksek skor almalı
    assert sim12 > sim13


def test_rank_evidence_for_claim():
    """İddia için kanıt sıralama testi."""
    claim = "mindfulness reduces depression relapse"
    candidates = [
        {"text": "mindfulness based cognitive therapy prevents depression relapse", "id": "EVD-001"},
        {"text": "exercise improves cardiovascular health", "id": "EVD-002"},
        {"text": "cognitive therapy reduces anxiety symptoms", "id": "EVD-003"},
    ]

    results = rank_evidence_for_claim(claim, [c["text"] for c in candidates], top_k=2)

    assert len(results) == 2
    # En benzer olan ilk sırada olmalı
    assert results[0][0] == 0  # İlk aday (mindfulness)
    assert results[0][1] > results[1][1]  # Skor daha yüksek


def test_extract_keywords():
    """Anahtar kelime çıkarma testi."""
    from tools.pdf_extract.similarity import ClaimEvidenceMatcher

    matcher = ClaimEvidenceMatcher()
    text = "mindfulness based cognitive therapy reduces depression relapse in adults"
    keywords = matcher._extract_keywords(text)

    assert "mindfulness" in keywords
    assert "cognitive" in keywords
    assert "therapy" in keywords
    assert "depression" in keywords
    assert "relapse" in keywords
    assert "adults" in keywords
    # Stopwords olmamalı
    assert "the" not in keywords
    assert "and" not in keywords
    assert "in" not in keywords


def test_detect_sections():
    """Bölüm tespiti testi."""
    text = """
    Abstract
    This study examines mindfulness therapy.

    Introduction
    Depression is a common disorder.

    Methods
    We conducted a randomized controlled trial.

    Results
    The treatment group showed significant improvement.

    Discussion
    The findings suggest mindfulness is effective.
    """

    sections = detect_sections(text)

    assert len(sections) >= 4
    section_titles = [s.title for s in sections]
    assert "Abstract" in section_titles
    assert "Introduction" in section_titles
    assert "Methods" in section_titles
    assert "Results" in section_titles
    assert "Discussion" in section_titles


def test_pdf_extractor_basic():
    """PDFExtractor temel testi (mock PDF ile)."""
    # Gerçek PDF dosyası olmadığı için sadece import ve sınıf oluşturma test ediliyor
    extractor = PDFExtractor.__new__(PDFExtractor)
    assert extractor is not None


def test_similarity_engine():
    """TFIDFSimilarityEngine testi."""
    from tools.pdf_extract.similarity import TFIDFSimilarityEngine

    engine = TFIDFSimilarityEngine()
    corpus = [
        "mindfulness based cognitive therapy for depression",
        "cognitive behavioral therapy for anxiety",
        "mindfulness meditation reduces stress",
    ]

    engine.fit(corpus)
    sim1 = engine.similarity("mindfulness therapy for depression", "mindfulness reduces depression")
    sim2 = engine.similarity("mindfulness therapy for depression", "exercise improves health")

    assert 0 <= sim1 <= 1
    assert 0 <= sim2 <= 1
    assert sim1 > sim2  # İlk çift daha benzer


def test_download_from_source_record_url_doi_siz(monkeypatch):
    """DOI'siz ama URL'si olan kayit, kaydin url alanindan indirilmelidir.

    Regresyon: download_from_source_record, kaydin 'url' alani yerine
    parametre olan 'source_url' degiskenini kontrol ediyordu; bu yuzden
    URL-only kayitlar hicbir zaman indirilemiyordu.
    """
    from tools.pdf_extract.downloader import PDFDownloader, DownloadResult

    indirilen = []
    downloader = PDFDownloader.__new__(PDFDownloader)  # ag kurulumu gerekmez
    monkeypatch.setattr(
        downloader,
        "download",
        lambda url, filename=None: indirilen.append(url) or DownloadResult(
            success=True, source_url=url, file_path=Path("/tmp/kurgusal.pdf")
        ),
    )

    sonuc = downloader.download_from_source_record(
        {"doi": "", "url": "https://ornek.org/makale.pdf"}
    )

    assert indirilen == ["https://ornek.org/makale.pdf"]
    assert sonuc.success is True


def test_download_from_source_record_ne_doi_ne_url():
    """Hem DOI hem URL yoksa hata donmelidir."""
    from tools.pdf_extract.downloader import PDFDownloader

    downloader = PDFDownloader.__new__(PDFDownloader)
    sonuc = downloader.download_from_source_record({})
    assert sonuc.success is False
    assert "DOI" in sonuc.error


def test_download_from_source_record_bos_url_dikkat():
    """Kaydin url alani bos string ise hata donmelidir."""
    from tools.pdf_extract.downloader import PDFDownloader

    downloader = PDFDownloader.__new__(PDFDownloader)
    sonuc = downloader.download_from_source_record({"doi": "", "url": "   "})
    assert sonuc.success is False


class _Yanit:
    """requests.Response'un download() icin gereken yuzeyini taklit eder."""

    def __init__(self, govde: bytes, content_type: str = "application/pdf"):
        self.govde = govde
        self.headers = {"Content-Type": content_type}

    def raise_for_status(self):
        return None

    def json(self):
        return {}

    def iter_content(self, chunk_size=8192):
        for i in range(0, len(self.govde), chunk_size):
            yield self.govde[i : i + chunk_size]


def test_download_html_govde_pdf_sayilmaz(tmp_path, monkeypatch):
    """HTML hata sayfasi .pdf olarak kaydedilmemeli; success=False donmeli.

    Regresyon: download(), Content-Type PDF degilse YALNIZCA uyari verip
    HTML govdeyi .pdf olarak yaziyor ve success=True donuyordu. Kaynak
    taramasinda 'indi=14' rapor edilirken dosyalarin cogu gercekte HTML
    hata sayfasiydi ve sonraki asama 'PDF degil' diye cokuyordu.
    """
    from tools.pdf_extract.downloader import PDFDownloader

    indirici = PDFDownloader(download_dir=str(tmp_path), max_retries=1)
    monkeypatch.setattr(
        indirici.session,
        "get",
        lambda *a, **k: _Yanit(b"<!DOCTYPE html><html>hata sayfasi</html>", "text/html"),
    )

    sonuc = indirici.download("https://ornek.org/makale.pdf?p=1", filename="test.pdf")

    assert sonuc.success is False
    assert "PDF" in sonuc.error
    assert not (tmp_path / "test.pdf").exists()


def test_download_gercek_pdf_kaydedilir(tmp_path, monkeypatch):
    """Gecerli %PDF govde kaydedilmeli ve success=True donmeli."""
    from tools.pdf_extract.downloader import PDFDownloader

    govde = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"
    indirici = PDFDownloader(download_dir=str(tmp_path), max_retries=1)
    monkeypatch.setattr(
        indirici.session,
        "get",
        lambda *a, **k: _Yanit(govde, "application/pdf"),
    )

    sonuc = indirici.download("https://ornek.org/makale.pdf", filename="test.pdf")

    assert sonuc.success is True
    assert (tmp_path / "test.pdf").read_bytes() == govde


def test_download_mevcut_cop_dosya_guvenilmez(tmp_path, monkeypatch):
    """Diskteki HTML/cop .pdf dosyasi guvenilmemeli; yeniden indirilmeli.

    Regresyon: 'zaten var' kestirmesi YALNIZCA dosyanin varligina bakiyordu;
    onceki hatali indirmelerle olusan HTML copu success=True olarak rapor
    ediliyor ve gecerli gorsele yeniden denenmeden hiç indirilemiyordu.
    """
    from tools.pdf_extract.downloader import PDFDownloader

    cop = tmp_path / "test.pdf"
    cop.write_bytes(b"<!DOCTYPE html><html>onceki hata</html>")

    govde = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"
    indirici = PDFDownloader(download_dir=str(tmp_path), max_retries=1)
    monkeypatch.setattr(
        indirici.session,
        "get",
        lambda *a, **k: _Yanit(govde, "application/pdf"),
    )

    sonuc = indirici.download("https://ornek.org/makale.pdf", filename="test.pdf")

    assert sonuc.success is True
    assert (tmp_path / "test.pdf").read_bytes() == govde


def test_check_unpaywall_email_siz_ag_istemez(monkeypatch):
    """Unpaywall API email gerektirir; email yoksa ag cagrisi YAPILMAMALI.

    Regresyon: email opsiyonel saniliyordu; email'siz her DOI icin API
    422 ile reddediyor, bos bir ag turu yapiliyor ve OA kontrolu sessizce
    kayboluyordu (her kaynak icin yaklasik 5 saniye bos bekleyis).
    """
    from tools.pdf_extract.downloader import PDFDownloader

    cagrilar = []
    indirici = PDFDownloader.__new__(PDFDownloader)
    indirici.unpaywall_email = None
    monkeypatch.setattr(
        "tools.pdf_extract.downloader.requests.get",
        lambda *a, **k: cagrilar.append(a) or _Yanit(b"{}"),
    )

    sonuc = indirici.check_unpaywall("10.1000/ornek")

    assert sonuc is None
    assert cagrilar == []


def test_query_coverage_ortak_kelimeler():
    """query_coverage, iddianin oz kelimelerinin metindeki kapsamini verir."""
    from tools.pdf_extract.similarity import query_coverage

    iddia = "Breeding seasonality, nesting and reproductive output of chukar partridges are associated with environmental conditions and habitat quality."
    paragraf = ("Breeding seasonality of chukar partridges begins in early spring; "
                "nesting success and reproductive output depend on habitat quality "
                "and environmental conditions.")
    alakasiz = "Exercise improves cardiovascular health in older adults who walk regularly."

    kapsam = query_coverage(iddia, paragraf)
    sifir = query_coverage(iddia, alakasiz)

    assert 0.5 <= kapsam <= 1.0, f"Alakali paragraf kapsami cok dusuk: {kapsam}"
    assert sifir == 0.0


def test_find_evidence_ortak_kelime_kapsami_esigi_asar(tmp_path):
    """Kisa iddia - uzun paragraf korpusunda cosine dusuk kalsa bile ortak
    anahtar kelime kapsami esigi asmali ve kanit donmelidir.

    Regresyon: yalnizca TF-IDF cosine esigi (0.3) kullaniliyordu. Kisa iddia
    ile uzun paragraf arasinda cosine yapisal olarak 0.05-0.15 araliginda
    kaldigindan, gercek ve iliskili bir PDF'te bile extract komutu hicbir
    zaman 'kanit bulunamadi' diyordu (10/10 cift sifir sonuc).
    """
    from fpdf import FPDF
    from tools.pdf_extract.extractor import find_evidence_for_claim

    pdf = tmp_path / "deneme.pdf"
    p = FPDF()
    p.add_page()
    p.set_font("Helvetica", size=10)
    # Bölüm tespiti (SECTION_PATTERNS) gercek PDF'teki gibi baslik satiri ister
    p.multi_cell(0, 5, "Abstract")
    p.ln(2)
    p.multi_cell(
        0, 5,
        "Breeding seasonality of chukar partridges is closely linked to the "
        "environmental conditions of the study area. Nesting begins in early "
        "spring and reproductive output is higher where habitat quality and "
        "dense nesting cover are available, supporting the association between "
        "habitat and breeding performance of this species.",
    )
    p.output(str(pdf))

    iddia = ("Breeding seasonality, nesting and reproductive output of chukar "
             "partridges are associated with environmental conditions and "
             "habitat quality.")

    bulgular = find_evidence_for_claim(str(pdf), iddia, top_k=1, min_similarity=0.3)

    assert bulgular, "Ortak anahtar kelime kapsami olan paragraf bulunamadi"


def test_extract_dar_aralikli_pdf_sozcukleri_ayirir(tmp_path):
    """Sik dizilmis (dar aralikli) PDF metninde sozcukler ayrilmali.

    Regresyon: page.extract_text() pdfplumber varsayilani x_tolerance=3 ile
    calisiyordu; kelime arasi bosluk 3 birimden kucuk olan PDF'lerde tum
    sozcukler tek jetona birlesiyordu (SRC-143: 'RESEARCHARTICLE' ve
    'massivereleaseofcaptive-bredchukarpartridge' gibi) ve token tabanli
    eslestirme o kaynaklar icin hic kanit bulamiyordu.
    """
    from fpdf import FPDF
    from tools.pdf_extract.extractor import extract_text_from_pdf_with_pages

    pdf = tmp_path / "dar.pdf"
    p = FPDF()
    p.add_page()
    p.set_font("Helvetica", size=14)
    kelimeler = ["Breeding", "seasonality", "of", "chukar", "partridge",
                 "is", "linked", "to", "environmental", "conditions",
                 "and", "habitat", "quality."]
    x, y = 20.0, 40.0
    for kelime in kelimeler:
        p.text(x, y, kelime)
        x += p.get_string_width(kelime) + 0.8
    p.output(str(pdf))

    sayfalar = extract_text_from_pdf_with_pages(str(pdf))
    metin = " ".join(t for _, t in sayfalar)

    assert "Breeding seasonality of chukar partridge" in metin
    assert "Breedingseasonality" not in metin


# --- similarity: saf mantik (ag/PDF gerekmez) ------------------------------

# Aday metinleri >= 50 karakter olmali ve iddiayla ortak kelime icermeli,
# aksi halde find_evidence adayi eler ve esik degeri asilmaz.
_UZUN_BIR = ("Mindfulness based cognitive therapy reduces depression relapse "
             "in adults compared with treatment as usual.")
_UZUN_IKI = ("Exercise improves cardiovascular health in older adults who "
             "walk regularly for thirty minutes each day.")


def test_find_evidence_cokmemeli():
    """find_evidence bos aday listesiyle cagrilinca bos liste donmelidir.

    Regresyon: cosine_similarity(...)[0,0] bir numpy skaleri donuyor,
    ardindan tfidf_sim[0] ile indekslenmeye calisildigi icin her cagri
    IndexError ile patliyordu.
    """
    from tools.pdf_extract.similarity import ClaimEvidenceMatcher

    assert ClaimEvidenceMatcher().find_evidence("bir iddia", []) == []


def test_find_evidence_skorlari_ekler():
    """find_evidence sonuclarina tfidf_similarity, keyword_bonus, final_score ekler."""
    from tools.pdf_extract.similarity import ClaimEvidenceMatcher

    sonuc = ClaimEvidenceMatcher().find_evidence(
        "mindfulness reduces depression relapse",
        [{"id": "EVD-001", "text": _UZUN_BIR}, {"id": "EVD-002", "text": _UZUN_IKI}],
    )
    assert sonuc, "en az bir aday esigi asmali"
    ilk = sonuc[0]
    for alan in ("tfidf_similarity", "keyword_bonus", "final_score"):
        assert alan in ilk
        assert isinstance(ilk[alan], float)
    assert ilk["id"] == "EVD-001"  # konu eslesen aday one cikmali


def test_find_evidence_skora_gore_sirali():
    """Sonuclar final_score azalan sirada olmalidir."""
    from tools.pdf_extract.similarity import ClaimEvidenceMatcher

    sonuc = ClaimEvidenceMatcher().find_evidence(
        "mindfulness reduces depression relapse",
        [{"id": "EVD-001", "text": _UZUN_BIR}, {"id": "EVD-002", "text": _UZUN_IKI}],
    )
    skorlar = [kayit["final_score"] for kayit in sonuc]
    assert skorlar == sorted(skorlar, reverse=True)


def test_find_evidence_kisa_metni_atlar():
    """50 karakterden kisa adaylar degerlendirilmez."""
    from tools.pdf_extract.similarity import ClaimEvidenceMatcher

    sonuc = ClaimEvidenceMatcher().find_evidence(
        "bir iddia metni", [{"id": "EVD-001", "text": "cok kisa"}]
    )
    assert sonuc == []


def test_find_evidence_ozel_metin_alani():
    """text_field parametresi ile baska alan okunabilmelidir."""
    from tools.pdf_extract.similarity import ClaimEvidenceMatcher

    sonuc = ClaimEvidenceMatcher().find_evidence(
        "mindfulness reduces depression relapse",
        [{"id": "EVD-001", "ozet": _UZUN_BIR}], text_field="ozet",
    )
    assert sonuc and sonuc[0]["id"] == "EVD-001"


def test_keyword_bonus_ortusmeye_gore_artan():
    """Ortak anahtar kelime arttikca bonus artmalidir."""
    from tools.pdf_extract.similarity import ClaimEvidenceMatcher

    matcher = ClaimEvidenceMatcher()
    dusuk = matcher._keyword_bonus("mindfulness therapy depression", _UZUN_IKI)
    yuksek = matcher._keyword_bonus("mindfulness therapy depression", _UZUN_BIR)
    assert yuksek > dusuk
    assert yuksek <= matcher.max_keyword_bonus


def test_keyword_bonus_bos_claim_sifir():
    """Anahtar kelime icermeyen iddia icin bonus sifir olmalidir."""
    from tools.pdf_extract.similarity import ClaimEvidenceMatcher

    assert ClaimEvidenceMatcher()._keyword_bonus("the and of", _UZUN_BIR) == 0.0


def test_similarity_matrix_kosegenel():
    """similarity_matrix kare matris dondurmelidir."""
    from tools.pdf_extract.similarity import TFIDFSimilarityEngine

    engine = TFIDFSimilarityEngine()
    metinler = ["mindfulness therapy for depression", "exercise for heart health",
                "mindfulness reduces stress"]
    matris = engine.similarity_matrix(metinler)
    assert matris.shape == (3, 3)
    # Kosegen bazen 1.0000000000000002 doner; kayan nokta payi birakilir.
    assert all(-1e-9 <= deger <= 1 + 1e-9 for deger in matris[0])


def test_rank_similar_top_k_sinirli():
    """rank_similar en fazla top_k aday dondurmelidir."""
    from tools.pdf_extract.similarity import TFIDFSimilarityEngine

    engine = TFIDFSimilarityEngine()
    adaylar = ["mindfulness reduces depression", "exercise improves health",
               "mindfulness therapy for stress"]
    sonuc = engine.rank_similar("mindfulness depression", adaylar, top_k=2)
    assert len(sonuc) == 2
    skorlar = [skor for _, skor in sonuc]
    assert skorlar == sorted(skorlar, reverse=True)


def test_transform_girdi_sayisi_kadar_dondurur():
    """transform, verilen metin sayisi kadar vektor dondurmelidir.

    Not: TfidfVectorizer'in token_pattern'i tek harfli belirtecleri eler,
    bu yuzden test verisi iki+ harfli kelimelerden olusmalidir.
    """
    from tools.pdf_extract.similarity import TFIDFSimilarityEngine

    engine = TFIDFSimilarityEngine()
    engine.fit(["mindfulness therapy", "exercise health"])
    assert engine.transform(["mindfulness", "health", "yeni metin"]).shape[0] == 3
    assert engine.fit_transform(["alpha beta", "gamma delta"]).shape[0] == 2


def test_ayni_metin_en_yuksek_benzerlik():
    """Ayni metin kendisiyle en yuksek benzerlige sahip olmalidir."""
    from tools.pdf_extract.similarity import compute_tfidf_similarity

    metin = "mindfulness based cognitive therapy reduces depression relapse"
    assert compute_tfidf_similarity(metin, metin) > compute_tfidf_similarity(
        metin, "exercise improves cardiovascular health"
    )


# --- pdf_extract CLI: hic calismamis (import hatasi) ------------------------

def test_cli_modulu_ice_aktarilabilir():
    """tools.pdf_extract.cli import edilebilmeli.

    Regresyon: import blogu var olmayan 'EvidenceExtractor' sinifini ve
    kullanilmayan 'extract_text_from_pdf_with_pages' fonksiyonunu
    getiriyordu. Bu yuzden 'pdf-extract' komutu HIC calismamisti, 6 komut
    ve 176 satir kod tamamen erisilemez durumdaydi.
    """
    import tools.pdf_extract.cli as pdf_cli

    assert callable(pdf_cli.main)


def test_cli_yardimci_yolla_arguman_isler(monkeypatch):
    """main() alt komutu dogru komut fonksiyonuna yonlendirmeli."""
    import tools.pdf_extract.cli as pdf_cli

    cagrilan = []
    monkeypatch.setattr(
        pdf_cli, "cmd_extract_text", lambda args: cagrilan.append("text") or 0
    )
    monkeypatch.setattr(
        pdf_cli, "cmd_download", lambda args: cagrilan.append("download") or 0
    )
    monkeypatch.setattr("sys.argv", ["pdf-extract", "extract-text", "x.pdf"])
    assert pdf_cli.main() == 0
    monkeypatch.setattr("sys.argv", ["pdf-extract", "download", "--doi", "10.1/x"])
    assert pdf_cli.main() == 0
    assert cagrilan == ["text", "download"]


def test_cli_bilinmeyen_komut_yardim_gosterir(monkeypatch):
    """Alt komut secilmezse yardim metni gosterilip 1 donmelidir."""
    import tools.pdf_extract.cli as pdf_cli

    monkeypatch.setattr("sys.argv", ["pdf-extract"])
    with pytest.raises(SystemExit):
        pdf_cli.main()


def test_cli_extract_text_yok_dosya_hata(tmp_path):
    """Var olmayan PDF yolunda hata donmeli."""
    import tools.pdf_extract.cli as pdf_cli

    args = argparse.Namespace(
        pdf=str(tmp_path / "yok.pdf"), output=None, pages=False
    )
    assert pdf_cli.cmd_extract_text(args) == 1


def test_cli_extract_evidence_yok_dosya_hata(tmp_path):
    """Var olmayan PDF yolunda kanit komutu hata donmeli."""
    import tools.pdf_extract.cli as pdf_cli

    args = argparse.Namespace(
        pdf=str(tmp_path / "yok.pdf"), claim="bir iddia", claim_id="CLM-001",
        keywords=None, top_k=5, min_sim=0.3, output=None,
    )
    assert pdf_cli.cmd_extract_evidence(args) == 1


def test_cli_extract_evidence_hata_yutucu(monkeypatch, tmp_path):
    """Cikarim sirasinda istisna olursa hata mesaji yazilip 1 donmeli."""
    import tools.pdf_extract.cli as pdf_cli

    pdf = tmp_path / "sahte.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    def patlat(**kwargs):
        raise RuntimeError("kurgusal hata")

    monkeypatch.setattr(pdf_cli, "find_evidence_for_claim", patlat)
    args = argparse.Namespace(
        pdf=str(pdf), claim="bir iddia", claim_id="CLM-001",
        keywords="a, b", top_k=5, min_sim=0.3, output=None,
    )
    assert pdf_cli.cmd_extract_evidence(args) == 1


def test_cli_anahtar_kelimeleri_ayirir(monkeypatch, tmp_path):
    """--keywords degeri virgulle ayrilmis anahtar kelimelere bolunmeli."""
    import tools.pdf_extract.cli as pdf_cli

    pdf = tmp_path / "sahte.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    alinan = {}

    def yakala(**kwargs):
        alinan.update(kwargs)
        return []

    monkeypatch.setattr(pdf_cli, "find_evidence_for_claim", yakala)
    args = argparse.Namespace(
        pdf=str(pdf), claim="bir iddia", claim_id="CLM-001",
        keywords="mindfulness, depresyon , terapi", top_k=3, min_sim=0.5,
        output=None,
    )
    assert pdf_cli.cmd_extract_evidence(args) == 0
    assert alinan["claim_keywords"] == ["mindfulness", "depresyon", "terapi"]
    assert alinan["top_k"] == 3
    assert alinan["min_similarity"] == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])