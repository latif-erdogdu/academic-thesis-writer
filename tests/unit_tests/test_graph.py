"""S4: Kanıt grafiği sorgu katmanı — kenar tablosu, registry, kopuk bağ, zincirler."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.atw import graph
from tools.atw.state import SCHEMA_DIR, empty_state, find_dangling_references


def _dolu_durum() -> dict:
    """Tüm varlık tiplerini temsil eden kurgusal bir durum.

    Alan adları ve zorunlu alanlar semalardan birebir alınmıştır.
    """
    durum = empty_state("THESIS-2026-001", "Örnek Tez")
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
    ]
    durum["research_questions"] = [
        {"id": "RQ-001", "text": "Kurgusal soru?", "type": "main",
         "status": "answered", "related_claims": ["CLM-001"]},
    ]
    durum["chapters"] = [
        {"id": "CH-002", "number": 2, "title": "Kuramsal Çerçeve",
         "paragraphs": [{"id": "P-014", "type": "background",
                         "chapter": "CH-002", "section": "2.3"}]},
    ]
    durum["citations"] = [
        {"id": "CIT-001", "source_id": "SRC-001", "paragraph_id": "P-014",
         "style": "apa7"},
    ]
    durum["evidence_registry"] = [
        {"id": "EVD-001", "text": "Kurgusal", "source_id": "SRC-001",
         "location": {"page": 3}, "evidence_type": "literature",
         "strength": "direct", "supports_claim": "CLM-001"},
        {"id": "EVD-002", "text": "Kurgusal", "source_id": "SRC-002",
         "location": {"page": 7}, "evidence_type": "literature",
         "strength": "direct", "supports_claim": "CLM-002"},
    ]
    durum["claims_registry"] = [
        {"id": "CLM-001", "text": "Kurgusal", "importance": "high",
         "verification_status": "verified", "sources": ["SRC-001"],
         "evidence_ids": ["EVD-001"]},
        {"id": "CLM-002", "text": "Kurgusal", "importance": "medium",
         "verification_status": "verified", "sources": ["SRC-002"],
         "evidence_ids": ["EVD-002"]},
        {"id": "CLM-003", "text": "Kanıtsız kurgusal", "importance": "low",
         "verification_status": "unverified", "evidence_ids": []},
    ]
    durum["findings_registry"] = [
        {"id": "FND-001", "rq_id": "RQ-001", "statement": "Kurgusal",
         "evidence_ids": ["EVD-001"]},
    ]
    durum["audit_registry"] = [
        {"audit_id": "AUD-001", "thesis_id": "THESIS-2026-001",
         "audit_type": "integrity", "date": "2026-09-26", "findings": []},
    ]
    return durum


# --- kenar tablosu -----------------------------------------------------------

def test_kenar_tablosu_bos_degil():
    assert len(graph.kenar_tablosu()) > 0


def test_kenar_tablosu_oncebellekli():
    """Aynı nesne dönmelidir; önbellek işe yaramazsa tablo her
    çağrıda yeniden türetilir ve testler yavaşlar."""
    assert graph.kenar_tablosu() is graph.kenar_tablosu()


def test_kimlik_alanlari_kenara_girmez():
    """Kaydın kendi kimliği referans değildir."""
    alanlar = {k.alan_adi for k in graph.kenar_tablosu()}
    assert "id" not in alanlar
    assert "audit_id" not in alanlar


def test_tablodaki_her_alan_semada_var():
    """Tablo ⊆ sema."""
    semalar = {p.stem: json.loads(p.read_text(encoding="utf-8"))
               for p in sorted(SCHEMA_DIR.glob("*.json"))}
    hatalar = []
    for kenar in graph.kenar_tablosu():
        sema = semalar[kenar.kayit_tipi]
        deger = sema
        for parca in kenar.alan_adi.split("."):
            if not isinstance(deger, dict):
                deger = None
                break
            props = deger.get("properties")
            if props is None and deger.get("type") == "array":
                props = (deger.get("items") or {}).get("properties")
            if props is None:
                deger = None
                break
            deger = props.get(parca)
            if deger is None:
                hatalar.append(f"{kenar.kayit_tipi}.{kenar.alan_adi}")
                break
    assert not hatalar, "Tablodaki alanlar semada yok: " + ", ".join(hatalar)


def test_semadaki_her_referans_alani_tabloda():
    """Sema ⊆ tablo. İki yönlü ölçeklemeden biri sessizce geçer."""
    tablo = {(k.kayit_tipi, k.alan_adi) for k in graph.kenar_tablosu()}
    semalar = {p.stem: json.loads(p.read_text(encoding="utf-8"))
               for p in sorted(SCHEMA_DIR.glob("*.json"))}
    eksikler = []
    for sema_adi, sema in semalar.items():
        if sema_adi == "thesis_state":
            continue
        for alan_yolu, _coklu, _hedef in graph._referans_alanlari(sema):
            if alan_yolu in graph._KIMLIK_ALANLARI:
                continue
            if (sema_adi, alan_yolu) not in tablo:
                eksikler.append(f"{sema_adi}.{alan_yolu}")
    assert not eksikler, "Tabloda olmayan referans alanları: " + ", ".join(eksikler)


def test_kenar_sayisi_semadan_turetilir():
    """Sabit sayı değil, semadan türetilen sayı kullanılır. Yeni sema
    eklendiğinde bu kriter kendiliğinden geçerli kalir.

    Karşılaştırma tablo ile bağımsız bir sayım arasındadır: her sema için
    doğrudan sayılır, sonra tabloyla karşılaştırılır.
    """
    semalar = graph._semalari()
    dogrudan = [
        (sema_adi, alan_yolu)
        for sema_adi, sema in semalar.items()
        if "$schema" in sema and sema_adi != "thesis_state"
        for alan_yolu, _coklu, _hedef in graph._referans_alanlari(sema)
        if alan_yolu not in graph._KIMLIK_ALANLARI
    ]
    tablo = {(k.kayit_tipi, k.alan_adi) for k in graph.kenar_tablosu()}
    assert tablo == set(dogrudan)


def test_registry_haritasi_gercekci_sayi():
    """Harita elle yazılmamış, 19 alan türetir. Elle yazılan
    ``_REGISTRY_FIELDS`` 15'tir ve 4'ünü kaçırır."""
    harita = graph.registry_haritasi()
    assert len(harita) == 19
    for alan in ("research_questions", "hypotheses", "chapters", "variables"):
        assert alan in harita, f"{alan} haritada yok: kopuk bağlar yanlış alarm verir"


def test_registry_haritasi_tum_dizileri_kapsar():
    """thesis_state'teki her ``$ref`` dizisi registry'dir."""
    sema = graph._semalari()["thesis_state"]
    beklenen = {
        alan for alan, t in (sema.get("properties") or {}).items()
        if isinstance(t, dict) and isinstance(t.get("items"), dict)
        and isinstance(t["items"].get("$ref"), str)
    }
    assert set(graph.registry_haritasi()) == beklenen


def test_bicim_kurallari_kenara_girmez():
    """``source.doi`` ve ``figure.image_path`` desen taşır ama önek
    içermez; bunlar biçim kuralıdır, kimlik referansı değildir."""
    alanlar = {(k.kayit_tipi, k.alan_adi) for k in graph.kenar_tablosu()}
    assert ("source", "doi") not in alanlar
    assert ("figure", "image_path") not in alanlar


def test_thesis_id_kenar_degildir():
    """``audit.thesis_id`` desen taşımaz. Bu doğru: ``thesis_id``
    (``THESIS-2026-001``) bir registry varlığı değil, tezin kendi
    serbest biçimli kimliğidir. Desen eklenmemeli - eklenirse her
    audit kaydı kopuk bildirilir."""
    alanlar = {(k.kayit_tipi, k.alan_adi) for k in graph.kenar_tablosu()}
    assert ("audit", "thesis_id") not in alanlar


# --- kopuk bağ denetimi ------------------------------------------------------

def test_bos_durumde_kopuk_bag_yok():
    assert graph.kopuk_baglari(empty_state("THESIS-2026-001", "Örnek")) == []


def test_bos_sozluk_kirmaz():
    """Eksik durum KeyError fırlatmamalı (Review Focus 4)."""
    assert graph.kopuk_baglari({}) == []


def test_null_registry_kirmaz():
    """Alan null ise .get(alan, []) devreye girmez; None atar (Review Focus 4)."""
    durum = empty_state("THESIS-2026-001", "Örnek")
    durum["sources"] = None
    durum["evidence_registry"] = None
    assert graph.kopuk_baglari(durum) == []


def test_dolu_durumun_kendisi_tutarli():
    """Kritik: örnek durumda HİÇBİR kopuk bağ olmamalı.

    Bu test kırmızı dönerse ya kenar tablosu yanlış üretiliyor ya da
    registry haritası eksik. Biri değilse diğeri bozuk demektir."""
    kopuk = graph.kopuk_baglari(_dolu_durum())
    assert not kopuk, "Örnek durumda kopuk var: " + "; ".join(kopuk)


def test_paragraph_ici_kayitlar_denetleniyor():
    """Paragraf üst düzey registry değil, ``chapter.paragraphs[]`` içinde
    yaşıyor. İç içe indeksleme olmazsa bu kayıtlar hiç gezilmez."""
    durum = _dolu_durum()
    assert "P-014" in graph._var_mi(durum, "paragraph")


def test_citation_paragraph_id_denetleniyor():
    """``citation.paragraph_id`` yalnızca iç içe indekslemeyle denetlenir."""
    durum = _dolu_durum()
    durum["citations"][0]["paragraph_id"] = "P-999"
    kopuk = graph.kopuk_baglari(durum)
    assert any("P-999" in k for k in kopuk), kopuk


def test_kendi_kimligi_kopuk_sayilmaz():
    """F18 regresyonu: ``audit_id`` bir referans değil, audit kaydının
    kendi kimliğidir. Kenara girerse her audit kaydı kopuk bildirilir."""
    durum = _dolu_durum()
    durum["audit_registry"][0]["audit_id"] = "AUD-002"
    kopuk = graph.kopuk_baglari(durum)
    assert not any("AUD-002" in k for k in kopuk), kopuk


def test_coklu_alan_kopugu_bulunuyor():
    """claim.evidence_ids daha önce hiç denetlenmiyordu."""
    durum = _dolu_durum()
    durum["claims_registry"][0]["evidence_ids"] = ["EVD-999"]
    kopuk = graph.kopuk_baglari(durum)
    assert any("EVD-999" in k for k in kopuk), kopuk


def test_ozel_adli_bag_kopugu_bulunuyor():
    """evidence.supports_claim daha önce hiç denetlenmiyordu."""
    durum = _dolu_durum()
    durum["evidence_registry"][0]["supports_claim"] = "CLM-999"
    assert any("CLM-999" in k for k in graph.kopuk_baglari(durum))


def test_ara_soru_kopugu_bulunuyor():
    """finding.rq_id: registry haritası ``research_questions``'i
    kaçırırsa bu alan HİÇBİR zaman denetlenmez."""
    durum = _dolu_durum()
    durum["findings_registry"][0]["rq_id"] = "RQ-999"
    assert any("RQ-999" in k for k in graph.kopuk_baglari(durum))


def test_variable_claim_ids_kopugu_bulunuyor():
    """variable.claim_ids: S2'de eklendi, registry haritası ``variables``
    kapsadığından denetlenmeli."""
    durum = _dolu_durum()
    durum["variables"] = [{"id": "VAR-001", "claim_ids": ["CLM-999"]}]
    assert any("CLM-999" in k for k in graph.kopuk_baglari(durum))


def test_variable_dataset_ids_kopugu_bulunuyor():
    """variable.dataset_ids: S2'de eklendi."""
    durum = _dolu_durum()
    durum["variables"] = [{"id": "VAR-001", "dataset_ids": ["DS-999"]}]
    assert any("DS-999" in k for k in graph.kopuk_baglari(durum))


def test_hypothesis_finding_ids_kopugu_bulunuyor():
    """hypothesis.finding_ids: S2'de eklendi."""
    durum = _dolu_durum()
    durum["hypotheses"] = [{"id": "HYP-001", "finding_ids": ["FND-999"]}]
    assert any("FND-999" in k for k in graph.kopuk_baglari(durum))


def test_hypothesis_related_rq_kopugu_bulunuyor():
    """hypothesis.related_research_questions: S2'de eklendi."""
    durum = _dolu_durum()
    durum["hypotheses"] = [{"id": "HYP-001", "related_research_questions": ["RQ-999"]}]
    assert any("RQ-999" in k for k in graph.kopuk_baglari(durum))


def test_sarmalayici_geriye_uyumlu():
    durum = _dolu_durum()
    assert find_dangling_references(durum) == graph.kopuk_baglari(durum)


# --- sorgular ----------------------------------------------------------------

def test_source_kullanan_iddialar():
    durum = _dolu_durum()
    assert graph.source_kullanan_iddialar(durum, "SRC-001") == ["CLM-001"]


def test_iddianin_dayandigi_kaynaklar_kaynaga_indirger():
    durum = _dolu_durum()
    assert graph.iddiyanin_dayandigi_kaynaklar(durum, "CLM-001") == ["SRC-001"]


def test_bulgunun_kanit_zinciri():
    durum = _dolu_durum()
    zincir = graph.bulgunun_kanit_zinciri(durum, "FND-001")
    turler = [(z.adim, z.kimlik) for z in zincir]
    assert ("bulgu", "FND-001") in turler
    assert ("kanit", "EVD-001") in turler
    assert ("iddia", "CLM-001") in turler
    assert ("kaynak", "SRC-001") in turler


def test_rq_dan_kaynakca():
    """Araştırma sorusundan kaynakçaya uzanan zincir.

    Yön önemli: ``claim.json``'de bir araştırma sorusu alanı **yoktur**.
    Bağ ``research_question.related_claims`` ile ters yönde kurulur.
    """
    durum = _dolu_durum()
    turler = [(z.adim, z.kimlik) for z in graph.rq_dan_kaynakca(durum, "RQ-001")]
    assert ("soru", "RQ-001") in turler
    assert ("iddia", "CLM-001") in turler
    assert ("kaynak", "SRC-001") in turler


def test_retraksiyona_ugrayan_iddialar():
    """Review Focus 5: geri çekilmiş kaynağı kullanan iddia."""
    durum = _dolu_durum()
    assert graph.retraksiyona_ugrayan_iddialar(durum) == ["CLM-002"]


def test_retraksiyon_yoksa_bos_liste():
    durum = _dolu_durum()
    durum["sources"][1]["retraction_status"] = "not_retracted"
    assert graph.retraksiyona_ugrayan_iddialar(durum) == []


def test_kanitsiz_iddialar():
    assert graph.kanitsiz_iddialar(_dolu_durum()) == ["CLM-003"]


def test_celiskili_iddialar():
    durum = _dolu_durum()
    durum["claims_registry"][0]["contradicted_by"] = ["CLM-002"]
    assert graph.celiskili_iddialar(durum) == ["CLM-001", "CLM-002"]


def test_kenar_turleri_ikili():
    turler = {k.tur for k in graph.kenar_tablosu()}
    assert turler <= {graph.YAPISAL, graph.ANLAMSAL}
    assert turler == {graph.YAPISAL, graph.ANLAMSAL}


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-p", "no:cacheprovider"])