"""tools.pdf_extract — PDF'ten kanıt çıkarma modülü.

Sayfa/bölüm düzeyinde kanıt çıkarma, claim-evidence linking,
Unpaywall OA kontrolü ile PDF indirme.
"""
from __future__ import annotations

from .extractor import (
    extract_text_from_pdf,
    extract_text_from_pdf_with_pages,
    detect_sections,
    find_evidence_for_claim,
    PDFExtractor,
    PDFPage,
    PDFSection,
    ExtractedEvidence,
)
from .downloader import download_pdf, check_unpaywall_oa, PDFDownloader
from .similarity import compute_tfidf_similarity, rank_evidence_for_claim

__all__ = [
    "extract_text_from_pdf",
    "extract_text_from_pdf_with_pages",
    "detect_sections",
    "find_evidence_for_claim",
    "PDFExtractor",
    "PDFPage",
    "PDFSection",
    "ExtractedEvidence",
    "download_pdf",
    "check_unpaywall_oa",
    "PDFDownloader",
    "compute_tfidf_similarity",
    "rank_evidence_for_claim",
]