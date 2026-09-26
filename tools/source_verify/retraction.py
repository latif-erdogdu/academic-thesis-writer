"""Retraksiyon ve düzeltme durumu kontrolü.

Crossref, OpenAlex, PubMed, Retraction Watch veritabanlarını kullanarak
kaynakların retraksiyon/korizyon durumunu kontrol eder.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class RetractionInfo:
    """Retraksiyon bilgisi."""
    is_retracted: bool
    retraction_type: str  # "retracted", "expression_of_concern", "correction", "erratum", "withdrawn"
    reason: str = ""
    retraction_date: str = ""
    retraction_doi: str = ""
    original_doi: str = ""
    notice_doi: str = ""
    source: str = ""  # "crossref", "openalex", "pubmed", "retraction_watch"


@dataclass
class CorrectionInfo:
    """Düzeltme bilgisi."""
    is_corrected: bool
    correction_type: str  # "correction", "erratum", "retraction_and_republication"
    correction_doi: str = ""
    correction_date: str = ""
    details: str = ""
    source: str = ""


# Crossref relation tipleri
CROSSREF_RETRACTION_RELATIONS = {
    "is-retracted-by": "retracted",
    "retracts": "retracted",
    "has-expression-of-concern": "expression_of_concern",
    "has-correction": "correction",
    "has-erratum": "erratum",
    "has-retraction": "retracted",
    "is-withdrawn-by": "withdrawn",
}


def check_crossref_retraction(doi: str, session: requests.Session | None = None) -> Optional[RetractionInfo]:
    """Crossref'ten retraksiyon durumu kontrol et."""
    if not doi:
        return None

    sess = session or requests.Session()
    sess.headers.update({"User-Agent": "AcademicThesisWriter/1.0"})

    try:
        # Works endpoint ile relation bilgilerini al
        url = f"https://api.crossref.org/works/{doi}"
        resp = sess.get(url, timeout=30)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        item = data.get("message", {})

        # Relation alanını kontrol et
        relations = item.get("relation", {}) or {}
        for rel_type, rel_items in relations.items():
            if rel_type in CROSSREF_RETRACTION_RELATIONS:
                for rel in rel_items:
                    rel_doi = rel.get("id", "").replace("https://doi.org/", "")
                    return RetractionInfo(
                        is_retracted=True,
                        retraction_type=CROSSREF_RETRACTION_RELATIONS[rel_type],
                        reason=f"Crossref relation: {rel_type}",
                        retraction_doi=rel_doi,
                        original_doi=doi,
                        source="crossref",
                    )

        # Type kontrolü
        work_type = item.get("type", "")
        if work_type == "retracted":
            return RetractionInfo(
                is_retracted=True,
                retraction_type="retracted",
                reason="Crossref work type: retracted",
                original_doi=doi,
                source="crossref",
            )

        return RetractionInfo(
            is_retracted=False,
            retraction_type="",
            source="crossref",
        )

    except Exception as e:
        logger.warning(f"Crossref retraksiyon kontrolü hatası ({doi}): {e}")
        return None


def check_openalex_retraction(doi: str, session: requests.Session | None = None) -> Optional[RetractionInfo]:
    """OpenAlex'ten retraksiyon durumu kontrol et."""
    if not doi:
        return None

    sess = session or requests.Session()
    sess.headers.update({"User-Agent": "AcademicThesisWriter/1.0"})

    try:
        url = f"https://api.openalex.org/works/https://doi.org/{doi}"
        resp = sess.get(url, timeout=30)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()

        # Retracted flag
        if data.get("retracted"):
            return RetractionInfo(
                is_retracted=True,
                retraction_type="retracted",
                reason="OpenAlex retracted flag",
                original_doi=doi,
                source="openalex",
            )

        # Retraction nature (daha detaylı)
        retraction_nature = data.get("retraction_nature")
        if retraction_nature:
            return RetractionInfo(
                is_retracted=True,
                retraction_type=retraction_nature.lower().replace(" ", "_"),
                reason=f"OpenAlex retraction nature: {retraction_nature}",
                original_doi=doi,
                source="openalex",
            )

        return RetractionInfo(
            is_retracted=False,
            retraction_type="",
            source="openalex",
        )

    except Exception as e:
        logger.warning(f"OpenAlex retraksiyon kontrolü hatası ({doi}): {e}")
        return None


def check_pubmed_retraction(pmid: str, session: requests.Session | None = None) -> Optional[RetractionInfo]:
    """PubMed'ten retraksiyon durumu kontrol et (E-utilities)."""
    if not pmid:
        return None

    sess = session or requests.Session()
    sess.headers.update({"User-Agent": "AcademicThesisWriter/1.0"})

    try:
        # E-utilities elink ile retraksiyon linkini kontrol et
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
        params = {
            "dbfrom": "pubmed",
            "db": "pubmed",
            "id": pmid,
            "linkname": "pubmed_pubmed_retracted",
            "retmode": "json",
        }
        resp = session.get(url, params=params, timeout=30) if session else requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        link_sets = data.get("linksets", [])
        for link_set in link_sets:
            if link_set.get("linksetdbs"):
                for ldb in link_set["linksetdbs"]:
                    if ldb.get("linkname") == "pubmed_pubmed_retracted":
                        ids = ldb.get("ids", [])
                        if ids:
                            return RetractionInfo(
                                is_retracted=True,
                                retraction_type="retracted",
                                reason="PubMed retraksiyon linki bulundu",
                                retraction_doi="",
                                original_doi=pmid,
                                source="pubmed",
                            )

        # Publication type kontrolü
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        params = {
            "db": "pubmed",
            "id": pmid,
            "retmode": "xml",
        }
        resp = session.get(fetch_url, params=params, timeout=30) if session else requests.get(fetch_url, params=params, timeout=30)
        resp.raise_for_status()
        import xml.etree.ElementTree as ET
        root = ET.fromstring(resp.text)
        for pt in root.findall(".//PublicationType"):
            if pt.text and "retracted" in pt.text.lower():
                return RetractionInfo(
                    is_retracted=True,
                    retraction_type="retracted",
                    reason="PubMed publication type: Retracted Publication",
                    original_doi=pmid,
                    source="pubmed",
                )

        return RetractionInfo(
            is_retracted=False,
            retraction_type="",
            source="pubmed",
        )

    except Exception as e:
        logger.warning(f"PubMed retraksiyon kontrolü hatası ({pmid}): {e}")
        return None


def check_retraction_status(
    doi: str = "",
    pmid: str = "",
    session: requests.Session | None = None,
) -> list[RetractionInfo]:
    """Tüm kaynaklardan retraksiyon durumu kontrol et.

    Returns: RetractionInfo listesi (her kaynak için bir tane)
    """
    results = []

    # Crossref
    if doi:
        result = check_crossref_retraction(doi)
        if result:
            results.append(result)

    # OpenAlex
    if doi:
        result = check_openalex_retraction(doi)
        if result:
            results.append(result)

    # PubMed (PMID gerekli)
    if pmid:
        result = check_pubmed_retraction(pmid)
        if result:
            results.append(result)

    return results


def check_correction_status(
    doi: str = "",
    session: requests.Session | None = None,
) -> Optional[CorrectionInfo]:
    """Crossref'ten düzeltme/erratum bilgisi kontrol et."""
    if not doi:
        return None

    try:
        url = f"https://api.crossref.org/works/{doi}"
        sess = session or requests.Session()
        sess.headers.update({"User-Agent": "AcademicThesisWriter/1.0"})
        resp = session.get(f"https://api.crossref.org/works/{doi}", timeout=30) if session else requests.get(f"https://api.crossref.org/works/{doi}", timeout=30)
        resp.raise_for_status()
        data = resp.json()
        item = data.get("message", {})

        relations = item.get("relation", {}) or {}
        for rel_type, rel_items in relations.items():
            if rel_type in ("has-correction", "has-erratum", "is-corrected-by"):
                for rel in rel_items:
                    rel_doi = rel.get("id", "").replace("https://doi.org/", "")
                    corr_type = "correction"
                    if rel_type == "has-erratum":
                        corr_type = "erratum"
                    return CorrectionInfo(
                        is_corrected=True,
                        correction_type=corr_type,
                        correction_doi=rel.get("id", "").replace("https://doi.org/", ""),
                        details=f"Crossref relation: {rel_type}",
                        source="crossref",
                    )

        return None
    except Exception as e:
        logger.warning(f"Düzeltme kontrolü hatası ({doi}): {e}")
        return None