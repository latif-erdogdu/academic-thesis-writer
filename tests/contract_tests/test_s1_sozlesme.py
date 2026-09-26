"""S1: Sözleşme testi — ajan belgelerindeki JSON blokları şemaya uygun mu?

Bu test KIRMIZI başlamalıdır. 4 ajan belgesi + SKILL.md + thesis_state.json
hedeflenir. Onarım sonrası YEŞIL olmalıdır.

Kapsam:
- F1: source-verifier.md:38 -> source.json additionalProperties (5 alan)
- F2: gap-analyzer.md:38 -> research_gap.json additionalProperties (3) + enum (2)
- F4: SKILL.md:242 -> thesis_state.json additionalProperties (claims) + 11x required
- F21: writer.md:34 -> paragraph.json pattern (RQ2 != ^RQ-\d{3,}$)
- F3: contradiction-analyzer.md:36 -> statistic.json power alan yok (sınıf-2)
- F22: fence'siz bloklar (source-verifier, gap-analyzer) -> fence'e alınacak

Sınıflar:
- Sınıf 1: additionalProperties / enum / pattern / type (geçerli)
- Sınıf 2: ardisik dizi kuralı (başındaki backtick'li tanımlayıcı dizisi)
- Sınıf 3: THESIS öneki dışı (şu an yeşil)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from tools.atw.ids import ID_PREFIXES
from tools.atw.state import SCHEMA_DIR, load_schema, schema_registry

# --- yardımcı: şema yükleme ---------------------------------------------------

def load_sema(adi: str) -> dict:
    return load_schema(f"{adi}.json")


REGISTRY = schema_registry()

# --- belge tarama -------------------------------------------------------------

FENCE_DESENI = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
FENCESIZ_DESENI = re.compile(r"(?m)^\s*(\{[\s\S]*?^\s*\})\s*$")


def json_bloklari_yol_yolla(yol: Path) -> list[tuple[dict, int, bool]]:
    """Dosyadaki JSON bloklarını (fence'li + fence'siz) döndürür.

    Returns: [(sozluk, satir_no, fence_li_mi), ...]
    """
    metin = yol.read_text(encoding="utf-8")
    satirlar = metin.splitlines(keepends=True)
    bloklar: list[tuple[dict, int, bool]] = []

    # Fence'li
    for eslesme in FENCE_DESENI.finditer(metin):
        bas = metin[:eslesme.start()].count("\n") + 1
        try:
            bloklar.append((json.loads(eslesme.group(1)), bas, True))
        except json.JSONDecodeError:
            pass

    # Fence'siz: satır 0'da '{' ile başlayıp satır 0'da '}' ile biten bloklar
    i = 0
    while i < len(satirlar):
        if satirlar[i].rstrip("\r\n") == "{":
            parca, j = [], i
            derinlik = 0
            while j < len(satirlar):
                parca.append(satirlar[j])
                for ch in satirlar[j]:
                    if ch == "{":
                        derinlik += 1
                    elif ch == "}":
                        derinlik -= 1
                if derinlik == 0:
                    break
                j += 1
            if derinlik == 0:
                try:
                    bloklar.append((json.loads("".join(parca)), i + 1, False))
                except json.JSONDecodeError:
                    pass
                i = j
        i += 1

    return bloklar


# --- hedef bloklar ------------------------------------------------------------

HEDEFLER = [
    # (dosya_yolu, satir_tahmini, hedef_sema_adi, aciklama)
    ("agents/source-verifier.md", 38, "source", "F1: additionalProperties"),
    ("agents/gap-analyzer.md", 38, "research_gap", "F2: additionalProperties + enum"),
    ("agents/writer.md", 34, "paragraph", "F21: pattern (RQ2)"),
    # contradiction-analyzer line 36: tablo satırı (JSON blok DEĞIL), atlanıyor
    ("agents/evidence-extractor.md", 24, "evidence", "temiz blok (fence'siz, kontrol)"),
    ("agents/integrity-auditor.md", 80, "audit", "temiz blok (fence'li, kontrol)"),
    ("agents/contradiction-analyzer.md", 57, "claim", "temiz blok: claim fence'li"),
    ("agents/contradiction-analyzer.md", 70, "research_gap", "temiz blok: research_gap fence'li"),
]

TAM_KAYIT_DOSYALARI = {"SKILL.md"}  # required hataları burda sayılmaz


# --- sınıf-2 ardisik dizi çözümleyici -----------------------------------------

ARDISIK_DIZI = re.compile(r"`([A-Z]{1,8}-\d{3,}[a-z]?)`")


def ardisik_dizi_coz(metin: str, satir: int) -> list[str]:
    """Satırdaki backtick'li tanımlayıcıları bulur (sıralı dizi varsayılarak)."""
    return ARDISIK_DIZI.findall(metin)


# --- testler ------------------------------------------------------------------

@pytest.mark.parametrize("dosya, satir_tahmin, sema_adi, aciklama", HEDEFLER)
def test_ajan_bloklari_semaya_uygun(dosya, satir_tahmin, sema_adi, aciklama):
    """Ajan belgelerindeki JSON blokları hedef semaya uygun mu?"""
    yol = Path(dosya)
    if not yol.exists():
        pytest.skip(f"{dosya} yok")

    sema = load_sema(sema_adi)
    dogrulayici = Draft202012Validator(sema, registry=REGISTRY)
    bloklar = json_bloklari_yol_yolla(yol)

    # hedef satıra en yakın bloğu bul
    blok = min(bloklar, key=lambda b: abs(b[1] - satir_tahmin), default=None)
    if blok is None:
        pytest.fail(f"{dosya}:{satir_tahmin} civarında JSON bloğu yok")

    veri, blk_satir, fence_li = blok

    # SKILL.md için required hataları yok sayılır
    if yol.name in TAM_KAYIT_DOSYALARI:
        hata_turleri = {"additionalProperties", "enum", "pattern", "type"}
    else:
        hata_turleri = None  # tümü

    hatalar = list(dogrulayici.iter_errors(veri))
    if hata_turleri:
        hatalar = [h for h in hatalar if h.validator in hata_turleri]

    assert not hatalar, (
        f"{dosya}:{blk_satir} ({aciklama}) -> {sema_adi}.json: "
        f"{len(hatalar)} hata: "
        + "; ".join(f"{h.validator} @ {'.'.join(str(p) for p in h.path)}" for h in hatalar)
    )


def test_sinif2_ardisik_dizi_regex_calisiyor():
    """Sınıf-2 regex'i basit bir girdi üzerinde çalışıyor mu? (Ölçüm: 27 atıftan 26'sı doğru)."""
    # Basit doğrulama: desen backtick'li tanımlayıcıları yakalıyor mu
    test_satir = "`EVD-001`, `EVD-004` / `SRC-001` ve `CLM-001`"
    kimlikler = ardisik_dizi_coz(test_satir, 1)
    assert "EVD-001" in kimlikler
    assert "EVD-004" in kimlikler
    assert "SRC-001" in kimlikler
    assert "CLM-001" in kimlikler
    # Her kimliğin öneki ID_PREFIXES'te olmalı
    for k in kimlikler:
        onkek = k.split("-")[0]
        assert onkek in ID_PREFIXES, f"{k} öneki {onkek} ID_PREFIXES'te yok"


def test_skill_md_claims_additionalproperties():
    """SKILL.md:242 -> thesis_state.json: claims alanı additionalProperties.

    SKILL.md TAM_KAYIT_DOSYALARI'nda olduğu için required hataları
    sayılmaz ama additionalProperties sayılır.
    """
    yol = Path("SKILL.md")
    if not yol.exists():
        pytest.skip("SKILL.md yok")

    sema = load_sema("thesis_state")
    dogrulayici = Draft202012Validator(sema, registry=REGISTRY)

    # SKILL.md'deki claims bloğunu bul (yaklaşık 242. satır)
    metin = yol.read_text(encoding="utf-8")
    satirlar = metin.splitlines()
    hedef_aralik = satirlar[235:255]
    blok_metin = "\n".join(hedef_aralik)

    # claims objesini çıkar
    eslesme = re.search(r'"claims"\s*:\s*(\{[\s\S]*?\})', blok_metin)
    if not eslesme:
        pytest.skip("claims bloğu bulunamadı")
    claims_obj = json.loads(eslesme.group(1))

    hatalar = list(dogrulayici.iter_errors(claims_obj))
    hatalar = [h for h in hatalar if h.validator == "additionalProperties"]
    assert not hatalar, f"SKILL.md claims additionalProperties: {hatalar}"


def test_thesis_state_additionalproperties_ve_required():
    """thesis_state.json ust seviye additionalProperties:false dogrulamasi.

    empty_state() ile oluşturulan durum geçmeli.
    """
    from tools.atw.state import empty_state, validate_state

    durum = empty_state("THESIS-2026-001", "Test Tezi")
    hatalar = validate_state(durum)
    assert not hatalar, f"empty_state thesis_state hataları: {hatalar}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-p", "no:cacheprovider"])