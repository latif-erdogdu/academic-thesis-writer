# -*- coding: utf-8 -*-
"""Duzeltmelerden sonra canli dogrulama kaniti.

Bu betik ag cagrisi yapar (Crossref + OpenAlex). Yalnizca elle girilmis
DOI'ler icin kullanilir; kaynak cozumlemesi yapmaz.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.source_verify.verify import verify_source  # noqa: E402

KAYITLAR = [
    {
        "id": "SRC-0001",
        "etiket": "Vidal 1973 (dogru kayit, 2000 oncesi)",
        "doi": "10.1146/annurev.bb.02.060173.001105",
        "title": "Toward direct brain-computer communication",
        "authors": ["Vidal, Jean J."],
        "year": 1973,
        "journal": "Annual Review of Biophysics and Bioengineering",
    },
    {
        "id": "SRC-0002",
        "etiket": "KONTROL: DOI dogru ama baslik yabanci bir kayit",
        "doi": "10.1038/nature04660",
        "title": "Neuronal ensemble control of prosthetic devices",
        "authors": ["Hochberg", "Serruya", "Donoghue"],
        "year": 2006,
        "journal": "Nature",
    },
    {
        "id": "SRC-0003",
        "etiket": "Schirrmeister 2017 (yaygin konu, guncel kayit)",
        "doi": "10.1002/hbm.23730",
        "title": (
            "Deep learning with convolutional neural networks for EEG "
            "decoding and visualization"
        ),
        "authors": ["Schirrmeister, Robin T.", "Springenberg, JT", "Fiederer"],
        "year": 2017,
        "journal": "Human Brain Mapping",
    },
    {
        "id": "SRC-0004",
        "etiket": "Lujan 2015 (yalnizca soyadi girilmis - D2 testi)",
        "doi": "10.1038/nrn.2015.7",
        "title": (
            "Out of the lab: The real-world complexities of brain-computer "
            "interface clinical research"
        ),
        "authors": ["Lujan", "Makin"],
        "year": 2015,
        "journal": "Nature Reviews Neuroscience",
    },
]

print(f"{'etiket':<48} {'durum':<11} {'skor':>6}  alanlar")
print("-" * 100)
for kayit in KAYITLAR:
    sonuc = verify_source(kayit)
    print(f"{kayit['etiket']}")
    print(f"  durum  : {sonuc.status}   (esik 0.60, en az 2 bagimsiz kaynak)")
    print(f"  skor   : {sonuc.bibliographic_match}")
    for kaynak, d in sonuc.verification_details.items():
        print(
            f"  {kaynak:<10} overall {d['overall']:.3f} | baslik {d['title']:.2f}"
            f" | yazar {d['author']:.2f} | yil {d['year']:.2f}"
            f" | dergi {d['journal']:.2f} | doi {'ok' if d['doi_match'] else 'yok'}"
        )
    print(f"  dogrulayan: {sonuc.verification_sources or '-'}")
    print()
