"""P0-1 butunlugunun uctan uca dogrulamasi.

Bu test ayri bir varlik modeli kurmaz; yalnizca butunluk iliskilerini
denetler. Fonksiyonel testler Task 1-9'un kendi testlerindedir.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_COPY = REPO_ROOT / ".opencode" / "skills" / "academic-thesis-writer"
CLAUDE_COPY = REPO_ROOT / ".claude" / "skills" / "academic-thesis-writer"


def test_opencode_kopya_yeni_ajanlari_iceriyor():
    kopya_ajanlar = {p.stem for p in (SKILL_COPY / "agents").glob("*.md")}
    assert {"contradiction-analyzer", "integrity-auditor"} <= kopya_ajanlar


def test_opencode_kopya_agentleri_ayni():
    kopya_ajanlar = {p.stem for p in (SKILL_COPY / "agents").glob("*.md")}
    kok_ajanlar = {p.stem for p in (REPO_ROOT / "agents").glob("*.md")}
    assert kopya_ajanlar == kok_ajanlar, (
        f"Senkron degil. Kopya: {kopya_ajanlar}, kok: {kok_ajanlar}"
    )


def test_opencode_skill_kopyasi_kok_ile_ayni():
    kopya = (SKILL_COPY / "SKILL.md").read_text(encoding="utf-8")
    kok = (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert kopya == kok, "SKILL.md kopyasi guncel degil"


def test_claude_skill_kopyasi_kok_ile_ayni():
    """`.claude/skills/<id>/SKILL.md` Claude Code'un kesif yoludur.

    OpenCode ayni SKILL.md'i `.claude/skills` project-compatibility
    kaynagindan da okur. Bu ikiz, kok SKILL.md ile birebir ayni
    olmali; ayri bir metin kopyasi iki kaynagi zamanla ayirir.
    """
    kopya = (CLAUDE_COPY / "SKILL.md").read_text(encoding="utf-8")
    kok = (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert kopya == kok, "`.claude` SKILL.md kopyasi guncel degil"


def test_claude_kopya_agentleri_birebir_ayni():
    """`.claude` ikizindeki ajanlar kok agents/ ile byte-ozdes olmali."""
    kok_ajanlar = {p.stem for p in (REPO_ROOT / "agents").glob("*.md")}
    ikiz_ajanlar = {p.stem for p in (CLAUDE_COPY / "agents").glob("*.md")}
    assert ikiz_ajanlar == kok_ajanlar, (
        f"`.claude` ikizinde ajan seti farkli. Icinde: {ikiz_ajanlar}"
    )
    for yol in (REPO_ROOT / "agents").glob("*.md"):
        ikiz = CLAUDE_COPY / "agents" / yol.name
        assert ikiz.is_file(), f"`.claude` ikizinde eksik: {ikiz}"
        assert ikiz.read_text(encoding="utf-8") == yol.read_text(
            encoding="utf-8"
        ), yol.name


def test_claude_kopya_icerik_agaci_tasimiyor():
    """`.claude` ikizi de yalnizca SKILL.md + agents/ tutar.

    `references/ workflows/ templates/ schemas/` icerik agaci depo
    kokundedir (execution_root: repo). Iki kopyalarına yola cikmak,
    ikinci kaynak olusturur; ayni kural `.opencode` ikizi icin de
    gecerli (test_skill_paketi_sozlesmesi.py).
    """
    for ad in ("references", "workflows", "templates", "schemas", "tools"):
        assert not (CLAUDE_COPY / ad).exists(), (
            f"`.claude` ikizi icerik agaci tasiyor: {ad}/. Icerik agaci "
            "depo kokundedir; ikiz yalnizca SKILL.md + agents/ tutar."
        )


def test_ajan_dosyalari_kopya_ile_birebir_ayni():
    for yol in (REPO_ROOT / "agents").glob("*.md"):
        kopya = SKILL_COPY / "agents" / yol.name
        assert kopya.is_file(), f"Eksik kopya: {kopya}"
        assert kopya.read_text(encoding="utf-8") == yol.read_text(encoding="utf-8"), yol.name


def test_tum_temel_testler_gecer():
    """Alt kumedeki tum testler yesil olmali.

    `--ignore` zorunludur: bu dosya kendi kendini cagirirsa
    pytest bu testi yeniden toplar ve sonsuz ozyineleme olur.
    """
    sonuc = subprocess.run(
        [
            sys.executable, "-m", "pytest", "-q", "--tb=short",
            "-p", "no:cacheprovider",
            "--ignore", str(REPO_ROOT / "tests" / "integration_tests"),
        ],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert sonuc.returncode == 0, sonuc.stdout[-3000:]


def test_ozyeleme_yok():
    """Alt kumedeki toplam test sayisi sifirdan buyuk olmali.

    Yanlis bir `--ignore` veya `testpaths` degerinin alt kumedeki
    testleri tamamen gizlemesi sessizce "hepsi gecti" gibi
    gorunur. Bu denetim o durumu yakalar.

    Toplam iki yerden okunur. pytest 9 `-q --collect-only` ile
    toplam satiri degil dosya bazli sayilari bastigi icin
    (ornek: `tests/x.py: 21`) once onlar toplanir. Daha eski
    surumler toplam satiri bastiyorsa o kullanilir.
    """
    sonuc = subprocess.run(
        [
            sys.executable, "-m", "pytest", "-q", "--collect-only",
            "-p", "no:cacheprovider",
            "--ignore", str(REPO_ROOT / "tests" / "integration_tests"),
        ],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    dosya_bazli = 0
    toplam_satiri = 0
    for satir in sonuc.stdout.splitlines():
        dosya_bazli_sayim = re.search(r":\s*(\d+)\s*$", satir)
        if dosya_bazli_sayim is not None:
            dosya_bazli += int(dosya_bazli_sayim.group(1))
            continue
        if "tests collected" in satir or "test collected" in satir:
            toplam_satiri = int(satir.split()[0])
    sayi = max(dosya_bazli, toplam_satiri)
    assert sayi > 100, f"Alt kumede yalnizca {sayi} test toplandi, beklenen >100"


def test_gercek_ag_cagrisi_yapilmiyor():
    """P0-1 testleri ag bagimliliği olmadan calismalidir.

    Bu dosya kendi kaynak metninde `@pytest.mark.live` diye yazili
    oldugu icin, denetlenen dosya disarida tutulmazsa arama kendini
    bulur ve "live isaretli test var" yanlis sonucuna varir.
    """
    sonuc = subprocess.run(
        [
            sys.executable, "-m", "pytest", "-q", "--collect-only", "--tb=no",
            "-p", "no:cacheprovider",
        ],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    # `live` isaretli test varsa addopts'ta varsayilan olarak
    # dislandigini dogrula.
    if "@pytest.mark.live" in _kaynaktan_oku("tests"):
        assert "-m" in _pytest_ini_addopts() and "live" in _pytest_ini_addopts(), (
            "live isaretli testler var ama varsayilan olarak dislanmiyor"
        )
    assert sonuc.returncode == 0, sonuc.stdout[-2000:]


def _kaynaktan_oku(alt_dizin: str) -> str:
    """Alt dizindeki Python kaynaklarini birlestirir.

    Bu dosya haric: kendi kaynagindaki `live` isareti diye yaziyi
    denetleyecegi icin tarama kendini bulmamalidir.
    """
    parcalar = []
    kendi = Path(__file__).resolve()
    for yol in sorted((REPO_ROOT / alt_dizin).rglob("*.py")):
        if yol.resolve() == kendi:
            continue
        parcalar.append(yol.read_text(encoding="utf-8"))
    return "\n".join(parcalar)


def _pytest_ini_addopts() -> str:
    for satir in (REPO_ROOT / "pytest.ini").read_text(encoding="utf-8").splitlines():
        if satir.strip().startswith("addopts"):
            return satir
    return ""


def test_sema_dosyalari_json_ve_gecerli():
    for yol in sorted((REPO_ROOT / "schemas").glob("*.json")):
        try:
            json.loads(yol.read_text(encoding="utf-8"))
        except json.JSONDecodeError as hata:
            raise AssertionError(f"{yol.name} gecerli JSON degil: {hata}") from hata


def test_requirements_txt_asgari_dependenslari_iceriyor():
    metin = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8")
    for paket in ["jsonschema", "pytest"]:
        assert paket in metin, paket


def test_readme_mimarisini_anlatiyor():
    metin = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "jsonschema" in metin
    assert "pytest" in metin
    for ajan in ["contradiction-analyzer", "integrity-auditor"]:
        assert ajan in metin, ajan


SURUM_DESENI = re.compile(r"(?<![\w/.])v(?:ersion)?\s*[0-9]+(?!\w)", re.IGNORECASE)


def test_kok_belgelerde_surum_ibaresi_yok():
    """Kok SKILL.md ve ajan dosyalari surum soyutlamasi yasagina tabidir.

    Ust duzey belgeler surum adlariyla anmaz; aksi halde kendi
    kuralini ihlal ederdi. Yalnizca kuralin metni denetlenir, kod
    blogu icindeki desen degil -- desen zaten harf ve rakam olarak
    ayri yazildigi icin eslesmez.
    """
    hedefler = [REPO_ROOT / "SKILL.md", *sorted((REPO_ROOT / "agents").glob("*.md"))]
    for yol in hedefler:
        metin = yol.read_text(encoding="utf-8")
        eslesme = SURUM_DESENI.search(metin)
        assert (
            eslesme is None
        ), f"{yol.name} dokumaninda surum ibaresi: {eslesme.group(0)!r}"


def test_opencode_kopyasinda_surum_ibaresi_yok():
    """`.opencode` ve `.claude` senkron kopyalari da yasaga tabidir.

    Kopyalar ayri dosya agaclaridir; kok SKILL.md duzeltildiginde
    kopyalar geride kalabilir. Boyle bir kayma daha once gerceklesmis ve
    hicbir test yakalamamisti: `test_ajan_dosyasi_surum_ibaresi_yok`
    yalnizca `agents/` dizinine bakiyordu.
    """
    suclar = []
    for kopya in (SKILL_COPY, CLAUDE_COPY):
        for yol in sorted(kopya.rglob("*.md")):
            metin = yol.read_text(encoding="utf-8")
            m = SURUM_DESENI.search(metin)
            if m is not None:
                suclar.append(f"{yol.relative_to(REPO_ROOT)}: {m.group(0)!r}")
    assert not suclar, "Surum ibaresi: " + "; ".join(suclar)
