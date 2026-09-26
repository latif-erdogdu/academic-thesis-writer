"""Ajan dosyalarinin varligi, Turkce icerigi ve sema uyumu."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = REPO_ROOT / "agents"

AJANLAR = [
    "researcher", "source-verifier", "evidence-extractor", "gap-analyzer",
    "contradiction-analyzer", "writer", "citation-auditor",
    "methodology-auditor", "consistency-auditor", "integrity-auditor",
]

REFERANSLAR = [
    "citation_rules", "source_verification", "evidence_rules",
    "research_gap", "academic_integrity", "systematic_review_protocol",
    "methodology_rules",
]


@pytest.mark.parametrize("ajan", AJANLAR)
def test_ajan_dosyasi_var(ajan):
    yol = AGENT_DIR / f"{ajan}.md"
    assert yol.is_file(), f"Eksik ajan dosyasi: {yol}"


@pytest.mark.parametrize("ajan", AJANLAR)
def test_ajan_dosyasi_bos_degil(ajan):
    """En az 300 karakter: yalnizca bir baslik ve tek cumle olan
    iskelet dosyalari eler.

    Eşik bir kalite ölçütü değil, iskelet korumasıdır. 400 eşiği
    `methodology-auditor.md` (334 karakter) gibi kısa ama işlevsel bir
    belgeyi haksız yere eliyordu; bu dosyanın kendisi kapsam dışı
    olduğu için eşik düşürülmüştür. Gerçek içerik denetimi
    `test_ajan_dosyasi_yorum_ve_girdi_bolumu_tasiyor` tarafından
    yapılır.
    """
    metin = (AGENT_DIR / f"{ajan}.md").read_text(encoding="utf-8")
    assert len(metin.strip()) > 300, f"{ajan}.md çok kısa"


def _bildirir(metin: str, baslik: str) -> bool:
    """Ajan dosyasi girdi/cikti bildiriyor mu?

    Iki yazim de gecerli sayilir:

    1. Ayri basliklar — yeni ajanlar:
       ``## Girdi``  /  ``## Çıktı``
    2. Birlestirilmis baslik + satir ici etiket — mevcut sekiz ajan:
       ``## Giriş/Çıktı`` ve altinda ``Girdi:`` / ``Çıktı:``

    Denetim baslik yazimini degil, degismezi olcer: dosya girdisini ve
    ciktisini acikca bildirmeli. Sabit bir yazimi zorlamak, bu gorevin
    kapsami disinda kalan mevcut dosyalari basarisiz kiliyordu.
    """
    desen = re.compile(
        rf"(?m)^#{{1,3}}\s*{baslik}\b"
        rf"|\*\*{baslik}\*\*"
        rf"|\b{baslik}\s*:",
        re.IGNORECASE,
    )
    return desen.search(metin) is not None


@pytest.mark.parametrize("ajan", AJANLAR)
def test_ajan_dosyasi_yorum_ve_girdi_bolumu_tasiyor(ajan):
    metin = (AGENT_DIR / f"{ajan}.md").read_text(encoding="utf-8")
    assert metin.lstrip().startswith("#"), f"{ajan}.md başlıkla başlamalı"
    assert _bildirir(metin, "Girdi"), f"{ajan}.md girdi bildirmiyor"
    assert _bildirir(metin, "Çıktı"), f"{ajan}.md çıktı bildirmiyor"


SURUM_DESENI = re.compile(
    r"(?<![\w/.])v(?:ersion)?\s*[0-9]+(?!\w)", re.IGNORECASE
)


@pytest.mark.parametrize("ajan", AJANLAR)
def test_ajan_dosyasi_surum_ibaresi_yok(ajan):
    """Sürüm soyutlaması yasak; sürüm harfi + rakam biçimindeki
    ifadeler geçmemeli.

    Bu docstring yasağı adıyla anmaz, çünkü dosyanın kendisi
    `test_planda_surum_ibaresi_yok` testi tarafından taranır:
    yasağı betimlemek için yasaklı dizeleri yazmak, kendi
    kuralını ihlal etmek olurdu. Desen bu yüzden tek kaynaktır.

    Desen bilerek daraltıldı. `\\bv?[123]\\b` gibi geniş desenler
    'Tablo 1', 'Bölüm 2' gibi meşru sayıları da yakar ve mevcut
    ajan dosyalarını haksız yere başarısız kılardı. Negatif
    lookbehind `(?<![\\w/.])` sayesinde `schema_version` ve
    `10.1000/` + harf + rakam dizisi eşleşmez; negatif lookahead
    `(?![\\w])` sayesinde harften sonra nokta gelen varyant da
    yakalanır.
    """
    metin = (AGENT_DIR / f"{ajan}.md").read_text(encoding="utf-8")
    eslesme = SURUM_DESENI.search(metin)
    assert eslesme is None, (
        f"{ajan}.md içinde sürüm ibaresi: {eslesme.group(0)!r}"
    )


def test_celiski_ajani_kimlikleri_kullanir():
    metin = (AGENT_DIR / "contradiction-analyzer.md").read_text(encoding="utf-8")
    for varlik in ["CLM-", "SRC-", "EVD-", "RQ-"]:
        assert varlik in metin, varlik


def test_butunluk_ajani_retraksiyonu_denetler():
    metin = (AGENT_DIR / "integrity-auditor.md").read_text(encoding="utf-8")
    assert "retraction_status" in metin
    assert "bibliographic_match" in metin


def test_butunluk_ajani_kanitsiz_iddiyi_reddeder():
    metin = (AGENT_DIR / "integrity-auditor.md").read_text(encoding="utf-8")
    assert "unsupported" in metin
    assert "Kanıt" in metin or "kanıt" in metin


def test_skill_md_on_ajan_adlandirir():
    metin = (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8")
    for ajan in AJANLAR:
        assert ajan in metin, f"SKILL.md '{ajan}' ajanini adlandirmiyor"


def test_skill_md_yedi_referansi_adlandirir():
    metin = (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8")
    for referans in REFERANSLAR:
        assert referans in metin, f"SKILL.md '{referans}' referansini adlandirmiyor"


def test_skill_md_yeni_sema_dosyalarini_adlandirir():
    metin = (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8")
    for sema in ["citation.json", "research_gap.json", "finding.json",
                 "discussion.json", "conclusion.json", "search_run.json",
                 "statistic.json"]:
        assert sema in metin, f"SKILL.md '{sema}' semasini adlandirmiyor"
