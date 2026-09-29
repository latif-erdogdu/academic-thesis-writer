"""Sizma engelleri: skill paketi disina kacis vektorleri.

Bu test dosyasi, skill paketinin DISINA cikmaya yonelik vektorleri
sabitler. Amac "saldirgan kodu calistirmak" degil; paketin ilan ettigi
sozlesmenin (test_skill_yaml_contracts.py, test_skill_paketi_sozlesmesi.py)
DISINA cikan bir yol tanimina izin verilmedigini denetlemektir:

  1. SHELL INJECTION — komut handler'lari `python -m tools.atw.cli <alt>`
     kalibinda olmalidir. Handler'da `;`, `&&`, `|` gibi metakarakterler
     bulunursa, kullanici girdisi (`{args[0]}` vb.) bir kabuk komutuna
     donuse bilir. Yer tutucular yalnizca `{...}` biciminde olabilir.

  2. PATH TRAVERSAL — commands[], hooks[], agents[], tools[],
     references[] icindeki tum dosya yollari, cozuldukleri kokun
     DISINA cikamaz:
       * agents[].file    -> SKILL_DIR altinda kalmali
       * tools[].file     -> REPO_ROOT altinda kalmali
       * references[]     -> REPO_ROOT/references altinda kalmali
       * hooks[].command  -> betik yolu REPO_ROOT altinda kalmali
     `../` iceren veya mutlak dize olan bir yol, kokun disina isaret
     eder ve reddedilmelidir.

  3. IKKINCI KAYNAK YASAGI — `.claude/` ikizi yalnizca SKILL.md + agents/
     tasiyabilir. Icerik agaci (references/ workflows/ templates/ schemas/)
     kopyalanirsa, ikiz "calisiyor" gorunen ama sessizce baylayan ikinci
     bir kaynak olur. Bu, test_repo_butunlugu.py'deki byte-ozdeslik
     testlerini tamamlar: burada IZIN VERILEN kume denetlenir.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / ".opencode" / "skills" / "academic-thesis-writer"
SKILL_YAML = SKILL_DIR / "skill.yaml"
CLAUDE_IKIZ = REPO_ROOT / ".claude" / "skills" / "academic-thesis-writer"
CLAUDE_KOMUTLAR = REPO_ROOT / ".claude" / "commands"

# Kabuk metakarakterleri: bunlardan biri handler'da varsa, yer tutucu
# (kullanici girdisi) bir kabuk komutuna donuse bilir. Kelime taramasi
# yapilmaz: `--format` gibi meşru bayrak adlari "format" kelimesini icerir
# ve bayrak ancak `;`/`&&`/`|` ayraciyla komuta donuse bilir — onlari
# zaten ilk alternatif yakalar. Yeni satir ayrac degildir: komut
# dosyalari (.md) dogal olarak cok satirlidir; her satir ayri bir
# talimattir, zincirleme bir kabuk komutu degil.
_SHELL_METAKARAKTER = re.compile(r"[;&|`]|\$\(|\$\{")

# Yol kaçış göstergeleri
_PARENT_KACIS = re.compile(r"(^|[\\/])\.\.[\\/]")
_MUTLAK_WIN = re.compile(r"^[A-Za-z]:[\\/]")
_MUTLAK_POSIX = re.compile(r"^/")


def _skill() -> dict:
    return yaml.safe_load(SKILL_YAML.read_text(encoding="utf-8"))


def _kayitli_yol(dizi: list[str]) -> list[str]:
    """skill.yaml altindan gelen dosya yolu dizisini dogrulanabilir yapar."""
    return dizi


# --- 1) shell injection ------------------------------------------------------

def test_komut_handlerlarinda_shell_metakarakteri_yok() -> None:
    """Hiçbir commands[].handler kabuk metakarakteri tasimamali.

    Handler kalibi: `python -m tools.atw.cli <alt_komut> {yer_tutucu}*`.
    `;`, `&&`, `|`, backtick, `$(...)` gibi metakarakterler handler'da
    bulunursa, kullanici girdisi `{...}` yer tutucusuyla birlestiginde
    kabuk komutuna donuse bilir. Yer tutucular kendi basina guvenlidir:
    onlari CLI argumani olarak isleyen model/harness onlari yorumlar.
    """
    for komut in _skill()["commands"]:
        handler = komut["handler"]
        eslesme = _SHELL_METAKARAKTER.search(handler)
        assert eslesme is None, (
            f"{komut['name']}: handler'da kabuk metakarakteri "
            f"{eslesme.group(0)!r} -> {handler!r}"
        )
        # Yer tutucular yalnizca {..} biciminde olabilir (args/options).
        for parca in handler.split():
            if "{" in parca or "}" in parca:
                assert re.fullmatch(r"\{[a-z0-9_.\[\]]+\}", parca), (
                    f"{komut['name']}: beklenmedik yer tutucu {parca!r}"
                )


def test_claude_komutlarinda_shell_metakarakteri_yok() -> None:
    """`.claude/commands/thesis-*.md` icerigi de ayni yasaga tabi.

    Bu dosyalar Claude Code'ta modelin CALISTIRDIGI talimatlardir. Govde
    `python -m tools.atw.cli <alt> $ARGUMENTS` kalibini cagirir; ayrica
    dogal dil metni tasir (Türkce noktali virgül vb.). Enjeksiyon riski
    yalnizca CLI cagirAN satirda tasinir — dogal dil metni komut degildir.
    Bu yuzden yalnizca `tools.atw.cli` iceren satirlar taranir.
    """
    for yol in sorted(CLAUDE_KOMUTLAR.glob("thesis-*.md")):
        for satir_no, satir in enumerate(yol.read_text(encoding="utf-8").splitlines(), 1):
            if "tools.atw.cli" not in satir:
                continue
            # Markdown inline-code ayracini (`` ` ``) cikar: komut ornegi
            # backtick ile sarilidir, bu KABUK substitusyonu degildir.
            temiz = satir.replace("`", "")
            eslesme = _SHELL_METAKARAKTER.search(temiz)
            assert eslesme is None, (
                f"{yol.name}:{satir_no}: CLI satirinda kabuk metakarakteri "
                f"{eslesme.group(0)!r}"
            )


def test_hook_komutlarinda_shell_metakarakteri_yok() -> None:
    """hooks[].command de handler'lar gibi tehlikesiz olmali."""
    for hook in _skill()["hooks"]:
        komut = hook["command"]
        eslesme = _SHELL_METAKARAKTER.search(komut)
        assert eslesme is None, (
            f"{hook['name']}: komutta kabuk metakarakteri {eslesme.group(0)!r}"
        )


# --- 2) path traversal -------------------------------------------------------

def _disari_cikiyor(yol: str, kok: Path) -> bool:
    """Yol dizesi, verilen kokun disina isaret ediyor mu?"""
    if _PARENT_KACIS.search(yol):
        return True
    if _MUTLAK_WIN.match(yol) or _MUTLAK_POSIX.match(yol):
        return True
    # Cikis: gercek dosya sisteminde denetle (var olan yol icin).
    hedef = (kok / yol).resolve()
    return not hedef.is_relative_to(kok.resolve())


def test_agents_yollari_skill_dizini_disina_cikamaz() -> None:
    """agents[].file SKILL_DIR altinda kalmali; `..` veya mutlak olamaz."""
    for ajan in _skill()["agents"]:
        yol = ajan["file"]
        assert not _disari_cikiyor(yol, SKILL_DIR), (
            f"agent '{ajan['name']}': yol skill dizininden cikiyor -> {yol!r}"
        )
        hedef = (SKILL_DIR / yol).resolve()
        assert hedef.is_file(), f"agent '{ajan['name']}': dosya yok -> {hedef}"


def test_tools_yollari_repo_kokunden_cikamaz() -> None:
    """tools[].file REPO_ROOT altinda kalmali (repo_relative_roots)."""
    for arac in _skill()["tools"]:
        yol = arac["file"]
        assert not _disari_cikiyor(yol, REPO_ROOT), (
            f"tool '{arac['name']}': yol repo kokunden cikiyor -> {yol!r}"
        )
        assert (REPO_ROOT / yol).is_file(), f"tool '{arac['name']}': dosya yok"


def test_referans_yollari_references_dizini_disina_cikamaz() -> None:
    """references[] REPO_ROOT/references altinda kalmali."""
    for ad in _skill()["references"]:
        assert not _disari_cikiyor(ad, REPO_ROOT / "references"), (
            f"references[]: yol references/ disina cikiyor -> {ad!r}"
        )
        assert (REPO_ROOT / "references" / ad).is_file(), f"yok: {ad!r}"


def test_hook_betik_yollari_repo_kokunden_cikamaz() -> None:
    """hooks[].command icindeki betik yolu REPO_ROOT altinda kalmali.

    Bu test, `python .opencode/skills/.../hooks/x.py` kalibini denetler;
    `python -m tools.atw.cli ...` bicimi ayri yasa (modul adi) tasimaz.
    """
    for hook in _skill()["hooks"]:
        komut = hook["command"]
        betik = re.match(r"python\s+(?P<yol>[\w./\\-]+\.py)", komut)
        if not betik:
            continue
        yol = betik.group("yol")
        assert not _disari_cikiyor(yol, REPO_ROOT), (
            f"hook '{hook['name']}': betik yolu repo kokunden cikiyor -> {yol!r}"
        )
        assert (REPO_ROOT / yol).is_file(), f"hook '{hook['name']}': betik yok"


# --- 3) ikinci kaynak yasagi ------------------------------------------------

def test_claude_ikizi_iznli_kumede_kalir() -> None:
    """`.claude/skills/<id>/` YALNIZCA SKILL.md + agents/ tasiyabilir.

    skill.yaml (komut/hook tanimlari) ve icerik agaci bu ikizde OLAMAZ:
    o durumda ikiz "calisiyor" gorunen ama kod tasimayan ikinci bir kaynak
    olur. Claude Code, SKILL.md'den agent tanimlarini okur; komutlar
    depo kokunden calisir (execution_root: repo sozlesmesi).
    """
    # Relative path: rglob altinda ajan dosyalari agents/ onekiyle gelir.
    dosyalar = sorted(p.relative_to(CLAUDE_IKIZ).as_posix() for p in CLAUDE_IKIZ.rglob("*") if p.is_file())
    aganlar = sorted(p.name for p in (CLAUDE_IKIZ / "agents").glob("*.md"))
    izinli = {"SKILL.md"} | {f"agents/{ad}" for ad in aganlar}
    disaridakiler = sorted(set(dosyalar) - izinli)
    assert not disaridakiler, (
        f"`.claude` ikizi izinli kumenin disinda dosya tasiyor: {disaridakiler}"
    )
    assert len(dosyalar) == 1 + len(aganlar), (
        f"beklenmeyen dosya sayisi: {sorted(dosyalar)}"
    )


def test_claude_komutlari_skill_komutlariyle_cakismaz() -> None:
    """`.claude/commands` yalnizca thesis-* adli dosyalar tasimali.

    Yabancı bir komut dosyasi (.claude/commands/ altina disaridan
    eklenen) bu paketin sözlesmesi degildir ve sessizce cakisma olusturur.
    """
    yabanci = [
        p.name for p in sorted(CLAUDE_KOMUTLAR.glob("*.md"))
        if not p.name.startswith("thesis-")
    ]
    assert not yabanci, f"yabanci komut dosyasi: {yabanci}"


def test_skill_dizini_yapisal_izinler() -> None:
    """skill dizini yalnizca tanimli dort ogeyi tasiyabilir.

    Bu, test_skill_paketi_sozlesmesi.py icindeki `skill_dir_contents`
    kuralinin sizma tarafi: kural DISARIDA bir dosya (ornegin tools/
    kopyasi, ikinci bir skill.yaml) skill dizinine girerse, test
    yakalamadan kopyaniyorsa sessizce iki kaynak olusur.
    """
    izinli_ust = {"SKILL.md", "skill.yaml", "agents", "hooks"}
    ust_ogeler = {p.name for p in SKILL_DIR.iterdir()}
    fazlalik = ust_ogeler - izinli_ust
    assert not fazlalik, (
        f"skill dizininde tanimsiz oge: {sorted(fazlalik)}. "
        "skill_dir_contents (skill.yaml:33-37) disinda bir sey "
        "duruyorsa ikinci kaynak riski var."
    )