"""Crossref REST API istemcisi.

API: https://api.crossref.org/
Rate limit: 50 req/s (polite pool, mailto ile)
Docs: https://github.com/CrossRef/rest-api-doc
"""
from __future__ import annotations

import time
import logging
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import quote_plus

import requests

logger = logging.getLogger(__name__)


@dataclass
class CrossrefWork:
    """Crossref'ten gelen bir çalışma (work) kaydı."""
    doi: str
    title: str
    authors: list[dict]
    year: Optional[int]
    journal: Optional[str]
    publisher: Optional[str]
    issn: list[str]
    url: Optional[str]
    type: str  # journal-article, book-chapter, proceedings-article, etc.
    license: list[dict]
    references_count: int
    is_referenced_by_count: int
    abstract: Optional[str]
    funded_by: list[dict]
    created: dict  # {date-parts: [[year, month, day]]}
    indexed: dict
    relation: dict  # has-preprint, has-preprint, is-preprint-of, etc.
    container_title: list[str]
    volume: Optional[str]
    issue: Optional[str]
    page: Optional[str]
    subject: list[str]
    orcid: list[str]
    funder: list[dict]
    award: list[dict]
    clinical_trial_number: list[str]

    @classmethod
    def from_api(cls, item: dict) -> "CrossrefWork":
        """Crossref API yanıtından CrossrefWork oluştur."""
        # Yazarları normalize et
        authors = []
        for a in item.get("author", []):
            authors.append({
                "given": a.get("given", ""),
                "family": a.get("family", ""),
                "orcid": a.get("ORCID", "").replace("https://orcid.org/", "") if a.get("ORCID") else "",
                "affiliation": [aff.get("name", "") for aff in a.get("affiliation", [])],
            })

        # ISSN'leri topla
        issn = item.get("ISSN", []) or []
        if isinstance(issn, str):
            issn = [issn]

        # Subject alanları
        subjects = item.get("subject", []) or []

        # ORCID'leri topla (author'dan ayrı olarak work-level'da da olabilir)
        orcids = []
        for a in item.get("author", []):
            if a.get("ORCID"):
                orcids.append(a["ORCID"].replace("https://orcid.org/", ""))

        # Funded-by
        funded_by = item.get("funder", []) or []

        # Clinical trial numbers
        clinical_trials = item.get("clinical-trial-number", []) or []

        return cls(
            doi=item.get("DOI", ""),
            title=item.get("title", [""])[0] if item.get("title") else "",
            authors=authors,
            year=item.get("published-print", {}).get("date-parts", [[None]])[0][0]
                 or item.get("published-online", {}).get("date-parts", [[None]])[0][0]
                 or item.get("created", {}).get("date-parts", [[None]])[0][0],
            journal=item.get("container-title", [""])[0] if item.get("container-title") else None,
            publisher=item.get("publisher"),
            issn=issn,
            url=item.get("URL"),
            type=item.get("type", ""),
            license=item.get("license", []) or [],
            references_count=item.get("references-count", 0),
            is_referenced_by_count=item.get("is-referenced-by-count", 0),
            abstract=item.get("abstract"),
            funded_by=funded_by,
            created=item.get("created", {}),
            indexed=item.get("indexed", {}),
            relation=item.get("relation", {}) or {},
            container_title=item.get("container-title", []) or [],
            volume=item.get("volume"),
            issue=item.get("issue"),
            page=item.get("page"),
            subject=subjects,
            orcid=orcids,
            funder=funded_by,
            award=item.get("award", []) or [],
            clinical_trial_number=clinical_trials,
        )

    def to_source_dict(self) -> dict:
        """source.json şemasına uygun dict'e dönüştür."""
        # Yazar string'lerini oluştur
        author_strings = []
        for a in self.authors:
            name = f"{a['family']}, {a['given']}" if a['family'] else a['given']
            if a.get('orcid'):
                name += f" (ORCID: {a['orcid']})"
            author_strings.append(name)

        # Yıl
        year = self.year

        # Dergi adı
        journal = self.journal or (self.container_title[0] if self.container_title else None)

        return {
            "id": "",  # SRC-XXX formatında atanacak
            "title": self.title,
            "authors": author_strings,
            "year": year,
            "journal": journal,
            "publisher": self.publisher,
            "doi": self.doi,
            "url": self.url,
            "source_type": self._map_type(),
            "publication_status": "published",
            "retraction_status": self._check_retraction(),
            "correction_status": "none",
            "supersedes_source_id": None,
            "verified": False,
            "verification": {
                "status": "pending",
                "bibliographic_match": 0.0,
                "doi_match": True,
                "author_match": None,
                "title_match": None,
                "year_match": None,
                "journal_match": None,
                "verified_at": "",
                "verification_sources": ["crossref"],
            },
            "verification_notes": f"Crossref metadata: {self.doi}",
            "supports_claims": [],
            "evidence_ids": [],
            "page_numbers": self._parse_pages(),
            "volume": self.volume,
            "issue": self.issue,
            "pages": self.page,
            "edition": "",
            "isbn": "",
            "location_verified": True,
            "access_date": "",
            "language": "en",
            "peer_reviewed": self.type in ("journal-article", "proceedings-article"),
        }

    def _map_type(self) -> str:
        """Crossref type -> source_type enum."""
        mapping = {
            "journal-article": "article",
            "book-chapter": "book_chapter",
            "book": "book",
            "proceedings-article": "conference",
            "proceedings": "conference",
            "report": "report",
            "dataset": "dataset",
            "standard": "other",
            "reference-book": "book",
            "edited-book": "book",
            "monograph": "book",
            "dissertation": "thesis",
            "peer-review": "article",
            "posted-content": "preprint",
        }
        return mapping.get(self.type, "other")

    def _check_retraction(self) -> str:
        """Retraction durumunu kontrol et."""
        # Crossref relation'da 'is-retracted-by' veya 'retracts' varsa
        rel = self.relation or {}
        if "is-retracted-by" in rel or "retracts" in rel:
            return "retracted"
        # type: retracted
        if self.type == "retracted":
            return "retracted"
        return "not_retracted"

    def _parse_pages(self) -> list[int] | None:
        """Sayfa aralığını parse et."""
        if not self.page:
            return None
        # "123-145" veya "123" formatı
        try:
            parts = self.page.split("-")
            start = int(parts[0])
            end = int(parts[1]) if len(parts) > 1 else start
            return list(range(start, end + 1))
        except (ValueError, IndexError):
            return None


class CrossrefClient:
    """Crossref REST API istemcisi."""

    BASE_URL = "https://api.crossref.org"
    DEFAULT_HEADERS = {
        "User-Agent": "AcademicThesisWriter/1.0 (mailto:research@example.com)",
        "Accept": "application/json",
    }

    def __init__(
        self,
        mailto: str = "research@example.com",
        rate_limit: float = 50.0,  # req/s
        timeout: int = 30,
    ):
        self.mailto = mailto
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        self.session.params = {"mailto": mailto}
        self._last_request = 0.0

    def _throttle(self):
        """Rate limiting."""
        elapsed = time.time() - self._last_request
        min_interval = 1.0 / self.rate_limit
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

    def _get(self, path: str, params: dict | None = None) -> dict:
        """GET isteği yap."""
        self._throttle()
        url = f"{self.BASE_URL}{path}"
        logger.debug(f"GET {url} params={params}")
        response = self.session.get(url, params=params, timeout=self.timeout)
        self._last_request = time.time()
        response.raise_for_status()
        return response.json()

    def works(
        self,
        query: str | None = None,
        filter: dict | None = None,
        rows: int = 20,
        offset: int = 0,
        sort: str = "relevance",
        order: str = "desc",
        select: list[str] | None = None,
    ) -> dict:
        """Works endpoint'ini sorgula.

        Args:
            query: Arama sorgusu (title, author, keyword vb.)
            filter: Filtreler (örn: {"type": "journal-article", "from-pub-date": "2020-01-01"})
            rows: Sayfa başına sonuç sayısı (max 1000)
            offset: Offset
            sort: Sıralama alanı (relevance, score, published, updated, deposited, index)
            order: asc/desc
            select: Dönüş alanları (örn: ["DOI", "title", "author"])
        """
        params = {
            "rows": min(rows, 1000),
            "offset": offset,
            "sort": sort,
            "order": order,
        }
        if query:
            params["query"] = query
        if filter:
            # Crossref filter formatı: key:value,key:value
            filter_str = ",".join(f"{k}:{v}" for k, v in filter.items())
            params["filter"] = filter_str
        if select:
            params["select"] = ",".join(select)

        data = self._get("/works", params)
        return data["message"]

    def work_by_doi(self, doi: str) -> CrossrefWork:
        """DOI ile tek bir work getir."""
        data = self._get(f"/works/{quote_plus(doi)}")
        return CrossrefWork.from_api(data["message"])

    def works_by_dois(self, dois: list[str]) -> list[CrossrefWork]:
        """Birden fazla DOI için batch sorgulama (filter=doi:...)."""
        # Crossref filter=doi:doi1,doi2,... destekler (max ~100 DOI)
        chunks = [dois[i:i+50] for i in range(0, len(dois), 50)]
        works = []
        for chunk in chunks:
            filter_dict = {"doi": ",".join(chunk)}
            data = self.works(filter=filter_dict, rows=len(chunk))
            for item in data["items"]:
                works.append(CrossrefWork.from_api(item))
        return works

    def journals(self, query: str | None = None, rows: int = 20) -> dict:
        """Journals endpoint."""
        params = {"rows": rows}
        if query:
            params["query"] = query
        data = self._get("/journals", params)
        return data["message"]

    def prefixes(self, prefix: str | None = None, rows: int = 20) -> dict:
        """Prefixes endpoint."""
        path = f"/prefixes/{prefix}" if prefix else "/prefixes"
        data = self._get(path, {"rows": rows})
        return data["message"]

    def funders(self, query: str | None = None, rows: int = 20) -> dict:
        """Funders endpoint."""
        params = {"rows": rows}
        if query:
            params["query"] = query
        data = self._get("/funders", params)
        return data["message"]


def search_crossref(
    query: str,
    databases: list[str] | None = None,
    max_results: int = 100,
    year_from: int | None = None,
    year_to: int | None = None,
    article_types: list[str] | None = None,
    mailto: str = "research@example.com",
) -> list[CrossrefWork]:
    """Crossref'te arama yap ve CrossrefWork listesi döndür.

    Kolaylık fonksiyonu: CLI ve üst seviye modüller için.
    """
    client = CrossrefClient(mailto=mailto)

    filter_dict = {}
    if year_from:
        filter_dict["from-pub-date"] = f"{year_from}-01-01"
    if year_to:
        filter_dict["until-pub-date"] = f"{year_to}-12-31"
    if article_types:
        filter_dict["type"] = ",".join(article_types)

    all_works = []
    rows = min(1000, max_results)
    offset = 0

    while len(all_works) < max_results:
        data = client.works(
            query=query,
            filter=filter_dict or None,
            rows=rows,
            offset=offset,
        )
        items = data.get("items", [])
        if not items:
            break

        for item in items:
            all_works.append(CrossrefWork.from_api(item))
            if len(all_works) >= max_results:
                break

        offset += len(items)
        if len(items) < rows:
            break

    return all_works[:max_results]