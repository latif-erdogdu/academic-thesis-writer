"""`thesis:exclude` — PRISMA tarama kararını kaynak kümesine uygulayan komut.

Neden bu test
-------------
Skill'in sistematik inceleme protokolü (SKILL.md 2.3) "Başlık/Özet Tarama"
ve "Hariç Tutma Kriterleri" adımlarını zorunlu kılıyor. Ama CLI'da kayıt
elemek için hiçbir komut YOKTU: `record sources` sahiplik nedeniyle
reddediliyor (`thesis:search` sahibi), silme komutu da yok. Gerçek bir
koşuda bu kendini gösterdi:

  * üç arama 80 kayıt getirdi, 25 çakışan DOI ile (aynı çalışma her
    aramada ayrı SRC kimliği aldı — arama-arası tekilleştirme yok);
  * `10.7717/peerj.20291/fig-1` gibi ek-materyal DOI'leri (`fig-*`,
    `supp-*`) taramaya girmişti.

Küme dürüst olamaz: `source_set` kapısı 80 kaydı "elenmiş" sayamaz.
`source.json` şemasında per-kayıt "excluded" işareti yok; elemek =
kaynakları `sources`'dan çıkarmak + arama kayıtlarının PRISMA akışını
yeniden türetmek (şemadaki `records_screened = records_excluded +
studies_included` dengesi bozulmadan).

Güvenlik kuralı: elenen kaynağa başka bir kayıt referans veriyorsa
(citation, evidence, gap, discussion, figure/table, supersedes) komut
YAZMAZ — kopuk bağ üretmek, tarama kararından daha ciddi bir hasardır.

Doğrulama sırası: bilinmeyen kimlik → boş gerekçe → referans koruması →
şema (validate_state). Hiçbir adımda kısmi yazım yoktur.
"""
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from tools.atw.cli import main as cli
from tools.atw.state import empty_state, validate_state


@pytest.fixture
def depo(tmp_path, monkeypatch):
    """CLI'nin veri kökünü geçici bir dizine bağlar (şemaları dahtan kopyalar)."""
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


def _kaynak(kimlik: str, baslik: str = "Kurgusal Kaynak") -> dict:
    return {
        "id": kimlik,
        "title": baslik,
        "source_type": "article",
        "verification": {
            "status": "verified",
            "bibliographic_match": 1.0,
            "verified_at": "2026-09-27T10:00:00+00:00",
            "verification_sources": ["crossref"],
        },
    }


def _arama_kaydi(dahil: list[str], kayit_sayisi: int = 2) -> dict:
    return {
        "id": "SEARCH-0001",
        "database": "crossref",
        "query": "kurgusal arama terimleri",
        "timestamp": "2026-09-27T10:00:00+00:00",
        "results_returned": kayit_sayisi,
        "inclusion_criteria": ["Sinif testi dahil etme olcutu"],
        "exclusion_criteria": ["Sinif testi dislama olcutu"],
        "prisma_flow": {
            "records_identified": kayit_sayisi,
            "duplicates_removed": 0,
            "records_screened": kayit_sayisi,
            "records_excluded": 0,
            "reports_sought": kayit_sayisi,
            "reports_not_retrieved": 0,
            "reports_excluded": 0,
            "studies_included": kayit_sayisi,
        },
        "included_source_ids": dahil,
    }


def _ns(*ids, sebep="duplicate of earlier record") -> Namespace:
    return Namespace(ids=list(ids), reason=sebep)


# --- varlik -----------------------------------------------------------------

def test_parser_exclude_komutunu_kaydeder():
    """`exclude` gerçek bir alt komut olmalı — tarama kararını veren başka yol yok."""
    from tools.atw.cli.main import build_parser

    ayristirilmis = build_parser().parse_args(
        ["exclude", "SRC-001", "--reason", "ek materyal DOI'si"]
    )
    assert ayristirilmis.ids == ["SRC-001"]
    assert ayristirilmis.reason == "ek materyal DOI'si"
    assert callable(ayristirilmis.func)


# --- temel eleme ------------------------------------------------------------

def test_kaynak_listeden_cikarilir(depo, capsys):
    """Verilen kimlik `sources`'dan çıkmalı; diğerleri yerinde kalmalı."""
    durum = _durum(depo)
    durum["sources"] = [_kaynak("SRC-001"), _kaynak("SRC-002")]
    _yaz(depo, durum)

    assert cli.cmd_exclude(_ns("SRC-001")) == 0

    kalan = [k["id"] for k in _oku(depo)["sources"]]
    assert kalan == ["SRC-002"]
    assert "SRC-001" in capsys.readouterr().out


def test_bilinmeyen_id_reddedilir(depo, capsys):
    """Var olmayan kimlik sessizce geçmemeli; durum değişmemeli."""
    durum = _durum(depo)
    durum["sources"] = [_kaynak("SRC-001")]
    _yaz(depo, durum)
    onceki = _oku(depo)

    assert cli.cmd_exclude(_ns("SRC-999")) == 1

    cikti = capsys.readouterr().out
    assert "SRC-999" in cikti
    assert _oku(depo) == onceki, "bilinmeyen kimlik için durum değiştirildi"


def test_bos_gerekce_reddedilir(depo, capsys):
    """Gerekçesiz eleme kararı yazılmamalı (kanıtsız tarama kararı olurdu)."""
    durum = _durum(depo)
    durum["sources"] = [_kaynak("SRC-001")]
    _yaz(depo, durum)

    assert cli.cmd_exclude(_ns("SRC-001", sebep="   ")) == 1
    assert "gerekçe" in capsys.readouterr().out
    assert [k["id"] for k in _oku(depo)["sources"]] == ["SRC-001"]


# --- PRISMA akışı -----------------------------------------------------------

def test_prisma_akis_ve_dahil_listesi_guncellenir(depo):
    """Elemeyle arama kaydı: screening elemesi records_excluded'a yazılır.

    Ölçülen-bozuk aşama eşlemesi (düzeltildi, 2026-09-28): `exclude`
    yalnızca başlık/DOI/özet TARAMA kararıdır (kopya, yayın türü,
    konu dışı); hiçbir kaydın tam metnine ulaşılmaz. Bu yüzden eleme
    `records_excluded` (başlık/özet aşaması) kademesine düşer ve
    `reports_sought` (tam metin aranan raporlar) aynı miktar azalır.
    Eski davranış her eleme kararını `reports_excluded`'a (tam metin
    uygunluk) yazıyordu — PRISMA diyagramı, tam metni hiç alınmamış
    raporlar için 'tam metin dışlanan N rapor' iddiası üretiyordu.
    """
    durum = _durum(depo)
    durum["sources"] = [_kaynak("SRC-001"), _kaynak("SRC-002")]
    durum["search_runs"] = [_arama_kaydi(["SRC-001", "SRC-002"])]
    _yaz(depo, durum)

    assert cli.cmd_exclude(_ns("SRC-002")) == 0

    kayit = _oku(depo)["search_runs"][0]
    assert kayit["included_source_ids"] == ["SRC-001"]
    assert kayit["prisma_flow"]["studies_included"] == 1
    assert kayit["prisma_flow"]["records_excluded"] == 1
    assert kayit["prisma_flow"]["reports_sought"] == 1, (
        "tam metin aranan rapor sayısı, taramada elenen kayıt kadar azalmalı"
    )
    assert kayit["prisma_flow"]["reports_excluded"] == 0, (
        "tam metin uygunluk aşamasında KARAR VERİLMEDİ — o sayı değişmemeli"
    )


def test_eleme_karari_exclusion_reasonsa_yazilir(depo):
    """Gerekçe arama kaydının `exclusion_reasons`'a kalıcı yazılmalı."""
    durum = _durum(depo)
    durum["sources"] = [_kaynak("SRC-001"), _kaynak("SRC-002")]
    durum["search_runs"] = [_arama_kaydi(["SRC-001", "SRC-002"])]
    _yaz(depo, durum)

    cli.cmd_exclude(_ns("SRC-002", sebep="ek materyal DOI'si"))

    nedenler = _oku(depo)["search_runs"][0].get("exclusion_reasons", [])
    assert nedenler == [{"reason": "ek materyal DOI'si", "count": 1}]


def test_ayni_neden_birikir(depo):
    """Aynı gerekçeyle ikinci eleme count'u artırmalı (satır çoğaltmamalı)."""
    durum = _durum(depo)
    durum["sources"] = [_kaynak("SRC-001"), _kaynak("SRC-002"), _kaynak("SRC-003")]
    durum["search_runs"] = [_arama_kaydi(["SRC-001", "SRC-002", "SRC-003"], 3)]
    _yaz(depo, durum)

    cli.cmd_exclude(_ns("SRC-002", sebep="ek materyal"))
    cli.cmd_exclude(_ns("SRC-003", sebep="ek materyal"))

    nedenler = _oku(depo)["search_runs"][0].get("exclusion_reasons", [])
    assert nedenler == [{"reason": "ek materyal", "count": 2}]


def test_eleme_her_zaman_tarama_asamasina_yazilir(depo):
    """Her `exclude` çağrısı başlık/özet (records_excluded) kademesine düşer.

    Tarama kararı tam metin incelemesi DEĞİLDİR: rapor hiç alınmadı,
    okuyucu hiç görmedi. `reports_excluded` (tam metin uygunluk) ve
    `reports_not_retrieved` (alınamayan) kademeleri bu komutla
    dokunulmadan kalmalı — aksi halde PRISMA diyagramı, tam metni hiç
    alınmamış raporlar için 'tam metin aşamasında dışlandı' iddiası taşır.
    """
    from tools.atw.state import validate_prisma_flow

    durum = _durum(depo)
    durum["sources"] = [
        _kaynak("SRC-001"), _kaynak("SRC-002"), _kaynak("SRC-003"),
    ]
    durum["search_runs"] = [_arama_kaydi(["SRC-001", "SRC-002", "SRC-003"], 3)]
    _yaz(depo, durum)

    cli.cmd_exclude(_ns("SRC-002", sebep="ek materyal"))
    cli.cmd_exclude(_ns("SRC-003", sebep="kopya"))

    akis = _oku(depo)["search_runs"][0]["prisma_flow"]
    assert akis["records_excluded"] == 2
    assert akis["reports_sought"] == 1
    assert akis["reports_excluded"] == 0
    assert akis["reports_not_retrieved"] == 0
    assert akis["studies_included"] == 1
    assert not validate_prisma_flow(akis), validate_prisma_flow(akis)


# --- referans koruması ------------------------------------------------------

def test_atif_yapilmis_kaynak_elenemez(depo, capsys):
    """Citation referans verdiği kaynağın elenmesini engellemeli."""
    durum = _durum(depo)
    durum["sources"] = [_kaynak("SRC-001")]
    durum["citations"] = [{
        "id": "CIT-001", "paragraph_id": "P-001", "source_id": "SRC-001",
        "style": "apa7", "in_text_form": "(Yazar, 2020)",
    }]
    _yaz(depo, durum)
    onceki = _oku(depo)

    assert cli.cmd_exclude(_ns("SRC-001")) == 1

    cikti = capsys.readouterr().out
    assert "CIT-001" in cikti
    assert _oku(depo) == onceki, "referans verilmiş kaynak elendi"


def test_supersedes_baglayan_kaynak_elenemez(depo, capsys):
    """Başka bir kaynağın `supersedes_source_id` döndüğü kaynak elenemez."""
    durum = _durum(depo)
    k1 = _kaynak("SRC-001")
    durum["sources"] = [k1, _kaynak("SRC-002")]
    durum["sources"][1]["supersedes_source_id"] = "SRC-001"
    _yaz(depo, durum)

    assert cli.cmd_exclude(_ns("SRC-001")) == 1

    cikti = capsys.readouterr().out
    assert "SRC-002" in cikti
    assert len(_oku(depo)["sources"]) == 2


# --- durum bütünlüğü --------------------------------------------------------

def test_elenen_durum_gecerli_kalir(depo):
    """Eleme sonrası durum şemaya uymalı (kapının gördüğü durumla aynı)."""
    durum = _durum(depo)
    durum["sources"] = [_kaynak("SRC-001"), _kaynak("SRC-002")]
    durum["search_runs"] = [_arama_kaydi(["SRC-001", "SRC-002"])]
    _yaz(depo, durum)

    assert cli.cmd_exclude(_ns("SRC-002")) == 0

    hatalar = validate_state(_oku(depo))
    assert not hatalar, hatalar


def test_tez_dosyasi_yoksa_baslamaz(depo, capsys):
    """Durum dosyası yoksa hiçbir şey yazılmamalı (diğer komutlarla aynı)."""
    assert cli.cmd_exclude(_ns("SRC-001")) == 2
    assert not (depo / "thesis_state.json").exists()
    assert "❌" in capsys.readouterr().out