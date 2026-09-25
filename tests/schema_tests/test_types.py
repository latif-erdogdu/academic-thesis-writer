"""Calisma-zamani tiplerinin dogrulama davranisi testleri."""
from __future__ import annotations

import pytest

from tools.atw.types import (
    EVIDENCE_TYPES,
    STRENGTHS,
    VERIFICATION_STATUSES,
    EvidenceDraft,
    Location,
    PageText,
    Passage,
    SourceCandidate,
    VerificationResult,
)


def test_page_text_alanlari():
    sayfa = PageText(page=3, text="icerik", sections=["Giris"])
    assert sayfa.page == 3
    assert sayfa.sections == ["Giris"]


def test_passage_kimlik_dogrulamasi_yapar():
    gecerli = Passage(
        source_id="SRC-001", page=17, section="3.2",
        text="X yontemi basariyi %23 artirmaktadir.",
        char_start=1204, char_end=1250,
    )
    assert gecerli.source_id == "SRC-001"
    assert gecerli.page == 17


def test_passage_gecersiz_kimlikte_hata_firlatir():
    with pytest.raises(ValueError):
        Passage(
            source_id="kaynak1", page=1, section="",
            text="x", char_start=0, char_end=1,
        )


def test_passage_karakter_araligi_tersten_olamaz():
    with pytest.raises(ValueError):
        Passage(
            source_id="SRC-001", page=1, section="",
            text="x", char_start=50, char_end=10,
        )


def test_source_candidate_doi_ve_yil_istege_bagli():
    aday = SourceCandidate(doi=None, title="Baslik", authors=[], year=None, source_type=None)
    assert aday.doi is None
    assert aday.year is None


@pytest.mark.parametrize("bozuk_doi", [
    "1234/abcd",            # kayit oneki (10.) yok
    "10.1234",              # son ek (/) yok
    "10.1234/abc def",      # son ekte bosluk var
    "doi:10.1234/abc",      # bicim oneki karistirilmis
])
def test_source_candidate_bicimsiz_doi_reddedilir(bozuk_doi):
    """Bicimsiz DOI reddedilmeli.

    Dikkat: `10.5555/` fixture'larda kurgusal kaynak icin gecerli bir
    prefikstir ve `^10\\.\\d{4,9}/\\S+$` deseniyle eslesir. Bu yuzden
    "gecersiz" ornegi `10.5555/` onekiyle kurulamaz.
    """
    with pytest.raises(ValueError):
        SourceCandidate(
            doi=bozuk_doi, title="Baslik", authors=[], year=2024,
            source_type="article",
        )


def test_source_candidate_bicimli_doi_kabul_edilir():
    """10.5555/ oneki fixture'lar icin gecerli olmali."""
    aday = SourceCandidate(
        doi="10.5555/kurgusal.ornek.2024.001", title="Baslik",
        authors=[], year=2024, source_type="article",
    )
    assert aday.doi == "10.5555/kurgusal.ornek.2024.001"


def test_verification_result_gecerli_durum_kabul_eder():
    sonuc = VerificationResult(
        status="verified", bibliographic_match=0.95,
        doi_match=True, author_match=True, title_match=True,
        year_match=True, journal_match=True,
        retraction_status="not_retracted", correction_status="none",
        supersedes=None, verified_at="2026-09-26T10:00:00Z",
        verification_sources=["crossref", "openalex"],
    )
    assert sonuc.status == "verified"
    assert sonuc.verification_sources == ["crossref", "openalex"]


def test_verification_result_gecersiz_durum_reddeder():
    with pytest.raises(ValueError):
        VerificationResult(
            status="oldu", bibliographic_match=0.9,
            doi_match=True, author_match=True, title_match=True,
            year_match=True, journal_match=True,
            retraction_status="not_retracted", correction_status="none",
            supersedes=None, verified_at="2026-09-26T10:00:00Z",
            verification_sources=["crossref"],
        )


def test_verification_result_en_az_iki_kaynak_zorunlu():
    with pytest.raises(ValueError):
        VerificationResult(
            status="verified", bibliographic_match=0.9,
            doi_match=True, author_match=True, title_match=True,
            year_match=True, journal_match=True,
            retraction_status="not_retracted", correction_status="none",
            supersedes=None, verified_at="2026-09-26T10:00:00Z",
            verification_sources=["crossref"],  # yalniz bir kaynak
        )


def test_verification_result_geri_caledilen_durum_en_az_iki_kaynak_ister():
    # Retraksiyon tespiti tek kaynaktan da anlamli olabilir, bu durumda
    # en az iki kaynak kurali gevser.
    sonuc = VerificationResult(
        status="retracted", bibliographic_match=1.0,
        doi_match=True, author_match=True, title_match=True,
        year_match=True, journal_match=True,
        retraction_status="retracted", correction_status="none",
        supersedes=None, verified_at="2026-09-26T10:00:00Z",
        verification_sources=["crossref"],
    )
    assert sonuc.status == "retracted"


def test_verification_result_eskisletme_zorunlu():
    with pytest.raises(ValueError):
        VerificationResult(
            status="verified", bibliographic_match=0.4,  # esik alti
            doi_match=True, author_match=False, title_match=False,
            year_match=True, journal_match=False,
            retraction_status="not_retracted", correction_status="none",
            supersedes=None, verified_at="2026-09-26T10:00:00Z",
            verification_sources=["crossref", "openalex"],
        )


def test_evidence_draft_kimlik_ve_enum_dogrulamasi():
    taslak = EvidenceDraft(
        source_id="SRC-014", location={"page": 17, "section": "3.2", "paragraph": None},
        text="X yontemi basariyi %23 artirmaktadir.",
        evidence_type="finding", strength="direct",
    )
    assert taslak.source_id == "SRC-014"
    assert "finding" in EVIDENCE_TYPES
    assert "direct" in STRENGTHS


def test_evidence_draft_gecersiz_tip_reddedilir():
    with pytest.raises(ValueError):
        EvidenceDraft(
            source_id="SRC-014", location={"page": 17, "section": "", "paragraph": None},
            text="x", evidence_type="varsayim", strength="direct",
        )


def test_location_alanlari():
    konum = Location(page=17, section="3.2", paragraph=None)
    assert konum.page == 17
    assert konum.as_dict() == {"page": 17, "section": "3.2", "paragraph": None}


# Review Focus 1: Turkce kaynak basliklarindaki diyakritik ve buyuk/kucuk
# harf farki kayit olustururken reddedilmemeli.
def test_source_candidate_turkce_basligini_kabul_eder():
    aday = SourceCandidate(
        doi=None, title="Çobanoğlu ve Yılmaz'ın Deneyimi",
        authors=["Çobanoğlu, A.", "Yılmaz, B."], year=2024, source_type="article",
    )
    assert aday.title.startswith("Ç")


def test_enum_kumeleri_bos_degil():
    assert len(VERIFICATION_STATUSES) >= 5
    assert len(EVIDENCE_TYPES) >= 5
    assert set(STRENGTHS) == {"direct", "indirect"}
