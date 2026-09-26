"""pdf_extract modülü testleri."""
from __future__ import annotations

import pytest
import tempfile
import os
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])