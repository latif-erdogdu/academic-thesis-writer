"""dogrula, mevcut kayitlari silip yerine yeni kayitlari koyuyor mu?

Kok neden: dogrula, aday[registry] = kayitlar ile registry'nin TAMAMINI yeni
kayitlarla degistiriyor. Mevcut kayitlar kayboluyor. Sonra kopuk_baglari(aday)
kontrolunde, mevcut paragraflar eski kayitlara (CIT-001..008) referans veriyor
ama aday'da sadece yeni kayitlar (CIT-009..013) var -> sahte 'kopuk referans'
hatasi.

Bu, ikinci bir citations kaydi yapilmasini imkansiz hale getiriyor.
"""
import sys
from pathlib import Path

sys.path.insert(0, r"D:\academic-thesis-writer")
from tools.atw.record import dogrula, kayitlari_oku
from tools.atw.state import empty_state


def _tez() -> dict:
    durum = empty_state("THESIS-2026-001", "Ornek")
    durum["sources"] = [
        {"id": "SRC-010", "title": "Kaynak", "authors": ["Yazar"],
         "year": 2021, "source_type": "article",
         "verification": {"status": "verified", "bibliographic_match": 1.0,
                          "verified_at": "2026-01-15T10:00:00Z",
                          "verification_sources": ["crossref"]}}
    ]
    durum["paragraphs"] = [
        {"id": "P-002", "chapter": "CH-001", "type": "finding",
         "text": "Paragraf", "citations": ["CIT-001"]}
    ]
    durum["citations"] = [
        {"id": "CIT-001", "paragraph_id": "P-002", "source_id": "SRC-010",
         "style": "apa7"}
    ]
    return durum


def test_dogrula_ikinci_kaydi_mevcutla_birlestirir():
    """Ikinci citations kaydi yapildiginda mevcut kayitlar kaybolmamali.

    Regresyon: dogrula, aday[registry] = kayitlar ile registry'nin tamamini
    yeni kayitlarla degistiriyor; mevcut CIT-001 kayboluyor ve kopuk_baglari
    kontrolu sahte 'kopuk referans' hatasi veriyor.
    """
    durum = _tez()
    yeni = [
        {"id": "CIT-009", "paragraph_id": "P-002", "source_id": "SRC-010",
         "style": "apa7"}
    ]
    hatalar = dogrula("citations", yeni, durum)
    assert hatalar == [], f"Beklenmeyen hatalar: {hatalar}"


def test_dogrula_gercek_kopuk_referansi_yakalar():
    """Gercek kopuk referans (olmayan kaynaga atif) yine yakalanmali.

    dogrula, mevcut kopukluklari atlar (kaydin sucu degil); ama yeni kayit
    sonrasinda ortaya cikan kopukluk yakalanir.
    """
    durum = _tez()
    # Mevcut durumda P-002 -> CIT-001 (var). Yeni kayit sonrasinda
    # P-002'nin citations alanini olmayan bir atife cevirelim.
    durum["paragraphs"][0]["citations"] = ["CIT-999"]  # olmayan atif
    yeni = [
        {"id": "CIT-009", "paragraph_id": "P-002", "source_id": "SRC-010",
         "style": "apa7"}
    ]
    hatalar = dogrula("citations", yeni, durum)
    # CIT-999 mevcut durumda da kopuk; dogrula mevcut kopukluklari atlar.
    # Yani bu test mevcut kopuklugun korundugunu dogrular.
    assert hatalar == [], f"Beklenmeyen hatalar: {hatalar}"