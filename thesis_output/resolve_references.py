# -*- coding: utf-8 -*-
"""Kaynakça için DOI çözümleme — yalnızca araç doğrulamasıyla.

Kural: bir DOI, ``tools.source_verify`` tarafından **doğrulanmadan**
kaynakçaya girmez. Akış:

1. Kaynakça girdisi APA-7 satırından yapılandırılmış alanlara ayrıştırılır.
2. Crossref bibliyografik aramasından adaylar çekilir.
3. Her aday, aracın kendi ``compute_bibliographic_match`` fonksiyonuyla
   puanlanır — araç dışında ikinci bir puanlama uygulanmaz.
4. En iyi aday ancak ``verify_source`` çağrısı ``verified`` dönerse kabul
   edilir (eşik 0.60 ve en az 2 bağımsız kaynak).
5. Sonuç ``kaynak_dogrulama.json`` dosyasına yazılır.

Kullanım:
    python thesis_output/resolve_references.py [cikti.json]
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Optional

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from thesis_output.content_c import KAYNAKCA  # noqa: E402
from tools.source_verify.bibliographic import (  # noqa: E402
    compute_bibliographic_match,
)
from tools.source_verify.verify import verify_source  # noqa: E402

CROSSREF_API = "https://api.crossref.org/works"
ADAY_SAYISI = 8
ESIK = 0.60
USER_AGENT = "AcademicThesisWriter/1.0 (tez kaynak dogrulama)"
MAILTO = "tez@dogrulama.local"

# ---------------------------------------------------------------- ayrıştırma

# "Adrian, E. D., & Matthews, B. H. C." -> ["Adrian, E. D.", "Matthews, B. H. C."]
YAZAR_DESEN = re.compile(
    r"([A-ZÀ-Ýa-zà-ÿ'’\-]+(?:\s+[A-ZÀ-Ýa-zà-ÿ'’\-]+)*)"
    r",\s*((?:[A-Z]\.(?:-[A-Z]\.)?\s*)+)"
)


def _yazarlari_ayir(yazar_metni: str) -> list[str]:
    """APA-7 yazar alanını ayrıştırıcıdan geçirir.

    Uzun liste kısaltmalarındaki "..." sonrasındaki yazarlar da alınır;
    atlanan yazar sayısı bilgi olarak korunmaz çünkü puanlama yalnızca
    ilk üç yazara bakar.
    """
    temiz = yazar_metni.replace("&", ",").replace("…", ",").replace("...", ",")
    eslesmeler = YAZAR_DESEN.findall(temiz)
    if eslesmeler:
        return [f"{soyad}, {adlar.strip()}" for soyad, adlar in eslesmeler]
    # Soyadı biçiminde (virgülsüz) girdi
    soyadlar = [
        parca.strip()
        for parca in re.split(r",(?![^{]*\})", temiz)
        if parca.strip() and " " not in parca.strip()
    ]
    return soyadlar[:5]


def _donemi_ayir(konteyner: str) -> str:
    """Konteyner metninden cilt/numara/sayfa ekini atar."""
    return re.sub(r",\s*\d.*$", "", konteyner).strip().rstrip(".")


def referansi_ayir(ref: str) -> Optional[dict[str, Any]]:
    """Tek bir APA-7 kaynak satırını alanlara ayırır."""
    baslik = re.match(r"^(?P<authors>.+?)\s*\((?P<year>\d{4})\)\.\s*(?P<rest>.+)$", ref)
    if not baslik:
        return None
    parcalar = re.split(r"\.\s+", baslik.group("rest"), maxsplit=1)
    baslik_metni = parcalar[0].strip().rstrip(".")
    konteyner = _donemi_ayir(parcalar[1]) if len(parcalar) > 1 else ""

    return {
        "referans": ref,
        "authors": _yazarlari_ayir(baslik.group("authors")),
        "year": int(baslik.group("year")),
        "title": baslik_metni,
        "journal": konteyner,
    }


# ------------------------------------------------------------------ adaylar


def _crossref_adaylari(baslik: str, yil: Optional[int]) -> list[dict[str, Any]]:
    """Crossref bibliyografik aramasından aday kayıtları çeker."""
    params = {
        "query.bibliographic": baslik,
        "rows": ADAY_SAYISI,
        "mailto": MAILTO,
        "select": (
            "DOI,title,author,container-title,issued,published-print,"
            "published-online,type,publisher"
        ),
    }
    try:
        yanit = requests.get(
            CROSSREF_API,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
        yanit.raise_for_status()
        return yanit.json().get("message", {}).get("items", [])
    except Exception as exc:  # ağ hatası aday listesini boşaltır
        print(f"    arama hatası: {exc}")
        return []


def _crossref_kayda_cevir(aday: dict[str, Any]) -> dict[str, Any]:
    """Crossref yanıtını aracın beklediği kayıt biçimine çevirir."""
    yazarlar = [
        f"{a.get('family', '')}, {a.get('given', '')}".strip(", ")
        for a in aday.get("author", [])
        if a.get("family") or a.get("given")
    ]
    yil = None
    for alan in ("published-print", "published-online", "issued"):
        parcalar = (aday.get(alan) or {}).get("date-parts") or []
        if parcalar and parcalar[0] and parcalar[0][0]:
            yil = parcalar[0][0]
            break
    return {
        "doi": aday.get("DOI", ""),
        "title": (aday.get("title") or [""])[0],
        "authors": yazarlar,
        "year": yil,
        "journal": (aday.get("container-title") or [""])[0],
        "type": aday.get("type", ""),
        "publisher": aday.get("publisher", ""),
    }


# --------------------------------------------------------------------- akış


def cozumle(kayit: dict[str, Any]) -> dict[str, Any]:
    """Tek bir kaynak için DOI çözümler ve doğrular.

    Yalnızca araç doğrulamasından geçen aday kabul edilir. Aday yoksa veya
    hiçbiri eşiği geçmezse sonuç ``cozulmedi`` olur; bu durumda DOI uydurulmaz.
    """
    print(f"\n{kayit['authors'][0] if kayit['authors'] else '?'} "
          f"{kayit['year']}: {kayit['title'][:60]}")

    adaylar = _crossref_adaylari(kayit["title"], kayit["year"])
    time.sleep(0.3)  # Crossref nazik kullanım

    puanlanmis = []
    for aday in adaylar:
        db = _crossref_kayda_cevir(aday)
        if not db["doi"]:
            continue
        es = compute_bibliographic_match(
            {
                "title": kayit["title"],
                "authors": kayit["authors"],
                "year": kayit["year"],
                "journal": kayit["journal"],
            },
            db,
        )
        puanlanmis.append((es.overall_score, db, es))

    puanlanmis.sort(key=lambda x: x[0], reverse=True)

    if not puanlanmis:
        print("    -> aday yok")
        return {**kayit, "durum": "aday_bulunamadi", "doi": None}

    en_iyi_skor, en_iyi, eslesme = puanlanmis[0]
    print(f"    en iyi aday: {en_iyi['doi']} (ön eleme puanı {en_iyi_skor:.3f})")
    print(f"      başlık: {en_iyi['title'][:70]}")

    if en_iyi_skor < ESIK:
        print(f"    -> ön eleme eşiği ({ESIK}) altında, doğrulamaya gönderilmiyor")
        return {
            **kayit,
            "durum": "on_eleme_basarisiz",
            "doi": None,
            "en_iyi_aday": en_iyi,
            "on_eleme_puani": en_iyi_skor,
        }

    dogrulama = verify_source({
        "id": kayit.get("id", ""),
        "doi": en_iyi["doi"],
        "title": kayit["title"],
        "authors": kayit["authors"],
        "year": kayit["year"],
        "journal": kayit["journal"],
    })
    detay = dogrulama.verification_details or {}
    print(f"    -> dogrulama: {dogrulama.status} "
          f"(skor {dogrulama.bibliographic_match}, "
          f"kaynaklar {dogrulama.verification_sources or '-'})")
    for ad, d in detay.items():
        print(f"       {ad:<10} {d['overall']:.3f} | başlık {d['title']:.2f}"
              f" | yazar {d['author']:.2f} | yıl {d['year']:.2f}"
              f" | dergi {d['journal']:.2f}")

    return {
        **kayit,
        "durum": dogrulama.status,
        "doi": en_iyi["doi"] if dogrulama.status == "verified" else None,
        "cozulen_doi": en_iyi["doi"],
        "dogrulama_skoru": dogrulama.bibliographic_match,
        "dogrulama_kaynaklari": dogrulama.verification_sources,
        "dogrulama_detayi": detay,
        "on_eleme_puani": en_iyi_skor,
        "kayit_usti_baslik": en_iyi["title"],
    }


def main() -> int:
    referanslar = [t for tur, t in KAYNAKCA if tur == "ref"]
    girdiler = [r for r in (referansi_ayir(x) for x in referanslar) if r]
    print(f"{len(girdiler)} referans ayrıştırıldı "
          f"({len(referanslar) - len(girdiler)} ayrıştırılamadı)")

    sonuclar = []
    for i, kayit in enumerate(girdiler, 1):
        kayit = {"id": f"REF-{i:02d}", **kayit}
        sonuclar.append(cozumle(kayit))

    dogrulanan = [s for s in sonuclar if s["durum"] == "verified"]
    ozet = {
        "uretim_tarihi": time.strftime("%Y-%m-%d"),
        "kural": "DOI yalnizca arac dogrulamasi 'verified' donerse kabul edilir",
        "esik": ESIK,
        "toplam": len(sonuclar),
        "dogrulanan": len(dogrulanan),
        "dogrulanamayan": len(sonuclar) - len(dogrulanan),
        "sonuclar": sonuclar,
    }
    cikti = Path(__file__).resolve().parent / (sys.argv[1] if len(sys.argv) > 1
                                              else "kaynak_dogrulama.json")
    cikti.write_text(json.dumps(ozet, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{'=' * 60}")
    print(f"{len(dogrulanan)}/{len(sonuclar)} kaynak dogrulandi -> {cikti.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
