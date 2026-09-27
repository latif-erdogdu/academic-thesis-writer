# -*- coding: utf-8 -*-
"""Kaynakca icin gercek DOI cozumleme + dogrulama.

Her kaynak icin Crossref/OpenAlex uzerinden bibliyografik sorgu calistirir,
bulunan DOI'yi dogrulama modulunden gecirir ve sonucu JSON olarak yazar.

Kullanim:
    python thesis_output/resolve_references.py [cikti.json]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.source_verify.bibliographic import compare_titles  # noqa: E402
from tools.source_verify.verify import verify_source  # noqa: E402

HEADERS = {
    "User-Agent": "AcademicThesisWriter/1.0 (mailto:research@example.com)"
}

# (kisaltma, baslik, soyadlar, yil, dergi)
KAYNAKLAR: list[tuple[str, str, list[str], int, str]] = [
    ("Adrian 1934", "The physiological basis of perception",
     ["Adrian", "Matthews"], 1934, "Brain"),
    ("Berger 1929", "Über das Elektrenkephalogramm des Menschen",
     ["Berger"], 1929, "Archiv für Psychiatrie und Nervenkrankheiten"),
    ("Farwell 1986", "The on-line brain", ["Farwell", "Donchin"], 1986,
     "Communications of the ACM"),
    ("Vidal 1973", "Toward direct brain-computer communication",
     ["Vidal"], 1973, "Annual Review of Biophysics and Bioengineering"),
    ("Wolpaw 2002", "Brain-computer interfaces for communication and control",
     ["Wolpaw", "Birbaumer", "McFarland", "Pfurtscheller", "Vaughan", "Nijholt"],
     2002, "Clinical Neurophysiology"),
    ("Blankertz 2006",
     "The Berlin brain-computer interface: Machine learning-based detection "
     "of user-specific brain activities",
     ["Blankertz", "Müller-Putz", "Dornhege", "Curio", "Hau"], 2006,
     "Journal of Universal Access in the Information Society"),
    ("Krauledat 2013", "Towards zero-training for BCI",
     ["Krauledat", "Mullen", "Cheng", "Groneveld"], 2013, "PLoS ONE"),
    ("Birbaumer 2010",
     "Brain-computer interface research: Honest reporting on the state of "
     "the art", ["Birbaumer"], 2010, "Frontiers in Neuroscience"),
    ("Schirrmeister 2017",
     "Deep learning with convolutional neural networks for EEG decoding "
     "and visualization",
     ["Schirrmeister", "Springenberg", "Fiederer"], 2017, "Human Brain Mapping"),
    ("Kostas 2020", "A machine learning framework for EEG classification",
     ["Kostas", "Rudzicz"], 2020, "Clinical Neurophysiology"),
    ("Suh 2021", "Generative pretrained transformer for EEG signal analysis",
     ["Suh", "Svec", "Chandrasekaran"], 2021,
     "2021 IEEE International Conference on Acoustics, Speech and Signal "
     "Processing (ICASSP)"),
    ("Saha 2020",
     "Inter-subject variability in EEG-based sensorless BCI: A review",
     ["Saha", "Baumert"], 2020, "Journal of Neural Engineering"),
    ("Lujan 2015",
     "Out of the lab: The real-world complexities of brain-computer "
     "interface clinical research",
     ["Lujan", "Makin", "Birbaumer"], 2015, "Nature Reviews Neuroscience"),
    ("Hochberg 2006",
     "Neuronal ensemble control of prosthetic devices by a human with "
     "tetraplegia", ["Hochberg", "Serruya", "Donoghue"], 2006, "Nature"),
    ("Hochberg 2012",
     "Reach and grasp by people with tetraplegia using a neurally "
     "controlled robotic arm", ["Hochberg", "Donoghue"], 2012, "Nature"),
    ("Young 2017",
     "Potential for brain-computer interface application in the treatment "
     "of stroke",
     ["Young", "Sollfrank", "Dragan", "Greenberg", "Shadmehr"], 2017,
     "Physical Therapy"),
    ("Biddiss 2012",
     "BCI-driven control of closed-loop brain stimulation: Attitudes and "
     "ethical considerations", ["Biddiss", "McIntyre"], 2012,
     "Frontiers in Neuroscience"),
    ("Tangermann 2012", "Review of the BCI competition III",
     ["Tangermann", "Müller-Putz", "Riedl", "Schwarzenberg"], 2012,
     "Frontiers in Neuroscience"),
    ("McFarland 2017", "Brain-computer interfaces",
     ["McFarland", "Wolpaw"], 2017, "Handbook of Clinical Neurology"),
    ("Wolpaw 2016",
     "Brain-computer interface technology: A review of the first "
     "international meeting",
     ["Wolpaw", "McFarland", "Newey", "Vaughan", "Lin"], 2016,
     "Journal of Neural Engineering"),
    ("Clausen 2013",
     "Man, machine and in between: On the concept of a brain-computer "
     "interface", ["Clausen"], 2013, "Science and Engineering Ethics"),
    ("Ienca 2017",
     "Towards new human rights in the age of neuroscience and "
     "neurotechnology", ["Ienca", "Andorno"], 2017,
     "Life Sciences Society Policy"),
    ("Vetter 2019",
     "Reading and writing the brain: Neurotechnology, neuroethics and "
     "free will",
     ["Vetter", "Steinbrecher", "Maurer", "Ienca", "MacKay"], 2019,
     "Cambridge Quarterly of Bioethics"),
    ("Wajnryb 2019", "The ethical dimensions of brain-computer interfaces",
     ["Wajnryb"], 2019, "Journal of Medical Ethics"),
    ("Lebedev 2019",
     "How to build a mind-reading machine: neural bases of human image "
     "reconstruction",
     ["Lebedev", "Gordon", "Fejdo", "Hughes", "Pang"], 2019, "PLoS ONE"),
    ("Shen 2019",
     "End-to-end deep image reconstruction from human brain activity",
     ["Shen", "Chen", "Zhang"], 2019, "PLOS Computational Biology"),
    ("Altaheri 2021",
     "Deep learning techniques for classification of electroencephalogram "
     "(EEG) motor imagery (MI) signals: A review",
     ["Altaheri", "Muhammad", "Alsulaiman"], 2021,
     "Neural Computing and Applications"),
]


def crossref_coz(baslik: str, yil: int) -> tuple[str | None, str]:
    """Crossref bibliyografik sorgu ile en iyi eslesen DOI'yi dondurur.

    Crossref siralamasi alaka sirasi verir; ancak ilk kayit her zaman dogru
    degildir (orn. IEEE abstract book girisleri one cikabilir). Bu yuzden
    adaylar aracinin kendi baslik karsilastirma fonksiyonuyla puanlanir ve
    en yuksek puanli aday secilir.
    """
    params = {
        "query.bibliographic": baslik,
        "rows": 8,
        "select": "DOI,title,container-title,issued,author",
        "mailto": "research@example.com",
    }
    resp = requests.get("https://api.crossref.org/works", params=params,
                        headers=HEADERS, timeout=30)
    resp.raise_for_status()
    ogeler = resp.json().get("message", {}).get("items", [])
    if not ogeler:
        return None, "Crossref: sonuc yok"

    en_iyi_doi, en_iyi_skor = None, -1.0
    for oge in ogeler:
        aday_baslik = (oge.get("title") or [""])[0]
        skor = compare_titles(baslik, aday_baslik)
        if skor > en_iyi_skor:
            en_iyi_skor, en_iyi_doi = skor, oge.get("DOI")
    return en_iyi_doi, f"{len(ogeler)} aday, en iyi baslik skoru {en_iyi_skor:.3f}"


def main() -> int:
    sonuclar = []
    for kisaltma, baslik, yazarlar, yil, dergi in KAYNAKLAR:
        kayit: dict = {
            "kisaltma": kisaltma,
            "baslik": baslik,
            "yil": yil,
            "dergi": dergi,
        }
        try:
            doi, not_ = crossref_coz(baslik, yil)
        except Exception as e:  # ağ hatası
            doi, not_ = None, f"Crossref hatasi: {e}"
        kayit["crossref_not"] = not_
        kayit["doi"] = doi
        if doi:
            try:
                r = verify_source({
                    "doi": doi, "title": baslik, "authors": yazarlar,
                    "year": yil, "journal": dergi,
                })
                kayit["durum"] = r.status
                kayit["skor"] = round(r.bibliographic_match, 3)
                kayit["kaynaklar"] = sorted(r.verification_sources)
                kayit["puan_dagilimi"] = r.verification_details
            except Exception as e:
                kayit["durum"] = "HATA"
                kayit["skor"] = None
                kayit["hata"] = str(e)[:120]
        else:
            kayit["durum"] = "DOI_BULUNAMADI"
            kayit["skor"] = None
        sonuclar.append(kayit)
        durum = kayit.get("durum")
        skor = kayit.get("skor")
        print(f'{kisaltma:20s} {str(durum):18s} {skor}  {doi}', flush=True)
        time.sleep(0.4)

    cikti = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        Path(__file__).resolve().parent / "kaynak_dogrulama.json")
    cikti.write_text(json.dumps(sonuclar, ensure_ascii=False, indent=2),
                     encoding="utf-8")
    dogrulanan = sum(1 for s in sonuclar if s.get("durum") == "verified")
    print(f"\n{dogrulanan}/{len(sonuclar)} kaynak 'verified' -> {cikti.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
