"""thesis_state semasi ve durum yonetimi testleri."""
from __future__ import annotations

import json

import pytest
from jsonschema import Draft202012Validator

from tools.atw.state import (
    APPROVAL_GATES,
    empty_state,
    find_dangling_references,
    load_schema,
    save_state,
    validate_state,
)


def test_tum_semalar_draft_2020_12_uyumlu(schema_dir):
    for sema_dosyasi in sorted(schema_dir.glob("*.json")):
        sema = json.loads(sema_dosyasi.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(sema), sema_dosyasi.name


@pytest.mark.xfaz
def test_sema_sayisi_onsekiz():
    from tools.atw.state import SCHEMA_DIR
    assert len(list(SCHEMA_DIR.glob("*.json"))) == 18


def test_her_semanin_id_alani_var(schema_dir):
    for sema_dosyasi in sorted(schema_dir.glob("*.json")):
        sema = json.loads(sema_dosyasi.read_text(encoding="utf-8"))
        assert sema.get("$id", "").endswith(sema_dosyasi.name), sema_dosyasi.name


def test_bos_durum_semayi_gecer():
    durum = empty_state("THESIS-2026-001", "Ornek Tez")
    assert validate_state(durum) == []


def test_bos_durum_zorunlu_alanlari_iceriyor():
    durum = empty_state("THESIS-2026-001")
    for alan in ["schema_version", "thesis_id", "language",
                 "human_approvals", "evidence_registry", "gap_registry"]:
        assert alan in durum


def test_onay_kapilari_yedi_adedir():
    assert len(APPROVAL_GATES) == 7
    assert APPROVAL_GATES[0] == "research_question"
    assert "final_thesis" in APPROVAL_GATES


def test_bos_durumda_hicbir_kapili_onalim_yok():
    durum = empty_state("THESIS-2026-001")
    assert all(deger is False for deger in durum["human_approvals"].values())


# Review Focus 2: eksik zorunlu alan sessizce varsayilan
# doldurulmamali, dogrulama hata vermeli.
def test_zorunlu_alan_eksikse_hata_verir():
    durum = empty_state("THESIS-2026-001")
    del durum["thesis_id"]
    hatalar = validate_state(durum)
    assert any("thesis_id" in hata for hata in hatalar)


def test_bilinmeyen_alan_reddedilir():
    durum = empty_state("THESIS-2026-001")
    durum["uydurma_alan"] = "deger"
    hatalar = validate_state(durum)
    assert any("uydurma_alan" in hata for hata in hatalar)


def test_sema_surumu_sabit():
    durum = empty_state("THESIS-2026-001")
    durum["schema_version"] = "2.0"
    hatalar = validate_state(durum)
    assert hatalar != []


def test_kimlik_bicimi_yanlis_kayit_reddedilir():
    durum = empty_state("THESIS-2026-001")
    durum["evidence_registry"].append({"id": "EVD-1"})  # iki hane yetersiz
    hatalar = validate_state(durum)
    assert hatalar != []


# Review Focus 4: registry'de olup kayit dosyasi olmayan varlik
# tespit edilebilmeli.
def test_kopuk_kanit_referansi_tespit_edilir():
    durum = empty_state("THESIS-2026-001")
    durum["evidence_registry"].append(
        {"id": "EVD-001", "source_id": "SRC-001", "location": {
            "page": 1, "section": "", "paragraph": None},
         "text": "x", "evidence_type": "finding",
         "supports_claim": None, "strength": "direct",
         "verified": False, "notes": ""}
    )
    kopuk = find_dangling_references(durum)
    assert any("EVD-001" in kopuk for kopuk in kopuk)


def test_kopuk_kanit_referansi_yoksa_bos_liste():
    durum = empty_state("THESIS-2026-001")
    assert find_dangling_references(durum) == []


def test_kaydet_yukle_gidis_donus(tmp_path):
    durum = empty_state("THESIS-2026-001", "Ornek Tez")
    durum["human_approvals"]["research_question"] = True
    yol = tmp_path / "durum.json"
    save_state(yol, durum)
    yuklenen = json.loads(yol.read_text(encoding="utf-8"))
    assert yuklenen["human_approvals"]["research_question"] is True


# Review Focus 5: onay durumu kaydedip yukleyince kaybolmamali.
def test_kaydet_yukle_onyan_korur(tmp_path):
    durum = empty_state("THESIS-2026-001")
    for kapili in ["research_question", "search_strategy", "methodology"]:
        durum["human_approvals"][kapili] = True
    yol = tmp_path / "durum.json"
    save_state(yol, durum)
    geri = validate_state(json.loads(yol.read_text(encoding="utf-8")))
    assert geri == []


def test_kaydet_bozuk_durumu_yazmaz(tmp_path):
    durum = empty_state("THESIS-2026-001")
    durum["schema_version"] = "bozuk"
    yol = tmp_path / "durum.json"
    try:
        save_state(yol, durum)
    except ValueError:
        pass
    else:
        raise AssertionError("save_state bozuk durumu yazmamaliydi")
    assert not yol.exists()


def test_sema_dosyasi_bulunamazsa_hata():
    try:
        load_schema("olmayan_sema.json")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Eksik sema icin FileNotFoundError bekleniyordu")
