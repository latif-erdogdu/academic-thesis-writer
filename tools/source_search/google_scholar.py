"""Google Scholar arama istemcisi.

Not: Google Scholar'ın resmi API'si yoktur.
Seçenekler:
1. SerpAPI (ücretli, güvenilir) - ÖNERİLEN
2. scholarly kütüphanesi (ücretsiz, kırılgan)
3. Manuel scraping (yasal risk, önerilmez)

Bu modül SerpAPI'yi birincil, scholarly'yi yedek olarak kullanır.
"""
from __future__ import annotations

import time
import logging
import os
from dataclasses import dataclass
from typing import Any, Optional

try:
    import requests
except ImportError:
    requests = None

try:
    from scholarly import scholarly
except ImportError:
    scholarly = None

logger = logging.getLogger(__name__)


@dataclass
class GoogleScholarResult:
    """Google Scholar arama sonucu."""
    title: str
    authors: list[str]
    year: Optional[int] = None
    venue: Optional[str] = None
    citations: int = 0
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    snippet: Optional[str] = None
    cited_by_url: Optional[str] = None
    related_articles_url: Optional[str] = None

    def to_source_dict(self) -> dict:
        """source.json şemasına uygun dict'e dönüştür."""
        return {
            "id": "",
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "journal": self.venue,
            "publisher": None,
            "doi": None,
            "url": self.url,
            "source_type": "article",
            "publication_status": "published",
            "retraction_status": "not_retracted",
            "correction_status": "none",
            "supersedes_source_id": None,
            "verified": False,
            "verification": {
                "status": "pending",
                "bibliographic_match": 0.0,
                "doi_match": False,
                "author_match": None,
                "title_match": None,
                "year_match": None,
                "journal_match": None,
                "verified_at": "",
                "verification_sources": ["google_scholar"],
            },
            "verification_notes": "Google Scholar result (unverified)",
            "supports_claims": [],
            "evidence_ids": [],
            "page_numbers": None,
            "volume": None,
            "issue": None,
            "pages": None,
            "edition": "",
            "isbn": "",
            "location_verified": False,
            "access_date": "",
            "language": "en",
            "peer_reviewed": True,
        }


class SerpAPIClient:
    """SerpAPI Google Scholar Search API istemcisi.

    API: https://serpapi.com/google-scholar-api
    Ücretli: ~$50/ay (1000 search)
    """

    BASE_URL = "https://serpapi.com/search"
    DEFAULT_HEADERS = {
        "Accept": "application/json",
    }

    def __init__(
        self,
        api_key: str | None = None,
        timeout: int = 30,
    ):
        self.api_key = api_key or os.getenv("SERPAPI_KEY")
        self.timeout = timeout
        self.session = requests.Session() if requests else None
        self.session.headers.update({"Accept": "application/json"})

    def search(
        self,
        query: str,
        num: int = 20,
        start: int = 0,
        as_ylo: int | None = None,
        as_yhi: int | None = None,
        as_sdt: str = "0,5",  # 0: articles, 5: include patents
        hl: str = "en",
    ) -> dict:
        """SerpAPI Google Scholar araması."""
        if not self.api_key:
            raise ValueError("SerpAPI key gerekli (SERPAPI_KEY env var)")

        params = {
            "engine": "google_scholar",
            "q": query,
            "api_key": self.api_key,
            "num": min(num, 100),
            "start": start,
            "as_sdt": as_sdt,
            "hl": hl,
        }
        if as_ylo:
            params["as_ylo"] = str(as_ylo)
        if as_yhi:
            params["as_yhi"] = str(as_yhi)

        response = self.session.get(self.BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def parse_results(self, data: dict) -> list[GoogleScholarResult]:
        """SerpAPI yanıtını GoogleScholarResult listesine dönüştür."""
        results = []
        for item in data.get("organic_results", []):
            # Yazarları parse et
            authors = []
            pub_info = item.get("publication_info", {})
            if "authors" in pub_info:
                for a in pub_info["authors"]:
                    authors.append(a.get("name", ""))

            # Yıl
            year = None
            if "year" in item:
                try:
                    year = int(item["year"])
                except (ValueError, TypeError):
                    pass

            # Atıf sayısı
            citations = 0
            cited_by = item.get("cited_by", {})
            if "value" in cited_by:
                try:
                    citations = int(cited_by["value"])
                except (ValueError, TypeError):
                    pass

            results.append(GoogleScholarResult(
                title=item.get("title", ""),
                authors=authors,
                year=year,
                venue=item.get("publication_info", {}).get("summary", ""),
                citations=citations,
                url=item.get("link"),
                pdf_url=item.get("resources", [{}])[0].get("link") if item.get("resources") else None,
                snippet=item.get("snippet"),
                cited_by_url=cited_by.get("link") if isinstance(cited_by, dict) else None,
                related_articles_url=item.get("related_articles_link"),
            ))
        return results


class ScholarlyClient:
    """scholarly kütüphanesi wrapper (ücretsiz, kırılgan).

    pip install scholarly
    """

    def __init__(self, timeout: int = 30):
        if not scholarly:
            raise ImportError("scholarly kütüphanesi gerekli: pip install scholarly")
        self.scholarly = scholarly
        self.timeout = timeout

    def search(
        self,
        query: str,
        max_results: int = 20,
    ) -> list[GoogleScholarResult]:
        """Google Scholar'da arama yap."""
        results = []
        try:
            search_query = self.scholarly.search_pubs(query)
            for i, pub in enumerate(search_query):
                if i >= max_results:
                    break
                try:
                    # Publication detaylarını çek
                    filled = self.scholarly.fill(pub)
                    results.append(GoogleScholarResult(
                        title=filled.get("bib", {}).get("title", ""),
                        authors=filled.get("bib", {}).get("author", "").split(" and "),
                        year=int(filled.get("bib", {}).get("pub_year", 0)) or None,
                        venue=filled.get("bib", {}).get("venue", ""),
                        citations=filled.get("num_citations", 0),
                        url=filled.get("pub_url") or filled.get("eprint_url"),
                        pdf_url=filled.get("eprint_url"),
                        snippet=filled.get("bib", {}).get("abstract", "")[:200] if filled.get("bib", {}).get("abstract") else None,
                        cited_by_url=filled.get("citedby_url"),
                        related_articles_url=filled.get("related_articles_url"),
                    ))
                except Exception as e:
                    logger.warning(f"Failed to fill publication: {e}")
                    continue
        except Exception as e:
            logger.error(f"Scholarly search failed: {e}")
        return results


def search_google_scholar(
    query: str,
    max_results: int = 20,
    api_key: str | None = None,
    use_serpapi: bool = True,
) -> list[GoogleScholarResult]:
    """Google Scholar'da arama yap (SerpAPI veya scholarly)."""
    if use_serpapi:
        if not api_key and not os.getenv("SERPAPI_KEY"):
            logger.warning("SerpAPI key yok, scholarly'ye fallback")
            use_serpapi = False

    if use_serpapi:
        client = SerpAPIClient(api_key=api_key)
        data = client.search(query, num=min(max_results, 100))
        return client.parse_results(data)
    else:
        if not scholarly:
            raise ImportError("Neither SerpAPI nor scholarly available")
        client = ScholarlyClient()
        return client.search(query, max_results=max_results)


# Backward compatibility
def search_google_scholar_legacy(
    query: str,
    max_results: int = 20,
) -> list[dict]:
    """Legacy fonksiyon - dict listesi döndürür."""
    results = search_google_scholar(query, max_results)
    return [r.to_source_dict() for r in results]