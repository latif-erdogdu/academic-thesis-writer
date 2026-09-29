"""Cift-platform skill sozlesmesi: OpenCode V2 + Claude Code.

Bu depo bir skill paketidir ve iki harness'in kesif yollarini ayni
anda saglamalıdır:

  OpenCode V2 (https://opencode.ai/v2/docs/skills/):
    - Skill yerlesimi: `.opencode/skills/<id>/SKILL.md`
    - Frontmatter: `name` + `description` (her ikisi de zorunlu)
    - ID, dizin adindan turetilir (`<src>/<id>/SKILL.md` -> id)
    - Project compatibility kaynaklari: `.claude/skills`, `.agents/skills`

  Claude Code (https://code.claude.com/docs/en/skills):
    - Skill yerlesimi: `.claude/skills/<name>/SKILL.md`
    - Frontmatter: `name` + `description`
    - Destekleyici dosyalar SKILL.md'nin yaninda yer alir

Neden bu test
-------------
Skill daha once YALNIZCA OpenCode V1-uyum dizinde duruyordu
(`.opencode/skill/<id>/`). V2 kesif yolu `.opencode/skills/<id>/`
ve Claude Code kesif yolu `.claude/skills/<name>/` kopya olarak
MEVCUT DEGİLDI — yani Claude Code bu skill'i hicbir dizinden
yukleyemiyordu. Bu test, her iki harness'in ilan ettigi kesif
yolunun diskte gercekten var oldugunu ve frontmatter'in her iki
semaya da uydugunu zorlar.

Ikiz kopyaların byte-ozdesligi burada tekrarlanmaz; o
`test_repo_butunlugu.py`deki isin (kok SKILL.md ↔ .opencode ↔ .claude).
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ID = "academic-thesis-writer"
OPCODE_SKILL = REPO_ROOT / ".opencode" / "skills" / SKILL_ID / "SKILL.md"
CLAUDE_SKILL = REPO_ROOT / ".claude" / "skills" / SKILL_ID / "SKILL.md"
CLAUDE_COMMANDS = REPO_ROOT / ".claude" / "commands"


def _frontmatter(yol: Path) -> dict:
    ham = yol.read_text(encoding="utf-8")
    # --- ile cevrili ilk YAML blogunu ayikla.
    bas = ham.index("---", 0) + 3
    son = ham.index("---", bas)
    return yaml.safe_load(ham[bas:son])


# --- OpenCode V2 ------------------------------------------------------------


def test_opencode_v2_kesif_yolu_var() -> None:
    """`.opencode/skills/<id>/SKILL.md` v2'nin ilan ettigi proje yolu."""
    assert OPCODE_SKILL.is_file(), (
        f"V2 kesif dosyasi yok: {OPCODE_SKILL}. OpenCode v2 skill'i "
        "`.opencode/skills/<id>/SKILL.md` altinda arar."
    )


def test_opencode_v2_frontmatter_name_ve_description_var() -> None:
    for alan in ("name", "description"):
        assert alan in _frontmatter(OPCODE_SKILL), (
            f"OpenCode v2 SKILL.md frontmatter'inda `{alan}` yok. V2 semasi "
            f"name + description ister."
        )


def test_opencode_v2_id_dizin_adiyla_uyumlu() -> None:
    """ID, `<dizin>/SKILL.md` yolunun dizin adindan turetilir."""
    fm = _frontmatter(OPCODE_SKILL)
    assert fm["name"] == SKILL_ID, (
        f"frontmatter name ({fm['name']!r}) dizin adiyla ({SKILL_ID!r}) "
        "uyusmuyor; ID cakismasi olur."
    )


# --- Claude Code ------------------------------------------------------------


def test_claude_code_kesif_yolu_var() -> None:
    """`.claude/skills/<name>/SKILL.md` Claude Code'un proje kesif yolu."""
    assert CLAUDE_SKILL.is_file(), (
        f"Claude Code kesif dosyasi yok: {CLAUDE_SKILL}. Claude Code skill'i "
        "`.claude/skills/<name>/SKILL.md` altinda arar (proje) ve "
        "`~/.claude/skills/` altinda (kisisel)."
    )


def test_claude_code_frontmatter_name_ve_description_var() -> None:
    for alan in ("name", "description"):
        assert alan in _frontmatter(CLAUDE_SKILL), (
            f"Claude Code SKILL.md frontmatter'inda `{alan}` yok."
        )


def test_claude_code_name_dizin_adiyla_uyumlu() -> None:
    fm = _frontmatter(CLAUDE_SKILL)
    assert fm["name"] == SKILL_ID, (
        f"frontmatter name ({fm['name']!r}) dizin adiyla ({SKILL_ID!r}) "
        "uyusmuyor; `/skill` cagrisi eslesmez."
    )


def test_claude_code_support_dosyalari_yaninda() -> None:
    """Claude Code destekleyici dosyalari SKILL.md'nin yaninda bekler.

    `agents/` ikizi bu dizinde durur (kok agents/ ile byte-ozdes,
    test_repo_butunlugu.py zorlar). Icerik agaci (references/ workflows/
    templates/ schemas/) burada OLMAMALI — o depo kokundedir.
    """
    ikiz = CLAUDE_SKILL.parent
    assert (ikiz / "agents").is_dir(), (
        f"`.claude/skills/{SKILL_ID}/agents/` yok. SKILL.md `agents/...` "
        "yollarini aniyor; destekleyici dosyalar skill dizininde olmali."
    )
    for ad in ("references", "workflows", "templates", "schemas"):
        assert not (ikiz / ad).exists(), (
            f"`.claude` ikizi icerik agaci tasiyor: {ad}/. Bu ikinci bir "
            "kaynak olur; icerik agaci depo kokundedir."
        )


# --- ortak: frontmatter GECERLI YAML olmali ---------------------------------


@pytest.mark.parametrize("yol", [OPCODE_SKILL, CLAUDE_SKILL], ids=["opencode", "claude"])
def test_frontmatter_gecerli_yaml(yol: Path) -> None:
    fm = _frontmatter(yol)
    assert isinstance(fm, dict) and fm, f"{yol}: frontmatter bos ya da YAML degil"


# --- Claude Code komutlari (.claude/commands/thesis-*.md) -------------------


def test_claude_komutlari_skill_yaml_ile_eslesir() -> None:
    """skill.yaml'daki 10 komut, `.claude/commands/thesis-*.md` icinde.

    OpenCode komutlari skill.yaml'dan okur; Claude Code ayri bir dizinden
    (`.claude/commands/`). Ayni 10 komutun her iki yerde de var olmasi,
    skill'in her iki harness'te ayni is akisini surebilecegini soyler.
    """
    yaml_yolu = REPO_ROOT / ".opencode" / "skills" / SKILL_ID / "skill.yaml"
    veri = yaml.safe_load(yaml_yolu.read_text(encoding="utf-8"))
    komutlar = veri["commands"]
    assert len(komutlar) == 10, f"skill.yaml komut sayisi degisti: {len(komutlar)}"

    for komut in komutlar:
        ad = komut["name"]  # "thesis:new"
        alt = ad.split(":")[1]  # "new"
        dosya = CLAUDE_COMMANDS / f"thesis-{alt}.md"
        assert dosya.is_file(), (
            f"skill.yaml '{ad}' icin `.claude/commands/thesis-{alt}.md` yok. "
            "Claude Code, komutlari `.claude/commands/` dizininden okur."
        )


def test_claude_komut_frontmatter_gecerli() -> None:
    """Her komut dosyasi: description zorunlu, argument-hint izinli."""
    dosyalar = sorted(CLAUDE_COMMANDS.glob("thesis-*.md"))
    assert len(dosyalar) == 10, f"Beklenen 10 komut dosyasi, var olan: {len(dosyalar)}"
    for yol in dosyalar:
        fm = _frontmatter(yol)
        assert "description" in fm, f"{yol.name}: description yok"
        assert isinstance(fm["description"], str) and fm["description"].strip()
        # argument-hint istege bagli ama varsa string olmali
        if "argument-hint" in fm:
            assert isinstance(fm["argument-hint"], str)


def test_claude_komut_gercek_alt_komutu_cagirir() -> None:
    """Gövde, uydurma degil gercek `tools.atw.cli <altkomut>` cagirisini icerir.

    Dosya adi thesis-<alt>.md ise govde `python -m tools.atw.cli <alt>`
    dizesini barindirmali. Boylece kosturan model gercek CLI'yi surer;
    skill.yaml handler'i ile ayni alt komutu cagirir.
    """
    for yol in sorted(CLAUDE_COMMANDS.glob("thesis-*.md")):
        alt = yol.stem.replace("thesis-", "")
        govde = yol.read_text(encoding="utf-8")
        desen = f"python -m tools.atw.cli {alt}"
        assert desen in govde, (
            f"{yol.name}: govde `{desen}` cagirisini icermiyor. Kopya ya da "
            "uydurma komut olabilir."
        )
        # `` geri-tik işaretli satırda da gorunmeli (calistirilabilir ornek)
        assert "```" in govde or f"`{desen}" in govde