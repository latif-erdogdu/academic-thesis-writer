"""`thesis:approve` — kapıları açan komutun var olduğu ve gerçekten açtığı.

Neden bu test
-------------
`tools/atw/approval.py` `onay_ver` / `onay_geri_al` uygular ve 7 kapının
adını bilir; `cmd_status` kapıları GÖSTERİR. Ama `tools/atw/cli/main.py`
hiçbir yerde onay vermiyordu. `human_approvals` yalnızca `empty_state()`
tarafından `False` olarak üretiliyordu.

Sonuç: akışın kilitlendiği nokta. Kapı hiçbir komutla açılamadığı için
`cmd_write` ve `cmd_export` hiçbir koşulda ilerleyemiyordu; `thesis:new`,
`search`, `status` dışında kullanılabilir komut kalmıyordu. Yani 7 kapılı
PRISMA akışı, kapıları açan bir araca sahip değildi.

Bu testler kapağı şu üç davranışa bağlar:

  1. Hazırlığı olmayan kapı açılmaz (`GATE_HAZIRLIK` boş dönerse reddet).
  2. Akış atlanamaz (`onay_ver`'in sıra denetimi CLI'dan da geçerli).
  3. Onay geri alınınca ona dayanan kapılar da kapanır.
"""
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from tools.atw.cli import main as cli
from tools.atw.state import empty_state


@pytest.fixture
def depo(tmp_path, monkeypatch):
    (tmp_path / "schemas").mkdir()
    for sema in Path("schemas").glob("*.json"):
        (tmp_path / "schemas" / sema.name).write_text(
            sema.read_text(encoding="utf-8"), encoding="utf-8"
        )
    monkeypatch.setattr(cli, "VERI_KOKU", tmp_path)
    return tmp_path


def _yaz(depo: Path, durum: dict) -> None:
    (depo / "thesis_state.json").write_text(
        json.dumps(durum, ensure_ascii=False), encoding="utf-8"
    )


def _oku(depo: Path) -> dict:
    return json.loads((depo / "thesis_state.json").read_text(encoding="utf-8"))


def _durum(depo: Path) -> dict:
    durum = empty_state("THESIS-2026-001", "Deneme Tezi")
    _yaz(depo, durum)
    return durum


def _onayli_oncekiler(depo: Path, kapi: str) -> dict:
    """`kapi`'dan önceki tüm kapılar onaylı, veri hazır durumda."""
    from tools.atw.approval import onay_ver
    from tools.atw.state import APPROVAL_GATES

    durum = _durum(depo)
    durum["research_questions"] = [{"id": "RQ-001", "text": "Soru", "type": "main", "status": "pending"}]
    durum["search_runs"] = [{
        "id": "SEARCH-0001",
        "database": "crossref",
        "query": "kurgusal arama terimleri",
        "timestamp": "2026-09-27T10:00:00+00:00",
        "results_returned": 0,
        "inclusion_criteria": ["Sinif testi dahil etme olcutu"],
        "exclusion_criteria": ["Sinif testi dislama olcutu"],
        "prisma_flow": {
            "records_identified": 0,
            "duplicates_removed": 0,
            "records_screened": 0,
            "records_excluded": 0,
            "reports_sought": 0,
            "reports_not_retrieved": 0,
            "reports_excluded": 0,
            "studies_included": 0,
        },
    }]
    durum["sources"] = [{
        "id": "SRC-001",
        "title": "Kurgusal Kaynak",
        "source_type": "article",
        "verification": {
            "status": "verified",
            "bibliographic_match": 1.0,
            "verified_at": "2026-09-27T10:00:00+00:00",
            "verification_sources": ["crossref"],
        },
    }]
    durum["gap_registry"] = [{"id": "GAP-001", "statement": "S", "gap_type": "population",
                              "evidence_ids": ["EVD-001"], "confidence": "low"}]
    durum["findings_registry"] = [{"id": "FND-001", "rq_id": "RQ-001", "statement": "S",
                                   "evidence_ids": ["EVD-001"]}]
    for onceki in APPROVAL_GATES[: APPROVAL_GATES.index(kapi)]:
        onay_ver(durum, onceki, onaylayan=DANISMAN)
    _yaz(depo, durum)
    return durum


#: Kurgusal danisman adi; bkz. `test_approval.py` icin aciklama.
DANISMAN = "Dr. Danışman Adı"

# --- yardimcilar ------------------------------------------------------------

def _ns(kapi=None, liste=False, geri_al=False, by=DANISMAN) -> Namespace:
    """`approve` komutunun argumanlarini taklit eder.

    `by` varsayilandir CIFT AMACLI: hem CLI kullanimini taklit eder
    hem de onaylayan zorunlulugunu butun testlere tek yerden yayar.
    Kimliksiz onay uretebilmek icin `by=None` verilebilir, ancak bu
    yalnizca kimligin REDDEDILMESINI konu alan testlerde yapilmalidir.
    """
    return Namespace(kapi=kapi, list=liste, revoke=geri_al, by=by)


def _acik_mi(depo: Path, kapi: str) -> bool:
    """Kapının insan onayı acik mi?

    `human_approvals[kapi]` ya eski `true`/`false` boolean'idir ya da tam
    onay kaydi (`schemas/approval.json`). Testler `is True` demek yerine bu
    yardimciyi kullanir; boylece onay kaydinin alanlari degisse de kapi
    durumu denetlenebilir.
    """
    from tools.atw.approval import kapi_acik_mi

    return kapi_acik_mi(_oku(depo), kapi)


# --- varlik -----------------------------------------------------------------

def test_parser_approve_komutunu_kaydeder():
    """`approve` gerçek bir alt komut olmalı — kapıları açan başka yol yok."""
    from tools.atw.cli.main import build_parser

    ayristirilmis = build_parser().parse_args(["approve", "methodology"])
    assert ayristirilmis.kapi == "methodology"
    assert callable(ayristirilmis.func)


# --- hazirlik reddi ---------------------------------------------------------

def test_hazirligi_olmayan_kapi_acilmaz(depo, capsys):
    """`research_questions` boşken `research_question` kapısı açılmamalı.

    Kapıyı boş bir belgeye vermek, modülün varlık sebebini (docstring
    satır 16-17) ihlal eder: "yalnız 'onay var' demek, boş bir şapaya onay
    vermiş olmak kadar anlamsızdır."
    """
    _durum(depo)

    assert cli.cmd_approve(_ns("research_question")) == 1

    cikti = capsys.readouterr().out
    assert "research_questions" in cikti
    assert not _acik_mi(depo, "research_question"), (
        "hazırlığı olmayan kapı onaylanmış olarak yazıldı"
    )


def test_hazirligi_olan_kapi_acilir(depo, capsys):
    """RQ kayıtlıysa kapı açılmalı ve kalıcı olmalı."""
    durum = _durum(depo)
    durum["research_questions"] = [
        {"id": "RQ-001", "text": "Soru", "type": "main", "status": "pending"}
    ]
    _yaz(depo, durum)

    assert cli.cmd_approve(_ns("research_question")) == 0

    assert "✅" in capsys.readouterr().out
    kayit = _oku(depo)["human_approvals"]["research_question"]
    assert kayit["approved"] is True, "onay kaydı yazılmadı"
    assert kayit["content_hash"].startswith("sha256:"), (
        "onay kaydı içerik özeti taşımıyor — onay bayatlatılamaz"
    )


# --- akis sirasi ------------------------------------------------------------

def test_onceki_kapi_onayli_degilse_acilmaz(depo, capsys):
    """`search_strategy`, `research_question` onaylı olmadan açılmamalı."""
    _onayli_oncekiler(depo, "search_strategy")
    durum = _oku(depo)
    durum["human_approvals"]["research_question"] = False
    _yaz(depo, durum)

    assert cli.cmd_approve(_ns("search_strategy")) == 1

    cikti = capsys.readouterr().out
    assert "research_question" in cikti
    assert not _acik_mi(depo, "search_strategy")


def test_oncekiler_onayliysa_kapi_acilir(depo):
    """Sıra doğruysa kapı açılmalı."""
    _onayli_oncekiler(depo, "search_strategy")

    assert cli.cmd_approve(_ns("search_strategy")) == 0
    assert _acik_mi(depo, "search_strategy")


# --- hazirliksiz kapi (methodology) -----------------------------------------

def test_hazirlik_denetimi_olmayan_kapi_hazirligi_sormaz(depo, capsys):
    """`methodology` hazırlık denetimi taşımaz; onay yine de verilebilir.

    Bu kapının çıktısının (`chapters`) yazıcısı, kapının ARKASINDA
    (`cmd_write`). Denetimi buraya geri koymak ilk bölümün yazılmasını
    engellerdi — `test_methodology_kapisi_bos_bolumle_yazilabilir`.
    """
    _onayli_oncekiler(depo, "methodology")

    assert cli.cmd_approve(_ns("methodology")) == 0
    assert _acik_mi(depo, "methodology")


# --- geri alma --------------------------------------------------------------

def test_geri_alma_sonraki_kapilari_da_kapatir(depo, capsys):
    """`research_question` geri alınınca aşağıdaki tüm onaylar düşmeli."""
    _onayli_oncekiler(depo, "search_strategy")
    assert cli.cmd_approve(_ns("search_strategy")) == 0
    assert _acik_mi(depo, "search_strategy")

    assert cli.cmd_approve(_ns("research_question", geri_al=True)) == 0

    assert not _acik_mi(depo, "research_question")
    assert not _acik_mi(depo, "search_strategy"), (
        "ona dayanan onay düşmedi — akış tutarsız"
    )
    assert "search_strategy" in capsys.readouterr().out


def test_geri_alma_hazirlik_sormaz(depo):
    """Geri alma, hazırlık denetimine takılmamalı.

    Kapıyı geri almak veri üretmekten daha kolaydır; hazırlığı olmayan bir
    kapı (ör. `methodology`) geri alınabilmelidir.
    """
    _onayli_oncekiler(depo, "methodology")
    assert cli.cmd_approve(_ns("methodology")) == 0

    assert cli.cmd_approve(_ns("methodology", geri_al=True)) == 0
    assert not _acik_mi(depo, "methodology")


# --- listeleme --------------------------------------------------------------

def test_liste_yedi_kapiyi_ve_engelleri_gosterir(depo, capsys):
    """`--list` akışı göstermeli ve durumu DEĞİŞTİRMEMELİ."""
    _durum(depo)
    onceki = _oku(depo)

    assert cli.cmd_approve(_ns(liste=True)) == 0

    cikti = capsys.readouterr().out
    for kapi in onceki["human_approvals"]:
        assert kapi in cikti
    assert "0/7" in cikti
    assert _oku(depo) == onceki, "--list durumu değiştirdi"


def test_liste_engeli_olan_kapiyi_isaretler(depo, capsys):
    """Kilitli ve hazırlığı olmayan kapı, gerekçesiyle birlikte çıkmalı."""
    _durum(depo)

    cli.cmd_approve(_ns(liste=True))

    cikti = capsys.readouterr().out
    assert "research_questions" in cikti, (
        "hazırlık eksikleri listelenmiyor — kullanıcı neden açılmadığını göremez"
    )


# --- girdi hatalari ---------------------------------------------------------

def test_bilinmeyen_kapi_reddedilir(depo, capsys):
    """Yazım hatası sessizce geçmemeli; geçerli kapılar listelenmeli."""
    _durum(depo)

    assert cli.cmd_approve(_ns("research_queston")) == 1

    cikti = capsys.readouterr().out
    assert "research_question" in cikti
    assert "final_thesis" in cikti


def test_kapisiz_cagri_reddedilir(depo, capsys):
    """Ne kapı ne `--list` verilmişse kullanıcıya ne yapacağını söylemeliyiz."""
    _durum(depo)

    assert cli.cmd_approve(_ns()) == 1
    assert "--list" in capsys.readouterr().out


# --- durum dosyasi yok ------------------------------------------------------

def test_tez_dosyasi_yoksa_baslamaz(depo, capsys):
    """Onay vermek için tez durumu şart; dosya yoksa hiçbir şey yazılmamalı."""
    assert cli.cmd_approve(_ns("methodology")) == 2
    assert not (depo / "thesis_state.json").exists()
    assert "❌" in capsys.readouterr().out
