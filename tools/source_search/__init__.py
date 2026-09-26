"""tools.source_search — Kaynak keşfi modülü.

Crossref, OpenAlex, Semantic Scholar, PubMed, Google Scholar
üzerinden sistematik kaynak arama ve PRISMA uyumlu search_run.json üretimi.
"""
from __future__ import annotations

from .crossref import CrossrefClient, search_crossref
from .openalex import OpenAlexClient, search_openalex
from .semantic_scholar import SemanticScholarClient, search_semantic_scholar
from .pubmed import PubMedClient, search_pubmed
from .query_builder import build_boolean_query, parse_pico, PICO
from .deduplicate import deduplicate_sources
from .search_run import run_systematic_search, SearchRunResult

__all__ = [
    "CrossrefClient",
    "search_crossref",
    "OpenAlexClient",
    "search_openalex",
    "SemanticScholarClient",
    "search_semantic_scholar",
    "PubMedClient",
    "search_pubmed",
    "PICO",
    "build_boolean_query",
    "parse_pico",
    "deduplicate_sources",
    "run_systematic_search",
    "SearchRunResult",
]