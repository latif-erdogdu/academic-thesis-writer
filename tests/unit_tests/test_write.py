"""`thesis:write` yazari ajanina VERILERI brifing olarak vermeli ve
yazdigini denetlemeli.

Bulgu
-----
`cmd_write` stub idi:

    print("✍️  Bölüm yazımı: ...")
    print("⚠️  Henüz implemente edilmedi (agent/writer)")
    return 0

Yani `methodology` kapısını sorup geçiyor, hiçbir şey üretmeden 0
dönüyordu — `cmd_export`'ın stub'ıyla aynı hastalık.

Kapsam (kararlaştırıldı): **brifing + denetim.** CLI Türkçe metin
ÜRETMEZ; üretim `agents/writer.md` ajanının işidir. CLI'nin iki gerçek
işi var:

  1. **Brifing.** Ajanın çalışacağı DOĞRULANMIŞ girdi kümesini
     üretmek. `agents/writer.md` "Yazar sadece doğrulanmış girdilerle
     çalışır" diyor ama hangi kaynakların doğrulanmış olduğu tek bir
     yerde yazılı değil. Ajan `references[]`'tan okuyor; o dosyalar
     KURAL verir, bu tezin KAYITLARINI vermez.

  2. **Denetim.** Ajanın ürettiği bölüm dosyasını denetlemek, geçerse
     tez durumuna kaydetmek.

Politika uydurmamak
-------------------
Kurallar mevcut koddan türetildi; `references/` ya da " academically doğru"
diyerek yeni kural konmadı:

  * `writing_gate.py`: atıfın `source_id`'si `thesis_state.json`'da
    olmalı, `style` `apa7` olmalı. → Uydurma `SRC-999` reddi, APA dışı
    atıf reddi.
  * `evidence_gate.py`: bölüm dosyasında en az bir `CLM-` ve en az
    bir `EVD-`/`SRC-` referansı olmalı. → Hook katmanında kalır; burada
    TEKRAR UYGULANMAZ (bkz. `test_denetim_kanit_kanini_tekrar_uygulamaz`
    ve modül docstring'i).
  * `graph.kopuk_baglari`: tezdeki her referans çözülebilmeli.
  * `citation_check.audit_citations` `retracted_sources_in_use`: geri
    çekilmiş kaynakla atıf yapılmaz.
  * `schemas/*.json`: `chapter.json` / `paragraph.json` / `citation.json`
    tek doğruluk kaynağı.
  * `empty_state()` yorumu: `citation.paragraph_id` çözülebilmesi için
    `state["paragraphs"]` düz kayıtçısının dolu olması gerekir.

İki uydurma kuralı buraya BİLEREK girmedi: paragraf başına en az bir
iddia, ve her paragrafta en az bir kanıt. `evidence_gate.py` bunları
DOSYA düzeyinde ister; dosya düzeyini paragraf düzeyine taşımak yeni
politika olurdu.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.atw.state import empty_state
from tools.atw.write import (
    YAZIM_KURALLARI,
    YazimHatasi,
    bolum_dogrula,
    bolumu_kaydet,
    brifing_metni,
    brifing_uret,
)


# --- yardimcilar ------------------------------------------------------------

def _kaynak(kimlik: str, **ek) -> dict:
    """Varsayilan olarak DOGRULANMIS bir source kaydi uretir."""
    kaynak = {
        "id": kimlik,
        "title": "Kurgusal Bir Yontemin Etkinligi Uzerine Bir Inceleme",
        "authors": ["Orman, A."],
        "year": 2023,
        "source_type": "article",
        "retraction_status": "not_retracted",
        "verification": {
            "status": "verified",
            "bibliographic_match": 1.0,
            "verified_at": "2026-01-15T10:00:00Z",
            "verification_sources": ["crossref"],
        },
    }
    kaynak.update(ek)
    return kaynak


def _iddia(kimlik: str, **ek) -> dict:
    """Varsayilan olarak `verification_status: verified` bir claim uretir."""
    iddia = {
        "id": kimlik,
        "text": "Kurgusal iddia: incelenen yontem basariyi artirmaktadir.",
        "importance": "high",
        "evidence_ids": ["EVD-001"],
        "sources": ["SRC-001"],
        "verification_status": "verified",
    }
    iddia.update(ek)
    return iddia


def _kanit(kimlik: str, kaynak_id: str, **ek) -> dict:
    kanit = {
        "id": kimlik,
        "source_id": kaynak_id,
        "location": {"page": 17, "section": "3.2", "paragraph": None},
        "text": "Kurgusal alinti metni.",
        "evidence_type": "literature",
        "strength": "direct",
    }
    kanit.update(ek)
    return kanit


def _atif(kimlik: str, kaynak_id: str, paragraf_id: str, **ek) -> dict:
    atif = {
        "id": kimlik,
        "source_id": kaynak_id,
        "paragraph_id": paragraf_id,
        "style": "apa7",
    }
    atif.update(ek)
    return atif


def _soru(kimlik: str = "RQ-001", **ek) -> dict:
    soru = {
        "id": kimlik,
        "text": "Kurgusal arastirma sorusu: yontemin etkisi nedir?",
        "type": "main",
        "status": "answered",
    }
    soru.update(ek)
    return soru


def _paragraf(kimlik: str, metin: str, **ek) -> dict:
    p = {
        "id": kimlik,
        "chapter": "CH-002",
        "type": "methodology",
        "text": metin,
        "claims": ["CLM-001"],
        "evidence": ["EVD-001"],
        "sources": ["SRC-001"],
        "research_questions": ["RQ-001"],
    }
    p.update(ek)
    return p


def _bolum(kimlik: str = "CH-002", **ek) -> dict:
    bolum = {
        "id": kimlik,
        "number": 2,
        "title": "Yontem",
        "paragraphs": [_paragraf("P-010", "Sistematik tarama yontemi kullanildi.")],
    }
    bolum.update(ek)
    return bolum


def _tez(**ek) -> dict:
    """methodology kapisi acik, dogrulanmis girdisi olan temiz tez durumu."""
    durum = empty_state("THESIS-2026-001", "Ornek Tez")
    durum["research_questions"] = [_soru()]
    durum["sources"] = [_kaynak("SRC-001")]
    durum["claims_registry"] = [_iddia("CLM-001")]
    durum["evidence_registry"] = [_kanit("EVD-001", "SRC-001", supports_claim="CLM-001")]
    durum["citations"] = [_atif("CIT-010", "SRC-001", "P-010")]
    durum["human_approvals"]["methodology"] = True
    durum.update(ek)
    return durum


# =============================================================================
# 1) BRIFING: yalnizca DOGRULANMIS girdi
# =============================================================================

def test_brifing_dogrulanmis_kaynagi_verir():
    brifing = brifing_uret(_tez(), "CH-002", "RQ-001")
    assert [k["id"] for k in brifing["kaynaklar"]] == ["SRC-001"]


def test_brifing_dogrulanmamis_kaynagi_dahil_etmez():
    """`verification.status != verified` olan kaynak ajana VERILMEZ.

    Yazarin bu kaynaga uzanmamasi icin: kayit hem verilmez hem de
    `haric_tutulanlar` icinde nedeniyle listelenir.
    """
    durum = _tez()
    durum["sources"].append(
        _kaynak("SRC-002", verification={
            "status": "pending",
            "bibliographic_match": 0.4,
            "verified_at": "2026-01-15T10:00:00Z",
            "verification_sources": ["crossref"],
        })
    )
    brifing = brifing_uret(durum, "CH-002", "RQ-001")

    assert [k["id"] for k in brifing["kaynaklar"]] == ["SRC-001"]
    haric = {k["id"]: k["neden"] for k in brifing["haric_tutulanlar"]["kaynaklar"]}
    assert "SRC-002" in haric
    assert "pending" in haric["SRC-002"], f"neden durum degerini vermeli: {haric}"


def test_brifing_retraksiyonlu_kaynagi_dahil_etmez():
    """Geri cekilmis kaynak brifingde YER ALMAZ.

    `citation_check.audit_citations` bunu `retracted_sources_in_use`
    (critical) sayiyor; brifing ayni karari yansitir.
    """
    durum = _tez()
    durum["sources"].append(
        _kaynak("SRC-002", retraction_status="retracted")
    )
    brifing = brifing_uret(durum, "CH-002", "RQ-001")

    assert [k["id"] for k in brifing["kaynaklar"]] == ["SRC-001"]
    haric = {k["id"] for k in brifing["haric_tutulanlar"]["kaynaklar"]}
    assert "SRC-002" in haric


def test_brifing_yalnizca_dogrulanmis_iddialari_verir():
    brifing = brifing_uret(_tez(), "CH-002", "RQ-001")
    assert [i["id"] for i in brifing["iddialar"]] == ["CLM-001"]


def test_brifing_dogrulanmamis_iddiayi_dahil_etmez():
    durum = _tez()
    durum["claims_registry"].append(
        _iddia("CLM-002", verification_status="pending", evidence_ids=[])
    )
    brifing = brifing_uret(durum, "CH-002", "RQ-001")

    assert [i["id"] for i in brifing["iddialar"]] == ["CLM-001"]
    haric = {i["id"]: i["neden"] for i in brifing["haric_tutulanlar"]["iddialar"]}
    assert "CLM-002" in haric
    assert "pending" in haric["CLM-002"], haric


def test_brifing_celis_kili_iddiayi_dahil_etmez():
    """Celiskili iddia brifinge girmez; celiski taraflari da haric kalir.

    `graph.celiskili_iddialar` bir celiskide IKI tarafi da isaretler
    (satir 402-404: `sonuc.add(kimlik); sonuc.add(diger)`). Bu test o
    olcumu tekrar kullanir; daha dar bir kural uydurmak ayni kaynaga
    ikinci, daha gevsek bir politika koymak olurdu.
    """
    durum = _tez()
    durum["claims_registry"].append(_iddia("CLM-002", evidence_ids=[]))
    durum["claims_registry"].append(
        _iddia("CLM-003", evidence_ids=[], contradicted_by=["CLM-002"])
    )
    brifing = brifing_uret(durum, "CH-002", "RQ-001")

    assert [i["id"] for i in brifing["iddialar"]] == ["CLM-001"]
    haric = {i["id"] for i in brifing["haric_tutulanlar"]["iddialar"]}
    assert {"CLM-002", "CLM-003"} <= haric, haric


def test_brifing_celiskinin_diger_tarafi_da_haric_tutulur():
    """Celiskinin `contradicted_by` YAN tarafi da yazim girdisi degil.

    Bunu ayri test yapiyoruz cunku sezgilere aykiridir: CLM-001,
    CLM-002'ye celiskili oldugu icin CLM-001'i de eleyen bir kural,
    okuyan kisi icin beklenmedik gelir.
    """
    durum = _tez()
    durum["claims_registry"].append(
        _iddia("CLM-002", evidence_ids=[], contradicted_by=["CLM-001"])
    )
    brifing = brifing_uret(durum, "CH-002", "RQ-001")

    assert [i["id"] for i in brifing["iddialar"]] == []
    haric = {i["id"] for i in brifing["haric_tutulanlar"]["iddialar"]}
    assert {"CLM-001", "CLM-002"} <= haric, haric


def test_brifing_retraksiyonlu_kaynaga_dayanan_iddiayi_dahil_etmez():
    """Geri cekilmis kaynaga dayanan iddia yazim girdisi olamaz."""
    durum = _tez()
    durum["sources"].append(_kaynak("SRC-002", retraction_status="retracted"))
    durum["claims_registry"].append(
        _iddia("CLM-002", sources=["SRC-002"], evidence_ids=[])
    )
    brifing = brifing_uret(durum, "CH-002", "RQ-001")

    assert [i["id"] for i in brifing["iddialar"]] == ["CLM-001"]
    haric = {i["id"] for i in brifing["haric_tutulanlar"]["iddialar"]}
    assert "CLM-002" in haric


def test_brifing_kaniti_bagli_oldugu_iddiaya_ait_verir():
    """Kanit yalnizca onayli iddiaya bagliysa brifinge girer."""
    durum = _tez()
    durum["evidence_registry"].append(
        _kanit("EVD-002", "SRC-001", supports_claim="CLM-999")
    )
    brifing = brifing_uret(durum, "CH-002", "RQ-001")

    assert [k["id"] for k in brifing["kanitlar"]] == ["EVD-001"]


def test_brifing_arastirma_sorusunu_kaydeder():
    brifing = brifing_uret(_tez(), "CH-002", "RQ-001")
    assert brifing["arastirma_sorusu"]["id"] == "RQ-001"
    assert brifing["arastirma_sorusu"]["text"]


def test_brifing_bilinmeyen_rq_da_hata_verir():
    """Olmayan RQ ile brifing uretilmez.

    `cmd_search` ayni durumda yalnizca uyari basip BOS PICO ile devam
    ediyor. Yazimda bu bir hata: RQ'suz brifing, ajanin hangi soruyu
    yanitlayacagini bilmedigi bir cift yazim talimatidir.
    """
    with pytest.raises(YazimHatasi, match="RQ-999"):
        brifing_uret(_tez(), "CH-002", "RQ-999")


def test_brifing_yeni_bolum_icin_iskelet_verir():
    """Bölüm henüz durumda yoksa brifing onu SIFATLA belirtir.

    Hata degil: `write CH-005` ilk kez calisiyor olabilir.
    """
    brifing = brifing_uret(_tez(), "CH-005", "RQ-001")
    assert brifing["bolum"]["id"] == "CH-005"
    assert brifing["bolum"]["var"] is False
    assert brifing["bolum"]["title"] in (None, "")


def test_brifing_var_olan_bolumu_basligiyla_verir():
    durum = _tez(chapters=[_bolum()])
    brifing = brifing_uret(durum, "CH-002", "RQ-001")
    assert brifing["bolum"]["var"] is True
    assert brifing["bolum"]["title"] == "Yontem"


# =============================================================================
# 2) BRIFING METNI: ajanin okudugu sozlesme
# =============================================================================

def test_brifing_metni_kimlikleri_yazar():
    """Ajanin kullanabilecegi her kimlik metinde AÇIKÇA yer alir.

    Kimligi metinde olmayan bir kaynak/iddia ajanin kullanimina
    sunulmus sayilmaz; bu yuzden hepsi yazilir.
    """
    metin = brifing_metni(brifing_uret(_tez(), "CH-002", "RQ-001"))
    for kimlik in ("CH-002", "RQ-001", "CLM-001", "EVD-001", "SRC-001"):
        assert kimlik in metin, f"brifing metninde {kimlik} yok"


def test_brifing_metni_kurallari_yazar():
    metin = brifing_metni(brifing_uret(_tez(), "CH-002", "RQ-001"))
    for kural in YAZIM_KURALLARI:
        assert kural in metin


def test_brifing_metni_haric_tutulanlari_nedeniyle_yazar():
    """Ajan neye UZANAMADIGINI da bilmeli.

    Yalnizca "kaynak yok" demek, ajanin ayni kaynagi tez durumundan
    bulup kullanmasina yol acar. Neden yazilmazsa ayni hata tekrarlar.
    """
    durum = _tez()
    durum["sources"].append(
        _kaynak("SRC-002", verification={
            "status": "unverified",
            "bibliographic_match": 0.0,
            "verified_at": "2026-01-15T10:00:00Z",
            "verification_sources": ["crossref"],
        })
    )
    metin = brifing_metni(brifing_uret(durum, "CH-002", "RQ-001"))
    assert "SRC-002" in metin
    assert "unverified" in metin


# =============================================================================
# 3) DOGRULAMA: uydurma kimlik
# =============================================================================

def test_gecerli_bolum_hatasiz_dogrulanir():
    assert bolum_dogrula(_bolum(), _tez(), "CH-002", "RQ-001") == []


def test_brifing_rq_suz_bolum_icin_uretilir():
    """RQ'suz bolum (giris/literatur/yontem/sonuc) brifing uretebilmeli.

    Regresyon: brifing_uret, rq_id None geldiyse YazimHatasi firlatiyordu;
    bu yuzden giris/literatur/yontem/sonuc bolumleri yazilamiyordu.
    """
    brifing = brifing_uret(_tez(), "CH-004", None)
    assert brifing["arastirma_sorusu"] is None
    assert [k["id"] for k in brifing["kaynaklar"]] == ["SRC-001"]


def test_dogrulama_rq_suz_bolumde_soru_kontrolunu_atlar():
    """RQ'suz bolumde RQ-mention kontrolu yapilmamali.

    Regresyon: _soru_hatalari, rq_id None iken cokuyordu; RQ'suz bolum
    RQ anmasa da hata veriyordu.
    """
    bolum = _bolum()
    bolum["id"] = "CH-004"
    bolum["paragraphs"][0]["chapter"] = "CH-004"
    assert bolum_dogrula(bolum, _tez(), "CH-004", None) == []


def test_bolum_kimligi_istendikle_ayni_olmali():
    """`write CH-002` cagrisi CH-003 dosyasini kabul etmemeli.

    Ajan yanlis dosyayi yazmis olabilir; kaydetmek tezi sessizce
    yanlis bolumle degistirirdi.
    """
    hatalar = bolum_dogrula(_bolum("CH-003"), _tez(), "CH-002", "RQ-001")
    assert any("CH-002" in h and "CH-003" in h for h in hatalar), hatalar


def test_bolum_numarasi_zorunlu():
    bolum = _bolum()
    bolum.pop("number")
    hatalar = bolum_dogrula(bolum, _tez(), "CH-002", "RQ-001")
    assert any("number" in h for h in hatalar), hatalar


def test_sema_ihlali_reddedilir():
    """`paragraph.type` enum disi deger: sema ihlali."""
    bolum = _bolum(paragraphs=[_paragraf("P-010", "Metin.", type="uydurma_tur")])
    hatalar = bolum_dogrula(bolum, _tez(), "CH-002", "RQ-001")
    assert any("type" in h for h in hatalar), hatalar


def test_uydurma_kaynak_kimligi_reddedilir():
    """`SRC-999` tezde yok: Writing Gate'in kurali, CANLI duruma gore.

    Hook bu kontrolu dosya yaziminda yapar; burada durum degismis olabilir
    (kaynak silinmis). Iki katman ayni seyi farkli anda dogrular.
    """
    bolum = _bolum(paragraphs=[_paragraf("P-010", "Metin.", sources=["SRC-999"])])
    hatalar = bolum_dogrula(bolum, _tez(), "CH-002", "RQ-001")
    assert any("SRC-999" in h for h in hatalar), hatalar


def test_uydurma_iddia_kimligi_reddedilir():
    bolum = _bolum(paragraphs=[_paragraf("P-010", "Metin.", claims=["CLM-999"])])
    hatalar = bolum_dogrula(bolum, _tez(), "CH-002", "RQ-001")
    assert any("CLM-999" in h for h in hatalar), hatalar


def test_uydurma_kanit_kimligi_reddedilir():
    bolum = _bolum(paragraphs=[_paragraf("P-010", "Metin.", evidence=["EVD-999"])])
    hatalar = bolum_dogrula(bolum, _tez(), "CH-002", "RQ-001")
    assert any("EVD-999" in h for h in hatalar), hatalar


def test_uydurma_atif_kimligi_reddedilir():
    bolum = _bolum(paragraphs=[_paragraf("P-010", "Metin.", citations=["CIT-999"])])
    hatalar = bolum_dogrula(bolum, _tez(), "CH-002", "RQ-001")
    assert any("CIT-999" in h for h in hatalar), hatalar


def test_retraksiyonlu_kaynagi_atif_reddedilir():
    """Kaynak sonradan geri cekildiyse yazim onaylanmaz."""
    durum = _tez()
    durum["sources"].append(_kaynak("SRC-002", retraction_status="retracted"))
    bolum = _bolum(paragraphs=[
        _paragraf("P-010", "Metin.", sources=["SRC-002"], citations=["CIT-011"])
    ])
    durum["citations"].append(_atif("CIT-011", "SRC-002", "P-010"))
    hatalar = bolum_dogrula(bolum, durum, "CH-002", "RQ-001")
    assert any("SRC-002" in h and "retraksiyon" in h.lower() for h in hatalar), hatalar


def test_apa7_disi_atif_reddedilir():
    durum = _tez()
    durum["citations"].append(_atif("CIT-011", "SRC-001", "P-010", style="ieee"))
    bolum = _bolum(paragraphs=[_paragraf("P-010", "Metin.", citations=["CIT-011"])])
    hatalar = bolum_dogrula(bolum, durum, "CH-002", "RQ-001")
    assert any("apa7" in h.lower() for h in hatalar), hatalar


# =============================================================================
# 4) DOGRULAMA: paragraf metadata'si
# =============================================================================

def test_paragraf_metni_bos_olamaz():
    """Bos metinli paragraf, icerik kaybi; `export` bunu zaten reddediyor.

    Burada kabul edilseydi kayit duruma girer ve hataci ancak
    disa aktarimda gorulurdi.
    """
    bolum = _bolum(paragraphs=[_paragraf("P-010", "   ")])
    hatalar = bolum_dogrula(bolum, _tez(), "CH-002", "RQ-001")
    # "boş" seçildi: "metin"/"metni" gibi sözcükler Türkçe ünlü düşmesiyle
    # değiştiği için ("metin" ⊄ "metni") tek biçimli bir eşleşme değil.
    assert any("P-010" in h and "boş" in h for h in hatalar), hatalar


def test_paragraf_bolum_geri_baglantisi_yanlis():
    """`paragraph.chapter` yanlis bolumu gosteriyorsa kayit yaniltici.

    `graph.kopuk_baglari` bunu kopuk kenar olarak yakalar; burada
    kullaniciya daha anlamli mesaj verilir.
    """
    bolum = _bolum(paragraphs=[_paragraf("P-010", "Metin.", chapter="CH-009")])
    hatalar = bolum_dogrula(bolum, _tez(), "CH-002", "RQ-001")
    assert any("P-010" in h and "CH-009" in h for h in hatalar), hatalar


def test_paragraf_kimlikleri_tekrar_edemez():
    bolum = _bolum(paragraphs=[
        _paragraf("P-010", "Birinci."),
        _paragraf("P-010", "İkinci."),
    ])
    hatalar = bolum_dogrula(bolum, _tez(), "CH-002", "RQ-001")
    assert any("P-010" in h and "tekrar" in h.lower() for h in hatalar), hatalar


def test_paragraf_id_bicimi_sema_kuralidir():
    bolum = _bolum(paragraphs=[_paragraf("P10", "Metin.")])
    hatalar = bolum_dogrula(bolum, _tez(), "CH-002", "RQ-001")
    assert any("P10" in h for h in hatalar), hatalar


def test_bolum_istendigi_arastirma_sorusunu_anmali():
    """`write CH-002 --rq RQ-001` cagrisi, bolumun RQ-001'i ANMASINI ister.

    Bu kural komutun KENDI imzasi kaynakli: `--rq` verilmesi, "bu
    bolum bu soruyu yanitlasin" demektir. hicbir paragraf RQ-001'i
    anmiyorsa bolum baska bir soruyu yanitliyordur.
    """
    bolum = _bolum(paragraphs=[
        _paragraf("P-010", "Metin.", research_questions=["RQ-002"])
    ])
    hatalar = bolum_dogrula(bolum, _tez(), "CH-002", "RQ-001")
    assert any("RQ-001" in h for h in hatalar), hatalar


def test_bilinmeyen_arastirma_sorusu_hata_verir():
    hatalar = bolum_dogrula(_bolum(), _tez(), "CH-002", "RQ-999")
    assert any("RQ-999" in h for h in hatalar), hatalar


def test_bolum_bos_paragrafla_gecerlidir():
    """Paragrafsiz bolum gecerli: yazi henuz baslamamis olabilir."""
    assert bolum_dogrula(_bolum(paragraphs=[]), _tez(), "CH-002", "RQ-001") == []


def test_bos_baslik_reddedilir():
    hatalar = bolum_dogrula(_bolum(title=""), _tez(), "CH-002", "RQ-001")
    assert any("baslik" in h.lower() or "title" in h.lower() for h in hatalar), hatalar


# =============================================================================
# 5) KAYIT: bölüm ve paragraflar
# =============================================================================

def test_bolum_duruma_kaydedilir():
    durum = _tez()
    bolumu_kaydet(durum, _bolum())
    assert [b["id"] for b in durum["chapters"]] == ["CH-002"]


def test_paragraf_duz_kayitciya_yazilir():
    """Paragraf AYRICA `state["paragraphs"]` icine yazilir.

    `citation.paragraph_id` bu duz kayitciya cozunur. `empty_state()`
    yorumu bunu acikca belirtir: kayitci bos kalirsa atiflarin paragraf
    referansi COZUMSUZ kalir ve butunluk denetimi kalici olarak kopuk
    referans bildirir.
    """
    durum = _tez()
    bolumu_kaydet(durum, _bolum())
    assert [p["id"] for p in durum["paragraphs"]] == ["P-010"]


def test_ayni_bolum_yeniden_yazilir():
    """Ikinci yazim cogaltmaz, bolumu degistirir."""
    durum = _tez()
    bolumu_kaydet(durum, _bolum())
    bolumu_kaydet(durum, _bolum(paragraphs=[_paragraf("P-011", "Yeni metin.")]))
    assert [b["id"] for b in durum["chapters"]] == ["CH-002"]
    assert [p["id"] for p in durum["chapters"][0]["paragraphs"]] == ["P-011"]


def test_kayitta_kalmayan_eski_paragraf_temizlenir():
    """Bolumden silinen paragraf duz kayitcida da silinir.

    Aksi halde `P-010` kayitli kalir ve `CIT-010` onu cozumlemeye
    devam eder; bolumde olmayan bir paragrafa atif birakmis oluruz.
    """
    durum = _tez()
    bolumu_kaydet(durum, _bolum())
    bolumu_kaydet(durum, _bolum(paragraphs=[_paragraf("P-011", "Yeni metin.")]))
    assert [p["id"] for p in durum["paragraphs"]] == ["P-011"]


def test_baska_bolumun_paragraflari_korunur():
    """Yalnizca YAZILAN bolumun duz kayitlari degisir."""
    durum = _tez()
    bolumu_kaydet(durum, _bolum("CH-001", paragraphs=[
        _paragraf("P-001", "Giris metni.", chapter="CH-001")
    ]))
    bolumu_kaydet(durum, _bolum("CH-002"))
    assert {p["id"] for p in durum["paragraphs"]} == {"P-001", "P-010"}


def test_kayittan_sonra_atif_paragraf_referansi_cozulur():
    """Kayit sonrasi butunluk denetiminde KOPUK atif referansi kalmaz.

    `graph.kopuk_baglari` turetilmis bir olcum: `citation.paragraph_id`
    gercekten cozuluyor mu, dogrudan onun ciktisina bakilir.
    """
    from tools.atw import graph

    durum = _tez()
    bolumu_kaydet(durum, _bolum())
    kopuk = graph.kopuk_baglari(durum)
    atif_kopukleri = [k for k in kopuk if "CIT-010" in k or "paragraph_id" in k]
    assert atif_kopukleri == [], atif_kopukleri


# =============================================================================
# 6) CLI
# =============================================================================

@pytest.fixture
def cli_tesi(tmp_path, monkeypatch):
    from tools.atw.cli import main as cli

    monkeypatch.setattr(cli, "VERI_KOKU", tmp_path)
    return cli


def _cli_durumunu_yaz(durum: dict, dizin: Path) -> None:
    (dizin / "thesis_state.json").write_text(
        json.dumps(durum, ensure_ascii=False), encoding="utf-8"
    )


def test_cli_write_brifing_yazar_ve_duruma_dokunmaz(cli_tesi, tmp_path, capsys):
    """`--file` verilmedikce brifing uretilir, durum DEGISTIRILMEZ.

    Yazim ajaninin isidir; CLI yalnizca girdiyi verir.
    """
    _cli_durumunu_yaz(_tez(), tmp_path)
    args = cli_tesi.build_parser().parse_args(["write", "CH-002", "--rq", "RQ-001"])

    cikis = cli_tesi.cmd_write(args)

    assert cikis == cli_tesi.CIKIS_OK
    cikti = capsys.readouterr().out
    for kimlik in ("CLM-001", "EVD-001", "SRC-001"):
        assert kimlik in cikti
    kayitli = json.loads((tmp_path / "thesis_state.json").read_text(encoding="utf-8"))
    assert kayitli["chapters"] == []


def test_cli_write_json_brifing_dokumler(cli_tesi, tmp_path, capsys):
    """`--json` ile brifing MAKINE-OKUNUR basar.

    Ajan metin kazimak yerine sozlesmeyi okusun diye.
    """
    _cli_durumunu_yaz(_tez(), tmp_path)
    args = cli_tesi.build_parser().parse_args(
        ["write", "CH-002", "--rq", "RQ-001", "--json"]
    )

    assert cli_tesi.cmd_write(args) == cli_tesi.CIKIS_OK

    brifing = json.loads(capsys.readouterr().out)
    assert brifing["arastirma_sorusu"]["id"] == "RQ-001"
    assert [k["id"] for k in brifing["kaynaklar"]] == ["SRC-001"]


def test_cli_write_dosyayi_dogrular_ve_kaydeder(cli_tesi, tmp_path, capsys):
    bolum_dosyasi = tmp_path / "CH-002.json"
    bolum_dosyasi.write_text(
        json.dumps(_bolum(), ensure_ascii=False), encoding="utf-8"
    )
    _cli_durumunu_yaz(_tez(), tmp_path)
    args = cli_tesi.build_parser().parse_args(
        ["write", "CH-002", "--rq", "RQ-001", "--file", str(bolum_dosyasi)]
    )

    cikis = cli_tesi.cmd_write(args)

    assert cikis == cli_tesi.CIKIS_OK, capsys.readouterr().out
    kayitli = json.loads((tmp_path / "thesis_state.json").read_text(encoding="utf-8"))
    assert [b["id"] for b in kayitli["chapters"]] == ["CH-002"]
    assert [p["id"] for p in kayitli["paragraphs"]] == ["P-010"]


def test_cli_write_hatali_dosyada_kaydetmez(cli_tesi, tmp_path, capsys):
    """Reddedilen bolum duruma GIRMEZ; dosya yerinde kalir.

    Ajanin dosyasi elle duzeltilip tekrar denenir; yarim kayit birakmak
    tezi iki bolumlu/eksik gosterirdi.
    """
    bolum_dosyasi = tmp_path / "CH-002.json"
    bolum_dosyasi.write_text(
        json.dumps(_bolum(paragraphs=[_paragraf("P-010", "Metin.", sources=["SRC-999"])]),
                   ensure_ascii=False),
        encoding="utf-8",
    )
    _cli_durumunu_yaz(_tez(), tmp_path)
    args = cli_tesi.build_parser().parse_args(
        ["write", "CH-002", "--rq", "RQ-001", "--file", str(bolum_dosyasi)]
    )

    cikis = cli_tesi.cmd_write(args)

    assert cikis == cli_tesi.CIKIS_SORUN
    assert "SRC-999" in capsys.readouterr().out
    kayitli = json.loads((tmp_path / "thesis_state.json").read_text(encoding="utf-8"))
    assert kayitli["chapters"] == []
    assert kayitli["paragraphs"] == []


# =============================================================================
# 7) BOZUK GIRDİ: çökme değil, anlamlı red
# =============================================================================

def test_bozuk_registry_alani_yoksayilir():
    """`sources` liste değilse sessizce boş sayılır, çökmez.

    `thesis_state.json` semasi bunu zaten reddeder; buradaki amaç
    brifingin bir bozuk durumla da metin üretmeye devam etmesi.
    """
    durum = _tez()
    durum["sources"] = "bozuk"
    brifing = brifing_uret(durum, "CH-002", "RQ-001")
    assert brifing["kaynaklar"] == []


def test_kimligsiz_kayit_atlanir():
    durum = _tez()
    durum["sources"].append({"title": "kimliksiz"})
    brifing = brifing_uret(durum, "CH-002", "RQ-001")
    assert [k["id"] for k in brifing["kaynaklar"]] == ["SRC-001"]


def test_kimligsiz_iddia_ve_kanit_atlanir():
    durum = _tez()
    durum["claims_registry"].append({"text": "kimliksiz iddia"})
    durum["evidence_registry"].append({"text": "kimliksiz kanit"})
    brifing = brifing_uret(durum, "CH-002", "RQ-001")
    assert [i["id"] for i in brifing["iddialar"]] == ["CLM-001"]
    assert [k["id"] for k in brifing["kanitlar"]] == ["EVD-001"]


def test_kanit_iddiaya_bagli_degilse_haric_tutulur():
    """`supports_claim` olmayan kanıt yazıma girmez."""
    durum = _tez()
    durum["evidence_registry"].append(_kanit("EVD-002", "SRC-001"))
    brifing = brifing_uret(durum, "CH-002", "RQ-001")

    assert [k["id"] for k in brifing["kanitlar"]] == ["EVD-001"]
    haric = {k["id"]: k["neden"] for k in brifing["haric_tutulanlar"]["kanitlar"]}
    assert "supports_claim" in haric["EVD-002"]


def test_kanitin_kaynagi_yazilabilir_degilse_haric_tutulur():
    """Kanıtın kaynağı brifinge girmiyorsa kanıt da giremez.

    Aksi halde brifing, ajana verilmemiş bir kaynak kimliğini
    `source_id` alanından sızdırırdı.
    """
    durum = _tez()
    durum["sources"].append(_kaynak("SRC-002", verification={
        "status": "pending",
        "bibliographic_match": 0.1,
        "verified_at": "2026-01-15T10:00:00Z",
        "verification_sources": ["crossref"],
    }))
    durum["evidence_registry"].append(
        _kanit("EVD-002", "SRC-002", supports_claim="CLM-001")
    )
    brifing = brifing_uret(durum, "CH-002", "RQ-001")

    assert [k["id"] for k in brifing["kanitlar"]] == ["EVD-001"]
    haric = {k["id"]: k["neden"] for k in brifing["haric_tutulanlar"]["kanitlar"]}
    assert "SRC-002" in haric["EVD-002"]


def test_brifing_metni_bos_registry_lerde_yer_tutar():
    """Doğrulanmış hiçbir kaynağı olmayan tezde metin boş kalmaz."""
    durum = empty_state("THESIS-2026-001", "Bos Tez")
    durum["research_questions"] = [_soru()]
    metin = brifing_metni(brifing_uret(durum, "CH-002", "RQ-001"))
    assert "yazılabilir doğrulanmış iddia yok" in metin
    assert "yazılabilir kanıt yok" in metin
    assert "yazılabilir doğrulanmış kaynak yok" in metin


def test_brifing_metni_soru_yontemini_yazar():
    durum = _tez(research_questions=[_soru(method="Kurgusal yontem")])
    metin = brifing_metni(brifing_uret(durum, "CH-002", "RQ-001"))
    assert "Kurgusal yontem" in metin


def test_brifing_metni_kayitli_bolumun_detayini_yazar():
    durum = _tez(chapters=[_bolum(goal="Kurgusal amaç")])
    metin = brifing_metni(brifing_uret(durum, "CH-002", "RQ-001"))
    assert "numara: 2" in metin
    assert "Yontem" in metin
    assert "Kurgusal amaç" in metin


def test_brifing_metni_doi_yazar():
    """DOI brifingte yazılır: atıf biçimi için gerekli."""
    durum = _tez(sources=[_kaynak("SRC-001", doi="10.1000/xyz")])
    metin = brifing_metni(brifing_uret(durum, "CH-002", "RQ-001"))
    assert "10.1000/xyz" in metin


def test_bolum_kimligi_yoksa_hata():
    bolum = _bolum()
    bolum.pop("id")
    hatalar = bolum_dogrula(bolum, _tez(), "CH-002", "RQ-001")
    assert any("kimlik" in h for h in hatalar), hatalar


def test_paragraphs_liste_degilse_denetleme_bozulmaz():
    """`paragraphs` bir sözcükse çökmez, yalnızca paragraf denetimleri atlanır."""
    bolum = _bolum(paragraphs="bozuk")
    hatalar = bolum_dogrula(bolum, _tez(), "CH-002", "RQ-001")
    assert any("paragraphs" in h for h in hatalar), hatalar


def test_paragraf_nesnesi_degilse_belirtilir():
    bolum = _bolum(paragraphs=["metin", _paragraf("P-010", "Geçerli.")])
    hatalar = bolum_dogrula(bolum, _tez(), "CH-002", "RQ-001")
    assert any("JSON nesnesi" in h for h in hatalar), hatalar


def test_bilinmeyen_varlik_tipi_cozumlenemez_olarak_isaretlenir():
    """`graph.registry_haritasi()` bilmediği bir tip için yer tutucu döner.

    Yer tutucu sessiz "hiçbir referans çözülemez" gibi davranır: bilinmeyen
    bir referans alanı eklendiğinde denetim onu UYDURMA sayar ve yazar
    durdurulur. Sessizce geçmekten iyidir.
    """
    from tools.atw.write import _kayitci_adi

    assert _kayitci_adi("claim") == "claims_registry"
    assert _kayitci_adi("bilinmeyen_tip").startswith("__cozulmeyen_tip__")


def test_atifin_kaynagi_tezde_yoksa_erken_cikilir():
    """Atıfın `source_id`'si tezde yoksa stil dışı başka hata da bildirilmez."""
    durum = _tez()
    durum["citations"].append(_atif("CIT-011", "SRC-999", "P-010"))
    bolum = _bolum(paragraphs=[_paragraf("P-010", "Metin.", citations=["CIT-011"])])
    hatalar = bolum_dogrula(bolum, durum, "CH-002", "RQ-001")
    # Kaynak eksikliği `_referans_hatalari`'nde "uydurulmuş olabilir" olarak
    # bildirilir; burada tekrarlanmaz.
    assert not any("SRC-999" in h and "atıf CIT-011" in h for h in hatalar), hatalar


def test_dogrulanmamis_kaynaga_atif_reddedilir():
    """Brifing yalnızca doğrulanmış kaynak verir; doğrulanmamışı atıflamak brifinge aykırı."""
    durum = _tez()
    durum["sources"].append(_kaynak("SRC-002", verification={
        "status": "unverified",
        "bibliographic_match": 0.0,
        "verified_at": "2026-01-15T10:00:00Z",
        "verification_sources": ["crossref"],
    }))
    durum["citations"].append(_atif("CIT-011", "SRC-002", "P-010"))
    bolum = _bolum(paragraphs=[_paragraf("P-010", "Metin.", citations=["CIT-011"])])
    hatalar = bolum_dogrula(bolum, durum, "CH-002", "RQ-001")
    assert any("SRC-002" in h and "doğrulanmamış" in h for h in hatalar), hatalar


def test_atif_bu_bolumun_disindaki_paragrafa_bagli_olamaz():
    """`citation.paragraph_id` bölümde olmayan bir paragrafı gösteriyorsa reddedilir.

    Aksi halde bölüm, kendi paragraflarında kullanmadığı bir atfı
    sahiplenirdi.
    """
    durum = _tez()
    durum["citations"].append(_atif("CIT-011", "SRC-001", "P-777"))
    bolum = _bolum(paragraphs=[_paragraf("P-010", "Metin.", citations=["CIT-011"])])
    hatalar = bolum_dogrula(bolum, durum, "CH-002", "RQ-001")
    assert any("CIT-011" in h and "P-777" in h for h in hatalar), hatalar


def test_atif_kimligi_metin_degilse_cokmez():
    """`citations` içinde sayı varsak çökmez.

    Şema zaten reddeder (`^CIT-\\d{3,}$`); buradaki amaç, reddeden
    katmanın bir `TypeError` ile değil bir mesajla durması.
    """
    bolum = _bolum(paragraphs=[_paragraf("P-010", "Metin.", citations=[123])])
    hatalar = bolum_dogrula(bolum, _tez(), "CH-002", "RQ-001")
    assert any("citations" in h for h in hatalar), hatalar


def test_kayitta_bolum_nesnesi_degilse_yoksayilir():
    """`chapters` içinde bozuk bir giriş varsa kayıt onu ezmez."""
    durum = _tez(chapters=["bozuk", _bolum()])
    bolumu_kaydet(durum, _bolum("CH-002", paragraphs=[]))
    assert [b["id"] for b in durum["chapters"] if isinstance(b, dict)] == ["CH-002"]


def test_cli_write_cozulmemis_sablon_yolu_brifing_kipinde_kalir(cli_tesi, tmp_path, capsys):
    """`--file` için `--file {options.file}` geçerse brifing kipi seçilir.

    `skill.yaml` handler'ı `write {args[0]} --rq {options.rq} --file
    {options.file}` biçiminde. Depo, seçenek verilmediğinde çalıştırma
    katmanının bu şablonu ATIP atmak yerine olduğu gibi geçirdiğini
    belgelemiyor (aynı kalıp `thesis:verify --all {options.all}` ve
    `thesis:extract --pdf {options.pdf}` içinde de var).

    Çözülmemiş `{...}` bir yol DEĞİLDİR. Onu dosya adı sanmak
    "Bölüm dosyası bulunamadı: {options.file}" demek, yani kullanıcı
    hiç brifing istemediği halde ikinci kip devreye girer.
    """
    _cli_durumunu_yaz(_tez(), tmp_path)
    args = cli_tesi.build_parser().parse_args(
        ["write", "CH-002", "--rq", "RQ-001", "--file", "{options.file}"]
    )

    cikis = cli_tesi.cmd_write(args)

    assert cikis == cli_tesi.CIKIS_OK
    cikti = capsys.readouterr().out
    assert "BRİFİNG" in cikti, cikti
    assert "bulunamadı" not in cikti, cikti


def test_cli_write_olmayan_dosyada_kaydetmez(cli_tesi, tmp_path, capsys):
    _cli_durumunu_yaz(_tez(), tmp_path)
    args = cli_tesi.build_parser().parse_args(
        ["write", "CH-002", "--rq", "RQ-001", "--file", str(tmp_path / "yok.json")]
    )

    cikis = cli_tesi.cmd_write(args)

    assert cikis == cli_tesi.CIKIS_SORUN
    assert "yok.json" in capsys.readouterr().out


def test_cli_write_bozuk_json_reddedilir(cli_tesi, tmp_path, capsys):
    bolum_dosyasi = tmp_path / "CH-002.json"
    bolum_dosyasi.write_text("{bozuk", encoding="utf-8")
    _cli_durumunu_yaz(_tez(), tmp_path)
    args = cli_tesi.build_parser().parse_args(
        ["write", "CH-002", "--rq", "RQ-001", "--file", str(bolum_dosyasi)]
    )

    cikis = cli_tesi.cmd_write(args)

    assert cikis == cli_tesi.CIKIS_SORUN
    assert "JSON" in capsys.readouterr().out


def test_cli_write_kapi_kapaliyken_engellenir(cli_tesi, tmp_path, capsys):
    """`methodology` kapisi kapaliyken ne brifing ne kayit uretilir.

    Yontem onayi olmadan yazilan bolum, sonradan yontem degisince
    gecersizlesir; yazmadan once kapi sorulmasi bunun icin.
    """
    durum = _tez()
    durum["human_approvals"]["methodology"] = False
    _cli_durumunu_yaz(durum, tmp_path)
    args = cli_tesi.build_parser().parse_args(["write", "CH-002", "--rq", "RQ-001"])

    cikis = cli_tesi.cmd_write(args)

    assert cikis == cli_tesi.CIKIS_SORUN
    assert "methodology" in capsys.readouterr().out


def test_parser_write_rq_opsiyonel():
    """--rq opsiyonel; RQ'suz bolum (giris/literatur/yontem/sonuc) yazilabilir.

    Degisim: --rq artik zorunlu degil. RQ'suz bolumler (front/back matter)
    yazilabilmeli; bu yuzden parser --rq'siz de calismali.
    """
    from tools.atw.cli.main import build_parser

    args = build_parser().parse_args(["write", "CH-004"])
    assert args.chapter == "CH-004"
    assert args.rq is None


def test_parser_write_file_bayragi_kayitli():
    from tools.atw.cli.main import build_parser

    args = build_parser().parse_args(
        ["write", "CH-002", "--rq", "RQ-001", "--file", "a.json", "--json"]
    )
    assert args.file == "a.json"
    assert args.json is True
