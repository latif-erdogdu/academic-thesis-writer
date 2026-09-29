"""skill.yaml sozlesmeleri — ilan edilen her sey gercekten cozumleniyor mu?

Bu dosya, skill.yaml'da ilan edilen komut, hook ve arac referanslarinin
var oldugunu ve belgelenen cagirmenin gercekten ayristirilabilir oldugunu
dogrular. Boyle bir test yoktu; sonucu 11 komutun 11'i de kirikti:

  * giris noktasi `python -m tools.atw.cli` idi, ama tools/atw/cli/
    altinda __main__.py yok -> HER komut "No module named" veriyordu
  * `new-thesis` diye bir alt komut yok (gercegi `new`)
  * `check-evidence`, `check-citations`, `verify-source` diye alt komutlar
    yok; gercek kapı mantigi .opencode/.../hooks/ altindaki betiklerde
  * konumsal argumanlar `--flag` biciminde yazilmis: `search --rq X`,
    `extract --source X`, `write --chapter X` — argparse bunlari reddeder
  * `verify --all {options.all}` : --all deger almayan bir bayrak, sonrasina
    deger gelince ayristirma hata verir
  * thesis-init hook'u `schemas/thesis_state.json` dosyasini kopyaliyordu;
    o dosya bir JSON SEMA, durum sablonu degil
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / ".opencode" / "skills" / "academic-thesis-writer"
SKILL_YAML = SKILL_DIR / "skill.yaml"
HOOKS_DIR = SKILL_DIR / "hooks"

# argparse ayristiricisinda doldurulacak sahte deger.
SAHTE = "X"


def _skill() -> dict:
    return yaml.safe_load(SKILL_YAML.read_text(encoding="utf-8"))


def _alt_parser(parser: argparse.ArgumentParser, ad: str):
    """Verilen adi kayitli alt komutun parser'ini dondurur, yoksa None."""
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action.choices.get(ad)
    return None


def _argv_dene(handler: str) -> list[str] | None:
    """Handler'dan sahte bir argv kurar; CLI bicimi degilse None doner.

    Dondurulen argv, belgelenen cagirmanin gercekten ayristirilip
    ayristirilamadigini test etmek icin argparse'a verilir.

    Iki incelik:
      * `--all` gibi deger almayan bayraklarin arkasindaki deger tuketilmez
        (yer tutucu atilir).
      * `--type` gibi `choices` kisitli seceneklerin arkasina gelen yer
        tutucu, GECERLI bir degerle degistirilir. Aksi halde test, dogru
        yazilmis bir handler'i hata diye raporlardi.
    """
    parcalar = shlex.split(handler, posix=False)
    if not parcalar or parcalar[0] != "python" or "-m" not in parcalar:
        return None
    modul_idx = parcalar.index("-m")
    if modul_idx + 1 >= len(parcalar) or modul_idx + 2 >= len(parcalar):
        return None

    alt_parser = _alt_parser(_build_parser(), parcalar[modul_idx + 2])
    if alt_parser is None:
        return None  # alt komut yok; bunu baska test bildiriyor

    # secenek adi -> (deger alir mi, gecerli degerler)
    secenekler: dict[str, tuple[bool, list]] = {}
    for action in alt_parser._actions:
        for ad in action.option_strings:
            secenekler[ad] = (action.nargs != 0, list(action.choices or []))

    argv: list[str] = []
    deger_isteyen: str | None = None
    onceki_deger_almayan_bayrak = False
    for parca in parcalar[modul_idx + 2:]:
        if parca.startswith("{") and parca.endswith("}"):
            # Yalnizca deger ALMAYAN bir bayragin ardindaki yer tutucu tuketilmez.
            # Konumsal slotlardaki yer tutucu yerine gecerli bir deger konur.
            if onceki_deger_almayan_bayrak:
                onceki_deger_almayan_bayrak = False
                continue
            kisitli = secenekler[deger_isteyen][1] if deger_isteyen else []
            argv.append(kisitli[0] if kisitli else SAHTE)
            deger_isteyen = None
            continue
        parca = parca.strip('"')
        argv.append(parca)
        bilgi = secenekler.get(parca)
        deger_isteyen = parca if (bilgi and bilgi[0]) else None
        onceki_deger_almayan_bayrak = bool(bilgi) and not bilgi[0]
    return argv


def _build_parser() -> argparse.ArgumentParser:
    from tools.atw.cli.main import build_parser

    return build_parser()


# --- giris noktasi ----------------------------------------------------------

def test_giris_noktasi_paket_olarak_calisiyor():
    """`python -m tools.atw.cli` hata vermemeli.

    skill.yaml'daki HER komut bu bicimi kullaniyor.
    """
    sonuc = subprocess.run(
        [sys.executable, "-m", "tools.atw.cli", "--help"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert sonuc.returncode == 0, sonuc.stderr
    assert "thesis" in sonuc.stdout.lower() or "new" in sonuc.stdout


def test_parser_fabrikasi_disa_aktarilmis():
    """main() bir parser fabrikasi sunmali; sozlesme testi bunu kullanir."""
    assert _alt_parser(_build_parser(), "status") is not None


# --- commands ---------------------------------------------------------------

@pytest.mark.parametrize("komut", _skill()["commands"], ids=lambda k: k["name"])
def test_komut_handler_i_gercek_alt_komut(komut: dict):
    """commands[].handler'daki alt komut CLI'da gercekten kayitli olmali."""
    eslesme = re.match(
        r"python\s+-m\s+(?P<modul>[\w.]+)\s+(?P<alt_komut>[\w-]+)", komut["handler"]
    )
    assert eslesme, f"{komut['name']}: handler bicimi taninmiyor -> {komut['handler']}"

    modul = eslesme.group("modul")
    alt_komut = eslesme.group("alt_komut")
    assert _alt_parser(_build_parser(), alt_komut) is not None, (
        f"{komut['name']}: '{alt_komut}' diye bir alt komut yok."
    )
    # Giris noktasi da dogru olmali: paket olarak -m ile calisabilmeli.
    assert modul == "tools.atw.cli", (
        f"{komut['name']}: modul '{modul}' — tools/atw/cli/__main__.py yoksa "
        f"'python -m {modul}' calismaz."
    )


@pytest.mark.parametrize("komut", _skill()["commands"], ids=lambda k: k["name"])
def test_komut_handler_i_argumanlari_ayristirilabilir(komut: dict):
    """Belgelenen handler, sahte degerlerle argparse'tan gecmelidir.

    Bu test konumsal/ bayrak karisimini yakalar: `search --rq X` gibi bir
    yazim, `rq` konumsal tanimlandigi icin ayristirmada hata verir.
    """
    argv = _argv_dene(komut["handler"])
    if argv is None:
        pytest.skip("bu handler argparse biciminde degil")

    alt_komut = argv[0]
    alt_parser = _alt_parser(_build_parser(), alt_komut)
    assert alt_parser is not None, f"{komut['name']}: '{alt_komut}' alt komutu yok"

    try:
        ayristirilmis = alt_parser.parse_args(argv[1:])
    except SystemExit:
        pytest.fail(
            f"{komut['name']}: belgelenen cagirma ayristirilamiyor.\n"
            f"  handler : {komut['handler']}\n"
            f"  denenen : {alt_komut} {' '.join(argv[1:])}\n"
            f"  CLI'de bu komutun bekledigi: konumsal="
            f"{[a.dest for a in alt_parser._actions if not a.option_strings]}, "
            f"bayrak={sorted(alt_parser._option_string_actions)}"
        )
    assert ayristirilmis is not None


# --- tools ------------------------------------------------------------------

@pytest.mark.parametrize("arac", _skill()["tools"], ids=lambda k: k["name"])
def test_arac_dosyasi_diskte_var(arac: dict):
    """tools[].file isaret ettigi dosya gercekten var olmali.

    Bu yollar REPO KOKUNE gore cozumlenir; skill dizininin altinda
    tools/ klasoru yoktur. Arac kodlari CLI ile paylasilan, depo kokunde
    durur.
    """
    yol = REPO_ROOT / arac["file"]
    assert yol.is_file(), f"{arac['name']}: dosya yok -> {yol}"


@pytest.mark.parametrize("arac", _skill()["tools"], ids=lambda k: k["name"])
def test_arac_modulu_ice_aktarilabilir(arac: dict):
    """tools[].name gercek bir Python modulu olmali (bos arac olmasin)."""
    try:
        __import__(f"tools.{arac['name']}")
    except ImportError as hata:
        pytest.fail(f"{arac['name']}: modul ice aktarilamiyor -> {hata}")


# --- agents -----------------------------------------------------------------

@pytest.mark.parametrize("ajan", _skill()["agents"], ids=lambda k: k["name"])
def test_ajanin_arsaclari_tanimli_araclardan(ajan: dict):
    """agents[].tools yalnizca tools: altinda tanimli araclari icermeli."""
    tanimli = {arac["name"] for arac in _skill()["tools"]}
    bilinmeyen = set(ajan.get("tools", [])) - tanimli
    assert not bilinmeyen, f"{ajan['name']}: tanimsiz arac -> {sorted(bilinmeyen)}"


@pytest.mark.parametrize("ajan", _skill()["agents"], ids=lambda k: k["name"])
def test_ajan_dosyasi_diskte_var(ajan: dict):
    """agents[].file isaret ettigi dosya var olmali.

    Bu yol SKILL_DIR'e gore cozumlenir: ajan .md'leri skill dizininde
    tutulur. Depo kokundeki agents/ kopyasi vardir ve
    test_repo_butunlugu.py her ikisinin birebir ayni oldugunu ve
    senkron kaldigini denetler; buradaki asil olan skill'in okudugu
    yolun var olmasi.
    """
    yol = SKILL_DIR / ajan["file"]
    assert yol.is_file(), f"{ajan['name']}: dosya yok -> {yol}"


# --- references --------------------------------------------------------------

def test_referans_listesi_diskte_var():
    """references[] altindaki her dosya gercekten var olmali.

    Bu blok HICBIR test tarafindan denetlenmiyordu: 7 dosya adi yaziliydi,
    hicbiri kontrol edilmiyordu. Yollari references/ altinda, depo kokunden
    cozumlenir (SKILL.md:339-345 ayni sekilde yaziyor).
    """
    adlar = _skill()["references"]
    assert adlar, "references listesi bos"
    eksikler = [ad for ad in adlar if not (REPO_ROOT / "references" / ad).is_file()]
    assert not eksikler, f"diskte olmayan referans: {eksikler}"


def test_referans_listesi_klasordeki_her_dosyayi_kapsiyor():
    """references[] tam olmali: diskteki her referans listede olmali.

    Ters yon: yeni bir referans dosyasi eklendiginde listeye girmezse
    skill onu yukleyemez, ama hicbir test de uyarmaz.
    """
    adlar = set(_skill()["references"])
    diskte = {p.name for p in (REPO_ROOT / "references").glob("*.md")}
    assert not (diskte - adlar), f"diskte var ama listede yok: {sorted(diskte - adlar)}"


def test_writer_ajani_gercekten_yazabiliyor():
    """writer ajaninin tek araci citation_check; bu gercekten calismali.

    Gecmise donuk: citation_check hic kod icermiyordu, yani writer ajani
    hicbir sey yazamiyordu.
    """
    from tools.citation_check import audit_citations

    assert callable(audit_citations)


# --- hooks ------------------------------------------------------------------

def _betigi_yukle(ad: str):
    """hooks/ altindaki betigi dosya adindan (tireli) modul adiyla yukler."""
    yol = HOOKS_DIR / f"{ad}.py"
    spec = importlib.util.spec_from_file_location(f"hook_{ad.replace('-', '_')}", yol)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


@pytest.mark.parametrize("hook", _skill()["hooks"], ids=lambda k: k["name"])
def test_hook_komutunun_hedefi_var(hook: dict):
    """hooks[].command gercek bir betigi veya modulu cagirabilmeli."""
    komut = hook["command"]
    betik = re.match(r"python\s+(?P<yol>[\w./\\-]+\.py)", komut)
    if betik:
        yol = REPO_ROOT / betik.group("yol")
        assert yol.is_file(), f"{hook['name']}: betik yok -> {yol}"
        return

    eslesme = re.match(
        r"python\s+-m\s+(?P<modul>[\w.]+)(?:\s+(?P<alt_komut>[\w-]+))?", komut
    )
    if eslesme:
        alt_komut = eslesme.group("alt_komut")
        if alt_komut is None:
            return
        assert _alt_parser(_build_parser(), alt_komut) is not None, (
            f"{hook['name']}: '{alt_komut}' diye bir alt komut yok."
        )
        return

    # Diger bicimler (cp, mkdir, ...) icin belirtilen yollar denetlenir.
    for yol_metni in re.findall(r"[\w./\\-]+\.(?:json|md|py|yaml)", komut):
        assert (REPO_ROOT / yol_metni).exists(), f"{hook['name']}: yol yok -> {yol_metni}"


def test_hook_semayi_durum_sablonu_olarak_kullanmaz():
    """schemas/thesis_state.json bir SEMA; hook onu durum olarak kopyalamamali."""
    sema = json.loads(
        (REPO_ROOT / "schemas" / "thesis_state.json").read_text(encoding="utf-8")
    )
    assert "$schema" in sema, "bu dosya sema degil, testin varsayimi bozuk"

    kopyalayan = [
        hook["name"]
        for hook in _skill()["hooks"]
        if "schemas/thesis_state.json" in hook["command"]
    ]
    assert not kopyalayan, (
        f"sema, durum sablonu olarak kopyalaniyor: {kopyalayan}. "
        f"Bunun yerine empty_state() kullanilmali."
    )


# --- thesis-init hook'unun davranisi ----------------------------------------

def test_thesis_init_hook_gecerli_durum_ure_tir(tmp_path):
    """thesis-init hook'u sema degil, dogrulanabilir bir durum uretmeli.

    Regresyon: hook, schemas/thesis_state.json dosyasini kopyaliyordu.
    Uretilen dosya $id/properties/required iceriyordu; 7 onay kapisinin
    hicbiri yoktu.
    """
    modul = _betigi_yukle("thesis-init")

    hedef = tmp_path / "thesis_state.json"
    assert modul.main(hedef) == 0
    assert hedef.is_file()

    durum = json.loads(hedef.read_text(encoding="utf-8"))
    assert "$schema" not in durum, "uretilen dosya sema kopyasi"
    assert durum["sources"] == [] and durum["citations"] == []
    assert durum["schema_version"] == "1.0"

    from tools.atw.state import APPROVAL_GATES

    assert sorted(durum["human_approvals"]) == sorted(APPROVAL_GATES)

    sema = json.loads(
        (REPO_ROOT / "schemas" / "thesis_state.json").read_text(encoding="utf-8")
    )
    jsonschema.Draft202012Validator(sema).validate(durum)


def test_thesis_init_hook_mevcut_dosyaya_ezmez(tmp_path):
    """Hook, var olan thesis_state.json dosyasini ezmemeli."""
    modul = _betigi_yukle("thesis-init")

    hedef = tmp_path / "thesis_state.json"
    hedef.write_text('{"thesis_id": "VAR"}', encoding="utf-8")
    assert modul.main(hedef) == 0
    assert json.loads(hedef.read_text(encoding="utf-8"))["thesis_id"] == "VAR"


def test_thesis_init_hook_yazamazsa_hata_dondurur(tmp_path):
    """Hook, durumu yazamazsa acikca hata donmeli; sessizce gecmemeli.

    Once bu test, `schemas/thesis_state.json` sablonunun bulunamasi
    durumunu denetliyordu. Hook artik sablon kopyalamaz (empty_state()
    uretir), dolayisiyla o hata yolu yok oldu; niyet korunur: hook
    basarisiz olursa bunu belli etmeli.
    """
    modul = _betigi_yukle("thesis-init")

    engel = tmp_path / "engel"
    engel.write_text("bu bir dosya, dizin degil", encoding="utf-8")

    # Engel dosyasinin ALTINA yazmak mumkun degil.
    assert modul.main(engel / "thesis_state.json") == 1


# --- evidence / writing gate davranisi --------------------------------------

def test_evidence_gate_claim_yoksa_reddeder(tmp_path):
    """Iddia referansi icermeyen bolum yazim kapisindan gecmemeli."""
    modul = _betigi_yukle("evidence_gate")

    bolum = tmp_path / "thesis_chapter_01.md"
    bolum.write_text("Bu bolumde hicbir CLM referansi yoktur.\n", encoding="utf-8")
    assert modul.main(str(bolum)) == 1


def test_evidence_gate_kanitsiz_claim_reddeder(tmp_path):
    """Iddia var ama kanit/kaynak yoksa da reddedilmeli."""
    modul = _betigi_yukle("evidence_gate")

    bolum = tmp_path / "thesis_chapter_01.md"
    bolum.write_text("B mindfulness CLM-001 etkili.\n", encoding="utf-8")
    assert modul.main(str(bolum)) == 1


def test_evidence_gate_tam_kabul_eder(tmp_path):
    """Iddia + kanit + kaynak birlikteyse kapidan gecmeli."""
    modul = _betigi_yukle("evidence_gate")

    bolum = tmp_path / "thesis_chapter_01.md"
    bolum.write_text("CLM-001 iddiası EVD-001 ve SRC-001 ile desteklenir.\n", encoding="utf-8")
    assert modul.main(str(bolum)) == 0


def test_writing_gate_eksik_alan_reddeder(tmp_path):
    """citation.json'da zorunlu alan yoksa yazim kapisi reddetmeli."""
    modul = _betigi_yukle("writing_gate")

    atif = tmp_path / "citation_001.json"
    atif.write_text(json.dumps({"id": "CIT-001"}), encoding="utf-8")
    assert modul.main(str(atif)) == 1


def test_writing_gecit_butunlugu_bozuk_atif_reddeder(tmp_path):
    """ Bozuk JSON da reddedilmeli. """
    modul = _betigi_yukle("writing_gate")

    atif = tmp_path / "citation_001.json"
    atif.write_text("{bozuk", encoding="utf-8")
    assert modul.main(str(atif)) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
