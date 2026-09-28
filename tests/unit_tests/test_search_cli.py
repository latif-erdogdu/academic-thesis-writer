"""`thesis:search` — bilinmeyen araştırma sorusunda akışı kirletmemeli.

Neden bu test
-------------
`cmd_search` şu an bilinmeyen RQ'yu bir uyarıyla geçiyordu:

    if not pico:
        print(f"⚠️  RQ {args.rq} bulunamadı, boş PICO ile devam ediliyor")
        pico = PICO()

Boş PICO, Crossref/OpenAlex/PubMed'e genel bir sorgu gönderir ve
sonuçları `sources`'a yazar. Yani bir yazım hatası ("RQ-001" yerine
"RQ-01"), kullanıcı "100 kaynak buldum" sanırken tezin kaynak
kütüphanesine alakasız kaynakları doldurur. Ölçüldü: 100 kaynak.

Bu sessiz kirlilik, `references/*.md`'nin KURAL verip tezin KAYITLARINI
vermediği, ajanın da tez durumunu görmediği yapının sonucu.

İkinci gerçek hata: `--pico` de verilmemişse `pico = None` kalıyordu.
`run_systematic_search(pico: PICO | str, ...)` zorunlu bir parametre alıyor
ve `build_multi_database_queries(None)` `AttributeError` veriyor — yani
sessiz kirlilik değil, izlenebilir olmayan bir çökme. argparse `rq`'yu
zorunlu yaptığı için bu yola yalnızca doğrudan çağrıdan ulaşılıyor; yine
de reddedilmesi gerekiyor.

Ağ YOK: `tools.source_search.run_systematic_search` testte sahte
arayla değiştirilir. Hiçbir test canlı veritabanı çağrısı yapmaz.
"""
from __future__ import annotations

import json
from argparse import Namespace
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from tools.atw.cli import main as cli
from tools.atw.state import empty_state


@dataclass
class _AramaSonucu:
    """`tools.source_search.SearchRunResult` ile aynı okuma yüzeyi.

    `to_dict()` çıktısı `schemas/search_run.json` ile UYUMLUDUR: CLI
    artık yazmadan önce doğruladığı için sahte sonuç da geçerli olmak
    zorunda. `inclusion_criteria`/`exclusion_criteria` dizi olmalı ve
    boş olamaz (`minItems: 1`), `prisma_flow` ise tam sekiz sayı
    taşımalı.
    """

    search_run_id: str = "SEARCH-0001"
    prisma_flow: dict = field(default_factory=lambda: {
        "records_identified": 0,
        "duplicates_removed": 0,
        "records_screened": 0,
        "records_excluded": 0,
        "reports_sought": 0,
        "reports_not_retrieved": 0,
        "reports_excluded": 0,
        "studies_included": 0,
    })
    deduplication: object = field(default_factory=lambda: type(
        "D", (), {"stats": {"removed": 0}})())
    included_source_ids: list = field(default_factory=list)
    database_results: list = field(default_factory=list)
    included_records: list = field(default_factory=list)

    def to_state_records(self) -> list[dict]:
        """Gerçek `SearchRunResult.to_state_records` yüzeyini yansıtır.

        Bu sahtenin `database_results`'u boştur (varsayılan `[]`);
        gerçek yöntem de boş listede hiç kayıt üretmezdi. CLI'nin yazma
        yolunun çağırdığı bu yüzeyin VAR olması sözleşmedir — içerik bu
        sahte için boştur.
        """
        return []

    def to_dict(self) -> dict:
        return {
            "id": self.search_run_id,
            "database": "crossref",
            "query": "patients cognitive behavioral therapy quality of life",
            "timestamp": "2026-09-27T10:00:00+00:00",
            "results_returned": 0,
            "inclusion_criteria": ["Sinif testi olcutu"],
            "exclusion_criteria": ["Sinif testi dislama olcutu"],
            "prisma_flow": self.prisma_flow,
        }


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


#: `parse_pico` yalnızca İngilizce anahtar kelimelere bakar
#: (`query_builder.py:72-91`: patients, treatment, randomized …). Bu metin
#: oluşturduğu PICO'nun boş OLMAYACAğını garanti eder. Türkçe bir soru
#: metni daima boş PICO üretir — bu bir CLI kusuru değil, `parse_pico`'nun
#: bilinen sınırı ve `test_turkce_rq_reddedilir` ile ayrıca sabitlenir.
_ARANABILIR_RQ_METNI = (
    "Do patients receiving cognitive behavioral therapy show improvement "
    "in quality of life compared to usual care?"
)


def _durum(depo: Path, sorular: list[dict] | None = None) -> dict:
    durum = empty_state("THESIS-2026-001", "Deneme Tezi")
    durum["research_questions"] = sorular if sorular is not None else [
        {
            "id": "RQ-001",
            "text": _ARANABILIR_RQ_METNI,
            "type": "main",
            "status": "pending",
        }
    ]
    _yaz(depo, durum)
    return durum


def _sahte_arama(monkeypatch) -> list[dict]:
    """Arama motorunu sahte olanla değiştirir; çağrıları toplar."""
    cagrilar: list[dict] = []

    def sahte(pico=None, **kwargs):
        cagrilar.append({"pico": pico, **kwargs})
        return _AramaSonucu()

    monkeypatch.setattr("tools.source_search.run_systematic_search", sahte)
    return cagrilar


def _ns(rq="RQ-001", pico=None, veritabanlari="crossref", yil_bas=None,
        yil_bit=None, en_fazla=100) -> Namespace:
    return Namespace(
        rq=rq, pico=pico, databases=veritabanlari,
        year_from=yil_bas, year_to=yil_bit, max_results=en_fazla,
    )


# --- bilinmeyen RQ ----------------------------------------------------------

def test_bilinmeyen_rq_reddedilir(depo, monkeypatch, capsys):
    """Yazım hatası aramayı BAŞLATMAMALI.

    `⚠️ ... boş PICO ile devam ediliyor` bir uyarı değil, 100 alakasız
    kaynağın teze yazılmasıydı.
    """
    _durum(depo)
    cagrilar = _sahte_arama(monkeypatch)

    assert cli.cmd_search(_ns(rq="RQ-01")) == 1

    assert cagrilar == [], "geçersiz RQ ile arama motoru çağrıldı"
    cikti = capsys.readouterr().out
    assert "RQ-01" in cikti
    assert "RQ-001" in cikti, "kullanılabilir RQ'lar gösterilmedi"


def test_bilinmeyen_rq_durumu_kirletmez(depo, monkeypatch, capsys):
    """Reddedilen arama `sources`'a kaynak EKLEMEMELİ."""
    _durum(depo)
    _sahte_arama(monkeypatch)
    onceki = _oku(depo)

    cli.cmd_search(_ns(rq="RQ-99"))

    assert _oku(depo)["sources"] == onceki["sources"]
    assert _oku(depo)["search_runs"] == onceki["search_runs"]
    capsys.readouterr()


def test_tezsiz_rq_listesi_bos_durumda_gosterilir(depo, monkeypatch, capsys):
    """RQ kaydı hiç yoksa kullanıcı ne yapacağını bilmeli.

    Kayda yazan komut henüz yok; mesaj hangi registry'nin boş olduğunu
    söylemeli.
    """
    _durum(depo, sorular=[])
    cagrilar = _sahte_arama(monkeypatch)

    assert cli.cmd_search(_ns(rq="RQ-001")) == 1

    assert cagrilar == []
    assert "research_questions" in capsys.readouterr().out


def test_arama_yapilabilir_rq_gecerlidir(depo, monkeypatch, capsys):
    """RQ varsa arama ÇALIŞMALI — reddetme her şeyi durdurmasın."""
    _durum(depo)
    cagrilar = _sahte_arama(monkeypatch)

    assert cli.cmd_search(_ns(rq="RQ-001")) == 0
    assert len(cagrilar) == 1
    assert "RQ-001" in capsys.readouterr().out


# --- bos / bos PICO ---------------------------------------------------------

def test_rq_metni_arama_terimi_uretmeyorsa_reddedilir(depo, monkeypatch, capsys):
    """Metni terim üretmeyen bir RQ, boş PICO demektir; aynı kirlilik riski.

    Kayıtlı ama aranabilir olmayan bir soru, kaydı bulmakla arama
    yapmak arasındaki farkı kapatmaz.
    """
    _durum(depo, sorular=[{"id": "RQ-001", "text": "", "type": "main", "status": "pending"}])
    cagrilar = _sahte_arama(monkeypatch)

    assert cli.cmd_search(_ns(rq="RQ-001")) == 1

    assert cagrilar == [], "boş PICO ile arama yapıldı"
    cikti = capsys.readouterr().out
    assert "RQ-001" in cikti


def test_turkce_rq_reddedilir_ve_gerekce_yazilir(depo, monkeypatch, capsys):
    """BILINEN SINIR: `parse_pico` Türkçe anlamıyor.

    `query_builder.py:72-91` yalnızca İngilizce anahtar kelime listelerine
    bakar. Skill tamamen Türkçe bir tez akışı için tasarlandığı için bu,
    `--rq` yolunun TÜM gerçek girdilerinde boş PICO demektir. Reddedilmesi
    doğru davranış; ama kullanıcı bunun kendi yazım hatası değil, araç
    sınırı olduğunu bilmeli. Bu test sınırı SABİTLER, böylece `parse_pico`
    Türkçe destekleyene kadar sessizce "düzeltilmiş" sanılmaz.
    """
    _durum(depo, sorular=[{
        "id": "RQ-001",
        "text": "Kurgusal örnek: yöntemin etkisi nedir?",
        "type": "main",
        "status": "pending",
    }])
    cagrilar = _sahte_arama(monkeypatch)

    assert cli.cmd_search(_ns(rq="RQ-001")) == 1

    assert cagrilar == [], "Türkçe RQ'den boş PICO ile arama yapıldı"
    cikti = capsys.readouterr().out
    assert "parse_pico" in cikti, (
        "gerekçe belirtilmedi — kullanıcı bunun kendi hatası sanır"
    )
    assert "İngilizce" in cikti
    assert "--pico" in cikti, "alternatif gösterilmedi"


def test_ne_rq_ne_pico_reddedilir(depo, monkeypatch, capsys):
    """PICO'suz arama `AttributeError` ile çöker; reddedilmeli.

    argparse `rq`'yu zorunlu yaptığı için bu yola yalnızca doğrudan
    çağrıdan ulaşılıyor, ama `run_systematic_search(pico: PICO | str)`
    zorunlu parametre alıyor ve `None` ile çağrılınca çöküyor.
    """
    _durum(depo)
    cagrilar = _sahte_arama(monkeypatch)

    assert cli.cmd_search(_ns(rq=None)) == 1

    assert cagrilar == []
    cikti = capsys.readouterr().out
    assert "--pico" in cikti or "rq" in cikti


# --- --pico -----------------------------------------------------------------

def test_pico_rq_dan_onceceliklidir(depo, monkeypatch):
    """`--pico` verilmişse RQ aranmaz; metin doğrudan kullanılır.

    Arama bazen kayıtlı bir RQ'ya bağlı olmadan, özgün PICO ile
    çalıştırılır (ör. ön tarama).
    """
    _durum(depo)
    cagrilar = _sahte_arama(monkeypatch)

    cli.cmd_search(_ns(rq="RQ-01", pico="pop: okul, intervention: egitim, outcome: basari"))

    assert len(cagrilar) == 1
    assert cagrilar[0]["pico"] is not None


# --- girdi aktarimi ---------------------------------------------------------

def test_veritabani_listesi_tek_kez_ayristirilir(depo, monkeypatch, capsys):
    """Virgülle ayrılmış liste `run_systematic_search`'e temiz geçmeli.

    Eski kodda `databases = [db.strip() ...]` bir kez hesaplanıyor,
    ikinci kez `args.databases.split(",")` inline geçiyordu; ilk
    hesap atılıydı.
    """
    _durum(depo)
    cagrilar = _sahte_arama(monkeypatch)

    cli.cmd_search(_ns(rq="RQ-001", veritabanlari="crossref, openalex"))

    assert cagrilar[0]["databases"] == ["crossref", "openalex"]


def test_yil_araligi_iletilir(depo, monkeypatch):
    """`--year-from`/`--year-to` aramaya aktarılmalı."""
    _durum(depo)
    cagrilar = _sahte_arama(monkeypatch)

    cli.cmd_search(_ns(rq="RQ-001", yil_bas=2015, yil_bit=2024, en_fazla=25))

    assert cagrilar[0]["year_from"] == 2015
    assert cagrilar[0]["year_to"] == 2024
    assert cagrilar[0]["max_results_per_db"] == 25


# --- tez dosyasi yok -------------------------------------------------------

def test_tez_dosyasi_yoksa_baslamaz(depo, monkeypatch, capsys):
    """Arama tez durumu olmadan yapılamaz."""
    cagrilar = _sahte_arama(monkeypatch)

    assert cli.cmd_search(_ns(rq="RQ-001")) == 2
    assert cagrilar == []
    assert "❌" in capsys.readouterr().out
