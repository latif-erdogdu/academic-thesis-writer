"""Onay kapıları — SIZMA ve GÜVENLİK TEST PAKETİ.

Bu dosya "mutlu yol" testi DEĞİLDİR. Buradaki soru şudur:

    "Kapıyı atlamaya çalışan bir ajan ya da kötü niyetli kullanıcı elinde
     ne varsa sistem ne yapıyor?"

Kanonik sözleşme: ``references/approval_gates.md``

  §1 onay / hazırlık / denetim / tazelik ayrımı — "denetim geçmesi onay değildir"
  §2 onay kaydı (approved_by zorunlu, comment ≤ 2000)
  §3 bağımlılık grafisi (sıraya değil, açık listeye bağlı)
  §4 kapı kontratları (on_kosul = önkoşul, son_kosul = sonkoşul)
  §5 tazelik — immutable onay (content_hash)
  §6 ret ve revizyon
  §7 olay günlüğü (append-only)
  §8 eşzamanlılık / atomik yazım
  §9 sınırlamalar

Neden burada kırmızı testler var
--------------------------------
Bu testler **spec'e göre** yazıldı, mevcut uygulamaya göre DEĞİL. Spec ile
çelişen bir davranış varsa (``references/approval_gates.md``: "Kod ile bu
doküman çelişirse **kod yanlıştır****) test kırmızı bırakılır ve ilgili
testin başlığında hangi maddenin ihlal edildiği yazılıdır. Kırmızı olmak bir
test hatası DEĞİL, kapatılmamış sızma yüzeyinin kanıtıdır.

Bilinen kırmızı davranışlar ve dayandıkları maddeler:

============================================  ==========================
Kırmızı test                                 İhlal edilen madde
============================================  ==========================
``test_ozet_kapi_sifir_bypass[rq]``         §4 "on_kosul = önkoşul"
``test_bos_registry_ile_*`` (5)              §4 aynı
``test_eksik_alanli_kayit_ile_*``            §4.1 aynı
``test_metni_olmayan_bolum_ile_*``            §4.7 aynı
``test_ret_sonrasi_on_kosul_*``              §6 "önkoşul sağlanana kadar"
``test_ret_baglantili_kapilari_kapatir``     §3 "geçerli onay"
``test_onaydan_sonra_kritik_denetim_*``      §5 "denetim de tazeliğe dâhil"
``test_cli_gerekesiz_ret_reddedilir``        §6 CLI yüzeyi eksik
============================================  ==========================

Gerekçe: ``onay_ver`` hazırlık denetimini bilerek CLI'da soruyor
(``approval.py`` docstring'i), yani **kütüphane düzeyinde** önkoşul denetimi
yoktur. CLI korur; ``approval.onay_ver`` çağıran bir ajan/kod korunmaz.

Kurallar
--------
* ``pytest.skip(allow_module_level=True)`` YOK, ``xfail`` YOK. Eksik bir
  özellik "test toplanmadı" diye sessizce atlanmaz: ``_api()`` yardımcısı
  eksik sembolü okunabilir bir assertion'a çevirir, böylece test dosyası
  DÜZGÜN TOPLANIR ve gerçek bir assertion ile kırmızı olur.
* Modül yalnızca ``import tools.atw.approval`` ile yüklenir; yeni API
  adları modül üzerinden ``_api()`` ile çözülür, böylece bir yeniden adlandırma
  toplama hatası değil görünür bir test hatası üretir.
* Testler birbirinden bağımsızdır: her biri tek bir davranışı sınar.

Bilinen spec <-> sema uyuşmazlıkları (testlerde kasıtlı olarak köprülenir)
-------------------------------------------------------------------------
1. §4.1 "her sorunun ``id``, ``question`` ve ``type`` alanı doludur" diyor;
   ``schemas/research_question.json`` alanı ``text`` tutuyor. Testler bu
   alana BULAŞMAZ — eksik alan denetimi iki kaynağın da ortak bildirdiği
   ``type`` üzerinden yapılır.
2. §4.4 ``basis_source_ids`` diyor; ``schemas/research_gap.json`` ise
   ``evidence_ids`` (EVD-*) tutuyor ve ``additionalProperties: false``.
   Fixture İKİ alanı da taşır ki spec'i okuyan uygulama da şemayı okuyan
   uygulama da kırılmasın.
3. §4.2 "her kayıt hangi soruyu (``rq_id``) taradığını ... belirtir" diyor;
   ``schemas/search_run.json`` ``additionalProperties: false`` ve ``rq_id``
   alanı YOK. Aynı köprü: yalnızca bellekteki (şemasız) fixture'de ``rq_id``
   bulunur, diske yazılan (şemaya uyumlu) fixture'de bulunmaz.
"""
from __future__ import annotations

import inspect
import json
import os
import re
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

import pytest

import tools.atw.approval as kapi
from tools.atw.state import APPROVAL_GATES, empty_state

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Kararı veren insan. Spec §2: approved_by insan adıdır, ajan adı değil.
DANISMAN = "Dr. Danışman Adı"

#: Spec §4.7 + §4.6: final_thesis beş denetim türünün hepsini ister.
GEREKEN_DENETIMLER: tuple[str, ...] = (
    "citation",
    "methodology",
    "consistency",
    "integrity",
    "evidence",
)

#: Spec §7: olay günlüğündeki eylem kümesi.
IZINLI_EYLEMLER = frozenset({"approve", "reject", "revoke", "stale", "block"})

#: Kontrol karakteri enjeksiyonu: NUL, ANSI kaçış dizisi, CR, LF, DEL, BS.
#: Konsol/terminal kaçışı, satır enjeksiyonu ve dosya bozma girişimi.
ZEHIR = "\x00\x1b[31m\x1b[0m\r\n\x7f\x08\x1b]0;başlık\x07"


# --- yeni API'ye güvenli erişim -------------------------------------------

def _api(ad: str) -> Any:
    """Spec §2-§7'den türetilen bir API'ye erişir; yoksa assertion ile durur.

    `AttributeError` sessizce testi "hata" olarak bitirirdi ve hangi saldırı
    yüzeyinin eksik olduğunu söylemezdi. Burada mesaj, EKSİK OLAN YÜZEYİ
    adıyla söyler.
    """
    assert hasattr(kapi, ad), (
        f"tools.atw.approval.{ad}() yok — approval_gates.md spec'inde tanımlı "
        f"API uygulanmamış. Bu saldırı yüzeyi henüz kapalı değil; testi "
        f"skip/xfail ile susturmak yerine kırmızı bırakıyoruz."
    )
    return getattr(kapi, ad)


def _imza(fonksiyon_adi: str, *anahtar_sozcukler: str) -> Callable[..., Any]:
    """Fonksiyonun istenen anahtar sözcükleri kabul ettiğini doğrular.

    Spec §2 `approved_by`'yi zorunlu kılıyor; imza bu kelimeleri kabul
    etmiyorsa sessizce kaydedilmiş bir "onay" üretmek, kapının en tehlikeli
    atlatma yoludur (kim onayladı? — kimse).
    """
    fonksiyon = _api(fonksiyon_adi)
    imza = inspect.signature(fonksiyon)
    if any(p.kind is p.VAR_KEYWORD for p in imza.parameters.values()):
        return fonksiyon
    eksik = [k for k in anahtar_sozcukler if k not in imza.parameters]
    assert not eksik, (
        f"{fonksiyon_adi}() imzası {eksik} anahtar sözcüğünü kabul etmiyor. "
        f"spec §2: kararı veren kişi (approved_by) zorunlu alandır."
    )
    return fonksiyon


def _onay_ver(
    durum: dict,
    kapi_adi: str,
    *,
    onaylayan: str = DANISMAN,
    yorum: str = "",
    denetim_idleri: tuple[str, ...] = (),
) -> dict:
    """Spec §2 imzalı `onay_ver` çağrısı."""
    return _imza("onay_ver", "onaylayan")(
        durum, kapi_adi, onaylayan=onaylayan, yorum=yorum,
        denetim_idleri=denetim_idleri,
    )


def _onay_stale_mi(durum: dict, kapi_adi: str) -> bool:
    return _api("onay_stale_mi")(durum, kapi_adi)


def _kapi_detay(durum: dict, kapi_adi: str) -> dict:
    return _api("kapi_detay")(durum, kapi_adi)


def _onay_reddet(
    durum: dict,
    kapi_adi: str,
    *,
    gerekce: str = "",
    onaylayan: str = DANISMAN,
    yorum: str = "",
) -> dict:
    """Spec §6 imzalı `onay_reddet` çağrısı."""
    return _imza("onay_reddet", "gerekce", "onaylayan")(
        durum, kapi_adi, gerekce=gerekce, onaylayan=onaylayan, yorum=yorum
    )


# --- durum fixture'ları -----------------------------------------------------

def _rq(kimlik: str = "RQ-001", *, durum_sonucu: str = "answered") -> dict:
    return {
        "id": kimlik,
        "text": f"Kurgusal soru {kimlik}: yöntemin etkisi nedir?",
        "type": "main" if kimlik == "RQ-001" else "sub",
        "status": durum_sonucu,
    }


def _paragraf() -> dict:
    return {
        "id": "P-001",
        "type": "introduction",
        "chapter": "CH-001",
        "text": "Özgün giriş metni.",
    }


def _denetim(audit_id: str, audit_turu: str, *, bulgular: list[dict] | None = None,
             tarih: str = "2026-01-01") -> dict:
    bulgular = list(bulgular or [])
    return {
        "audit_id": audit_id,
        "thesis_id": "THESIS-2026-001",
        "audit_type": audit_turu,
        "date": tarih,
        "findings": bulgular,
        "critical_issues": [
            b["message"] for b in bulgular if b.get("severity") == "critical"
        ],
    }


def _kritik_bulgu(mesaj: str = "Atıf kaydı bulunamadı") -> dict:
    return {"severity": "critical", "message": mesaj, "location": "CH-001"}


def _temiz_denetimler() -> list[dict]:
    """Gerekli beş denetim türünün de TEMİZ sonuçlu kaydı."""
    return [
        _denetim(f"AUD-{i:03d}", tur)
        for i, tur in enumerate(GEREKEN_DENETIMLER, start=1)
    ]


def _dolu_durum() -> dict:
    """Spec §4'ün YEDİ kapısının da karşılanmış olduğu bir tez durumu.

    Bu fixture HEM bellekte hem diske yazılır (CLI alt süreç testleri),
    dolayısıyla `schemas/thesis_state.json`'a uymak ZORUNDADIR. "Bellek için
    ayrı sürüm" kavramı bilinçli olarak YOK: aynı fixture iki yolda da geçerli
    olmalıdır; aksi halde sızma testleri, gerçekte diske yazılamayan bir
    durumu "geçerli" kabul ederdi.
    """
    durum = empty_state("THESIS-2026-001", "Sızma Testi Tezi")
    paragraf = _paragraf()
    durum["research_questions"] = [_rq()]
    durum["search_runs"] = [
        {
            "id": "SEARCH-001",
            "database": "crossref",
            "query": "kurgusal sorgu",
            "timestamp": "2026-01-01T09:00:00+00:00",
            "results_returned": 1,
            "inclusion_criteria": ["akademik makale"],
            "exclusion_criteria": ["derleme"],
            "prisma_flow": {
                "records_identified": 1,
                "duplicates_removed": 0,
                "records_screened": 1,
                "records_excluded": 0,
                "reports_sought": 1,
                "reports_not_retrieved": 0,
                "reports_excluded": 0,
                "studies_included": 1,
            },
        }
    ]
    durum["sources"] = [
        {
            "id": "SRC-001",
            "title": "Kurgusal kaynak",
            "doi": "10.1234/kurgusal",
            "source_type": "article",
            "verified": True,
            "retraction_status": "not_retracted",
            # spec §4.4: boşluk beyanı DOĞRULANMIŞ bir kaynağa çözülmelidir.
            "verification": {
                "status": "verified",
                "bibliographic_match": 1.0,
                "verified_at": "2026-01-01T09:00:00+00:00",
                "verification_sources": ["crossref"],
            },
        }
    ]
    durum["evidence_registry"] = [
        {
            "id": "EVD-001",
            "source_id": "SRC-001",
            "location": {"page": 1, "section": "3.1", "paragraph": None},
            "text": "Kurgusal alıntı.",
            "evidence_type": "literature",
            "strength": "direct",
        }
    ]
    durum["claims_registry"] = [
        {
            "id": "CLM-001",
            "text": "Kurgusal iddia.",
            "importance": "high",
            "verification_status": "verified",
            "evidence_ids": ["EVD-001"],
        }
    ]
    durum["gap_registry"] = [
        {
            "id": "GAP-001",
            "statement": "Kurgusal boşluk beyanı.",
            "gap_type": "unanswered_question",
            "evidence_ids": ["EVD-001"],
            # spec §4.4: boşluğun dayandığı DOĞRULANMIŞ kaynak.
            "supporting_source_ids": ["SRC-001"],
            "confidence": "high",
        }
    ]
    durum["findings_registry"] = [
        {
            "id": "FND-001",
            "rq_id": "RQ-001",
            "statement": "Kurgusal bulgu.",
            "evidence_ids": ["EVD-001"],
        }
    ]
    durum["chapters"] = [
        {"id": "CH-001", "number": 1, "title": "Giriş", "paragraphs": [paragraf]}
    ]
    durum["paragraphs"] = [paragraf]
    durum["audit_registry"] = _temiz_denetimler()
    return durum


def _kapili_durum() -> dict:
    """Hiçbir kapı açık değil, veri de yok: en zayıf durum."""
    return empty_state("THESIS-2026-001", "Sızma Testi Tezi")


def _onayli_durum(hedef: str) -> dict:
    """`hedef` kapısı dâhil, önceki kapılar GERÇEKTEN onaylanmış durum.

    Onaylar elle `True` yazılarak değil, `onay_ver` çağrılarak üretilir:
    sahte onayla kurulmuş bir fixture, kendi kuralını kendi test etmez.
    """
    durum = _dolu_durum()
    for adim in APPROVAL_GATES:
        _onay_ver(durum, adim, onaylayan=DANISMAN)
        if adim == hedef:
            return durum
    raise AssertionError(f"hedef kapı akışta yok: {hedef}")


def _kayit(durum: dict, kapi_adi: str) -> dict:
    """`human_approvals.<kapı>` kaydı; metadata'sızsa test kırılır."""
    kayit = (durum.get("human_approvals") or {}).get(kapi_adi)
    assert isinstance(kayit, dict), (
        f"human_approvals.{kapi_adi} = {kayit!r} — spec §2: onay kaydı "
        f"approved/approved_by/approved_at/content_hash alanlarını taşır. "
        f"Yalnızca bool tutmak, 'kim, neye bakarak, ne zaman onayladı' "
        f"sorusunu yanıtsız bırakır."
    )
    return kayit


def _olaylar(durum: dict) -> list[dict]:
    olaylar = durum.get("approval_events")
    assert isinstance(olaylar, list), (
        "durumda `approval_events` dizisi yok — spec §7: her onay, ret, geri "
        "alma ve tazelik kaybı bir olay yazar."
    )
    return olaylar


def _kontrol_karakteri_var(metin: str) -> bool:
    return any(ord(k) < 0x20 or ord(k) == 0x7F for k in metin)


# --- 1) gate bypass: sıra atlama -------------------------------------------

def test_final_thesis_findings_onaysiz_acilamaz() -> None:
    """En pahalı atlatma: son kapıyı, orta kapı atlanarak açmak.

    Saldırganın kazancı en büyük buradadır: `findings` incelenmeden tez
    onaylanır. Spec §3: `final_thesis` doğrudan yalnızca `findings`'e
    bağımlıdır ve o kapı geçerli (onaylı **ve** taze) olmadan açılmaz.
    """
    durum = _onayli_durum("findings")
    durum["human_approvals"]["findings"] = False

    with pytest.raises(kapi.OnayHatasi) as hata:
        _onay_ver(durum, "final_thesis", onaylayan=DANISMAN)

    assert "findings" in str(hata.value), (
        f"engel hangi kapı olduğunu ADIYLA söylemeli: {hata.value}"
    )
    assert kapi.kapi_acik_mi(durum, "final_thesis") is False


def test_research_gap_onaysiz_methodology_acilamaz() -> None:
    """Spec §3: `methodology`, yalnızca `research_gap`'e bağımlıdır.

    Aradaki `search_strategy`/`source_set` kapıları açık olsa bile boşluk
    kanıtlanmadan yöntem onaylanamaz.
    """
    durum = _onayli_durum("methodology")
    durum["human_approvals"]["research_gap"] = False
    onceki_olay = len(_olaylar(durum))
    onceki_rev = _kayit(durum, "methodology").get("revision")

    with pytest.raises(kapi.OnayHatasi) as hata:
        _onay_ver(durum, "methodology", onaylayan=DANISMAN)

    assert "research_gap" in str(hata.value)
    # Başarısız yeniden onay hiçbir iz bırakmamalı: yeni olay yazılmaz,
    # sürüm sayacı artmaz (spec §7 "olaylar eklenir", §8 "yarım yazım yok").
    assert len(_olaylar(durum)) == onceki_olay, "başarısız onay olay yazdı"
    assert _kayit(durum, "methodology").get("revision") == onceki_rev, (
        "başarısız onay revision'ı artırdı — kısmi yazım"
    )


def test_bagimlilik_sozlugu_grafi_tasiyor() -> None:
    """`GATE_BAGIMLILIK`, spec §3'teki grafiğin ta kendisidir.

    İki ayrı sıkma: yedi anahtar eksiksiz, kök kapı (`research_question`)
    bağımlılıksız, uç kapı (`final_thesis`) yalnızca `findings`'e bağlı.
    Sıralı bir uygulama (sabit önceki-kapı listesi) ikincisini sağlayamaz.
    """
    bagimlilik = _api("GATE_BAGIMLILIK")
    assert set(bagimlilik) == set(APPROVAL_GATES), (
        f"GATE_BAGIMLILIK yedi kapıyı kapsamalı, eksik: "
        f"{sorted(set(APPROVAL_GATES) - set(bagimlilik))}"
    )
    assert tuple(bagimlilik["research_question"]) == (), "kök kapının bağımlılığı olmamalı"
    assert tuple(bagimlilik["final_thesis"]) == ("findings",), (
        "spec §3: final_thesis doğrudan yalnızca findings'e bağlıdır"
    )
    assert tuple(bagimlilik["methodology"]) == ("research_gap",)

    for ad, bagimlilar in bagimlilik.items():
        konum = APPROVAL_GATES.index(ad)
        for hedef in bagimlilar:
            assert hedef in APPROVAL_GATES, f"{ad} bilinmeyen kapıya bağlı: {hedef}"
            assert APPROVAL_GATES.index(hedef) < konum, (
                f"{ad} akışta SONRA gelen {hedef} kapısına bağlı — döngüsel bağımlılık"
            )


_BAGIMLILIK_CIFTLERI = [
    ("search_strategy", "research_question"),
    ("source_set", "search_strategy"),
    ("research_gap", "source_set"),
    ("methodology", "research_gap"),
    ("findings", "methodology"),
    ("final_thesis", "findings"),
]


@pytest.mark.parametrize(
    ("kapi_adi", "bagimli_kapi"), _BAGIMLILIK_CIFTLERI,
    ids=[f"{k}<-{b}" for k, b in _BAGIMLILIK_CIFTLERI],
)
def test_bagimlilik_kapaliyken_ilgili_kapi_acilamaz(
    kapi_adi: str, bagimli_kapi: str
) -> None:
    """Grafiğin HER kenarı tek tek yoklanır: bağımlılık kapalıysa kapı açılmaz."""
    durum = _onayli_durum(kapi_adi)
    durum["human_approvals"][bagimli_kapi] = False

    with pytest.raises(kapi.OnayHatasi):
        _onay_ver(durum, kapi_adi, onaylayan=DANISMAN)


# --- 2) gate bypass: boş kapıya onay ---------------------------------------

_ON_KOSUL_REGISTRY = [
    ("research_question", "research_questions"),
    ("search_strategy", "search_runs"),
    ("source_set", "sources"),
    ("research_gap", "gap_registry"),
    ("findings", "findings_registry"),
]


@pytest.mark.parametrize(
    ("kapi_adi", "registry"), _ON_KOSUL_REGISTRY,
    ids=[f"{k}/{r}" for k, r in _ON_KOSUL_REGISTRY],
)
def test_bos_registry_ile_kapi_onaylanamaz(kapi_adi: str, registry: str) -> None:
    """Spec §4 (satır 75): ``on_kosul`` = ÖNKOŞUL, "onay verilebilmesi için
    verinin hazır olması".

    Boş bir belgeye onay vermek, kapı sistemini anlamsızlaştırır: kapı açık
    görünür ama uygulanacak hiçbir şey yoktur.

    ⚠ KIRMIZI: spec §4'ün her kapı için yazdığı önkoşulu `onay_ver`
    kütüphane düzeyinde denetlemiyor; denetim yalnızca CLI'da
    (`hazirlik_engelleri`). `approval.onay_ver` çağıran bir ajan önkoşulu
    atlıyor. Kapatılana kadar bu test kırmızı kalır.
    """
    durum = _onayli_durum(kapi_adi)
    durum[registry] = []

    with pytest.raises((kapi.OnayHatasi, ValueError)):
        _onay_ver(durum, kapi_adi, onaylayan=DANISMAN)

    assert kapi.kapi_acik_mi(durum, kapi_adi) is False


def test_eksik_alanli_kayit_ile_kapi_onaylanamaz() -> None:
    """Tek satırlık yarım kayıt da önkoşulu sağlamaz.

    `type` alanı, hem spec §4.1 hem `research_question.json` tarafından
    zorunlu; test bu ortak alana bakar (modül docstring, uyuşmazlık 1).

    ⚠ KIRMIZI: §4.1 önkoşulu `onay_ver` içinde denetlenmiyor (bkz.
    `test_bos_registry_ile_kapi_onaylanamaz`).
    """
    durum = _onayli_durum("research_question")
    durum["research_questions"] = [{"id": "RQ-001", "text": "Soru metni"}]

    with pytest.raises((kapi.OnayHatasi, ValueError)):
        _onay_ver(durum, "research_question", onaylayan=DANISMAN)

    assert kapi.kapi_acik_mi(durum, "research_question") is False


def test_metni_olmayan_bolum_ile_final_thesis_onaylanamaz() -> None:
    """Spec §4.7: her bölümde metni olan en az bir paragraf olmalı.

    Yalnızca bölüm başlıklarından oluşan bir "tez" onaylanabilirse, kapı
    hiçbir şeyi doğrulamıyor demektir.

    ⚠ KIRMIZI: §4.7 önkoşulu `onay_ver` içinde denetlenmiyor; bütünlük
    taraması yalnızca `hazirlik_engelleri` (CLI) yolunda çalışıyor.
    """
    durum = _onayli_durum("final_thesis")
    durum["chapters"][0]["paragraphs"] = [
        {"id": "P-001", "type": "introduction", "chapter": "CH-001", "text": ""}
    ]
    durum["paragraphs"] = durum["chapters"][0]["paragraphs"]

    with pytest.raises((kapi.OnayHatasi, ValueError)):
        _onay_ver(durum, "final_thesis", onaylayan=DANISMAN)

    assert kapi.kapi_acik_mi(durum, "final_thesis") is False


# --- 3) bilinmeyen kapı adı ------------------------------------------------

def test_onay_ver_bilinmeyen_kapi_hata_verir() -> None:
    """`human_approvals`'a yeni bir anahtar sessizce eklenemez.

    `onay_ver(durum, "hacker_gate")` çağıran bir saldırgan, sistemde
    tanımsız bir kapı açtığını sanar. Sessiz geçiş, kapı tablosuna eklenen
    ama burada unutulan her yeni aşamayı da gizler.
    """
    durum = _kapili_durum()
    with pytest.raises(ValueError, match="bilinmeyen"):
        kapi.onay_ver(durum, "hacker_gate")
    assert "hacker_gate" not in durum["human_approvals"]


def test_kapi_acik_mi_bilinmeyen_kapi_hata_verir() -> None:
    """Sorgu tarafı da aynı disiplini uygular: bilinmeyen ad `False` DEĞİLDİR.

    `kapi_acik_mi` bilinmeyen adda `False` dönerse, "kapı yok" ile "kapı
    kapalı" ayırt edilemez ve hatayı bulan yoktur.
    """
    durum = _kapili_durum()
    with pytest.raises(ValueError, match="bilinmeyen"):
        kapi.kapi_acik_mi(durum, "hacker_gate")
    with pytest.raises(ValueError, match="bilinmeyen"):
        kapi.kontrol_yaz(durum, "hacker_gate")


@pytest.mark.parametrize(
    "fonksiyon_adi", ["onay_stale_mi", "kapi_detay", "denetim_gereksinimleri"],
)
def test_yeni_api_bilinmeyen_kapida_sessiz_gecmemeli(fonksiyon_adi: str) -> None:
    """Spec ile gelen her yeni okuma fonksiyonu aynı kapı sözleşmesini paylaşır.

    `denetim_gereksinimleri` listede döndürdüğü için "bilinmeyen kapı" için
    boş liste döndürmek cazip bir atlatma yoludur: kapı yokmuş gibi davranır.
    """
    durum = _kapili_durum()
    with pytest.raises(ValueError, match="bilinmeyen"):
        _api(fonksiyon_adi)(durum, "hacker_gate")


# --- 4) immutable onay: tazelik (EN KRİTİK) --------------------------------

#: Spec §5 (immutable onay) için beş mutasyon. Her biri, o kapının §4
#: kontratında AÇIKÇA sayılan bir içeriği değiştirir; hiçbiri "ekstra
#: güzellik" değildir:
#:
#:   research_question  §4.1  `research_questions` en az bir soru içerir
#:   source_set         §4.3  `sources` en az bir kaynak içerir / her kaynak atıf yapılabilir
#:   findings           §4.6  `findings_registry` en az bir bulgu içerir
#:   final_thesis       §4.7  "her bölümde metni olan en az bir paragraf"
#:
#: `methodology` kapısı BİLEREK dışarıda: spec §4.5'in kontratı yalnızca soru
#: *durumları* (`answered`/`pending`) ve gerekçe üzerine; paragraf metni ya da
#: yeni bir soru eklenmesi §4.5'i ihlal etmez. Spec'in istemedikleri bir
#: gereksinim test edilmez.
_BAYALAMA_SENARYOLARI = [
    ("research_question", "soru_eklendi",
     lambda d: d["research_questions"].append(_rq("RQ-002"))),
    ("source_set", "kaynak_cikarildi", lambda d: d["sources"].pop()),
    ("source_set", "kaynak_eklendi", lambda d: d["sources"].append({
        "id": "SRC-002", "title": "Sonradan eklenen kaynak",
        "doi": "10.1234/eklenen", "source_type": "article",
        "verified": True, "retraction_status": "not_retracted",
    })),
    ("findings", "bulgu_eklendi", lambda d: d["findings_registry"].append(
        {"id": "FND-002", "rq_id": "RQ-001", "statement": "Yeni bulgu.",
         "evidence_ids": ["EVD-001"]}
    )),
    ("final_thesis", "paragraf_metni_degisti",
     lambda d: d["paragraphs"][0].update({"text": "Değiştirilmiş metin."})),
]


@pytest.mark.parametrize(
    ("kapi_adi", "ad", "mutasyon"), _BAYALAMA_SENARYOLARI,
    ids=[f"{k}/{a}" for k, a, _ in _BAYALAMA_SENARYOLARI],
)
def test_icerik_degisince_onay_bayalar(
    kapi_adi: str, ad: str, mutasyon: Callable[[dict], None]
) -> None:
    """EN KRİTİK TEST: onay verildikten sonra içerik değişirse kapı kapanır.

    Spec §1'in çözdüğü asıl soru: "onaylanan içerik sonradan değişse bile
    onay geçerli görünüyordu." Spec §5'in sonucu birebir: içerik değiştiyse
    ``kapi_acik_mi -> False`` ve ``onay_stale_mi -> True``.

    Beş mutasyonun beşi de reddedilirse, onayın "hangi sürümü gördüm"
    anlamı yoktur: insan onayladığını sandığı metin ile üretilen metin
    arasındaki fark sessiz kalır.
    """
    durum = _onayli_durum(kapi_adi)
    assert kapi.kapi_acik_mi(durum, kapi_adi) is True, "kurulum hatası"

    mutasyon(durum)

    assert kapi.kapi_acik_mi(durum, kapi_adi) is False, (
        f"{kapi_adi}/{ad}: içerik değişti ama kapı açık kaldı — onay "
        f"değişen içeriği kapsamıyor"
    )
    assert _onay_stale_mi(durum, kapi_adi) is True, (
        f"{kapi_adi}/{ad}: bayalama bildirilmedi"
    )


def test_hash_elle_uydurulunca_kapi_kapali() -> None:
    """`thesis_state.json`'ı elle düzenleyip `approved: true` yazmak yetmez.

    Bu, sızmanın en ucuz yoludur: dosya bir metin dosyasıdır, `onay_ver`
    çağrılmadan `human_approvals` alanına yazılabilir. Onay kaydı ancak
    içeriğin `content_hash` özetiyle eşleşiyorsa geçerlidir (spec §2, §5).
    """
    durum = _onayli_durum("source_set")
    durum["human_approvals"]["source_set"] = {
        "approved": True,
        "approved_by": "totally_not_a_human",
        "content_hash": "sha256:0000000000000000",
    }

    assert kapi.kapi_acik_mi(durum, "source_set") is False, (
        "elle yazılmış sahte hash, kapıyı açtı"
    )
    assert _onay_stale_mi(durum, "source_set") is True


def test_kapi_detay_bayatligi_yansitir() -> None:
    """Teşhis yüzeyi de bayalamayı bildirir.

    `kapi_detay` yalnızca "açık mı" diye sormaz; hangi sürümü kapsadığını ve
    o sürümün hâlâ geçerli olup olmadığını bildirir (spec §5). Kullanıcı
    "kapı neden kapalı?" sorusunu bu yüzeyden sorar; bayalamayı burada
    göremiyorsa sorusu da yanıtsız kalır.
    """
    durum = _onayli_durum("research_question")
    taze = _kapi_detay(durum, "research_question")
    assert isinstance(taze, dict) and taze, "kapi_detay boş sözlük döndürdü"
    assert taze.get("stale") is False, "taze kayıt bayat görünüyor"

    durum["research_questions"].append(_rq("RQ-002"))
    bayat = _kapi_detay(durum, "research_question")

    assert bayat != taze, (
        "içerik değişti ama kapi_detay aynı çıktıyı verdi — teşhis yüzeyi "
        "bayalamayı göremiyor"
    )
    assert bayat.get("stale") is True, f"stale alanı yanlış: {bayat.get('stale')!r}"
    assert bayat.get("content_hash") != bayat.get("simdiki_ozet"), (
        "onayın kapsadığı özet ile içeriğin şimdiki özeti aynı görünüyor"
    )


def test_eskbicim_true_geriye_uyumlu() -> None:
    """Geriye uyum: eski `true` kaydı hata vermemeli, kapı açık sayılmalıdır.

    Spec §2 eski biçimi açıkça tanır. Bu test, geriye uyumu bir sızma
    yoluna dönüştürmeden sabitler: yeni kayıt şeması zorunlu kılındığında
    `onay_ver(durum, kapi)` eski imzayla da çağrılabilir olmalıdır.
    """
    durum = _dolu_durum()
    durum["human_approvals"]["methodology"] = True
    assert kapi.kapi_acik_mi(durum, "methodology") is True


# --- 5) ret (rejection) ----------------------------------------------------

def test_ret_kapim_kapatir_ve_gerekce_yazar() -> None:
    """Spec §6: ret kapıyı kapatır ve gerekçeyi kayda yazar.

    Gerekçesiz ret, insan kararının izini yok eder: "neden yapılmadı?"
    sorusu yanıtsız kalır ve kapı sessizce kapalı görünür.
    """
    durum = _onayli_durum("findings")
    _onay_reddet(
        durum, "findings", gerekce="kanıt kaydı eksik", onaylayan=DANISMAN
    )

    assert kapi.kapi_acik_mi(durum, "findings") is False
    gerekce = _kayit(durum, "findings").get("rejection_reason")
    assert gerekce and gerekce.strip(), (
        f"ret gerekçesi boş: {gerekce!r} — spec §6: gerekçe zorunludur"
    )


@pytest.mark.parametrize(
    "ek",
    [{}, {"gerekce": ""}, {"gerekce": "   "}, {"gerekce": None}],
    ids=["gerekce-yok", "gerekce-bos", "gerekce-bosluk", "gerekce-none"],
)
def test_gerekesiz_ret_reddedilir(ek: dict) -> None:
    """Boş/eksik gerekçeli ret çağrısı reddedilmelidir.

    `TypeError` da kabul edilir: sözleşme gerekçeyi zorunlu kıldığı için,
    imzada olmayan bir `gerekce=` de aynı reddi üretir (bugünkü durum).
    """
    durum = _onayli_durum("findings")
    with pytest.raises((TypeError, ValueError, kapi.OnayHatasi)):
        kapi.onay_reddet(durum, "findings", onaylayan=DANISMAN, **ek)

    assert kapi.kapi_acik_mi(durum, "findings") is True, (
        "başarısız ret, kapıyı yine de kapattı — kısmi yazım"
    )


def test_ret_sonrasi_on_kosul_saglanana_kadar_acilamaz() -> None:
    """Spec §6: ret, önkoşul sağlanana kadar tekrar açılamaz.

    "Ret ettim ama veri aynen duruyor, hemen tekrar onaylıyorum" yolu,
    ret kararını anlamsızlaştırır.

    ⚠ KIRMIZI: `onay_ver` §4.6 önkoşulunu (bulgular boşken onay) denetlemediği
    için retten hemen sonra kapı yeniden açılabiliyor. Spec §6 açıkça
    "Kapının önkoşulu sağlanana kadar tekrar açılamaz" diyor.
    """
    durum = _onayli_durum("findings")
    durum["findings_registry"] = []
    _onay_reddet(durum, "findings", gerekce="kanıtsız bulgu", onaylayan=DANISMAN)

    with pytest.raises((kapi.OnayHatasi, ValueError)):
        _onay_ver(durum, "findings", onaylayan=DANISMAN)

    # Önkoşul sağlandığında kapı yeniden açılabilir olmalı.
    durum["findings_registry"] = [
        {"id": "FND-001", "rq_id": "RQ-001", "statement": "Kurgusal bulgu.",
         "evidence_ids": ["EVD-001"]}
    ]
    _onay_ver(durum, "findings", onaylayan=DANISMAN)
    assert kapi.kapi_acik_mi(durum, "findings") is True


def test_ret_baglantili_kapilari_kapatir() -> None:
    """Reddedilen bir kapıya dayanan kapılar açık kalamaz.

    Aksi halde durum "yöntem onaylanmadı ama tez onaylı" gibi tutarsız olur;
    `kapi_acik_mi` tek kapıya baktığı için bu tutarsızlık görünmez kalır.

    ⚠ KIRMIZI: `onay_reddet` yalnızca kendi kapısını kapatıyor; bağımlı
    kapılara zincirleme yayılmıyor (`onay_geri_al` yayıyor, ret yaymıyor).
    Spec §3: "Bir kapı ... doğrudan bağımlı kapıların *geçerli* (onaylı **ve**
    taze) onayına dayanır" — ret edilen bir bağımlılığın dayandırdığı onay
    artık geçerli değildir. Etkisi: ret kararına rağmen `cmd_export`
    `final_thesis` kapısını açık bulabilir.
    """
    durum = _onayli_durum("final_thesis")
    _onay_reddet(
        durum, "methodology", gerekce="yöntem gerekçesi eksik", onaylayan=DANISMAN
    )

    assert kapi.kapi_acik_mi(durum, "methodology") is False
    assert kapi.kapi_acik_mi(durum, "findings") is False, (
        "methodology reddedildi ama findings açık kaldı"
    )
    assert kapi.kapi_acik_mi(durum, "final_thesis") is False


# --- 6) denetim / onay ayrımı ----------------------------------------------

def test_final_thesis_critical_bulguyla_acilamaz() -> None:
    """Spec §1: "Denetim geçmesi onay değildir" — ve kritik bulgu geçmez.

    Denetim kaydı `findings: []` içeriyorsa kapı açılır; `critical` bulgu
    varsa açılmaz. Denetimin "koşmuş olması" tek başına yeterli değildir.
    """
    durum = _onayli_durum("final_thesis")
    durum["audit_registry"] = [
        _denetim(
            f"AUD-{i:03d}", tur,
            bulgular=([_kritik_bulgu()] if tur == "citation" else []),
        )
        for i, tur in enumerate(GEREKEN_DENETIMLER, start=1)
    ]

    with pytest.raises((kapi.OnayHatasi, ValueError)):
        _onay_ver(durum, "final_thesis", onaylayan=DANISMAN)

    assert kapi.kapi_acik_mi(durum, "final_thesis") is False


@pytest.mark.parametrize("eksik_tur", GEREKEN_DENETIMLER)
def test_final_thesis_eksik_denetim_turuyle_acilamaz(eksik_tur: str) -> None:
    """Spec §4.7: beş denetim türünün beşi de çalışmış olmalıdır.

    Dört türü temiz, bir türü hiç çalıştırılmamış bir tez "denetlenmiş"
    sayılamaz; eksik tür bilinmezliktir, temiz sonuç değildir.
    """
    durum = _onayli_durum("final_thesis")
    durum["audit_registry"] = [
        _denetim(f"AUD-{i:03d}", tur)
        for i, tur in enumerate(GEREKEN_DENETIMLER, start=1)
        if tur != eksik_tur
    ]

    with pytest.raises((kapi.OnayHatasi, ValueError)):
        _onay_ver(durum, "final_thesis", onaylayan=DANISMAN)

    # Eksik tür ADIYLA bildirilmeli. `denetim_gereksinimleri`'nin dönüş tipi
    # (tür adı mı, insan metni mi) spec'te tanımlı DEĞİL; bu yüzden test
    # içeriği değil varlığını ve türü anmasını sınar.
    engeller = _api("denetim_gereksinimleri")(durum, "final_thesis")
    assert engeller, "eksik denetim türü hiç bildirilmedi"
    assert any(eksik_tur in str(engel) for engel in engeller), (
        f"denetim_gereksinimleri() eksik türü ({eksik_tur}) belirtmiyor: {engeller}"
    )


def test_denetim_gecse_de_insan_onayi_olmadan_kapi_acilmaz() -> None:
    """Beş denetim de temiz, ama insan onayı yok: kapı KAPALI kalır.

    Bu, spec §1'in ayrımının tam hâli: otomatik denetim ile insan kararı
    iki ayrı koşuldur ve ikisi de sağlanmalıdır. Denetimi "onay" sayan bir
    uygulama bu testi kaybeder.
    """
    durum = _dolu_durum()
    assert len(durum["audit_registry"]) == len(GEREKEN_DENETIMLER)
    assert all(not k["findings"] for k in durum["audit_registry"])

    assert kapi.kapi_acik_mi(durum, "final_thesis") is False
    with pytest.raises((kapi.OnayHatasi, ValueError)):
        _onay_ver(durum, "final_thesis", onaylayan=DANISMAN)


# --- 7) bayat denetim -------------------------------------------------------

def test_onaydan_sonra_kritik_denetim_onayi_bayaltir() -> None:
    """Spec §5: denetim de tazeliğe dâhildir.

    Onaydan sonra aynı `audit_type` için FARKLI sonuçlu yeni bir denetim
    yazılırsa onay bayatlar. Aksi halde "denetim geçti diye onay" sonradan
    geçersizleşmiş olurdu ve kapı, eski temizliğe dayanarak açık kalırdı.

    ⚠ KIRMIZI: denetim özeti yalnızca `audit_registry` kapsamda olan kapılarda
    (yani yalnızca `final_thesis`) hesaba katılıyor; ara kapılarda `kapsam`
    alanları veri registry'lerinden ibaret. `findings` kapısı §4.6 gereği
    `evidence` ve `consistency` denetimlerine dayandığı hâlde, bu denetimler
    değiştiğinde onayı bayatlatmıyor.
    """
    durum = _onayli_durum("findings")
    assert kapi.kapi_acik_mi(durum, "findings") is True

    durum["audit_registry"].append(
        _denetim("AUD-006", "evidence", bulgular=[_kritik_bulgu("kanıt eksik")],
                 tarih="2026-02-01")
    )

    assert _onay_stale_mi(durum, "findings") is True, (
        "yeni ve farklı sonuçlu denetim onayı bayatlatmadı"
    )
    assert kapi.kapi_acik_mi(durum, "findings") is False


def test_ayni_sonuclu_yeni_denetim_onayi_baylatmaz() -> None:
    """Kontrol senaryosu: aynı türde TEMİZ yeni denetim onayı bozmamalıdır.

    Bu olmadan, "her yeni denetim bayatlatır" kuralı yüzünden insan her
    `thesis:audit` çalıştırmasında tüm onaylarını yeniden yapmak zorunda
    kalır ve kapı sistemi kullanılamaz hâle gelir.
    """
    durum = _onayli_durum("findings")

    durum["audit_registry"].append(
        _denetim("AUD-006", "evidence", tarih="2026-02-01")
    )

    assert _onay_stale_mi(durum, "findings") is False
    assert kapi.kapi_acik_mi(durum, "findings") is True


# --- 8) girdi enjeksiyonu ---------------------------------------------------

_ZEHR_ALANLARI = ["approved_by", "comment", "rejection_reason"]


@pytest.mark.parametrize("alan", _ZEHR_ALANLARI)
def test_kontrol_karakterleri_temizlenir(alan: str) -> None:
    """NUL/ANSI/SOH/DEL yazılan alan temizlenerek kaydedilmelidir.

    Kontrol karakterleri: konsol kaçışıyla sahte çıktı, satır enjeksiyonuyla
    sahte olay kaydı, NUL ile dosya okuma/ayrıştırma bozulması. Üçü de aynı
    yüzey (kullanıcı/ajan kontrollü serbest metin).
    """
    durum = _onayli_durum("source_set")
    if alan == "rejection_reason":
        kapi.onay_reddet(
            durum, "source_set", gerekce=ZEHIR, onaylayan=DANISMAN
        )
    else:
        _onay_ver(
            durum, "source_set",
            onaylayan=ZEHIR if alan == "approved_by" else DANISMAN,
            yorum=ZEHIR if alan == "comment" else "",
        )

    deger = _kayit(durum, "source_set").get(alan)
    assert isinstance(deger, str), f"{alan} metin değil: {deger!r}"
    assert not _kontrol_karakteri_var(deger), (
        f"{alan} alanında kontrol karakteri kaldı: {deger!r}"
    )


_UZUNLUK_SINIRLARI = [
    ("approved_by", 120, "onay_ver", {"onaylayan": "A" * 4000}),
    ("comment", 2000, "onay_ver", {"yorum": "B" * 5000}),
]


@pytest.mark.parametrize(
    ("alan", "sinir", "isim", "girdi"),
    _UZUNLUK_SINIRLARI,
    ids=[f"{a}<={s}" for a, s, _, _ in _UZUNLUK_SINIRLARI],
)
def test_uzun_metin_sinirlanir(alan: str, sinir: int, isim: str, girdi: dict) -> None:
    """Spec §2: `approved_by` ≤ 120, `comment`/`rejection_reason` ≤ 2000.

    Sınırsız alan, `thesis_state.json`'ı şişirir (disk dolumu) ve kaydı
    okunamaz hâle getirir; sınır, kayıt formatının bir parçasıdır.
    """
    durum = _onayli_durum("source_set")
    _onay_ver(durum, "source_set", **girdi)

    deger = _kayit(durum, "source_set").get(alan)
    assert isinstance(deger, str)
    assert len(deger) <= sinir, f"{alan} {len(deger)} karakter; sınır {sinir}"


def test_zehirli_girdi_dosyayi_bozmaz() -> None:
    """Enjeksiyonlu alanlar diske yazılsa da JSON bütünlüğü korunur.

    Kontrol karakteri + JSON kaçış karakteri (`\\"`, `\\\\`) karışımı:
    dosya yeniden okunabilir, kayıt yine metindir (yapıya dönüşmüyor),
    hiçbir yerde kontrol karakteri kalmaz.
    """
    durum = _onayli_durum("source_set")
    _onay_ver(
        durum, "source_set",
        onaylayan='Daniş"man\\' + ZEHIR,
        yorum='{"approved": true}\n' + ZEHIR,
    )

    metin = json.dumps(durum, ensure_ascii=False, sort_keys=True)
    assert not _kontrol_karakteri_var(metin), (
        "serileştirilmiş durumda kontrol karakteri kaldı"
    )
    assert json.loads(metin) == durum, "JSON gidiş-dönüş durumu bozdu"

    # Zehirli yorum METİN olarak kalmalı: `{"approved": true}` geçerli JSON gibi
    # görünse de kayıt alanı str olmaya devam eder, hiçbir yerde bir nesne
    # alanına dönüşmez. Sınır kontrolü: dosya yeniden okunduğunda yorum hâlâ
    # düz metin olarak aynı yerde duruyor.
    kayit = _kayit(durum, "source_set")
    for alan in ("approved_by", "comment"):
        deger = kayit[alan]
        assert isinstance(deger, str), (
            f"{alan} metin olmaktan çıktı (yapıya dönüştü?): {deger!r}"
        )
    assert '{"approved": true}' in kayit["comment"], (
        "yorum alanı olduğu gibi saklanmadı — içerik dönüştürülüyor"
    )
    assert json.loads(metin)["human_approvals"]["source_set"]["comment"] == (
        kayit["comment"]
    ), "yorum yazma/okuma gidiş-dönüşünde bozuldu"


# --- 9) olay günlüğü (append-only) -----------------------------------------

def test_onay_karar_kimligini_kayda_ve_olaya_yazar() -> None:
    """Spec §2 + §7: onay izi kayıtta da olay günlüğünde de bulunur.

    `human_approvals` anlık durumu, `approval_events` geçmişi tutar; ikisi
    de "kim, neye bakarak, ne zaman" sorusunu yanıtlamak zorundadır.
    """
    durum = _onayli_durum("search_strategy")
    onceki = len(_olaylar(durum))
    _onay_ver(durum, "source_set", onaylayan=DANISMAN, yorum="taslak incelendi")
    olaylar = _olaylar(durum)

    kayit = _kayit(durum, "source_set")
    assert kayit["approved"] is True
    assert kayit["approved_by"] == DANISMAN, "kararı veren kişi kayda yazılmadı"
    assert isinstance(kayit.get("approved_at"), str) and kayit["approved_at"]
    assert str(kayit.get("content_hash", "")).startswith("sha256:"), (
        f"content_hash yok/bozuk: {kayit.get('content_hash')!r}"
    )
    # İlk onay: `search_strategy`'e kadar onaylanmış bir durumda `source_set`
    # henüz hiç onaylanmadığı için sayaç 1'den başlamalı.
    assert kayit.get("revision") == 1, f"revision: {kayit.get('revision')!r}"
    assert isinstance(kayit.get("audit_refs"), list)

    assert len(olaylar) == onceki + 1, "onay için yeni olay yazılmadı"
    olay = olaylar[-1]
    assert olay["gate"] == "source_set"
    assert olay["action"] == "approve"
    assert olay["actor"] == DANISMAN
    assert re.match(r"^\d{4}-\d{2}-\d{2}T", str(olay.get("at", ""))), (
        f"olay anı RFC3339 değil: {olay.get('at')!r}"
    )
    assert olay.get("content_hash") == kayit["content_hash"]


def test_olay_gunlugu_yalnizca_eklenir() -> None:
    """Spec §7: olaylar eklenir, silinmez veya güncellenmez.

    Yaşam döngüsü onay → geri alma → yeniden onay → ret boyunca eski
    kayıtların bayt bayt aynı kaldığı doğrulanır: geçmişin yeniden
    yazılabilmesi, olay günlüğünü kanıt değeri olmaktan çıkarır.
    """
    durum = _onayli_durum("source_set")
    ilk = deepcopy(_olaylar(durum))
    kapi.onay_geri_al(durum, "source_set")
    ikinci = deepcopy(_olaylar(durum))

    assert len(ikinci) > len(ilk), "geri alma yeni olay yazmadı"
    assert ikinci[: len(ilk)] == ilk, "geri alma geçmiş olayları değiştirdi"
    assert ikinci[-1]["action"] == "revoke", f"{ikinci[-1]}"

    for adim in ("research_question", "search_strategy", "source_set"):
        _onay_ver(durum, adim, onaylayan=DANISMAN)
    _onay_reddet(durum, "source_set", gerekce="kaynak kümesi eksik",
                 onaylayan=DANISMAN)
    ucuncu = deepcopy(_olaylar(durum))

    assert len(ucuncu) > len(ikinci), "ret yeni olay yazmadı"
    assert ucuncu[: len(ikinci)] == ikinci, "ret geçmiş olayları değiştirdi"
    assert ucuncu[-1]["action"] == "reject", f"{ucuncu[-1]}"


def test_olay_kimligi_tekil_ve_eylemler_izinli_kumede() -> None:
    """Olay günlüğü bütünlüğü: kimlikler tekil, eylemler izinli kümede."""
    durum = _onayli_durum("findings")
    _onay_reddet(durum, "findings", gerekce="kanıt yok", onaylayan=DANISMAN)
    kapi.onay_geri_al(durum, "findings")
    olaylar = _olaylar(durum)

    kimlikler = [olay.get("event_id") for olay in olaylar]
    assert len(set(kimlikler)) == len(kimlikler), f"çift event_id: {kimlikler}"
    assert all(re.fullmatch(r"EVT-\d{3,}", str(k)) for k in kimlikler), (
        f"event_id biçimi EVT-XXX olmalı: {kimlikler}"
    )
    eylemler = {olay.get("action") for olay in olaylar}
    assert eylemler <= IZINLI_EYLEMLER, f"izinli olmayan eylem: {eylemler}"


# --- 10) CLI düzeyinde atlatma ---------------------------------------------

def _cli(depo: Path, *args: str) -> subprocess.CompletedProcess:
    """CLI'yi GERÇEK bir alt süreç olarak çalıştırır.

    Aynı süreç içinde `main()` çağırmak, `sys.argv` kirletmesi ve çıktı
    yakalama kaybı yüzünden yanlış yeşil verebilir. Atlatma yüzeyi burada
    süreç sınırıdır; bu yüzden alt süreç.
    """
    ortam = dict(os.environ)
    ortam["PYTHONPATH"] = str(REPO_ROOT)
    ortam["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, "-m", "tools.atw.cli", *args],
        cwd=str(depo), env=ortam, capture_output=True,
        text=True, encoding="utf-8", timeout=180,
    )


def _dosyaya_yaz(depo: Path, durum: dict) -> Path:
    yol = depo / "thesis_state.json"
    yol.write_text(json.dumps(durum, ensure_ascii=False, indent=2), encoding="utf-8")
    return yol


def _onaylayan_bayragi() -> list[str]:
    """`approve` alt komutunun onaylayan bayrağını keşfeder.

    Spec §2 `approved_by`'yi zorunlu kılıyor ama bayrağın ADINI sabitlemiyor.
    Testin konusu bayrağın adı değil, onayın durumu değiştirmesidir.
    """
    yardim = _cli(REPO_ROOT, "approve", "--help").stdout
    for bayrak in ("--approved-by", "--approver", "--actor", "--by"):
        if bayrak in yardim:
            return [bayrak, DANISMAN]
    return []


def test_cli_kapilar_kapaliyken_basarisiz_ve_dosya_ayni(tmp_path: Path) -> None:
    """Katta 10: süreç `CIKIS_SORUN` döner ve durum dosyası BİT BIT AYNIDIR.

    1) `approve final_thesis` — zincirin sonu doğrudan açılmaya çalışılır.
    2) `approve hacker_gate` — tablo dışı adla kapı yaratma.

    Aynı test, katman 12'yi de kapsar: yarım yazım olmadığı gibi geçici
    dosya artığı da bırakılmamalıdır.
    """
    durum = _dolu_durum()
    yol = _dosyaya_yaz(tmp_path, durum)
    onceki = yol.read_bytes()

    sonuc = _cli(tmp_path, "approve", "final_thesis")
    assert sonuc.returncode == 1, (
        f"kapılar kapalıyken süreç 0 döndü (CIKIS_SORUN beklenir):\n"
        f"{sonuc.stdout}\n{sonuc.stderr}"
    )
    assert yol.read_bytes() == onceki, "başarısız onay durumu dosyasını DEĞİŞTİRDİ"
    assert json.loads(yol.read_text(encoding="utf-8")) == durum, "dosya bozuldu"

    bilinmeyen = _cli(tmp_path, "approve", "hacker_gate")
    assert bilinmeyen.returncode == 1, (
        f"bilinmeyen kapı 0 döndü:\n{bilinmeyen.stdout}"
    )
    assert yol.read_bytes() == onceki, "bilinmeyen kapı durumu dosyasını DEĞİŞTİRDİ"

    artiklar = [p.name for p in tmp_path.iterdir() if p.name != "thesis_state.json"]
    assert artiklar == [], f"başarısız komut geçici dosya bıraktı: {artiklar}"


def test_cli_gerekesiz_ret_reddedilir(tmp_path: Path) -> None:
    """Spec §6: ret komutu olmalı, gerekçesiz ret reddedilmeli.

    Spec §6 CLI'yi açıkça yazıyor: ``thesis:approve <kapı> --reject --reason
    "..."``. Yani (a) ``--reject``/``--reason`` bayrakları mevcut olmalı,
    (b) gerekçe boşken ret `CIKIS_SORUN` döndürmeli ve dosyayı değiştirmemeli.

    ⚠ KIRMIZI: `approve` alt komutunda `--reject`/`--reason` bayrağı YOK;
    argparse komutu "unrecognized arguments" diyerek 2'de kesiyor. Ret yüzeyi
    yalnızca kütüphanede var, insanın kullanabileceği tek yüzeyde yok.
    """
    durum = _dolu_durum()
    yol = _dosyaya_yaz(tmp_path, durum)
    onceki = yol.read_bytes()

    ret = _cli(tmp_path, "approve", "findings", "--reject")
    assert ret.returncode == 1, (
        f"gerekçesiz ret CIKIS_SORUN(=1) dönmeliydi, {ret.returncode} döndü.\n"
        f"Spec §6 `--reject --reason` yüzeyi eksikse ret insan tarafından "
        f"kullanılamaz.\n{ret.stdout}\n{ret.stderr}"
    )
    assert yol.read_bytes() == onceki, "başarısız ret durumu dosyasını DEĞİŞTİRDİ"


def test_cli_basarili_onay_durumu_degistirir(tmp_path: Path) -> None:
    """Kontrol: doğru kullanımda kapı AÇILIR ve dosya değişir.

    Bu olmadan, "başarısız komut dosyayı değiştirmedi" testi boş bir gerçek
    olur: dosyayı hiç yazmayan bir yardımcı da aynı testi geçirirdi.
    """
    durum = _dolu_durum()
    yol = _dosyaya_yaz(tmp_path, durum)
    onceki = yol.read_bytes()

    sonuc = _cli(tmp_path, "approve", "research_question", *_onaylayan_bayragi())
    assert sonuc.returncode == 0, f"geçerli onay reddedildi:\n{sonuc.stdout}\n{sonuc.stderr}"
    assert yol.read_bytes() != onceki, "geçerli onay durumu değiştirmedi"
    assert kapi.kapi_acik_mi(json.loads(yol.read_text(encoding="utf-8")),
                             "research_question") is True


# --- 11) atomiklik: kısmi yazım yok ----------------------------------------

_BASARISIZ_ISLEMLER = [
    ("onay", lambda d: kapi.onay_ver(d, "final_thesis")),  # atlanan akış
    ("ret", lambda d: kapi.onay_reddet(d, "final_thesis")),  # gerekçesiz ret
]


@pytest.mark.parametrize(
    ("ad", "islem"), _BASARISIZ_ISLEMLER, ids=[a for a, _ in _BASARISIZ_ISLEMLER]
)
def test_basarisiz_islem_durumu_kismi_degistirmez(ad: str, islem: Callable) -> None:
    """Katman 12: başarısız işlem, durumu YARIM değiştiremez.

    Reddedilen bir onayın `approved_by`'i yazıp `approved`'ı yazamaması,
    sonraki sürecin "onaylı ama kimse onaylamamış" gibi bir kayıt bulmasına
    yol açar. Hata, yazmadan ÖNCE gelmelidir.
    """
    durum = _onayli_durum("methodology")
    onceki = json.dumps(durum, ensure_ascii=False, sort_keys=True)

    with pytest.raises((TypeError, ValueError, kapi.OnayHatasi)):
        islem(durum)

    assert json.dumps(durum, ensure_ascii=False, sort_keys=True) == onceki, (
        f"{ad}: başarısız işlem durumu kısmen değiştirdi"
    )


# --- 12) META: sıfır atlatma özeti -----------------------------------------

@pytest.mark.parametrize("kapi_adi", APPROVAL_GATES)
def test_ozet_kapi_sifir_bypass(kapi_adi: str) -> None:
    """Yedi kapının HİÇBİRİ, hiçbir ön koşul sağlanmadan açılamaz.

    Sıra atlamadan bağımlılık grafiğine, boş kapıdan ret gerekçesine kadar
    bütün tekil testlerin özeti: en zayıf durumda, sıfır onayla, hiçbir
    kapı açılmamalıdır. Bir istisna olarak geçerse sistem, saldırgana
    sıfır maliyetli bir atlatma yolu vermiş demektir.

    ⚠ KIRMIZI (yalnızca `research_question`): kök kapının bağımlılığı yoktur,
    dolayısıyla onu yalnızca §4.1'in önkoşulu (`research_questions` en az bir
    soru içerir) koruyabilir — `onay_ver` o önkoşulu denetlemediği için
    BOŞ bir durumda `research_question` açılabiliyor. Bkz.
    `test_bos_registry_ile_kapi_onaylanamaz`.
    """
    durum = _kapili_durum()
    with pytest.raises((kapi.OnayHatasi, ValueError)):
        _onay_ver(durum, kapi_adi, onaylayan=DANISMAN)
    assert kapi.kapi_acik_mi(durum, kapi_adi) is False
    assert not any(durum["human_approvals"].values()), (
        f"{kapi_adi} atlatıldı: {durum['human_approvals']}"
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v", "-o", "addopts="]))
