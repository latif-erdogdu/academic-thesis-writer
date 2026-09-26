"""PRISMA uyumlu search_run.json üretimi ve sistematik arama koordine edici."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .crossref import search_crossref, CrossrefWork
from .openalex import search_openalex, OpenAlexWork
from .semantic_scholar import search_semantic_scholar
from .pubmed import search_pubmed, PubMedArticle
from .google_scholar import search_google_scholar
from .query_builder import build_multi_database_queries, PICO, parse_pico, SearchQuery
from .deduplicate import deduplicate_sources, merge_duplicate_records, DedupResult

from tools.atw.ids import format_id
from tools.atw.state import load_state, save_state


@dataclass
class DatabaseSearchResult:
    """Tek veritabanı arama sonucu."""
    database: str
    query: SearchQuery
    records_found: int
    records_returned: int
    records: list[dict]  # source.json formatında
    execution_time_ms: int
    errors: list[str] = field(default_factory=list)


@dataclass
class SearchRunResult:
    """PRISMA akışı için tam arama sonucu."""
    search_run_id: str
    query: SearchQuery
    timestamp: str
    databases_searched: list[str]
    database_results: list[DatabaseSearchResult]
    prisma_flow: dict
    deduplication: DedupResult
    included_source_ids: list[str]
    excluded_reasons: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.search_run_id,
            "query": self.query.boolean_string,
            "database": self.query.databases[0] if self.query.databases else "multi",
            "timestamp": self.timestamp,
            "results_returned": sum(r.records_returned for r in self.database_results),
            "inclusion_criteria": self.query.pico.to_dict() if hasattr(self.query, 'pico') else {},
            "exclusion_criteria": [],
            "prisma_flow": self.prisma_flow,
            "exclusion_reasons": self.excluded_reasons,
            "included_source_ids": self.included_source_ids,
            "deduplication_stats": self.deduplication.stats,
        }


class SystematicSearchOrchestrator:
    """Sistematik arama koordine edici - PRISMA uyumlu."""

    DATABASES = ["crossref", "openalex", "semantic_scholar", "pubmed", "google_scholar"]

    def __init__(
        self,
        crossref_mailto: str = "research@example.com",
        openalex_email: str | None = None,
        semantic_scholar_key: str | None = None,
        pubmed_email: str | None = None,
        serpapi_key: str | None = None,
        max_results_per_db: int = 100,
        deduplication_threshold: float = 0.9,
    ):
        self.crossref_mailto = crossref_mailto
        self.openalex_email = openalex_email
        self.semantic_scholar_key = semantic_scholar_key
        self.pubmed_email = pubmed_email
        self.serpapi_key = serpapi_key
        self.max_results_per_db = max_results_per_db
        self.deduplication_threshold = deduplication_threshold

    def run_systematic_search(
        self,
        pico: PICO | str,
        databases: list[str] | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        inclusion_criteria: dict | None = None,
        exclusion_criteria: list[str] | None = None,
        thesis_id: str = "THESIS-2026-001",
    ) -> SearchRunResult:
        """Sistematik arama çalıştır ve PRISMA akışı üret."""

        if isinstance(pico, str):
            pico = parse_pico(pico)

        if databases is None:
            databases = self.DATABASES

        # Sorgu oluştur
        queries = build_multi_database_queries(pico, databases=databases)

        # Her veritabanında arama
        db_results = []
        all_records = []
        prisma_counts = {
            "records_identified": 0,
            "duplicates_removed": 0,
            "records_screened": 0,
            "records_excluded": 0,
            "reports_sought": 0,
            "reports_not_retrieved": 0,
            "reports_excluded": 0,
            "studies_included": 0,
        }

        search_run_id = format_id("SEARCH", int(time.time() * 1000) % 10000)

        for db in databases:
            if db not in queries:
                continue

            query = queries[db]
            start_time = time.time()
            records = []
            errors = []

            try:
                if db == "crossref":
                    raw = search_crossref(
                        query=query.boolean_string,
                        max_results=self.max_results_per_db,
                    )
                    records = [w.to_source_dict() for w in raw]
                elif db == "openalex":
                    raw = search_openalex(
                        query=query.boolean_string,
                        max_results=self.max_results_per_db,
                    )
                    records = [w.to_source_dict() for w in raw]
                elif db == "semantic_scholar":
                    raw = search_semantic_scholar(
                        query=query.boolean_string,
                        max_results=self.max_results_per_db,
                    )
                    records = [w.to_source_dict() for w in raw]
                elif db == "pubmed":
                    raw = search_pubmed(
                        query=query.boolean_string,
                        max_results=self.max_results_per_db,
                    )
                    records = [w.to_source_dict() for w in raw]
                elif db == "google_scholar":
                    raw = search_google_scholar(
                        query=query.boolean_string,
                        max_results=min(20, self.max_results_per_db),  # Google Scholar sınırlı
                    )
                    records = [r.to_source_dict() for r in raw]
                else:
                    errors.append(f"Bilinmeyen veritabanı: {db}")
            except Exception as e:
                errors.append(str(e))
                records = []

            exec_time = int((time.time() - start_time) * 1000)

            # Kayıt sayısını güncelle
            prisma_counts["records_identified"] += len(records)

            db_results.append(DatabaseSearchResult(
                database=db,
                query=query,
                records_found=len(records),
                records_returned=len(records),
                records=records,
                execution_time_ms=exec_time,
                errors=errors,
            ))

            all_records.extend(records)

        # Deduplication
        print(f"Deduplicating {len(all_records)} records...")
        dedup_result = deduplicate_sources(
            all_records,
            threshold=self.deduplication_threshold,
        )
        prisma_counts["duplicates_removed"] = dedup_result.stats["removed"]

        # Unique kayıtları birleştir (aynı kaynak farklı DB'den gelmişse)
        unique_records = dedup_result.unique

        # Screening (basit: inclusion/exclusion criteria)
        # Şimdilik hepsini include ediyoruz, gerçek implementasyonda
        # inclusion/exclusion criteria uygulanacak
        screened = unique_records
        prisma_counts["records_screened"] = len(screened)

        # Exclusion (örnek: review articles, non-english, etc.)
        # Gerçek implementasyonda exclusion criteria uygulanır
        excluded_count = 0
        exclusion_reasons = {}

        # Final included
        included = screened  # Şimdilik hepsi
        prisma_counts["reports_sought"] = len(included)
        prisma_counts["studies_included"] = len(included)

        # Source ID'leri ata (SRC-XXX formatında)
        included_ids = []
        for i, record in enumerate(included):
            src_id = format_id("SRC", i + 1)
            record["id"] = src_id
            included_ids.append(src_id)

        prisma_counts["records_excluded"] = excluded_count

        result = SearchRunResult(
            search_run_id=search_run_id,
            query=build_multi_database_queries(pico)[databases[0]] if databases else list(build_multi_database_queries(pico).values())[0],
            timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            databases_searched=databases,
            database_results=db_results,
            prisma_flow=prisma_counts,
            deduplication=dedup_result,
            included_source_ids=included_ids,
            excluded_reasons=exclusion_reasons,
        )

        return result

    def save_search_run(self, result: SearchRunResult, thesis_state_path: str = "thesis_state.json") -> None:
        """Search run sonucunu thesis_state.json'a kaydet."""
        state = load_state(thesis_state_path)
        state["search_runs"].append(result.to_dict())

        # Sources registry'e ekle
        for db_result in result.database_results:
            for record in db_result.records:
                if "id" in record and record["id"]:
                    state["sources"].append(record)

        save_state(thesis_state_path, state)


def run_systematic_search(
    pico: PICO | str,
    databases: list[str] | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    max_results_per_db: int = 100,
    thesis_state_path: str = "thesis_state.json",
    crossref_mailto: str = "research@example.com",
    openalex_email: str | None = None,
    semantic_scholar_key: str | None = None,
    pubmed_email: str | None = None,
    serpapi_key: str | None = None,
) -> SearchRunResult:
    """Sistematik arama çalıştır (kolaylık fonksiyonu)."""
    orchestrator = SystematicSearchOrchestrator(
        crossref_mailto=crossref_mailto,
        openalex_email=openalex_email,
        semantic_scholar_key=semantic_scholar_key,
        pubmed_email=pubmed_email,
        serpapi_key=serpapi_key,
        max_results_per_db=max_results_per_db,
    )

    if isinstance(pico, str):
        pico = parse_pico(pico)

    return orchestrator.run_systematic_search(
        pico=pico,
        databases=databases,
        year_from=year_from,
        year_to=year_to,
    )