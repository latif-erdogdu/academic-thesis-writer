"""`scripts/install_skill.ps1` ne yapmali — ve ne yapmamali?

Problem
-------
Bu depoda skill'in iki farkli yukleme yolu var:

  1. `.opencode/skills/academic-thesis-writer` otomatik kesifle gelir
     (bu depoda calisirken); ikiz kopya `.claude/skills/academic-thesis-writer`
     hem Claude Code hem OpenCode project-compatibility kaynagidir.
  2. `~/.agents/skills/academic-thesis-writer/`
     (Agent Skills standart dizini — OpenCode compatibility; Claude Code
     ise `~/.claude/skills/` okur, bu yuzden betik hedefi secilebilir)

(2) yolu daha once ad-hoc `robocopy /MIR` ile bir kez aynalandi. Iki
sonuc oldu:

  * Kurulu kopya 4 adet `__pycache__/*.pyc` tasidi — hook'lar bir kez
    calistiginda uretilen derleme artiklari. Metodatada degil, pisdir.
  * Kopya SKILL.md'nin `workflows/…`, `references/…`, `templates/…`,
    `schemas/…` atiflarini iceriyordu ama o dosyalar yoktu; ve hicbir
    komut calistiramiyordu, cunku `tools/` skill dizininde degil.

Yani kopya "calisir" gibi gorunuyordu. `runtime.execution_root: repo`
(bkz. test_skill_paketi_sozlesmesi.py) bu modelin yalnizca
DEPOLARDA gecerli oldugunu ilan ediyor; aynalama betigi de ayni
seyi soylemeli.

Bu testler betigin sozlesmesini sabitler: kaynagi skill dizinidir,
derleme artiklarini tasimaz, ve kullanicya kopyanin ne olup ne
olmadigini soyler. Kurulumun tekrarlanabilir olmasi buradan gelir;
robocopy ile ad-hoc aynalamada degil.

Tasarim karari: betik `runtime.execution_root` degerini skill.yaml'dan
OKUR ve uyarida o degeri kullanir. Boylece uyari ilan edilen modelle
celisemez — ikisi ayni kaynaktan gelir.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / ".opencode" / "skills" / "academic-thesis-writer"
SKILL_YAML = SKILL_DIR / "skill.yaml"
SCRIPT = REPO_ROOT / "scripts" / "install_skill.ps1"

# Windows PowerShell 5.1 yolu. Linux/CI'da yoksa testler atlanir.
POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")

pytestmark = pytest.mark.skipif(
    POWERSHELL is None, reason="PowerShell yok; kurulum betigi Windows'a ozgudur"
)


def _skill() -> dict:
    return yaml.safe_load(SKILL_YAML.read_text(encoding="utf-8"))


def _calistir(*args: str) -> str:
    """Betigi calistirip stdout+stderr dondurur (hata ciktisi da onemli)."""
    sonuc = subprocess.run(
        [POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    assert sonuc.returncode == 0, (
        f"betik hata ile bitti (k={sonuc.returncode})\n"
        f"--- stdout ---\n{sonuc.stdout}\n--- stderr ---\n{sonuc.stderr}"
    )
    return sonuc.stdout + sonuc.stderr


# --- betigin varligi ve kaynagi ---------------------------------------------


def test_kurulum_betigi_diskte_var() -> None:
    """Aynalama betigi repoda olmali; ad-hoc robocopy bir cozum degil."""
    assert SCRIPT.is_file(), f"bulunamadi: {SCRIPT}"


def test_betik_skill_dizininden_kopyalar() -> None:
    """Kaynak depo koku DEGIL, skill dizini olmali.

    Depo kokunden kopyalamak `references/ workflows/ templates/ schemas/
    tools/`'u de gotururdi — yani ikinci kaynak. runtime blogu tam da
    bunu yasakliyor; betik ayni yere bakmali.
    """
    ham = SCRIPT.read_text(encoding="utf-8")
    # skill dizini yolu gorunmeli.
    assert ".opencode" in ham and "skill" in ham, (
        "betik skill dizinini isaret etmiyor; kaynak belirsiz"
    )
    # icerik agacini kopyalayan bir yol olmamali.
    for ad in _skill()["runtime"]["repo_relative_roots"]:
        if ad in ("agents/", "hooks/"):
            continue
        assert ad not in ham, (
            f"betik `{ad}` yolunu aniyor. Bu depo-goklu bir agac; skill "
            f"paketi onu tasimaz. Icerik agaci kopyalamak ikinci kaynak olusturur."
        )


# --- derleme artiklari ------------------------------------------------------


def test_betik_derleme_artiklarini_disarida_birakir() -> None:
    """`__pycache__` / `*.pyc` KOPYALANMAMALI.

    Gercek gozlem: robocopy ile aynalanan kurulu kopyada 4 adet .pyc
    vardi. Hook'lar bir kez calistiklar mi uretiliyor. Metadatada degil,
    pisdir; ve skill'in hangi surumde calistigini yaniltir.
    """
    ham = SCRIPT.read_text(encoding="utf-8").lower()
    assert "__pycache__" in ham, "betik __pycache__'i dislamiyor"
    assert ".pyc" in ham, "betik .pyc dosyalarini dislamiyor"


# --- kuru calistirma: neyin kopyalanacagini gosterir -----------------------


def test_kuru_calistirma_hedef_dizini_degistirmez() -> None:
    """-DryRun hicbir sey yazmamali, yalnizca listelemeli."""
    cikti = _calistir("-DryRun")
    assert "DryRun" in cikti or "dry" in cikti.lower(), (
        f"-DryRun ciktisi ne yapacagini belirtmiyor:\n{cikti}"
    )


# --- uyari: kopya ne olup ne OLMAZ ---------------------------------------


def test_betik_kopya_nedir_neyse_degildir_der() -> None:
    """Uyari, skill.yaml'daki `execution_root` degerini YANLINTMAMALI.

    Betik degeri skill.yaml'dan okur. Bu test o degerin gercekten
    aktarildigini dogrular; boylece uyari ile ilan edilen model
    celisemez.
    """
    kok = _skill()["runtime"]["execution_root"]
    cikti = _calistir("-DryRun")
    assert kok in cikti, (
        f"uyari `execution_root` degerini ({kok!r}) icermiyor. Betik degeri "
        f"skill.yaml'dan okumuyorsa uyari ile ilan edilen model celisir.\n"
        f"--- cikti ---\n{cikti}"
    )


def test_betik_metadata_only_oldugunu_soyler() -> None:
    """Uyari, kopyanin YALNIZCA metadata oldugunu acikca belirtmeli.

    Yoksa kullanici SKILL.md'yi okuyup `workflows/…` dosyalarini arar
    ve bulamayinca ya da komutlari calistirip hata alinca dogru yorumlayamaz.
    """
    cikti = _calistir("-DryRun").lower()
    # Turkce veya Ingilizce olabilir; ikisinden biri yeter.
    anlatim = ("metadata" in cikti) or ("metadatas" in cikti) or ("yalnizca" in cikti)
    assert anlatim, (
        f"uyari kopyanin metadata-only oldugunu soylemiyor:\n{cikti}"
    )


def test_betik_icerik_agacini_listelemez() -> None:
    """Kuru calistirma, icerik agaci dosyalarini ONERMEMELI.

    Yanlis cozum olan "4 dizini pakete kopyala" seceneginin kuru
    calistirmada gorunmesi, iki kaynak riskinin kazara girmezligini
    gosterirdi.
    """
    cikti = _calistir("-DryRun")
    for ad in _skill()["runtime"]["repo_relative_roots"]:
        if ad in ("agents/", "hooks/"):
            continue
        assert ad not in cikti, f"kuru calistirma `{ad}` oneriyor -> ikinci kaynak riski"


# --- betigin okunabilirligi ------------------------------------------------


def test_betik_neyi_yaptigini_belgeliyor() -> None:
    """Kurulum betigi yorum satiri icermeli: neyi, nereye, neden."""
    ham = SCRIPT.read_text(encoding="utf-8")
    yorumlar = [l for l in ham.splitlines() if l.strip().startswith("#")]
    assert len(yorumlar) >= 5, (
        "betigin basinda amacini anlatan yorum yok. Kurulum betigi "
        "belgeye ihtiyac duyar: tez calistirilabilirligi buradan degil, "
        "depodan gelir."
    )
    # Yanlis: hedefin ne olmadigini soylemeyen betik.
    assert re.search(r"depo|repo", "\n".join(yorumlar), re.IGNORECASE), (
        "betik yorumlari calistirma kokunu (depo) anmiyor"
    )
