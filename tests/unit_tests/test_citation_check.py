"""citation_check: metin↔kaynakça atıf bütünlüğü denetimi.

tools/citation_check/README.md'deki 7 denetim türünü kapsar:
kaynak varlığı, retraksiyon, terk (orphan), iddia desteği, APA 7 biçim,
sayfa numarası tutarlılığı.
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from tools.atw.state import SCHEMA_DIR, empty_state
from tools.citation_check import audit_citations, validate_apa7


# --- yardimcilar -------------------------------------------------------------

def _sema_yukle(ad: str) -> dict:
    """Kok sema dizininden sema yukler."""
    return json.loads((SCHEMA_DIR / f"{ad}.json").read_text(encoding="utf-8"))


def _dolu_durum() -> dict:
    """Atif denetimi icin kurgusal, semaya uygun durum.

    Alan adlari ve zorunlu alanlar semalardan birebir alinmistir.
    """
    durum = empty_state("THESIS-2026-001", "Ornek Tez")
    durum["sources"] = [
        {"id": "SRC-001", "title": "Kurgusal A", "source_type": "article",
         "verification": {"status": "verified", "bibliographic_match": 0.95,
                          "verified_at": "2026-09-26T10:12:00+00:00",
                          "verification_sources": ["crossref"]},
         "retraction_status": "not_retracted"},
        {"id": "SRC-002", "title": "Kurgusal B", "source_type": "article",
         "verification": {"status": "verified", "bibliographic_match": 0.91,
                          "verified_at": "2026-09-26T10:12:00+00:00",
                          "verification_sources": ["crossref"]},
         "retraction_status": "retracted"},
        {"id": "SRC-003", "title": "Terk edilecek kurgusal kaynak",
         "source_type": "article",
         "verification": {"status": "verified", "bibliographic_match": 0.88,
                          "verified_at": "2026-09-26T10:12:00+00:00",
                          "verification_sources": ["crossref"]},
         "retraction_status": "not_retracted"},
    ]
    durum["chapters"] = [
        {"id": "CH-002", "number": 2, "title": "Kuramsal Cerceve",
         "paragraphs": [{"id": "P-014", "type": "background",
                         "chapter": "CH-002", "section": "2.3"}]},
    ]
    durum["citations"] = [
        {"id": "CIT-001", "source_id": "SRC-001", "paragraph_id": "P-014",
         "style": "apa7", "in_text_form": "(Orman, 2020)"},
        {"id": "CIT-002", "source_id": "SRC-002", "paragraph_id": "P-014",
         "style": "apa7", "in_text_form": "(Kaya, 2021)"},
        {"id": "CIT-003", "source_id": "SRC-099", "paragraph_id": "P-014",
         "style": "apa7", "in_text_form": "(Hayalet, 2022)"},
    ]
    durum["claims_registry"] = [
        {"id": "CLM-001", "text": "Kurgusal", "importance": "high",
         "verification_status": "verified", "sources": ["SRC-001"],
         "evidence_ids": []},
        {"id": "CLM-002", "text": "Kanitsiz kurgusal iddia",
         "importance": "low", "verification_status": "unverified",
         "sources": ["SRC-002"], "evidence_ids": []},
    ]
    return durum


def _bulgu(rapor: dict, entity_id: str) -> dict:
    """Verilen entity_id'ye ait ilk bulguyu dondurur; yoksa hata verir."""
    eslesen = [b for b in rapor["findings"] if b.get("entity_id") == entity_id]
    assert eslesen, f"{entity_id} icin bulgu yok: {rapor['findings']}"
    return eslesen[0]


# --- sozlesme ---------------------------------------------------------------

def test_audit_citations_dosya_dondurur():
    """Denetim bir audit kaydi sozlugu dondurur."""
    rapor = audit_citations(_dolu_durum())
    assert isinstance(rapor, dict)
    assert rapor["audit_type"] == "citation"
    assert rapor["thesis_id"] == "THESIS-2026-001"


def test_audit_ciktisi_audit_semasina_uvar():
    """Denetim ciktisi audit.json semasina uymalidir (additionalProperties:false)."""
    rapor = audit_citations(_dolu_durum())
    jsonschema.Draft202012Validator(_sema_yukle("audit")).validate(rapor)


# --- denetim 1: kaynak varligi (critical) -----------------------------------

def test_kaynagi_olmayan_atif_kritik_bulgu():
    """sources registry'de olmayan kaynak atiflanmissa critical bulgu uretilir."""
    rapor = audit_citations(_dolu_durum())
    bulgu = _bulgu(rapor, "CIT-003")
    assert bulgu["severity"] == "critical"
    assert "SRC-099" in bulgu["message"]
    assert rapor["integrity_checks"]["fabricated_sources"] == 1


def test_kaynagi_olan_atif_kritik_bulgu_uretmez():
    """registry'de var olan kaynak icin kritik bulgu uretilmez."""
    rapor = audit_citations(_dolu_durum())
    kritikler = [b for b in rapor["findings"]
                 if b.get("entity_id") == "CIT-001" and b["severity"] == "critical"]
    assert kritikler == []


# --- denetim 2: retraksiyon (critical) --------------------------------------

def test_retrakte_kaynak_kritik_bulgu():
    """Retrakte edilmis kaynak atiflanmissa critical sayilir."""
    rapor = audit_citations(_dolu_durum())
    bulgu = _bulgu(rapor, "CIT-002")
    assert bulgu["severity"] == "critical"
    assert "retraksiyon" in bulgu["message"].lower()
    assert rapor["integrity_checks"]["retracted_sources_in_use"] == 1


# --- denetim 3: metinde atiflanmayan kaynak (major) ------------------------

def test_atiflanmamis_kaynak_terk_bulgu():
    """registry'de olup hic atiflanmayan kaynak major bulgu uretir."""
    rapor = audit_citations(_dolu_durum())
    bulgu = _bulgu(rapor, "SRC-003")
    assert bulgu["severity"] == "major"
    assert rapor["integrity_checks"]["orphaned_citations"] == 1


# --- denetim 4: iddia destegi (major) ---------------------------------------

def test_desteklenmeyen_iddia_bulgu():
    """verification_status=u olan iddia major bulgu uretir."""
    rapor = audit_citations(_dolu_durum())
    bulgu = _bulgu(rapor, "CLM-002")
    assert bulgu["severity"] == "major"
    assert rapor["integrity_checks"]["unsupported_claims"] == 1


# --- denetim 5: APA 7 bicim (minor) -----------------------------------------

def test_apa7_tek_yazar_parantez_dogrusu():
    """Tek yazarli parantez atfi APA 7 uyumlu olmalidir."""
    assert validate_apa7("(Orman, 2020)") == []


def test_apa7_iki_yazar_ve_ile_dogru():
    """Iki yazarli atif '&' veya Turkce 've' ile yazilabilir."""
    assert validate_apa7("(Orman & Kaya, 2020)") == []
    assert validate_apa7("(Orman ve Kaya, 2020)") == []


def test_apa7_iki_yazar_virgul_hatasi():
    """Iki yazarli atif virgulle ayrilmissa hata bildirilir."""
    sorunlar = validate_apa7("(Orman, Kaya, 2020)")
    assert len(sorunlar) == 1
    assert "2" in sorunlar[0] or "iki" in sorunlar[0].lower()


def test_apa7_uc_yazar_et_al_kurali():
    """Uc veya daha fazla yazar 'et al.' ile kisaltilmalidir."""
    assert validate_apa7("(Orman vd., 2020)") == []
    assert validate_apa7("(Orman et al., 2020)") == []
    sorunlar = validate_apa7("(Orman, Kaya, Aydin, 2020)")
    assert len(sorunlar) == 1
    assert "et al" in sorunlar[0].lower()


def test_apa7_bos_bicim_hata():
    """Bos in_text_form hata bildirmelidir."""
    assert len(validate_apa7("")) == 1


def test_apa7_yilsiz_bicim_hata():
    """Yil icermeyen atif bicimi hata bildirmelidir."""
    assert len(validate_apa7("(Orman)")) == 1


def test_apa7_bos_parca_hata():
    """Noktali virgulle ayrilmis bos atif parcasi hata bildirmelidir."""
    assert len(validate_apa7("(Orman, 2020); ")) == 1


def test_apa7_yazarsiz_bicim_hata():
    """Yil var ama yazar yoksa hata bildirmelidir."""
    sorunlar = validate_apa7("(2020)")
    assert len(sorunlar) == 1
    assert "Yazar" in sorunlar[0]


def test_apa7_coklu_atif_noktali_virgulle_ayrilir():
    """Noktali virgulle ayrilmis her girdi ayri denetlenir."""
    assert validate_apa7("(Orman, 2020; Kaya, 2021)") == []
    assert validate_apa7("(Orman vd., 2020; Kaya, 2021)") == []
    # Ikinci girdi iki yazarli ama virgulle ayrilmis -> tek bir sorun bildirilir.
    assert len(validate_apa7("(Orman, 2020; Kaya, Aydin, 2021)")) == 1


# --- denetim 6: sayfa numarasi (minor) --------------------------------------

def test_dogrudan_alintida_sayfa_zorunlu():
    """in_text_form'da sayfa varsa citation.page bos olamaz."""
    durum = _dolu_durum()
    durum["citations"][0]["in_text_form"] = "(Orman, 2020, s. 15)"
    rapor = audit_citations(durum)
    bulgu = _bulgu(rapor, "CIT-001")
    assert bulgu["severity"] == "minor"
    assert "s. 15" in bulgu["message"]


def test_sayfa_tutarli_birakildiginda_bulgu_yok():
    """in_text_form ve citation.page uyumlu ise sayfa bulgusu uretilmez."""
    durum = _dolu_durum()
    durum["citations"][0]["in_text_form"] = "(Orman, 2020, s. 15)"
    durum["citations"][0]["page"] = 15
    rapor = audit_citations(durum)
    assert not [b for b in rapor["findings"]
                if b.get("entity_id") == "CIT-001" and "s. 15" in b["message"]]


def test_sayfa_var_bicimde_lokator_yok_hata():
    """citation.page dolu ama in_text_form'de lokator yoksa hata bildirilir."""
    durum = _dolu_durum()
    durum["citations"][0]["page"] = 15
    rapor = audit_citations(durum)
    bulgu = _bulgu(rapor, "CIT-001")
    assert bulgu["severity"] == "minor"
    assert "lokator yok" in bulgu["message"]


def test_apa7_hatali_bicim_denetimde_karsilaniyor():
    """Denetimde APA 7 bicim hatalari minor bulgu olarak raporlanir."""
    durum = _dolu_durum()
    durum["citations"][0]["in_text_form"] = "(Orman, Kaya, 2020)"
    rapor = audit_citations(durum)
    bulgu = _bulgu(rapor, "CIT-001")
    assert bulgu["severity"] == "minor"
    assert "CIT-001" in bulgu["message"]
    assert any("CIT-001" in m for m in rapor["deferred_minors"])


def test_apa7_disi_stil_denetlenmez():
    """style=apa7 olmayan atif APA 7 denetimine girmez."""
    durum = _dolu_durum()
    durum["citations"][0]["style"] = "ieee"
    durum["citations"][0]["in_text_form"] = "[1]"
    rapor = audit_citations(durum)
    assert not [b for b in rapor["findings"] if b.get("entity_id") == "CIT-001"]


# --- temiz durum ------------------------------------------------------------

def test_temiz_durum_bulgu_uretmez():
    """Sorunsuz bir durumda hicbir bulgu uretilmemelidir."""
    durum = empty_state("THESIS-2026-002", "Temiz Tez")
    durum["sources"] = [
        {"id": "SRC-001", "title": "Kurgusal A", "source_type": "article",
         "verification": {"status": "verified", "bibliographic_match": 0.95,
                          "verified_at": "2026-09-26T10:12:00+00:00",
                          "verification_sources": ["crossref"]},
         "retraction_status": "not_retracted"},
    ]
    durum["citations"] = [
        {"id": "CIT-001", "source_id": "SRC-001", "paragraph_id": "P-014",
         "style": "apa7", "in_text_form": "(Orman, 2020)"},
    ]
    rapor = audit_citations(durum)
    assert rapor["findings"] == []
    assert rapor["critical_issues"] == []
    assert rapor["deferred_minors"] == []
    for sayac in rapor["integrity_checks"].values():
        assert sayac == 0
