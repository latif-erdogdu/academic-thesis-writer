"""Kimlik uretimi ve dogrulama testleri."""
from __future__ import annotations

import pytest

from tools.atw.ids import (
    ID_PREFIXES,
    IdError,
    format_id,
    is_valid_id,
    next_id,
    parse_id,
)


def test_format_id_uc_hane_sifir_doldurur():
    assert format_id("SRC", 1) == "SRC-001"
    assert format_id("EVD", 42) == "EVD-042"
    assert format_id("SEARCH", 7) == "SEARCH-007"


def test_format_id_dokuz_yuz_dokuzu_agir_uzar():
    assert format_id("SRC", 1000) == "SRC-1000"


def test_format_id_alan_kisa_olsun():
    assert format_id("P", 3) == "P-003"


def test_parse_id_donus():
    assert parse_id("CLM-017") == ("CLM", 17)
    assert parse_id("SEARCH-001") == ("SEARCH", 1)
    assert parse_id("P-004") == ("P", 4)


def test_parse_id_hatali_girdide_hata_firlatir():
    for hatali in ["CLM17", "CLM-", "-017", "clm-017", "CLM-17a", "CLM-1.7"]:
        with pytest.raises(IdError):
            parse_id(hatali)


def test_is_valid_id_alan_ayirt_edici_degil():
    assert is_valid_id("SRC-001") is True
    assert is_valid_id("XXX-001") is False  # bilinmeyen prefiks
    assert is_valid_id("SRC-1") is False  # iki hane yetersiz
    assert is_valid_id("") is False


def test_id_prefixes_yirmi_ogeyi_kapsar():
    assert len(ID_PREFIXES) == 20
    for beklenen in ["SRC", "EVD", "CLM", "CIT", "P", "RQ", "HYP", "FND",
                      "DSC", "CON", "GAP", "AUD", "SEARCH", "DS", "ANL",
                      "STAT", "TBL", "FIG", "CH", "VAR"]:
        assert beklenen in ID_PREFIXES


def test_next_id_bos_listeden_baslar():
    assert next_id([], "SRC") == "SRC-001"


def test_next_id_en_yuksek_kimlikten_devam_eder():
    mevcut = ["SRC-001", "SRC-002", "SRC-009", "SRC-010"]
    assert next_id(mevcut, "SRC") == "SRC-011"


def test_next_id_karisik_kimlikleri_yoksayarak_ilerler():
    # CLM-005 varken SRC sayaci bundan etkilenmemeli
    assert next_id(["SRC-001", "CLM-005"], "SRC") == "SRC-002"


def test_next_id_bilinmeyen_prefiks_hata_firlatir():
    with pytest.raises(IdError):
        next_id([], "XXX")


# Review Focus 3: ayni kimligin iki varlikta kullilmasi sessizce
# uzerine yazilmamali; next_id bunu bir sonraki bos yere kaydirarak
# fark edilebilir kilar.
def test_next_id_cakisan_kimligi_atlar():
    # SRC-001 iki kez geciyor: sonraki kimlik SRC-002 olmali, SRC-001 degil
    assert next_id(["SRC-001", "SRC-001"], "SRC") == "SRC-002"
