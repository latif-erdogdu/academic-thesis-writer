"""Onay kaydi, icerik ozeti (hash), bagimlilik grafigi ve ret dongusu testleri.

Kapsam
------
`tests/unit_tests/test_approval.py` eski `bool` tabanli API'yi sinar.
Buradaki testler YENI sozlesmeyi sinar; kanonik dokuman
`references/approval_gates.md` dosyasidir.

Onay kaydi
    `human_approvals[kapı]` ya `true`/`false` (eski) ya da onay nesnesidir.
    Nesne `approved_by`, `approved_at`, `content_hash`, `comment`,
    `rejection_reason`, `audit_refs`, `revision` alanlarini tasir.

Icerik ozeti (immutable onay)
    Onay aninda kapsanan icerigin SHA-256 ozeti saklanir. Icerik sonradan
    degisirse `kapi_acik_mi` `False` doner. Bu, "onaylandi ama sonra metin
    degisti" durumunu kapatir.

Bagimlilik grafigi
    Kapilar siraya degil acik bagimlilik listesine dayanir.

Denetim / onay ayrimi
    `thesis:audit` gecmesi onay DEGILDIR. `final_thesis` kapisi icin
    bes denetim turunun de gecmis olmasi ve hicbirinde `critical` bulgu
    bulunmamasi gerekir; bu kosul `kontrol_yaz` uzerinden zorlanir.
"""
from __future__ import annotations

import copy

import pytest

from tools.atw.approval import (
    GATE_BAGIMLILIK,
    GATE_KOSULLARI,
    OnayHatasi,
    bagimlilik_engelleri,
    denetim_gereksinimleri,
    icerik_ozeti,
    kapi_acik_mi,
    kapi_detay,
    kontrol_yaz,
    onay_geri_al,
    onay_reddet,
    onay_stale_mi,
    onay_ver,
    temizle,
)
from tools.atw.state import APPROVAL_GATES, empty_state

# --- yardimcilar -------------------------------------------------------------


def _onay_izni(sozlesme) -> None:
    """Bir onayi denetim gereksinimleri DEGISMEDEN acabilir hale getirir.

    `onay_ver` denetimleri zorunlu TUTMAZ; onlar `kontrol_yaz` yolunda
    sorgulanir. Testler onayin kendisini denetlemek istedigi icin
    gerekli denetim kayitlarini once hazirlar.
    """
    for tur in sozlesme.denetim_turleri:
        if not any(k.get("audit_type") == tur for k in _denetimler):
            _denetimler.append(_denetim(tur))


def _denetim(tur: str, bulgular=None) -> dict:
    bulgular = bulgular if bulgular is not None else []
    return {
        "audit_id": "AUD-%03d" % (len(_denetimler) + 1),
        "thesis_id": "THESIS-2026-999",
        "audit_type": tur,
        "date": "2026-09-30",
        "findings": bulgular,
    }


_denetimler: list[dict] = []


@pytest.fixture(autouse=True)
def _denetimleri_temizle():
    _denetimler.clear()
    yield
    _denetimler.clear()


def _durum() -> dict:
    d = empty_state("THESIS-2026-999", "Sınama Tezi")
    d["audit_registry"] = copy.deepcopy(_denetimler)
    return d


def _onaya_hazir(durum: dict, kapi: str) -> dict:
    """Kapinin on kosullarini saglar, kapinin kendisini acmaz.

    Kayitlar kendi SEMALARINA UYGUNDUR. Once kucuk sahte kayitlar
    (`{"id": "RQ-001", "question": "S?"}`) kullaniliyordu; `onay_ver`
    artik on kosulu kayit duzeyinde denetledigi icin bu kayitlar kapilari
    acmiyordu. Kural su: bir test fixture'i, uretimde yazilamayacak bir
    durum uretmemelidir. Yazilabilir degilse o kayit gercekten hatadir.
    """
    dolu = {
        "research_question": ("research_questions", {
            "id": "RQ-001", "text": "Soru metni?", "type": "main", "status": "pending",
        }),
        "search_strategy": ("search_runs", {
            "id": "SEARCH-001", "database": "crossref", "query": "kurgusal sorgu",
            "timestamp": "2026-09-30T09:00:00+00:00", "results_returned": 1,
            "inclusion_criteria": ["akademik makale"], "exclusion_criteria": ["derleme"],
            "prisma_flow": {
                "records_identified": 1, "duplicates_removed": 0, "records_screened": 1,
                "records_excluded": 0, "reports_sought": 1, "reports_excluded": 0,
                "studies_included": 1,
            },
        }),
        "source_set": ("sources", {
            "id": "SRC-001", "title": "Baslik", "doi": "10.1234/ornek",
            "source_type": "article", "verified": True,
            "retraction_status": "not_retracted",
            "verification": {
                "status": "verified", "bibliographic_match": 1.0,
                "verified_at": "2026-09-30T09:00:00+00:00",
                "verification_sources": ["crossref"],
            },
        }),
        "research_gap": ("gap_registry", {
            "id": "GAP-001", "statement": "Bosluk beyani",
            "gap_type": "unanswered_question",
            "evidence_ids": ["EVD-001"], "supporting_source_ids": ["SRC-001"],
            "confidence": "high",
        }),
        "findings": ("findings_registry", {
            "id": "FND-001", "rq_id": "RQ-001", "statement": "Bulgu beyani",
            "evidence_ids": ["EVD-001"],
        }),
    }
    # Kanit kaydi. `gap_registry.evidence_ids` ve
    # `findings_registry.evidence_ids` bu kaydi gosterir; kayit
    # YAZILMAZDIGI bir kapi acilamiyor, cunku `final_thesis` on kosulu
    # butunluk taramasinda kopuk referansi gercek bir hatadir.
    kanit = {
        "id": "EVD-001",
        "source_id": "SRC-001",
        "location": {"page": 1, "section": "3.1", "paragraph": None},
        "text": "Kurgusal alinti metni.",
        "evidence_type": "literature",
        "strength": "direct",
    }

    for gecilen in _kapi_yolu(kapi):
        if gecilen in dolu:
            alan, kayit = dolu[gecilen]
            durum[alan] = [copy.deepcopy(kayit)]
            if alan in ("gap_registry", "findings_registry"):
                durum["evidence_registry"] = [copy.deepcopy(kanit)]
        _denetimler.extend([])
        for tur in GATE_KOSULLARI[gecilen].denetim_turleri:
            if not any(k.get("audit_type") == tur for k in _denetimler):
                _denetimler.append(_denetim(tur))
        durum["audit_registry"] = copy.deepcopy(_denetimler)
        onay_ver(durum, gecilen, onaylayan="Danışman")
    if kapi in dolu:
        alan, kayit = dolu[kapi]
        durum[alan] = [copy.deepcopy(kayit)]
    durum["audit_registry"] = copy.deepcopy(_denetimler)
    return durum


def _kapi_yolu(kapi: str) -> list[str]:
    """`kapi`ye giden bagimlilik yolunu kapı sirasiyla dondurur."""
    yol: list[str] = []
    for adim in APPROVAL_GATES:
        yol.append(adim)
        if adim == kapi:
            return yol
    return yol


# =============================================================================
# 1) Onay kaydi (approval object)
# =============================================================================


class TestOnayKaydi:
    def test_bos_durumda_yedi_kapi_var(self):
        d = empty_state("THESIS-2026-999")
        assert sorted(d["human_approvals"]) == sorted(APPROVAL_GATES)

    def test_onay_kaydi_zorunlu_alanlari_tasiyor(self):
        d = _onaya_hazir(_durum(), "research_question")
        kayit = d["human_approvals"]["research_question"]
        assert kayit["approved"] is True
        assert kayit["approved_by"] == "Danışman"
        assert kayit["approved_at"]
        assert kayit["content_hash"].startswith("sha256:")
        assert kayit["revision"] == 1

    def test_eski_bicim_true_hala_gecerli(self):
        """Geriye uyum: elle yazilmis `True` onayli sayilir."""
        d = _durum()
        d["human_approvals"]["research_question"] = True
        assert kapi_acik_mi(d, "research_question") is True

    def test_eski_bicim_hash_tasimadigi_icin_bayat_sayilmaz(self):
        d = _durum()
        d["human_approvals"]["research_question"] = True
        assert onay_stale_mi(d, "research_question") is False

    def test_bilinmeyen_kapi_hata_verir(self):
        d = _durum()
        with pytest.raises(ValueError):
            kapi_acik_mi(d, "hacker_gate")

    def test_ikinci_onay_revizyonu_artirir(self):
        d = _onaya_hazir(_durum(), "research_question")
        onay_geri_al(d, "research_question", gerekce="yeniden")
        onay_ver(d, "research_question", onaylayan="Danışman")
        assert d["human_approvals"]["research_question"]["revision"] == 2

    def test_kapi_detay_alanlari_dondurur(self):
        d = _onaya_hazir(_durum(), "research_question")
        detay = kapi_detay(d, "research_question")
        assert detay["kapi"] == "research_question"
        assert detay["acik"] is True
        assert detay["stale"] is False
        assert detay["attested"] is True
        assert detay["content_hash"].startswith("sha256:")

    def test_kapi_detay_elle_yazilmis_onyayi_attested_saymaz(self):
        """Hash'i olmayan `True` onay 'attested' degildir.

        Durum dosyasi imzasiz JSON oldugu icin elle duzenlemeyi tamamen
        engellemek mumkun degildir; ancak `attested=False` ve olay
        gunlugunde kayit bulunmamasi tespit edilebilir bir iz birakir.
        """
        d = _durum()
        d["human_approvals"]["research_question"] = True
        detay = kapi_detay(d, "research_question")
        assert detay["acik"] is True
        assert detay["attested"] is False


# =============================================================================
# 2) Icerik ozeti / immutable onay
# =============================================================================


class TestIcerikOzeti:
    def test_ozet_sabit_ve_onsekilli(self):
        d = _durum()
        a = icerik_ozeti(d, "research_question")
        b = icerik_ozeti(_durum(), "research_question")
        assert a == b
        assert a.startswith("sha256:")
        assert len(a.split(":")[1]) == 16

    def test_kapsam_disi_degisiklik_ozeti_bozmaz(self):
        d = _durum()
        once = icerik_ozeti(d, "source_set")
        d["chapters"] = [{"id": "CH-001", "number": 1, "title": "X"}]
        assert icerik_ozeti(d, "source_set") == once

    def test_kapsam_icindeki_degisiklik_ozeti_bozar(self):
        d = _durum()
        once = icerik_ozeti(d, "research_question")
        d["research_questions"] = [{"id": "RQ-001", "question": "Degisti mi?", "type": "main"}]
        assert icerik_ozeti(d, "research_question") != once

    def test_icerik_degisince_kapi_bayatlar(self):
        d = _onaya_hazir(_durum(), "research_question")
        assert kapi_acik_mi(d, "research_question") is True
        assert onay_stale_mi(d, "research_question") is False
        d["research_questions"][0]["question"] = "Soru değişti mi?"
        assert kapi_acik_mi(d, "research_question") is False
        assert onay_stale_mi(d, "research_question") is True

    def test_kaynak_eklenince_ilgili_kapi_bayatlar(self):
        d = _onaya_hazir(_durum(), "source_set")
        d["sources"].append({"id": "SRC-002", "title": "Yeni", "doi": "10.1/y"})
        assert onay_stale_mi(d, "source_set") is True

    def test_bulgu_eklenince_findings_bayatlar(self):
        d = _onaya_hazir(_durum(), "findings")
        d["findings_registry"].append({"id": "FND-002", "title": "Yeni", "evidence_ids": ["EVD-002"]})
        assert onay_stale_mi(d, "findings") is True

    def test_bayat_kapi_kontrol_yaz_engeli_uretir(self):
        d = _onaya_hazir(_durum(), "research_question")
        d["research_questions"][0]["question"] = "Değişti"
        engeller = kontrol_yaz(d, "research_question")
        assert any("bayat" in e.lower() for e in engeller)

    def test_denetim_sonucu_degisince_final_bayatlar(self):
        d = _onaya_hazir(_durum(), "findings")
        d["chapters"] = [{"id": "CH-001", "number": 1, "title": "Giriş",
                          "paragraphs": [{"id": "P-001", "type": "introduction", "text": "Merhaba"}]}]
        for tur in ("citation", "methodology", "consistency", "integrity", "evidence"):
            if not any(k.get("audit_type") == tur for k in d["audit_registry"]):
                d["audit_registry"].append(_denetim(tur))
        once = icerik_ozeti(d, "final_thesis")
        onay_ver(d, "final_thesis", onaylayan="Danışman")
        d["audit_registry"].append(
            _denetim("integrity", [{"severity": "critical", "message": "uydurma kaynak"}])
        )
        assert icerik_ozeti(d, "final_thesis") != once
        assert onay_stale_mi(d, "final_thesis") is True

    def test_ayni_sonucu_tekrarlayan_denetim_ozeti_bozmaz(self):
        """Ayni bulgularla yeni denetim yeniden calistirildiginde onay gecerli kalir."""
        d = _onaya_hazir(_durum(), "findings")
        d["chapters"] = [{"id": "CH-001", "number": 1, "title": "Giriş",
                          "paragraphs": [{"id": "P-001", "type": "introduction", "text": "Merhaba"}]}]
        for tur in ("citation", "methodology", "consistency", "integrity", "evidence"):
            if not any(k.get("audit_type") == tur for k in d["audit_registry"]):
                d["audit_registry"].append(_denetim(tur))
        onay_ver(d, "final_thesis", onaylayan="Danışman")
        once = d["human_approvals"]["final_thesis"]["content_hash"]
        d["audit_registry"].append(_denetim("integrity", []))
        assert d["human_approvals"]["final_thesis"]["content_hash"] == once
        assert onay_stale_mi(d, "final_thesis") is False


# =============================================================================
# 3) Bagimlilik grafigi
# =============================================================================


class TestBagimlilikGrafiği:
    def test_yedi_kapi_bagimlilik_sozlugunde_tanimli(self):
        assert sorted(GATE_BAGIMLILIK) == sorted(APPROVAL_GATES)

    def test_bagimliliklar_sozlesmeyle_ayni(self):
        for kapi, bagimlilar in GATE_BAGIMLILIK.items():
            assert bagimlilar == GATE_KOSULLARI[kapi].bagimlilik

    def test_research_question_bagimsizdir(self):
        assert GATE_BAGIMLILIK["research_question"] == ()

    def test_final_thesis_findings_bagimlidir(self):
        assert "findings" in GATE_BAGIMLILIK["final_thesis"]

    def test_bagimlilik_dongusu_yoktur(self):
        """Grafik cevrimsiz olmali; cevrim onay dongusu yaratir."""
        for kapi, bagimlilar in GATE_BAGIMLILIK.items():
            for bagimli in bagimlilar:
                assert kapi not in GATE_BAGIMLILIK.get(bagimli, ()), (
                    f"{kapi} -> {bagimli} -> {kapi} cevrimi"
                )

    def test_sira_atlanca_hata_verir(self):
        d = _onaya_hazir(_durum(), "source_set")
        d["human_approvals"]["search_strategy"] = False
        with pytest.raises(OnayHatasi):
            onay_ver(d, "source_set", onaylayan="Danışman")

    def test_bagimlilik_engelleri_eksigi_soyler(self):
        d = _durum()
        engeller = bagimlilik_engelleri(d, "final_thesis")
        assert engeller
        assert all(isinstance(x, str) for x in engeller)


# =============================================================================
# 4) Denetim / onay ayrimi (P0-6)
# =============================================================================


class TestDenetimOnayAyrimi:
    def test_final_thesis_bes_denetim_turu_ister(self):
        assert set(GATE_KOSULLARI["final_thesis"].denetim_turleri) == {
            "citation", "methodology", "consistency", "integrity", "evidence",
        }

    def test_eksik_denetim_kontrol_yaz_engeli_uretir(self):
        d = _onaya_hazir(_durum(), "findings")
        d["chapters"] = [{"id": "CH-001", "number": 1, "title": "Giriş",
                          "paragraphs": [{"id": "P-001", "type": "introduction", "text": "Merhaba"}]}]
        for tur in ("citation", "methodology", "consistency", "integrity", "evidence"):
            if not any(k.get("audit_type") == tur for k in d["audit_registry"]):
                d["audit_registry"].append(_denetim(tur))
        onay_ver(d, "final_thesis", onaylayan="Danışman")
        d["audit_registry"] = [a for a in d["audit_registry"] if a["audit_type"] != "integrity"]
        engeller = kontrol_yaz(d, "final_thesis")
        assert any("integrity" in e for e in engeller)

    def test_critical_bulgu_kapiyi_kapatir(self):
        d = _onaya_hazir(_durum(), "findings")
        d["chapters"] = [{"id": "CH-001", "number": 1, "title": "Giriş",
                          "paragraphs": [{"id": "P-001", "type": "introduction", "text": "Merhaba"}]}]
        for tur in ("citation", "methodology", "consistency", "integrity", "evidence"):
            if not any(k.get("audit_type") == tur for k in d["audit_registry"]):
                d["audit_registry"].append(_denetim(tur))
        onay_ver(d, "final_thesis", onaylayan="Danışman")
        d["audit_registry"].append(
            _denetim("integrity", [{"severity": "critical", "message": "uydurma kaynak"}])
        )
        engeller = kontrol_yaz(d, "final_thesis")
        assert any("critical" in e.lower() for e in engeller)

    def test_denetim_gereksinimleri_listesi_donusur(self):
        d = _durum()
        assert denetim_gereksinimleri(d, "final_thesis")

    def test_minor_bulgu_kapiyi_kapatmaz(self):
        d = _onaya_hazir(_durum(), "findings")
        d["chapters"] = [{"id": "CH-001", "number": 1, "title": "Giriş",
                          "paragraphs": [{"id": "P-001", "type": "introduction", "text": "Merhaba"}]}]
        for tur in ("citation", "methodology", "consistency", "integrity", "evidence"):
            if not any(k.get("audit_type") == tur for k in d["audit_registry"]):
                d["audit_registry"].append(
                    _denetim(tur, [{"severity": "minor", "message": "kucuk eksik"}])
                )
        onay_ver(d, "final_thesis", onaylayan="Danışman")
        engeller = kontrol_yaz(d, "final_thesis")
        assert not any("critical" in e.lower() for e in engeller)


# =============================================================================
# 5) Ret / geri alma / revizyon
# =============================================================================


class TestRetDongusu:
    def test_ret_kapiyi_kapatir_ve_gerekce_yazar(self):
        d = _onaya_hazir(_durum(), "research_question")
        onay_reddet(d, "research_question", gerekce="kapsam çok geniş", onaylayan="Danışman")
        assert d["human_approvals"]["research_question"]["approved"] is False
        assert d["human_approvals"]["research_question"]["rejection_reason"] == "kapsam çok geniş"
        assert kapi_acik_mi(d, "research_question") is False

    def test_gerekesiz_ret_reddedilir(self):
        d = _onaya_hazir(_durum(), "research_question")
        with pytest.raises(ValueError):
            onay_reddet(d, "research_question", gerekce="  ", onaylayan="Danışman")

    def test_retten_sonra_yeniden_acilabilir(self):
        d = _onaya_hazir(_durum(), "research_question")
        onay_reddet(d, "research_question", gerekce="düzelt", onaylayan="Danışman")
        onay_ver(d, "research_question", onaylayan="Danışman")
        assert kapi_acik_mi(d, "research_question") is True

    def test_geri_alma_sonraki_kapilari_kapatir(self):
        # Iki kapi de ACIK olmali. `onay_geri_al` yalniz halihazirde
        # onaylanmis kapilari kapatir; hic acilmamis bir kapinin kaydini
        # yazmak, o kapinin `revision` sayacini da uydururdu.
        d = _onaya_hazir(_durum(), "search_strategy")
        assert kapi_acik_mi(d, "search_strategy") is True
        onay_geri_al(d, "research_question", gerekce="değişti")
        assert d["human_approvals"]["research_question"]["approved"] is False
        assert d["human_approvals"]["search_strategy"]["approved"] is False

    def test_geri_alma_hic_acilmamis_kapiya_kayit_yazmaz(self):
        """Kapanan kapinin sonrasinda hic acilmamis bir kapi varsa
        dokunulmaz. Yazilsaydi `revision` sayaci uydurulur ve o kapinin
        hic onaylanmadigi kayda bakarak anlasilamazdi."""
        d = _onaya_hazir(_durum(), "research_question")
        onay_geri_al(d, "research_question")
        assert d["human_approvals"]["search_strategy"] is False, (
            "hic acilmamis kapiye geri alma kaydi yazilmamali"
        )

    def test_geri_alma_tam_bos_durum_birakir(self):
        d = _onaya_hazir(_durum(), "research_question")
        onay_geri_al(d, "research_question")
        assert kapi_acik_mi(d, "search_strategy") is False


# =============================================================================
# 6) Olay gunlugu
# =============================================================================


class TestOlayGunlugu:
    def test_bos_durumda_gunluk_bos_liste(self):
        d = empty_state("THESIS-2026-999")
        assert d["approval_events"] == []

    def test_onay_olay_yazar(self):
        d = _onaya_hazir(_durum(), "research_question")
        assert d["approval_events"], "onay bir olay yazmalı"
        eylemler = [e["action"] for e in d["approval_events"]]
        assert "approve" in eylemler

    def test_olay_kimlikleri_tekildir(self):
        d = _onaya_hazir(_durum(), "research_question")
        kimlikler = [e["event_id"] for e in d["approval_events"]]
        assert len(kimlikler) == len(set(kimlikler))

    def test_olay_aktori_ve_ani_tasiyor(self):
        d = _onaya_hazir(_durum(), "research_question")
        son = d["approval_events"][-1]
        assert son["actor"]
        assert son["at"]
        assert son["gate"] == "research_question"

    def test_olay_gunlugu_eklenir_guncellenmez(self):
        d = _onaya_hazir(_durum(), "research_question")
        onceki = copy.deepcopy(d["approval_events"])
        onay_geri_al(d, "research_question", gerekce="gerekçe")
        assert d["approval_events"][: len(onceki)] == onceki
        assert len(d["approval_events"]) > len(onceki)

    def test_ret_olayi_yazilir(self):
        d = _onaya_hazir(_durum(), "research_question")
        onay_reddet(d, "research_question", gerekce="eksik", onaylayan="Danışman")
        assert "reject" in [e["action"] for e in d["approval_events"]]

    def test_geri_alma_olayi_yazilir(self):
        d = _onaya_hazir(_durum(), "research_question")
        onay_geri_al(d, "research_question", gerekce="iptal")
        assert "revoke" in [e["action"] for e in d["approval_events"]]


# =============================================================================
# 7) Girdi temizleme (sizma)
# =============================================================================


class TestGirdiTemizleme:
    def test_kontrol_karakterleri_atilir(self):
        assert "\x1b" not in temizle("ad\x1b[31msoyad\x07", 120)
        assert "\x00" not in temizle("a\x00b", 120)

    def test_yeni_satirlar_kalirsa_dosya_bozulmaz(self):
        temiz = temizle("ilk satır\nikinci satır", 120)
        assert "\n" not in temiz

    def test_uzunluk_sinirlanir(self):
        assert len(temizle("x" * 5000, 120)) <= 120

    def test_bos_metin_none_doner(self):
        assert temizle("   ", 120) is None

    def test_onaylayan_uzunlugu_kirpilir(self):
        d = _onaya_hazir(_durum(), "research_question")
        onay_ver(d, "research_question", onaylayan="A" * 400)
        assert len(d["human_approvals"]["research_question"]["approved_by"]) <= 120

    def test_yorum_kontrol_karakteri_tasimaz(self):
        d = _onaya_hazir(_durum(), "research_question")
        onay_ver(d, "research_question", onaylayan="Danışman", yorum="temiz\x1b[2J" + "x" * 3000)
        yorum = d["human_approvals"]["research_question"]["comment"]
        assert "\x1b" not in (yorum or "")
        assert len(yorum) <= 2000

    def test_ret_gerekcesi_kontrol_karakteri_tasimaz(self):
        d = _onaya_hazir(_durum(), "research_question")
        onay_reddet(d, "research_question", gerekce="kötü\x07", onaylayan="Danışman")
        assert "\x07" not in d["human_approvals"]["research_question"]["rejection_reason"]
