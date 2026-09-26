"""Sema yukleme, tez durumu yukleme/kaydetme ve dogrulama.

Kalici varliklarin tek dogruluk kaynagi ``schemas/*.json`` dosyardir.

Bu modul semarii yukler, ``thesis_state`` belgesini dogrular ve diskte
tutar. Semalarin Python karsiliklari burada tanimlanmaz.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

SCHEMA_DIR: Path = Path(__file__).resolve().parents[2] / "schemas"

APPROVAL_GATES: list[str] = [
    "research_question",
    "search_strategy",
    "source_set",
    "research_gap",
    "methodology",
    "findings",
    "final_thesis",
]

_STATE_IDENTITY = "id"

# Kopuk referans denetimi icin: registry adi -> kayitlarin tutuldugu alan
_REGISTRY_FIELDS: dict[str, str] = {
    "evidence_registry": "evidence",
    "claims_registry": "claim",
    "findings_registry": "finding",
    "discussion_registry": "discussion",
    "conclusion_registry": "conclusion",
    "gap_registry": "research_gap",
    "audit_registry": "audit",
    "search_runs": "search_run",
    "sources": "source",
    "citations": "citation",
    "datasets": "dataset",
    "analyses": "analysis",
    "statistics": "statistic",
    "tables": "table",
    "figures": "figure",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_schema(name: str) -> dict[str, Any]:
    """``schemas/<name>`` dosyasini sozluk olarak yukler.

    Raises:
        FileNotFoundError: Sema dosyasi yoksa.
        json.JSONDecodeError: Dosya gecerli JSON degilse.
    """
    yol = SCHEMA_DIR / name
    if not yol.is_file():
        raise FileNotFoundError(f"Sema dosyasi bulunamadi: {yol}")
    return json.loads(yol.read_text(encoding="utf-8"))


def schema_registry() -> Registry:
    """Tum semalarin ``$id`` degerleriyle kurulmus referans kaydi.

    ``schemas/`` altindaki dosyalarin hepsi gercek sema degildir: Task 4 ve
    Task 5'e kadar alti dosya duz JSON sablon olarak durur ve ``$schema``
    bildirmez. ``Resource.from_contents()`` diyalecti yalnizca ``$schema``
    alanindan belirledigi icin, sablon dosyalar kayda katilmaz. Bu bir
    hata yutma degil, tanim degil: bir duz JSON sablonu sema registry'sinde
    yer almamalidir. Gercek bir semanin ``$schema`` bildirmemesi hali
    ``test_her_semanin_id_alani_var`` ve
    ``test_tum_semalar_draft_2020_12_uyumlu`` testleriyle Task 7'de yakalanir.
    """
    kaynaklar = []
    for yol in sorted(SCHEMA_DIR.glob("*.json")):
        sema = json.loads(yol.read_text(encoding="utf-8"))
        if "$schema" not in sema:
            continue
        uri = sema.get("$id") or yol.as_uri()
        kaynaklar.append((uri, Resource.from_contents(sema)))
    return Registry().with_resources(kaynaklar)


def _state_validator() -> Draft202012Validator:
    return Draft202012Validator(load_schema("thesis_state.json"), registry=schema_registry())


def empty_state(thesis_id: str, title: str = "") -> dict[str, Any]:
    """Onaylanmamis, bos bir tez durumu olusturur."""
    simdi = _utc_now()
    return {
        "schema_version": "1.0",
        "thesis_id": thesis_id,
        "title": title,
        "language": "tr",
        "research_questions": [],
        "hypotheses": [],
        "conceptual_framework": [],
        "methodology": {},
        "chapters": [],
        "evidence_registry": [],
        "claims_registry": [],
        "findings_registry": [],
        "discussion_registry": [],
        "conclusion_registry": [],
        "gap_registry": [],
        "audit_registry": [],
        "search_runs": [],
        "sources": [],
        "citations": [],
        "datasets": [],
        "analyses": [],
        "statistics": [],
        "tables": [],
        "figures": [],
        "definitions": [],
        "variables": [],
        "open_questions": [],
        "quality_issues": [],
        "human_approvals": {kapili: False for kapili in APPROVAL_GATES},
        "style_profile": "apa7",
        "created_at": simdi,
        "updated_at": simdi,
        "version": 1,
    }


def validate_state(state: dict[str, Any]) -> list[str]:
    """Durumu semaya gore dogrular.

    Returns:
        Hata mesajlari listesi. Dokuman gecerliyse bosListe doner.
    """
    dogrulayici = _state_validator()
    hatalar = []
    for hata in sorted(dogrulayici.iter_errors(state), key=lambda e: list(e.absolute_path)):
        konum = "/".join(str(parca) for parca in hata.absolute_path) or "<kok>"
        hatalar.append(f"{konum}: {hata.message}")
    return hatalar


def find_dangling_references(state: dict[str, Any]) -> list[str]:
    """Registry alanlarindaki her kaydin ``<alan>_<id>`` iletisim kuralini denetler.

    Ornegin ``evidence_registry`` icindeki bir kaydin ``source_id`` degeri
    ``sources`` icinde bulunamazsa kopuk bag olarak bildirilir.
    """
    kopuk: list[str] = []
    for alan, varlik_adi in _REGISTRY_FIELDS.items():
        for kayit in state.get(alan, []) or []:
            if not isinstance(kayit, dict):
                continue
            kimlik = kayit.get(_STATE_IDENTITY)
            if not kimlik:
                continue
            for hedef_alan, hedef_adi in _REGISTRY_FIELDS.items():
                if hedef_alan == alan:
                    continue
                referans_alan = f"{hedef_adi}_id"
                referans = kayit.get(referans_alan)
                if not isinstance(referans, str):
                    continue
                mevcut = {
                    k.get(_STATE_IDENTITY)
                    for k in (state.get(hedef_alan) or []) if isinstance(k, dict)
                }
                if referans not in mevcut:
                    kopuk.append(
                        f"{varlik_adi} {kimlik} -> {referans_alan}={referans} "
                        f"({hedef_adi} kaydi bulunamadi)"
                    )
    return kopuk


def load_state(path: str | Path) -> dict[str, Any]:
    """Durumu diskten okur ve dogrular.

    Raises:
        FileNotFoundError: Dosya yoksa.
        ValueError: Belge semaya uymuyorsa.
    """
    yol = Path(path)
    if not yol.is_file():
        raise FileNotFoundError(f"Durum dosyasi bulunamadi: {yol}")
    durum = json.loads(yol.read_text(encoding="utf-8"))
    hatalar = validate_state(durum)
    if hatalar:
        detay = "; ".join(hatalar[:5])
        raise ValueError(f"Durum semaya uymuyor ({len(hatalar)} hata): {detay}")
    return durum


def save_state(path: str | Path, state: dict[str, Any]) -> None:
    """Durumu dogrular ve diskte yazar.

    Dogrulama basarisizsa hicbir dosya yazilmaz.

    Raises:
        ValueError: Belge semaya uymuyorsa.
    """
    hatalar = validate_state(state)
    if hatalar:
        detay = "; ".join(hatalar[:5])
        raise ValueError(f"Durum semaya uymuyor ({len(hatalar)} hata): {detay}")
    yol = Path(path)
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def validate_prisma_flow(flow: dict[str, Any]) -> list[str]:
    """PRISMA sayimlari arasindaki aritmetik tutarliligi denetler.

    Denetlenen uc iliski:
      1. records_identified - duplicates_removed = records_screened
      2. records_screened  - records_excluded  = reports_sought
      3. reports_sought    - reports_not_retrieved
         = reports_excluded + studies_included

    Ucuncu iliskide `reports_not_retrieved` ayri bir sayimdir:
    ulasilan rapor sayisi, alinamayan raporlar dusuldugunde
    dislenen raporlar + dahil edilen calismalar toplamina esit olmalidir.

    `exclusion_reasons` toplaminin `records_excluded`a esitligi bu
    fonksiyonda denetlenemez: alan `prisma_flow` disindadir ve fonksiyon
    yalnizca `prisma_flow` alir.

    Args:
        flow: ``search_run.json`` icindeki ``prisma_flow`` nesnesi.

    Returns:
        Hata mesajlari listesi. Tutarliysa bosListe doner.
    """
    hatalar: list[str] = []
    sayi = flow.get

    sol = sayi("records_identified", 0) - sayi("duplicates_removed", 0)
    if sol != sayi("records_screened", 0):
        hatalar.append(
            f"records_identified({sayi("records_identified", 0)}) - "
            f"duplicates_removed({sayi("duplicates_removed", 0)}) = {sol}, "
            f"ancak records_screened = {sayi("records_screened", 0)}"
        )

    sol = sayi("records_screened", 0) - sayi("records_excluded", 0)
    if sol != sayi("reports_sought", 0):
        hatalar.append(
            f"records_screened({sayi("records_screened", 0)}) - "
            f"records_excluded({sayi("records_excluded", 0)}) = {sol}, "
            f"ancak reports_sought = {sayi("reports_sought", 0)}"
        )

    sol = sayi("reports_sought", 0) - sayi("reports_not_retrieved", 0)
    sag = sayi("reports_excluded", 0) + sayi("studies_included", 0)
    if sol != sag:
        hatalar.append(
            f"reports_sought({sayi("reports_sought", 0)}) - "
            f"reports_not_retrieved({sayi("reports_not_retrieved", 0)}) = {sol}, "
            f"ancak reports_excluded({sayi("reports_excluded", 0)}) + "
            f"studies_included({sayi("studies_included", 0)}) = {sag}"
        )

    return hatalar