# -*- coding: utf-8 -*-
"""Kaynak dogrulama sonuclarini siniflandir.

Aracin 0.60 esigi kasidir: yazar ve yil tutuyorsa bambaşka bir makale de
esigi gecebilir (Saha 2020 -> 0.782, ama cozulen kayit "Intra- and
Inter-subject Variability in EEG-Based Sensorimotor Brain Computer
Interfaces" idi). Buna karsi, yazar listeleri uzun/kisaltilmis oldugu icin
yazar alanini cok sert eleyen kurallar da dogru eslesmeleri disari atar
(Gama 2014 ve Mitchell 2019 yazar puani 0.767 olmasina ragmen ayni
kayittir).

Bu yuzden kural, DOI'nin **kimligini** belirleyen alanlara bakar:
baslik ve yil. Dergi ve yazar alanlari yalnizca "celisen" bir kaydi
isaretlemek icin incelenir, tek basina ret sebebi degildir.

Siniflar:
  KATTI   - kimlik alanlari (baslik, yil) her iki kaynakta da guclu
  SUPHELI - kimlik alanlarindan biri zayif; kaynakca yazilmaz
  RED     - dogrulama hic gecmedi
"""
from __future__ import annotations

import json
import sys
from urllib.parse import quote
from urllib.request import Request, urlopen
from pathlib import Path

KUTU = Path(__file__).resolve().parent
KAYNAK = KUTU / "kaynak_dogrulama.json"

# Kimlik alanlari: her iki dogrulama kaynaginda da bu esikleri asmali.
KATTI_ESIK = {"title": 0.85, "year": 0.50}
# Celiski isaretleyen ama tek basina ret etmeyen alanlar.
SUPHELI_ESIK = {"author": 0.60, "journal": 0.25}


def _etiket(s: dict) -> str:
    y = s["authors"][0] if s["authors"] else "?"
    return f"{y.split(',')[0]} {s['year']}"


def _crossref_ust_veri(doi: str) -> tuple[str, str, str]:
    """DOI'nun Crossref kaydindan baslik/dergi/yil okur (insan kontrolu icin)."""
    istek = Request(
        f"https://api.crossref.org/works/{quote(doi, safe='')}",
        headers={"User-Agent": "AcademicThesisWriter/1.0 (dogrulama)"},
    )
    try:
        with urlopen(istek, timeout=30) as yanit:
            mesaj = json.load(yanit)["message"]
    except Exception as exc:
        return ("HATA", str(exc), "")
    yil = ""
    for alan in ("published-print", "published-online", "issued"):
        parcalar = (mesaj.get(alan) or {}).get("date-parts") or []
        if parcalar and parcalar[0]:
            yil = str(parcalar[0][0])
            break
    return (
        (mesaj.get("title") or [""])[0],
        (mesaj.get("container-title") or [""])[0],
        yil,
    )


def degerlendir(sonuc: dict) -> str:
    if sonuc.get("durum") != "verified":
        return "RED"
    detay = sonuc.get("dogrulama_detayi") or {}
    if len(detay) < 2:
        return "SUPHELI"
    en_zayif = {
        alan: min(d.get(alan, 0.0) for d in detay.values())
        for alan in ("title", "author", "year", "journal")
    }
    sonuc["en_zayif_alan"] = en_zayif
    kimlik = all(
        en_zayif[alan] >= KATTI_ESIK[alan] for alan in KATTI_ESIK
    )
    celiski = [
        alan for alan, esik in SUPHELI_ESIK.items() if en_zayif[alan] < esik
    ]
    sonuc["celisen_alanlar"] = celiski
    return "KATTI" if kimlik and not celiski else "SUPHELI"


def main() -> int:
    veri = json.loads(KAYNAK.read_text(encoding="utf-8"))
    sonuclar = veri["sonuclar"]

    katti, supheli, red = [], [], []
    for s in sonuclar:
        sinif = degerlendir(s)
        s["sinif"] = sinif
        {"KATTI": katti, "SUPHELI": supheli, "RED": red}[sinif].append(s)

    print("=" * 80)
    print("KATTI - DOI kimligi her iki kaynakta da teyit edildi")
    print("=" * 80)
    for s in katti:
        z = s["en_zayif_alan"]
        gercek_baslik, gercek_dergi, gercek_yil = _crossref_ust_veri(s["doi"])
        s["crossref_ust_veri"] = {
            "baslik": gercek_baslik, "dergi": gercek_dergi, "yil": gercek_yil,
        }
        print(f"\n  {_etiket(s)}   {s['doi']}")
        print(f"    kaynakca  : {s['title']}")
        print(f"    crossref : {gercek_baslik}")
        print(f"    dergi    : kaynakca '{s['journal']}' | crossref '{gercek_dergi}'")
        print(f"    puan     : {s['dogrulama_skoru']:.3f} | "
              f"baslik {z['title']:.2f} yazar {z['author']:.2f} "
              f"yil {z['year']:.2f} dergi {z['journal']:.2f}")

    print()
    print("=" * 80)
    print("SUPHELI - kaynakcya yazilmaz")
    print("=" * 80)
    for s in supheli:
        z = s.get("en_zayif_alan", {})
        s_ = s.get("celisen_alanlar", [])
        print(f"  {_etiket(s):<20} {s.get('dogrulama_skoru', 0):.3f} "
              f"celiski: {', '.join(s_) or '-'}")
        print(f"  {'':<20} benzer: {(s.get('kayit_usti_baslik') or '')[:66]}")

    print()
    print("=" * 80)
    print(f"RED - dogrulama gecmedi ({len(red)})")
    print("=" * 80)
    for s in red:
        print(f"  {_etiket(s):<20} en iyi aday puani "
              f"{s.get('on_eleme_puani', 0):.3f}")

    veri["kabul"] = {
        "kural": "verified + baslik>=0.85 + yil>=0.50 + yazar>=0.60 + dergi>=0.25",
        "katti_doi": [s["doi"] for s in katti],
        "ozet": {"katti": len(katti), "supheli": len(supheli), "red": len(red)},
    }
    KAYNAK.write_text(json.dumps(veri, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print(f"SONUC: katti {len(katti)} | supheli {len(supheli)} | red {len(red)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
