"""`opencode.json` OpenCode'un ilan ettigi skills sekline uymali.

Neden bu test
-------------
`opencode.json` GITIGNORE'dadir (`.gitignore:12`) — yerel makine
yapilandirmasidir, reponun parcasi degildir. Bu yuzden bu testin asil
sozlesmesi repoda TUTULAN gercekler uzerine kuruludur:

  1. Skill, config kaydina gerek kalmadan `.opencode/skills/<id>/SKILL.md`
     altindan otomatik kesfedilir (V2 migration rehberi: "V2 discovers
     skills from both `.opencode/skill/` and `.opencode/skills/`.").
     Ayrica `.claude/skills` ve `.agents/skills` OpenCode'un project
     compatibility kaynaklaridir — ikiz kopyalar cakismaz, ayni ID
     ayni icerigi verir.
  2. `opencode.json` YEREL KOPYADA varsa, `skills` blogu (varsa) yayinlanan
     semaninkinden farkli bir bicimde olamaz.

Yayinlanan semada (opencode.ai/config.json) `skills` icin gecerli tek bicim
`{ \"paths\": [...], \"urls\": [...] }`'dur — `additionalProperties: false`.
Deneysel object-form kayit (`{ \"<id>\": { \"path\": ..., \"enabled\": ... } }`)
semaya aykiridir ve config uzerinden hicbir sey yukleyemez. Bu form daha once
yerel `opencode.json`'da vardi; kaldirildi cunku zaten islevsizdi: skill
kesif yoluyla geliyordu.

Dosya yoksa (taze klon) yapilandirma testleri atlanir; skill-kesif testi
her ortamda calisir. Test kitapliklari disk gercegini denetler, sav
uretmaz.

Kayma notu
----------
Kayit kaldirildiktan sonra iki contract testinin docstring'i `opencode.json:16`
yi yukleme mekanizmasi olarak aniyordu; dogru mekanizma otomatik kesiftir.
O docstringler bu teslerle ayni commit'te duzeltildi (yorum, sav yok).
`opencode.json` gitignore'da oldugundan config duzeltmesi commit'e girmez;
yalniz yerel calisma agacinda kalir.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
OPCODE_CONFIG = REPO_ROOT / "opencode.json"


def _config() -> dict:
    """Yerel config'i okur; dosya yoksa (taze klon) atlar.

    Dosya gitignore'da oldugundan bir klonda bulunmayabilir. Bu testin
    committed sozlesmesi o zaman yalniz kesif yoludur; config denetimi
    yalnizca dosya varken anlamlidir.
    """
    if not OPCODE_CONFIG.is_file():
        pytest.skip(
            "opencode.json yerel makine yapilandirmasidir (gitignore'da) "
            "ve bu kopyada yok; yalnizca varken denetlenir."
        )
    return json.loads(OPCODE_CONFIG.read_text(encoding="utf-8"))


def test_opencode_json_gecerli_json() -> None:
    """Config dosyasi JSON olarak cozulmeli (schema dogrulamasi bunun uzerine kurulur)."""
    assert isinstance(_config(), dict), f"{OPCODE_CONFIG} gecerli JSON degil"


def test_skills_blogu_sema_sekillerinden_birini_tasiyor() -> None:
    """`skills` anahtari varsa yalnizca yayinlanan semanin bicimleri gecerli.

    Semada `skills` icin tek gecerli yapi:
        { "paths": [...], "urls": [...] }   (additionalProperties: false)
    Object-form kayit (`{ "<id>": { "path": ..., "enabled": ... } }`) semaya
    aykiridir ve config uzerinden hicbir sey yukleyemez.
    """
    skills = _config().get("skills")
    if skills is None:
        return  # blok yok: kesif yolu gecerli, test 3 bunu dogrular
    gecersiz = set(skills) - {"paths", "urls"}
    assert not gecersiz, (
        "skills sema-disinda anahtarlar tasiyor: "
        + ", ".join(sorted(gecersiz))
        + ". Gecerli bicim yalniz { 'paths': [...], 'urls': [...] } - "
        "skill kaydi object-form olamaz; kesif yolu kullan."
    )
    for anahtar, deger in skills.items():
        assert isinstance(deger, list), f"skills.{anahtar} dizi olmali -> {type(deger).__name__}"
        assert all(isinstance(s, str) for s in deger), (
            f"skills.{anahtar} yalnizca dizge (yol/URL) icermeli"
        )


def test_skill_config_kaydina_gerek_kalmadan_kesfedilir() -> None:
    """`.opencode/skills/<id>/SKILL.md` var oldugu surece kayit gereksizdir.

    V2 migration rehberi hem `.opencode/skill/` (V1-uyum) hem
    `.opencode/skills/` (V2 tercih) altindaki skill'leri otomatik kesfeder.
    Repo yalnizca V2 yolunu tasir (`.opencode/skills/`); `.claude/skills`
    project-compatibility kaynagidir ve ikiz kopya ayni icerigi verir.
    Bu yuzden `opencode.json`'daki skills kaydi kaldirilabilir.
    """
    skill_md = REPO_ROOT / ".opencode" / "skills" / "academic-thesis-writer" / "SKILL.md"
    assert skill_md.is_file(), (
        f"kesif dosyasi yok: {skill_md}. Skill yalnizca config kaydina "
        "baglanmissa kayit kaldirilamaz."
    )