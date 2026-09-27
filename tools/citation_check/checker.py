"""Atif butunluk denetimi.

tools/citation_check/README.md'deki denetim akisini uygular: kaynak varligi,
retraksiyon, metinde atiflanmayan kaynak, iddia destegi, APA 7 bicim ve
sayfa numarasi tutarliligi. Cikti, schemas/audit.json'a uyan bir denetim
kaydidir.
"""
from __future__ import annotations

import re
from datetime import date as _bugun
from typing import Any

from .style import validate_apa7

# "s. 15", "ss. 3-7", "p. 42" gibi sayfa/aralik isaretleri.
_LOKATOR_DESENI = re.compile(r"\b(?:s|ss|p|pp)\.\s*\d+", re.IGNORECASE)


def audit_citations(durum: dict[str, Any]) -> dict[str, Any]:
    """Atif butunluk denetimi yapar ve audit.json kaydi dondurur.

    Denetlenen alanlar: kaynaklar, citations, claims_registry.
    """
    kaynaklar = {k.get("id"): k for k in durum.get("sources") or [] if k.get("id")}
    atiflar = durum.get("citations") or []
    iddialar = durum.get("claims_registry") or []

    bulgular: list[dict[str, Any]] = []
    sayaclar = {
        "fabricated_sources": 0,
        "unsupported_claims": 0,
        "retracted_sources_in_use": 0,
        "orphaned_citations": 0,
        "unverifiable_claims": 0,
    }
    atiflanan: set[str] = set()

    for atif in atiflar:
        kimlik = atif.get("id")
        kaynak_kimlik = atif.get("source_id")
        kaynak = kaynaklar.get(kaynak_kimlik)
        konum = f"atıf {kimlik}"

        # Denetim 1 — kaynak varligi (critical).
        if kaynak is None:
            sayaclar["fabricated_sources"] += 1
            bulgular.append(_bulgu(
                "critical",
                f"{kimlik}, kaynaklarda bulunmayan {kaynak_kimlik} kaynagini gosteriyor.",
                konum, kimlik,
            ))
            continue

        atiflanan.add(kaynak_kimlik)

        # Denetim 2 — retraksiyon (critical).
        if kaynak.get("retraction_status") == "retracted":
            sayaclar["retracted_sources_in_use"] += 1
            bulgular.append(_bulgu(
                "critical",
                f"{kaynak_kimlik} retraksiyona ugramis ama metinde atiflanmis.",
                konum, kimlik,
            ))

        # Denetim 5 — APA 7 bicim (minor).
        if atif.get("style") == "apa7":
            for sorun in validate_apa7(atif.get("in_text_form", "")):
                bulgular.append(_bulgu("minor", f"{kimlik}: {sorun}", konum, kimlik))

        # Denetim 6 — sayfa numarasi tutarliligi (minor).
        sorun = _sayfa_tutarliligi(atif)
        if sorun is not None:
            bulgular.append(_bulgu("minor", f"{kimlik}: {sorun}", konum, kimlik))

    # Denetim 3 — metinde atiflanmayan kaynak (major).
    for kaynak_kimlik in kaynaklar:
        if kaynak_kimlik not in atiflanan:
            sayaclar["orphaned_citations"] += 1
            bulgular.append(_bulgu(
                "major",
                f"Kaynakta {kaynak_kimlik} var ama metinde hic atiflanmamis.",
                "Kaynakça", kaynak_kimlik,
            ))

    # Denetim 4 — iddia destegi (major).
    for iddia in iddialar:
        if iddia.get("verification_status") != "verified":
            sayaclar["unsupported_claims"] += 1
            bulgular.append(_bulgu(
                "major",
                f"{iddia.get('id')} iddiasi dogrulanmamis durumda.",
                "İddia kaydı", iddia.get("id"),
            ))

    return {
        "audit_id": _sonraki_audit_id(durum),
        "thesis_id": durum.get("thesis_id", ""),
        "audit_type": "citation",
        "date": _bugun.today().isoformat(),
        "findings": bulgular,
        "integrity_checks": sayaclar,
        "critical_issues": [b["message"] for b in bulgular if b["severity"] == "critical"],
        "deferred_minors": [b["message"] for b in bulgular if b["severity"] == "minor"],
    }


def _bulgu(severity: str, message: str, location: str, entity_id: str | None) -> dict[str, Any]:
    """audit.json findings girdisi olusturur."""
    return {
        "severity": severity,
        "message": message,
        "location": location,
        "entity_id": entity_id,
    }


def _sayfa_tutarliligi(atif: dict[str, Any]) -> str | None:
    """in_text_form lokatoru ile citation.page tutarliligini dogrular."""
    eslesme = _LOKATOR_DESENI.search(atif.get("in_text_form") or "")
    sayfa = atif.get("page")
    if eslesme is not None and sayfa is None:
        return (f"'{eslesme.group(0)}' lokatoru var ama citation.page bos; "
                f"dogrudan alintida sayfa zorunludur.")
    if eslesme is None and sayfa is not None:
        return f"citation.page {sayfa} var ama in_text_form'de lokator yok."
    return None


def _sonraki_audit_id(durum: dict[str, Any]) -> str:
    """mevcut audit_registry sayisina gore sonraki AUD kimligini uretir."""
    return f"AUD-{len(durum.get('audit_registry') or []) + 1:03d}"
