"""Semantic Scholar API istemcisi.

API: https://api.semanticscholar.org/
Rate limit: 100 req/5min (with API key), 10 req/min (without)
Docs: https://api.semanticscholar.org/api-docs/
"""
from __future__ import annotations

import time
import logging
from dataclasses import dataclass
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class SemanticScholarPaper:
    """Semantic Scholar'ten gelen bir makale kaydı."""
    paper_id: str  # S2PaperId veya CorpusId
    doi: Optional[str]
    title: str
    authors: list[dict]
    year: Optional[int]
    venue: Optional[str]
    journal: Optional[str]
    volume: Optional[str]
    issue: Optional[str]
    pages: Optional[str]
    citation_count: int
    influential_citation_count: int
    is_open_access: bool
    open_access_pdf: Optional[dict]
    abstract: Optional[str]
    fields_of_study: list[str]
    publication_types: list[str]
    publication_date: Optional[str]
    citation_styles: dict
    references: list[dict]
    citations: list[dict]
    embedding: Optional[dict]
    tldr: Optional[dict]

    @classmethod
    def from_api(cls, item: dict) -> "SemanticScholarPaper":
        """Semantic Scholar API yanıtından Paper oluştur."""
        # Yazarları normalize et
        authors = []
        for a in item.get("authors", []):
            authors.append({
                "author_id": a.get("authorId"),
                "name": a.get("name", ""),
                "affiliations": a.get("affiliations", []) or [],
            })

        # Open Access PDF
        oa_pdf = item.get("openAccessPdf")
        if oa_pdf:
            oa_pdf = {
                "url": oa_pdf.get("url"),
                "status": oa_pdf.get("status"),
            }

        # Citation styles
        citation_styles = item.get("citationStyles", {}) or {}

        # Referanslar ve atıflar
        references = item.get("references", []) or []
        citations = item.get("citations", []) or []

        return cls(
            paper_id=item.get("paperId", "") or str(item.get("corpusId", "")),
            doi=item.get("doi"),
            title=item.get("title", ""),
            authors=authors,
            year=item.get("year"),
            venue=item.get("venue"),
            journal=item.get("journal", {}).get("name") if item.get("journal") else None,
            volume=item.get("journal", {}).get("volume") if item.get("journal") else None,
            issue=item.get("journal", {}).get("issue") if item.get("journal") else None,
            pages=item.get("pages"),
            citation_count=item.get("citationCount", 0),
            influential_citation_count=item.get("influentialCitationCount", 0),
            is_open_access=item.get("isOpenAccess", False),
            open_access_pdf=oa_pdf,
            abstract=item.get("abstract"),
            fields_of_study=item.get("fieldsOfStudy", []) or [],
            publication_types=item.get("publicationTypes", []) or [],
            publication_date=item.get("publicationDate"),
            citation_styles=citation_styles,
            references=references,
            citations=citations,
            embedding=item.get("embedding"),
            tldr=item.get("tldr"),
        )

    def to_source_dict(self) -> dict:
        """source.json şemasına uygun dict'e dönüştür."""
        author_strings = []
        for a in self.authors:
            name = a.get("name", "")
            if a.get("author_id"):
                name += f" (S2AuthorId: {a['author_id']})"
            author_strings.append(name)

        page_list = None
        if self.pages:
            try:
                parts = self.pages.split("-")
                start = int(parts[0])
                end = int(parts[1]) if len(parts) > 1 else start
                page_list = list(range(start, end + 1))
            except (ValueError, IndexError):
                pass

        return {
            "id": "",
            "title": self.title,
            "authors": author_strings,
            "year": self.year,
            "journal": self.journal or self.venue,
            "publisher": None,
            "doi": self.doi,
            "url": f"https://www.semanticscholar.org/paper/{self.paper_id}" if self.paper_id else None,
            "source_type": self._map_type(),
            "publication_status": "published",
            "retraction_status": "not_retracted",
            "correction_status": "none",
            "supersedes_source_id": None,
            "verified": False,
            "verification": {
                "status": "pending",
                "bibliographic_match": 0.0,
                "doi_match": bool(self.doi),
                "author_match": None,
                "title_match": None,
                "year_match": None,
                "journal_match": None,
                "verified_at": "",
                "verification_sources": ["semantic_scholar"],
            },
            "verification_notes": f"Semantic Scholar metadata: {self.paper_id}",
            "supports_claims": [],
            "evidence_ids": [],
            "page_numbers": page_list,
            "volume": self.volume,
            "issue": self.issue,
            "pages": self.pages,
            "edition": "",
            "isbn": "",
            "location_verified": True,
            "access_date": "",
            "language": "en",
            "peer_reviewed": True,
        }

    def _map_type(self) -> str:
        if self.publication_types:
            pt = self.publication_types[0].lower()
            if "journal" in pt:
                return "article"
            if "conference" in pt or "proceedings" in pt:
                return "conference"
            if "preprint" in pt or "arxiv" in pt:
                return "preprint"
            if "book" in pt:
                return "book"
            if "report" in pt:
                return "report"
        return "article"


class SemanticScholarClient:
    """Semantic Scholar API istemcisi."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    DEFAULT_HEADERS = {
        "Accept": "application/json",
    }

    def __init__(
        self,
        api_key: str | None = None,
        timeout: int = 30,
        rate_limit: float = 20.0,  # req/min (with API key)
    ):
        self.api_key = api_key
        self.timeout = timeout
        self.rate_limit = rate_limit  # req per minute
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        if api_key:
            self.session.headers["x-api-key"] = api_key
        self._last_request = 0.0

    def _throttle(self):
        elapsed = time.time() - self._last_request
        min_interval = 60.0 / self.rate_limit  # seconds per request
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

    def _get(self, path: str, params: dict | None = None) -> dict:
        self._throttle()
        url = f"{self.BASE_URL}{path}"
        logger.debug(f"GET {url} params={params}")
        response = self.session.get(url, params=params, timeout=self.timeout)
        self._last_request = time.time()
        if response.status_code == 429:
            # Rate limited - wait and retry once
            wait = int(response.headers.get("Retry-After", "60"))
            logger.warning(f"Rate limited, waiting {wait}s")
            time.sleep(wait)
            response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def paper(
        self,
        paper_id: str,
        fields: list[str] | None = None,
    ) -> SemanticScholarPaper:
        """Tek bir paper getir.

        paper_id: S2PaperId (örn: 649def34f8be52c8b66281af98ae884c09aef38b)
                 veya CorpusId (örn: 2030103)
                 veya DOI (örn: 10.1038/nature12373)
                 veya ArXiv ID (örn: 1706.03762)
        """
        default_fields = [
            "paperId", "corpusId", "doi", "title", "authors", "year",
            "venue", "journal", "volume", "issue", "pages",
            "citationCount", "influentialCitationCount",
            "isOpenAccess", "openAccessPdf", "abstract",
            "fieldsOfStudy", "publicationTypes", "publicationDate",
            "citationStyles", "references", "citations",
            "embedding", "tldr",
        ]
        fields_str = ",".join(fields or default_fields)
        data = self._get(f"/paper/{paper_id}", {"fields": fields_str})
        return SemanticScholarPaper.from_api(data)

    def paper_batch(
        self,
        paper_ids: list[str],
        fields: list[str] | None = None,
    ) -> list[SemanticScholarPaper]:
        """Birden fazla paper getir (POST /paper/batch)."""
        default_fields = [
            "paperId", "doi", "title", "authors", "year",
            "venue", "journal", "volume", "issue", "pages",
            "citationCount", "influentialCitationCount",
            "isOpenAccess", "openAccessPdf", "abstract",
        ]
        fields_str = ",".join(fields or default_fields)
        data = self.session.post(
            f"{self.BASE_URL}/paper/batch",
            params={"fields": fields_str},
            json={"ids": paper_ids},
            timeout=self.timeout,
        )
        data.raise_for_status()
        results = data.json()
        return [SemanticScholarPaper.from_api(item) for item in results if item]

    def search(
        self,
        query: str,
        limit: int = 100,
        offset: int = 0,
        fields: list[str] | None = None,
        year: str | None = None,
        publication_types: list[str] | None = None,
        open_access_pdf: bool | None = None,
        venue: list[str] | None = None,
        fields_of_study: list[str] | None = None,
    ) -> dict:
        """Semantic Scholar'da arama yap.

        Returns: {"total": int, "data": [paper, ...], "next": offset}
        """
        params = {
            "query": query,
            "limit": min(limit, 100),
            "offset": offset,
        }
        if fields:
            params["fields"] = ",".join(fields)
        else:
            params["fields"] = ",".join([
                "paperId", "doi", "title", "authors", "year",
                "venue", "journal", "volume", "issue", "pages",
                "citationCount", "influentialCitationCount",
                "isOpenAccess", "openAccessPdf", "abstract",
            ])
        if year:
            params["year"] = year
        if publication_types:
            params["publicationTypes"] = ",".join(publication_types)
        if open_access_pdf is not None:
            params["openAccessPdf"] = str(open_access_pdf).lower()
        if venue:
            params["venue"] = ",".join(venue)
        if fields_of_study:
            params["fieldsOfStudy"] = ",".join(fields_of_study)

        data = self._get("/paper/search", params)
        return data

    def get_references(self, paper_id: str, limit: int = 1000) -> list[dict]:
        """Bir paper'ın referanslarını getir."""
        data = self._get(f"/paper/{paper_id}/references", {"limit": limit})
        return data.get("data", [])

    def get_citations(self, paper_id: str, limit: int = 1000) -> list[dict]:
        """Bir paper'ı atıflayan makaleleri getir."""
        data = self._get(f"/paper/{paper_id}/citations", {"limit": limit})
        return data.get("data", [])


def search_semantic_scholar(
    query: str,
    max_results: int = 100,
    year_from: int | None = None,
    year_to: int | None = None,
    api_key: str | None = None,
) -> list[dict]:
    """Semantic Scholar'da arama yap ve basit dict listesi döndür."""
    client = SemanticScholarClient(api_key=api_key)

    year_filter = None
    if year_from or year_to:
        yf = year_from or 1900
        yt = year_to or 2099
        year_filter = f"{yf}:{yt}"

    all_results = []
    limit = 100
    offset = 0

    while len(all_results) < max_results:
        data = client.search(
            query=query,
            limit=min(100, max_results - len(all_results)),
            offset=len(all_results),
            year=f"{year_from}-{year_to}" if year_from or year_to else None,
        )
        papers = data.get("data", [])
        if not papers:
            break
        all_results.extend(papers)
        if len(papers) < 100:
            break

    return all_results[:max_results]