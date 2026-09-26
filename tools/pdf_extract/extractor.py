"""PDF metin çıkarma ve bölüm tespiti.

pdfplumber kullanarak sayfa metni, tablolar, başlıklar çıkarır.
Bölüm hiyerarşisi (Abstract, Introduction, Methods, Results, Discussion, Conclusion) tespiti.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import pdfplumber

logger = logging.getLogger(__name__)


# Yaygın akademik bölüm başlıkları (büyük/küçük harf duyarsız)
SECTION_PATTERNS = [
    (r"^\s*abstract\s*$", "Abstract"),
    (r"^\s*introduction\s*$", "Introduction"),
    (r"^\s*background\s*$", "Background"),
    (r"^\s*related\s+work\s*$", "Related Work"),
    (r"^\s*methods?\s*$", "Methods"),
    (r"^\s*methodology\s*$", "Methodology"),
    (r"^\s*materials?\s+and\s+methods?\s*$", "Materials and Methods"),
    (r"^\s*experimental\s+(setup|design)\s*$", "Experimental Setup"),
    (r"^\s*results?\s*$", "Results"),
    (r"^\s*findings\s*$", "Findings"),
    (r"^\s*discussion\s*$", "Discussion"),
    (r"^\s*conclusion\s*$", "Conclusion"),
    (r"^\s*conclusions?\s*$", "Conclusions"),
    (r"^\s*references?\s*$", "References"),
    (r"^\s*bibliography\s*$", "Bibliography"),
    (r"^\s*acknowledgments?\s*$", "Acknowledgments"),
    (r"^\s*appendix\s*[A-Z]?\s*$", "Appendix"),
    (r"^\s*supplementary\s+(material|information)\s*$", "Supplementary Material"),
]

# Alt bölüm kalıpları
SUBSECTION_PATTERNS = [
    r"^\s*\d+(\.\d+)*\s+[A-Z][a-z].*$",  # 1.1 Introduction, 2.3.1 Participants
    r"^\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*$",  # Participants, Statistical Analysis
]

# Başlık tanıma: kısa, büyük harfle başlayan, noktalama yok
HEADING_PATTERN = re.compile(r"^[A-Z][A-Za-z\s]{2,50}$")


@dataclass
class PDFPage:
    """PDF sayfası metni ve meta verisi."""
    page_number: int
    text: str
    tables: list[list[list[str]]] = field(default_factory=list)
    chars: list[dict] = field(default_factory=list)  # pdfplumber char info


@dataclass
class PDFSection:
    """PDF bölümü (heading + içerik)."""
    title: str
    level: int  # 1=ana bölüm, 2=alt bölüm
    page_start: int
    page_end: int
    text: str
    char_start: int = 0
    char_end: int = 0
    subsection_of: Optional[str] = None


@dataclass
class ExtractedEvidence:
    """Çıkarılan kanıt."""
    text: str
    page: int
    section: str
    subsection: Optional[str] = None
    paragraph_index: Optional[int] = None
    char_start: int = 0
    char_end: int = 0
    evidence_type: str = "literature"
    strength: str = "direct"
    supports_claim: Optional[str] = None
    confidence: float = 0.0


class PDFExtractor:
    """PDF'ten metin ve kanıt çıkarma."""

    def __init__(
        self,
        pdf_path: str | Path,
        min_heading_length: int = 3,
        max_heading_length: int = 80,
    ):
        self.pdf_path = Path(pdf_path)
        self.min_heading_length = min_heading_length
        self.max_heading_length = max_heading_length
        self._pdf = None
        self.pages: list[PDFPage] = []
        self.sections: list[PDFSection] = []

    def __enter__(self):
        self._pdf = pdfplumber.open(self.pdf_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._pdf:
            self._pdf.close()

    def extract_all(self) -> dict[str, Any]:
        """Tüm PDF'i işle: metin, bölümler, tablolar."""
        if not self._pdf:
            raise RuntimeError("PDF açılmadı. Context manager kullanın.")

        self.pages = []
        full_text_parts = []
        char_offset = 0

        for i, page in enumerate(self._pdf.pages):
            page_num = i + 1
            text = page.extract_text() or ""
            tables = page.extract_tables() or []

            # Karakter bilgileri (sayfa numarası doğrulaması için)
            chars = page.chars or []

            page_obj = PDFPage(
                page_number=page_num,
                text=text,
                tables=tables,
                chars=chars,
            )
            self.pages.append(page_obj)

            full_text_parts.append(text)
            char_offset += len(text) + 1  # +1 for newline

        full_text = "\n".join(full_text_parts)

        # Bölüm tespiti
        self.sections = self._detect_sections(full_text)

        return {
            "pages": self.pages,
            "sections": self.sections,
            "full_text": full_text,
            "page_count": len(self.pages),
        }

    def _detect_sections(self, full_text: str) -> list[PDFSection]:
        """Metinden bölüm hiyerarşisi tespit et."""
        lines = full_text.split("\n")
        sections = []
        current_section: Optional[PDFSection] = None
        current_subsection: Optional[PDFSection] = None
        char_offset = 0

        for line_idx, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                char_offset += len(line) + 1
                continue

            # Ana bölüm kontrolü
            matched_section = None
            for pattern, section_name in SECTION_PATTERNS:
                if re.match(pattern, line_stripped, re.IGNORECASE):
                    matched_section = section_name
                    break

            if matched_section:
                # Önceki bölümü kapat
                if current_section:
                    current_section.char_end = char_offset
                    current_section.page_end = self._estimate_page(char_offset)
                    sections.append(current_section)

                # Yeni ana bölüm
                current_section = PDFSection(
                    title=matched_section,
                    level=1,
                    page_start=self._estimate_page(char_offset),
                    page_end=0,
                    text="",
                    char_start=char_offset,
                )
                current_subsection = None
                char_offset += len(line) + 1
                continue

            # Alt bölüm kontrolü (sadece ana bölüm varsa)
            if current_section and self._is_subsection_heading(line_stripped):
                if current_subsection:
                    current_subsection.char_end = char_offset
                    current_subsection.page_end = self._estimate_page(char_offset)
                    sections.append(current_subsection)

                current_subsection = PDFSection(
                    title=line_stripped,
                    level=2,
                    page_start=self._estimate_page(char_offset),
                    page_end=0,
                    text="",
                    char_start=char_offset,
                    subsection_of=current_section.title,
                )
                char_offset += len(line) + 1
                continue

            # Metni mevcut bölüme ekle
            if current_subsection:
                current_subsection.text += line + "\n"
            elif current_section:
                current_section.text += line + "\n"

            char_offset += len(line) + 1

        # Son bölümleri kapat
        if current_subsection:
            current_subsection.char_end = char_offset
            current_subsection.page_end = self._estimate_page(char_offset)
            sections.append(current_subsection)
        if current_section:
            current_section.char_end = char_offset
            current_section.page_end = self._estimate_page(char_offset)
            sections.append(current_section)

        # Boş metinli bölümleri temizle
        return [s for s in sections if s.text.strip()]

    def _is_subsection_heading(self, line: str) -> bool:
        """Satır alt bölüm başlığı mı?"""
        if not line or len(line) > self.max_heading_length or len(line) < self.min_heading_length:
            return False
        # Başlık kalıbı: kısa, büyük harfle başlayan, nokta ile bitmeyen
        if HEADING_PATTERN.match(line):
            return True
        # Numaralı başlık: 1.1, 2.3.1 gibi
        if re.match(r"^\s*\d+(\.\d+)+\s+[A-Z]", line):
            return True
        return False

    def _estimate_page(self, char_offset: int) -> int:
        """Karakter ofsetinden tahmini sayfa numarası."""
        if not self.pages:
            return 1
        # Ortalama sayfa başına karakter sayısı
        avg_chars_per_page = sum(len(p.text) for p in self.pages) / max(len(self.pages), 1)
        estimated = max(1, int(char_offset / max(avg_chars_per_page, 1)) + 1)
        return min(estimated, len(self.pages))

    def find_evidence_for_claim(
        self,
        claim_text: str,
        claim_keywords: list[str] | None = None,
        top_k: int = 5,
        min_similarity: float = 0.3,
    ) -> list[ExtractedEvidence]:
        """İddia metni için en alakalı kanıtları bul (TF-IDF similarity)."""
        from .similarity import compute_tfidf_similarity

        if claim_keywords is None:
            # İddia metninden anahtar kelimeleri çıkar
            claim_keywords = self._extract_keywords(claim_text)

        candidates = []

        for section in self.sections:
            if not section.text.strip():
                continue

            # Paragraflara böl
            paragraphs = [p.strip() for p in section.text.split("\n\n") if p.strip()]

            for para_idx, paragraph in enumerate(paragraphs):
                if len(paragraph) < 50:  # Çok kısa paragrafları atla
                    continue

                # TF-IDF benzerlik
                similarity = compute_tfidf_similarity(claim_text, paragraph)

                if similarity >= min_similarity:
                    # Anahtar kelime bonus
                    keyword_bonus = 0.0
                    if claim_keywords:
                        matches = sum(1 for kw in claim_keywords if kw.lower() in paragraph.lower())
                        keyword_bonus = min(matches * 0.05, 0.2)

                    final_score = similarity + keyword_bonus

                    evidence = ExtractedEvidence(
                        text=paragraph[:1000],  # Max 1000 char
                        page=section.page_start,
                        section=section.title,
                        subsection=current_subsection.title if current_subsection else None,
                        paragraph_index=para_idx,
                        char_start=section.char_start,
                        char_end=section.char_end,
                        confidence=final_score,
                    )
                    candidates.append(evidence)

        # Skora göre sırala ve top-k döndür
        candidates.sort(key=lambda e: e.confidence, reverse=True)
        return candidates[:top_k]

    def _extract_keywords(self, text: str) -> list[str]:
        """Metinden anahtar kelimeleri çıkar (basit: stopwords çıkar, 3+ harf)."""
        stopwords = {
            "the", "a", "an", "and", "or", "of", "in", "for", "to", "with", "on", "by",
            "as", "at", "from", "into", "during", "including", "until", "against",
            "among", "throughout", "despite", "towards", "upon", "within", "without",
            "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
            "do", "does", "did", "will", "would", "could", "should", "may", "might",
            "must", "shall", "can", "this", "that", "these", "those", "it", "its",
            "we", "our", "you", "your", "he", "she", "his", "her", "they", "their",
        }
        words = re.findall(r"\b[a-z]{3,}\b", text.lower())
        return list(set(w for w in words if w not in stopwords and len(w) > 3))[:20]


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """PDF'ten ham metin çıkar (basit fonksiyon)."""
    with pdfplumber.open(pdf_path) as pdf:
        texts = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                texts.append(text)
        return "\n".join(texts)


def extract_text_from_pdf_with_pages(pdf_path: str | Path) -> list[tuple[int, str]]:
    """PDF'ten sayfa bazlı metin çıkar."""
    results = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if text.strip():
                results.append((i + 1, text))
    return results


def detect_sections(text: str) -> list[PDFSection]:
    """Metinden bölüm tespiti (PDFExtractor'dan bağımsız)."""
    extractor = PDFExtractor.__new__(PDFExtractor)
    extractor.min_heading_length = 3
    extractor.max_heading_length = 80
    extractor.pages = []  # _estimate_page için gerekli
    return extractor._detect_sections(text)


def find_evidence_for_claim(
    pdf_path: str | Path,
    claim_text: str,
    claim_keywords: list[str] | None = None,
    top_k: int = 5,
    min_similarity: float = 0.3,
) -> list[ExtractedEvidence]:
    """PDF'den iddiaya uygun kanıtları bul (yüksek seviye fonksiyon)."""
    with PDFExtractor(pdf_path) as extractor:
        extractor.extract_all()
        return extractor.find_evidence_for_claim(
            claim_text=claim_text,
            claim_keywords=claim_keywords,
            top_k=top_k,
            min_similarity=min_similarity,
        )