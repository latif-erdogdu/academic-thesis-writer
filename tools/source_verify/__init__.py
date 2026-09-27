"""tools.source_verify — Kaynak doğrulama modülü.

DOI ve bibliyografik doğrulama (en az 2 bağımsız kaynak, skor ≥0.60).
Retraksiyon/korizyon kontrolü.
"""
from __future__ import annotations

from .verify import (
    verify_source,
    verify_sources_batch,
    VerificationResult,
    VerificationStatus,
)
from .bibliographic import (
    compute_bibliographic_match,
    compare_titles,
    compare_authors,
    compare_years,
    compare_journals,
)
from .retraction import check_retraction_status, check_correction_status
from .verify import MIN_BIBLIOGRAPHIC_MATCH, MIN_INDEPENDENT_SOURCES

__all__ = [
    "verify_source",
    "verify_sources_batch",
    "VerificationResult",
    "VerificationStatus",
    "compute_bibliographic_match",
    "compare_titles",
    "compare_authors",
    "compare_years",
    "compare_journals",
    "check_retraction_status",
    "check_correction_status",
    # Eşikler. `tools.atw.cli.cmd_verify` karşılaştırma işaretlerini
    # (title_match vb.) motorun KENDI eşiğinden türetir; eşiği ikinci bir
    # yerde yazmak motorun kuralıyla ayrışabilir.
    "MIN_BIBLIOGRAPHIC_MATCH",
    "MIN_INDEPENDENT_SOURCES",
]
