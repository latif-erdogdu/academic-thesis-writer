"""`thesis:record` — registry'lere kayıt yazan TEK komut.

Neden bu modül
--------------
`empty_state()` 20 registry başlatıyor, ama bunların çoğunun
YAZICISI YOK. Yazıcısı olanlar:

  * `search_runs` + `sources`  — `cmd_search`
  * `evidence_registry`        — `cmd_extract`
  * `chapters` + `paragraphs`  — `cmd_write` (ikili kayıt)
  * `audit_registry`           — `cmd_audit`

Yazıcısı olmayanlar: `research_questions`, `hypotheses`,
`claims_registry`, `citations`, `gap_registry`, `findings_registry`,
`discussion_registry`, `conclusion_registry` ve ölçüm/varlık
koleksiyonları. Ajanlar durumu GÖREMEZ — `agents/*.md` yalnızca rapor
üretir — dolayısıyla bu registry'ler hiç dolmuyor.

Zincirleme sonuç: `research_questions` boş → `research_question` kapısı
hiç açılamaz → sonraki tüm kapılar sırayla kilitli → `write` ve `export`
erişilemez.

Tek komut, tek yazıcı
---------------------
Beş ayrı komut yazmak, her biri kendi testine sahip birer ikinci yüzey
olurdu; bu depo tam olarak bu hastalıkla yaşıyor (iki şema ağacı, iki
`empty_state`, ölü `pdf_extract` test dizini, `cmd_verify` stub'ı).
Bunun yerine `record <registry> --file <json>`:

  * tek denetim yolu (şema + kopuk referans)
  * tek hata biçimi
  * yeni registry eklemek = tabloya bir satır (ve tablo bile elle
    yazılmıyor, `graph.registry_haritasi()` semadan türetiliyor)

Bir registry'nin İKİ yazıcısı olmaması bir kuraldır. `record`
`SAHIPLI_KOMUTLAR` ile sahiplenilmiş registry'leri reddeder ve sahibini
söyler; aksi halde `record sources` ile `search_runs` eşlemesi atlanır,
`record chapters` ile `write`'ın kapı denetimi atlanır.

Kopuk referanslar neden reddediliyor
------------------------------------
Kayıt, kendi şemasına uygun olsa bile başka bir kayda işaret ediyorsa
o kayıt yoksa yazılmaz. Sebebi: `graph.kopuk_baglari` bu kopukluğu
zaten her bütünlük denetiminde raporluyor; kayıt anında reddetmek,
raporun "ne zaman bozuldu" sorusuna da yanıt verir.

Bu, `claim.contradicted_by` gibi ileri referansları da reddeder. Bu
kasıtlı: `graph.celiskili_iddialar` çelişkinin İKİ tarafını da
çelişkili sayar, yani çelişen iddiayı önce yazıp sonra karşı tarafı
`contradicted_by` ile bağlamak aynı bilgiyi verir ve tek yönlü bir
kayıt bırakmaz. Aynı şekilde `research_question.answered_by` yalnızca
bulgular yazıldıktan sonra doğru olabilir.
"""
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from tools.atw import record as rec
from tools.atw.cli import main as cli
from tools.atw.state import empty_state, validate_state


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


def _dosya(depo: Path, icerik, ad="kayit.json") -> Path:
    yol = depo / ad
    yol.write_text(json.dumps(icerik, ensure_ascii=False), encoding="utf-8")
    return yol


def _rq(kimlik="RQ-001", **ek) -> dict:
    kayit = {
        "id": kimlik,
        "text": "Kurgusal örnek araştırma sorusu",
        "type": "main",
        "status": "pending",
    }
    kayit.update(ek)
    return kayit


def _ns(registry="research_questions", dosya=None) -> Namespace:
    return Namespace(registry=registry, file=dosya)


# --- kayitci yuzeyi (saf fonksiyonlar) --------------------------------------

def test_yazilabilir_registry_sema_turetiyor():
    """Registry -> varlık eşlemesi ELLE yazılmaz, semadan türer.

    `graph.registry_haritasi()` `thesis_state.json`'in `$ref` dizilerinden
    türetiliyor. Elle tablo yazmak, yeni bir sema eklendiğinde sessizce
    eksik kalır.
    """
    from tools.atw.graph import registry_haritasi

    yazilabilir = rec.yazilabilir_registryler()
    assert yazilabilir["research_questions"] == "research_question"
    assert set(yazilabilir).issubset(set(registry_haritasi()))


def test_sahiplenilmis_registry_yazilamaz():
    """Bir registry'nin iki yazıcısı olmaz.

    `record sources` ile `search_runs` eşlemesi atlanabilir,
    `record chapters` ile `write`'ın kapı denetimi atlanabilirdi.
    """
    for registry, sahip in rec.SAHIPLI_KOMUTLAR.items():
        assert registry not in rec.yazilabilir_registryler(), (
            f"{registry} iki yazıcıya açık: {sahip} ve thesis:record"
        )


def test_sahiplik_tablosu_gecerli_registry_adi_taşır():
    """Sahiplik tablosundaki her ad gerçekten bir registry olmalı."""
    from tools.atw.graph import registry_haritasi

    for registry in rec.SAHIPLI_KOMUTLAR:
        assert registry in registry_haritasi(), f"{registry} registry değil"


# --- dosya okuma ------------------------------------------------------------

def test_tek_kayit_tek_sozluk_olarak_okunur(tmp_path):
    yol = _dosya(tmp_path, _rq())
    assert rec.kayitlari_oku(yol) == [_rq()]


def test_kayit_dizisi_okunur(tmp_path):
    kayitlar = [_rq("RQ-001"), _rq("RQ-002", type="sub")]
    yol = _dosya(tmp_path, kayitlar)
    assert rec.kayitlari_oku(yol) == kayitlar


def test_bos_dosya_reddedilir(tmp_path):
    yol = _dosya(tmp_path, [])
    with pytest.raises(rec.KayitHatasi) as hata:
        rec.kayitlari_oku(yol)
    assert "boş" in str(hata.value).lower() or "bos" in str(hata.value).lower()


def test_sozluk_olmayan_icerik_reddedilir(tmp_path):
    yol = _dosya(tmp_path, "metin")
    with pytest.raises(rec.KayitHatasi):
        rec.kayitlari_oku(yol)


def test_json_sozde_esi_reddedilir(tmp_path):
    yol = tmp_path / "bozuk.json"
    yol.write_text("{bozuk", encoding="utf-8")
    with pytest.raises(rec.KayitHatasi):
        rec.kayitlari_oku(yol)


# --- dogrulama --------------------------------------------------------------

def test_gecerli_kayit_hatasiz():
    durum = empty_state("T", "Baslik")
    assert rec.dogrula("research_questions", [_rq()], durum) == []


def test_semaya_aykiri_kayit_hata_uretir():
    durum = empty_state("T", "Baslik")
    # `type` enum degil.
    hatalar = rec.dogrula("research_questions", [_rq(type="yanlis")], durum)
    assert hatalar
    assert any("type" in h for h in hatalar)


def test_zorunlu_alan_eksikse_hata_uretir():
    durum = empty_state("T", "Baslik")
    bozuk = _rq()
    del bozuk["text"]
    hatalar = rec.dogrula("research_questions", [bozuk], durum)
    assert hatalar
    assert any("text" in h for h in hatalar)


def test_kimlik_bicimi_yanlissa_hata_uretir():
    durum = empty_state("T", "Baslik")
    hatalar = rec.dogrula("research_questions", [_rq(kimlik="SORU-1")], durum)
    assert hatalar


def test_ayni_dosyada_tekrarli_kimlik_reddedilir():
    """İki kayıt aynı kimliği taşıyorsa hangisinin kazandığı belirsizdir."""
    durum = empty_state("T", "Baslik")
    hatalar = rec.dogrula("research_questions", [_rq("RQ-001"), _rq("RQ-001")], durum)
    assert hatalar
    assert any("RQ-001" in h for h in hatalar)


def test_yeni_kopuk_referans_reddedilir():
    """`related_claims` gösterilmeyen iddiyaya işaret edemez.

    `graph.kopuk_baglari` bu kopukluğu zaten her bütünlük denetiminde
    raporluyor; kayıt anında reddetmek "ne zaman bozuldu" sorusuna da
    yanıt verir.
    """
    durum = empty_state("T", "Baslik")
    hatalar = rec.dogrula(
        "research_questions", [_rq(related_claims=["CLM-001"])], durum
    )
    assert hatalar
    assert any("CLM-001" in h for h in hatalar)


def mevcut_kopukluk_kaydin_suçu_değildir():
    durum = empty_state("T", "Baslik")
    durum["claims_registry"] = [{"id": "CLM-001", "text": "x", "importance": "high",
                                 "verification_status": "verified",
                                 "evidence_ids": ["EVD-999"]}]
    # CLM-001'in EVD-999'u yok; ama bizim kaydımız onu TETİKLEMİYOR.
    hatalar = rec.dogrula("research_questions", [_rq()], durum)
    assert hatalar == []


def test_var_olan_referans_kabul_edilir():
    durum = empty_state("T", "Baslik")
    durum["claims_registry"] = [{"id": "CLM-001", "text": "x", "importance": "high",
                                 "verification_status": "verified", "evidence_ids": []}]
    hatalar = rec.dogrula(
        "research_questions", [_rq(related_claims=["CLM-001"])], durum
    )
    assert hatalar == []


def test_bilinmeyen_registry_reddedilir():
    durum = empty_state("T", "Baslik")
    with pytest.raises(rec.KayitHatasi) as hata:
        rec.dogrula("uydurma_registry", [_rq()], durum)
    assert "research_questions" in str(hata.value)


def test_sahiplenilmis_registry_dogrulamada_reddedilir():
    durum = empty_state("T", "Baslik")
    with pytest.raises(rec.KayitHatasi) as hata:
        rec.dogrula("sources", [{"id": "SRC-001"}], durum)
    assert "thesis:search" in str(hata.value)


# --- kaydetme --------------------------------------------------------------

def test_yeni_kayit_eklenir():
    durum = empty_state("T", "Baslik")
    ozet = rec.kaydet(durum, "research_questions", [_rq()])
    assert ozet["eklendi"] == ["RQ-001"]
    assert ozet["degistirildi"] == []
    assert [k["id"] for k in durum["research_questions"]] == ["RQ-001"]


def test_ayni_kimlik_degistirilir():
    """Yeniden kayıt EKLEMEZ, değiştirir.

    `cmd_write`'ın bölüm/paragraf davranışıyla aynı: ikinci kayıt
    tekrardır, güncellemedir.
    """
    durum = empty_state("T", "Baslik")
    rec.kaydet(durum, "research_questions", [_rq()])
    ozet = rec.kaydet(durum, "research_questions",
                      [_rq(text="Düzeltilmiş soru", status="answered")])

    assert ozet["degistirildi"] == ["RQ-001"]
    assert len(durum["research_questions"]) == 1
    assert durum["research_questions"][0]["text"] == "Düzeltilmiş soru"
    assert durum["research_questions"][0]["status"] == "answered"


def test_kimliksiz_kayda_sonraki_bos_kimlik_atar():
    """`ids.next_id` ile boş numara verilir; ajan numara saymak zorunda değil.

    Sema `id` alanını zorunlu kılıyor, ama numarayı insanın değil
    `ids.next_id`'nin seçmesi doğru taraf: RQ-007 silinince bir sonraki
    kayıt RQ-007 olur, çakışmaz.
    """
    durum = empty_state("T", "Baslik")
    rec.kaydet(durum, "research_questions", [_rq("RQ-001")])
    kayitsiz = _rq()
    del kayitsiz["id"]
    rec.kaydet(durum, "research_questions", [kayitsiz])
    assert [k["id"] for k in durum["research_questions"]] == ["RQ-001", "RQ-002"]


def test_kayit_sirasi_korunur():
    durum = empty_state("T", "Baslik")
    rec.kaydet(durum, "research_questions", [_rq("RQ-002"), _rq("RQ-001")])
    assert [k["id"] for k in durum["research_questions"]] == ["RQ-002", "RQ-001"]


# --- CLI --------------------------------------------------------------------

def test_parser_record_komutunu_kaydeder():
    from tools.atw.cli.main import build_parser

    ayristirilmis = build_parser().parse_args(
        ["record", "research_questions", "--file", "x.json"]
    )
    assert ayristirilmis.registry == "research_questions"
    assert ayristirilmis.file == "x.json"
    assert callable(ayristirilmis.func)


def test_cli_kaydi_duruma_yazar(depo, capsys):
    _durum(depo)
    yol = _dosya(depo, _rq())

    assert cli.cmd_record(_ns(dosya=yol)) == 0

    cikti = capsys.readouterr().out
    assert "RQ-001" in cikti
    assert [k["id"] for k in _oku(depo)["research_questions"]] == ["RQ-001"]


def test_cli_yazilan_durum_sema_uyumlu(depo):
    """CLI'nin kendi `save_state`'i doğrulamıyor; sonuç yine de geçerli olmalı."""
    from tools.atw.state import validate_state as dogrula_state

    _durum(depo)
    yol = _dosya(depo, _rq())
    cli.cmd_record(_ns(dosya=yol))
    assert dogrula_state(_oku(depo)) == []


def test_cli_hatali_kayitta_hicbir_sey_yazmaz(depo, capsys):
    _durum(depo)
    onceki = _oku(depo)
    yol = _dosya(depo, [_rq(type="yanlis")])

    assert cli.cmd_record(_ns(dosya=yol)) == 1
    assert _oku(depo) == onceki, "reddedilen kayıt kısmen yazıldı"
    assert "type" in capsys.readouterr().out


def test_cli_dosyasiz_cagri_yardim_gosterir(depo, capsys):
    _durum(depo)
    assert cli.cmd_record(_ns()) == 1
    cikti = capsys.readouterr().out
    assert "--file" in cikti
    assert "research_questions" in cikti


def test_cli_olmayan_dosya_reddedilir(depo, capsys):
    _durum(depo)
    assert cli.cmd_record(_ns(dosya=depo / "yok.json")) == 1
    assert "yok.json" in capsys.readouterr().out


def test_cli_bilinmeyen_registry_reddedilir(depo, capsys):
    _durum(depo)
    yol = _dosya(depo, _rq())
    assert cli.cmd_record(_ns(registry="uydurma", dosya=yol)) == 1
    assert "research_questions" in capsys.readouterr().out


def test_cli_tez_dosyasi_yoksa_baslamaz(depo, capsys):
    yol = _dosya(depo, _rq())
    assert cli.cmd_record(_ns(dosya=yol)) == 2
    assert "❌" in capsys.readouterr().out
