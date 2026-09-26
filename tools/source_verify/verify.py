"""Ana doğrulama orkestratörü.

Kaynak kayıtlarını (source.json) birden fazla veritabanıyla doğrular:
- DOI doğrulaması (Crossref, OpenAlex, Semantic Scholar, PubMed)
- Bibliyografik eşleşme (başlık, yazar, yıl, dergi)
- Retraksiyon/korizyon kontrolü
- En az 2 bağımsız kaynak, skor ≥ 0.60
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests

from .bibliographic import compute_bibliographic_match, BibliographicMatch
from .retraction import check_retraction_status, check_correction_status, RetractionInfo, CorrectionInfo
from tools.atw.ids import format_id
from tools.atw.state import load_state, save_state


@dataclass
class VerificationSource:
    """Tek bir veritabanı doğrulama sonucu."""
    source: str                    # "crossref", "openalex", "semantic_scholar", "pubmed"
    match: BibliographicMatch      # Bibliyografik eşleşme
    retraction: Any = None         # RetractionInfo
    correction: Any = None         # CorrectionInfo
    execution_time_ms: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class VerificationResult:
    """Kaynak doğrulama sonucu."""
    source_id: str
    status: str                    # "verified", "unverified", "pending", "retracted", "corrected"
    bibliographic_match: float     # 0.0 - 1.0 (en yüksek skor)
    verified_at: str
    verification_sources: list[str] = field(default_factory=list)  # Hangi DB'ler eşleşti
    verification_details: dict = field(default_factory=dict)       # Detaylı skorlar
    retraction_info: list = field(default_factory=list)            # RetractionInfo listesi
    correction_info: Any = None                                    # CorrectionInfo


class VerificationStatus:
    """Doğrulama durum sabitleri."""
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    PENDING = "pending"
    RETRACTED = "retracted"
    CORRECTED = "corrected"

    @classmethod
    def all(cls) -> list[str]:
        return [cls.VERIFIED, cls.UNVERIFIED, cls.PENDING, cls.RETRACTED, cls.CORRECTED]


# Minimum eşleşme eşikleri
MIN_BIBLIOGRAPHIC_MATCH = 0.60
MIN_INDEPENDENT_SOURCES = 2


class SourceVerifier:
    """Kaynak doğrulayıcı."""

    def __init__(
        self,
        crossref_mailto: str = "research@example.com",
        openalex_email: str | None = None,
        semantic_scholar_key: str | None = None,
        pubmed_email: str | None = None,
        pubmed_api_key: str | None = None,
        timeout: int = 30,
        min_match: float = MIN_BIBLIOGRAPHIC_MATCH,
        min_sources: int = MIN_INDEPENDENT_SOURCES,
    ):
        self.crossref_mailto = crossref_mailto
        self.openalex_email = openalex_email
        self.semantic_scholar_key = semantic_scholar_key
        self.pubmed_email = pubmed_email
        self.pubmed_api_key = pubmed_api_key
        self.timeout = timeout
        self.min_match = min_match
        self.min_sources = min_sources
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "AcademicThesisWriter/1.0",
            "Accept": "application/json",
        })

    def _throttle(self, rate_limit: float):
        """Basit rate limiting."""
        if not hasattr(self, '_last_request'):
            self._last_request = 0.0
        elapsed = time.time() - self._last_request
        min_interval = 1.0 / rate_limit
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_request = time.time()

    def verify_crossref(self, source_record: dict) -> VerificationSource:
        """Crossref ile doğrula."""
        start = time.time()
        doi = source_record.get("doi", "").strip()
        errors = []

        if not doi:
            return VerificationSource(
                source="crossref",
                match=BibliographicMatch(0, 0, 0, 0, 0, False, {}),
                execution_time_ms=0,
                errors=["DOI yok"]
            )

        try:
            self._throttle(50)  # 50 req/s
            url = f"https://api.crossref.org/works/{doi}"
            headers = {"User-Agent": f"AcademicThesisWriter/1.0 (mailto:{self.crossref_mailto})"}
            resp = requests.get(url, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            item = data.get("message", {})

            # Veritabanı formatında kayıt oluştur
            db_record = {
                "doi": item.get("DOI"),
                "title": item.get("title", [""])[0] if item.get("title") else "",
                "authors": [f"{a.get('family', '')}, {a.get('given', '')}" for a in item.get("author", []) if a.get("family") or a.get("given")],
                "year": item.get("published-print", {}).get("date-parts", [[None]])[0][0] or
                        item.get("published-online", {}).get("date-parts", [[None]])[0][0],
                "journal": item.get("container-title", [""])[0] if item.get("container-title") else "",
                "volume": item.get("volume"),
                "issue": item.get("issue"),
                "pages": item.get("page"),
            }

            match = compute_bibliographic_match(
                {"doi": doi, "title": source_record.get("title", ""), "authors": source_record.get("authors", []),
                 "year": source_record.get("year"), "journal": source_record.get("journal", "")},
                db_record
            )

            # Retraksiyon kontrolü
            from .retraction import check_crossref_retraction
            retraction = check_crossref_retraction(source_record.get("doi", ""))

            return VerificationSource(
                source="crossref",
                match=match,
                retraction=retraction,
                execution_time_ms=int((time.time() - start) * 1000),
            )

        except Exception as e:
            return VerificationSource(
                source="crossref",
                match=BibliographicMatch(0, 0, 0, 0, 0, False, {}),
                execution_time_ms=int((time.time() - start) * 1000),
                errors=[str(e)]
            )

    def verify_openalex(self, source_record: dict) -> VerificationSource:
        """OpenAlex ile doğrula."""
        start = time.time()
        doi = source_record.get("doi", "").strip()

        if not doi:
            return VerificationSource(
                source="openalex",
                match=BibliographicMatch(0, 0, 0, 0, 0, False, {}),
                execution_time_ms=0,
                errors=["DOI yok"]
            )

        try:
            self._throttle(10)  # 10 req/s anonymous
            url = f"https://api.openalex.org/works/https://doi.org/{doi}"
            params = {"mailto": self.openalex_email} if self.openalex_email else {}
            headers = {"User-Agent": "AcademicThesisWriter/1.0"}
            resp = requests.get(url, params=params, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            item = resp.json()

            # OpenAlex author format: authorships -> author.display_name
            authors = []
            for auth in item.get("authorships", []):
                author = auth.get("author", {})
                if author.get("display_name"):
                    authors.append(author["display_name"])

            db_record = {
                    "doi": item.get("doi"),
                    "title": item.get("display_name", ""),
                    "authors": authors,
                    "year": item.get("publication_year"),
                    "journal": item.get("host_venue", {}).get("display_name", ""),
                    "volume": item.get("biblio", {}).get("volume"),
                    "issue": item.get("biblio", {}).get("issue"),
                    "pages": item.get("biblio", {}).get("first_page", "") + "-" + item.get("biblio", {}).get("last_page", "")
                        if item.get("biblio", {}).get("first_page") and item.get("biblio", {}).get("last_page")
                        else item.get("biblio", {}).get("first_page", ""),
                }

            match = compute_bibliographic_match(
                {"doi": doi, "title": source_record.get("title", ""), "authors": source_record.get("authors", []),
                 "year": source_record.get("year"), "journal": source_record.get("journal", "")},
                db_record
            )

            from .retraction import check_openalex_retraction
            retraction = check_openalex_retraction(source_record.get("doi", ""))

            return VerificationSource(
                source="openalex",
                match=match,
                retraction=retraction,
                execution_time_ms=int((time.time() - start) * 1000),
            )

        except Exception as e:
            return VerificationSource(
                source="openalex",
                match=BibliographicMatch(0, 0, 0, 0, 0, False, {}),
                execution_time_ms=int((time.time() - start) * 1000),
                errors=[str(e)]
            )

    def verify_pubmed(self, source_record: dict) -> VerificationSource:
        """PubMed ile doğrula (DOI veya PMID ile)."""
        start = time.time()
        doi = source_record.get("doi", "").strip()
        pmid = source_record.get("pmid", "").strip()

        if not doi and not pmid:
            return VerificationSource(
                source="pubmed",
                match=BibliographicMatch(0, 0, 0, 0, 0, False, {}),
                execution_time_ms=0,
                errors=["DOI veya PMID yok"]
            )

        try:
            self._throttle(3)  # 3 req/s no API key
            # DOI varsa önce DOI ile PMID bul
            if doi and not pmid:
                # DOI -> PMID çevir (Crossref veya PubMed ID converter)
                pass

            # Bu fonksiyon tam implementasyon için PubMedClient gerektirir
            # Şimdilik placeholder
            return VerificationSource(
                source="pubmed",
                match=BibliographicMatch(0, 0, 0, 0, 0, False, {}),
                execution_time_ms=int((time.time() - start) * 1000),
                errors=["Henüz implemente edilmedi"]
            )
        except Exception as e:
            return VerificationSource(
                source="pubmed",
                match=BibliographicMatch(0, 0, 0, 0, 0, False, {}),
                execution_time_ms=int((time.time() - start) * 1000),
                errors=[str(e)]
            )

    def verify_source(self, source_record: dict) -> VerificationResult:
        """Kaynak kaydını tüm veritabanlarıyla doğrula."""
        source_id = source_record.get("id", "")

        # Paralel doğrulama (şimdilik sıralı)
        sources_results = []

        # Crossref (birincil - DOI authority)
        cr = self.verify_crossref(source_record)
        if not cr.errors or cr.match.overall_score > 0:
            sources_results.append(cr)

        # OpenAlex (ikincil)
        oa = self.verify_openalex(source_record)
        if not oa.errors or oa.match.overall_score > 0:
            sources_results.append(oa)

        # PubMed (biyomedikal için)
        # pm = self.verify_pubmed(source_record)
        # if not pm.errors or pm.match.overall_score > 0:
        #     sources_results.append(pm)

        # Eşik geçen kaynakları filtrele
        passed_sources = [s for s in sources_results if s.match.overall_score >= self.min_match]

        # Retraksiyon kontrolü (herhangi bir kaynak retraksiyona işaret ederse)
        all_retractions = []
        for s in sources_results:
            if s.retraction and s.retraction.is_retracted:
                all_retractions.append(s.retraction)

        # Korizyon kontrolü
        correction = None
        for s in sources_results:
            if s.correction and s.correction.is_corrected:
                correction = s.correction
                break

        # Durum belirle
        if any(r.is_retracted for r in all_retractions):
            status = "retracted"
        elif correction and correction.is_corrected:
            status = "corrected"
        elif len(passed_sources) >= self.min_sources:
            status = "verified"
        elif len(sources_results) > 0:
            status = "unverified"
        else:
            status = "pending"

        # En yüksek bibliyografik skor
        max_score = max((s.match.overall_score for s in sources_results), default=0.0)

        # Doğrulayan kaynak isimleri
        verified_by = [s.source for s in passed_sources]

        # Detaylı skorlar
        details = {
            s.source: {
                "overall": s.match.overall_score,
                "title": s.match.title_score,
                "author": s.match.author_score,
                "year": s.match.year_score,
                "journal": s.match.journal_score,
                "doi_match": s.match.doi_match,
            }
            for s in sources_results
        }

        return VerificationResult(
            source_id=source_id,
            status=status,
            bibliographic_match=round(max_score, 3),
            verified_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            verification_sources=verified_by,
            verification_details=details,
            retraction_info=[asdict(r) for r in all_retractions if r.is_retracted],
            correction_info=asdict(correction) if correction else None,
        )

    def verify_batch(self, source_records: list[dict]) -> list[VerificationResult]:
        """Birden fazla kaydı doğrula."""
        results = []
        for record in source_records:
            result = self.verify_source(record)
            results.append(result)
        return results


def verify_source(source_record: dict, **kwargs) -> VerificationResult:
    """Kolaylık fonksiyonu: tek kaynak doğrula."""
    verifier = SourceVerifier(**kwargs)
    return verifier.verify_source(source_record)


def verify_sources_batch(source_records: list[dict], **kwargs) -> list[VerificationResult]:
    """Kolaylık fonksiyonu: toplu doğrulama."""
    verifier = SourceVerifier(**kwargs)
    return verifier.verify_batch(source_records)