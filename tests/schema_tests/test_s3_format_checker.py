"""S3: Çalışma zamanı dayanıklılığı — FormatChecker, PEP 701 f-string, Python 3.9+."""
from __future__ import annotations

import ast
import pathlib
import sys

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

# tools.atw.state içe aktarılmadan önce path ayarla
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from tools.atw.state import load_schema, _state_validator, validate_state, empty_state


def _kaynak(**ek):
    """`source.json`'a göre geçerli bir kayıt üretir.

    `verification` iç içe nesnedir ve dört alanın hepsi zorunludur.
    """
    return {
        "id": "SRC-001",
        "title": "Kurgusal örnek",
        "source_type": "article",
        "verification": {
            "status": "pending",
            "bibliographic_match": 0.0,
            "verified_at": "2026-09-26T10:12:00+00:00",
            "verification_sources": ["manual"],
        },
        **ek,
    }


def test_bozuk_access_date_reddediliyor():
    """access_date '26.09.2026' formatı reddedilmeli (format: date)."""
    dogrulayici = _state_validator()
    sema = load_schema("source.json")
    kayit = _kaynak(access_date="26.09.2026")
    with pytest.raises(ValidationError) as hata:
        dogrulayici.evolve(schema=sema).validate(kayit)
    assert "'date'" in str(hata.value)


def test_access_date_yalniz_tarih_kabul():
    """access_date '2026-09-26' (sadece tarih) kabul edilmeli."""
    dogrulayici = _state_validator()
    sema = load_schema("source.json")
    dogrulayici.evolve(schema=sema).validate(_kaynak(access_date="2026-09-26"))


def test_access_date_null_kabul():
    """access_date null kabul edilmeli (nullable)."""
    dogrulayici = _state_validator()
    sema = load_schema("source.json")
    dogrulayici.evolve(schema=sema).validate(_kaynak(access_date=None))


def test_verified_at_gun_yalniz_reddediliyor():
    """verified_at '2026-09-26' (sadece gün) reddedilmeli — format: date-time.

    4 fixture tam tarih-saat kullanıyor; belgeler de eski halde gün yazıyordu.
    """
    dogrulayici = _state_validator()
    sema = load_schema("source.json")
    kayit = _kaynak()
    kayit["verification"]["verified_at"] = "2026-09-26"
    with pytest.raises(ValidationError) as hata:
        dogrulayici.evolve(schema=sema).validate(kayit)
    assert "'date-time'" in str(hata.value)


def test_verified_at_tam_tarih_saat_kabul():
    """verified_at '2026-09-26T10:12:00+00:00' kabul edilmeli."""
    dogrulayici = _state_validator()
    sema = load_schema("source.json")
    kayit = _kaynak()
    kayit["verification"]["verified_at"] = "2026-09-26T10:12:00+00:00"
    dogrulayici.evolve(schema=sema).validate(kayit)


def test_bozuk_search_run_timestamp_reddediliyor():
    """search_run.timestamp '2026-09-26 09:00' (boşluklu) reddedilmeli — format: date-time."""
    dogrulayici = _state_validator()
    sema = load_schema("search_run.json")
    kayit = {
        "id": "SEARCH-001",
        "query": "kurgusal",
        "database": "crossref",
        "timestamp": "2026-09-26 09:00",
        "results_returned": 10,
        "inclusion_criteria": ["a"],
        "exclusion_criteria": ["b"],
        "prisma_flow": {
            "records_identified": 10,
            "duplicates_removed": 0,
            "records_screened": 10,
            "records_excluded": 0,
            "reports_sought": 10,
            "reports_not_retrieved": 0,
            "reports_excluded": 0,
            "studies_included": 10,
        },
    }
    with pytest.raises(ValidationError):
        dogrulayici.evolve(schema=sema).validate(kayit)


def test_bos_durum_formatlari_gecer():
    """empty_state() oluşturulan durum format hatası vermemeli."""
    durum = empty_state("THESIS-2026-001", "Test Tezi")
    hatalar = validate_state(durum)
    assert not hatalar, f"empty_state format hataları: {hatalar}"


def test_state_py_ast_parse_3_9():
    """tools/atw/state.py AST parse edilebilmeli: Python 3.9 (feature_version=(3,9))."""
    kod = pathlib.Path("tools/atw/state.py").read_text(encoding="utf-8")
    # 3.9'da PEP 701 f-string (iç içe aynı tırnak) SÖZ DİZİM hatasıdır
    ast.parse(kod, feature_version=(3, 9))


def test_state_py_ast_parse_3_10():
    """tools/atw/state.py AST parse edilebilmeli: Python 3.10."""
    kod = pathlib.Path("tools/atw/state.py").read_text(encoding="utf-8")
    ast.parse(kod, feature_version=(3, 10))


def test_state_py_ast_parse_3_11():
    """tools/atw/state.py AST parse edilebilmeli: Python 3.11."""
    kod = pathlib.Path("tools/atw/state.py").read_text(encoding="utf-8")
    ast.parse(kod, feature_version=(3, 11))


def test_state_py_ast_parse_3_12():
    """tools/atw/state.py AST parse edilebilmeli: Python 3.12 (bugün)."""
    kod = pathlib.Path("tools/atw/state.py").read_text(encoding="utf-8")
    ast.parse(kod, feature_version=(3, 12))


def test_requirements_txt_dil_tabani():
    """requirements.txt içinde Python 3.9+ dil tabanı notu olmalı."""
    icerik = pathlib.Path("requirements.txt").read_text(encoding="utf-8")
    assert "3.9" in icerik or "3.10" in icerik or "3.11" in icerik


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-p", "no:cacheprovider"])