"""Skill paketi hangi modeli ilan ediyor — ve o model gerçek mi?

Neden bu test
-------------
`.opencode/skill/academic-thesis-writer/` dizini otomatik kesifle
yukleniyor. Bu dizinin ne OLDUGU konusunda skill.yaml'da iki birbiriyle
celisan iddia vardi:

  * satır 86-89 (dogru): "tools[].file yollari DEPO KOKUNE gore cozumlenir,
    skill dizinine gore degil (skill dizininde tools/ klasoru yoktur)"
  * satır 18 (YANLIŞ): "Bu kopya KASITLIDIR: skill dizini kendi basina
    tasinabilir olmalidir"

Ikinci iddia dogrulanabilir degildi. On komutun handler'i
`python -m tools.atw.cli …`; dort hook'un komutu
`python .opencode/skill/…/hooks/x.py`. Yani skill dizini TEK BIR komut
calistiramaz — `tools/` dizini onda yok. Buna rağmen "tasinabilir" yaziyordu.
Bunun sonucu: skill, `~/.agents/skills/` altina aynalandiginda metadatasi
yukleniyor ama hicbir komutu calistiramayan bir kopya olusuyor.

Bu testler iki is yapiyor:

  1. Gercek modeli skill.yaml'da VERI olarak ilan ediyorlar (`runtime:`
     blogu). Boylece yazi bir iddia degil, denetlenebilir bir sozlesme olur.
  2. Ilan edilen modelin diskte DEGER gerceklestigini dogruluyorlar.

Ayrica, yanlis cozum olan "4 dizini skill dizinine kopyala" secenegini
kapatan bir kural var (test 6): skill dizini icerik agaci DEGILDIR.
Kopyalama yapilsaydi iki kaynak ortaya cikardi ve kayma korumasi olmazdi —
ayni tuzak daha once agents/ icin yasandi.

Kayma notu
----------
`agents/` kopyasi KASITLIDIR ve `test_plan1_integrity.py` her iki kopyanin
byte-ozdes oldugunu zorlar. Burada o test tekrarlanmaz; bu dosya farkli
soruya bakar: paketin ne olmadigini (calistirilabilir) zorlar.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / ".opencode" / "skill" / "academic-thesis-writer"
SKILL_YAML = SKILL_DIR / "skill.yaml"

# handler: "python -m tools.atw.cli new {args[0]} {args[1]}"
_MODUL_DESEN = re.compile(r"-m\s+([\w.]+)")
# command: "python .opencode/skill/…/hooks/thesis-init.py"
_SCRIPT_DESEN = re.compile(r"^python\s+([\w./-]+\.py)")
# Bir dosya yolu gibi gorunen sey.
_YOL_DESEN = re.compile(
    r"(?<![\w/.-])((?:[\w-]+/)*[\w-]+\.(?:json|md|bib|docx|pdf|yaml|yml|py))(?![\w-])"
)
# Temsili ad: <BULGULAR.json>, [X], tez_<id>.md
_TEMSILI = re.compile(r"[\[\]<>{}]")

# SKILL.md'nin atiflarinin cozumlendigi iki kok. `agents/` skill dizininde
# (skill'in okudugu yer); geri kalan her sey depo kokunde.
_SKILL_KOKU = {"agents"}


def _skill() -> dict:
    return yaml.safe_load(SKILL_YAML.read_text(encoding="utf-8"))


# --- 1. model ilan edilmis mi ------------------------------------------------


def test_calistirma_modeli_ilan_edilmis() -> None:
    """skill.yaml calistirma modelini `runtime:` blogu olarak VERI tasimali.

    Yoksa model yalnizca bir yorum satiri olarak kalir ve denetlenemez.
    Yanlis iddianin yorum olarak yazilmasi, bu blogu yazmaya zorlandi.
    """
    assert "runtime" in _skill(), (
        "skill.yaml'da `runtime:` blogu yok. Calistirma modeli veri olarak "
        "ilan edilmedigi icin denetlenemiyor: iki satir uyusmuyor — 18 "
        "skill dizininin tasinabilir oldugunu, 86-89 ise olmadigini yaziyor."
    )


def test_calistirma_modeli_depo_kokunu_ilan_ediyor() -> None:
    """`execution_root` degeri diskte gercekten ne oldugunu gostermeli."""
    assert _skill()["runtime"]["execution_root"] == "repo", (
        "execution_root 'repo' degil. Deger degistiyse bu testi degil, "
        "TAHMINI degil, modeli yeniden yaz: skill dizininde tools/ yok, "
        "dolayisiyla baska bir kok mumkun degil."
    )


# --- 2. ilan edilen model gercek mi -----------------------------------------


def test_komut_handler_leri_depo_kokundeki_modulu_caagirir() -> None:
    """Her handler'in `python -m X` hedefi depo kökünde var olmalı."""
    eksikler = []
    for komut in _skill()["commands"]:
        eslesme = _MODUL_DESEN.search(komut["handler"])
        assert eslesme, f"{komut['name']}: handler'da `python -m` yok -> {komut['handler']}"
        modul = eslesme.group(1)
        parcalar = modul.split(".")
        giris = REPO_ROOT.joinpath(*parcalar) / "__main__.py"
        if not giris.is_file():
            eksikler.append(f"{komut['name']}: {modul} -> {giris}")
    assert not eksikler, "depo kökünde karşılığı olmayan komutlar:\n  " + "\n  ".join(eksikler)


def test_skill_dizini_hicbir_komutu_calistiramaz() -> None:
    """Skill dizininde `tools/` OLMAMALI — modelin tersini kanıtlar.

    `execution_root: repo` ancak skill dizininde calistirilabilir kod
    bulunmadigi surece dogrudur. `tools/` bir gun skill dizinine
    tasinirsa bu test kirmiziya doner: o zaman ya model degismis ya da
    iki calistirma yolu olusmustur. Ikisi de sessizce gecilmemeli.
    """
    assert not (SKILL_DIR / "tools").exists(), (
        "skill dizininde tools/ var. execution_root: repo iddiasi ancak "
        "skill dizini calistirilabilir kod ICERMEDIGI surece dogrudur. "
        "Modeli degistiriyorsan ikinci kaynak yaratma."
    )


@pytest.mark.parametrize("hook", _skill()["hooks"], ids=lambda h: h["name"])
def test_hook_betigi_depo_kokunden_cozuluyor(hook: dict) -> None:
    """Hook betiği REPO_ROOT altında olmalı (skill.yaml:113-134 yolları)."""
    eslesme = _SCRIPT_DESEN.match(hook["command"])
    assert eslesme, f"{hook['name']}: `python <yol>` bicimi degil -> {hook['command']}"
    yol = REPO_ROOT / eslesme.group(1)
    assert yol.is_file(), f"{hook['name']}: betik yok -> {yol}"


# --- 3. SKILL.md'nin atiflari cozuluyor mu -----------------------------------


def test_skill_md_yollari_cozuluyor() -> None:
    """SKILL.md'nin atıf yaptığı HER dosya gerçekten var olmalı.

    Kullanıcının karşılaştığı asıl boşluk bu: SKILL.md §7 `workflows/…`
    diyor, §10 `templates/…` diyor, ama ajan skill dizininden okuduğu
    için bu yollar orada yok. Bu test, yolların iki kokten birinde
    çözüldüğünü zorlar.
    """
    metin = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    kopuler = [m.group(1) for m in _YOL_DESEN.finditer(metin)
               if not _TEMSILI.search(metin[max(0, m.start() - 1):m.end() + 1])]
    assert kopuler, "SKILL.md hiç dosya yolu anmıyor — desen bozulmuş olabilir"

    cozulmeyen = []
    for yol in sorted(set(kopuler)):
        kokler = [SKILL_DIR] if yol.split("/")[0] in _SKILL_KOKU else [REPO_ROOT]
        if not any((kok / yol).exists() for kok in kokler):
            cozulmeyen.append(yol)
    assert not cozulmeyen, (
        "SKILL.md cozulemeyen yol aniyor:\n  " + "\n  ".join(cozulmeyen)
        + "\n  `agents/` skill dizininden, diger her sey depo kokunden cozulur."
    )


# --- 4. ikinci kaynak riski -------------------------------------------------


@pytest.mark.parametrize("ad", ["references", "workflows", "templates", "schemas"])
def test_skill_dizini_icerik_agaci_tasimiyor(ad: str) -> None:
    """Skill dizini `references/ workflows/ templates/ schemas/` TAŞIMAMALI.

    Bu, yanlis cozumun kapisi. Skill dizinine bu dort dizini kopyalamak
    belgeleri cozulebilir kilar — ama komutlar yine calismaz (tools/ yok)
    ve iki kaynak ortaya cikar. Ayni tuzak `agents/` icin daha once
    yasandi: kopya senkrondan dustu ve iki ayri ajan kumesi belirdi.
    """
    assert not (SKILL_DIR / ad).exists(), (
        f"skill dizininde {ad}/ var. Bu ikinci bir kaynak: skill dizini "
        f"icerik agaci tasimaz, yalnizca SKILL.md + skill.yaml + agents/ + "
        f"hooks/ tutar. Kopyalama yapacaksan kayma korumasi da ekle."
    )


# --- 5. geri alinan iddia geri gelmemeli -------------------------------------


def test_tasinabilirlik_iddiasi_kaldirilmis() -> None:
    """Retract edilen cümle geri gelmemeli.

    Dar ve savunmasiz bir test (yorum satiri denetliyor) ama tam da
    geri aldigimiz seyi sabitler. Model artik `runtime:` bloguyla
    denetleniyor; bu test yalniz o blogun yazilma sebebini korur.
    """
    ham = SKILL_YAML.read_text(encoding="utf-8").lower()
    assert "taşınabilir" not in ham and "tasinabilir" not in ham, (
        "skill.yaml yine 'taşınabilir' diyor. Bu iddia yanlıştı: komutlar "
        "`python -m tools.atw.cli`, skill dizininde tools/ yok. Gerçek model "
        "`runtime: execution_root: repo` bloğudur."
    )
