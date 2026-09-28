"""workflows/*.md gercekten CLI'yi anlatıyor mu, yoksa kâğıt üstünde mi?

Neden bu test
-------------
`workflows/` altındaki 8 dosya SKILL.md §7'de listelenir ve ajana
"şunu çalıştır" diye verilir. Ama sekizinin de içeriği salt prosedür:
HİÇBİRİ tek bir `thesis:` komutu anmıyor. Yani ajan bu dosyaları okuyup
neyi hangi komutla yazacağını bulamıyor.

Bu, kilitlenmenin BELGESEL nedeni. `research_questions` registry'sini
dolduran komut (`thesis:record`) vardı ama hiçbir akış dosyasında geçmiyordu;
`research_question` kapısının hazırlığı sağlanmadığı için yedi kapılı
akış ilk adımda kilitleniyordu.

Dahası, akışlar var OLMAYAN dosyaları da vaat ediyordu:
`methodology_state.json`, `literature_matrix.md`, `Kaynarca.bib`,
`01_Giris.md`…`06_Sonuc_Oneri.md`, `Kalite_Raporu.md`. CLI'nin ürettiği
tek çıktı `tez_<thesis_id>.{md,docx,pdf}` (export.py:537). Yani akışlar,
ajanın bulamayacağı bir çıktı ağacını tarif ediyordu.

Bu testler dört kural koyar. Hepsi kuraldır, yasak listesi değil — yeni
bir akış dosyası eklendiğinde de aynı ölçüt geçerli olur:

  1. Akışlarda anılan her `thesis:X` komutu skill.yaml'da gerçekten var.
  2. Her akış EN AZ BİR gerçek komut anar (boş kalmak serbest değil).
  3. Akışların atıf yaptığı her dosya gerçekten var (temsilî çıktı adları
     hariç: `<...>` yer tutucular ve `thesis_state.json`).
  4. Yedi kapının adı ve SIRASI `thesis_creation.md` içinde bulunur; akış
     zinciri tek yerden okunabilir olmalı.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_YAML = REPO_ROOT / ".opencode" / "skill" / "academic-thesis-writer" / "skill.yaml"
WORKFLOW_DIZIN = REPO_ROOT / "workflows"
ANA_AKIS = WORKFLOW_DIZIN / "thesis_creation.md"

# `thesis:record research_questions` gibi bir yazım.
_KOMUT_DESEN = re.compile(r"\bthesis:([a-z][a-z-]*)")

# Bir dosya yolu gibi görünen şey: dizin/veya noktasuz dosya adı.
_DOSYA_DESEN = re.compile(
    r"(?<![\w/.-])"
    r"((?:[\w-]+/)*[\w-]+\.(?:json|md|bib|docx|pdf|yaml|yml))"
    r"(?![\w-])"
)

# Akışların atıf yapabildiği kök dizinler. SKILL.md §7 ve §10 bu
# yolların depo köküne göre yazıldığını söylüyor.
_KOK_DIZINLER = ("schemas", "references", "templates", "workflows", "agents")

# Gerçekten var olmayan ve var OLMAYACAK dosyalar: CLI bunları üretmez.
# Temsili adlar (köşeli parantez, `<...>`) kural dışıdır.
_TEMSILI = re.compile(r"[\[\]<>{}]")

def _skill() -> dict:
    return yaml.safe_load(SKILL_YAML.read_text(encoding="utf-8"))


def _gercek_komutlar() -> set[str]:
    return {k["name"].split(":", 1)[1] for k in _skill()["commands"] if ":" in k["name"]}


def _akis_dosyalari() -> list[Path]:
    dosyalar = sorted(WORKFLOW_DIZIN.glob("*.md"))
    assert dosyalar, f"{WORKFLOW_DIZIN} altında akış dosyası yok"
    return dosyalar


@pytest.fixture(scope="module")
def akislar() -> dict[str, str]:
    return {f.name: f.read_text(encoding="utf-8") for f in _akis_dosyalari()}


# --- 1. anilan komutlar gercek mi --------------------------------------------


def test_akislarda_anilan_komutlar_gercek(akislar: dict[str, str]) -> None:
    """Akışlarda geçen her `thesis:X`, skill.yaml'da ilan edilmiş olmalı."""
    gercek = _gercek_komutlar()
    hayalet: list[str] = []
    for ad, metin in akislar.items():
        for komut in _KOMUT_DESEN.findall(metin):
            if komut not in gercek:
                hayalet.append(f"{ad}: thesis:{komut}")
    assert not hayalet, (
        "Akışlar CLI'da olmayan komutları anıyor:\n  " + "\n  ".join(sorted(hayalet))
    )


# --- 2. her akis en az bir komut anyor mu ------------------------------------


def test_her_akis_en_az_bir_gercek_komut_aniyor(akislar: dict[str, str]) -> None:
    """Sekiz akışın hiçbiri tek bir komut anmıyordu; ajana ne yapacağını söylemiyordu."""
    gercek = _gercek_komutlar()
    susuz = [
        ad
        for ad, metin in akislar.items()
        if not (_KOMUT_DESEN.findall(metin) and set(_KOMUT_DESEN.findall(metin)) & gercek)
    ]
    assert not susuz, (
        "Hiçbir gerçek komut anmayan akışlar: " + ", ".join(susuz)
        + "\n  Her akış, verdiği adımın HANGİ komutla yapılacağını söylemelidir."
    )


# --- 3. atif yapilan dosyalar gercek mi --------------------------------------


def test_akislar_var_olmayan_dosya_adi_adreslemez(akislar: dict[str, str]) -> None:
    """`methodology_state.json`, `Kaynarca.bib`, `01_Giris.md` … hiçbir zaman yok.

    Kural: akışın atıf yaptığı her dosya gerçekten var olmalıdır.

    İki istisna:

    * **Temsili ad** — `<BULGULAR.json>`, `[X]`, `tez_<id>.md`. Köşeli
      parantezin İÇİNDEKİ yol bir taslaktır, dosya değil; ajanın dolduracağı
      bir girdidir ve depoda durmasının sebebi yoktur. `_DOSYA_DESEN` köşeli
      parantezi yakalamadığı için kontrol, eşleşmenin **çevresindeki
      karakterlere** bakılır. (Bu ilk yazımda kontrol yakalanan yolun
      kendisine bakıyordu ve `<BULGULAR.json>` içindeki 11 yeri yanlışlıkla
      gerçek çıktı sayıyordu.)
    * **Tez verisinin kendisi** — `thesis_state.json`, izlenmeyen kullanıcı
      verisi; `thesis:new` üretir.

    Bir çıktı ağacı vaat eden akış (`01_Giris.md`, `methodology_state.json`,
    `Kaynarca.bib`) köşeli parantez kullanmaz, bu yüzden yakalanmaya devam eder.
    """
    hayalet: list[str] = []
    for ad, metin in akislar.items():
        for eslesme in _DOSYA_DESEN.finditer(metin):
            yol = eslesme.group(1)
            cevre = metin[eslesme.start() - 1:eslesme.end() + 1]
            if _TEMSILI.search(cevre) or yol == "thesis_state.json":
                continue
            adaylar = [REPO_ROOT / yol]
            if "/" not in yol:
                adaylar += [REPO_ROOT / d / yol for d in _KOK_DIZINLER]
            if not any(a.exists() for a in adaylar):
                hayalet.append(f"{ad}: {yol}")
    assert not hayalet, (
        "Akışlar CLI'nin üretmediği dosyaları vaat ediyor:\n  "
        + "\n  ".join(sorted(set(hayalet)))
        + "\n  export.py:537 tek çıktıyı üretir: tez_<thesis_id>.{md,docx,pdf}"
    )


# --- 4. kapi zinciri tek yerde okunabiliyor mu -------------------------------


def test_ana_akis_yedi_kapiyi_sirasiyla_belgiler() -> None:
    """Ajan akışı tek yerden öğrenebilmeli: kapı adları + sıra."""
    from tools.atw.state import APPROVAL_GATES

    assert ANA_AKIS.exists(), f"{ANA_AKIS} yok — SKILL.md §7 listeliyor"
    metin = ANA_AKIS.read_text(encoding="utf-8")

    konumlar: list[int] = []
    for kapi in APPROVAL_GATES:
        i = metin.find(f"`{kapi}`")
        assert i != -1, (
            f"thesis_creation.md '{kapi}' kapısını anmıyor. Ajan yedi kapılı "
            f"akışın sırasını buradan öğrenemez."
        )
        konumlar.append(i)

    assert konumlar == sorted(konumlar), (
        "Kapılar yanlış sırada listelenmiş. Akış sırası şu: "
        + " -> ".join(APPROVAL_GATES)
    )
