"""State'e yazilmayan calisma-zamani tipleri.

Bu tipler arac zincirinin ara sonuclarini tasiyan gecici nesnelerdir;
kalici varliklar ``schemas/*.json`` ve ``thesis_state`` icinde yasar.
Burada tanimlanan alanlar o yuzden JSON Schema ile tekrar tanimlanmaz.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Final

from tools.atw.ids import is_valid_id

VERIFICATION_STATUSES: Final[tuple[str, ...]] = (
    "verified", "unverified", "pending", "retracted", "corrected",
)

EVIDENCE_TYPES: Final[tuple[str, ...]] = (
    "literature", "primary_data", "statistical", "finding", "method", "theory",
)

STRENGTHS: Final[tuple[str, ...]] = ("direct", "indirect")

EN_AZ_BAGIMSIZ_KAYNAK: Final = 2
ESIK_ESLESME: Final = 0.60

_DOI_PATTERN: Final = re.compile(r"^10\.\d{4,9}/\S+$")


@dataclass(frozen=True)
class Location:
    """Kanitin kaynak icindeki konumu."""

    page: int | None = None
    section: str = ""
    paragraph: int | None = None

    def as_dict(self) -> dict:
        return {"page": self.page, "section": self.section, "paragraph": self.paragraph}


@dataclass
class PageText:
    """Bir PDF sayfasinin cikarilan metni ve basliklari."""

    page: int
    text: str
    sections: list[str] = field(default_factory=list)


@dataclass
class Passage:
    """Sayfa icinde konumlandirilmis tek bir kanit parcasi."""

    source_id: str
    page: int
    section: str
    text: str
    char_start: int
    char_end: int

    def __post_init__(self) -> None:
        if not is_valid_id(self.source_id):
            raise ValueError(f"Gecersiz kaynak kimligi: {self.source_id!r}")
        if self.char_start < 0 or self.char_end < 0:
            raise ValueError("Karakter konumlari negatif olamaz")
        if self.char_end < self.char_start:
            raise ValueError(
                f"char_end ({self.char_end}) char_start'tan "
                f"kucuk olamaz ({self.char_start})"
            )


@dataclass
class SourceCandidate:
    """Dogrulanmamis bir kaynak adayi."""

    doi: str | None
    title: str
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    source_type: str | None = None

    def __post_init__(self) -> None:
        if self.doi is not None and not _DOI_PATTERN.match(self.doi):
            raise ValueError(f"Bicimsiz DOI: {self.doi!r}")


@dataclass
class VerificationResult:
    """Bir kaynak adayinin dogrulama sonucu."""

    status: str
    bibliographic_match: float
    doi_match: bool
    author_match: bool
    title_match: bool
    year_match: bool
    journal_match: bool
    retraction_status: str
    correction_status: str
    supersedes: str | None
    verified_at: str
    verification_sources: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.status not in VERIFICATION_STATUSES:
            raise ValueError(
                f"Bilinmeyen dogrulama durumu: {self.status!r}. "
                f"Izin verilenler: {list(VERIFICATION_STATUSES)}"
            )
        if not 0.0 <= self.bibliographic_match <= 1.0:
            raise ValueError(
                f"bibliographic_match 0-1 araliginda olmali: "
                f"{self.bibliographic_match}"
            )
        if self.status in ("verified", "corrected"):
            if self.bibliographic_match < ESIK_ESLESME:
                raise ValueError(
                    f"Durum {self.status!r} iken eslesme esigin altinda: "
                    f"{self.bibliographic_match} < {ESIK_ESLESME}"
                )
            if len(self.verification_sources) < EN_AZ_BAGIMSIZ_KAYNAK:
                raise ValueError(
                    f"{self.status!r} icin en az {EN_AZ_BAGIMSIZ_KAYNAK} "
                    f"bagimsiz kaynak gerekli, verilen: "
                    f"{self.verification_sources}"
                )


@dataclass
class EvidenceDraft:
    """Kanit cikarimindan hemen sonraki, henuz kaydedilmemis kanit."""

    source_id: str
    location: dict
    text: str
    evidence_type: str
    strength: str

    def __post_init__(self) -> None:
        if not is_valid_id(self.source_id):
            raise ValueError(f"Gecersiz kaynak kimligi: {self.source_id!r}")
        if self.evidence_type not in EVIDENCE_TYPES:
            raise ValueError(
                f"Bilinmeyen kanit tipi: {self.evidence_type!r}. "
                f"Izin verilenler: {list(EVIDENCE_TYPES)}"
            )
        if self.strength not in STRENGTHS:
            raise ValueError(
                f"Bilinmeyen kanit gucu: {self.strength!r}. "
                f"Izin verilenler: {list(STRENGTHS)}"
            )
