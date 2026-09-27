"""Tez denetimleri: atif, butunluk, kanit, yontem.

Her denetim schemas/audit.json'a uyan bir kayit dondurur. Denetimler
YALNIZCA veriden turen bulgular yazar; supheli bir eslesmeyi "bulgu" diye
sunmaz.

Kapsam disi birakilani tutarli olsun diye burada YOK: `consistency`.
Terminoloji, sayi ve tarih caprazlari guvenilir sekilde mekaniklestirilemez;
onlar skill.yaml'daki consistency-auditor ajaninin isi. Bu modul onu sahte
bir denetimle taklit etmez.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Callable

from tools.atw.graph import (
    celiskili_iddialar,
    kanitsiz_iddialar,
    kopuk_baglari,
    retraksiyona_ugrayan_iddialar,
)

# integrity_checks'in bes sayaci. Sema additionalProperties: false oldugu
# icin buraya yeni sayac eklenemez; her sayacin anlami asagida KOSULLA'dir.
_SIFIR_SAYACLAR = (
    "fabricated_sources",
    "unsupported_claims",
    "retracted_sources_in_use",
    "orphaned_citations",
    "unverifiable_claims",
)

# Bir iddianin dogrulanmis sayilmasi icin olmasi gereken durumlar.
# "unverified"/"pending" bir sonuc degil, henuz calisma durumudur.
_TERMINAL_DOGRULAMA = frozenset({"verified"})


def _bulgu(
    severity: str, message: str, location: str, entity_id: str | None = None
) -> dict[str, Any]:
    """audit.json findings girdisi olusturur."""
    return {
        "severity": severity,
        "message": message,
        "location": location,
        "entity_id": entity_id,
    }


def _kayit(
    audit_type: str, durum: dict[str, Any], bulgular: list[dict[str, Any]], sayaclar: dict[str, int]
) -> dict[str, Any]:
    """Denetim kaydini semaya uyan sozlug olarak kurar.

    ``audit_id`` gecici olarak mevcut registry sayisindan uretilir; boylece
    kayit tek basina da semaya gecer. Birden fazla denetim ayni anda
    calistiginda hepsi ayni gecici kimligi alir; cakismayi
    denetim_kimligi_ata() cozer.
    """
    return {
        "audit_id": f"AUD-{len(durum.get('audit_registry') or []) + 1:03d}",
        "thesis_id": durum.get("thesis_id", ""),
        "audit_type": audit_type,
        "date": date.today().isoformat(),
        "findings": bulgular,
        "integrity_checks": sayaclar,
        "critical_issues": [b["message"] for b in bulgular if b["severity"] == "critical"],
        "deferred_minors": [b["message"] for b in bulgular if b["severity"] == "minor"],
    }


def denetim_kimligi_ata(durum: dict[str, Any], kayitlar: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Denetim kayitlarina sirali AUD kimligi verir.

    audit_citations() ve _denetim_butunluk() ayni anda calistiginda ikisi de
    len(audit_registry)+1 hesaplar ve ayni kimligi uretir. Kimlik atama
    burada, kayitlar eklendikten SONRA yapilir; boylece cakisma olusmaz.
    """
    kullanilan = {
        k.get("audit_id")
        for k in durum.get("audit_registry") or []
        if isinstance(k, dict)
    }
    sonraki = 1
    atanan: list[dict[str, Any]] = []
    for kayit in kayitlar:
        while f"AUD-{sonraki:03d}" in kullanilan:
            sonraki += 1
        kimlik = f"AUD-{sonraki:03d}"
        kayit["audit_id"] = kimlik
        atanan.append(kayit)
        sonraki += 1
    return atanan


# --- atif denetimi ----------------------------------------------------------

def _denetim_atif(durum: dict[str, Any]) -> dict[str, Any]:
    """Atif butunlugu (kaynak varligi, retraksiyon, terk, APA 7, sayfa)."""
    from tools.citation_check import audit_citations

    return audit_citations(durum)


# --- butunluk denetimi ------------------------------------------------------

def _denetim_butunluk(durum: dict[str, Any]) -> dict[str, Any]:
    """Yapisal butunluk: kopuk referanslar, kanitsiz iddia, retraksiyon.

    Sayaclarin anlami:
      fabricated_sources      -> atiflanan ama kayitlari olmayan kaynak
      orphaned_citations      -> hicbir kaynagi olmayan atif
      unsupported_claims      -> kaniti olmayan iddia
      retracted_sources_in_use-> geri cekilmis kaynaga dayanan iddia
      unverifiable_claims     -> dogru/yanlis sonuc vermemis iddia
    """
    bulgular: list[dict[str, Any]] = []
    sayaclar = {ad: 0 for ad in _SIFIR_SAYACLAR}

    # KOPUK BAGLAR: semalardaki 53 referans alaninin tamami taranir. Bulgu
    # listesi bu yuzden kapsamlidir; asagidaki sayaclar onun bir alt
    # toplamidir, ayri bir taramadir.
    for aciklama in kopuk_baglari(durum):
        bulgular.append(_bulgu("critical", f"Kopuk referans: {aciklama}", "durum"))

    kaynak_kimlikleri = {
        k.get("id") for k in durum.get("sources") or [] if isinstance(k, dict)
    }

    for atif in durum.get("citations") or []:
        if not atif.get("source_id"):
            sayaclar["orphaned_citations"] += 1
        elif atif.get("source_id") not in kaynak_kimlikleri:
            sayaclar["fabricated_sources"] += 1

    for kimlik in kanitsiz_iddialar(durum):
        bulgular.append(
            _bulgu("major", f"{kimlik} iddiasinin kaniti yok.", "iddialar", kimlik)
        )
    sayaclar["unsupported_claims"] = len(kanitsiz_iddialar(durum))

    for kimlik in retraksiyona_ugrayan_iddialar(durum):
        bulgular.append(
            _bulgu(
                "critical",
                f"{kimlik} iddiasi geri cekilmis bir kaynaga dayaniyor.",
                "iddialar",
                kimlik,
            )
        )
    sayaclar["retracted_sources_in_use"] = len(retraksiyona_ugrayan_iddialar(durum))

    dogrulanamayan = [
        kayit.get("id")
        for kayit in durum.get("claims_registry") or []
        if isinstance(kayit, dict)
        and kayit.get("verification_status") not in _TERMINAL_DOGRULAMA
    ]
    for kimlik in dogrulanamayan:
        bulgular.append(
            _bulgu("minor", f"{kimlik} iddiasi dogrulanmamis durumda.", "iddialar", kimlik)
        )
    sayaclar["unverifiable_claims"] = len(dogrulanamayan)

    # Celiskili iddialar sayac tablosunda YER almaz (sema kapali); bulgu
    # olarak raporlanir.
    for kimlik in celiskili_iddialar(durum):
        bulgular.append(
            _bulgu("major", f"{kimlik} celiskeli iddialarla baglantili.", "iddialar", kimlik)
        )

    return _kayit("integrity", durum, bulgular, sayaclar)


# --- kanit denetimi --------------------------------------------------------

def _denetim_kanit(durum: dict[str, Any]) -> dict[str, Any]:
    """Kanit kayitlarinin butunlugu: dogrulanmamis ve iddiyasiz kanit."""
    bulgular: list[dict[str, Any]] = []
    kanitlar = durum.get("evidence_registry") or []
    iddia_kimlikleri = {
        k.get("id") for k in durum.get("claims_registry") or [] if isinstance(k, dict)
    }

    dogrulanmamis = 0
    iddisiz = 0
    kopuk = 0
    for kanit in kanitlar:
        kimlik = kanit.get("id")
        if not kanit.get("verified"):
            dogrulanmamis += 1
            bulgular.append(
                _bulgu("major", f"{kimlik} kaniti elle dogrulanmamis.", "kanitlar", kimlik)
            )
        destekledigi = kanit.get("supports_claim")
        if not destekledigi:
            iddisiz += 1
            bulgular.append(
                _bulgu("major", f"{kimlik} kaniti hicbir iddiyaya baglanmamis.", "kanitlar", kimlik)
            )
        elif destekledigi not in iddia_kimlikleri:
            kopuk += 1
            bulgular.append(
                _bulgu(
                    "critical",
                    f"{kimlik} kaniti var olmayan {destekledigi} iddiasini destekliyor.",
                    "kanitlar",
                    kimlik,
                )
            )

    # integrity_checks bu denetim icin de ayni bes alani kullanir; kanit
    # odakli sayimlar en yakin karsiliklarina yerlestirilir.
    sayaclar = {
        "fabricated_sources": 0,
        "unsupported_claims": kopuk,
        "retracted_sources_in_use": 0,
        "orphaned_citations": iddisiz,
        "unverifiable_claims": dogrulanmamis,
    }
    return _kayit("evidence", durum, bulgular, sayaclar)


# --- yontem denetimi --------------------------------------------------------

def _denetim_metodoloji(durum: dict[str, Any]) -> dict[str, Any]:
    """Araştirma sorusu ile bulgu arasindaki yapisal tutarsizlik.

    Yalnizca YAPISAL olanlar denetlenir: "cevaplanmis" bir sorunun hicbir
    bulgusu olmamasi, ya da hala "pending" iken bulgusu olmasi.

    "Nitel soru ama nicel yontem" turu denetimler YAPILMAZ: research_question
    semasinda `method` serbest metindir, nitel/nicel sinifini kod tarafinda
    guvenilir sekilde turemek mumkun degil. Tahmin yurutmek, bulguymus gibi
    sunmaktan kotudur.
    """
    bulgular: list[dict[str, Any]] = []
    for soru in durum.get("research_questions") or []:
        if not isinstance(soru, dict):
            continue
        kimlik = soru.get("id")
        durumu = soru.get("status")
        bulgular_var = bool(soru.get("finding_ids"))

        if durumu == "answered" and not bulgular_var:
            bulgular.append(
                _bulgu(
                    "major",
                    f"{kimlik} 'answered' isaretli ama hicbir bulgusu yok.",
                    "araştırma soruları",
                    kimlik,
                )
            )
        elif durumu in {"pending", "partially_answered"} and bulgular_var:
            bulgular.append(
                _bulgu(
                    "minor",
                    f"{kimlik} '{durumu}' durumunda ama zaten bulgusu var.",
                    "araştırma soruları",
                    kimlik,
                )
            )

    sayaclar = {ad: 0 for ad in _SIFIR_SAYACLAR}
    sayaclar["unsupported_claims"] = sum(
        1 for b in bulgular if b["severity"] == "major"
    )
    sayaclar["unverifiable_claims"] = sum(
        1 for b in bulgular if b["severity"] == "minor"
    )
    return _kayit("methodology", durum, bulgular, sayaclar)


DENETIMLER: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "citation": _denetim_atif,
    "integrity": _denetim_butunluk,
    "evidence": _denetim_kanit,
    "methodology": _denetim_metodoloji,
}

# skill.yaml'in --type secenekleriyle ayni kume.
DESTEKLENEN_TURLER = ("citation", "methodology", "consistency", "integrity", "evidence")

# Denetimi olmayan turler: ajan isidir, uydurma bir denetim yazilmaz.
UYARILACAK_TURLER = tuple(t for t in DESTEKLENEN_TURLER if t not in DENETIMLER)


def denetim_calistir(durum: dict[str, Any], tur: str) -> dict[str, Any]:
    """Tek bir denetimi calistirir."""
    if tur not in DENETIMLER:
        raise ValueError(f"desteklenmeyen denetim türü: {tur}")
    return DENETIMLER[tur](durum)


def tum_denetimler(
    durum: dict[str, Any], turler: list[str] | None = None
) -> list[dict[str, Any]]:
    """Verilen turlerin denetim kayitlarini dondurur (kimlikler atanmamis).

    turler None ise ya da "all" ise DENETIMLER'daki tum turler calisir.
    Desteklenmeyen turler sessizce ATLANIR; cagiran tarafi uyarmak
    UYARILACAK_TURLER listesinden sorumludur.
    """
    if not turler or "all" in turler:
        secili = list(DENETIMLER)
    else:
        secili = [t for t in turler if t in DENETIMLER]
    return [denetim_calistir(durum, t) for t in secili]
