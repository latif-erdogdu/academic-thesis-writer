"""Insan onayi kapilari: PRISMA akisinin 7 asamasini kapiya baglar.

Neden bu modul gerekiyor
-------------------------
``state.APPROVAL_GATES`` 7 kapinin adini soyluyordu, ama HICBIR YERDE
zorlanmiyordu. Durumda kapilar ``False`` olarak basliyor ve oyle kaliyordu;
`cmd_status` yalnizca sayiyordu. Yani "her yazim oturumunda insan onayi
zorunlu" vaadi (skill.yaml) kodda hicbir sey ifade etmiyordu.

PRISMA (Preferred Reporting Items for Systematic Reviews and Meta-Analyses)
akisi: kaynak secimi, tarama, eleme ve sentez insan kararidir. Bir
asamanin ciktisi, onceki asama onaylanmadan uretilmemelidir.

Dort kavram ayridir
-------------------
  onay    -> insan bir karari VERDI, kapı acildi       (human_approvals)
  hazir   -> verilen karari uygulamaya hazir veri var  (write, export)
  denetim -> otomatik denetim bulgu uretti             (audit_registry)
  tazelik -> onay verildikten sonra icerik degisti mi  (content_hash)

`kapi_acik_mi()` ilk ikisinden yalniz "onay"i sorar ve BAYAT onayi kapali
sayar. `kontrol_yaz()` onaya ek olarak hazirligi ve denetim gereklerini de
dener; yalniz "onay var" demek, bos bir capaya onay vermis olmak kadar
anlamsizdir.

Denetim onay degildir
---------------------
`thesis:audit` bir kapiyi ACAMAZ. Denetim gecmis olmak icin kapinin
insan onayi yine ayrica gerekir. Tersi de gecerlidir: `final_thesis`
kapisi, bes denetim turunun de gecmis olmasini ve hicbirinde `critical`
bulgu bulunmamasini ister. Ikisi ayri kosuldur.

Kapsam ilkesi
-------------
Bu modul KALDIYLA degil, veriyle karar verir. Onaylanmamis bir asamayi
otomatik gecmek mumkun degildir; onun yerine eksigi ADIYLA bildirir.

Kanitik sozlesme
----------------
`references/approval_gates.md` bu modelin kanonik spesifikasyonudur. Kod
ile dokuman celisirse kod yanlistir.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from tools.atw.graph import (
    kanitsiz_iddialar,
    kopuk_baglari,
    registry_haritasi,
    retraksiyona_ugrayan_iddialar,
)
from tools.atw.state import APPROVAL_GATES

# Uzunluk sinirlari. Girdi temizlemede kullanilir; semada da ayni sinirlar
# vardir. Iki tarafin ayrilmasi, kodun semayi bilmedigi durumda sessizce
# gecersiz kayit yazmasina yol acar; bu yuzden testler ikisini birlikte
# dogrular.
UZUNLUK_SINIRI = {"approved_by": 120, "comment": 2000, "rejection_reason": 2000}

# Kontrol karakterleri (0x00-0x1F ve 0x7F). ANSI kaçis dizileri de bunlarin
# icinde; `yorum` alanina yazilan bir `\x1b[2J` ekranı temizleyebilirdi.
_KONTROL_KARAKTER = re.compile(r"[\x00-\x1f\x7f]")


def temizle(metin: Any, en_fazla: int) -> str | None:
    """Serbest metin alanini tasinabilir hale getirir.

    Yapilanlar:
      * kontrol karakterleri ( satir sonu, sekme, ANSI kacisi, NUL ) atilir
      * ardisik bosluklar tek bosluga indirgenir, bastan/sondan kirpilir
      * `en_fazla` karakterden sonrasi kesilir
      * sonuc bos ise ``None`` doner

    Neden kirpma ucuz ama gerekli: durum dosyasi JSON'dur, kontrol
    karakterleri dosyayi bozmaz; ancak `status`/`approve --list` ciktisi
    terminale yazildiginda ekran bozulur ve kayit asil kaynaklastirilamaz.
    """
    if metin is None:
        return None
    if not isinstance(metin, str):
        metin = str(metin)
    metin = _KONTROL_KARAKTER.sub(" ", metin)
    metin = " ".join(metin.split()).strip()
    if not metin:
        return None
    if len(metin) > en_fazla:
        metin = metin[:en_fazla].rstrip()
    return metin or None


@dataclass(frozen=True)
class GateSozlesmesi:
    """Bir kapinin tam sozlesmesi.

    Alanlar
    -------
    kapi
        Kapinin adi (`APPROVAL_GATES` icinde olmali).
    bagimlilik
        Bu kapinin ACILMASI icin dogrudan acik olmasi gereken kapilar.
        Siraya degil acik listeye dayanir: akis sirasi tesadufi degisse de
        kapinin acilma kosulu degismez.
    kapsam
        Onay aninda kapsanan ve icerik ozetiyle korunan durum alanlari.
        Onaydan sonra bu alanlardan biri degisirse onay bayatlar.
    registry
        Bos olmamasi gereken registry alanlari (on kosul).
    denetim_turleri
        Bu kapinin dayandigi denetim turleri. `final_thesis` icin
        ZORUNLUDUR; ara kapilarda yalniz `critical` bulgu varsa engeldir.
    on_kosul / son_kosul
        Insan-okur metin. `references/approval_gates.md` ile ayni olmali.
    """

    kapi: str
    bagimlilik: tuple[str, ...]
    kapsam: tuple[str, ...]
    registry: tuple[str, ...]
    denetim_turleri: tuple[str, ...]
    on_kosul: tuple[str, ...]
    son_kosul: tuple[str, ...]


_GATE_TANIMLARI: tuple[GateSozlesmesi, ...] = (
    GateSozlesmesi(
        kapi="research_question",
        bagimlilik=(),
        kapsam=("research_questions",),
        registry=("research_questions",),
        denetim_turleri=(),
        on_kosul=(
            "`research_questions` en az bir soru icerir.",
            "Her sorunun `id`, `question`/`text` ve `type` alani doludur.",
        ),
        son_kosul=("Arastirma sorulari tanimlidir ve hicbiri `pending` degildir.",),
    ),
    GateSozlesmesi(
        kapi="search_strategy",
        bagimlilik=("research_question",),
        kapsam=("search_runs",),
        registry=("search_runs",),
        denetim_turleri=(),
        on_kosul=(
            "`search_runs` en az bir kayit icerir.",
            "Her kayit hangi soruyu (`rq_id`) taradigini ve hangi veri tabanini "
            "kullandigini belirtir.",
        ),
        son_kosul=("Her arastirma sorusu en az bir tarama kosusuna baglidir.",),
    ),
    GateSozlesmesi(
        kapi="source_set",
        bagimlilik=("search_strategy",),
        kapsam=("sources",),
        registry=("sources",),
        denetim_turleri=(),
        on_kosul=(
            "`sources` en az bir kaynak icerir.",
            "Her kaynagin `doi` veya `url` alanindan en az biri doludur.",
        ),
        son_kosul=(
            "Kaynak kumesi tanimlidir ve hicbir kaynak geri cekilmis "
            "(`retracted`) degildir.",
        ),
    ),
    GateSozlesmesi(
        kapi="research_gap",
        bagimlilik=("source_set",),
        kapsam=("gap_registry", "sources"),
        registry=("gap_registry",),
        denetim_turleri=(),
        on_kosul=(
            "`gap_registry` en az bir bosluk icerir.",
            "Her bosluk `statement` ve dayanak kaynak kimlikleri tasir.",
        ),
        son_kosul=(
            "Literatürdeki bosluk kanitlanmistir; bosluk beyani uydurma "
            "kaynakla desteklenemez.",
        ),
    ),
    GateSozlesmesi(
        kapi="methodology",
        bagimlilik=("research_gap",),
        # `research_questions` BILINCLI OLARAK kapsam disinda. Sorunun
        # `status` alani calisma ilerledikce `pending` -> `answered` olur;
        # bu bir yontem degisikligi degil, isin dogal sonucudur. Kapsama
        # alinsa `cmd_write` (bu kapiya bagli) kendi onayini bayatlatirdi
        # ve yazim dongusu kilitlenirdi.
        kapsam=(
            "methodology",
            "hypotheses",
            "conceptual_framework",
            "datasets",
            "variables",
            "analyses",
            "statistics",
            "audit_registry",
        ),
        # `chapters` de kapsam disinda: bu kapinin on kosulu, kapinin
        # yazdirdigi seyin kendisiydi. `chapters`'i dolduran tek yol
        # `cmd_write`, o da `methodology` kapisinin arkasinda. Boylece ilk
        # bolum yazilamiyordu. Ayrinti:
        # `test_methodology_kapisi_bos_bolumle_yazilabilir`.
        registry=(),
        denetim_turleri=("methodology",),
        on_kosul=(
            "Her `research_questions` kaydi `status` alanina sahiptir.",
            "`pending` soru varsa gerekce (`unanswerable_reason`) zorunludur.",
        ),
        son_kosul=(
            "Yontem, her arastirma sorusunun yanitlanip yanitlanamayacagini "
            "gerekcesiyle birlikte belirtir.",
            "Yanitlanamayan soru sessizce atlanmaz.",
        ),
    ),
    GateSozlesmesi(
        kapi="findings",
        bagimlilik=("methodology",),
        # `audit_registry` kapsamdadir: kapının dayandigi `evidence` ve
        # `consistency` denetimlerinin bulgu basliklari ozete girer. Onaydan
        # sonra `critical` bulgu uretildiginde bu kapinin onayi bayatlar —
        # "denetim onay degildir" ilkesinin onay tarafındaki karsiligi.
        kapsam=(
            "findings_registry",
            "evidence_registry",
            "claims_registry",
            "audit_registry",
        ),
        registry=("findings_registry",),
        denetim_turleri=("evidence", "consistency"),
        on_kosul=(
            "`findings_registry` en az bir bulgu icerir.",
            "Her bulgunun `evidence_ids` listesi bos degildir.",
        ),
        son_kosul=(
            "Her bulgu en az bir kanit kaydina baglidir; kanitsiz bulgu "
            "onaylanabilir degildir.",
        ),
    ),
    GateSozlesmesi(
        kapi="final_thesis",
        bagimlilik=("findings",),
        kapsam=(
            "chapters",
            "paragraphs",
            "citations",
            "sources",
            "evidence_registry",
            "claims_registry",
            "findings_registry",
            "discussion_registry",
            "conclusion_registry",
            "audit_registry",
        ),
        registry=(),
        denetim_turleri=(
            "citation",
            "methodology",
            "consistency",
            "integrity",
            "evidence",
        ),
        on_kosul=(
            "`chapters` en az bir bolum icerir.",
            "Her bolumde metni olan en az bir paragraf vardir.",
            "Butunluk taramasi bos doner: kopuk referans, kanitsiz iddia, "
            "geri cekilmis kaynak yoktur.",
        ),
        son_kosul=(
            "Tez aktarilabilir: hicbir metinde gosterilen kaynak `sources` "
            "icindedir, hicbiri geri cekilmemistir.",
            "Kaynakca yalnizca gercekten atif yapilan kaynaklari icerir.",
        ),
    ),
)

GATE_KOSULLARI: dict[str, GateSozlesmesi] = {t.kapi: t for t in _GATE_TANIMLARI}

#: Kapinin dogrudan bagimli oldugu kapilar. Siradan turetilmez; acik
#: listedir.
GATE_BAGIMLILIK: dict[str, tuple[str, ...]] = {
    kapi: sozlesme.bagimlilik for kapi, sozlesme in GATE_KOSULLARI.items()
}

#: Hangi kapinin hangi denetim turlerini ZORUNLU istedigi. Yalniz
#: teslim kapisi (`final_thesis`) icin denetim kaydi olmadan onay verilemez;
#: ara kapilarda denetim henuz calismamis olabilir, ama calistiginda
#: `critical` bulgu varsa kapı kapanir.
ZORUNLU_DENETIM_KAPILARI: frozenset[str] = frozenset({"final_thesis"})

# Geriye uyum: eski modul API'si. `GATE_ASAMALARI` degerleri sozlesmenin
# `registry` alanidir; degerler HICBIR ZAMAN okunmaz, yalnizca uyelik
# denetimi ve belge amaci tasir.
GATE_ASAMALARI: dict[str, tuple[str, ...]] = {
    kapi: sozlesme.registry for kapi, sozlesme in GATE_KOSULLARI.items()
}


class OnayHatasi(RuntimeError):
    """Kapi acilmadan once bir asamaya girilmeye calisildi."""


# --- icerik ozeti ------------------------------------------------------------


def _denetim_projeksiyonu(
    durum: dict[str, Any], turler: tuple[str, ...]
) -> dict[str, Any]:
    """Denetim kayitlarinin OZETI: turun kendisi ve bulgu basliklari.

    Neden ham kayit degil

    `audit_registry` her calistirmada yeni bir kayit alir; ayni sonucu
    ureten ikinci bir calistirma bile `audit_id` ve `date` degistirir. Ham
    kayit ozete girseydi, ayni bulgularla tekrarlanan bir denetim onayi
    bayatlatirdi — kullaniciye "bir sey degismedi ama onayiniz gecersiz"
    demenin bir yolu yok.

    Bu yuzden yalniz `audit_type` ve bulgu `(severity, message)` ciftleri
    projeye edilir. Ayni bulgular -> ayni ozet -> onay gecerli kalir. Yeni
    ve farkli bulgu -> farkli ozet -> onay bayatlar.

    "En son" kayit liste SONUDUR: `audit_registry` yalnizca eklenen bir
    dizidir, tarih alanina guvenilmez.
    """
    kayitlar = [k for k in (durum.get("audit_registry") or []) if isinstance(k, dict)]
    projeksiyon: dict[str, Any] = {}
    for tur in sorted(turler):
        eslesen = [k for k in kayitlar if k.get("audit_type") == tur]
        if not eslesen:
            projeksiyon[tur] = None
            continue
        bulgular = eslesen[-1].get("findings") or []
        projeksiyon[tur] = sorted(
            f"{b.get('severity', '')}|{b.get('message', '')}"
            for b in bulgular
            if isinstance(b, dict)
        )
    return projeksiyon


def icerik_ozeti(durum: dict[str, Any], kapi: str) -> str:
    """Kapinin on kosulu olan icerigin kisa SHA-256 ozeti.

    Donus bicimi: ``sha256:<16 hex>``.

    Ozete giren alanlar `GATE_KOSULLARI[kapi].kapsam` ile belirlenir.
    Kapsam disindaki degisiklikler (orn. `source_set` onayinda `chapters`
    degisikligi) ozeti BOZMAZ; kapsam icindekiler bozar.
    """
    if kapi not in GATE_KOSULLARI:
        raise ValueError(f"bilinmeyen onay kapisi: {kapi}")
    sozlesme = GATE_KOSULLARI[kapi]
    parcalar: dict[str, Any] = {}
    for alan in sozlesme.kapsam:
        if alan == "audit_registry":
            parcalar[alan] = _denetim_projeksiyonu(durum, sozlesme.denetim_turleri)
        else:
            parcalar[alan] = durum.get(alan)
    ham = json.dumps(parcalar, ensure_ascii=False, sort_keys=True, default=str)
    return "sha256:" + hashlib.sha256(ham.encode("utf-8")).hexdigest()[:16]


# --- kayit normalizasyonu ----------------------------------------------------


def _kayit(durum: dict[str, Any], kapi: str) -> dict[str, Any]:
    """`human_approvals[kapi]` degerini tek bicimde bir sozluk olusturur.

    Uc bicim desteklenir:
      * ``False``/eksik  -> kapali
      * ``True``          -> ACIK ama `attested: False` (eski dosyalar)
      * nesne             -> tam kayit

    Eski `True` bicimi icerik ozeti tasimadigi icin tazelik denetimi
    yapilamaz. Bu, geriye uyumun bedeli ve acikca belgelenmis bir
    sinirdir: `attested: False` degeri ve `approval_events` gunlugundeki
    kayit yoksunlugu, elle yazilmis bir onayi tespit edilebilir kilar.
    """
    if kapi not in GATE_KOSULLARI:
        raise ValueError(f"bilinmeyen onay kapisi: {kapi}")
    ham = (durum.get("human_approvals") or {}).get(kapi, False)
    if isinstance(ham, dict):
        kayit = dict(ham)
        kayit.setdefault("approved", False)
        kayit.setdefault("revision", 1)
        return kayit
    return {
        "approved": bool(ham),
        # `False` -> 0: kapı hiç açılmamış, ilk `onay_ver` 1 yazmalıdır.
        # `True`  -> 1: eski dosyada kapı bir kez açılmış demektir.
        "revision": 1 if ham else 0,
        "attested": False,
        "content_hash": None,
        "approved_by": None,
        "approved_at": None,
        "comment": None,
        "rejection_reason": None,
        "audit_refs": [],
    }


def onay_stale_mi(durum: dict[str, Any], kapi: str) -> bool:
    """Onay verildikten sonra kapsanan icerik degisti mi?

    `True` dondugunde `kapi_acik_mi` de `False` doner; yani bayat onay
    "acik" sayilmaz. Bu, onayin icerik degistikce kendiliginden
    gecersizlesmesidir (immutable onay).

    Eski `True` biciminde hash yoktur; tazelik tespit edilemedigi icin
    `False` doner. `attested: False` ile bu ayrim gorunur kilinir.
    """
    kayit = _kayit(durum, kapi)
    if not kayit.get("approved"):
        return False
    kayitli = kayit.get("content_hash")
    if not kayitli:
        return False
    return kayitli != icerik_ozeti(durum, kapi)


def kapi_acik_mi(durum: dict[str, Any], kapi: str) -> bool:
    """Verilen kapi insan tarafindan onaylanmis VE taze mi?

    Taninmayan kapi adi hata verir; sessizce "kapali" donmek, kapi
    sistemine eklenen ama burada unutulan bir asamayi gizlerdi.
    """
    if kapi not in GATE_KOSULLARI:
        raise ValueError(f"bilinmeyen onay kapisi: {kapi}")
    kayit = _kayit(durum, kapi)
    if not kayit.get("approved"):
        return False
    return not onay_stale_mi(durum, kapi)


# --- bagimlilik ve denetim engelleri ----------------------------------------


def bagimlilik_engelleri(durum: dict[str, Any], kapi: str) -> list[str]:
    """Bu kapinin acilmasi icin eksik dogrudan bagimliliklari dondurur.

    Sira denetimi degil, ACIK BAGIMLILIK denetimidir. `APPROVAL_GATES`
    sirasi tesadufi degisse bile kapi acilma kosulu degismez.
    """
    if kapi not in GATE_KOSULLARI:
        raise ValueError(f"bilinmeyen onay kapisi: {kapi}")
    return [
        f"'{bagimli}' kapısı henüz onaylı değil"
        for bagimli in GATE_BAGIMLILIK[kapi]
        if not kapi_acik_mi(durum, bagimli)
    ]


def denetim_gereksinimleri(durum: dict[str, Any], kapi: str) -> list[str]:
    """Kapiyi kapatan denetim sorunlarini dondurur; sorun yoksa liste bos.

    Iki kural birlikte:

    1. ZORUNLU denetim turleri icin kayit olmamasi (yalniz `final_thesis`).
       Denetim kaydi yoksa "denetim gecti" denemez; teslim kapisi bunu
       kabul etmez.
    2. Kapinin dayandigi her denetim turunde `critical` bulgu. Bu kural
       TUM kapilar icin gecerlidir: `methodology` denetimi `critical`
       bulgu uretmisse `methodology` kapisi acilmaz.
    """
    if kapi not in GATE_KOSULLARI:
        raise ValueError(f"bilinmeyen onay kapisi: {kapi}")
    sozlesme = GATE_KOSULLARI[kapi]
    kayitlar = [k for k in (durum.get("audit_registry") or []) if isinstance(k, dict)]
    sorunlar: list[str] = []
    for tur in sozlesme.denetim_turleri:
        eslesen = [k for k in kayitlar if k.get("audit_type") == tur]
        if not eslesen:
            if kapi in ZORUNLU_DENETIM_KAPILARI:
                sorunlar.append(
                    f"'{tur}' denetimi hiç çalıştırılmamış — "
                    f"`thesis:audit --type {tur}` çalıştırılmalı"
                )
            continue
        kritikler = [
            b.get("message", "")
            for b in (eslesen[-1].get("findings") or [])
            if isinstance(b, dict) and b.get("severity") == "critical"
        ]
        if kritikler:
            sorunlar.append(
                f"'{tur}' denetiminde {len(kritikler)} critical bulgu: "
                f"{kritikler[0]}"
            )
    return sorunlar


# --- olay gunlugu ------------------------------------------------------------


def _olay_yaz(
    durum: dict[str, Any],
    kapi: str,
    eylem: str,
    *,
    aktör: str | None = None,
    an: str | None = None,
    icerik_ozeti_deger: str | None = None,
    gerekce: str | None = None,
    yorum: str | None = None,
    denetim_idleri: list[str] | None = None,
) -> dict[str, Any]:
    """`approval_events` dizisine bir olay EKLER.

    Gunluk yalnizca buyur; guncelleme veya silme YAPILMAZ. Gecmis bir olayin
    uzerine yazmak, "kim ne zaman neyi onayladi" sorusunu cevaplanamaz
    hale getirirdi.
    """
    gunluk = durum.setdefault("approval_events", [])
    if not isinstance(gunluk, list):
        gunluk = []
        durum["approval_events"] = gunluk
    olay = {
        "event_id": f"EVT-{len(gunluk) + 1:04d}",
        "gate": kapi,
        "action": eylem,
        "actor": temizle(aktör, UZUNLUK_SINIRI["approved_by"]),
        "at": an or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "content_hash": icerik_ozeti_deger,
        "reason": temizle(gerekce, UZUNLUK_SINIRI["rejection_reason"]),
        "comment": temizle(yorum, UZUNLUK_SINIRI["comment"]),
        "audit_refs": sorted(denetim_idleri or []),
    }
    gunluk.append(olay)
    return olay


# --- karar yazma -------------------------------------------------------------


def _sonraki_kapilar(kapi: str) -> list[str]:
    """Verilen kapidan sonra gelen kapilar (akis sirasina gore)."""
    return APPROVAL_GATES[APPROVAL_GATES.index(kapi) + 1 :]


def _bagimli_kapilari_kapat(durum: dict[str, Any], kapi: str) -> list[str]:
    """`kapi`ya bagli olarak ACILMIS kapilari kapatir, kapananlari doner.

    Ortak kural: bir kapinin dayandigi onay gecersizlestiginde, o kapiya
    dayanan onaylar da gecersizlestirilir. Aksi halde "methodology geri
    alindi ama final_thesis onayli" gibi, hicbir yerde yazili olmayan bir
    durum olusur. `onay_geri_al` ve `onay_reddet` ayni kurali paylasir;
    farklari yalniz ret gerekcesinin kaydedilmesidir.

    Yalniz halihazirde ACIK olan kapilar yazilir. Kapali bir kapinin
    kaydina dokunmak, sonraki `onay_ver` cagrisinin `revision` sayacini
    bozardi; kapali kapinin durumu zaten dogru.
    """
    onaylar = durum.setdefault("human_approvals", {})
    kapanan: list[str] = []
    for hedef in _sonraki_kapilar(kapi):
        mevcut = onaylar.get(hedef)
        # Eski bicim (`true`) de acik sayilir. `onay_ver` icin geriye
        # uyum destekleniyorsa, geri alma da ayni veriyi tanimali: aksi
        # halde eski bir durumda "bagimli kapilari kapat" sessizce hicbir
        # sey yapamaz ve "methodology geri alindi ama findings onayli"
        # gibi tutarsiz durum olusur.
        if not (mevcut is True or (isinstance(mevcut, dict) and mevcut.get("approved"))):
            continue
        onaylar[hedef] = {
            "approved": False,
            # Sema `revision >= 1` istiyor; hic acilmamis bir kapi
            # kapatildiginda sayac 0'da kalir, bu yuzden alta birden baslanir.
            "revision": max(
                1, int(mevcut.get("revision") or 0) if isinstance(mevcut, dict) else 1
            ),
            "approved_by": None,
            "approved_at": None,
            "content_hash": None,
            "comment": None,
            "rejection_reason": None,
            "audit_refs": [],
        }
        kapanan.append(hedef)
    return kapanan


def onay_ver(
    durum: dict[str, Any],
    kapi: str,
    *,
    onaylayan: str | None = None,
    yorum: str | None = None,
    denetim_idleri: list[str] | None = None,
    saat: str | None = None,
) -> dict[str, Any]:
    """Kapiyi acar ve durumu gunceller.

    Dort kosulun HEPPSI burada zorlanir; kapiyi acmanin tek yolu budur:

      1. bagimlilik -> dogrudan bagimli kapilar acik ve taze mi
      2. hazirlik   -> on kosul registry'leri dolu mu
      3. denetim    -> kapinin dayandigi denetim gecmis ve temiz mi
      4. kimlik     -> karari veren kisi belli mi

    Neden CLI'da degil de burada
    --------------------------
    `onay_ver` kamuya acik bir kutuphane yuzeyidir. Hazirlik denetimini
    yalniz `cmd_approve` icinde birakmak, CLI kullanmayan bir ajan icin
    bos bir kapiyi onaylama bypass'iydi: ayni karar, iki farkli yerde,
    iki farkli kural. Denetim CLI'da tekrarlanir — kullaniciya engelleri
    gostermek icin — ama karar YALNIZ burada verilir.

    Dairesellik yoktur: `GATE_HAZIRLIK` icinde `methodology` ve
    `final_thesis` YOKTUR, cunku bu iki kapinin ciktisi kendi
    arklarindaki komutla uretilir. Bkz. `GATE_HAZIRLIK` yorumu.

    KIMLIK ZORUNLUDUR
    -----------------
    `onaylayan` verilmezse kapI ACILMAZ. Aksi halde kayit
    `approved_by: null` ile yazilir ve "bu onayi kim verdi" sorusunun
    cevabi kaybolur; sistem kendi urettigi icerigi kendi onaylamis
    sayilir. Bu, sozlesmenin merkezindeki ilkedir: **ajan kendi
    onayini yazamaz.**

    Bosluk ve yalnizca bosluk iceren degerler de kimlik sayilmaz;
    `temizle()` kirpildigi icin denetleme kirpma SONRASI yapilir ve
    kayda giren deger dogrulanan degerin kendisidir.

    Muafiyet: `onay_geri_al` icin aktzor gerekli DEGILDIR. Geri alma
    kapiyi kapatir, yani guvenlik yonu "daha az izin ver" yonudur.
    Bkz. `onay_geri_al`.
    """
    if kapi not in GATE_KOSULLARI:
        raise ValueError(f"bilinmeyen onay kapisi: {kapi}")

    eksik = bagimlilik_engelleri(durum, kapi)
    if eksik:
        raise OnayHatasi(
            f"'{kapi}' kapisi acilamiyor: onceki asamalar onayli degil -> "
            + ", ".join(eksik)
        )
    hazirlik = hazirlik_engelleri(durum, kapi)
    if hazirlik:
        raise OnayHatasi(
            f"'{kapi}' kapisi acilamiyor: veri hazir degil -> "
            + "; ".join(hazirlik)
        )
    denetim_engel = denetim_gereksinimleri(durum, kapi)
    if denetim_engel:
        raise OnayHatasi(
            f"'{kapi}' kapisi acilamiyor: denetim gecmemiş -> "
            + "; ".join(denetim_engel)
        )
    # Kimlik denetimi BILINCLI OLARAK en sona konur: yukaridaki
    # kosullardan biri ihlal edildiyse o kosulun adi soylenmelidir.
    temiz_onaylayan = temizle(onaylayan, UZUNLUK_SINIRI["approved_by"])
    if not temiz_onaylayan:
        raise OnayHatasi(
            f"'{kapi}' kapisi icin onaylayan zorunludur: karari veren "
            "kisinin adi yazilmali (CLI: --by \"Ad Soyad\"). Kim onayladi "
            "bilinmeden onay kaydi onay zincirini denetimsiz birakir."
        )

    onceki = _kayit(durum, kapi)
    an = saat or datetime.now(timezone.utc).isoformat(timespec="seconds")
    ozet = icerik_ozeti(durum, kapi)
    denetimler = sorted(denetim_idleri or [])

    durum.setdefault("human_approvals", {})[kapi] = {
        "approved": True,
        "revision": int(onceki.get("revision") or 0) + 1,
        "approved_by": temiz_onaylayan,
        "approved_at": an,
        "content_hash": ozet,
        "comment": temizle(yorum, UZUNLUK_SINIRI["comment"]),
        "rejection_reason": None,
        "audit_refs": denetimler,
    }
    _olay_yaz(
        durum,
        kapi,
        "approve",
        aktör=onaylayan,
        an=an,
        icerik_ozeti_deger=ozet,
        yorum=yorum,
        denetim_idleri=denetimler,
    )
    return durum


def onay_reddet(
    durum: dict[str, Any],
    kapi: str,
    *,
    gerekce: str,
    onaylayan: str | None = None,
    yorum: str | None = None,
    saat: str | None = None,
) -> dict[str, Any]:
    """Kapiyi ret ile kapatir, gerekceyi kaydeder ve bagli kapilari kapatir.

    Zincirleme zorunludur. `methodology` retliyken acik kalan bir
    `findings` onayi gecerli bir onaya degil, reddedilmis bir kapiya
    dayanirdi; `cmd_export` yolu bu yolla acilirdi.

    Gerekcesiz ret kabul edilmez. Ret bir onay degildir: kapı kapanır,
    `on_kosul` saglanana kadar yeniden acilamaz. Icerik ozeti yazilmaz
    (kapı acık degildi); ret gerekcesi neyin duzeltilmesi gerektigini
    soyler ve `references/approval_gates.md` ile ayni sorumluluktadir.

    Ret de bir KARARDIR ve karari vereni tasir: gerekce "kimi dinlemedik"
    sorusunu yanitlar, anonim ret bu zinciri koparir. Bu yuzden
    `onaylayan` ret icin de zorunludur (bkz. `onay_ver`).
    """
    if kapi not in GATE_KOSULLARI:
        raise ValueError(f"bilinmeyen onay kapisi: {kapi}")
    temiz_gerekce = temizle(gerekce, UZUNLUK_SINIRI["rejection_reason"])
    if not temiz_gerekce:
        raise ValueError(
            f"'{kapi}' kapisi icin ret gerekcesi zorunludur: "
            "hangi alanin duzeltilmesi gerektigi soylenmelidir."
        )
    temiz_onaylayan = temizle(onaylayan, UZUNLUK_SINIRI["approved_by"])
    if not temiz_onaylayan:
        raise OnayHatasi(
            f"'{kapi}' kapisi icin ret eden zorunludur: karari veren "
            "kisinin adi yazilmali (CLI: --by \"Ad Soyad\"). Anonim ret, "
            "itirazin kime yapildigini kaybetmektedir."
        )

    onceki = _kayit(durum, kapi)
    an = saat or datetime.now(timezone.utc).isoformat(timespec="seconds")
    durum.setdefault("human_approvals", {})[kapi] = {
        "approved": False,
        "revision": int(onceki.get("revision") or 0) + 1,
        "approved_by": temiz_onaylayan,
        "approved_at": an,
        "content_hash": None,
        "comment": temizle(yorum, UZUNLUK_SINIRI["comment"]),
        "rejection_reason": temiz_gerekce,
        "audit_refs": [],
    }
    _olay_yaz(
        durum, kapi, "reject", aktör=onaylayan, an=an, gerekce=temiz_gerekce,
        yorum=yorum,
    )
    for hedef in _bagimli_kapilari_kapat(durum, kapi):
        _olay_yaz(
            durum, hedef, "block", an=an,
            gerekce=f"'{kapi}' kapısı reddedildi; bağımlı onay düşürüldü.",
        )
    return durum


def onay_geri_al(
    durum: dict[str, Any],
    kapi: str,
    *,
    gerekce: str | None = None,
    saat: str | None = None,
) -> dict[str, Any]:
    """Kapiyi kapatir ve ona bagli acik kapilari da kapatir.

    NEDEN `onaylayan` PARAMETRESI YOK
    -------------------------------
    Geri alma kapiyi KAPATIR. Guvenlik yonu "daha az izin ver" yonudur;
    onay vermekten farkli olarak burada zorlama yalnizca geri almayi
    zorlastirir, kazanci yoktur. Kayit `approved_by: None` ile yazilir
    cunku onaylayan kimligi onayla birlikte silinir. Bu BILINCLI bir
    muafiyettir; `test_geri_almada_aktor_zorunlu_degil` onu sabitler.

    Bir onay geri alinirsa, ona dayanan onaylar da gecersizdir; aksi halde
    "methodology geri alindi ama final_thesis onayli" gibi durum olusur.
    Ayni kural `onay_reddet` icinde de gecerlidir.
    """
    if kapi not in GATE_KOSULLARI:
        raise ValueError(f"bilinmeyen onay kapisi: {kapi}")

    onaylar = durum.setdefault("human_approvals", {})
    an = saat or datetime.now(timezone.utc).isoformat(timespec="seconds")
    onceki = onaylar.get(kapi)
    onaylar[kapi] = {
        "approved": False,
        # Sema `revision >= 1` istiyor; hic acilmamis bir kapi geri
        # alindiginda sayac 0'da kalir, bu yuzden alta birden baslanir.
        "revision": max(1, int(_kayit(durum, kapi).get("revision") or 0)),
        "approved_by": None,
        "approved_at": None,
        "content_hash": None,
        "comment": None,
        "rejection_reason": None,
        "audit_refs": [],
    }
    _olay_yaz(durum, kapi, "revoke", an=an, gerekce=gerekce)
    for hedef in _bagimli_kapilari_kapat(durum, kapi):
        _olay_yaz(
            durum, hedef, "block", an=an,
            gerekce=f"'{kapi}' kapısı geri alındı; bağımlı onay düşürüldü.",
        )
    return durum


# --- hazirlik denetimleri --------------------------------------------------


def _bulgulari_tara(durum: dict[str, Any]) -> list[str]:
    """Bütünlük taraması: gerçekten bozuk olanı döndürür.

    Burada kopuk referans veya retraksiyonlu kaynak yoksa liste boştur.
    """
    sorunlar = []
    kopuk = kopuk_baglari(durum)
    if kopuk:
        sorunlar.append(f"{len(kopuk)} kopuk referans: {kopuk[0]}")
    retraksiyon = retraksiyona_ugrayan_iddialar(durum)
    if retraksiyon:
        sorunlar.append(f"geri çekilmiş kaynağa dayanan iddia: {', '.join(retraksiyon)}")
    kanitsiz = kanitsiz_iddialar(durum)
    if kanitsiz:
        sorunlar.append(f"{len(kanitsiz)} kanıtsız iddia: {', '.join(kanitsiz)}")
    return sorunlar


#: Hazirlik denetleyicileri. Semalar degismezse yeniden kurulmaz.
_HAZIRLIK_DOGRULAYICI: dict[str, Any] = {}

#: Bir denetimde gosterilecek en fazla sorun. Kesilme sebebi: kullaniciya
#: 300 satirlik sema hatasini gostermek teşhis degil, gizlemedir.
_HAZIRLIK_RAPOR_SINIRI = 5


def _kayit_dogrulayicisi(alan: str) -> Any:
    """`alan` registry'sinin kayit semasina karsi dogrulayici dondurur.

    Varlik tipi `graph.registry_haritasi()`'ndan gelir; hangi sema'nin
    gecerli oldugu bilgisi burada TEKRARLANMAZ. `record.varlik_tipi`
    kullanilmaz: o fonksiyon yalniz `thesis:record` ile YAZILABILEN
    registry'lere cevap verir ve `search_runs` gibi sahiplenilmis
    registry'lerde bilerek hata verir. Hazirlik denetimi yazma izni
    degil, var olan verinin GECERLILIGINI sorar.

    Semalar degismezse dogrulayici onbellekten gelir.
    """
    if alan not in _HAZIRLIK_DOGRULAYICI:
        from jsonschema import Draft202012Validator

        from tools.atw.state import load_schema

        varlik = registry_haritasi().get(alan)
        if varlik is None:
            raise ValueError(f"'{alan}' bir registry değil (sema eşlemesi yok)")
        # `load_schema` dosya ADI ister: sonuna `.json` eklenir.
        _HAZIRLIK_DOGRULAYICI[alan] = Draft202012Validator(
            load_schema(f"{varlik}.json")
        )
    return _HAZIRLIK_DOGRULAYICI[alan]


def _registry_hazir(durum: dict[str, Any], alan: str) -> list[str]:
    """Registry'nin on kosulunun saglanip saglanmadigini dondurur.

    Yalniz "dolu mu" diye bakmak ZAYIF bir denetimdir: `[{}]` doludur ama
    hicbir sey tasimaz. `{"id": "RQ-001", "text": "..."}` doludur ama
    `type` alani yoktur; `research_question` semasi bunu zorunlu kilar.
    Boyle bir kayitla kapi acilmasi, kapinin hicbir seyi dogrulamadigi
    anlamina gelir.

    Bu yuzden her kayit KENDI varlik semasina karsi denetlenir. Sema,
    kaydin yazildigi yolun ayni kuralidir: `thesis:record` bir kaydi
    yazmadan once bu semayi kullanir, `thesis:approve` de ayni semayi
    kullanir. Iki farkli kural olsaydi, yazilabilen ama onaylanamayan
    kayitlar olusurdu.
    """
    kayitlar = durum.get(alan) or []
    if not kayitlar:
        return [f"'{alan}' boş — bu aşamanın çıktısı henüz üretilmemiş"]
    try:
        dogrulayici = _kayit_dogrulayicisi(alan)
    except (ValueError, OSError) as hata:
        # Bilinmeyen veya sahiplenilmis registry. Sessizce gecmek,
        # denetlenmeyen bir kapiyi denetlenmis gibi gostermekten kotudur.
        return [f"'{alan}' denetlenemiyor: {hata}"]

    sorunlar: list[str] = []
    for sira, kayit in enumerate(kayitlar, start=1):
        if not isinstance(kayit, dict):
            sorunlar.append(f"{alan}[{sira}]: kayıt bir JSON nesnesi olmalı")
            continue
        # `iter_errors` TUM hatalari dondurur; `validate` yalniz ilkini.
        # Ilk hata gosterilseydi, tek komutla duzeltilemeyen bir kayit
        # icin kullanici her seferinde yeni bir hata ogrenirdi.
        for hata in dogrulayici.iter_errors(kayit):
            yol = ".".join(str(parca) for parca in hata.path) or "kayıt"
            sorunlar.append(f"{alan}[{sira}].{yol}: {hata.message}")
    if len(sorunlar) > _HAZIRLIK_RAPOR_SINIRI:
        kalan = len(sorunlar) - _HAZIRLIK_RAPOR_SINIRI
        sorunlar = sorunlar[:_HAZIRLIK_RAPOR_SINIRI] + [f"… ve {kalan} sorun daha"]
    return sorunlar


def _bolumler_hazir(durum: dict[str, Any]) -> list[str]:
    """Teslim edilebilir metin var mi? (spec §4.7)

    Yalniz bolum BASLIKLARINDAN olusan bir "tez" onaylanabilirse, kapı
    hiçbir şeyi dogrulamiyor demektir. Her bolumde metni olan en az bir
    paragraf olmalidir.
    """
    bolumler = durum.get("chapters") or []
    if not bolumler:
        return ["'chapters' boş — teslim edilecek bölüm yok"]

    sorunlar: list[str] = []
    for bolum in bolumler:
        kimlik = bolum.get("id", "?") if isinstance(bolum, dict) else "?"
        paragraflar = bolum.get("paragraphs") or [] if isinstance(bolum, dict) else []
        dolu = [
            p
            for p in paragraflar
            if isinstance(p, dict) and str(p.get("text") or "").strip()
        ]
        if not dolu:
            sorunlar.append(f"'{kimlik}': metni olan paragraf yok")
    if len(sorunlar) > _HAZIRLIK_RAPOR_SINIRI:
        kalan = len(sorunlar) - _HAZIRLIK_RAPOR_SINIRI
        sorunlar = sorunlar[:_HAZIRLIK_RAPOR_SINIRI] + [f"… ve {kalan} sorun daha"]
    return sorunlar


# Kapi basina hazirlik denetimleri. Her kapi kendi asamasinin registry'sini
# DOLDURMUS ve kayitlari GECERLI olmalidir; aksi halde kapı, içliği boş
# ya da yarım doldurulmuş bir belgeye verilmiş onay olur.
#
# KURAL (dolaylı ama zorunlu): bir kapinin hazirlik denetimi YALNIZCA
# kendisinden ONCE uretilen veriye bakabilir. Denetimi, kapinin arkasindaki
# komutun URETTIGI registry'ye bakmak dairesel bagimlilik kurar ve o
# komutun hic calismamasina yol acar. `methodology` kapisi tam olarak
# boyle bir durumdu: `chapters` bu kapinin arkasindaki `cmd_write` ile
# doluyor, `cmd_write` da bu kapinin on kosulu olarak `chapters`'i
# ariyordu. `methodology` bilincli olarak listede YOK.
#
# `final_thesis` ise bütünluk + kanıt taramasının yanında metin varlığını
# da denetler: basliklardan olusan bos bir "tez" teslim edilmemelidir.
#
# `test_baska_kapilarin_hazirligi_korunur` bu kurali digerleri icin
# sabitler.
GATE_HAZIRLIK: dict[str, Callable[[dict[str, Any]], list[str]]] = {
    "research_question": lambda d: _registry_hazir(d, "research_questions"),
    "search_strategy": lambda d: _registry_hazir(d, "search_runs"),
    "source_set": lambda d: _registry_hazir(d, "sources"),
    "research_gap": lambda d: _registry_hazir(d, "gap_registry"),
    "findings": lambda d: _registry_hazir(d, "findings_registry"),
    "final_thesis": lambda d: _bulgulari_tara(d) + _bolumler_hazir(d),
}


def acik_olanlar(durum: dict[str, Any]) -> list[str]:
    """Açık olan kapılar, akış sırasına göre."""
    return [k for k in APPROVAL_GATES if kapi_acik_mi(durum, k)]


def kapali_olanlar(durum: dict[str, Any]) -> list[str]:
    return [k for k in APPROVAL_GATES if not kapi_acik_mi(durum, k)]


def hazirlik_engelleri(durum: dict[str, Any], kapi: str) -> list[str]:
    """Yalnizca VERI HAZIRLIĞI denetimi; onay sorulmaz.

    `kontrol_yaz` iki şeyi birleştirir: "insan onayı var mı" ve "onayı
    uygulayacak veri var mı". Onay vermekten once yalniz ikincisi
    sorulmalıdır — birincisi zaten verilmeyecek, o sorulacaksa kapı
    hicbir zaman acilmaz.

    Hazirlik denetimi tasimayan tek kapi `methodology`dur: ciktilari
    `chapters` bu kapinin arkasinda yazildigi icin, ayni anda hem
    on kosul hem sonuc olurdu. `final_thesis` bütünlük denetimini
    `cmd_export` yolunda zaten yapiyor; burada metin varligini da
    denetler.
    """
    if kapi not in GATE_KOSULLARI:
        raise ValueError(f"bilinmeyen onay kapisi: {kapi}")
    denetim = GATE_HAZIRLIK.get(kapi)
    return list(denetim(durum)) if denetim is not None else []


def kontrol_yaz(durum: dict[str, Any], kapi: str) -> list[str]:
    """Yazim/ihracat icin kapinin acik ve verinin hazir olup olmadigini doner.

    Donen liste bos ise yazim yapilabilir. Dolu ise her ogge bir engeldir.

    Uc ayri kontrol:
      1. onay   -> insan karari verilmis mi, bayat mi (kapi_acik_mi)
      2. hazirlik -> o karari uygulayacak veri gercekten var mi
      3. denetim -> kapinin dayandigi denetim gecmis ve temiz mi
    """
    if kapi not in GATE_KOSULLARI:
        raise ValueError(f"bilinmeyen onay kapisi: {kapi}")

    engeller: list[str] = []
    kayit = _kayit(durum, kapi)
    if not kapi_acik_mi(durum, kapi):
        if kayit.get("approved") and onay_stale_mi(durum, kapi):
            engeller.append(
                f"'{kapi}' kapısı onayı BAYAT: onaydan sonra kapsanan içerik "
                f"değişti ({kayit.get('content_hash')} != "
                f"{icerik_ozeti(durum, kapi)}). Yeniden onaylayın."
            )
        else:
            engeller.append(
                f"'{kapi}' kapısı insan onayı bekliyor "
                f"(human_approvals.{kapi} = false)"
            )
    engeller.extend(denetim_gereksinimleri(durum, kapi))
    denetim = GATE_HAZIRLIK.get(kapi)
    if denetim is not None:
        engeller.extend(denetim(durum))
    return engeller


def yazim_hazir_mi(durum: dict[str, Any], kapi: str = "methodology") -> bool:
    return not kontrol_yaz(durum, kapi)


def kapi_detay(durum: dict[str, Any], kapi: str) -> dict[str, Any]:
    """Tek kapinin rapor sözlüğü.

    `attested` alani, onayin icerik ozeti tasiyip tasimadigini bildirir.
    `attested: False` + acik kapı = "onay var ama dosya elle yazılmış ya da
    eski bicimde kalmış". Durum dosyasi imzasiz JSON oldugu icin elle
    duzenlemeyi tamamen engellemek mumkun degildir; bu alan ve
    `approval_events` gunlugu tespit edilebilir iz birakir.
    """
    if kapi not in GATE_KOSULLARI:
        raise ValueError(f"bilinmeyen onay kapisi: {kapi}")
    kayit = _kayit(durum, kapi)
    gunluk = [
        e
        for e in (durum.get("approval_events") or [])
        if isinstance(e, dict) and e.get("gate") == kapi
    ]
    return {
        "kapi": kapi,
        "acik": kapi_acik_mi(durum, kapi),
        "stale": onay_stale_mi(durum, kapi),
        "attested": bool(kayit.get("content_hash")),
        "content_hash": kayit.get("content_hash"),
        "simdiki_ozet": icerik_ozeti(durum, kapi),
        "revision": kayit.get("revision"),
        "approved_by": kayit.get("approved_by"),
        "approved_at": kayit.get("approved_at"),
        "comment": kayit.get("comment"),
        "rejection_reason": kayit.get("rejection_reason"),
        "bagimlilik": GATE_BAGIMLILIK[kapi],
        "engeller": kontrol_yaz(durum, kapi),
        "olay_sayisi": len(gunluk),
        "son_olay": gunluk[-1] if gunluk else None,
    }


def ozet(durum: dict[str, Any]) -> list[tuple[str, bool, list[str]]]:
    """Tum kapilarin durumunu ve engellerini sirayla doner.

    CLI raporu ve `thesis:status` bunu kullanir; akis tek bir yerde
    tanimli kalir, cift tanim olusmaz.
    """
    return [
        (kapi, kapi_acik_mi(durum, kapi), kontrol_yaz(durum, kapi))
        for kapi in APPROVAL_GATES
    ]
