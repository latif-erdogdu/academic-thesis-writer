"""Hook betiklerinin yol cozumlemesi ve durustlugu.

Bu dosya iki sinif hatayi kapatir.

1) YOL COZUMLEME HATASI — dort hook'un tamaminda `parents[3]` kullaniliyordu.
   Betikler `.opencode/skill/academic-thesis-writer/hooks/` altinda, yani
   deger zinciri 4 derinlikte:

       parents[0] = hooks
       parents[1] = academic-thesis-writer
       parents[2] = skill
       parents[3] = .opencode      <- hesaplanan (YANLIS)
       parents[4] = <depo koku>    <- olmasi gereken

   Sonuc: nispi bir dosya yolu `.opencode/` altinda aranir, bulunamaz ve
   hook "Dosya yok" deyip 0 donerek SESSIZCE hicbir sey yapmadan cikar.
   thesis-init icin daha kotu: REPO_ROOT hem sys.path hem de varsayilan
   thesis_state.json konumu olarak kullanildigi icin tez durumu
   `.opencode/thesis_state.json` altina yazilirdi.

   Ayni sey `tools/atw/cli/main.py:15` icin dogru (orada derinlik 3), yani
   idiom kopyalanirken derinlik degistirilmis.

2) UYDURMA MENSE — auto_verify.py, HICBIR ag cagrisi yapmadan
   `verification_sources: ["crossref", "openalex"]` yaziyordu. Kodun kendi
   yorumu bile bunu itiraf ediyordu: "# Simdilik placeholder". `status` deger
   `pending` oldugu icin durusttu, ama kaynak dizisi kalici bir yalandi:
   kaydi okuyan biri "Crossref ve OpenAlex sorgulandi" sanir.

   Buradaki kural: hook, SORGULAMADIGI bir kaynagi asla yazmaz. Liste
   dogrulayicinin gercekte yanit alan veritabanlarindan gelir.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / ".opencode" / "skill" / "academic-thesis-writer" / "hooks"

HOOK_ADLARI = ["auto_verify", "evidence_gate", "writing_gate", "thesis-init"]


def _yukle(ad: str):
    """hooks/ altindaki betigi dosya adindan (tireli) modul adiyla yukler."""
    yol = HOOKS_DIR / f"{ad}.py"
    spec = importlib.util.spec_from_file_location(f"hook_{ad.replace('-', '_')}", yol)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _kaynak_kaydi(**ek) -> dict:
    """Gecerli bir source kaydi; verification alani varsayilan olarak bos."""
    kayit = {
        "id": "SRC-001",
        "title": "Ornek makale",
        "authors": ["Erdogdu, L."],
        "year": 2026,
        "journal": "Ornek Dergi",
        "verification": {
            "status": "pending",
            "bibliographic_match": 0.0,
            "verified_at": "",
            "verification_sources": [],
        },
    }
    kayit.update(ek)
    return kayit


class _SahteSonuc:
    """tools.source_verify.verify.VerificationResult taklidi."""

    def __init__(self, status="verified", match=0.93,
                 sources=("crossref", "openalex"), verified_at="2026-09-27T10:00:00Z"):
        self.source_id = "SRC-001"
        self.status = status
        self.bibliographic_match = match
        self.verified_at = verified_at
        self.verification_sources = list(sources)
        self.verification_details = {}
        self.retraction_info = []
        self.correction_info = None


class _SahteDogrulayici:
    """SourceVerifier taklidi; hangi kaydin soruldugunu kaydeder."""

    gorulen: list = []
    sonuc = None
    hata: Exception | None = None

    def __init__(self, *args, **kwargs):
        pass

    def verify_source(self, kayit: dict):
        type(self).gorulen.append(kayit)
        if type(self).hata is not None:
            raise type(self).hata
        return type(self).sonuc


@pytest.fixture
def sahte_dogrulayici(monkeypatch):
    """auto_verify'in SourceVerifier'ini sahte ile degistirir (ag cagrisi yok).

    Dondurulen deger auto_verify modulu; cagri kaydi `_SahteDogrulayici`
    uzerinden okunur.
    """
    modul = _yukle("auto_verify")
    _SahteDogrulayici.gorulen = []
    _SahteDogrulayici.sonuc = _SahteSonuc()
    _SahteDogrulayici.hata = None
    if not hasattr(modul, "SourceVerifier"):
        pytest.skip("auto_verify henuz SourceVerifier kullanmiyor")
    monkeypatch.setattr(modul, "SourceVerifier", _SahteDogrulayici)
    return modul


# --- 1) yol cozumlemesi -----------------------------------------------------

@pytest.mark.parametrize("ad", HOOK_ADLARI)
def test_hook_repo_kokunu_cozumluyor(ad: str):
    """Her hook depo kokunu BIR MODUL SEVIYESI sabiti olarak cozumlemeli.

    Neden modul seviyesinde: deger hem sys.path'e hem de tez durumu
    konumuna giriyor, bu yuzden test edilebilir olmali. Ice fonksiyon
    icinde kalsaydi yalnizca dolarli (dosya olusturup silme) bir testle
    denetlenebilirdi.

    Guvenlik gerekce: `parents[3]` `.opencode`ye isaret eder, depo kokune
    degil. Yanlis kademe, nispi yollarin `.opencode/` altinda aranmasina
    ve hook'un sessizce 0 donmesine yol acar; `thesis_state.json` da
    `.opencode/` altina yazilir.
    """
    modul = _yukle(ad)
    assert hasattr(modul, "REPO_ROOT"), (
        f"{ad} modul seviyesinde REPO_ROOT tanimlamiyor; "
        f"cozumleme ic fonksiyona gomulu, test edilemiyor"
    )
    assert modul.REPO_ROOT == REPO_ROOT, (
        f"{ad}: REPO_ROOT yanlis: {modul.REPO_ROOT} (olmasi gereken {REPO_ROOT})"
    )
    assert modul.REPO_ROOT.name != ".opencode", (
        f"{ad}: REPO_ROOT .opencode'ye isaret ediyor"
    )


@pytest.mark.parametrize("ad", HOOK_ADLARI)
def test_hook_repo_koku_depo_koku_gibidir(ad: str):
    """Cozumlenen kok gercekten depo koku olmali (schemas/ ve tools/ var)."""
    kok = _yukle(ad).REPO_ROOT
    assert (kok / "schemas").is_dir(), f"{ad}: schemas/ bulunamadi: {kok}"
    assert (kok / "tools").is_dir(), f"{ad}: tools/ bulunamadi: {kok}"


def test_nispi_yol_depo_kokuna_gore_cozumlenir(tmp_path, monkeypatch, capsys):
    """evidence_gate nispi yolu `.opencode/` altinda ARAMAMALI.

    Behavior testi: nispi bir dosya adi verilir, hook dosyayi bulup
    okumalidir. Bulamazsa "Dosya yok" yazip 0 doner — sessizgecer.
    """
    modul = _yukle("evidence_gate")
    probe = REPO_ROOT / "_hook_probe_bolum.md"
    assert not probe.exists(), "probe dosyasi zaten var"
    probe.write_text("# Gecici bolum\n\nCLM-001 metni.\n", encoding="utf-8")
    try:
        modul.main(probe.name)
        cikti = capsys.readouterr().out
        assert "Dosya yok" not in cikti, (
            f"nispi yol cozumlenmedi; hook '{probe.name}' dosyasini bulamadi. "
            f"Cikti: {cikti.strip()!r} — repo_root yanlis kademede"
        )
    finally:
        probe.unlink(missing_ok=True)


def test_mutlak_yol_calismaya_devam_eder(tmp_path, capsys):
    """Mutlak yol her zaman calismali (parents derinliginden bagimsiz)."""
    modul = _yukle("writing_gate")
    atif = tmp_path / "CIT-001.json"
    atif.write_text(json.dumps({"id": "CIT-001", "source_id": "SRC-001"}), encoding="utf-8")
    modul.main(str(atif))
    cikti = capsys.readouterr().out
    assert "Dosya yok" not in cikti, f"mutlak yol bulunamadi: {cikti.strip()!r}"


# --- 2) writing_gate capraz referans kontrolü ------------------------------
#
# writing_gate.py:46 `parents[3] / "thesis_state.json"` yaziyordu; bu
# `.opencode/thesis_state.json`a isaret eder ve HIC VAR OLMADIGI icin
# `if ... .exists()` her zaman False donuyor, capraz referans kontrolu
# SESSIZCE ATLANIYORDU. Sonuc: tezde olmayan `SRC-999` gibi uydurma bir
# source_id tasiyan atif Writing Gate'i gecmekteydi. Uydurma mense sinifinin
# aynisi: kayit dogrulanmadigi halde dogrulanmis sayiliyor.

def _atik_kaydi(source_id: str = "SRC-001", **ek) -> dict:
    """writing_gate'in bekledigi en az citation kaydi."""
    kayit = {
        "id": "CIT-001",
        "source_id": source_id,
        "paragraph_id": "P-001",
        "style": "apa7",
    }
    kayit.update(ek)
    return kayit


def _tez_durumu(tmp_path: Path, *source_idler: str) -> None:
    """tmp_path altinda writing_gate'in okuyacagi thesis_state.json yazar."""
    durum = {
        "thesis": {"id": "THESIS-2026-001", "title": "Test"},
        "sources": [{"id": s} for s in source_idler],
    }
    (tmp_path / "thesis_state.json").write_text(
        json.dumps(durum), encoding="utf-8"
    )


def test_writing_gate_bilinmeyen_kaynak_kimligini_reddeder(tmp_path, monkeypatch, capsys):
    """Tezde olmayan source_id'li atif reddedilmeli."""
    modul = _yukle("writing_gate")
    monkeypatch.setattr(modul, "REPO_ROOT", tmp_path)
    _tez_durumu(tmp_path, "SRC-001", "SRC-002")

    atif = tmp_path / "CIT-001.json"
    atif.write_text(json.dumps(_atik_kaydi("SRC-999")), encoding="utf-8")

    assert modul.main(str(atif)) == 1, (
        "tezde olmayan source_id kabul edildi; capraz referans kontrolu "
        "calismiyor (thesis_state.json yanlis yolda araniyor olabilir)"
    )
    assert "thesis_state" in capsys.readouterr().out


def test_writing_gate_bilinen_kaynak_kimligini_kabul_eder(tmp_path, monkeypatch, capsys):
    """Tezde OLAN source_id'li atif gecmeli (kontrol yanlis pozitif vermemeli)."""
    modul = _yukle("writing_gate")
    monkeypatch.setattr(modul, "REPO_ROOT", tmp_path)
    _tez_durumu(tmp_path, "SRC-001", "SRC-002")

    atif = tmp_path / "CIT-002.json"
    atif.write_text(json.dumps(_atik_kaydi("SRC-002")), encoding="utf-8")

    assert modul.main(str(atif)) == 0
    cikti = capsys.readouterr().out
    assert "geçti" in cikti, f"gecmesi bekleniyordu: {cikti.strip()!r}"
    assert "thesis_state" not in cikti, (
        f"bilinen source_id reddedildi: {cikti.strip()!r}"
    )


def test_tez_durumu_yoksa_capraz_kontrol_atlanir(tmp_path, monkeypatch, capsys):
    """thesis_state.json yoksa kontrol atlanmali (mevcut davranis, kasitli).

    Atlanma durumu ayri bir karardir: tez durumu olmadan hangi kaynak
    gecerli bilinemedigi icin reddetmek de yaniltici olurdu.
    """
    modul = _yukle("writing_gate")
    monkeypatch.setattr(modul, "REPO_ROOT", tmp_path)

    atif = tmp_path / "CIT-003.json"
    atif.write_text(json.dumps(_atik_kaydi("SRC-999")), encoding="utf-8")

    assert modul.main(str(atif)) == 0
    assert "thesis_state" not in capsys.readouterr().out


# --- 3) BOM'lu JSON ---------------------------------------------------------

def test_bomlu_json_reddedilmemeli(tmp_path):
    """UTF-8 BOM'lu JSON gecerli JSON'dur; reddedilmemeli.

    PowerShell `Set-Content -Encoding UTF8`, Notepad ve Excel bu formati
    uretir. Windows'u hedefleyen bir arac bunu reddetmemeli.
    Onceki hata: "Gecersiz JSON: Unexpected UTF-8 BOM".
    """
    modul = _yukle("auto_verify")
    kaynak = tmp_path / "SRC-001.json"
    kaynak.write_text(json.dumps(_kaynak_kaydi()), encoding="utf-8-sig")
    assert modul.main(str(kaynak)) == 0, "BOM'lu JSON reddedildi"


def test_bomsuz_json_bozulmamali(tmp_path):
    """BOM duzeltmesi BOM'suz dosyalari da bozmamali."""
    modul = _yukle("auto_verify")
    kaynak = tmp_path / "SRC-002.json"
    kaynak.write_text(json.dumps(_kaynak_kaydi()), encoding="utf-8")
    assert modul.main(str(kaynak)) == 0


def test_bozuk_json_hala_reddedilmeli(tmp_path, capsys):
    """BOM duzeltmesi gercek bozuk JSON'u kabul etmemeli."""
    modul = _yukle("auto_verify")
    kaynak = tmp_path / "SRC-003.json"
    kaynak.write_text("{bozuk", encoding="utf-8")
    assert modul.main(str(kaynak)) == 1
    # Hook'un gercek mesaji Turkce karakterle yaziliyor ("Geçersiz JSON").
    assert "JSON" in capsys.readouterr().out


# --- 4) uydurma mense -------------------------------------------------------

def test_dogrulanmayan_kayit_hicbir_kaynak_yazmaz(tmp_path, sahte_dogrulayici):
    """DOI yoksa hicbir kaynak YAZILMAMALI.

    Once `["manual"]` yaziyordu. "manual" enum'da "elle dogrulandi" demek;
    kimse dogrulamadigi halde yazmak, sorgulanmamis bir kaynak bildirmektir.
    Dogrulanmadiysa liste bos olmali.
    """
    kaynak = tmp_path / "SRC-004.json"
    kaynak.write_text(json.dumps(_kaynak_kaydi()), encoding="utf-8")
    sahte_dogrulayici.main(str(kaynak))

    veri = json.loads(kaynak.read_text(encoding="utf-8"))
    assert veri["verification"]["verification_sources"] == [], (
        f"DOI yokken kaynak yazildi: {veri['verification']['verification_sources']}"
    )
    assert _SahteDogrulayici.gorulen == [], "DOI yokken dogrulayici cagrildi"


def test_verification_alani_yoksa_bos_liste(tmp_path, sahte_dogrulayici):
    """verification alani yoksa da hicbir kaynak yazilmamali."""
    kaynak = tmp_path / "SRC-005.json"
    kayit = _kaynak_kaydi()
    del kayit["verification"]
    kaynak.write_text(json.dumps(kayit), encoding="utf-8")
    sahte_dogrulayici.main(str(kaynak))

    veri = json.loads(kaynak.read_text(encoding="utf-8"))
    assert veri["verification"]["verification_sources"] == []
    assert veri["verification"]["status"] == "pending"


def test_dogrulayiciya_kayit_gecer(sahte_dogrulayici, tmp_path):
    """DOI varsa dogrulayici gercekten cagrilmali (placeholder degil)."""
    kaynak = tmp_path / "SRC-006.json"
    kaynak.write_text(json.dumps(_kaynak_kaydi(doi="10.1234/abc")), encoding="utf-8")
    sahte_dogrulayici.main(str(kaynak))

    assert len(_SahteDogrulayici.gorulen) == 1, "dogrulayici cagrilmadi"
    assert _SahteDogrulayici.gorulen[0]["doi"] == "10.1234/abc"


def test_sonuc_dosyaya_yazilir(sahte_dogrulayici, tmp_path):
    """Dogrulayicinin sonucu kayda gecmeli: status, skor, zaman, kaynaklar."""
    kaynak = tmp_path / "SRC-007.json"
    kaynak.write_text(json.dumps(_kaynak_kaydi(doi="10.1234/abc")), encoding="utf-8")
    sahte_dogrulayici.main(str(kaynak))

    dogrulama = json.loads(kaynak.read_text(encoding="utf-8"))["verification"]
    assert dogrulama["status"] == "verified"
    assert dogrulama["bibliographic_match"] == pytest.approx(0.93)
    assert dogrulama["verified_at"] == "2026-09-27T10:00:00Z"


def test_yalnizca_sorgulanan_kaynaklar_yazilir(sahte_dogrulayici, tmp_path):
    """EN ONEMLI TEST: listede yalnizca GERCEKTEN yanit alanlar olmali.

    Onceki kod `["crossref", "openalex"]` yaziyordu. Simdi yalnizca Crossref
    yanit veriyorsa dosyada da yalnizca Crossref gorunmeli.
    """
    _SahteDogrulayici.sonuc = _SahteSonuc(sources=("crossref",))
    kaynak = tmp_path / "SRC-008.json"
    kaynak.write_text(json.dumps(_kaynak_kaydi(doi="10.1234/abc")), encoding="utf-8")
    sahte_dogrulayici.main(str(kaynak))

    dogrulama = json.loads(kaynak.read_text(encoding="utf-8"))["verification"]
    assert dogrulama["verification_sources"] == ["crossref"], (
        f"sorgulanmayan kaynak yazildi: {dogrulama['verification_sources']}"
    )


def test_hicbir_kaynak_yanit_vermezse_bos_liste(sahte_dogrulayici, tmp_path):
    """Tum veritabanlari hata verirse liste bos kalmali, sahte ad yazilmamali."""
    _SahteDogrulayici.sonuc = _SahteSonuc(status="unverified", match=0.0, sources=())
    kaynak = tmp_path / "SRC-009.json"
    kaynak.write_text(json.dumps(_kaynak_kaydi(doi="10.1234/abc")), encoding="utf-8")
    sahte_dogrulayici.main(str(kaynak))

    dogrulama = json.loads(kaynak.read_text(encoding="utf-8"))["verification"]
    assert dogrulama["verification_sources"] == []
    assert dogrulama["status"] == "unverified"


def test_ag_hatasi_kaydi_bozmaz(sahte_dogrulayici, tmp_path):
    """Dogrulayici cokerse kayit bozulmamali; hicbir sey yazilip UYDURULMAMALI.

    Onceki kod burada bile `["crossref","openalex"]` yaziyordu.
    """
    _SahteDogrulayici.hata = RuntimeError("ag hatasi")
    kaynak = tmp_path / "SRC-010.json"
    kaynak.write_text(json.dumps(_kaynak_kaydi(doi="10.1234/abc")), encoding="utf-8")
    onceki = kaynak.read_text(encoding="utf-8")

    sonuc = sahte_dogrulayici.main(str(kaynak))

    assert sonuc != 0, "ag hatasinda basari donuldu"
    dogrulama = json.loads(kaynak.read_text(encoding="utf-8"))["verification"]
    assert dogrulama["verification_sources"] == [], (
        f"ag hatasi olmasina ragmen kaynak yazildi: {dogrulama['verification_sources']}"
    )
    assert kaynak.read_text(encoding="utf-8") == onceki, "kayit degistirildi"


def test_zaten_dogrulanmis_atlanir(sahte_dogrulayici, tmp_path):
    """status=verified ise yeniden dogrulanmamali."""
    kaynak = tmp_path / "SRC-011.json"
    kaynak.write_text(json.dumps(_kaynak_kaydi(doi="10.1234/abc", verification={
        "status": "verified",
        "bibliographic_match": 0.91,
        "verified_at": "2026-01-01T00:00:00Z",
        "verification_sources": ["crossref"],
    })), encoding="utf-8")
    assert sahte_dogrulayici.main(str(kaynak)) == 0
    assert _SahteDogrulayici.gorulen == [], "dogrulanmis kaynak tekrar dogrulandi"


def test_sema_uyumlu_calisma_zamani_dolu_yazilir(sahte_dogrulayici, tmp_path):
    """pending durumunda verified_at bos birakilmali (zaman olusmadi).

    Uretimde zaman damgasi olusturulur; testte sahte sonuc sabit.
    """
    kaynak = tmp_path / "SRC-012.json"
    kaynak.write_text(json.dumps(_kaynak_kaydi(doi="10.1234/abc")), encoding="utf-8")
    sahte_dogrulayici.main(str(kaynak))
    dogrulama = json.loads(kaynak.read_text(encoding="utf-8"))["verification"]
    assert dogrulama["verified_at"], "verified_at bos birakildi"
