"""Fixture'larin semaya uygunlugu ve sinir durum beklentileri.

Tum fixture'lardaki kaynak, yazar, yayinci, DOI ve metin bilgileri
KURGUSALDIR. 10.5555/ prefeksi bilerek uydurma bir DOI alanidir.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from tools.atw.ids import parse_id
from tools.atw.state import SCHEMA_DIR, schema_registry

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"

DOGRULANACAK = {
    "valid_source.json": "source.json",
    "fabricated_source.json": "source.json",
    "retracted_paper.json": "source.json",
    "corrected_paper.json": "source.json",
    "unsupported_claim.json": "claim.json",
    "contradictory_claim.json": "claim.json",
    "inconsistent_method.json": "research_question.json",
}

KURGUSAL_DOI_ONEKI = "10.5555/"


def _yukle(dosya_adi: str) -> dict:
    return json.loads((FIXTURE_DIR / dosya_adi).read_text(encoding="utf-8"))


def _dogrulayici(sema_adi: str) -> Draft202012Validator:
    sema = json.loads((SCHEMA_DIR / sema_adi).read_text(encoding="utf-8"))
    return Draft202012Validator(sema, registry=schema_registry())


def test_fixture_dosyalarinin_tumu_var():
    for ad in DOGRULANACAK:
        assert (FIXTURE_DIR / ad).is_file(), f"Eksik fixture: {ad}"


@pytest.mark.parametrize("fixture_adi,sema_adi", sorted(DOGRULANACAK.items()))
def test_fixture_ilgili_semayi_gecer(fixture_adi, sema_adi):
    kayit = _yukle(fixture_adi)
    hatalar = list(_dogrulayici(sema_adi).iter_errors(kayit))
    assert hatalar == [], f"{fixture_adi}: {hatalar[0].message if hatalar else ''}"


@pytest.mark.parametrize("fixture_adi,sema_adi", sorted(DOGRULANACAK.items()))
def test_fixture_kimligi_gecerli(fixture_adi, sema_adi):
    """Fixture kimligi bicimsel olarak dogru olmali (prefiks + 3 hane)."""
    kayit = _yukle(fixture_adi)
    prefiks, numara = parse_id(kayit["id"])
    assert numara >= 1
    assert kayit["id"] == f"{prefiks}-{numara:03d}"


def test_gecerli_kaynak_dogrulanmis_durumda():
    kayit = _yukle("valid_source.json")
    assert kayit["verification"]["status"] == "verified"
    assert len(kayit["verification"]["verification_sources"]) >= 2
    assert kayit["retraction_status"] == "not_retracted"


def test_gecerli_kaynak_kurgusal_doi_alanini_kullanir():
    """Fixture'lar gercek bir yayini temsil etmemeli."""
    kayit = _yukle("valid_source.json")
    assert kayit["doi"].startswith(KURGUSAL_DOI_ONEKI), (
        "Fixture DOI'si kurgusal onek kullanmali; gercek DOI kullanilmamali"
    )


def test_uydurulmus_kaynak_dogrulanmamis_isaretli():
    """Uydurma kayit semayi gecer ama dogrulanmis OLMAMALIDIR."""
    kayit = _yukle("fabricated_source.json")
    assert kayit["verified"] is False
    assert kayit["verification"]["status"] == "unverified"
    assert kayit["verification"]["bibliographic_match"] < 0.6


def test_uydurulmus_kaynak_kanit_tasimaz():
    kayit = _yukle("fabricated_source.json")
    assert kayit["evidence_ids"] == []


def test_geri_caledilmis_kayit_isaretli():
    kayit = _yukle("retracted_paper.json")
    assert kayit["retraction_status"] == "retracted"
    assert kayit["publication_status"] == "retracted"
    assert kayit["verification"]["status"] == "retracted"


def test_geri_caledilmis_kayit_veri_kaynagi_olarak_kullanilamaz():
    """Geri cekilmis kayit hala 'dogrulanmis' gorunmemeli."""
    kayit = _yukle("retracted_paper.json")
    assert kayit["verified"] is False


def test_duzeltilmis_kayit_ust_kaynaga_isaret_eder():
    kayit = _yukle("corrected_paper.json")
    assert kayit["correction_status"] in ("corrected", "erratum")
    assert kayit["supersedes_source_id"] is not None


def test_duzeltilmis_kayit_ust_kaynagin_kimligi_gecerli():
    kayit = _yukle("corrected_paper.json")
    ust_kimlik = kayit["supersedes_source_id"]
    assert parse_id(ust_kimlik)


def test_kanitsiz_iddia_isaretli():
    kayit = _yukle("unsupported_claim.json")
    assert kayit["evidence_ids"] == []
    assert kayit["verification_status"] == "unsupported"


def test_celiskili_iddia_her_iki_yonu_tasir():
    kayit = _yukle("contradictory_claim.json")
    assert kayit["evidence_ids"], "Celiskili iddia kanit tasimali"
    assert kayit["counter_claims"], "Celiskili iddia karsi iddia tasimali"


def test_yontem_tutarsizligi_soruda_gorunur():
    kayit = _yukle("inconsistent_method.json")
    assert kayit["status"] != "answered"
    assert kayit["finding_ids"] == [], "Bulgu baglanmamis olmali"


def test_yontem_tutarsizligi_notlarda_aciklanir():
    kayit = _yukle("inconsistent_method.json")
    assert "notes" in kayit
