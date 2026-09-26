"""Kanit grafigi sorgulari: kenarlar semalardan turetilir.

Grafik materyalize edilmez. Bu modul ``thesis_state.json`` uzerinde
salt-okunur gezinir ve hicbir sey diske yazmaz.

Iki sey elle yazilmaz:

* **Kenar tablosu.** Her alanin ``pattern`` degeri oneki verir,
  ``ID_PREFIXES`` oneki varlik adina cevirir. Yeni sema eklendiginde
  tablo kendiliginden genisler.
* **Registry haritasi.** ``thesis_state.json``'in ``$ref`` dizilerinden
  turetilir; hangi alan hangi varligi tutuyor sema zaten soyluyor.

Elle yazilan tek parca ``_ANLAMSAL_ALANLAR`` sabitidir.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Final, Iterator, NamedTuple

from tools.atw.ids import ID_PREFIXES
from tools.atw.state import SCHEMA_DIR

#: Yapi veya anlam. "Bu kayit nereye bagli?" / "Neyi destekliyor?"
YAPISAL: Final = "yapisal"
ANLAMSAL: Final = "anlamsal"

_ONEK_DESENI: Final = re.compile(r"^\^([A-Z]+)-")


@dataclass(frozen=True)
class Kenar:
    """Bir referans alani: kayit tipi -> hedef tipi baglantisi."""

    kayit_tipi: str
    alan_adi: str
    hedef_tipi: str
    coklu_mu: bool
    tur: str

    @property
    def anahtar(self) -> tuple[str, str]:
        return (self.kayit_tipi, self.alan_adi)


class Zincir(NamedTuple):
    """Bir kaynaktan hedefe yuruyusun adimlari."""

    adim: str
    kimlik: str
    tur: str


def _semalari() -> dict[str, dict]:
    return {p.stem: json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(SCHEMA_DIR.glob("*.json"))}


def _kimlik_alani(sema: dict[str, Any], sema_adi: str) -> str | None:
    """Kaydin kimlik alanini semadan belirler.

    ``id`` varsa o. Yoksa varlik adinin kendi ``*_id`` alani olabilir:
    ``audit.json`` -> ``audit_id`` (F18).

    Onemli: aday alan adi ``sema_adi``den **turetilir**, ``pattern``
    icindeki onkiden degil. ``pattern`` "AUD" verir, alan adi "audit_id"
    verir; karsilastirilirsa buyuk/kucuk harf yuzunden hic eslesmez ve
    ``audit_id`` bir kenara girer - yani duzeltmek icin yazilan kod
    duzeltmek icin yazildigi hatayi yeniden uretir.
    """
    ozellikler = sema.get("properties") or {}
    if "id" in ozellikler:
        return "id"
    aday = f"{sema_adi}_id"
    return aday if aday in ozellikler else None


def _tur_belirle(alan_adi: str) -> str:
    """Alan adindan kenar turunu cikarir.

    Kural: alan adi neyi *anlatiyorsa* o yon degistirme anlam, "nereye
    bagli" yonu yapidadir. Kanit/idda zinciri alanlari (evidence_ids,
    sources, claims, findings, datasets, analyses, statistics, tables,
    figures, research_questions, rq_ids, hypothesis_outcomes,
    paragraph_id, chapter) yapisaldir. Degerlendirme nitelikli
    alanlar (contradicted_by, counter_claims, related_claims,
    agrees_with, disagrees_with, supersedes_source_id,
    original_source_id, conflicting_claim_ids, contradicting_source_ids)
    ve asyikadir.
    """
    if alan_adi in _ANLAMSAL_ALANLAR:
        return ANLAMSAL
    return YAPISAL


#: Anlamsal kenar alanlari. Bunlar "nereye bagli" degil, "neyi
#: destekliyor / celistiriyor / yerine gecti" anlami tasir.
_ANLAMSAL_ALANLAR: Final[frozenset[str]] = frozenset({
    "contradicted_by", "counter_claims", "related_claims",
    "agrees_with", "disagrees_with", "supersedes_source_id",
    "original_source_id", "conflicting_claim_ids",
    "contradicting_source_ids", "supports_claim", "supports_claims",
    "supports_findings", "supports_hypotheses", "related_findings",
    "finding_ids", "answered_by", "gap_ids",
})


def _referans_alanlari(sema: dict[str, Any], yol: str = "") -> Iterator[tuple[str, bool, str]]:
    """Sema icindeki tum kimlik referans alanlarini gezer.

    Yields:
        (alan_yolu, coklu_mu, hedef_tipi)
    """
    for ad, tanim in (sema.get("properties") or {}).items():
        if ad == "$comment":
            continue
        tam = f"{yol}{ad}"
        if not isinstance(tanim, dict):
            continue
        dizi = tanim.get("type") == "array"
        oge = tanim.get("items") if dizi else tanim
        if not isinstance(oge, dict):
            continue
        desen = oge.get("pattern")
        eslesme = _ONEK_DESENI.match(desen) if isinstance(desen, str) else None
        if eslesme and eslesme.group(1) in ID_PREFIXES:
            yield (tam, dizi, ID_PREFIXES[eslesme.group(1)])
            continue
        if oge.get("type") == "object" and oge.get("properties"):
            yield from _referans_alanlari(oge, f"{tam}.")


@lru_cache(maxsize=1)
def _kimlik_alanlari() -> frozenset[str]:
    """Her semada kaydin kendi kimlik alani olan alanlar. Bunlar
    referans degildir; kenara girmez."""
    semalar = _semalari()
    alanlar: set[str] = set()
    for sema_adi, sema in semalar.items():
        alan = _kimlik_alani(sema, sema_adi)
        if alan:
            alanlar.add(alan)
    return frozenset(alanlar)


_KIMLIK_ALANLARI: Final = _kimlik_alanlari()


@lru_cache(maxsize=1)
def registry_haritasi() -> dict[str, str]:
    """Durum alani -> varlik tipi. ``thesis_state.json``'den turetilir.

    Her ``$ref`` dizisi bir registry'dir. Elle yazilan
    ``state._REGISTRY_FIELDS`` 15 alan icerir ve 4'unu kacirir;
    bu yuzden burada kullanilmaz. Olculen: 18 semada 19 alan.
    """
    harita: dict[str, str] = {}
    for alan, tanim in (_semalari()["thesis_state"].get("properties") or {}).items():
        if not isinstance(tanim, dict):
            continue
        oge = tanim.get("items")
        ref = oge.get("$ref") if isinstance(oge, dict) else None
        if isinstance(ref, str) and ref.endswith(".json"):
            harita[alan] = ref[:-len(".json")]
    return harita


def _kimlik(kayit: dict) -> str | None:
    """Kaydin kimligi. ``audit`` kayitlarinda alan adi ``audit_id``."""
    for alan in ("id", "audit_id"):
        deger = kayit.get(alan)
        if isinstance(deger, str) and deger:
            return deger
    return None


def _ic_refler(varlik_tipi: str) -> list[tuple[str, str]]:
    """Varlik semasindaki ic ice ``$ref`` dizileri: (alan, alt varlik).

    ``paragraph`` kayitlari ust duzey registry degil, ``chapter``'in
    icinde yasar. ``citation.paragraph_id`` bu yuzden yalnizca bu
    indeksle denetlenebilir.
    """
    sema = _semalari().get(varlik_tipi) or {}
    cikti: list[tuple[str, str]] = []
    for alan, tanim in (sema.get("properties") or {}).items():
        if not isinstance(tanim, dict) or tanim.get("type") != "array":
            continue
        oge = tanim.get("items")
        ref = oge.get("$ref") if isinstance(oge, dict) else None
        if isinstance(ref, str) and ref.endswith(".json"):
            cikti.append((alan, ref[: -len(".json")]))
    return cikti


def _kayitlar(durum: dict[str, Any]) -> Iterator[tuple[str, dict]]:
    """Durumdaki tum kayitlari (varlik_tipi, kayit) uclusuyle verir.

    Ic ice koleksiyonlar da dahil: ``chapter.paragraphs[]`` icindeki
    paragraf kayitlari ``paragraph`` turuyle yields edilir.
    """
    for alan, varlik_tipi in registry_haritasi().items():
        for kayit in (durum.get(alan) or []):
            if not isinstance(kayit, dict):
                continue
            yield (varlik_tipi, kayit)
            for ic_alan, alt in _ic_refler(varlik_tipi):
                for ic in (kayit.get(ic_alan) or []):
                    if isinstance(ic, dict):
                        yield (alt, ic)


def _var_mi(durum: dict[str, Any], varlik_tipi: str) -> set[str]:
    """Verilen varlik tipindeki tum kimlikler."""
    return {
        kimlik
        for varlik, kayit in _kayitlar(durum)
        if varlik == varlik_tipi
        for kimlik in [_kimlik(kayit)]
        if kimlik
    }


def _kimlikler(durum: dict[str, Any], varlik_tipi: str) -> Iterator[tuple[dict, str]]:
    for varlik, kayit in _kayitlar(durum):
        if varlik != varlik_tipi:
            continue
        kimlik = _kimlik(kayit)
        if kimlik:
            yield (kayit, kimlik)


@lru_cache(maxsize=1)
def kenar_tablosu() -> tuple[Kenar, ...]:
    """Semalardan turetilen kenar tablosu. Onbellekli ve salt-okunur.

    Yeni sema eklendiginde bu tablo kendiliginden genisler; elle
    guncellenmez. Olculen: 18 semada 53 kenar (Gorev 2'den sonra 59).
    """
    semalar = _semalari()
    kimlikler = _kimlik_alanlari()
    kenarlar: list[Kenar] = []
    for sema_adi, sema in semalar.items():
        if "$schema" not in sema or sema_adi == "thesis_state":
            continue
        for alan_yolu, coklu, hedef in _referans_alanlari(sema):
            if alan_yolu in kimlikler:
                continue
            kenarlar.append(Kenar(
                kayit_tipi=sema_adi,
                alan_adi=alan_yolu,
                hedef_tipi=hedef,
                coklu_mu=coklu,
                tur=_tur_belirle(alan_yolu.split(".")[-1]),
            ))
    return tuple(kenarlar)


def kopuk_baglari(durum: dict[str, Any]) -> list[str]:
    """Durumdaki tum kopuk kimlik referanslarini dondurur.

    Kapsam: semalardaki HER referans alani. Daha once yalniz
    ``<ad>_id`` kaliplari denetleniyordu ve 53 referans alaninin 6'si
    kapsaniyordu.
    """
    bulunanlar: list[str] = []
    for varlik, kayit in _kayitlar(durum):
        for kenar in kenar_tablosu():
            if kenar.kayit_tipi != varlik:
                continue
            deger = kayit
            for parca in kenar.alan_adi.split("."):
                if not isinstance(deger, dict):
                    deger = None
                    break
                deger = deger.get(parca)
            if deger is None:
                continue
            referanslar = deger if kenar.coklu_mu else [deger]
            var = _var_mi(durum, kenar.hedef_tipi)
            for referans in referanslar:
                if isinstance(referans, str) and referans not in var:
                    bulunanlar.append(
                        f"{varlik}.{kenar.alan_adi} -> {referans} "
                        f"({kenar.hedef_tipi} bulunamadi)")
    return sorted(set(bulunanlar))


def source_kullanan_iddialar(durum: dict, source_id: str) -> list[str]:
    """Verilen kaynagi kullanan IDDIA kimlikleri (yapisal yuru).

    Sadece ``claim`` kayitlari dondurur; citation/evidence degil.
    """
    sonuc = []
    for kenar in kenar_tablosu():
        if kenar.hedef_tipi != "source" or kenar.tur != YAPISAL:
            continue
        if kenar.kayit_tipi != "claim":
            continue
        for kayit, kimlik in _kimlikler(durum, kenar.kayit_tipi):
            deger = kayit.get(kenar.alan_adi)
            if deger is None:
                continue
            liste = deger if kenar.coklu_mu else [deger]
            if source_id in liste:
                sonuc.append(kimlik)
    return sorted(set(sonuc))


def iddiyanin_dayandigi_kaynaklar(durum: dict, claim_id: str) -> list[str]:
    """Verilen iddianin dayandigi kaynak kimlikleri."""
    for kayit, kimlik in _kimlikler(durum, "claim"):
        if kimlik != claim_id:
            continue
        kaynaklar = list(kayit.get("sources") or [])
        for evd in kayit.get("evidence_ids") or []:
            for e_kayit, e_kimlik in _kimlikler(durum, "evidence"):
                if e_kimlik == evd:
                    src = e_kayit.get("source_id")
                    if isinstance(src, str):
                        kaynaklar.append(src)
        return sorted(set(kaynaklar))
    return []


def bulgunun_kanit_zinciri(durum: dict, finding_id: str) -> list[Zincir]:
    """Bulgudan kaynaklara uzanan kanit zinciri."""
    zincir: list[Zincir] = []
    for kayit, kimlik in _kimlikler(durum, "finding"):
        if kimlik != finding_id:
            continue
        zincir.append(Zincir("bulgu", kimlik, YAPISAL))
        for evd in kayit.get("evidence_ids") or []:
            zincir.append(Zincir("kanit", evd, YAPISAL))
            for e_kayit, e_kimlik in _kimlikler(durum, "evidence"):
                if e_kimlik != evd:
                    continue
                if e_kayit.get("supports_claim"):
                    zincir.append(Zincir("iddia", e_kayit["supports_claim"],
                                         ANLAMSAL))
                if e_kayit.get("source_id"):
                    zincir.append(Zincir("kaynak", e_kayit["source_id"],
                                         YAPISAL))
        return zincir
    return []


def rq_dan_kaynakca(durum: dict, rq_id: str) -> list[Zincir]:
    """Arastirma sorusundan kaynakcaya uzanan zincir.

    Yon onemli: ``claim.json``'de bir arastirma sorusu alani **yoktur**.
    Bag ``research_question.related_claims`` ile ters yonunde kurulur, yani
    sorudan iddiaya gitmek icin once soru kaydini bulup ``related_claims``
    listesini okumak gerekir.
    """
    zincir: list[Zincir] = [Zincir("soru", rq_id, YAPISAL)]
    for kayit, kimlik in _kimlikler(durum, "research_question"):
        if kimlik != rq_id:
            continue
        for claim_id in (kayit.get("related_claims") or []):
            if not isinstance(claim_id, str):
                continue
            zincir.append(Zincir("iddia", claim_id, YAPISAL))
            for kaynak in iddiyanin_dayandigi_kaynaklar(durum, claim_id):
                zincir.append(Zincir("kaynak", kaynak, YAPISAL))
    return zincir


def retraksiyona_ugrayan_iddialar(durum: dict) -> list[str]:
    """Geri cekilmis kaynagi kullanan iddialar (yapisal yuru)."""
    geri = {kimlik for kayit, kimlik in _kimlikler(durum, "source")
            if kayit.get("retraction_status") == "retracted"}
    if not geri:
        return []
    sonuc = []
    for kaynak in sorted(geri):
        sonuc.extend(source_kullanan_iddialar(durum, kaynak))
    return sorted(set(sonuc))


def kanitsiz_iddialar(durum: dict) -> list[str]:
    """Hic kaniti olmayan iddialar."""
    return sorted(kimlik for kayit, kimlik in _kimlikler(durum, "claim")
                  if not (kayit.get("evidence_ids") or []))


def celiskili_iddialar(durum: dict) -> list[str]:
    """Celiskili iddialar (anlamsal yuru)."""
    sonuc: set[str] = set()
    for kayit, kimlik in _kimlikler(durum, "claim"):
        for kenar in kenar_tablosu():
            if kenar.kayit_tipi != "claim" or kenar.tur != ANLAMSAL:
                continue
            deger = kayit.get(kenar.alan_adi)
            if deger is None:
                continue
            liste = deger if kenar.coklu_mu else [deger]
            for diger in liste:
                if isinstance(diger, str) and diger != kimlik:
                    sonuc.add(kimlik)
                    sonuc.add(diger)
    return sorted(sonuc)