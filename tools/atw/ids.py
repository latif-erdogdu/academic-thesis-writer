"""Tez varliklari icin kimlik uretimi, ayristirma ve dogrulama.

Kimlik bicimi: ``<PREFIX>-<NNN>`` (uc haneli sifir dolgulu).
999'u asan sayaclar genisler: ``SRC-1000``.
"""
from __future__ import annotations

import re
from typing import Final, Iterable

ID_PREFIXES: Final[dict[str, str]] = {
    "SRC": "source",
    "EVD": "evidence",
    "CLM": "claim",
    "CIT": "citation",
    "P": "paragraph",
    "RQ": "research_question",
    "HYP": "hypothesis",
    "FND": "finding",
    "DSC": "discussion",
    "CON": "conclusion",
    "GAP": "research_gap",
    "AUD": "audit",
    "SEARCH": "search_run",
    "DS": "dataset",
    "ANL": "analysis",
    "STAT": "statistic",
    "TBL": "table",
    "FIG": "figure",
}

_ID_PATTERN: Final = re.compile(r"^(?P<prefix>[A-Z]+)-(?P<number>\d{3,})$")
_HANE_SAYISI: Final = 3


class IdError(ValueError):
    """Gecersiz kimlik bicimi veya bilinmeyen prefiks."""


def format_id(prefix: str, number: int) -> str:
    """Prefiks ve sayiyi kimlik metnine cevirir.

    Args:
        prefix: ``ID_PREFIXES`` icindeki bir prefiks.
        number: Sifirdan kucuk olmayan tam sayi.

    Returns:
        ``SRC-001`` biciminde kimlik.

    Raises:
        IdError: Prefiks bilinmiyorsa veya sayi gecersizse.
    """
    if prefix not in ID_PREFIXES:
        raise IdError(f"Bilinmeyen prefiks: {prefix!r}")
    if not isinstance(number, int) or isinstance(number, bool):
        raise IdError(f"Sayi tam sayi olmali: {number!r}")
    if number < 0:
        raise IdError(f"Sayi negatif olamaz: {number!r}")
    return f"{prefix}-{number:0{_HANE_SAYISI}d}"


def parse_id(value: str) -> tuple[str, int]:
    """Kimlik metnini ``(prefiks, sayi)`` ciftine ayristirir.

    Raises:
        IdError: Bicim hataliysa veya prefiks bilinmiyorsa.
    """
    if not isinstance(value, str):
        raise IdError(f"Kimlik metin olmali: {value!r}")
    eslesme = _ID_PATTERN.match(value)
    if eslesme is None:
        raise IdError(f"Bicim hatali kimlik: {value!r}")
    prefiks = eslesme.group("prefix")
    if prefiks not in ID_PREFIXES:
        raise IdError(f"Bilinmeyen prefiks: {value!r}")
    return prefiks, int(eslesme.group("number"))


def is_valid_id(value: str) -> bool:
    """Kimligin bicim ve prefiks kurallarina uyup uymadigini bildirir."""
    try:
        parse_id(value)
    except IdError:
        return False
    return True


def next_id(existing: Iterable[str], prefix: str) -> str:
    """Verilen kimlikler arasindan sonraki bos numarayi uretir.

    Args:
        existing: Var olan kimlikler (``"SRC-003"`` gibi). Hatali bicimli
            girdiler sessizce yok sayilir.
        prefix: Hedef prefiks.

    Returns:
        Bir sonraki kullanilabilir kimlik, orn. ``"SRC-004"``.

    Raises:
        IdError: Prefiks bilinmiyorsa.

    Examples:
        >>> next_id(["SRC-001", "SRC-002", "SRC-009"], "SRC")
        'SRC-010'
    """
    if prefix not in ID_PREFIXES:
        raise IdError(f"Bilinmeyen prefiks: {prefix!r}")
    en_yuksek = 0
    for kimlik in existing:
        try:
            kimlik_prefiks, sayi = parse_id(kimlik)
        except IdError:
            continue
        if kimlik_prefiks == prefix and sayi > en_yuksek:
            en_yuksek = sayi
    return format_id(prefix, en_yuksek + 1)
