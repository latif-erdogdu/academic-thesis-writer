# -*- coding: utf-8 -*-
"""Dogrulama sonrasinda hatali cikan kaynakca girdilerini yeniden ara.

Kullanim:
    python thesis_output/fix_refs.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.source_verify.bibliographic import (  # noqa: E402
    compute_bibliographic_match,
)

HEDEFLER = [
    {
        "etiket": "Blankertz 2006 (JUAIS, gercek baslik 'user specific brain states')",
        "kaynak": {
            "title": "The Berlin Brain-Computer Interface: Machine "
                     "Learning-Based Detection of User Specific Brain States",
            "authors": ["Blankertz, Lutz", "Muller-Putz, Sven L.",
                        "Dornhege, Frank", "Curio, Gerhard", "Hau, Jan"],
            "year": 2006,
            "journal": "Journal of Universal Access in the Information Society",
        },
    },
    {
        "etiket": "Shen 2019 (PLOS Comp Biol, gercek baslik 'End-to-end deep ...' kontrolu)",
        "kaynak": {
            "title": "Deep image reconstruction from human brain activity",
            "authors": ["Shen, Xing", "Chen, Hao", "Zhang, Yu"],
            "year": 2019,
            "journal": "PLOS Computational Biology",
        },
    },
    {
        "etiket": "Hochberg 2012 (Nature, tam yazar listesi)",
        "kaynak": {
            "title": "Reach and grasp by people with tetraplegia using a "
                     "neurally controlled robotic arm",
            "authors": ["Hochberg, Leigh R.", "Bhad, T"],
            "year": 2012,
            "journal": "Nature",
        },
    },
    {
        "etiket": "Lujan 2015 (Nature Reviews Neuroscience)",
        "kaynak": {
            "title": "Out of the lab: The real-world complexities of "
                     "brain-computer interface clinical research",
            "authors": ["Lujan, Macy A.", "Makin, James E.", "Birbaumer, Niels"],
            "year": 2015,
            "journal": "Nature Reviews Neuroscience",
        },
    },
    {
        "etiket": "Wolpaw 2002 (Clinical Neurophysiology)",
        "kaynak": {
            "title": "Brain-computer interfaces for communication and control",
            "authors": ["Wolpaw, Jonathan R.", "Birbaumer, Niels",
                        "McFarland, Dennis J."],
            "year": 2002,
            "journal": "Clinical Neurophysiology",
        },
    },
    {
        "etiket": "Wolpaw 2016 (J Neural Eng, ilk uluslarasi toplanti derlemesi)",
        "kaynak": {
            "title": "Brain-computer interface technology: A review of the "
                     "first international meeting",
            "authors": ["Wolpaw, Jonathan R.", "McFarland, Dennis J.",
                        "Newey, Craig", "Vaughan, Theodore M.", "Lin, Zhiming"],
            "year": 2016,
            "journal": "Journal of Neural Engineering",
        },
    },
    {
        "etiket": "Young 2017 (Physical Therapy, stroke)",
        "kaynak": {
            "title": "Potential for brain-computer interface application in "
                     "the treatment of stroke",
            "authors": ["Young, Alexander W.", "Sollfrank, Hubert"],
            "year": 2017,
            "journal": "Physical Therapy",
        },
    },
    {
        "etiket": "Tangermann 2012 (Frontiers in Neuroscience, BCI Competition III)",
        "kaynak": {
            "title": "Review of the BCI competition III",
            "authors": ["Tangermann, Michael", "Muller-Putz, Sven L.",
                        "Riedl, Sebastian", "Schwarzenberg, Georg"],
            "year": 2012,
            "journal": "Frontiers in Neuroscience",
        },
    },
    {
        "etiket": "Krauledat 2013 (PLoS ONE, zero-training for BCI)",
        "kaynak": {
            "title": "Towards zero training for BCI",
            "authors": ["Krauledat, Jan Hendrik", "Mullen, Molly E.",
                        "Cheng, Robert", "Groneveld, Pieter"],
            "year": 2013,
            "journal": "PLoS ONE",
        },
    },
    {
        "etiket": "Birbaumer 2010 (Frontiers in Neuroscience, honest reporting)",
        "kaynak": {
            "title": "Brain-computer interface research: Honest reporting "
                     "on the state of the art",
            "authors": ["Birbaumer, Niels"],
            "year": 2010,
            "journal": "Frontiers in Neuroscience",
        },
    },
    {
        "etiket": "Biddiss 2012 (Frontiers in Neuroscience, closed-loop stimulation)",
        "kaynak": {
            "title": "BCI-driven control of closed-loop brain stimulation: "
                     "Attitudes and ethical considerations",
            "authors": ["Biddiss, Ewan A.", "McIntyre, Adam"],
            "year": 2012,
            "journal": "Frontiers in Neuroscience",
        },
    },
    {
        "etiket": "Sample 2017 (Philosophy & Technology, Mind the Gap)",
        "kaynak": {
            "title": "Mind the Gap: Ethics and Human Technologies",
            "authors": ["Sample, Matthew", "Racine, Eric"],
            "year": 2017,
            "journal": "Philosophy & Technology",
        },
    },
    {
        "etiket": "Ienca 2017 (Life Sciences Society Policy)",
        "kaynak": {
            "title": "Towards new human rights in the age of neuroscience "
                     "and neurotechnology",
            "authors": ["Ienca, Andrea", "Andorno, Demetrio"],
            "year": 2017,
            "journal": "Life Sciences Society Policy",
        },
    },
    {
        "etiket": "Vetter 2019 (Cambridge Quarterly of Bioethics)",
        "kaynak": {
            "title": "Reading and writing the brain: Neurotechnology, "
                     "neuroethics and free will",
            "authors": ["Vetter, Denise S.", "Steinbrecher, Philipp S.",
                        "Maurer, Helder", "Ienca, Andrea",
                        "MacKay, David J."],
            "year": 2019,
            "journal": "Cambridge Quarterly of Bioethics",
        },
    },
    {
        "etiket": "Wajnryb 2019 (Journal of Medical Ethics)",
        "kaynak": {
            "title": "The ethical dimensions of brain-computer interfaces",
            "authors": ["Wajnryb, Patricia"],
            "year": 2019,
            "journal": "Journal of Medical Ethics",
        },
    },
    {
        "etiket": "Clausen 2013 (Science and Engineering Ethics)",
        "kaynak": {
            "title": "Man, machine and in between: On the concept of a "
                     "brain-computer interface",
            "authors": ["Clausen, Jørgen"],
            "year": 2013,
            "journal": "Science and Engineering Ethics",
        },
    },
    {
        "etiket": "Farwell 1986 (Communications of the ACM, The on-line brain)",
        "kaynak": {
            "title": "The on-line brain",
            "authors": ["Farwell, Lawrence A.", "Donchin, Ehud"],
            "year": 1986,
            "journal": "Communications of the ACM",
        },
    },
    {
        "etiket": "Kostas 2020 (Clinical Neurophysiology, EEG ML framework)",
        "kaynak": {
            "title": "A machine learning framework for EEG classification",
            "authors": ["Kostas, Dimitrios", "Rudzicz, Filip"],
            "year": 2020,
            "journal": "Clinical Neurophysiology",
        },
    },
    {
        "etiket": "Lebedev 2019 (PLoS ONE, mind-reading machine)",
        "kaynak": {
            "title": "How to build a mind-reading machine: Neural bases of "
                     "human image reconstruction",
            "authors": ["Lebedev, Alexander O.", "Gordon, Stephen M.",
                        "Fejdo, Jasmin", "Hughes, Eric M.", "Pang, J. L."],
            "year": 2019,
            "journal": "PLoS ONE",
        },
    },
    {
        "etiket": "Adrian 1934 (Brain, physiological basis of perception)",
        "kaynak": {
            "title": "The physiological basis of perception",
            "authors": ["Adrian, Edgar D.", "Matthews, B. H. C."],
            "year": 1934,
            "journal": "Brain",
        },
    },
    {
        "etiket": "Lundberg 2017 (NIPS, SHAP)",
        "kaynak": {
            "title": "A unified approach to interpreting model predictions",
            "authors": ["Lundberg, Scott M.", "Lee, Su-In"],
            "year": 2017,
            "journal": "Advances in Neural Information Processing Systems",
        },
    },
    {
        "etiket": "Suh 2021 (ICASSP, generative pretrained transformer for EEG)",
        "kaynak": {
            "title": "Generative Pretrained Transformer for EEG Signal Analysis",
            "authors": ["Suh, S.", "Svec, W. M.", "Chandrasekaran, S."],
            "year": 2021,
            "journal": "ICASSP",
        },
    },
    {
        "etiket": "McFarland 2017 (Handbook of Clinical Neurology, BCI review)",
        "kaynak": {
            "title": "Brain-computer interfaces",
            "authors": ["McFarland, Dennis J.", "Wolpaw, Jonathan R."],
            "year": 2017,
            "journal": "Handbook of Clinical Neurology",
        },
    },
    {
        "etiket": "Niedermeyer 2005 (EEG kitap, 3. baski)",
        "kaynak": {
            "title": "Electroencephalography: Basic principles, clinical "
                     "applications, and related fields",
            "authors": ["Niedermeyer, Ernst", "Lopes da Silva, Fernando H."],
            "year": 2005,
            "journal": "Oxford University Press",
        },
    },
]


def adaylar(baslik: str) -> list[dict]:
    istek = Request(
        "https://api.crossref.org/works?rows=8&select=DOI,title,author,"
        "container-title,issued,published-print,published-online,type,publisher"
        f"&query.bibliographic={quote(baslik)}",
        headers={"User-Agent": "AcademicThesisWriter/1.0 (dogrulama)"},
    )
    try:
        with urlopen(istek, timeout=30) as yanit:
            return json.load(yanit)["message"]["items"]
    except Exception as exc:
        print(f"    arama hatasi: {exc}")
        return []


def cevir(aday: dict) -> dict:
    yazarlar = [
        f"{a.get('family', '')}, {a.get('given', '')}".strip(", ")
        for a in aday.get("author", []) if a.get("family") or a.get("given")
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
    }


def main() -> int:
    sonuclar = []
    for hedef in HEDEFLER:
        kaynak = hedef["kaynak"]
        print(f"\n{hedef['etiket']}")
        bulunanlar = adaylar(kaynak["title"])
        time.sleep(0.3)
        puanli = []
        for aday in bulunanlar:
            db = cevir(aday)
            if not db["doi"]:
                continue
            es = compute_bibliographic_match(kaynak, db)
            puanli.append((es.overall_score, db, es))
        puanli.sort(key=lambda x: x[0], reverse=True)
        if not puanli:
            print("    aday yok")
            sonuclar.append({"hedef": hedef["etiket"], "durum": "aday_yok"})
            continue
        for skor, db, es in puanli[:2]:
            print(f"    {skor:.3f}  {db['doi']}")
            print(f"          baslik : {db['title'][:72]}")
            print(f"          dergi  : {db['journal'][:60]} ({db['type']})")
            print(f"          alanlar: baslik {es.title_score:.2f} yazar "
                  f"{es.author_score:.2f} yil {es.year_score:.2f} "
                  f"dergi {es.journal_score:.2f}")
        sonuclar.append({
            "hedef": hedef["etiket"],
            "kaynak": kaynak,
            "en_iyi_doi": puanli[0][1]["doi"],
            "en_iyi_puan": puanli[0][0],
            "kayit_usti_baslik": puanli[0][1]["title"],
            "kayit_usti_dergi": puanli[0][1]["journal"],
            "alanlar": {
                "baslik": puanli[0][2].title_score,
                "yazar": puanli[0][2].author_score,
                "yil": puanli[0][2].year_score,
                "dergi": puanli[0][2].journal_score,
            },
        })

    cikti = Path(__file__).resolve().parent / "yeniden_arama.json"
    cikti.write_text(json.dumps(sonuclar, ensure_ascii=False, indent=2),
                     encoding="utf-8")
    print(f"\n-> {cikti.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
