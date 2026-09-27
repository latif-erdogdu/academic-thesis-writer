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

Iki kavram ayridir
------------------
  onay  -> insan bir karari VERDI, kapı acildi (human_approvals)
  hazir -> verilen karari uygulamaya hazir veri var (write, export)

`kapi_acik_mi()` sadece onayi sorar. `kontrol_yaz()` ayrica verinin
gercekten hazir olup olmadigini da dener; yalniz "onay var" demek, bos bir
capaya onay vermis olmak kadar anlamsizdir.

Kapsam ilkesi
-------------
Bu modul KALDIYLA degil, veriyle karar verir. Onaylanmamis bir asamayi
otomatik gecmek mumkun degildir; onun yerine eksigi ADIYLA bildirir.
"""
from __future__ import annotations

from typing import Any, Callable

from tools.atw.graph import (
    kanitsiz_iddialar,
    kopuk_baglari,
    retraksiyona_ugrayan_iddialar,
)
from tools.atw.state import APPROVAL_GATES

# Her kapi icin: kapinin hangi registry'leri bos olmamali, ve o asamada
# calisacak ek hazirlik denetimi. Sirayla bagimlidir: bir onceki kapinin
# onayi olmadan sonrakinin denetimi calistirilmaz.
#
# DIKKAT: buradaki registry tuple'lari HIC OKUNMAZ (yalnizca uyelik ve
# sira denetimi yapilir). Canli hazirlik denetimi `GATE_HAZIRLIK`te.
# Buradaki degerler belge amaclidir; degistirdiginizde `GATE_HAZIRLIK`i de
# degistirin.
GATE_ASAMALARI: dict[str, tuple[str, ...]] = {
    "research_question": ("research_questions",),
    "search_strategy": ("search_runs",),
    "source_set": ("sources",),
    "research_gap": ("gap_registry",),
    # `chapters` BILINCLI OLARAK bos. Bu kapinin on kosulu, kapinin
    # yazdirdigi seyin kendisiydi: `chapters`'i dolduran tek yol
    # `cmd_write`, o da `methodology` kapisinin arkasinda. Boylece ilk
    # bolum yazilamiyordu. Ayrinti: `test_methodology_kapisi_bos_bolumle_yazilabilir`.
    "methodology": (),
    "findings": ("findings_registry",),
    # final_thesis'te ayrica butunluk ve kanit denetimi calisir; tez
    # kanitsiz iddia veya kopuk referans iceriyorsa onaylanabilir degildir.
    "final_thesis": (),
}


class OnayHatasi(RuntimeError):
    """Kapi acilmadan once bir asamaya girilmeye calisildi."""


def kapi_acik_mi(durum: dict[str, Any], kapi: str) -> bool:
    """Verilen kapi insan tarafindan onaylanmis mi?

    Taninmayan kapi adi hata verir; sessizce "kapali" donmek, kapi
    sistemine eklenen ama burada unutulan bir asamayi gizlerdi.
    """
    if kapi not in GATE_ASAMALARI:
        raise ValueError(f"bilinmeyen onay kapisi: {kapi}")
    return bool(durum.get("human_approvals", {}).get(kapi, False))


def onay_ver(durum: dict[str, Any], kapi: str) -> dict[str, Any]:
    """Kapiyi acar ve durumu gunceller.

    Kapi acilmadan once ONCEDEN KAPALI olan tum kapilarin acik olmasi
    gerekir; aksi halde akis atlanmis olur.
    """
    if kapi not in GATE_ASAMALARI:
        raise ValueError(f"bilinmeyen onay kapisi: {kapi}")

    eksik = [
        onceki
        for onceki in APPROVAL_GATES[: APPROVAL_GATES.index(kapi)]
        if not kapi_acik_mi(durum, onceki)
    ]
    if eksik:
        raise OnayHatasi(
            f"'{kapi}' kapisi acilamiyor: onceki asamalar onayli degil -> {', '.join(eksik)}"
        )

    durum.setdefault("human_approvals", {})[kapi] = True
    return durum


def onay_geri_al(durum: dict[str, Any], kapi: str) -> dict[str, Any]:
    """Kapiyi kapatir ve sonraki acik kapilari da kapatir.

    Bir onay geri alinirsa, ona dayanan onaylar da gecersizdir; aksi halde
    "methodology geri alindi ama final_thesis onayli" gibi durum olusur.
    """
    if kapi not in GATE_ASAMALARI:
        raise ValueError(f"bilinmeyen onay kapisi: {kapi}")

    onaylar = durum.setdefault("human_approvals", {})
    onaylar[kapi] = False
    for sonraki in APPROVAL_GATES[APPROVAL_GATES.index(kapi) + 1 :]:
        onaylar[sonraki] = False
    return durum


def _bos_registry(durum: dict[str, Any], alan: str) -> bool:
    return not (durum.get(alan) or [])


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


# Kapi basina hazirlik denetimleri. Bos liste = ek kosul yok.
def _registry_dolu(durum: dict[str, Any], alan: str) -> list[str]:
    """Registry bos ise eksigi dondurur."""
    if _bos_registry(durum, alan):
        return [f"'{alan}' boş — bu aşamanın çıktısı henüz üretilmemiş"]
    return []


# Kapi basina hazirlik denetimleri. Her kapi kendi asamasinin registry'sini
# doldurmus olmalidir; aksi halde kapı, içliği boş bir belgeye verilmiş
# onay olur.
#
# KURAL (dolaylı ama zorunlu): bir kapinin hazirlik denetimi YALNIZCA
# kendisinden ONCE uretilen veriye bakabilir. Denetimi, kapinin arkasindaki
# komutun URETTIGI registry'ye bakmak dairesel bagimlilik kurar ve o
# komutun hic calismamasina yol acar. `methodology` kapisi tam olarak
# boyle bir durumdu: `chapters` bu kapinin arkasindaki `cmd_write` ile
# doluyor, `cmd_write` da bu kapinin on kosulu olarak `chapters`'i
# ariyordu. `methodology` bilincli olarak listede YOK; hazirlik denetimi
# tasimayan tek kapi `final_thesis`tir (butunluk + kanit).
#
# `test_baska_kapilarin_hazirligi_korunur` bu kurali digerleri icin
# sabitler.
GATE_HAZIRLIK: dict[str, Callable[[dict[str, Any]], list[str]]] = {
    "research_question": lambda d: _registry_dolu(d, "research_questions"),
    "search_strategy": lambda d: _registry_dolu(d, "search_runs"),
    "source_set": lambda d: _registry_dolu(d, "sources"),
    "research_gap": lambda d: _registry_dolu(d, "gap_registry"),
    "findings": lambda d: _registry_dolu(d, "findings_registry"),
    "final_thesis": _bulgulari_tara,
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

    Hazirlik denetimi tasimayan kapilarda liste bos doner. `methodology`
    ve `final_thesis` boyledir: `methodology` ciktilari `chapters` bu
    kapinin arkasinda yazildigi icin, `final_thesis` ise butunluk
    denetimini `cmd_export` yolunda zaten yapiyor.
    """
    if kapi not in GATE_ASAMALARI:
        raise ValueError(f"bilinmeyen onay kapisi: {kapi}")
    denetim = GATE_HAZIRLIK.get(kapi)
    return list(denetim(durum)) if denetim is not None else []


def kontrol_yaz(durum: dict[str, Any], kapi: str) -> list[str]:
    """Yazim/ihracat icin kapinin acik ve verinin hazir olup olmadigini doner.

    Donen liste bos ise yazim yapilabilir. Dolu ise her ogge bir engeldir.

    Iki ayri kontrol:
      1. onay   -> insan karari verilmis mi (kapi_acik_mi)
      2. hazirlik -> o karari uygulayacak veri gercekten var mi
    """
    if kapi not in GATE_ASAMALARI:
        raise ValueError(f"bilinmeyen onay kapisi: {kapi}")

    engeller: list[str] = []
    if not kapi_acik_mi(durum, kapi):
        engeller.append(
            f"'{kapi}' kapısı insan onayı bekliyor "
            f"(human_approvals.{kapi} = false)"
        )
    denetim = GATE_HAZIRLIK.get(kapi)
    if denetim is not None:
        engeller.extend(denetim(durum))
    return engeller


def yazim_hazir_mi(durum: dict[str, Any], kapi: str = "methodology") -> bool:
    return not kontrol_yaz(durum, kapi)


def ozet(durum: dict[str, Any]) -> list[tuple[str, bool, list[str]]]:
    """Tum kapilarin durumunu ve engellerini sirayla doner.

    CLI raporu ve `thesis:status` bunu kullanir; akis tek bir yerde
    tanimli kalir, cift tanim olusmaz.
    """
    return [
        (kapi, kapi_acik_mi(durum, kapi), kontrol_yaz(durum, kapi))
        for kapi in APPROVAL_GATES
    ]
