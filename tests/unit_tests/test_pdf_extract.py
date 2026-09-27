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