"""PubMed/NCBI E-utilities istemcisi.

API: https://www.ncbi.nlm.nih.gov/books/NBK25501/
Rate limit: 3 req/s (no API key), 10 req/s (with API key)
Docs: https://www.ncbi.nlm.nih.gov/books/NBK25499/
"""
from __future__ import annotations

import time
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import quote_plus

import requests

logger = logging.getLogger(__name__)

# NCBI E-utilities base URLs
EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PUBMED_BASE = "https://pubmed.ncbi.nlm.nih.gov"


@dataclass
class PubMedArticle:
    """PubMed/MEDLINE'ten gelen bir makale kaydı."""
    pmid: str
    doi: Optional[str]
    pmcid: Optional[str]
    title: str
    authors: list[dict]
    year: Optional[int]
    journal: Optional[str]
    journal_abbrev: Optional[str]
    volume: Optional[str]
    issue: Optional[str]
    pages: Optional[str]
    publication_date: Optional[str]
    publication_types: list[str]
    mesh_terms: list[dict]
    keywords: list[str]
    abstract: Optional[str]
    affiliation: list[str]
    grant_support: list[str]
    publication_status: str  # pubmed, medline, publisher, in-process
    language: list[str]
    url: Optional[str]

    @classmethod
    def from_xml(cls, article_elem: ET.Element) -> "PubMedArticle":
        """PubMed XML'den Article oluştur."""
        # PMID
        pmid_elem = article_elem.find(".//PMID")
        pmid = pmid_elem.text if pmid_elem is not None else ""

        # DOI
        doi = None
        for id_elem in article_elem.findall(".//ArticleId"):
            if id_elem.get("IdType") == "doi":
                doi = id_elem.text
                break

        # PMCID
        pmcid = None
        for id_elem in article_elem.findall(".//ArticleId"):
            if id_elem.get("IdType") == "pmc":
                pmcid = id_elem.text
                break

        # Başlık
        title_elem = article_elem.find(".//ArticleTitle")
        title = title_elem.text if title_elem is not None else ""

        # Yazarlar
        authors = []
        for author_elem in article_elem.findall(".//Author"):
            last = author_elem.findtext("LastName", "")
            fore = author_elem.findtext("ForeName", "")
            initials = author_elem.findtext("Initials", "")
            affil = author_elem.findtext("Affiliation", "")
            orcid = ""
            for id_elem in author_elem.findall(".//Identifier"):
                if id_elem.get("Source") == "ORCID":
                    orcid = id_elem.text
                    break
            authors.append({
                "last_name": last,
                "fore_name": fore,
                "initials": initials,
                "affiliation": affil,
                "orcid": orcid,
            })

        # Dergi bilgileri
        journal_elem = article_elem.find(".//Journal")
        journal = journal_elem.findtext("Title") if journal_elem is not None else None
        journal_abbrev = journal_elem.findtext("ISOAbbreviation") if journal_elem is not None else None

        # Volume, Issue, Pages
        journal_issue = article_elem.find(".//JournalIssue")
        volume = journal_issue.findtext("Volume") if journal_issue is not None else None
        issue = journal_issue.findtext("Issue") if journal_issue is not None else None

        # Sayfa
        pages = None
        for page_elem in article_elem.findall(".//MedlinePgn"):
            pages = page_elem.text
            break

        # Yayın tarihi
        pub_date_elem = article_elem.find(".//PubDate")
        year = None
        pub_date = ""
        if pub_date_elem is not None:
            year_elem = pub_date_elem.find("Year")
            if year_elem is not None:
                year = int(year_elem.text)
            medline_date = pub_date_elem.findtext("MedlineDate")
            if medline_date:
                pub_date = medline_date
            else:
                month = pub_date_elem.findtext("Month", "")
                day = pub_date_elem.findtext("Day", "")
                parts = [year_elem.text if year_elem is not None else "", month, day]
                pub_date = " ".join(p for p in parts if p)

        # Publication types
        pub_types = [pt.text for pt in article_elem.findall(".//PublicationType") if pt.text]

        # MeSH terimleri
        mesh_terms = []
        for mesh_elem in article_elem.findall(".//MeshHeading"):
            descriptor = mesh_elem.find("DescriptorName")
            if descriptor is not None:
                mesh_terms.append({
                    "descriptor": descriptor.text,
                    "ui": descriptor.get("UI", ""),
                    "major_topic": descriptor.get("MajorTopicYN") == "Y",
                })

        # Keywords
        keywords = [kw.text for kw in article_elem.findall(".//Keyword") if kw.text]

        # Affiliation
        affiliations = []
        for affil_elem in article_elem.findall(".//Affiliation"):
            if affil_elem.text:
                affiliations.append(affil_elem.text)

        # Grant support
        grants = [g.text for g in article_elem.findall(".//Grant") if g.text]

        # Publication status
        pub_status = article_elem.findtext(".//PublicationStatus", "pubmed")

        # Language
        languages = [lang.text for lang in article_elem.findall(".//Language") if lang.text]

        # URL
        url = f"{PUBMED_BASE}/{pmid}" if pmid else None

        return cls(
            pmid=pmid,
            doi=doi,
            pmcid=pmcid,
            title=title,
            authors=authors,
            year=year,
            journal=journal,
            journal_abbrev=journal_abbrev,
            volume=volume,
            issue=issue,
            pages=pages,
            publication_date=pub_date,
            publication_types=pub_types,
            mesh_terms=mesh_terms,
            keywords=keywords,
            abstract=None,  # Abstract ayrı endpoint'ten alınır
            affiliation=affiliations,
            grant_support=grants,
            publication_status=pub_status,
            language=languages,
            url=f"{PUBMED_BASE}/{pmid}" if pmid else None,
        )

    def to_source_dict(self) -> dict:
        """source.json şemasına uygun dict'e dönüştür."""
        author_strings = []
        for a in self.authors:
            name = f"{a['last_name']}, {a['fore_name']}"
            if a.get("orcid"):
                name += f" (ORCID: {a['orcid']})"
            author_strings.append(name)

        page_list = None
        if self.pages:
            try:
                parts = self.pages.replace(" ", "").split("-")
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
            "journal": self.journal,
            "publisher": None,
            "doi": self.doi,
            "url": self.url,
            "source_type": self._map_type(),
            "publication_status": self.publication_status,
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
                "verification_sources": ["pubmed"],
            },
            "verification_notes": f"PubMed PMID: {self.pmid}",
            "supports_claims": [],
            "evidence_ids": [],
            "page_numbers": self._parse_pages(),
            "volume": self.volume,
            "issue": self.issue,
            "pages": self.pages,
            "edition": "",
            "isbn": "",
            "location_verified": True,
            "access_date": "",
            "language": self.language[0] if self.language else "en",
            "peer_reviewed": True,
        }

    def _map_type(self) -> str:
        for pt in self.publication_types:
            pt_lower = pt.lower()
            if "journal" in pt_lower and "article" in pt_lower:
                return "article"
            if "review" in pt_lower:
                return "article"
            if "clinical trial" in pt_lower:
                return "article"
            if "meta-analysis" in pt_lower:
                return "article"
            if "book" in pt_lower:
                return "book"
            if "conference" in pt_lower:
                return "conference"
        return "article"

    def _parse_pages(self) -> Optional[list[int]]:
        if not self.pages:
            return None
        try:
            parts = self.pages.replace(" ", "").split("-")
            start = int(parts[0])
            end = int(parts[1]) if len(parts) > 1 else start
            return list(range(start, end + 1))
        except (ValueError, IndexError):
            return None


class PubMedClient:
    """NCBI E-utilities istemcisi."""

    EUTILS_BASE = EUTILS_BASE
    DEFAULT_HEADERS = {
        "User-Agent": "AcademicThesisWriter/1.0",
        "Accept": "application/xml",
    }

    def __init__(
        self,
        api_key: str | None = None,
        email: str | None = None,
        tool: str = "AcademicThesisWriter",
        timeout: int = 30,
        rate_limit: float = 3.0,  # req/s (no API key)
    ):
        self.api_key = api_key
        self.email = email
        self.tool = tool
        self.timeout = timeout
        self.rate_limit = rate_limit  # req per second
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        base_params = {"tool": tool}
        if email:
            base_params["email"] = email
        if api_key:
            base_params["api_key"] = api_key
        self.session.params = base_params
        self._last_request = 0.0

    def _throttle(self):
        elapsed = time.time() - self._last_request
        min_interval = 1.0 / self.rate_limit
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

    def _get(self, path: str, params: dict | None = None) -> str:
        self._throttle()
        url = f"{self.EUTILS_BASE}{path}"
        logger.debug(f"GET {url} params={params}")
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        self._last_request = time.time()
        return response.text

    def _post(self, path: str, data: dict) -> str:
        self._throttle()
        url = f"{self.EUTILS_BASE}{path}"
        logger.debug(f"POST {url} data={data}")
        response = self.session.post(url, data=data, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def search(
        self,
        query: str,
        db: str = "pubmed",
        retmax: int = 100,
        retstart: int = 0,
        sort: str = "relevance",
        datetype: str = "pdat",
        mindate: str | None = None,
        maxdate: str | None = None,
        mindate_year: int | None = None,
        maxdate_year: int | None = None,
    ) -> dict:
        """E-search: ID listesi getir."""
        params = {
            "db": db,
            "term": query,
            "retmax": min(retmax, 10000),
            "retstart": retstart,
            "sort": sort,
            "datetype": datetype,
            "retmode": "json",
        }
        if mindate:
            params["mindate"] = mindate
        if maxdate:
            params["maxdate"] = maxdate
        if mindate_year:
            params["mindate"] = f"{mindate_year}/01/01"
        if maxdate_year:
            params["maxdate"] = f"{maxdate_year}/12/31"

        xml_text = self._get("/esearch.fcgi", params)
        return self._parse_esearch(xml_text)

    def _parse_esearch(self, xml_text: str) -> dict:
        root = ET.fromstring(xml_text)
        id_list = [id_elem.text for id_elem in root.findall(".//Id")]
        count = int(root.findtext(".//Count", "0"))
        return {"ids": id_list, "count": count}

    def fetch(
        self,
        ids: list[str],
        db: str = "pubmed",
        rettype: str = "xml",
        retmode: str = "xml",
    ) -> list[PubMedArticle]:
        """E-fetch: ID listesiyle tam kayıtları getir."""
        if not ids:
            return []

        # E-fetch max 200 ID per request (POST önerilir)
        all_articles = []
        for i in range(0, len(ids), 200):
            chunk = ids[i:i+200]
            id_string = ",".join(chunk)
            xml_text = self._post(
                "/efetch.fcgi",
                {
                    "db": db,
                    "id": id_string,
                    "rettype": rettype,
                    "retmode": retmode,
                }
            )
            articles = self._parse_efetch(xml_text)
            all_articles.extend(articles)
        return all_articles

    def _parse_efetch(self, xml_text: str) -> list[PubMedArticle]:
        root = ET.fromstring(xml_text)
        articles = []
        for article_elem in root.findall(".//PubmedArticle"):
            try:
                articles.append(PubMedArticle.from_xml(article_elem))
            except Exception as e:
                logger.warning(f"Article parse error: {e}")
        return articles

    def fetch_abstracts(self, ids: list[str]) -> dict[str, str]:
        """E-fetch ile sadece abstract'ları getir (text formatında)."""
        if not ids:
            return {}
        id_string = ",".join(ids[:200])
        text = self._post(
            "/efetch.fcgi",
            {
                "db": "pubmed",
                "id": id_string,
                "rettype": "abstract",
                "retmode": "text",
            }
        )
        # Abstract metnini parse et (basit)
        abstracts = {}
        current_pmid = None
        current_abstract = []
        for line in text.split("\n"):
            if line.startswith("PMID:"):
                if current_pmid and current_abstract:
                    abstracts[current_pmid] = "\n".join(current_abstract).strip()
                current_pmid = line.split(":")[1].strip()
                current_abstract = []
            elif line.startswith("ABSTRACT:"):
                current_abstract.append(line[9:])
            elif line.startswith("      "):  # continuation
                current_abstract.append(line.strip())
        if current_pmid and current_abstract:
            abstracts[current_pmid] = "\n".join(current_abstract).strip()
        return abstracts

    def search_and_fetch(
        self,
        query: str,
        max_results: int = 100,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> list[PubMedArticle]:
        """Arama yap ve sonuçları fetch et."""
        search_result = self.search(
            query=query,
            retmax=max_results,
            mindate_year=year_from,
            maxdate_year=year_to,
        )
        ids = search_result["ids"]
        if not ids:
            return []
        articles = self.fetch(ids)
        # Abstract'ları da çek
        abstracts = self.fetch_abstracts(ids)
        for article in articles:
            article.abstract = abstracts.get(article.pmid, "")
        return articles

    def get_citations(self, pmid: str) -> list[str]:
        """PMID ile atıf yapan makaleleri getir (E-link)."""
        xml_text = self._get("/elink.fcgi", {
            "dbfrom": "pubmed",
            "db": "pubmed",
            "id": pmid,
            "linkname": "pubmed_pubmed_citedin",
        })
        root = ET.fromstring(xml_text)
        return [id_elem.text for id_elem in root.findall(".//Id")]

    def get_references(self, pmid: str) -> list[str]:
        """PMID ile referans veren makaleleri getir (E-link)."""
        xml_text = self._get("/elink.fcgi", {
            "dbfrom": "pubmed",
            "db": "pubmed",
            "id": pmid,
            "linkname": "pubmed_pubmed_refs",
        })
        root = ET.fromstring(xml_text)
        return [id_elem.text for id_elem in root.findall(".//Id")]

    def get_similar(self, pmid: str) -> list[str]:
        """Benzer makaleleri getir (E-link)."""
        xml_text = self._get("/elink.fcgi", {
            "dbfrom": "pubmed",
            "db": "pubmed",
            "id": pmid,
            "linkname": "pubmed_pubmed",
        })
        root = ET.fromstring(xml_text)
        return [id_elem.text for id_elem in root.findall(".//Id")]


def search_pubmed(
    query: str,
    max_results: int = 100,
    year_from: int | None = None,
    year_to: int | None = None,
    email: str | None = None,
    api_key: str | None = None,
) -> list[PubMedArticle]:
    """PubMed'de arama yap ve PubMedArticle listesi döndür."""
    client = PubMedClient(email=email, api_key=email)
    return client.search_and_fetch(
        query=query,
        max_results=max_results,
        year_from=year_from,
        year_to=year_to,
    )