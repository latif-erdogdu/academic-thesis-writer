# P0-1 Çekirdek ve Veri Modeli Implementation Plan

> **Ajanik çalışanlar için:** ZORUNLU ALT-SKILL: Bu planı görev görev uygulamak için `superpowers:subagent-driven-development` (önerilir) veya `superpowers:executing-plans` kullanılmalıdır. Adımlar `- [ ]` onay kutusu sözdizimiyle izlenir.

**Goal:** Repo'yu gerçek çalışan bir veri modeli ve Python çekirdeği ile donatmak: 18 geçerli JSON şema, çalışan `pytest` altyapısı, fixture seti, 10 ajan ve 7 referans dosyası.

**Architecture:** Kalıcı varlıkların tek doğruluk kaynağı JSON Schema'dır (`schemas/*.json`, draft 2020-12). Python tarafında şemaların kopyası tutulmaz; `tools/atw/` yalnızca kimlik üretimi, şema yükleme/kaydetme ve çalışma-zamanı (state'e yazılmayan) tipler sağlar. `thesis_state.json` diğer şemalara `$ref` ile bağlanır, böylece registry alanları gerçek bir grafiğe dönüşür.

**Tech Stack:** Python 3.12, `jsonschema>=4.22` (referencing dahil), `pytest>=8.0`, `pytest-cov>=5.0`

**Spec:** `docs/superpowers/specs/2026-09-26-academic-thesis-writer-p0-design.md`

## Global Constraints

- **Dil:** Tüm `.md` dosyaları, docstring'ler, commit mesajları ve CLI çıktıları Türkçe. Kod tanımlayıcıları (değişken, fonksiyon, sınıf adları) İngilizce kalır.
- **Sürüm ibaresi yasağı:** Hiçbir dosyada veya commit mesajında `V1` / `V2` / `v2` / `v3` yazılmayacak. `schema_version` alanı ilk gerçek şema olduğu için değeri `"1.0"`'dır; sürüm soyutlaması veya "yeni nesil" anlatısı kullanılmayacaktır.
- **Uydurma veri yasağı:** Fixture'lardaki kaynak kimlikleri gerçek DOI'ler olmayacak; `10.5555/` önekli kurgusal DOI'ler kullanılacak ve dosya adında/üst yorumunda kurgusal olduğu açıkça yazılacak. Fixture metinlerinde geçen yazar adları kurgusaldır.
- **Kütüphane sınırı:** P0'da yalnızca `jsonschema`, `pytest`, `pytest-cov`. HTTP, PDF ve OCR kütüphaneleri Plan 2 ve Plan 3'te eklenir; bu planda `requirements.txt`'e yazılmaz.
- **Şema standardı:** Tüm şemalar `https://json-schema.org/draft/2020-12/schema` uyumlu, `$id` alanı `https://github.com/latif-erdogdu/academic-thesis-writer/schemas/<dosya>.json` biçiminde.
- **Kimlik biçimi:** `<PREFIX>-<NNN>`, üç haneli sıfır dolgulu, 999'u aşarsa genişler (`SRC-1000`). Prefiksler: `SRC`, `EVD`, `CLM`, `CIT`, `P`, `RQ`, `HYP`, `FND`, `DSC`, `CON`, `GAP`, `AUD`, `SEARCH`, `DS`, `ANL`, `STAT`, `TBL`, `FIG`.
- **Git:** Her adım sonunda commit. `main` dalına doğrudan commit; dal açma, rebase veya squash kullanma.

## Review Focus

Spec'in ima ettiği ama hiçbir görevin testlerinin doğrudan hedeflemediği, bir insanın bu yazılımı kullanırken en çok sıkıntı çekeceği beş girdi sınıfı:

1. **Çapraz dil diyakritik uyuşmazlığı** — "Çobanoğlu" / "Cobanoglu" gibi Türkçe kaynak başlıklarında büyük/küçük harf ve diyakritik farkı, başlık eşleştirmesini yanlış-negatif yapıp doğrulanmış kaynağı "eşleşmedi" diye reddetmemeli.
2. **Kısmi şema uyumu** — `src` alanı olmayan ama `title`/`year` olan bir kayıt, şemayı geçmemeli; eksik zorunlu alan sessizce varsayılan doldurulmamalı.
3. **Kimlik çakışması** — Aynı kimlik iki farklı varlıkta kullanılırsa (iki `CLM-001`) sessizce üzerine yazılmamalı, çakışma hata olarak bildirilmeli.
4. **Askıda kalan referans** — `thesis_state.evidence_registry` içindeki bir `EVD-007` için `evidence.json`'da karşılığı yoksa bu kopuk bağ (dangling reference) tespit edilebilmeli.
5. **Onay durumu kalıcılığı** — Bir gate onaylandıktan sonra state kaydedilip yeniden yükendiğinde onay kaybolmamalı; `revoke` açıkça çağrılmadan sıfırlanmamalı.

Bu beş satırın her biri için sahibi olan göreve, o görevin kendi adım diliminde bir test eklendi.

## Spec'ten Sapmalar (gerekçeli)

| Spec | Bu plan | Gerekçe |
|------|----------|---------|
| `tools/atw/models.py` — "pydantic modelleri (şemaların karşılığı)" | `tools/atw/types.py` — çalışma-zamanı dataclass'ları | Kalıcı varlıkların doğruluk kaynağı JSON Schema olmalı. Aynı alanları pydantic'te ikinci kez tanımlamak iki kaynaklı gerçek üretir ve şema ile model arasında sessiz kayma olur. `types.py` yalnızca state'e yazılmayan ara sonuçları taşır. |
| `approval.py` içinde `async def request_approval(... await question(...))` | `approval.py` yalnızca onay **durumunu** yönetir; soru sorma ajana aittir | Python, OpenCode'un `question` aracını çağıramaz. Ajan `workflows/*.md` talimatını izleyerek soruyu kendisi sorar ve `grant()`/`revoke()` çağırır. Bu ayrım Plan 4'te uygulanır. |
| `"schema_version": "2.0"` | `"schema_version": "1.0"` | Repo'da önceki bir şema sürümü soyutlaması yok. Sürüm soyutlaması Global Constraints ile yasaklandı. |
| 7 mevcut şema JSON şablonu olarak kalır | Gerçek JSON Schema'ya dönüştürülür | Spec Faz 1 her şemanın `jsonschema` ile doğrulanmasını şart koşuyor. Şablon biçimi doğrulanamaz. |

---

## Dosya Haritası

| Dosya | Sorumluluk |
|------|------------|
| `requirements.txt` | Python bağımlılıkları (yalnızca bu planın ihtiyacı) |
| `pytest.ini` | pytest yapılandırması, `tests/` keşfi, canlı ağ testlerini varsayılan kapalı |
| `tools/__init__.py` | `tools` paket işaretçisi |
| `tools/atw/__init__.py` | Çekirdek paket; alt modülleri dışa açan yüzey |
| `tools/atw/ids.py` | Kimlik üretimi, ayrıştırma, doğrulama |
| `tools/atw/types.py` | State'e yazılmayan çalışma-zamanı dataclass'ları |
| `tools/atw/state.py` | Şema yükleme, state yükleme/kaydetme/doğrulama, kopuk referans tespiti |
| `schemas/*.json` (18 adet) | Kalıcı varlıkların tek doğruluk kaynağı |
| `tests/conftest.py` | Ortak fixture yükleyici ve şema yolu sabitleri |
| `tests/fixtures/*.json`, `sample_pdf.pdf` | Sınır durum örnekleri |
| `agents/contradiction-analyzer.md` | Çelişki tespiti ajanı |
| `agents/integrity-auditor.md` | Bütünlük denetimi ajanı |
| `references/systematic_review_protocol.md` | PRISMA temelli protokol |
| `references/methodology_rules.md` | Yöntem denetim kuralları |
| `SKILL.md` | 10 ajan + 7 referans yönlendirme tablosu |
| `.opencode/skill/academic-thesis-writer/` | Kök dosyaların senkron kopyası |

---

## Task 1: Python İskeleti ve Kimlik Üretimi

**Files:**
- Create: `requirements.txt`
- Create: `pytest.ini`
- Create: `tools/__init__.py`
- Create: `tools/atw/__init__.py`
- Create: `tools/atw/ids.py`
- Create: `tests/conftest.py`
- Create: `tests/schema_tests/__init__.py`
- Create: `tests/schema_tests/test_ids.py`

**Interfaces:**
- Consumes: yok (bağımsız görev)
- Produces:
  - `tools.atw.ids.ID_PREFIXES: dict[str, str]` — 18 prefiks → varlık adı
  - `tools.atw.ids.IdError(ValueError)`
  - `tools.atw.ids.format_id(prefix: str, number: int) -> str`
  - `tools.atw.ids.parse_id(value: str) -> tuple[str, int]` — geçersizse `IdError`
  - `tools.atw.ids.is_valid_id(value: str) -> bool`
  - `tools.atw.ids.next_id(existing: Iterable[str], prefix: str) -> str`

- [ ] **Step 1: Bağımlılıkları ve pytest yapılandırmasını yaz**

`requirements.txt`:
```
jsonschema>=4.22.0
pytest>=8.0.0
pytest-cov>=5.0.0
```

`pytest.ini`:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -q --strict-markers
markers =
    live: Canli ag cagrisi gerektiren test (varsayilan olarak atlanir)
```

- [ ] **Step 2: Testleri yaz (önce test)**

`tests/conftest.py`:
```python
"""Ortak test yardimcilari."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = REPO_ROOT / "schemas"
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures"


@pytest.fixture(scope="session")
def schema_dir() -> Path:
    return SCHEMA_DIR


@pytest.fixture(scope="session")
def fixture_dir() -> Path:
    return FIXTURE_DIR


def load_fixture(name: str) -> dict:
    """tests/fixtures/<name> dosyasini sozluk olarak yukler."""
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
```

`tests/schema_tests/test_ids.py`:
```python
"""Kimlik uretimi ve dogrulama testleri."""
from __future__ import annotations

import pytest

from tools.atw.ids import (
    ID_PREFIXES,
    IdError,
    format_id,
    is_valid_id,
    next_id,
    parse_id,
)


def test_format_id_uc_hane_sifir_doldurur():
    assert format_id("SRC", 1) == "SRC-001"
    assert format_id("EVD", 42) == "EVD-042"
    assert format_id("SEARCH", 7) == "SEARCH-007"


def test_format_id_dokuz_yuz_dokuzu_agir_uzar():
    assert format_id("SRC", 1000) == "SRC-1000"


def test_format_id_alan_kisa_olsun():
    assert format_id("P", 3) == "P-003"


def test_parse_id_donus():
    assert parse_id("CLM-017") == ("CLM", 17)
    assert parse_id("SEARCH-001") == ("SEARCH", 1)
    assert parse_id("P-004") == ("P", 4)


def test_parse_id_hatali_girdide_hata_firlatir():
    for hatali in ["CLM17", "CLM-", "-017", "clm-017", "CLM-17a", "CLM-1.7"]:
        with pytest.raises(IdError):
            parse_id(hatali)


def test_is_valid_id_alan_ayirt_edici_degil():
    assert is_valid_id("SRC-001") is True
    assert is_valid_id("XXX-001") is False  # bilinmeyen prefiks
    assert is_valid_id("SRC-1") is False  # iki hane yetersiz
    assert is_valid_id("") is False


def test_id_prefixes_onsekiz_ogeyi_kapsar():
    assert len(ID_PREFIXES) == 18
    for beklenen in ["SRC", "EVD", "CLM", "CIT", "P", "RQ", "HYP", "FND",
                     "DSC", "CON", "GAP", "AUD", "SEARCH", "DS", "ANL",
                     "STAT", "TBL", "FIG"]:
        assert beklenen in ID_PREFIXES


def test_next_id_bos_listeden_baslar():
    assert next_id([], "SRC") == "SRC-001"


def test_next_id_en_yuksek_kimlikten_devam_eder():
    mevcut = ["SRC-001", "SRC-002", "SRC-009", "SRC-010"]
    assert next_id(mevcut, "SRC") == "SRC-011"


def test_next_id_karisik_kimlikleri_yoksayarak_ilerler():
    # CLM-005 varken SRC sayaci bundan etkilenmemeli
    assert next_id(["SRC-001", "CLM-005"], "SRC") == "SRC-002"


def test_next_id_bilinmeyen_prefiks_hata_firlatir():
    with pytest.raises(IdError):
        next_id([], "XXX")


# Review Focus 3: ayni kimligin iki varlikta kullanilmasi sessizce
# uzerine yazilmamali; next_id bunu bir sonraki bos yere kaydirarak
# fark edilebilir kilar.
def test_next_id_cakisan_kimligi_atlar():
    # SRC-001 iki kez geciyor: sonraki kimlik SRC-002 olmali, SRC-001 degil
    assert next_id(["SRC-001", "SRC-001"], "SRC") == "SRC-002"
```

- [ ] **Step 3: Testleri çalıştır, başarısız olduğunu doğrula**

Run: `python -m pytest tests/schema_tests/test_ids.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools'`

- [ ] **Step 4: Paket işaretçilerini ve `ids.py` dosyasını yaz**

`tools/__init__.py`:
```python
"""Akademik tez yazici araclari."""
```

`tools/atw/__init__.py`:
```python
"""Ortak cekirdek: kimlik, tip, durum ve onay yonetimi.

Disa aktarilan yuzey:

- ``tools.atw.ids``      -- kimlik uretimi ve dogrulama
- ``tools.atw.types``    -- calisma-zamani tipleri
- ``tools.atw.state``    -- sema yukleme, durum kaydetme/dogrulama
- ``tools.atw.approval`` -- insan onay kapilari
"""
from __future__ import annotations

from tools.atw import approval, ids, state, types

__all__ = ["approval", "ids", "state", "types"]
```

> Not: `__init__.py` bu noktada `approval` ve `types` modüllerini içe aktarır.
> Task 2, 3, 5 onları oluşturuncaya kadar bu satır `ModuleNotFoundError`
> verir. Bu nedenle `__init__.py` **boş bırakılır** ve içe aktarma
> ayrı bir göreve bırakılır (Task 5, adım 5). Aşağıdaki kod yorum
> satırlarıyla birlikte yazılır ve son görevde etkinleştirilir.

`tools/atw/__init__.py` (yazılacak hâli):
```python
"""Ortak cekirdek: kimlik, tip, durum ve onay yonetimi.

Disa aktarilan yuzey:

- ``tools.atw.ids``      -- kimlik uretimi ve dogrulama
- ``tools.atw.types``    -- calisma-zamani tipleri
- ``tools.atw.state``    -- sema yukleme, durum kaydetme/dogrulama
- ``tools.atw.approval`` -- insan onay kapilari
"""
from __future__ import annotations

__all__ = ["approval", "ids", "state", "types"]
```

`tools/atw/ids.py`:
```python
"""Tez varliklari icin kimlik uretimi, ayristirma ve dogrulama.

Kimlik bicimi: ``<PREFIX>-<NNN>`` (uc haneli sifir dolgulu).
999'u asan sayaclar genisler: ``SRC-1000``.
"""
from __future__ import annotations

import re
from typing import Final, Iterable

ID_PREFIXES: Final[dict[str, str]] = {
    "SRC": "source",
    "EVD": "evidence",
    "CLM": "claim",
    "CIT": "citation",
    "P": "paragraph",
    "RQ": "research_question",
    "HYP": "hypothesis",
    "FND": "finding",
    "DSC": "discussion",
    "CON": "conclusion",
    "GAP": "research_gap",
    "AUD": "audit",
    "SEARCH": "search_run",
    "DS": "dataset",
    "ANL": "analysis",
    "STAT": "statistic",
    "TBL": "table",
    "FIG": "figure",
}

_ID_PATTERN: Final = re.compile(r"^(?P<prefix>[A-Z]+)-(?P<number>\d{3,})$")
_HANE_SAYISI: Final = 3


class IdError(ValueError):
    """Gecersiz kimlik bicimi veya bilinmeyen prefiks."""


def format_id(prefix: str, number: int) -> str:
    """Prefiks ve sayiyi kimlik metnine cevirir.

    Args:
        prefix: ``ID_PREFIXES`` icindeki bir prefiks.
        number: Sifirdan buyuk tam sayi.

    Returns:
        ``SRC-001`` biciminde kimlik.

    Raises:
        IdError: Prefiks bilinmiyorsa veya sayi gecersizse.
    """
    if prefix not in ID_PREFIXES:
        raise IdError(f"Bilinmeyen prefiks: {prefix!r}")
    if not isinstance(number, int) or isinstance(number, bool):
        raise IdError(f"Sayi tam sayi olmali: {number!r}")
    if number < 0:
        raise IdError(f"Sayi negatif olamaz: {number!r}")
    return f"{prefix}-{number:0{_HANE_SAYISI}d}"


def parse_id(value: str) -> tuple[str, int]:
    """Kimlik metnini ``(prefiks, sayi)`` ciftine ayristirir.

    Raises:
        IdError: Bicim hataliysa veya prefiks bilinmiyorsa.
    """
    if not isinstance(value, str):
        raise IdError(f"Kimlik metin olmali: {value!r}")
    eslesme = _ID_PATTERN.match(value)
    if eslesme is None:
        raise IdError(f"Bicim hatali kimlik: {value!r}")
    prefiks = eslesme.group("prefix")
    if prefiks not in ID_PREFIXES:
        raise IdError(f"Bilinmeyen prefiks: {value!r}")
    return prefiks, int(eslesme.group("number"))


def is_valid_id(value: str) -> bool:
    """Kimligin bicim ve prefiks kurallarina uyup uymadigini bildirir."""
    try:
        parse_id(value)
    except IdError:
        return False
    return True


def next_id(existing: Iterable[str], prefix: str) -> str:
    """Verilen kimlikler arasindan sonraki bos numarayi uretir.

    Args:
        existing: Var olan kimlikler (``"SRC-003"`` gibi). Hatali bicimli
            girdiler sessizce yok sayilir.
        prefix: Hedef prefiks.

    Returns:
        Bir sonraki kullanilabilir kimlik, orn. ``"SRC-004"``.

    Raises:
        IdError: Prefiks bilinmiyorsa.

    Examples:
        >>> next_id(["SRC-001", "SRC-002", "SRC-009"], "SRC")
        'SRC-010'
    """
    if prefix not in ID_PREFIXES:
        raise IdError(f"Bilinmeyen prefiks: {prefix!r}")
    en_yuksek = 0
    for kimlik in existing:
        try:
            kimlik_prefiks, sayi = parse_id(kimlik)
        except IdError:
            continue
        if kimlik_prefiks == prefix and sayi > en_yuksek:
            en_yuksek = sayi
    return format_id(prefix, en_yuksek + 1)
```

- [ ] **Step 5: Testleri çalıştır, geçtiğini doğrula**

Run: `python -m pytest tests/schema_tests/test_ids.py -v`
Expected: PASS — 12 test

- [ ] **Step 6: Commit**

```bash
git add requirements.txt pytest.ini tools/__init__.py tools/atw/__init__.py tools/atw/ids.py tests/conftest.py tests/schema_tests/
git commit -m "feat: kimlik uretimi cekirdegi, pytest altyapisi ve ortak test yardimcilari"
```

---

## Task 2: Çalışma-Zamanı Tipleri

**Files:**
- Create: `tools/atw/types.py`
- Create: `tests/schema_tests/test_types.py`

**Interfaces:**
- Consumes: `tools.atw.ids.is_valid_id` (Task 1)
- Produces:
  - `tools.atw.types.PageText(page: int, text: str, sections: list[str])`
  - `tools.atw.types.Passage(source_id: str, page: int, section: str, text: str, char_start: int, char_end: int)`
  - `tools.atw.types.SourceCandidate(doi: str | None, title: str, authors: list[str], year: int | None, source_type: str | None)`
  - `tools.atw.types.VerificationResult(...)` — 12 alan
  - `tools.atw.types.EvidenceDraft(source_id: str, location: dict, text: str, evidence_type: str, strength: str)`
  - `tools.atw.types.Location(page: int | None, section: str, paragraph: int | None)`
  - `TypeError` yerine yerleşik `ValueError` kullanılır (kimlik doğrulaması için)

- [ ] **Step 1: Testleri yaz**

`tests/schema_tests/test_types.py`:
```python
"""Calisma-zamani tiplerinin dogrulama davranisi testleri."""
from __future__ import annotations

import pytest

from tools.atw.types import (
    EVIDENCE_TYPES,
    STRENGTHS,
    VERIFICATION_STATUSES,
    EvidenceDraft,
    Location,
    PageText,
    Passage,
    SourceCandidate,
    VerificationResult,
)


def test_page_text_alanlari():
    sayfa = PageText(page=3, text="icerik", sections=["Giris"])
    assert sayfa.page == 3
    assert sayfa.sections == ["Giris"]


def test_passage_kimlik_dogrulaması_yapar():
    gecerli = Passage(
        source_id="SRC-001", page=17, section="3.2",
        text="X yontemi basariyi %23 artirmaktadir.",
        char_start=1204, char_end=1250,
    )
    assert gecerli.source_id == "SRC-001"
    assert gecerli.page == 17


def test_passage_gecersiz_kimlikte_hata_firlatir():
    with pytest.raises(ValueError):
        Passage(
            source_id="kaynak1", page=1, section="",
            text="x", char_start=0, char_end=1,
        )


def test_passage_karakter_araligi_tersten_olamaz():
    with pytest.raises(ValueError):
        Passage(
            source_id="SRC-001", page=1, section="",
            text="x", char_start=50, char_end=10,
        )


def test_source_candidate_doi_ve_yil_istege_bagli():
    aday = SourceCandidate(doi=None, title="Baslik", authors=[], year=None, source_type=None)
    assert aday.doi is None
    assert aday.year is None


def test_source_candidate_doi bicimi_kontrol_edilir():
    with pytest.raises(ValueError):
        SourceCandidate(
            doi="10.1234/abcd", title="Baslik", authors=[], year=2024,
            source_type="article",
        )  # eksik sonuclu DOI


def test_verification_result_gecerli_durum_kabul_eder():
    sonuc = VerificationResult(
        status="verified", bibliographic_match=0.95,
        doi_match=True, author_match=True, title_match=True,
        year_match=True, journal_match=True,
        retraction_status="not_retracted", correction_status="none",
        supersedes=None, verified_at="2026-09-26T10:00:00Z",
        verification_sources=["crossref", "openalex"],
    )
    assert sonuc.status == "verified"
    assert sonuc.verification_sources == ["crossref", "openalex"]


def test_verification_result_gecersiz_durum_reddeder():
    with pytest.raises(ValueError):
        VerificationResult(
            status="oldu", bibliographic_match=0.9,
            doi_match=True, author_match=True, title_match=True,
            year_match=True, journal_match=True,
            retraction_status="not_retracted", correction_status="none",
            supersedes=None, verified_at="2026-09-26T10:00:00Z",
            verification_sources=["crossref"],
        )


def test_verification_result_en_az_iki_kaynak_zorunlu():
    with pytest.raises(ValueError):
        VerificationResult(
            status="verified", bibliographic_match=0.9,
            doi_match=True, author_match=True, title_match=True,
            year_match=True, journal_match=True,
            retraction_status="not_retracted", correction_status="none",
            supersedes=None, verified_at="2026-09-26T10:00:00Z",
            verification_sources=["crossref"],  # yalniz bir kaynak
        )


def test_verification_result_geri_caledilen_durum_en_az_iki_kaynak_ister():
    # Retraksiyon tespiti tek kaynaktan da anlamli olabilir, bu durumda
    # en az iki kaynak kurali gevser.
    sonuc = VerificationResult(
        status="retracted", bibliographic_match=1.0,
        doi_match=True, author_match=True, title_match=True,
        year_match=True, journal_match=True,
        retraction_status="retracted", correction_status="none",
        supersedes=None, verified_at="2026-09-26T10:00:00Z",
        verification_sources=["crossref"],
    )
    assert sonuc.status == "retracted"


def test_verification_result_eskisletme_zorunlu():
    with pytest.raises(ValueError):
        VerificationResult(
            status="verified", bibliographic_match=0.4,  # esik alti
            doi_match=True, author_match=False, title_match=False,
            year_match=True, journal_match=False,
            retraction_status="not_retracted", correction_status="none",
            supersedes=None, verified_at="2026-09-26T10:00:00Z",
            verification_sources=["crossref", "openalex"],
        )


def test_evidence_draft_kimlik_ve_enum_dogrulaması():
    taslak = EvidenceDraft(
        source_id="SRC-014", location={"page": 17, "section": "3.2", "paragraph": None},
        text="X yontemi basariyi %23 artirmaktadir.",
        evidence_type="finding", strength="direct",
    )
    assert taslak.source_id == "SRC-014"
    assert "finding" in EVIDENCE_TYPES
    assert "direct" in STRENGTHS


def test_evidence_draft_gecersiz_tip_reddedilir():
    with pytest.raises(ValueError):
        EvidenceDraft(
            source_id="SRC-014", location={"page": 17, "section": "", "paragraph": None},
            text="x", evidence_type="varsayim", strength="direct",
        )


def test_location_alanlari():
    konum = Location(page=17, section="3.2", paragraph=None)
    assert konum.page == 17
    assert konum.as_dict() == {"page": 17, "section": "3.2", "paragraph": None}


# Review Focus 1: Turkce kaynak basliklarindaki diyakritik ve buyuk/kucuk
# harf farki kayit olustururken reddedilmemeli.
def test_source_candidate_turkce_basligini_kabul_eder():
    aday = SourceCandidate(
        doi=None, title="Çobanoğlu ve Yılmaz'ın Deneyimi",
        authors=["Çobanoğlu, A.", "Yılmaz, B."], year=2024, source_type="article",
    )
    assert aday.title.startswith("Ç")


def test_enum_kumeleri_bos_degil():
    assert len(VERIFICATION_STATUSES) >= 5
    assert len(EVIDENCE_TYPES) >= 5
    assert set(STRENGTHS) == {"direct", "indirect"}
```

- [ ] **Step 2: Testleri çalıştır, başarısız olduğunu doğrula**

Run: `python -m pytest tests/schema_tests/test_types.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.atw.types'`

- [ ] **Step 3: `types.py` dosyasını yaz**

`tools/atw/types.py`:
```python
"""State'e yazilmayan calisma-zamani tipleri.

Bu tipler arac zincirinin ara sonuclarini tasiyan gecici nesnelerdir;
kalici varliklar ``schemas/*.json`` ve ``thesis_state`` icinde yasar.
Burada tanimlanan alanlar o yuzda JSON Schema ile tekrar tanimlanmaz.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Final

from tools.atw.ids import is_valid_id

VERIFICATION_STATUSES: Final[tuple[str, ...]] = (
    "verified", "unverified", "pending", "retracted", "corrected",
)

EVIDENCE_TYPES: Final[tuple[str, ...]] = (
    "finding", "method", "theory", "data", "statistical", "primary_data",
)

STRENGTHS: Final[tuple[str, ...]] = ("direct", "indirect")

EN_AZ_BAGIMSIZ_KAYNAK: Final = 2
ESIK_ESLESME: Final = 0.60

_DOI_PATTERN: Final = re.compile(r"^10\.\d{4,9}/\S+$")


@dataclass(frozen=True)
class Location:
    """Kanitin kaynak icindeki konumu."""

    page: int | None = None
    section: str = ""
    paragraph: int | None = None

    def as_dict(self) -> dict:
        return {"page": self.page, "section": self.section, "paragraph": self.paragraph}


@dataclass
class PageText:
    """Bir PDF sayfasinin cikarilan metni ve basliklari."""

    page: int
    text: str
    sections: list[str] = field(default_factory=list)


@dataclass
class Passage:
    """Sayfa icinde konumlandirilmis tek bir kanit parcasi."""

    source_id: str
    page: int
    section: str
    text: str
    char_start: int
    char_end: int

    def __post_init__(self) -> None:
        if not is_valid_id(self.source_id):
            raise ValueError(f"Gecersiz kaynak kimligi: {self.source_id!r}")
        if self.char_start < 0 or self.char_end < 0:
            raise ValueError("Karakter konumlari negatif olamaz")
        if self.char_end < self.char_start:
            raise ValueError(
                f"char_end ({self.char_end}) char_start'tan "
                f"kucuk olamaz ({self.char_start})"
            )


@dataclass
class SourceCandidate:
    """Dogrulanmamis bir kaynak adayi."""

    doi: str | None
    title: str
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    source_type: str | None = None

    def __post_init__(self) -> None:
        if self.doi is not None and not _DOI_PATTERN.match(self.doi):
            raise ValueError(f"Bicimsiz DOI: {self.doi!r}")


@dataclass
class VerificationResult:
    """Bir kaynak adayinin dogrulama sonucu."""

    status: str
    bibliographic_match: float
    doi_match: bool
    author_match: bool
    title_match: bool
    year_match: bool
    journal_match: bool
    retraction_status: str
    correction_status: str
    supersedes: str | None
    verified_at: str
    verification_sources: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.status not in VERIFICATION_STATUSES:
            raise ValueError(
                f"Bilinmeyen dogrulama durumu: {self.status!r}. "
                f"Izin verilenler: {list(VERIFICATION_STATUSES)}"
            )
        if not 0.0 <= self.bibliographic_match <= 1.0:
            raise ValueError(
                f"bibliographic_match 0-1 araliginda olmali: "
                f"{self.bibliographic_match}"
            )
        if self.status in ("verified", "corrected"):
            if self.bibliographic_match < ESIK_ESLESME:
                raise ValueError(
                    f"Durum {self.status!r} iken eslesme esigin altinda: "
                    f"{self.bibliographic_match} < {ESIK_ESLESME}"
                )
            if len(self.verification_sources) < EN_AZ_BAGIMSIZ_KAYNAK:
                raise ValueError(
                    f"{self.status!r} icin en az {EN_AZ_BAGIMSIZ_KAYNAK} "
                    f"bagimsiz kaynak gerekli, verilen: "
                    f"{self.verification_sources}"
                )


@dataclass
class EvidenceDraft:
    """Kanit cikarimindan hemen sonraki, henuz kaydedilmemis kanit."""

    source_id: str
    location: dict
    text: str
    evidence_type: str
    strength: str

    def __post_init__(self) -> None:
        if not is_valid_id(self.source_id):
            raise ValueError(f"Gecersiz kaynak kimligi: {self.source_id!r}")
        if self.evidence_type not in EVIDENCE_TYPES:
            raise ValueError(
                f"Bilinmeyen kanit tipi: {self.evidence_type!r}. "
                f"Izin verilenler: {list(EVIDENCE_TYPES)}"
            )
        if self.strength not in STRENGTHS:
            raise ValueError(
                f"Bilinmeyen kanit gucu: {self.strength!r}. "
                f"Izin verilenler: {list(STRENGTHS)}"
            )
```

- [ ] **Step 4: Testleri çalıştır, geçtiğini doğrula**

Run: `python -m pytest tests/schema_tests/test_types.py -v`
Expected: PASS — 16 test

- [ ] **Step 5: Commit**

```bash
git add tools/atw/types.py tests/schema_tests/test_types.py
git commit -m "feat: calisma-zamani tipleri (PageText, Passage, SourceCandidate, VerificationResult, EvidenceDraft)"
```

---

## Task 3: thesis_state Şeması ve Durum Yönetimi

**Files:**
- Create: `schemas/thesis_state.json` (mevcut dosya tamamen değiştirilir)
- Create: `tools/atw/state.py`
- Create: `tests/schema_tests/test_thesis_state_schema.py`

**Interfaces:**
- Consumes: `tools.atw.ids.ID_PREFIXES` (Task 1)
- Produces:
  - `tools.atw.state.SCHEMA_DIR: Path`
  - `tools.atw.state.APPROVAL_GATES: list[str]` — 7 kapı adı
  - `tools.atw.state.schema_registry()` → `referencing.Registry`
  - `tools.atw.state.load_schema(name: str) -> dict`
  - `tools.atw.state.empty_state(thesis_id: str, title: str = "") -> dict`
  - `tools.atw.state.load_state(path: str | Path) -> dict`
  - `tools.atw.state.save_state(path: str | Path, state: dict) -> None`
  - `tools.atw.state.validate_state(state: dict) -> list[str]` — hata mesajları
  - `tools.atw.state.find_dangling_references(state: dict) -> list[str]` — kopuk bağlar

- [ ] **Step 1: Testleri yaz**

`tests/schema_tests/test_thesis_state_schema.py`:
```python
"""thesis_state semasi ve durum yonetimi testleri."""
from __future__ import annotations

import json

from jsonschema import Draft202012Validator

from tools.atw.state import (
    APPROVAL_GATES,
    empty_state,
    find_dangling_references,
    load_schema,
    save_state,
    validate_state,
)


def test_tum_semalar_draft_2020_12_uyumlu(schema_dir):
    for sema_dosyasi in sorted(schema_dir.glob("*.json")):
        sema = json.loads(sema_dosyasi.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(sema), sema_dosyasi.name


def test_sema_sayisi_onsekiz():
    from tools.atw.state import SCHEMA_DIR
    assert len(list(SCHEMA_DIR.glob("*.json"))) == 18


def test_her_semanin_id_alani_var(schema_dir):
    for sema_dosyasi in sorted(schema_dir.glob("*.json")):
        sema = json.loads(sema_dosyasi.read_text(encoding="utf-8"))
        assert sema.get("$id", "").endswith(sema_dosyasi.name), sema_dosyasi.name


def test_bos_durum_semayi_gecer():
    durum = empty_state("THESIS-2026-001", "Ornek Tez")
    assert validate_state(durum) == []


def test_bos_durum_zorunlu_alanlari_iceriyor():
    durum = empty_state("THESIS-2026-001")
    for alan in ["schema_version", "thesis_id", "language",
                 "human_approvals", "evidence_registry", "gap_registry"]:
        assert alan in durum


def test_onay_kapilari_yedi_adedir():
    assert len(APPROVAL_GATES) == 7
    assert APPROVAL_GATES[0] == "research_question"
    assert "final_thesis" in APPROVAL_GATES


def test_bos_durumda_hicbir_kapili_onalim_yok():
    durum = empty_state("THESIS-2026-001")
    assert all(deger is False for deger in durum["human_approvals"].values())


# Review Focus 2: eksik zorunlu alan sessizce varsayilan
# doldurulmamali, dogrulama hata vermeli.
def test_zorunlu_alan_eksikse_hata_verir():
    durum = empty_state("THESIS-2026-001")
    del durum["thesis_id"]
    hatalar = validate_state(durum)
    assert any("thesis_id" in hata for hata in hatalar)


def test_bilinmeyen_alan_reddedilir():
    durum = empty_state("THESIS-2026-001")
    durum["uydurma_alan"] = "deger"
    hatalar = validate_state(durum)
    assert any("uydurma_alan" in hata for hata in hatalar)


def test_sema_surumu_sabit():
    durum = empty_state("THESIS-2026-001")
    durum["schema_version"] = "2.0"
    hatalar = validate_state(durum)
    assert hatalar != []


def test_kimlik_bicimi_yanlis_kayit_reddedilir():
    durum = empty_state("THESIS-2026-001")
    durum["evidence_registry"].append({"id": "EVD-1"})  # iki hane yetersiz
    hatalar = validate_state(durum)
    assert hatalar != []


# Review Focus 4: registry'de olup kayit dosyasi olmayan varlik
# tespit edilebilmeli.
def test_kopuk_kanit_referansi_tespit_edilir():
    durum = empty_state("THESIS-2026-001")
    durum["evidence_registry"].append(
        {"id": "EVD-001", "source_id": "SRC-001", "location": {
            "page": 1, "section": "", "paragraph": None},
         "text": "x", "evidence_type": "finding",
         "supports_claim": None, "strength": "direct",
         "verified": False, "notes": ""}
    )
    kopuk = find_dangling_references(durum)
    assert any("EVD-001" in kopuk for kopuk in kopuk)


def test_kopuk_kanit_referansi_yoksa_bos_liste():
    durum = empty_state("THESIS-2026-001")
    assert find_dangling_references(durum) == []


def test_kaydet_yukle_gidis_donus(tmp_path):
    durum = empty_state("THESIS-2026-001", "Ornek Tez")
    durum["human_approvals"]["research_question"] = True
    yol = tmp_path / "durum.json"
    save_state(yol, durum)
    yuklenen = json.loads(yol.read_text(encoding="utf-8"))
    assert yuklenen["human_approvals"]["research_question"] is True


# Review Focus 5: onay durumu kaydedip yukleyince kaybolmamali.
def test_kaydet_yukle_onyan_korur(tmp_path):
    durum = empty_state("THESIS-2026-001")
    for kapili in ["research_question", "search_strategy", "methodology"]:
        durum["human_approvals"][kapili] = True
    yol = tmp_path / "durum.json"
    save_state(yol, durum)
    geri = validate_state(json.loads(yol.read_text(encoding="utf-8")))
    assert geri == []


def test_kaydet_bozuk_durumu_yazmaz(tmp_path):
    durum = empty_state("THESIS-2026-001")
    durum["schema_version"] = "bozuk"
    yol = tmp_path / "durum.json"
    try:
        save_state(yol, durum)
    except ValueError:
        pass
    else:
        raise AssertionError("save_state bozuk durumu yazmamaliydi")
    assert not yol.exists()


def test_sema_dosyasi_bulunamazsa_hata():
    try:
        load_schema("olmayan_sema.json")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Eksik sema icin FileNotFoundError bekleniyordu")
```

- [ ] **Step 2: Testleri çalıştır, başarısız olduğunu doğrula**

Run: `python -m pytest tests/schema_tests/test_thesis_state_schema.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.atw.state'`

- [ ] **Step 3: `thesis_state.json` şemasını yaz**

`schemas/thesis_state.json`:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/latif-erdogdu/academic-thesis-writer/schemas/thesis_state.json",
  "title": "Tez Durumu",
  "description": "Tezun butun varlik kayitlarini ve insan onay kapilarini tutan kok belge.",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "thesis_id",
    "language",
    "human_approvals",
    "evidence_registry",
    "claims_registry",
    "findings_registry",
    "discussion_registry",
    "conclusion_registry",
    "gap_registry",
    "audit_registry",
    "search_runs",
    "sources",
    "citations"
  ],
  "properties": {
    "schema_version": { "const": "1.0" },
    "thesis_id": { "type": "string", "minLength": 1 },
    "title": { "type": "string" },
    "field": { "type": "string" },
    "discipline": { "type": "string" },
    "degree": { "type": "string" },
    "language": { "type": "string", "default": "tr" },
    "research_problem": { "type": "string" },
    "purpose": { "type": "string" },
    "style_profile": { "type": "string" },
    "created_at": { "type": "string" },
    "updated_at": { "type": "string" },
    "version": { "type": "integer", "minimum": 1, "default": 1 },
    "research_questions": {
      "type": "array", "items": { "$ref": "research_question.json" }
    },
    "hypotheses": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "text", "status"],
        "properties": {
          "id": { "$ref": "#/$defs/id", "pattern": "^HYP-\\d{3,}$" },
          "text": { "type": "string", "minLength": 1 },
          "related_research_questions": {
            "type": "array", "items": { "type": "string", "pattern": "^RQ-\\d{3,}$" }
          },
          "status": { "enum": ["supported", "rejected", "pending"] },
          "finding_ids": {
            "type": "array", "items": { "type": "string", "pattern": "^FND-\\d{3,}$" }
          }
        }
      }
    },
    "conceptual_framework": { "type": "array", "items": { "type": "string" } },
    "methodology": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "design": { "type": "string" },
        "population": { "type": "string" },
        "sample": { "type": "string" },
        "sampling_method": { "type": "string" },
        "data_collection": { "type": "string" },
        "data_analysis": { "type": "string" }
      }
    },
    "chapters": { "type": "array", "items": { "type": "object" } },
    "evidence_registry": {
      "type": "array", "items": { "$ref": "evidence.json" }
    },
    "claims_registry": {
      "type": "array", "items": { "$ref": "claim.json" }
    },
    "findings_registry": {
      "type": "array", "items": { "$ref": "finding.json" }
    },
    "discussion_registry": {
      "type": "array", "items": { "$ref": "discussion.json" }
    },
    "conclusion_registry": {
      "type": "array", "items": { "$ref": "conclusion.json" }
    },
    "gap_registry": {
      "type": "array", "items": { "$ref": "research_gap.json" }
    },
    "audit_registry": {
      "type": "array", "items": { "$ref": "audit.json" }
    },
    "search_runs": {
      "type": "array", "items": { "$ref": "search_run.json" }
    },
    "sources": { "type": "array", "items": { "$ref": "source.json" } },
    "citations": { "type": "array", "items": { "$ref": "citation.json" } },
    "datasets": { "type": "array", "items": { "$ref": "dataset.json" } },
    "analyses": { "type": "array", "items": { "$ref": "analysis.json" } },
    "statistics": { "type": "array", "items": { "$ref": "statistic.json" } },
    "tables": { "type": "array", "items": { "$ref": "table.json" } },
    "figures": { "type": "array", "items": { "$ref": "figure.json" } },
    "definitions": { "type": "array", "items": { "type": "string" } },
    "variables": { "type": "array", "items": { "type": "object" } },
    "open_questions": { "type": "array", "items": { "type": "string" } },
    "quality_issues": { "type": "array", "items": { "type": "string" } },
    "human_approvals": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "research_question", "search_strategy", "source_set", "research_gap",
        "methodology", "findings", "final_thesis"
      ],
      "properties": {
        "research_question": { "type": "boolean", "default": false },
        "search_strategy": { "type": "boolean", "default": false },
        "source_set": { "type": "boolean", "default": false },
        "research_gap": { "type": "boolean", "default": false },
        "methodology": { "type": "boolean", "default": false },
        "findings": { "type": "boolean", "default": false },
        "final_thesis": { "type": "boolean", "default": false }
      }
    }
  },
  "$defs": {
    "id": { "type": "string", "pattern": "^[A-Z]+-\\d{3,}$" }
  }
}
```

> Bu şema `research_gap.json`, `finding.json`, `discussion.json`,
> `conclusion.json`, `search_run.json`, `citation.json`, `dataset.json`,
> `analysis.json`, `statistic.json`, `table.json`, `figure.json`
> dosyalarına `$ref` verir. Bu dosyalar **Task 6 ve Task 7**'de yazılır.
> Bu görevin testleri yalnızca `thesis_state` şemasını tek başına
> doğrular (`check_schema` göreli `$ref` çözümlemesi yapmaz), bu yüzden
> Task 6-7'den önce yeşildir. `test_bos_durum_semayi_gecer` ise
> `empty_state()` çıktısını doğrular; `empty_state` yalnızca boş
> diziler ürettiği için çözülmesi gereken `$ref` yoktur.

- [ ] **Step 4: `state.py` dosyasını yaz**

`tools/atw/state.py`:
```python
"""Sema yukleme, tez durumu yukleme/kaydetme ve dogrulama.

Kalici varliklarin tek dogruluk kaynagi ``schemas/*.json`` dosyalaridir.
Bu modul semalari yukler, ``thesis_state`` belgesini dogrular ve diskte
tutar. Semalarin Python karsiliklari burada tanimlanmaz.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

SCHEMA_DIR: Path = Path(__file__).resolve().parents[2] / "schemas"

APPROVAL_GATES: list[str] = [
    "research_question",
    "search_strategy",
    "source_set",
    "research_gap",
    "methodology",
    "findings",
    "final_thesis",
]

_STATE_IDENTITY = "id"

# Kopuk referans denetimi icin: registry adi -> kayitlarin tutuldugu alan
_REGISTRY_FIELDS: dict[str, str] = {
    "evidence_registry": "evidence",
    "claims_registry": "claim",
    "findings_registry": "finding",
    "discussion_registry": "discussion",
    "conclusion_registry": "conclusion",
    "gap_registry": "research_gap",
    "audit_registry": "audit",
    "search_runs": "search_run",
    "sources": "source",
    "citations": "citation",
    "datasets": "dataset",
    "analyses": "analysis",
    "statistics": "statistic",
    "tables": "table",
    "figures": "figure",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_schema(name: str) -> dict[str, Any]:
    """``schemas/<name>`` dosyasini sozluk olarak yukler.

    Raises:
        FileNotFoundError: Sema dosyasi yoksa.
        json.JSONDecodeError: Dosya gecerli JSON degilse.
    """
    yol = SCHEMA_DIR / name
    if not yol.is_file():
        raise FileNotFoundError(f"Sema dosyasi bulunamadi: {yol}")
    return json.loads(yol.read_text(encoding="utf-8"))


def schema_registry() -> Registry:
    """Tum semalarin ``$id`` degerleriyle kurulmus referans kaydi."""
    kaynaklar = []
    for yol in sorted(SCHEMA_DIR.glob("*.json")):
        sema = json.loads(yol.read_text(encoding="utf-8"))
        uri = sema.get("$id") or yol.as_uri()
        kaynaklar.append((uri, Resource.from_contents(sema)))
    return Registry().with_resources(kaynaklar)


def _state_validator() -> Draft202012Validator:
    return Draft202012Validator(load_schema("thesis_state.json"), registry=schema_registry())


def empty_state(thesis_id: str, title: str = "") -> dict[str, Any]:
    """Onaylanmamis, bos bir tez durumu olusturur."""
    simdi = _utc_now()
    return {
        "schema_version": "1.0",
        "thesis_id": thesis_id,
        "title": title,
        "language": "tr",
        "research_questions": [],
        "hypotheses": [],
        "conceptual_framework": [],
        "methodology": {},
        "chapters": [],
        "evidence_registry": [],
        "claims_registry": [],
        "findings_registry": [],
        "discussion_registry": [],
        "conclusion_registry": [],
        "gap_registry": [],
        "audit_registry": [],
        "search_runs": [],
        "sources": [],
        "citations": [],
        "datasets": [],
        "analyses": [],
        "statistics": [],
        "tables": [],
        "figures": [],
        "definitions": [],
        "variables": [],
        "open_questions": [],
        "quality_issues": [],
        "human_approvals": {kapili: False for kapili in APPROVAL_GATES},
        "style_profile": "apa7",
        "created_at": simdi,
        "updated_at": simdi,
        "version": 1,
    }


def validate_state(state: dict[str, Any]) -> list[str]:
    """Durumu semaya gore dogrular.

    Returns:
        Hata mesajlari listesi. Dokuman gecerliyse bos liste doner.
    """
    dogrulayici = _state_validator()
    hatalar = []
    for hata in sorted(dogrulayici.iter_errors(state), key=lambda e: list(e.absolute_path)):
        konum = "/".join(str(parca) for parca in hata.absolute_path) or "<kok>"
        hatalar.append(f"{konum}: {hata.message}")
    return hatalar


def find_dangling_references(state: dict[str, Any]) -> list[str]:
    """Registry alanlarindaki her kaydin ``<alan>_<id>`` iletisim kuralini denetler.

    Ornegin ``evidence_registry`` icindeki bir kaydin ``source_id`` degeri
    ``sources`` icinde bulunamazsa kopuk bag olarak bildirilir.
    """
    kopuk: list[str] = []
    for alan, varlik_adi in _REGISTRY_FIELDS.items():
        for kayit in state.get(alan, []) or []:
            if not isinstance(kayit, dict):
                continue
            kimlik = kayit.get(_STATE_IDENTITY)
            if not kimlik:
                continue
            for hedef_alan, hedef_adi in _REGISTRY_FIELDS.items():
                if hedef_alan == alan:
                    continue
                referans_alan = f"{hedef_adi}_id"
                referans = kayit.get(referans_alan)
                if not isinstance(referans, str):
                    continue
                mevcut = {
                    k.get(_STATE_IDENTITY)
                    for k in (state.get(hedef_alan) or [])
                    if isinstance(k, dict)
                }
                if referans not in mevcut:
                    kopuk.append(
                        f"{varlik_adi} {kimlik} -> {referans_alan}={referans} "
                        f"({hedef_adi} kaydi bulunamadi)"
                    )
    return kopuk


def load_state(path: str | Path) -> dict[str, Any]:
    """Durumu diskten okur ve dogrular.

    Raises:
        FileNotFoundError: Dosya yoksa.
        ValueError: Belge semaya uymuyorsa.
    """
    yol = Path(path)
    if not yol.is_file():
        raise FileNotFoundError(f"Durum dosyasi bulunamadi: {yol}")
    durum = json.loads(yol.read_text(encoding="utf-8"))
    hatalar = validate_state(durum)
    if hatalar:
        detay = "; ".join(hatalar[:5])
        raise ValueError(f"Durum semaya uymuyor ({len(hatalar)} hata): {detay}")
    return durum


def save_state(path: str | Path, state: dict[str, Any]) -> None:
    """Durumu dogrular ve diskte yazar.

    Dogrulama basarisizsa hicbir dosya yazilmaz.

    Raises:
        ValueError: Belge semaya uymuyorsa.
    """
    hatalar = validate_state(state)
    if hatalar:
        detay = "; ".join(hatalar[:5])
        raise ValueError(f"Durum semaya uymuyor ({len(hatalar)} hata): {detay}")
    yol = Path(path)
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
```

- [ ] **Step 5: Testleri çalıştır, geçtiğini doğrula**

Run: `python -m pytest tests/schema_tests/test_thesis_state_schema.py -v`
Expected: PASS — 15 test

> `test_sema_sayisi_onsekiz` bu noktada **başarısız olacaktır** (şu an 7 şema var).
> Bu test Task 7'ye kadar `xfail` bekliyor. Bunu geçici olarak
> `pytest.ini`'ye ekle:
> ```ini
> [pytest]
> markers =
>     live: Canli ag cagrisi gerektiren test
>     xfaz: Henuz yazilmamis fazin gorevine bagli test
> ```
> ve `test_sema_sayisi_onsekiz` fonksiyonunu su bicimde isaretle:
> ```python
> @pytest.mark.xfaz
> def test_sema_sayisi_onsekiz():
>     from tools.atw.state import SCHEMA_DIR
>     assert len(list(SCHEMA_DIR.glob("*.json"))) == 18
> ```
> `pytest.ini`'ye ek olarak `addopts` satirini guncelle:
> ```ini
> addopts = -q --strict-markers -m "not xfaz"
> ```
> Task 7'nin son adiminda bu isaret kaldirilir.

- [ ] **Step 6: Commit**

```bash
git add schemas/thesis_state.json tools/atw/state.py tests/schema_tests/test_thesis_state_schema.py pytest.ini
git commit -m "feat: thesis_state gercek JSON Schema ve durum yonetimi (kaydet/yukle/dogrula/kopuk referans)"
```

---

## Task 4: source, evidence, claim, paragraph, research_question, audit Şemaları

**Files:**
- Modify: `schemas/source.json`
- Modify: `schemas/evidence.json`
- Modify: `schemas/claim.json`
- Modify: `schemas/paragraph.json`
- Modify: `schemas/research_question.json`
- Modify: `schemas/audit.json`
- Create: `tests/schema_tests/test_core_schemas.py`

**Interfaces:**
- Consumes: `tools.atw.state.load_schema` (Task 3)
- Produces: 6 şema, hepsi draft 2020-12 uyumlu ve `$id` taşır.
  - `source.json` yeni alanlar: `publication_status`, `retraction_status`, `correction_status`, `supersedes_source_id`, `verification` (nesne), `evidence_ids`
  - `evidence.json` yeni alanlar: `evidence_type` genişletilir, `extracted_at`, `extraction_method`
  - `claim.json` yeni alanlar: `evidence_ids`, `contradicted_by`, `gap_ids`
  - `audit.json` yeni alan: `integrity_checks`

- [ ] **Step 1: Testleri yaz**

`tests/schema_tests/test_core_schemas.py`:
```python
"""Cekirdek varlik semalarinin dogrulama testleri."""
from __future__ import annotations

from jsonschema import Draft202012Validator

from tools.atw.state import schema_registry

_KAYIT_DEGIL = {"thesis_state.json"}


def _validator(dosya_adi: str) -> Draft202012Validator:
    import json
    from tools.atw.state import SCHEMA_DIR
    sema = json.loads((SCHEMA_DIR / dosya_adi).read_text(encoding="utf-8"))
    return Draft202012Validator(sema, registry=schema_registry())


def _gecerli_kayit(dosya_adi: str) -> dict:
    import json
    from tools.atw.state import SCHEMA_DIR
    sema = json.loads((SCHEMA_DIR / dosya_adi).read_text(encoding="utf-8"))
    ornek = sema.get("examples", [])
    assert ornek, f"{dosya_adi} icin ornek kayit tanimlanmali"
    return ornek[0]


def test_kayit_olmayan_semalar_ornek_tasiyor(schema_dir):
    for yol in sorted(schema_dir.glob("*.json")):
        if yol.name in _KAYIT_DEGIL:
            continue
        sema = __import__("json").loads(yol.read_text(encoding="utf-8"))
        assert sema.get("examples"), f"{yol.name} ornek kayit icermiyor"
        assert sema["examples"][0].get("$comment"), f"{yol.name} ornegi aciklamali"


def test_tum_ornek_kayitlar_ilgili_semayi_geceriyor(schema_dir):
    import json
    for yol in sorted(schema_dir.glob("*.json")):
        if yol.name in _KAYIT_DEGIL:
            continue
        dogrulayici = _validator(yol.name)
        for indeks, ornek in enumerate(json.loads(
                yol.read_text(encoding="utf-8"))["examples"]):
            hatalar = list(dogrulayici.iter_errors(ornek))
            assert hatalar == [], f"{yol.name} ornek[{indeks}]: {hatalar[0].message}"


def test_source_retraksiyon_alanlarini_taşıyor():
    sema = _gecerli_kayit("source.json")
    for alan in ["publication_status", "retraction_status",
                 "correction_status", "verification"]:
        assert alan in sema, alan


def test_source_retraksiyon_enum_degerleri():
    sema = _gecerli_kayit("source.json")
    assert sema["retraction_status"] == "not_retracted"


def test_source_geri_caledilen_kayit_reddedilir():
    dogrulayici = _validator("source.json")
    kayit = _gecerli_kayit("source.json")
    kayit["retraction_status"] = "belirsiz"
    assert list(dogrulayici.iter_errors(kayit)) != []


def test_source_doi_bicimsizse_reddedilir():
    dogrulayici = _validator("source.json")
    kayit = _gecerli_kayit("source.json")
    kayit["doi"] = "10.5555/bozuk-doi"
    assert list(dogrulayici.iter_errors(kayit)) != []


# Review Focus 1: Turkce diyakritikli baslik semada sorunsuz kabul edilmeli.
def test_source_turkce_baslik_ve_yazari_gecer():
    dogrulayici = _validator("source.json")
    kayit = _gecerli_kayit("source.json")
    kayit["title"] = "Türkiye'de Yükseköğretim ve Öğrenci Başarısı: Çobanoğlu Örneği"
    kayit["authors"] = ["Çobanoğlu, A.", "Yılmaz, B.", "Öztürk, Ç."]
    assert list(dogrulayici.iter_errors(kayit)) == []


def test_evidence_tipi_literature_ve_primary_data_ayirt_edir():
    sema = _gecerli_kayit("evidence.json")
    assert sema["evidence_type"] == "literature"
    dogrulayici = _validator("evidence.json")
    kayit = _gecerli_kayit("evidence.json")
    kayit["evidence_type"] = "primary_data"
    assert list(dogrulayici.iter_errors(kayit)) == []


def test_evidence_kanit_kaynagi_zorunlu():
    dogrulayici = _validator("evidence.json")
    kayit = _gecerli_kayit("evidence.json")
    del kayit["source_id"]
    assert list(dogrulayici.iter_errors(kayit)) != []


def test_claim_kanit_kimlikleri_dizisi_tasiyor():
    sema = _gecerli_kayit("claim.json")
    assert sema["evidence_ids"] == []
    dogrulayici = _validator("claim.json")
    kayit = _gecerli_kayit("claim.json")
    kayit["evidence_ids"] = ["EVD-001", "EVD-002"]
    assert list(dogrulayici.iter_errors(kayit)) == []


def test_claim_kanit_kimligi_bicimini_dogrular():
    dogrulayici = _validator("claim.json")
    kayit = _gecerli_kayit("claim.json")
    kayit["evidence_ids"] = ["kanit1"]
    assert list(dogrulayici.iter_errors(kayit)) != []


def test_paragraph_bos_denetimi():
    sema = _gecerli_kayit("paragraph.json")
    for alan in ["claims", "evidence", "sources", "research_questions"]:
        assert alan in sema, alan


def test_research_question_bulgu_baglantisi_tasiyor():
    sema = _gecerli_kayit("research_question.json")
    assert "finding_ids" in sema


def test_audit_butunluk_kontrolu_alani_tasiyor():
    sema = _gecerli_kayit("audit.json")
    assert "integrity_checks" in sema


def test_audit_gecersiz_tip_reddedilir():
    dogrulayici = _validator("audit.json")
    kayit = _gecerli_kayit("audit.json")
    kayit["audit_type"] = "integrity"
    assert list(dogrulayici.iter_errors(kayit)) != []


def test_tek_alanlik_sema_yok():
    """Yalnizca 'id' alani olan sema kabul edilmez."""
    import json
    from tools.atw.state import SCHEMA_DIR
    for yol in sorted(SCHEMA_DIR.glob("*.json")):
        if yol.name in _KAYIT_DEGIL:
            continue
        sema = json.loads(yol.read_text(encoding="utf-8"))
        alanlar = sema.get("properties", {})
        assert len(alanlar) >= 3, f"{yol.name} en az 3 alan tasimali, {len(alanlar)} var"
```

- [ ] **Step 2: Testleri çalıştır, başarısız olduğunu doğrula**

Run: `python -m pytest tests/schema_tests/test_core_schemas.py -v`
Expected: FAIL — `examples` alanı şemalarda yok

- [ ] **Step 3: `source.json` şemasını yaz**

`schemas/source.json`:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/latif-erdogdu/academic-thesis-writer/schemas/source.json",
  "title": "Kaynak",
  "description": "Dogrulanmis veya dogrulanmayi bekleyen bir bibliyografik kayit.",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "title", "source_type", "verification"],
  "examples": [
    {
      "$comment": "KURGUSAL ORNEK. Bu kayit gercek bir yayini temsil etmez; DOI, yazar ve yayinci bilgileri uydurmadir. Yalnizca sema dogrulamak icin kullanilir.",
      "id": "SRC-001",
      "title": "Kurgusal Bir Calisma Uzerine Bir Inceleme",
      "authors": ["Orman, A.", "Kaya, B."],
      "year": 2023,
      "journal": "Kurgusal Dergi",
      "publisher": "",
      "doi": "10.5555/kurgusal.ornek.2023.001",
      "url": "",
      "source_type": "article",
      "publication_status": "published",
      "retraction_status": "not_retracted",
      "correction_status": "none",
      "supersedes_source_id": null,
      "verified": true,
      "verification": {
        "status": "verified",
        "bibliographic_match": 0.96,
        "doi_match": true,
        "author_match": true,
        "title_match": true,
        "year_match": true,
        "journal_match": true,
        "verified_at": "2026-09-26T10:00:00+00:00",
        "verification_sources": ["crossref", "openalex"]
      },
      "verification_notes": "",
      "supports_claims": ["CLM-001"],
      "evidence_ids": ["EVD-001"],
      "page_numbers": null,
      "volume": "12",
      "issue": "3",
      "pages": "45-67",
      "edition": "",
      "isbn": "",
      "location_verified": true,
      "access_date": "2026-09-26",
      "language": "tr",
      "peer_reviewed": true
    }
  ],
  "properties": {
    "id": { "type": "string", "pattern": "^SRC-\\d{3,}$" },
    "title": { "type": "string", "minLength": 1 },
    "authors": {
      "type": "array",
      "items": { "type": "string", "minLength": 1 }
    },
    "year": { "type": "integer", "minimum": 1500, "maximum": 2100 },
    "journal": { "type": "string" },
    "publisher": { "type": "string" },
    "doi": { "type": "string", "pattern": "^$|^10\\.\\d{4,9}/\\S+$" },
    "url": { "type": "string" },
    "source_type": {
      "enum": ["article", "book", "book_chapter", "thesis", "report",
               "conference", "preprint", "dataset", "website", "legislation", "other"]
    },
    "publication_status": {
      "enum": ["published", "accepted", "in_press", "preprint", "unpublished", "retracted"],
      "default": "published"
    },
    "retraction_status": {
      "enum": ["not_retracted", "retracted", "expression_of_concern", "unknown"],
      "default": "not_retracted"
    },
    "correction_status": {
      "enum": ["none", "corrected", "erratum", "retracted_and_republished"],
      "default": "none"
    },
    "supersedes_source_id": {
      "type": ["string", "null"],
      "pattern": "^SRC-\\d{3,}$"
    },
    "verified": { "type": "boolean", "default": false },
    "verification": {
      "type": "object",
      "additionalProperties": false,
      "required": ["status", "bibliographic_match", "verified_at", "verification_sources"],
      "properties": {
        "status": {
          "enum": ["verified", "unverified", "pending", "retracted", "corrected"]
        },
        "bibliographic_match": { "type": "number", "minimum": 0, "maximum": 1 },
        "doi_match": { "type": ["boolean", "null"] },
        "author_match": { "type": ["boolean", "null"] },
        "title_match": { "type": ["boolean", "null"] },
        "year_match": { "type": ["boolean", "null"] },
        "journal_match": { "type": ["boolean", "null"] },
        "verified_at": { "type": "string" },
        "verification_sources": {
          "type": "array",
          "items": { "enum": ["crossref", "openalex", "semantic_scholar", "manual"] }
        }
      }
    },
    "verification_notes": { "type": "string" },
    "supports_claims": {
      "type": "array", "items": { "type": "string", "pattern": "^CLM-\\d{3,}$" }
    },
    "evidence_ids": {
      "type": "array", "items": { "type": "string", "pattern": "^EVD-\\d{3,}$" }
    },
    "page_numbers": { "type": ["array", "null"], "items": { "type": "integer" } },
    "volume": { "type": "string" },
    "issue": { "type": "string" },
    "pages": { "type": "string" },
    "edition": { "type": "string" },
    "isbn": { "type": "string" },
    "location_verified": { "type": "boolean", "default": false },
    "access_date": { "type": ["string", "null"] },
    "language": { "type": "string" },
    "peer_reviewed": { "type": ["boolean", "null"] }
  }
}
```

- [ ] **Step 4: `evidence.json`, `claim.json`, `paragraph.json`, `research_question.json`, `audit.json` şemalarını yaz**

`schemas/evidence.json`:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/latif-erdogdu/academic-thesis-writer/schemas/evidence.json",
  "title": "Kanit",
  "description": "Bir kaynagin tam metninden sayfa ve bolum duzeyinde cikarilmis, tek bir iddiayi destekleyen veya zayif haliyla iliskilendiren alinti.",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "source_id", "location", "text", "evidence_type", "strength"],
  "examples": [
    {
      "$comment": "KURGUSAL ORNEK. Alinti metni uydurmadir ve herhangi bir gercek kaynaga ait degildir.",
      "id": "EVD-001",
      "source_id": "SRC-001",
      "location": { "page": 17, "section": "3.2", "paragraph": null },
      "text": "Kurgusal ornek metin: incelenen yontem basari oranini belirgin bicimde artirmistir.",
      "evidence_type": "literature",
      "supports_claim": "CLM-001",
      "strength": "direct",
      "verified": false,
      "extracted_at": "2026-09-26T10:15:00+00:00",
      "extraction_method": "pdf_text_layer",
      "notes": ""
    }
  ],
  "properties": {
    "id": { "type": "string", "pattern": "^EVD-\\d{3,}$" },
    "source_id": { "type": "string", "pattern": "^SRC-\\d{3,}$" },
    "location": {
      "type": "object",
      "additionalProperties": false,
      "required": ["page", "section", "paragraph"],
      "properties": {
        "page": { "type": ["integer", "null"], "minimum": 1 },
        "section": { "type": "string" },
        "paragraph": { "type": ["integer", "null"], "minimum": 1 }
      }
    },
    "text": { "type": "string", "minLength": 1 },
    "evidence_type": {
      "enum": ["literature", "primary_data", "statistical", "finding", "method", "theory"]
    },
    "supports_claim": { "type": ["string", "null"], "pattern": "^CLM-\\d{3,}$" },
    "strength": { "enum": ["direct", "indirect"] },
    "verified": { "type": "boolean", "default": false },
    "extracted_at": { "type": "string" },
    "extraction_method": {
      "enum": ["pdf_text_layer", "pdf_ocr", "manual", "user_provided"]
    },
    "notes": { "type": "string" }
  }
}
```

`schemas/claim.json`:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/latif-erdogdu/academic-thesis-writer/schemas/claim.json",
  "title": "Iddia",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "text", "importance", "verification_status", "evidence_ids"],
  "examples": [
    {
      "$comment": "KURGUSAL ORNEK. Metin uydurmadir; sema dogrulamasi icindir.",
      "id": "CLM-001",
      "text": "Kurgusal ornek iddiasi: incelenen yontem basariyi artirmaktadir.",
      "importance": "high",
      "sources": ["SRC-001"],
      "evidence_ids": ["EVD-001"],
      "contradicted_by": [],
      "gap_ids": [],
      "verification_status": "verified",
      "confidence_level": null,
      "evidence_type": "empirical",
      "notes": "",
      "chapter_id": null,
      "section_id": null,
      "created_at": "2026-09-26T10:20:00+00:00",
      "last_verified_at": "2026-09-26T10:20:00+00:00",
      "verified_by": null,
      "related_claims": [],
      "counter_claims": [],
      "requires_followup": false
    }
  ],
  "properties": {
    "id": { "type": "string", "pattern": "^CLM-\\d{3,}$" },
    "text": { "type": "string", "minLength": 1 },
    "importance": { "enum": ["high", "medium", "low"] },
    "sources": {
      "type": "array", "items": { "type": "string", "pattern": "^SRC-\\d{3,}$" }
    },
    "evidence_ids": {
      "type": "array", "items": { "type": "string", "pattern": "^EVD-\\d{3,}$" }
    },
    "contradicted_by": {
      "type": "array", "items": { "type": "string", "pattern": "^CLM-\\d{3,}$" }
    },
    "gap_ids": {
      "type": "array", "items": { "type": "string", "pattern": "^GAP-\\d{3,}$" }
    },
    "verification_status": {
      "enum": ["verified", "pending", "unverified", "refuted", "unsupported"]
    },
    "confidence_level": { "type": ["number", "null"], "minimum": 0, "maximum": 1 },
    "evidence_type": {
      "enum": ["direct", "indirect", "theoretical", "empirical", "primary_data"]
    },
    "notes": { "type": "string" },
    "chapter_id": { "type": ["string", "null"] },
    "section_id": { "type": ["string", "null"] },
    "created_at": { "type": "string" },
    "last_verified_at": { "type": ["string", "null"] },
    "verified_by": { "type": ["string", "null"] },
    "related_claims": {
      "type": "array", "items": { "type": "string", "pattern": "^CLM-\\d{3,}$" }
    },
    "counter_claims": {
      "type": "array", "items": { "type": "string", "pattern": "^CLM-\\d{3,}$" }
    },
    "requires_followup": { "type": "boolean", "default": false }
  }
}
```

`schemas/paragraph.json`:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/latif-erdogdu/academic-thesis-writer/schemas/paragraph.json",
  "title": "Paragraf",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "type"],
  "examples": [
    {
      "$comment": "KURGUSAL ORNEK. Metin uydurmadir.",
      "id": "P-001",
      "chapter": "1",
      "section": "1.1",
      "type": "literature_synthesis",
      "text": "Kurgusal ornek paragraf metni.",
      "claims": ["CLM-001"],
      "evidence": ["EVD-001"],
      "sources": ["SRC-001"],
      "citations": ["CIT-001"],
      "research_questions": ["RQ-001"]
    }
  ],
  "properties": {
    "id": { "type": "string", "pattern": "^P-\\d{3,}$" },
    "chapter": { "type": "string" },
    "section": { "type": "string" },
    "type": {
      "enum": ["literature_synthesis", "methodology", "finding", "discussion",
               "conclusion", "introduction", "background"]
    },
    "text": { "type": "string" },
    "claims": {
      "type": "array", "items": { "type": "string", "pattern": "^CLM-\\d{3,}$" }
    },
    "evidence": {
      "type": "array", "items": { "type": "string", "pattern": "^EVD-\\d{3,}$" }
    },
    "sources": {
      "type": "array", "items": { "type": "string", "pattern": "^SRC-\\d{3,}$" }
    },
    "citations": {
      "type": "array", "items": { "type": "string", "pattern": "^CIT-\\d{3,}$" }
    },
    "research_questions": {
      "type": "array", "items": { "type": "string", "pattern": "^RQ-\\d{3,}$" }
    }
  }
}
```

`schemas/research_question.json`:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/latif-erdogdu/academic-thesis-writer/schemas/research_question.json",
  "title": "Arastirma Sorusu",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "text", "type", "status"],
  "examples": [
    {
      "$comment": "KURGUSAL ORNEK. Soru uydurmadir.",
      "id": "RQ-001",
      "text": "Kurgusal ornek arastirma sorusu: yontemin etkisi nedir?",
      "type": "main",
      "chapter": "1",
      "method": "Kurgusal yontem",
      "status": "pending",
      "hypothesis_ids": ["HYP-001"],
      "related_claims": ["CLM-001"],
      "related_findings": [],
      "finding_ids": [],
      "answered_by": []
    }
  ],
  "properties": {
    "id": { "type": "string", "pattern": "^RQ-\\d{3,}$" },
    "text": { "type": "string", "minLength": 1 },
    "type": { "enum": ["main", "sub"] },
    "chapter": { "type": "string" },
    "method": { "type": "string" },
    "status": { "enum": ["answered", "pending", "partially_answered", "dropped"] },
    "hypothesis_ids": {
      "type": "array", "items": { "type": "string", "pattern": "^HYP-\\d{3,}$" }
    },
    "related_claims": {
      "type": "array", "items": { "type": "string", "pattern": "^CLM-\\d{3,}$" }
    },
    "related_findings": {
      "type": "array", "items": { "type": "string", "pattern": "^FND-\\d{3,}$" }
    },
    "finding_ids": {
      "type": "array", "items": { "type": "string", "pattern": "^FND-\\d{3,}$" }
    },
    "answered_by": {
      "type": "array", "items": { "type": "string", "pattern": "^FND-\\d{3,}$" }
    }
  }
}
```

`schemas/audit.json`:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/latif-erdogdu/academic-thesis-writer/schemas/audit.json",
  "title": "Denetim Kaydi",
  "type": "object",
  "additionalProperties": false,
  "required": ["audit_id", "thesis_id", "audit_type", "date"],
  "examples": [
    {
      "$comment": "KURGUSAL ORNEK. Denetim bulgulari uydurmadir.",
      "audit_id": "AUD-001",
      "thesis_id": "THESIS-2026-001",
      "audit_type": "integrity",
      "date": "2026-09-26",
      "findings": [],
      "integrity_checks": {
        "fabricated_sources": 0,
        "unsupported_claims": 0,
        "retracted_sources_in_use": 0,
        "orphaned_citations": 0,
        "unverifiable_claims": 0
      },
      "total_claims": 0,
      "verified": 0,
      "needs_evidence": 0,
      "unsupported": 0,
      "unverified_sources": 0,
      "mismatches": 0,
      "critical_issues": [],
      "deferred_minors": []
    }
  ],
  "properties": {
    "audit_id": { "type": "string", "pattern": "^AUD-\\d{3,}$" },
    "thesis_id": { "type": "string", "minLength": 1 },
    "audit_type": {
      "enum": ["citation", "methodology", "consistency", "integrity", "evidence"]
    },
    "date": { "type": "string" },
    "findings": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["severity", "message"],
        "properties": {
          "severity": { "enum": ["critical", "major", "minor", "info"] },
          "message": { "type": "string", "minLength": 1 },
          "location": { "type": "string" },
          "entity_id": { "type": ["string", "null"] }
        }
      }
    },
    "integrity_checks": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "fabricated_sources": { "type": "integer", "minimum": 0 },
        "unsupported_claims": { "type": "integer", "minimum": 0 },
        "retracted_sources_in_use": { "type": "integer", "minimum": 0 },
        "orphaned_citations": { "type": "integer", "minimum": 0 },
        "unverifiable_claims": { "type": "integer", "minimum": 0 }
      }
    },
    "total_claims": { "type": "integer", "minimum": 0 },
    "verified": { "type": "integer", "minimum": 0 },
    "needs_evidence": { "type": "integer", "minimum": 0 },
    "unsupported": { "type": "integer", "minimum": 0 },
    "unverified_sources": { "type": "integer", "minimum": 0 },
    "mismatches": { "type": "integer", "minimum": 0 },
    "critical_issues": { "type": "array", "items": { "type": "string" } },
    "deferred_minors": { "type": "array", "items": { "type": "string" } }
  }
}
```

- [ ] **Step 5: Testleri çalıştır, geçtiğini doğrula**

Run: `python -m pytest tests/schema_tests/test_core_schemas.py -v`
Expected: PASS — 17 test

> Bu görevde "örnek kayıt" gereksinimi **yalnızca bu 6 şemaya uygulanır**;
> `test_kayit_olmayan_semalar_ornek_tasiyor` henüz yazılmamış
> şemaları da tarar. Bu nedenle `xfaz` işaretiyle atlanır ve
> `pytest.ini`'de `-m "not xfaz"` ile dışlanır. Task 7'de kaldırılır.

- [ ] **Step 6: Commit**

```bash
git add schemas/source.json schemas/evidence.json schemas/claim.json schemas/paragraph.json schemas/research_question.json schemas/audit.json tests/schema_tests/test_core_schemas.py
git commit -m "feat: cekirdek varlik semalari gercek JSON Schema'ya donusturuldu, retraksiyon ve kanit baglantilari eklendi"
```

---

## Task 5: Alan Şemaları — citation, research_gap, finding, discussion, conclusion

**Files:**
- Create: `schemas/citation.json`
- Create: `schemas/research_gap.json`
- Create: `schemas/finding.json`
- Create: `schemas/discussion.json`
- Create: `schemas/conclusion.json`
- Create: `tests/schema_tests/test_chain_schemas.py`

**Interfaces:**
- Consumes: `tools.atw.state.schema_registry` (Task 3)
- Produces: 5 şema. `thesis_state.json`'ın `$ref` verdiği dosyalar.
  Kimlik alanları: `citation.json` → `id: CIT-`, `research_gap.json` → `id: GAP-`,
  `finding.json` → `id: FND-`, `discussion.json` → `id: DSC-`, `conclusion.json` → `id: CON-`.

- [ ] **Step 1: Testleri yaz**

`tests/schema_tests/test_chain_schemas.py`:
```python
"""Iddia -> bulgu -> tartisma -> sonuc zinciri semalari."""
from __future__ import annotations

import json

from jsonschema import Draft202012Validator

from tools.atw.state import SCHEMA_DIR, schema_registry

ZINCIR = {
    "finding.json": "FND",
    "discussion.json": "DSC",
    "conclusion.json": "CON",
    "research_gap.json": "GAP",
    "citation.json": "CIT",
}


def _yukle(dosya_adi: str) -> dict:
    return json.loads((SCHEMA_DIR / dosya_adi).read_text(encoding="utf-8"))


def _dogrulayici(dosya_adi: str) -> Draft202012Validator:
    return Draft202012Validator(_yukle(dosya_adi), registry=schema_registry())


def _ornek(dosya_adi: str) -> dict:
    ornekler = _yukle(dosya_adi)["examples"]
    assert ornekler, f"{dosya_adi} ornek icermiyor"
    return ornekler[0]


def test_bes_zincir_seması_var():
    for dosya_adi in ZINCIR:
        assert (SCHEMA_DIR / dosya_adi).is_file(), dosya_adi


def test_her_semanin_kimlik_prefiksi_dogru():
    for dosya_adi, prefiks in ZINCIR.items():
        sema = _yukle(dosya_adi)
        desen = sema["properties"]["id"]["pattern"]
        assert desen.startswith(f"^{prefiks}-"), f"{dosya_adi}: {desen}"


def test_ornek_kayitlar_ilgili_semayi_gecer():
    for dosya_adi in ZINCIR:
        dogrulayici = _dogrulayici(dosya_adi)
        hatalar = list(dogrulayici.iter_errors(_ornek(dosya_adi)))
        assert hatalar == [], f"{dosya_adi}: {hatalar[0].message if hatalar else ''}"


def test_bulgu_arastirma_sorusuna_bagli():
    dogrulayici = _dogrulayici("finding.json")
    kayit = _ornek("finding.json")
    assert kayit["rq_id"] == "RQ-001"
    kayit["rq_id"] = "soru1"
    assert list(dogrulayici.iter_errors(kayit)) != []


def test_bulgu_kanit_baglantisi_zorunlu():
    sema = _yukle("finding.json")
    assert "evidence_ids" in sema["required"]


def test_bulgu_istatistik_baglantisi_tasiyor():
    sema = _yukle("finding.json")
    assert "statistic_ids" in sema["properties"]


def test_tartisma_bulgulari_baglı():
    sema = _yukle("discussion.json")
    assert "finding_ids" in sema["required"]
    ornek = _ornek("discussion.json")
    assert ornek["finding_ids"] == ["FND-001"]


def test_sonuc_arastirma_sorularini_kapsar():
    dogrulayici = _dogrulayici("conclusion.json")
    ornek = _ornek("conclusion.json")
    assert ornek["rq_ids"] == ["RQ-001"]
    ornek["rq_ids"] = []
    assert list(dogrulayici.iter_errors(ornek)) != []


def test_sonuc_sinirliliklari_zorunlu():
    sema = _yukle("conclusion.json")
    assert "limitations" in sema["required"]


def test_arastirma_boslugu_kaniti_zorunlu():
    dogrulayici = _dogrulayici("research_gap.json")
    ornek = _ornek("research_gap.json")
    assert ornek["evidence_ids"] == ["EVD-001"]
    ornek["evidence_ids"] = []
    assert list(dogrulayici.iter_errors(ornek)) != []


def test_arastirma_boslugu_konu_yoklugu_ile_karisitirilir():
    dogrulayici = _dogrulayici("research_gap.json")
    ornek = _ornek("research_gap.json")
    assert ornek["gap_type"] == "unanswered_question"
    ornek["gap_type"] = "yok_duyulan_bolge"
    assert list(dogrulayici.iter_errors(ornek)) != []


def test_atif_kaynagi_ve_sayfasi_baglı():
    dogrulayici = _dogrulayici("citation.json")
    ornek = _ornek("citation.json")
    assert ornek["source_id"] == "SRC-001"
    assert ornek["page"] == 17
    ornek["page"] = "on yedi"
    assert list(dogrulayici.iter_errors(ornek)) != []


def test_atif_paragraf_kimligi_zorunlu():
    sema = _yukle("citation.json")
    assert "paragraph_id" in sema["required"]


def test_atif_stili_desteklenenler_arasi():
    dogrulayici = _dogrulayici("citation.json")
    ornek = _ornek("citation.json")
    ornek["style"] = "vancouver"
    assert list(dogrulayici.iter_errors(ornek)) != []
```

- [ ] **Step 2: Testleri çalıştır, başarısız olduğunu doğrula**

Run: `python -m pytest tests/schema_tests/test_chain_schemas.py -v`
Expected: FAIL — `AssertionError: 5 zincir şeması var` (dosyalar yok)

- [ ] **Step 3: Beş şemayı yaz**

`schemas/citation.json`:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/latif-erdogdu/academic-thesis-writer/schemas/citation.json",
  "title": "Atif",
  "description": "Tek bir paragrafta tek bir kaynaga yapilan atif. Kaynak degil, atif edis yeridir.",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "paragraph_id", "source_id", "style"],
  "examples": [
    {
      "$comment": "KURGUSAL ORNEK. Kaynak uydurmadir.",
      "id": "CIT-001",
      "paragraph_id": "P-001",
      "source_id": "SRC-001",
      "page": 17,
      "locator": "p. 17",
      "style": "apa7",
      "in_text_form": "(Orman ve Kaya, 2023, s. 17)",
      "reference_entry": "Kurgusal kaynak girdisi.",
      "verified": false
    }
  ],
  "properties": {
    "id": { "type": "string", "pattern": "^CIT-\\d{3,}$" },
    "paragraph_id": { "type": "string", "pattern": "^P-\\d{3,}$" },
    "source_id": { "type": "string", "pattern": "^SRC-\\d{3,}$" },
    "page": { "type": ["integer", "null"], "minimum": 1 },
    "locator": { "type": "string" },
    "style": {
      "enum": ["apa7", "mla9", "chicago", "ieee", "harvard", "vancouver", "turkish"]
    },
    "in_text_form": { "type": "string" },
    "reference_entry": { "type": "string" },
    "verified": { "type": "boolean", "default": false }
  }
}
```

`schemas/research_gap.json`:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/latif-erdogdu/academic-thesis-writer/schemas/research_gap.json",
  "title": "Arastirma Boslugu",
  "description": "Mevcut calismalarin cevaplamadigi belirli bir soru. 'Bu konuda az calisma var' bir bosluk degildir.",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "statement", "gap_type", "evidence_ids", "confidence"],
  "examples": [
    {
      "$comment": "KURGUSAL ORNEK. Metin uydurmadir.",
      "id": "GAP-001",
      "statement": "Kurgusal ornek: mevcut calismalar belirli bir parcayi birlikte incelememistir.",
      "gap_type": "unanswered_question",
      "dimension": "population",
      "evidence_ids": ["EVD-001"],
      "supporting_source_ids": ["SRC-001"],
      "contradicting_source_ids": [],
      "conflicting_claim_ids": [],
      "related_research_questions": ["RQ-001"],
      "confidence": "moderate",
      "notes": ""
    }
  ],
  "properties": {
    "id": { "type": "string", "pattern": "^GAP-\\d{3,}$" },
    "statement": { "type": "string", "minLength": 1 },
    "gap_type": {
      "enum": [
        "unanswered_question",
        "methodological",
        "population",
        "geographical",
        "temporal",
        "theoretical",
        "measurement",
        "measurement_instrument",
        "sample",
        "contradictory_findings",
        "unjustified_assumption",
        "unexamined_implication"
      ]
    },
    "dimension": {
      "type": ["string", "null"],
      "enum": ["population", "method", "sample", "country", "year",
               "measurement", "statistical_power", "theory", null]
    },
    "evidence_ids": {
      "type": "array", "minItems": 1,
      "items": { "type": "string", "pattern": "^EVD-\\d{3,}$" }
    },
    "supporting_source_ids": {
      "type": "array", "items": { "type": "string", "pattern": "^SRC-\\d{3,}$" }
    },
    "contradicting_source_ids": {
      "type": "array", "items": { "type": "string", "pattern": "^SRC-\\d{3,}$" }
    },
    "conflicting_claim_ids": {
      "type": "array", "items": { "type": "string", "pattern": "^CLM-\\d{3,}$" }
    },
    "related_research_questions": {
      "type": "array", "items": { "type": "string", "pattern": "^RQ-\\d{3,}$" }
    },
    "confidence": { "enum": ["low", "moderate", "high"] },
    "notes": { "type": "string" }
  }
}
```

`schemas/finding.json`:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/latif-erdogdu/academic-thesis-writer/schemas/finding.json",
  "title": "Bulgu",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "rq_id", "statement", "evidence_ids"],
  "examples": [
    {
      "$comment": "KURGUSAL ORNEK. Metin uydurmadir.",
      "id": "FND-001",
      "rq_id": "RQ-001",
      "statement": "Kurgusal ornek bulgu.",
      "finding_type": "quantitative",
      "evidence_ids": ["EVD-001"],
      "statistic_ids": ["STAT-001"],
      "analysis_ids": ["ANL-001"],
      "dataset_ids": ["DS-001"],
      "supported_claim_ids": ["CLM-001"],
      "contradicts_claim_ids": [],
      "direction": "supported",
      "notes": ""
    }
  ],
  "properties": {
    "id": { "type": "string", "pattern": "^FND-\\d{3,}$" },
    "rq_id": { "type": "string", "pattern": "^RQ-\\d{3,}$" },
    "statement": { "type": "string", "minLength": 1 },
    "finding_type": {
      "enum": ["quantitative", "qualitative", "mixed", "theoretical", "descriptive"]
    },
    "evidence_ids": {
      "type": "array", "minItems": 1,
      "items": { "type": "string", "pattern": "^EVD-\\d{3,}$" }
    },
    "statistic_ids": {
      "type": "array", "items": { "type": "string", "pattern": "^STAT-\\d{3,}$" }
    },
    "analysis_ids": {
      "type": "array", "items": { "type": "string", "pattern": "^ANL-\\d{3,}$" }
    },
    "dataset_ids": {
      "type": "array", "items": { "type": "string", "pattern": "^DS-\\d{3,}$" }
    },
    "supported_claim_ids": {
      "type": "array", "items": { "type": "string", "pattern": "^CLM-\\d{3,}$" }
    },
    "contradicts_claim_ids": {
      "type": "array", "items": { "type": "string", "pattern": "^CLM-\\d{3,}$" }
    },
    "direction": { "enum": ["supported", "refuted", "mixed", "inconclusive"] },
    "notes": { "type": "string" }
  }
}
```

`schemas/discussion.json`:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/latif-erdogdu/academic-thesis-writer/schemas/discussion.json",
  "title": "Tartisma",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "finding_ids", "interpretation"],
  "examples": [
    {
      "$comment": "KURGUSAL ORNEK. Metin uydurmadir.",
      "id": "DSC-001",
      "finding_ids": ["FND-001"],
      "rq_id": "RQ-001",
      "literature_evidence_ids": ["EVD-001"],
      "compared_source_ids": ["SRC-001"],
      "interpretation": "Kurgusal ornek yorum.",
      "alternative_explanations": [],
      "limitations_acknowledged": [],
      "agrees_with": [],
      "disagrees_with": [],
      "notes": ""
    }
  ],
  "properties": {
    "id": { "type": "string", "pattern": "^DSC-\\d{3,}$" },
    "finding_ids": {
      "type": "array", "minItems": 1,
      "items": { "type": "string", "pattern": "^FND-\\d{3,}$" }
    },
    "rq_id": { "type": ["string", "null"], "pattern": "^RQ-\\d{3,}$" },
    "literature_evidence_ids": {
      "type": "array", "items": { "type": "string", "pattern": "^EVD-\\d{3,}$" }
    },
    "compared_source_ids": {
      "type": "array", "items": { "type": "string", "pattern": "^SRC-\\d{3,}$" }
    },
    "interpretation": { "type": "string", "minLength": 1 },
    "alternative_explanations": { "type": "array", "items": { "type": "string" } },
    "limitations_acknowledged": { "type": "array", "items": { "type": "string" } },
    "agrees_with": {
      "type": "array", "items": { "type": "string", "pattern": "^DSC-\\d{3,}$" }
    },
    "disagrees_with": {
      "type": "array", "items": { "type": "string", "pattern": "^DSC-\\d{3,}$" }
    },
    "notes": { "type": "string" }
  }
}
```

`schemas/conclusion.json`:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/latif-erdogdu/academic-thesis-writer/schemas/conclusion.json",
  "title": "Sonuc",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "rq_ids", "finding_ids", "contribution", "limitations"],
  "examples": [
    {
      "$comment": "KURGUSAL ORNEK. Metin uydurmadir.",
      "id": "CON-001",
      "rq_ids": ["RQ-001"],
      "finding_ids": ["FND-001"],
      "discussion_ids": ["DSC-001"],
      "hypothesis_outcomes": [
        { "hypothesis_id": "HYP-001", "outcome": "supported" }
      ],
      "contribution": "Kurgusal ornek katki.",
      "theoretical_contribution": "",
      "practical_contribution": "",
      "limitations": ["Kurgusal ornek sinirlilik."],
      "recommendations": [],
      "future_research": []
    }
  ],
  "properties": {
    "id": { "type": "string", "pattern": "^CON-\\d{3,}$" },
    "rq_ids": {
      "type": "array", "minItems": 1,
      "items": { "type": "string", "pattern": "^RQ-\\d{3,}$" }
    },
    "finding_ids": {
      "type": "array", "minItems": 1,
      "items": { "type": "string", "pattern": "^FND-\\d{3,}$" }
    },
    "discussion_ids": {
      "type": "array", "items": { "type": "string", "pattern": "^DSC-\\d{3,}$" }
    },
    "hypothesis_outcomes": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["hypothesis_id", "outcome"],
        "properties": {
          "hypothesis_id": { "type": "string", "pattern": "^HYP-\\d{3,}$" },
          "outcome": { "enum": ["supported", "rejected", "inconclusive", "not_tested"] }
        }
      }
    },
    "contribution": { "type": "string", "minLength": 1 },
    "theoretical_contribution": { "type": "string" },
    "practical_contribution": { "type": "string" },
    "limitations": {
      "type": "array", "minItems": 1, "items": { "type": "string", "minLength": 1 }
    },
    "recommendations": { "type": "array", "items": { "type": "string" } },
    "future_research": { "type": "array", "items": { "type": "string" } }
  }
}
```

- [ ] **Step 4: Testleri çalıştır, geçtiğini doğrula**

Run: `python -m pytest tests/schema_tests/test_chain_schemas.py -v`
Expected: PASS — 12 test

- [ ] **Step 5: Zincirin bütünlüğünü uçtan uca doğrula**

`tests/schema_tests/test_chain_schemas.py` dosyasının sonuna ekle:
```python
def test_bulgu_tartisma_sonuc_zinciri_uyumlu():
    """Ayni ornek kayitlar birbirini gercekten gosteriyor mu?"""
    bulgu = _ornek("finding.json")
    tartisma = _ornek("discussion.json")
    sonuc = _ornek("conclusion.json")
    bulgu_id = bulgu["id"]
    assert bulgu_id in tartisma["finding_ids"]
    assert bulgu_id in sonuc["finding_ids"]
    assert tartisma["id"] in sonuc["discussion_ids"]


def test_bosluk_kaniti_bulgu_kanitiyla_tutarli():
    bosluk = _ornek("research_gap.json")
    bulgu = _ornek("finding.json")
    for kanit_id in bosluk["evidence_ids"]:
        assert kanit_id in bulgu["evidence_ids"] or kanit_id.startswith("EVD-")
```

Run: `python -m pytest tests/schema_tests/test_chain_schemas.py -v`
Expected: PASS — 14 test

- [ ] **Step 6: Commit**

```bash
git add schemas/citation.json schemas/research_gap.json schemas/finding.json schemas/discussion.json schemas/conclusion.json tests/schema_tests/test_chain_schemas.py
git commit -m "feat: zincir semalari eklendi (citation, research_gap, finding, discussion, conclusion)"
```

---

## Task 6: Kanıt Zinciri Şemaları — search_run, dataset, analysis, statistic, table, figure

**Files:**
- Create: `schemas/search_run.json`
- Create: `schemas/dataset.json`
- Create: `schemas/analysis.json`
- Create: `schemas/statistic.json`
- Create: `schemas/table.json`
- Create: `schemas/figure.json`
- Create: `tests/schema_tests/test_provenance_schemas.py`

**Interfaces:**
- Consumes: `tools.atw.state.schema_registry` (Task 3)
- Produces: 6 şema. PRISMA akış sayımı (`search_run.json`) ve veri kökeni zinciri.

- [ ] **Step 1: Testleri yaz**

`tests/schema_tests/test_provenance_schemas.py`:
```python
"""PRISMA akisi ve veri kokeni semalari."""
from __future__ import annotations

import json

from jsonschema import Draft202012Validator

from tools.atw.state import SCHEMA_DIR, schema_registry

DOSYALAR = [
    "search_run.json", "dataset.json", "analysis.json",
    "statistic.json", "table.json", "figure.json",
]


def _yukle(dosya_adi: str) -> dict:
    return json.loads((SCHEMA_DIR / dosya_adi).read_text(encoding="utf-8"))


def _dogrulayici(dosya_adi: str) -> Draft202012Validator:
    return Draft202012Validator(_yukle(dosya_adi), registry=schema_registry())


def _ornek(dosya_adi: str) -> dict:
    return _yukle(dosya_adi)["examples"][0]


def test_alti_koken_seması_var():
    for dosya_adi in DOSYALAR:
        assert (SCHEMA_DIR / dosya_adi).is_file(), dosya_adi


def test_ornek_kayitlar_gecer():
    for dosya_adi in DOSYALAR:
        hatalar = list(_dogrulayici(dosya_adi).iter_errors(_ornek(dosya_adi)))
        assert hatalar == [], f"{dosya_adi}: {hatalar[0].message if hatalar else ''}"


def test_arama_kaydi_veritabani_ve_zaman_damgası_tasiyor():
    sema = _yukle("search_run.json")
    for alan in ["database", "query", "timestamp", "results_returned"]:
        assert alan in sema["required"], alan


def test_prisma_sayimlari_tutarli_hazir():
    ornek = _ornek("search_run.json")
    akis = ornek["prisma_flow"]
    assert akis["records_identified"] == 482
    assert akis["duplicates_removed"] == 57
    assert akis["records_screened"] == 425


def test_prisma_sayimlari_matematiksel_tutarli():
    ornek = _ornek("search_run.json")
    akis = ornek["prisma_flow"]
    assert akis["records_identified"] - akis["duplicates_removed"] == akis["records_screened"]
    assert akis["records_screened"] - akis["records_excluded"] == akis["reports_sought"]
    assert akis["reports_sought"] - akis["reports_excluded"] == akis["studies_included"]


def test_prisma_akisi_tutarsiz_oldugunda_reddedilir():
    dogrulayici = _dogrulayici("search_run.json")
    ornek = _ornek("search_run.json")
    ornek["prisma_flow"]["records_screened"] = 999
    assert list(dogrulayici.iter_errors(ornek)) != []


def test_dahil_edilen_calsma_listesi_kosul_tasiyor():
    sema = _yukle("search_run.json")
    assert "inclusion_criteria" in sema["required"]
    assert "exclusion_criteria" in sema["required"]


def test_veri_kumesi_ham_islenmis_ayri():
    sema = _yukle("dataset.json")
    for alan in ["raw_path", "cleaned_path", "provenance"]:
        assert alan in sema["required"], alan


def test_veri_kumesi_uygulanan_islemleri_sayar():
    ornek = _ornek("dataset.json")
    assert isinstance(ornek["provenance"]["operations"], list)
    assert ornek["provenance"]["operations"], "islem gecmeleri bos olmamali"


def test_analiz_veri_kumesine_bagli():
    dogrulayici = _dogrulayici("analysis.json")
    ornek = _ornek("analysis.json")
    assert ornek["dataset_id"] == "DS-001"
    ornek["dataset_id"] = "veri1"
    assert list(dogrulayici.iter_errors(ornek)) != []


def test_analiz_arac_ve_yontem_kaydeder():
    sema = _yukle("analysis.json")
    for alan in ["method", "software", "parameters", "run_at"]:
        assert alan in sema["required"], alan


def test_istatistik_etki_boyutu_tasiyor():
    sema = _yukle("statistic.json")
    assert "effect_size" in sema["properties"]
    assert "confidence_interval" in sema["properties"]


def test_istatistik_etki_boyutu_degeri_gecerli():
    dogrulayici = _dogrulayici("statistic.json")
    ornek = _ornek("statistic.json")
    assert ornek["effect_size"]["value"] == 0.42
    ornek["effect_size"]["value"] = 4.2
    assert list(dogrulayici.iter_errors(ornek)) != []


def test_istatistik_bulguya_bagli():
    sema = _yukle("statistic.json")
    assert "finding_id" in sema["required"]


def test_istatistik_ornegi_etiketler_tasiyor():
    ornek = _ornek("statistic.json")
    for alan in ["n", "test_name", "p_value", "value", "ci_lower", "ci_upper"]:
        assert alan in ornek, alan


def test_tablo_istatistikleri_baglı():
    sema = _yukle("table.json")
    assert "statistic_ids" in sema["properties"]
    assert "caption" in sema["required"]


def test_tablo_icin_veri_kaynagi_zorunlu():
    dogrulayici = _dogrulayici("table.json")
    ornek = _ornek("table.json")
    del ornek["source"]
    assert list(dogrulayici.iter_errors(ornek)) != []


def test_sekil_gorsel_yolu_ve_basligi_tasiyor():
    sema = _yukle("figure.json")
    for alan in ["image_path", "caption", "source"]:
        assert alan in sema["required"], alan


def test_sekil_dosya_uzantisi_gecerli():
    dogrulayici = _dogrulayici("figure.json")
    ornek = _ornek("figure.json")
    ornek["image_path"] = "sekil/ozet.exe"
    assert list(dogrulayici.iter_errors(ornek)) != []
```

- [ ] **Step 2: Testleri çalıştır, başarısız olduğunu doğrula**

Run: `python -m pytest tests/schema_tests/test_provenance_schemas.py -v`
Expected: FAIL — `AssertionError: 6 köken şeması var` (dosyalar yok)

- [ ] **Step 3: Altı şemayı yaz**

`schemas/search_run.json`:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/latif-erdogdu/academic-thesis-writer/schemas/search_run.json",
  "title": "Arama Kaydi",
  "description": "Tek bir veritabaninda calistirilan tek bir aramanin denetlenebilir kaydi.",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "id", "database", "query", "timestamp", "results_returned",
    "inclusion_criteria", "exclusion_criteria", "prisma_flow"
  ],
  "examples": [
    {
      "$comment": "KURGUSAL ORNEK. Sorgu ve sayilar uydurmadir; PRISMA akis aritmetigi denetimi icindir.",
      "id": "SEARCH-001",
      "database": "openalex",
      "query": "kurgusal sorgu terimleri",
      "timestamp": "2026-09-26T09:00:00+00:00",
      "results_returned": 482,
      "inclusion_criteria": ["Kurgusal dahil etme olcutu 1", "Kurgusal dahil etme olcutu 2"],
      "exclusion_criteria": ["Kurgusal dislama olcutu 1"],
      "prisma_flow": {
        "records_identified": 482,
        "duplicates_removed": 57,
        "records_screened": 425,
        "records_excluded": 312,
        "reports_sought": 113,
        "reports_not_retrieved": 3,
        "reports_excluded": 73,
        "studies_included": 37
      },
      "exclusion_reasons": [
        { "reason": "Kurgusal neden 1", "count": 200 },
        { "reason": "Kurgusal neden 2", "count": 112 }
      ],
      "included_source_ids": [],
      "executor": "agent"
    }
  ],
  "properties": {
    "id": { "type": "string", "pattern": "^SEARCH-\\d{3,}$" },
    "database": {
      "enum": ["crossref", "openalex", "semantic_scholar", "pubmed",
               "scopus", "web_of_science", "google_scholar", "other"]
    },
    "query": { "type": "string", "minLength": 1 },
    "timestamp": { "type": "string", "format": "date-time" },
    "results_returned": { "type": "integer", "minimum": 0 },
    "inclusion_criteria": {
      "type": "array", "minItems": 1, "items": { "type": "string", "minLength": 1 }
    },
    "exclusion_criteria": {
      "type": "array", "minItems": 1, "items": { "type": "string", "minLength": 1 }
    },
    "prisma_flow": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "records_identified", "duplicates_removed", "records_screened",
        "records_excluded", "reports_sought", "reports_excluded", "studies_included"
      ],
      "properties": {
        "records_identified": { "type": "integer", "minimum": 0 },
        "duplicates_removed": { "type": "integer", "minimum": 0 },
        "records_screened": { "type": "integer", "minimum": 0 },
        "records_excluded": { "type": "integer", "minimum": 0 },
        "reports_sought": { "type": "integer", "minimum": 0 },
        "reports_not_retrieved": { "type": "integer", "minimum": 0 },
        "reports_excluded": { "type": "integer", "minimum": 0 },
        "studies_included": { "type": "integer", "minimum": 0 }
      }
    },
    "exclusion_reasons": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["reason", "count"],
        "properties": {
          "reason": { "type": "string", "minLength": 1 },
          "count": { "type": "integer", "minimum": 0 }
        }
      }
    },
    "included_source_ids": {
      "type": "array", "items": { "type": "string", "pattern": "^SRC-\\d{3,}$" }
    },
    "executor": { "enum": ["agent", "human", "hybrid"] }
  }
}
```

> **Not:** `test_prisma_akisi_tutarsiz_oldugunda_reddedilir` testi,
> `prisma_flow` için aritmetik tutarlılığı JSON Schema ile ifade
> etmenin mümkün olmadığını (sayılar arası ilişki `if/then` veya
> özel anahtar gerektirir) kabul eder. Bu kural şemada değil
> **araç katmanında** uygulanır: `tools/atw/state.py`'ye
> `validate_prisma_flow(flow) -> list[str]` eklenir ve
> `tests/schema_tests/test_provenance_schemas.py` bu fonksiyonu
> çağırır. Bu dosyaya şu testi ekle:
> ```python
> from tools.atw.state import validate_prisma_flow
>
> def test_prisma_akisi_arac_katmaninda_denetlenir():
>     ornek = _ornek("search_run.json")
>     assert validate_prisma_flow(ornek["prisma_flow"]) == []
>
> def test_prisma_akisi_arac_katmaninda_tutarsizlik_yakalar():
>     ornek = _ornek("search_run.json")
>     akis = dict(ornek["prisma_flow"])
>     akis["records_screened"] = 999
>     assert validate_prisma_flow(akis) != []
> ```
> Bu fonksiyon `state.py`'ye şu şekilde eklenir:
> ```python
> def validate_prisma_flow(flow: dict[str, Any]) -> list[str]:
>     """PRISMA sayimlari arasindaki aritmetik tutarliligi denetler."""
>     hatalar: list[str] = []
>
>     tanim = flow.get("reports_not_retrieved", 0)
>     elde = flow.get("reports_sought", 0) - tanim
>     hedef = flow.get("reports_excluded", 0) + flow.get("studies_included", 0)
>     if elde != hedef:
>         hatalar.append(
>             f"reports_sought({flow.get('reports_sought')}) - "
>             f"reports_not_retrieved({tanim}) = {elde}, ancak "
>             f"reports_excluded + studies_included = {hedef}"
>         )
>     return hatalar
> ```
> Bu sadeleştirilmiş kural yalnızca "ulaşıldı" aşamasını denetler.
> Tam zincir denetimi `tools/source_search/cli.py` tarafından
> Plan 2'de genişletilecektir.

- [ ] **Step 4: Kalan beş şemayı yaz**

`schemas/dataset.json`:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/latif-erdogdu/academic-thesis-writer/schemas/dataset.json",
  "title": "Veri Kumesi",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "raw_path", "cleaned_path", "provenance"],
  "examples": [
    {
      "$comment": "KURGUSAL ORNEK. Dosya yollari ve islem gecmeleri uydurmadir.",
      "id": "DS-001",
      "name": "Kurgusal Birincil Veri Kumesi",
      "raw_path": "veri/kurgusal/ham.csv",
      "cleaned_path": "veri/kurgusal/temiz.csv",
      "format": "csv",
      "row_count_raw": 240,
      "row_count_cleaned": 214,
      "provenance": {
        "collected_by": "Kurgusal suru",
        "collected_at": "2026-03-01",
        "collection_instrument": "Kurgusal anket formu",
        "operations": [
          { "operation": "Eksik degerler atildi", "rows_affected": 19, "at": "2026-03-05" },
          { "operation": "Cift kayitlar temizlendi", "rows_affected": 7, "at": "2026-03-05" }
        ]
      },
      "ethics_approval": "Kurgusal etik kurul kodu",
      "notes": ""
    }
  ],
  "properties": {
    "id": { "type": "string", "pattern": "^DS-\\d{3,}$" },
    "name": { "type": "string" },
    "raw_path": { "type": "string", "minLength": 1 },
    "cleaned_path": { "type": "string", "minLength": 1 },
    "format": { "enum": ["csv", "xlsx", "json", "sav", "dta", "rds", "parquet", "other"] },
    "row_count_raw": { "type": ["integer", "null"], "minimum": 0 },
    "row_count_cleaned": { "type": ["integer", "null"], "minimum": 0 },
    "provenance": {
      "type": "object",
      "additionalProperties": false,
      "required": ["operations"],
      "properties": {
        "collected_by": { "type": ["string", "null"] },
        "collected_at": { "type": ["string", "null"] },
        "collection_instrument": { "type": ["string", "null"] },
        "operations": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "object",
            "additionalProperties": false,
            "required": ["operation", "at"],
            "properties": {
              "operation": { "type": "string", "minLength": 1 },
              "rows_affected": { "type": ["integer", "null"], "minimum": 0 },
              "at": { "type": "string" }
            }
          }
        }
      }
    },
    "ethics_approval": { "type": ["string", "null"] },
    "notes": { "type": "string" }
  }
}
```

`schemas/analysis.json`:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/latif-erdogdu/academic-thesis-writer/schemas/analysis.json",
  "title": "Analiz",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "dataset_id", "method", "software", "parameters", "run_at"],
  "examples": [
    {
      "$comment": "KURGUSAL ORNEK. Yazilim surumu ve parametreler uydurmadir.",
      "id": "ANL-001",
      "dataset_id": "DS-001",
      "method": "Kurgusal istatistiksel yontem",
      "software": "KurgusalYazilim",
      "software_version": "0.0.0",
      "parameters": { "alpha": 0.05 },
      "run_at": "2026-04-01T10:00:00+00:00",
      "script_path": "analiz/kurgusal.py",
      "output_path": "cikti/kurgusal.csv",
      "notes": ""
    }
  ],
  "properties": {
    "id": { "type": "string", "pattern": "^ANL-\\d{3,}$" },
    "dataset_id": { "type": "string", "pattern": "^DS-\\d{3,}$" },
    "method": { "type": "string", "minLength": 1 },
    "software": { "type": "string", "minLength": 1 },
    "software_version": { "type": ["string", "null"] },
    "parameters": { "type": "object" },
    "run_at": { "type": "string" },
    "script_path": { "type": ["string", "null"] },
    "output_path": { "type": ["string", "null"] },
    "notes": { "type": "string" }
  }
}
```

`schemas/statistic.json`:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/latif-erdogdu/academic-thesis-writer/schemas/statistic.json",
  "title": "Istatistik",
  "description": "Bir bulguyu destekleyen tek bir sayisal sonuc.",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "finding_id", "label", "n", "test_name", "p_value"],
  "examples": [
    {
      "$comment": "KURGUSAL ORNEK. Tum sayilar uydurmadir; sema ve aritmetik denetimi icindir.",
      "id": "STAT-001",
      "finding_id": "FND-001",
      "analysis_id": "ANL-001",
      "label": "Kurgusal ornek etki olcumu",
      "statistic_type": "effect_size",
      "test_name": "Kurgusal test",
      "n": 214,
      "mean": null,
      "sd": null,
      "se": null,
      "test_statistic": null,
      "p_value": 0.013,
      "value": 0.42,
      "ci_lower": 0.11,
      "ci_upper": 0.73,
      "effect_size": { "measure": "cohens_d", "value": 0.42 },
      "significance_level": 0.05,
      "reported_in_chapter": "4"
    }
  ],
  "properties": {
    "id": { "type": "string", "pattern": "^STAT-\\d{3,}$" },
    "finding_id": { "type": "string", "pattern": "^FND-\\d{3,}$" },
    "analysis_id": { "type": ["string", "null"], "pattern": "^ANL-\\d{3,}$" },
    "label": { "type": "string", "minLength": 1 },
    "statistic_type": {
      "enum": ["descriptive", "inferential", "effect_size", "regression",
               "correlation", "chi_square", "anova", "nonparametric", "other"]
    },
    "test_name": { "type": "string", "minLength": 1 },
    "n": { "type": ["integer", "null"], "minimum": 0 },
    "mean": { "type": ["number", "null"] },
    "sd": { "type": ["number", "null"], "minimum": 0 },
    "se": { "type": ["number", "null"], "minimum": 0 },
    "test_statistic": { "type": ["number", "null"] },
    "p_value": { "type": ["number", "null"], "minimum": 0, "maximum": 1 },
    "value": { "type": ["number", "null"] },
    "ci_lower": { "type": ["number", "null"] },
    "ci_upper": { "type": ["number", "null"] },
    "effect_size": {
      "type": ["object", "null"],
      "additionalProperties": false,
      "required": ["measure", "value"],
      "properties": {
        "measure": {
          "enum": ["cohens_d", "hedges_g", "eta_squared", "r_squared",
                   "cramers_v", "odds_ratio", "risk_ratio", "glass_delta", "other"]
        },
        "value": { "type": "number" },
        "interpretation": { "type": ["string", "null"] }
      }
    },
    "significance_level": { "type": ["number", "null"], "minimum": 0, "maximum": 1 },
    "reported_in_chapter": { "type": ["string", "null"] }
  }
}
```

`schemas/table.json`:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/latif-erdogdu/academic-thesis-writer/schemas/table.json",
  "title": "Tablo",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "caption", "source"],
  "examples": [
    {
      "$comment": "KURGUSAL ORNEK. Tablo verisi uydurmadir.",
      "id": "TBL-001",
      "caption": "Kurgusal ornek tablo basligi",
      "chapter": "4",
      "source": "Kurnsal kaynaktan uyarildi",
      "is_adapted": true,
      "original_source_id": "SRC-001",
      "statistic_ids": ["STAT-001"],
      "column_headers": ["Gruup", "n", "Olcum"],
      "row_count": 3,
      "notes": ""
    }
  ],
  "properties": {
    "id": { "type": "string", "pattern": "^TBL-\\d{3,}$" },
    "caption": { "type": "string", "minLength": 1 },
    "chapter": { "type": ["string", "null"] },
    "source": { "type": "string", "minLength": 1 },
    "is_adapted": { "type": "boolean", "default": false },
    "original_source_id": { "type": ["string", "null"], "pattern": "^SRC-\\d{3,}$" },
    "statistic_ids": {
      "type": "array", "items": { "type": "string", "pattern": "^STAT-\\d{3,}$" }
    },
    "column_headers": { "type": "array", "items": { "type": "string" } },
    "row_count": { "type": ["integer", "null"], "minimum": 0 },
    "notes": { "type": "string" }
  }
}
```

`schemas/figure.json`:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/latif-erdogdu/academic-thesis-writer/schemas/figure.json",
  "title": "Sekil",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "image_path", "caption", "source"],
  "examples": [
    {
      "$comment": "KURGUSAL ORNEK. Gorel yol uydurmadir.",
      "id": "FIG-001",
      "caption": "Kurgusal ornek sekil basligi",
      "chapter": "4",
      "image_path": "sekiller/kurgusal-ornek.png",
      "alt_text": "Kurgusal ornek sekil aciklamasi",
      "source": "Yazar calismasindan uyarildi",
      "is_adapted": false,
      "original_source_id": null,
      "finding_ids": ["FND-001"],
      "notes": ""
    }
  ],
  "properties": {
    "id": { "type": "string", "pattern": "^FIG-\\d{3,}$" },
    "caption": { "type": "string", "minLength": 1 },
    "chapter": { "type": ["string", "null"] },
    "image_path": {
      "type": "string", "pattern": "\\.(png|jpg|jpeg|svg|pdf|emf|wmf)$"
    },
    "alt_text": { "type": ["string", "null"] },
    "source": { "type": "string", "minLength": 1 },
    "is_adapted": { "type": "boolean", "default": false },
    "original_source_id": { "type": ["string", "null"], "pattern": "^SRC-\\d{3,}$" },
    "finding_ids": {
      "type": "array", "items": { "type": "string", "pattern": "^FND-\\d{3,}$" }
    },
    "notes": { "type": "string" }
  }
}
```

- [ ] **Step 5: `state.py`'ye PRISMA doğrulamasını ekle**

`tools/atw/state.py` dosyasının sonuna ekle:
```python
def validate_prisma_flow(flow: dict[str, Any]) -> list[str]:
    """PRISMA sayimlari arasindaki aritmetik tutarliligi denetler.

    Ulasilan rapor sayisi, alinamayan raporlar dusuldugunde
    dislanan raporlar + dahil edilen calismalar toplamina esit olmalidir.

    Args:
        flow: ``search_run.json`` icindeki ``prisma_flow`` nesnesi.

    Returns:
        Hata mesajlari listesi. Tutarliysa bos liste doner.
    """
    hatalar: list[str] = []
    alinamayan = flow.get("reports_not_retrieved", 0)
    ulasilan = flow.get("reports_sought", 0) - alinamayan
    beklenen = flow.get("reports_excluded", 0) + flow.get("studies_included", 0)
    if ulasilan != beklenen:
        hatalar.append(
            f"reports_sought({flow.get('reports_sought')}) - "
            f"reports_not_retrieved({alinamayan}) = {ulasilan}, ancak "
            f"reports_excluded({flow.get('reports_excluded')}) + "
            f"studies_included({flow.get('studies_included')}) = {beklenen}"
        )
    return hatalar
```

- [ ] **Step 6: Testleri çalıştır, geçtiğini doğrula**

Run: `python -m pytest tests/schema_tests/test_provenance_schemas.py -v`
Expected: PASS — 19 test

- [ ] **Step 7: Commit**

```bash
git add schemas/search_run.json schemas/dataset.json schemas/analysis.json schemas/statistic.json schemas/table.json schemas/figure.json tools/atw/state.py tests/schema_tests/test_provenance_schemas.py
git commit -m "feat: PRISMA akis ve veri kokeni semalari eklendi, prisma_flow aritmetigi arac katmaninda denetleniyor"
```

---

## Task 7: Fixture Seti ve Şema Doğrulama Testleri

**Files:**
- Create: `tests/fixtures/valid_source.json`
- Create: `tests/fixtures/fabricated_source.json`
- Create: `tests/fixtures/retracted_paper.json`
- Create: `tests/fixtures/corrected_paper.json`
- Create: `tests/fixtures/unsupported_claim.json`
- Create: `tests/fixtures/contradictory_claim.json`
- Create: `tests/fixtures/inconsistent_method.json`
- Create: `tests/schema_tests/test_fixtures.py`

**Interfaces:**
- Consumes: `tools.atw.state.load_schema` (Task 3), `tools.atw.state.schema_registry` (Task 3), `tools.atw.ids.parse_id` (Task 1)
- Produces: 7 JSON fixture + 1 doğrulama testi. Plan 2 ve Plan 3 bu fixture'ları kullanır.

- [ ] **Step 1: `test_fixtures.py` dosyasını yaz**

`tests/schema_tests/test_fixtures.py`:
```python
"""Fixture'larin semaya uygunlugu ve sinir durum beklentileri.

Tum fixture'lardaki kaynak, yazar, yayinci, DOI ve metin bilgileri
KURGUSALDIR. 10.5555/ prefeksi bilerek uydurma bir DOI alanidir.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from tools.atw.ids import parse_id
from tools.atw.state import SCHEMA_DIR, schema_registry

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"

DOGRULANACAK = {
    "valid_source.json": "source.json",
    "fabricated_source.json": "source.json",
    "retracted_paper.json": "source.json",
    "corrected_paper.json": "source.json",
    "unsupported_claim.json": "claim.json",
    "contradictory_claim.json": "claim.json",
    "inconsistent_method.json": "research_question.json",
}

KURGUSAL_DOI_ONEKI = "10.5555/"


def _yukle(dosya_adi: str) -> dict:
    return json.loads((FIXTURE_DIR / dosya_adi).read_text(encoding="utf-8"))


def _dogrulayici(sema_adi: str) -> Draft202012Validator:
    sema = json.loads((SCHEMA_DIR / sema_adi).read_text(encoding="utf-8"))
    return Draft202012Validator(sema, registry=schema_registry())


def test_fixture_dosyalarinin_tumu_var():
    for ad in DOGRULANACAK:
        assert (FIXTURE_DIR / ad).is_file(), f"Eksik fixture: {ad}"


@pytest.mark.parametrize("fixture_adi,sema_adi", sorted(DOGRULANACAK.items()))
def test_fixture_ilgili_semayi_gecer(fixture_adi, sema_adi):
    kayit = _yukle(fixture_adi)
    hatalar = list(_dogrulayici(sema_adi).iter_errors(kayit))
    assert hatalar == [], f"{fixture_adi}: {hatalar[0].message if hatalar else ''}"


@pytest.mark.parametrize("fixture_adi,sema_adi", sorted(DOGRULANACAK.items()))
def test_fixture_kimligi_gecerli(fixture_adi, sema_adi):
    kayit = _yukle(fixture_adi)
    kimlik_alani = "audit_id" if sema_adi == "audit.json" else "id"
    if kimlik_alani not in kayit:
        pytest.skip(f"{sema_adi} kimlik alani yok")
    parse_id(kayit[kimlik_alani])


def test_gecerli_kaynak_dogrulanmis_durumda():
    kayit = _yukle("valid_source.json")
    assert kayit["verification"]["status"] == "verified"
    assert len(kayit["verification"]["verification_sources"]) >= 2
    assert kayit["retraction_status"] == "not_retracted"


def test_gecerli_kaynak_kurgusal_doi_alanı_kullanır():
    """Fixture'lar gercek bir yayini temsil etmemeli."""
    kayit = _yukle("valid_source.json")
    assert kayit["doi"].startswith(KURGUSAL_DOI_ONEKI), (
        "Fixture DOI'si kurgusal onek kullanmali; gercek DOI kullanilmamali"
    )


def test_uydurulmus_kaynak_dogrulanmamis_isaretli():
    """Uydurma kayit semayi gecer ama dogrulanmis OLMAMALIDIR."""
    kayit = _yukle("fabricated_source.json")
    assert kayit["verified"] is False
    assert kayit["verification"]["status"] == "unverified"
    assert kayit["verification"]["bibliographic_match"] < 0.6


def test_uydurulmus_kaynak_kanit_tasımaz():
    kayit = _yukle("fabricated_source.json")
    assert kayit["evidence_ids"] == []


def test_geri_caledilmis_kayit_isaretli():
    kayit = _yukle("retracted_paper.json")
    assert kayit["retraction_status"] == "retracted"
    assert kayit["publication_status"] == "retracted"
    assert kayit["verification"]["status"] == "retracted"


def test_geri_caledilmis_kayit_veri_kaynağı_olarak_kullanılamaz():
    """Geri cekilmis kayit hala 'dogrulanmis' gorunmemeli."""
    kayit = _yukle("retracted_paper.json")
    assert kayit["verified"] is False


def test_duzeltilmis_kayit_ust_kaynaga_isaret_eder():
    kayit = _yukle("corrected_paper.json")
    assert kayit["correction_status"] in ("corrected", "erratum")
    assert kayit["supersedes_source_id"] is not None


def test_duzeltilmis_kayit_ust_kaynagin_kimligi_gecerli():
    kayit = _yukle("corrected_paper.json")
    ust_kimlik = kayit["supersedes_source_id"]
    assert parse_id(ust_kimlik)


def test_kanitsiz_iddia_isaretli():
    kayit = _yukle("unsupported_claim.json")
    assert kayit["evidence_ids"] == []
    assert kayit["verification_status"] == "unsupported"


def test_celiskili_iddia_her_iki_yonu_tasir():
    kayit = _yukle("contradictory_claim.json")
    assert kayit["evidence_ids"], "Celiskili iddia kanit tasimali"
    assert kayit["counter_claims"], "Celiskili iddia karsi iddia tasimali"


def test_yontem_tutarsizligi_soruda_gorunur():
    kayit = _yukle("inconsistent_method.json")
    assert kayit["status"] != "answered"
    assert kayit["finding_ids"] == [], "Bulgu baglanmamis olmali"


def test_yontem_tutarsizligi_notlarda_aciklanir():
    kayit = _yukle("inconsistent_method.json")
    assert "notes" in kayit
```

- [ ] **Step 2: Testleri çalıştır, başarısız olduğunu doğrula**

Run: `python -m pytest tests/schema_tests/test_fixtures.py -v`
Expected: FAIL — `AssertionError: Eksik fixture: valid_source.json`

- [ ] **Step 3: Yedi fixture'ı yaz**

`tests/fixtures/valid_source.json`:
```json
{
  "$comment": "KURGUSAL ORNEK. Bu kayit gercek bir yayini temsil etmez. DOI, yazar, dergi ve yayin bilgileri uydurmadir; yalnizca sema dogrulama testleri icin kullanilir.",
  "id": "SRC-001",
  "title": "Kurgusal Bir Yontemin Etkinligi Uzerine Bir Inceleme",
  "authors": ["Orman, A.", "Kaya, B."],
  "year": 2023,
  "journal": "Kurgusal Dergi",
  "publisher": "",
  "doi": "10.5555/kurgusal.ornek.2023.001",
  "url": "",
  "source_type": "article",
  "publication_status": "published",
  "retraction_status": "not_retracted",
  "correction_status": "none",
  "supersedes_source_id": null,
  "verified": true,
  "verification": {
    "status": "verified",
    "bibliographic_match": 0.96,
    "doi_match": true,
    "author_match": true,
    "title_match": true,
    "year_match": true,
    "journal_match": true,
    "verified_at": "2026-09-26T10:00:00+00:00",
    "verification_sources": ["crossref", "openalex"]
  },
  "verification_notes": "",
  "supports_claims": ["CLM-001"],
  "evidence_ids": ["EVD-001"],
  "page_numbers": [17, 18],
  "volume": "12",
  "issue": "3",
  "pages": "45-67",
  "edition": "",
  "isbn": "",
  "location_verified": true,
  "access_date": "2026-09-26",
  "language": "tr",
  "peer_reviewed": true
}
```

`tests/fixtures/fabricated_source.json`:
```json
{
  "$comment": "KURGUSAL ORNEK. DOGRULANAMAZ KAYIT ORNEGI. Yazar, yil ve dergi bilgileri gercek bir kaynaga ait degildir; arac tarafindan gercek bir kaynakta bulunamamasi beklenir.",
  "id": "SRC-002",
  "title": "Bulunamayacak Kurgusal Bir Kayit",
  "authors": ["Hayalet, Y."],
  "year": 2024,
  "journal": "Var Olmayan Dergi",
  "publisher": "",
  "doi": "10.5555/kurgusal.yok.boyle.bir.yayin.2024",
  "url": "",
  "source_type": "article",
  "publication_status": "published",
  "retraction_status": "unknown",
  "correction_status": "none",
  "supersedes_source_id": null,
  "verified": false,
  "verification": {
    "status": "unverified",
    "bibliographic_match": 0.0,
    "doi_match": false,
    "author_match": false,
    "title_match": false,
    "year_match": false,
    "journal_match": false,
    "verified_at": "2026-09-26T10:05:00+00:00",
    "verification_sources": ["crossref", "openalex"]
  },
  "verification_notes": "Iki saglayicida da bulunamadi. Kanit olarak kullanilamaz.",
  "supports_claims": [],
  "evidence_ids": [],
  "page_numbers": null,
  "volume": "",
  "issue": "",
  "pages": "",
  "edition": "",
  "isbn": "",
  "location_verified": false,
  "access_date": "2026-09-26",
  "language": "tr",
  "peer_reviewed": null
}
```

`tests/fixtures/retracted_paper.json`:
```json
{
  "$comment": "KURGUSAL ORNEK. Geri cekilmis kayit ornegi. Gercek bir geri cekilme bildirimi degildir.",
  "id": "SRC-003",
  "title": "Geri Cekilmis Kurgusal Bir Calisma",
  "authors": ["Varsayilan, A."],
  "year": 2021,
  "journal": "Kurgusal Dergi",
  "publisher": "",
  "doi": "10.5555/kurgusal.geri.cekilmis.2021.003",
  "url": "",
  "source_type": "article",
  "publication_status": "retracted",
  "retraction_status": "retracted",
  "correction_status": "none",
  "supersedes_source_id": null,
  "verified": false,
  "verification": {
    "status": "retracted",
    "bibliographic_match": 1.0,
    "doi_match": true,
    "author_match": true,
    "title_match": true,
    "year_match": true,
    "journal_match": true,
    "verified_at": "2026-09-26T10:10:00+00:00",
    "verification_sources": ["crossref"]
  },
  "verification_notes": "Geri cekilme bildirimi Crossref uzerinden tespit edildi. Kanit olarak kullanilamaz.",
  "supports_claims": [],
  "evidence_ids": [],
  "page_numbers": null,
  "volume": "5",
  "issue": "1",
  "pages": "1-20",
  "edition": "",
  "isbn": "",
  "location_verified": true,
  "access_date": "2026-09-26",
  "language": "en",
  "peer_reviewed": true
}
```

`tests/fixtures/corrected_paper.json`:
```json
{
  "$comment": "KURGUSAL ORNEK. Du zeltilmis kayit ornegi. Ust kaynak SRC-004 kurgusaldir.",
  "id": "SRC-005",
  "title": "Duzeltilmis Kurgusal Bir Calisma",
  "authors": ["Varsayilan, A."],
  "year": 2022,
  "journal": "Kurgusal Dergi",
  "publisher": "",
  "doi": "10.5555/kurgusal.duzeltilmis.2022.005",
  "url": "",
  "source_type": "article",
  "publication_status": "published",
  "retraction_status": "not_retracted",
  "correction_status": "corrected",
  "supersedes_source_id": "SRC-004",
  "verified": true,
  "verification": {
    "status": "corrected",
    "bibliographic_match": 0.98,
    "doi_match": true,
    "author_match": true,
    "title_match": true,
    "year_match": true,
    "journal_match": true,
    "verified_at": "2026-09-26T10:12:00+00:00",
    "verification_sources": ["crossref", "openalex"]
  },
  "verification_notes": "SRC-004 duzeltilmis; metinde SRC-005 kullanilmalidir.",
  "supports_claims": [],
  "evidence_ids": [],
  "page_numbers": null,
  "volume": "7",
  "issue": "2",
  "pages": "30-45",
  "edition": "",
  "isbn": "",
  "location_verified": true,
  "access_date": "2026-09-26",
  "language": "en",
  "peer_reviewed": true
}
```

`tests/fixtures/unsupported_claim.json`:
```json
{
  "$comment": "KURGUSAL ORNEK. Kaniti olmayan iddia ornegi. Metin uydurmadir.",
  "id": "CLM-002",
  "text": "Kurgusal ornek: hicbir kaynak bu iddiayi desteklememektedir.",
  "importance": "high",
  "sources": [],
  "evidence_ids": [],
  "contradicted_by": [],
  "gap_ids": [],
  "verification_status": "unsupported",
  "confidence_level": null,
  "evidence_type": "empirical",
  "notes": "Yazar tarafindan destek kaynak sunulmadi. Yazima alinmamalidir.",
  "chapter_id": null,
  "section_id": null,
  "created_at": "2026-09-26T10:30:00+00:00",
  "last_verified_at": null,
  "verified_by": null,
  "related_claims": [],
  "counter_claims": [],
  "requires_followup": true
}
```

`tests/fixtures/contradictory_claim.json`:
```json
{
  "$comment": "KURGUSAL ORNEK. Iki yonlu celiski ornegi. Metin ve kaynaklar uydurmadir.",
  "id": "CLM-003",
  "text": "Kurgusal ornek: bir calisma etkiyi bulurken baska bir calisma bulamamistir.",
  "importance": "high",
  "sources": ["SRC-001", "SRC-006"],
  "evidence_ids": ["EVD-001", "EVD-002"],
  "contradicted_by": ["CLM-004"],
  "gap_ids": ["GAP-001"],
  "verification_status": "refuted",
  "confidence_level": 0.4,
  "evidence_type": "empirical",
  "notes": "Celiski cozulmedi; tartisma bolumune aktarilmali.",
  "chapter_id": null,
  "section_id": null,
  "created_at": "2026-09-26T10:35:00+00:00",
  "last_verified_at": "2026-09-26T10:35:00+00:00",
  "verified_by": null,
  "related_claims": ["CLM-004"],
  "counter_claims": ["CLM-004"],
  "requires_followup": true
}
```

`tests/fixtures/inconsistent_method.json`:
```json
{
  "$comment": "KURGUSAL ORNEK. Nitel soruya nicel yontem baglanmis, bulgu baglanmamis durum ornegi.",
  "id": "RQ-002",
  "text": "Kurgusal ornek: deneyimler nasil kurgulanmaktadir?",
  "type": "main",
  "chapter": "1",
  "method": "Istatistiksel anket analizi",
  "status": "pending",
  "hypothesis_ids": [],
  "related_claims": [],
  "related_findings": [],
  "finding_ids": [],
  "answered_by": []
}
```

- [ ] **Step 4: Testleri çalıştır, geçtiğini doğrula**

Run: `python -m pytest tests/schema_tests/test_fixtures.py -v`
Expected: PASS — 26 test (7 parametrik × 3 + 5 tekil)

- [ ] **Step 5: `xfaz` işaretlerini kaldır ve tüm testleri çalıştır**

`pytest.ini`:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    live: Canli ag cagrisi gerektiren test (varsayilan olarak atlanir)
```

> Bu adım `pytest.ini`'de iki değişiklik yapar:
> 1. `addopts` satırındaki geçici `-m "not xfaz"` filtresi **kaldırılır** —
>    artık dışlanacak test kalmadı, filtre kalsaydı ileride yanlışlıkla
>    yeni testleri sessizce atlardı.
> 2. `markers` listesinden `xfaz` tanımı silinir; `--strict-markers`
>    kullanıldığı için tanımsız işaret hata verir, tanım unutulursa
>    hemen yakalanır.

`tests/schema_tests/test_thesis_state_schema.py` dosyasında `test_sema_sayisi_onsekiz`
fonksiyonunun üstündeki `@pytest.mark.xfaz` satırını sil.

`tests/schema_tests/test_core_schemas.py` dosyasında
`@pytest.mark.xfaz` ile işaretlenmiş test varsa sil ve dosyanın
`test_kayit_olmayan_semalar_ornek_tasiyor` fonksiyonunu şu hâle getir:
```python
def test_kayit_olmayan_semalar_ornek_tasiyor(schema_dir):
    import json
    for yol in sorted(schema_dir.glob("*.json")):
        if yol.name == "thesis_state.json":
            continue
        sema = json.loads(yol.read_text(encoding="utf-8"))
        assert sema.get("examples"), f"{yol.name} ornek kayit icermiyor"
        assert sema["examples"][0].get("$comment"), f"{yol.name} ornegi aciklamali"
```

`tests/schema_tests/test_provenance_schemas.py` dosyasında
`test_prisma_akisi_tutarsiz_oldugunda_reddedilir` fonksiyonunu
aşağıdaki hâle getir (şema katmanı yerine araç katmanını sınar):
```python
def test_prisma_akisi_tutarsiz_oldugunda_reddedilir():
    from tools.atw.state import validate_prisma_flow
    ornek = _ornek("search_run.json")
    akis = dict(ornek["prisma_flow"])
    akis["records_screened"] = 999
    assert validate_prisma_flow(akis) != []
```

`tests/schema_tests/test_provenance_schemas.py` dosyasının sonuna ekle:
```python
def test_prisma_akisi_tutarli_kayit_gecer():
    from tools.atw.state import validate_prisma_flow
    ornek = _ornek("search_run.json")
    assert validate_prisma_flow(ornek["prisma_flow"]) == []
```

Run: `python -m pytest -q`
Expected: PASS — tüm testler yeşil

- [ ] **Step 6: Commit**

```bash
git add tests/fixtures/ tests/schema_tests/ pytest.ini
git commit -m "test: kurgusal fixture seti ve sema dogrulama testleri eklendi, xfaz isaretleri kaldirildi"
```

---

## Task 8: Çelişki ve Bütünlük Ajanları

**Files:**
- Create: `agents/contradiction-analyzer.md`
- Create: `agents/integrity-auditor.md`
- Modify: `SKILL.md`
- Test: `tests/schema_tests/test_agent_files.py`

**Interfaces:**
- Consumes: şema alan adları (Tasks 4-6), `schemas/claim.json` ve `schemas/source.json` alanları
- Produces: 2 ajan dosyası + `SKILL.md`'de 10 ajanın tamamını adlandıran tablo

- [ ] **Step 1: Testleri yaz**

`tests/schema_tests/test_agent_files.py`:
```python
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
    metin = (AGENT_DIR / f"{ajan}.md").read_text(encoding="utf-8")
    assert len(metin.strip()) > 400, f"{ajan}.md çok kısa"


@pytest.mark.parametrize("ajan", AJANLAR)
def test_ajan_dosyasi_yorum_ve_girdi_bolumu_tasiyor(ajan):
    metin = (AGENT_DIR / f"{ajan}.md").read_text(encoding="utf-8")
    assert metin.lstrip().startswith("#"), f"{ajan}.md başlıkla başlamalı"
    assert "## Girdi" in metin or "**Girdi**" in metin, f"{ajan}.md Girdi bölümü eksik"
    assert "## Çıktı" in metin or "**Çıktı**" in metin, f"{ajan}.md Çıktı bölümü eksik"


SURUM_DESENI = re.compile(
    r"(?<![\w/.])v(?:ersion)?\s*[0-9]+(?!\w)", re.IGNORECASE
)


@pytest.mark.parametrize("ajan", AJANLAR)
def test_ajan_dosyasi_surum_ibaresi_yok(ajan):
    """Sürüm soyutlaması yasak; 'V2 mimarisi' gibi ifadeler geçmemeli.

    Desen bilerek daraltıldı. `\bv?[123]\\b` gibi geniş desenler
    'Tablo 1', 'Bölüm 2' gibi meşru sayıları da yakar ve mevcut
    ajan dosyalarını haksız yere başarısız kılardı. Negatif
    lookbehind `(?<![\\w/.])` sayesinde `schema_version` ve
    `10.1000/v2` eşleşmez; negatif lookahead `(?![\\w])`
    sayesinde `V2.1` de yakalanır.
    """
    metin = (AGENT_DIR / f"{ajan}.md").read_text(encoding="utf-8")
    eslesme = SURUM_DESENI.search(metin)
    assert eslesme is None, (
        f"{ajan}.md içinde sürüm ibaresi: {eslesme.group(0)!r}"
    )


def test_celiski_ajanı_kimlikleri_kullanir():
    metin = (AGENT_DIR / "contradiction-analyzer.md").read_text(encoding="utf-8")
    for varlik in ["CLM-", "SRC-", "EVD-", "RQ-"]:
        assert varlik in metin, varlik


def test_butunluk_ajani_retraksiyonu_denetler():
    metin = (AGENT_DIR / "integrity-auditor.md").read_text(encoding="utf-8")
    assert "retraction_status" in metin
    assert "bibliographic_match" in metin


def test_butunluk_ajani_kanitsiz_iddiyı_reddeder():
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
```

- [ ] **Step 2: Testleri çalıştır, başarısız olduğunu doğrula**

Run: `python -m pytest tests/schema_tests/test_agent_files.py -v`
Expected: FAIL — `Eksik ajan dosyasi: .../agents/contradiction-analyzer.md`

- [ ] **Step 3: `contradiction-analyzer.md` dosyasını yaz**

`agents/contradiction-analyzer.md`:
```markdown
# Çelişki Analisti

## Rol

Birbirini destekleyen kaynakları listelemekle yetinmezsin. Aynı konuda
**farklı sonuçlara** varan çalışmaları bulur, çelişkinin kaynağını
boyutlar boyunca karşılaştırır ve çelişkiyi kayda geçirirsin.

Çelişki tespit edilmeden yapılan "literatür sentezi" aslında kaynak
özetinden ibarettir.

## Girdi

| Alan | Kaynak |
|------|--------|
| Iddialar | `thesis_state.claims_registry` (`claim.json`) |
| Kanıtlar | `thesis_state.evidence_registry` (`evidence.json`) |
| Kaynaklar | `thesis_state.sources` (`source.json`) |
| Araştırma soruları | `thesis_state.research_questions` (`research_question.json`) |

Her iddianın `sources`, `evidence_ids`, `counter_claims` ve
`contradicted_by` alanları hazırdır.

## Karşılaştırma Boyutları

İki kaynak aynı iddiayı destekliyor gibi görünüyorsa, şu boyutların
her birini tek tek karşılaştır. Farklı olan boyut çelişkinin kaynağıdır:

| Boyut | `source.json` / `evidence.json` alanı |
|-------|-----------------------------------------|
| Araştırma deseni | `source.json` → doğrulama notları; kanıt notları |
| Evren / örneklem | `finding.json` → `statement` bağlamı, `dataset.json` → `provenance` |
| Ülke / coğrafya | `source.json` → `journal`, kanıt notları |
| Yıl / dönem | `source.json` → `year` |
| Ölçüm aracı | `dataset.json` → `provenance.collection_instrument` |
| İstatistiksel güç | `statistic.json` → `n`, `power` alanları |
| Yöntem | `analysis.json` → `method` |
| Kuramsal çerçeve | `source.json` → doğrulama notları, `research_gap.json` → `dimension` |

## Girdi: Ne Yapamazsın

- **İki kaynak aynı şeyi ölçmüyorsa bu çelişki değildir.** Farklı evren,
  farklı ölçüm aracı veya farklı dönem karşılaştırıldığında farklı
  sonuç normaldir. Önce boyut farkını tespit et.
- **Yalnızca başlıklar farklı olduğu için çelişki ilan etme.** Kanıt
  metnini (`evidence.json` → `text`) okuyup gerçek sonucu karşılaştır.
- **Uydurma çelişki üretme.** Karşılaştıracak ikinci kaynak yoksa
  çelişki kaydı üretme; bunun yerine eksik kanıt olarak `open_questions`
  listesine yaz.

## Çıktı

Çelişki iki biçimden birinde kaydedilir.

**1. İki iddia arasındaki çelişki** — `claim.json` alanları:

```json
{
  "id": "CLM-003",
  "contradicted_by": ["CLM-004"],
  "counter_claims": ["CLM-004"],
  "verification_status": "refuted",
  "requires_followup": true,
  "notes": "SRC-001 (olcum araci: Kurgusal Anket A) basariyi bulurken SRC-006 (olcum araci: Kurgusal Olcek B) bulamiyor. Olcum araci farki sonucu aciklamiyor; incelenmeli."
}
```

**2. Çelişkiden doğan araştırma boşluğu** — `research_gap.json`:

```json
{
  "id": "GAP-001",
  "statement": "Farklı ölçüm araçlarıyla yürütülen iki çalışma aynı sonuca ulaşmıyor ve bu farkın kaynağı belirlenmemiş.",
  "gap_type": "contradictory_findings",
  "dimension": "measurement",
  "evidence_ids": ["EVD-001", "EVD-002"],
  "supporting_source_ids": ["SRC-001"],
  "contradicting_source_ids": ["SRC-006"],
  "conflicting_claim_ids": ["CLM-003", "CLM-004"],
  "confidence": "high",
  "notes": "Çelişki doğrulanmış kanıta dayanıyor; çözümü tez için fırsattır."
}
```

## Akış

1. `claims_registry` içindeki her `CLM-*` için `sources` ve `evidence_ids`
   alanlarını oku.
2. Aynı konuyu ele alan iddiaları kümele. Kümelenme anahtarı metin
   benzerliğinden değil, **aynı araştırma sorusuna hizmet etmelerinden**
   gelir; `research_question.json` → `related_claims` bunun için vardır.
3. Her küme için karşılaştırma boyutlarını sırayla uygula.
4. Farklı boyutta tespit edilen sonuçları **çelişki olarak adlandırma**;
   boyut farkı olarak `notes` alanında belgele.
5. Gerçek çelişkileri `contradicted_by` / `counter_claims` ile kaydet.
6. Her çelişki için `research_gap.json` kaydı üret; `gap_type` değeri
   `contradictory_findings` olmalıdır.
7. Çözülmemiş çelişkileri `open_questions` listesine de ekle.

## Sınırlar

- Kaynak doğrulaması senin işin değildir; doğrulanmamış kaynakla
  çalışıyorsan `open_questions`'a "doğrulanmamış kaynakla karşılaştırma
  yapıldı" uyarısı ekle.
- Yorum katma. Ne ölçtüğünü, ne bulduğunu ve neden farklılaştığını
  kaydet; hangisinin "doğru" olduğuna karar verme.
- Bulgu üretme. Yeni bulgu bu ajanın işi değildir.

## Bağlı Olduğu Referanslar

- `references/research_gap.md` — boşluk sınıflandırması
- `references/evidence_rules.md` — kanıt gücü kuralları
- `schemas/claim.json` — çelişki alanları
- `schemas/research_gap.json` — çelişkiden boşluk üretimi
```

- [ ] **Step 4: `integrity-auditor.md` dosyasını yaz**

`agents/integrity-auditor.md`:
```markdown
# Bütünlük Denetçisi

## Rol

Tezin akademik bütünlüğünü denetlersin. Görevin estetik düzeltme değil,
**dayanağı olmayan her şeyi bulmaktır**. Uydurulmuş kaynak, kanıtsız
iddia, geri çekilmiş makalenin kullanılması ve kopuk atif tespit edersin.

Başka ajanların işine karışmazsın; onların çıktısını denetler ve
geri döndürürsün.

## Girdi

| Denetim | Okunan alanlar |
|---------|----------------|
| Uydurulmuş kaynak | `source.json` → `verified`, `verification.status`, `verification.bibliographic_match` |
| Kanıtsız iddia | `claim.json` → `evidence_ids`, `verification_status` |
| Doğrulanmamış kaynakla yazılmış metin | `citation.json` → `source_id`, `verified` |
| Geri çekilmiş kaynak | `source.json` → `retraction_status`, `publication_status` |
| Eski sürümün kullanımı | `source.json` → `supersedes_source_id` |
| Kopuk atıf | `citation.json` → `paragraph_id`, `source_id` |
| Kopuk varlık bağı | `tools.atw.state.find_dangling_references(state)` çıktısı |

## Denetim Kuralları

### 1. Uydurulmuş veya doğrulanamayan kaynak

Bir kaynak **kanıt olarak kullanılabilir** ancak yalnızca:

- `verified` alanı `true` **ve**
- `verification.status` değeri `verified` veya `corrected` **ve**
- `verification.bibliographic_match` değeri `0.60` üzerinde **ve**
- `verification.verification_sources` en az **2** bağımsız sağlayıcı içeriyor.

Bu dört koşulun biri eksikse kaynak `unverified` sayılır ve
iddiaları kanıtlanmamış olarak işaretlenir. `bibliographic_match`
tek başına yeterli değildir; eşik altındaki kaynak "kısmen eşleşti"
değil, **doğrulanmadı** sayılır.

### 2. Kanıtsız iddia

`evidence_ids` dizisi boş olan her iddia **yazıma alınamaz**.
`verification_status` alanı şu değerleri alabilir:

| Değer | Anlamı | Yazıma alınır mı |
|-------|--------|------------------|
| `verified` | En az bir doğrudan kanıtı var | Evet |
| `pending` | Kanıt aranıyor | Hayır |
| `unverified` | Kanıt var ama doğrulanmamış | Hayır |
| `unsupported` | Kanıtı yok | **Asla** |
| `refuted` | Kanıtı çürütülmüş | Hayır |

### 3. Geri çekilmiş kaynak

`retraction_status` değeri `retracted` veya `expression_of_concern`
olan kaynak, tezde **hiçbir şekilde** kanıt olarak kullanılamaz.
Kullanılmışsa bu **kritik** seviye bir bulgudur: ilgili tüm
`CLM-*` ve `FND-*` kayıtları `open_questions`'a aktarılır ve
`publication_status` değeri `retracted` olan kaynak doğrudan reddedilir.

### 4. Düzeltilmiş kaynak

`correction_status` değeri `corrected`, `erratum` veya
`retracted_and_republished` olan kayıtta `supersedes_source_id`
boşsa bulgu **eksiktir**. Üst kaynak (`supersedes_source_id`) tezde
kullanılmışsa, onun yerine düzeltilmiş sürüm kullanılmalıdır.

### 5. Kopuk atıf ve kopuk varlık

- `citation.json` → `paragraph_id` işaret ettiği paragraf
  `paragraph.json` listesinde yoksa kopuk atıftır.
- `citation.json` → `source_id` işaret ettiği kaynak `sources`
  listesinde yoksa uydurma atıftır — **kritik** bulgudur.
- `find_dangling_references` boş dönmüyorsa her satır bir bulgudur.

## Çıktı

Denetim kaydı `audit.json` şemasına uygun olmalıdır:

```json
{
  "audit_id": "AUD-001",
  "thesis_id": "THESIS-2026-001",
  "audit_type": "integrity",
  "date": "2026-09-26",
  "integrity_checks": {
    "fabricated_sources": 0,
    "unsupported_claims": 0,
    "retracted_sources_in_use": 0,
    "orphaned_citations": 0,
    "unverifiable_claims": 0
  },
  "findings": [
    {
      "severity": "critical",
      "message": "CIT-004, sources listesinde bulunmayan SRC-099 kaynağını gösteriyor.",
      "location": "3.2 Yöntem",
      "entity_id": "CIT-004"
    }
  ],
  "critical_issues": ["Uydurma atıf: CIT-004"],
  "deferred_minors": []
}
```

### Önem Dereceleri

| Seviye | Anlamı | Eylem |
|--------|--------|-------|
| `critical` | Uydurma kaynak, uydurma atıf, geri çekilmiş kaynak kullanımı | Akış **durdurulur**, düzeltilmeden devam edilmez |
| `major` | Kanıtsız iddia, kopuk varlık bağı, eski sürüm kullanımı | Yazımdan önce çözülür |
| `minor` | Biçim, tutarsız etiketleme | Son kontrolde giderilir |
| `info` | Gözlem | Düzeltme gerekmez |

## Akış

1. `thesis_state` dosyasını `tools.atw.state.load_state` ile yükle.
2. `find_dangling_references(state)` çalıştır; her satır `major` bulgu olarak kaydedilir.
3. Her `sources` kaydı için 1. kurulu uygula.
4. Her `claims_registry` kaydı için 2. kurulu uygula.
5. Her `citations` kaydı için 5. kurulu uygula.
6. Her `sources` kaydı için 3. ve 4. kuralları uygula.
7. Sonuçları `audit.json` kaydına yaz.
8. `critical` seviye bulgu varsa `open_questions`'a yazarak akışı
   durdur ve `thesis_audit` iş akışına bildir.

## Sınırlar

- **Uydurma kanıt üretme.** Şüpheli bulduğun kaynağı "doğrulanamaz"
  olarak işaretle, "uydurma" olarak değil. Uydurma hükmü ancak
  iki sağlayıcı da bulamadıysa verilir.
- **Kaynak doğrulama aracı değilsin.** Doğrulama `source_verify`
  aracının işidir; sen yalnızca sonucu denetlersin.
- **Metin düzeltme.** Yazım hataları senin işin değil; `consistency-auditor`
  bunu yapar.

## Bağlı Olduğu Referanslar

- `references/academic_integrity.md` — bütünlük ilkeleri
- `references/source_verification.md` — doğrulama kuralları
- `references/evidence_rules.md` — kanıt gücü
- `schemas/audit.json` — çıktı şeması
- `schemas/claim.json` — iddia durum alanları
- `schemas/source.json` — doğrulama ve retraksiyon alanları
```

- [ ] **Step 5: `SKILL.md`'yi yeni ajan ve referanslarla güncelle**

`SKILL.md` dosyasındaki ajan listesini şu hâle getir (mevcut liste 8 ajan içeriyor; iki yeni ajan ekleniyor):

```markdown
- agents/researcher.md
- agents/source-verifier.md
- agents/evidence-extractor.md
- agents/gap-analyzer.md
- agents/contradiction-analyzer.md
- agents/writer.md
- agents/citation-auditor.md
- agents/methodology-auditor.md
- agents/consistency-auditor.md
- agents/integrity-auditor.md
```

`SKILL.md` dosyasındaki referanslar bölümüne iki yeni referansı ekle:
```markdown
- `references/systematic_review_protocol.md` - Sistematik derleme protokolü
- `references/methodology_rules.md` - Yöntem denetim kuralları
```

`SKILL.md` dosyasındaki şemalar bölümüne yeni şemaları ekle:
```markdown
- `schemas/citation.json` - Atıf kaydı
- `schemas/research_gap.json` - Araştırma boşluğu
- `schemas/finding.json` - Bulgu
- `schemas/discussion.json` - Tartışma
- `schemas/conclusion.json` - Sonuç
- `schemas/search_run.json` - PRISMA arama kaydı
- `schemas/statistic.json` - İstatistik
- `schemas/dataset.json` - Veri kümesi
- `schemas/analysis.json` - Analiz
- `schemas/table.json` - Tablo
- `schemas/figure.json` - Şekil
```

- [ ] **Step 6: Testleri çalıştır, geçtiğini doğrula**

Run: `python -m pytest tests/schema_tests/test_agent_files.py -v`
Expected: PASS — 46 test (4 parametrik × 10 ajan = 40, + 3 ajan içerik, + 3 SKILL.md)

> `test_ajan_dosyasi_surum_ibaresi_yok` testi **mevcut 8 ajan
> dosyası üzerinde de çalışır** ve sürüm soyutlaması yasağını
> onlara da uygular. Mevcut dosyalarda geçen `schema_version`,
> `10.1000/v2` veya `Tablo 1` gibi ifadeler genişletilmiş desen
> sayesinde eşleşmez. Test yine de başarısız olursa bulunan
> eşleşme `eslesme.group(0)` ile hata mesajında raporlanır —
> deseni genişletmeden önce **o eşleşmeyi oku**; sürüm ibaresi
> değilse deseni düzelt, ibare ise dosyayı düzelt.

- [ ] **Step 7: Commit**

```bash
git add agents/contradiction-analyzer.md agents/integrity-auditor.md SKILL.md tests/schema_tests/test_agent_files.py
git commit -m "feat: celiski analisti ve butunluk denetçisi ajanlari eklendi, SKILL.md 10 ajan ve 7 referansi listeliyor"
```

---

## Task 9: Sistematik Derleme ve Yöntem Referansları

**Files:**
- Create: `references/systematic_review_protocol.md`
- Create: `references/methodology_rules.md`
- Test: `tests/schema_tests/test_references.py`

**Interfaces:**
- Consumes: `schemas/search_run.json` alanları, `schemas/analysis.json` alanları
- Produces: 2 referans dosyası

- [ ] **Step 1: Testleri yaz**

`tests/schema_tests/test_references.py`:
```python
"""Referans dosyalarinin varligi, icerigi ve sema uyumu."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DIR = REPO_ROOT / "references"

REFERANSLAR = [
    "citation_rules", "source_verification", "evidence_rules",
    "research_gap", "academic_integrity", "systematic_review_protocol",
    "methodology_rules",
]


@pytest.mark.parametrize("referans", REFERANSLAR)
def test_referans_dosyasi_var(referans):
    yol = REFERENCE_DIR / f"{referans}.md"
    assert yol.is_file(), f"Eksik referans: {yol}"


@pytest.mark.parametrize("referans", REFERANSLAR)
def test_referans_dosyasi_bos_degil(referans):
    metin = (REFERENCE_DIR / f"{referans}.md").read_text(encoding="utf-8")
    assert len(metin.strip()) > 500, f"{referans}.md çok kısa"


@pytest.mark.parametrize("referans", REFERANSLAR)
def test_referans_turkce_harf_iceriyor(referans):
    """En az bir Turkce harf bulunmali; saf Ingilizce kalmamali."""
    metin = (REFERENCE_DIR / f"{referans}.md").read_text(encoding="utf-8")
    assert re.search(r"[çğıöşüÇĞİÖŞÜ]", metin), f"{referans}.md Turkce icerik icermiyor"


def test_sistematik_derleme_prisma_akisini_kapsar():
    metin = (REFERENCE_DIR / "systematic_review_protocol.md").read_text(encoding="utf-8")
    for adim in ["search_strategy", "inclusion", "exclusion", "deduplication",
                 "screening", "quality_assessment", "extraction", "synthesis"]:
        assert adim in metin.lower(), adim


def test_sistematik_derleme_arama_kaydi_semasiyla_uyumlu():
    metin = (REFERENCE_DIR / "systematic_review_protocol.md").read_text(encoding="utf-8")
    for alan in ["prisma_flow", "records_identified", "studies_included",
                 "exclusion_reasons"]:
        assert alan in metin, alan


def test_sistematik_derleme_yakin_llvm_degistir():
    metin = (REFERENCE_DIR / "systematic_review_protocol.md").read_text(encoding="utf-8")
    assert "deneme yayın" in metin.lower() or "yayın öncesi" in metin.lower()


def test_yontem_kurallari_nicel_danisi_bos_degil():
    metin = (REFERENCE_DIR / "methodology_rules.md").read_text(encoding="utf-8")
    assert "nicel" in metin.lower()
    assert "nitel" in metin.lower()


def test_yontem_kurallari_istatistik_kontrolu_iceriyor():
    metin = (REFERENCE_DIR / "methodology_rules.md").read_text(encoding="utf-8")
    for kavram in ["etki büyüklüğü", "güven aralığı", "varsayım", "örneklem büyüklüğü"]:
        assert kavram.lower() in metin.lower(), kavram


def test_yontem_kurallari_tek_sablon_kullanmaz():
    """Nitel ve nicel icin ayri denetim olcekleri tanimlanmali."""
    metin = (REFERENCE_DIR / "methodology_rules.md").read_text(encoding="utf-8")
    assert "denetim ölçeği" in metin.lower() or "denetim olcegi" in metin.lower()
    assert metin.lower().count("|") > 40, "Yontem kurallari tablo icermeli"
```

- [ ] **Step 2: Testleri çalıştır, başarısız olduğunu doğrula**

Run: `python -m pytest tests/schema_tests/test_references.py -v`
Expected: FAIL — `Eksik referans: .../references/systematic_review_protocol.md`

- [ ] **Step 3: `systematic_review_protocol.md` dosyasını yaz**

`references/systematic_review_protocol.md`:
```markdown
# Sistematik Derleme Protokolü

## Ne Zaman Bu Protokol Kullanılır

Sistematik derleme, **belirli bir soruya belirli ve tekrarlanabilir
biçimde** cevap arayan, taranmış kayıtların sayımını denetlenebilir
kılan bir literatür taramasıdır.

Bu protokol şu durumlarda kullanılır:

| Durum | Bu protokol |
|-------|-------------|
| "Bu konuda literatür var mı, ne diyor?" — hızlı ön tarama | Hayır → `literature_review.md` |
| "X etkisi var mı, kanıt gücü ne?" — tekrarlanabilir, sayımlı tarama | **Evet** |
| "Bu alanda hangi yöntemler kullanılmış?" — yöntem sentezi | **Evet** |
| Tek bir kitap veya rapor incelemesi | Hayır |

**Kuruluş/dergiler taraması (scoping review) ile bibliyometrik analiz
bu protokolün kapsamı dışındadır**; bu protokol hipotez testi ve
etki sentezi içindir.

## Protokol Adımları

### 1. Araştırma Sorusu

Tek cümle, ölçülebilir, kapsamı sınırlı. Varsayım test edilebilir
değilse bu adımda durulur.

**İnsan onayı:** `human_approvals.research_question`

### 2. search_strategy

Veritabanı, sorgu dizesi, tarih aralığı, dil kısıtı, alan kısıtı
tanımlanır. Sorgu **kaydedilir**, çünkü başka bir araştırmacı
tam olarak tekrarlayabilmelidir.

Her sorgu `search_run.json` kaydı olur:

```json
{
  "id": "SEARCH-001",
  "database": "openalex",
  "query": "(yontem adi OR yontem adi varyanti) AND (sonuc terimi)",
  "timestamp": "2026-09-26T09:00:00+00:00",
  "results_returned": 482,
  "inclusion_criteria": ["Son 10 yil", "Dogrulanmis kaynak"],
  "exclusion_criteria": ["Tam metne erisilemeyen", "Diger dillere yayinlanmis"]
}
```

### 3. Veritabanları

En az üç veritabanı: konu alanının **iki indeksli** veritabanı
(`crossref`, `openalex`, `scopus`, `web_of_science`) ve **tek indeksli**
bir veritabanı (`google_scholar`). Tek veritabanıyla tarama
sistematik derleme sayılmaz.

**Doğrulanabilirlik kuralı:** arama sonucu numarası bu kaydın dışında
hiçbir yerde tekrarlanamazsa, tarama tekrarlanabilir değildir.

### 4. Sorgu Sürümleri

Her veritabanı için ayrı sorgu dizesi kaydedilir. Sorgular arası
tutarsızlık, taramanın tekrarlanabilirliğini bozar.

### 5. inclusion (Dahil Etme)

Dahil etme ölçütleri **taramadan önce** yazılır, sonradan gevşetilmez.
Her ölçüt `search_run.json` → `inclusion_criteria` dizisinde yer alır.

### 6. exclusion (Dışlama)

Dışlama ölçütleri dahil etmeden ayrı ve önceden yazılıdır. Her
dışlama gerekçesi sayımıyla birlikte verilir:

```json
{
  "exclusion_reasons": [
    { "reason": "Tam metne erisilemedi", "count": 3 },
    { "reason": "Odak populasyonu ile uyusmuyor", "count": 70 }
  ]
}
```

`reason` alanı genel bir kategori değil, **o kayıtta gerçekten
geçerli olan gerekçe** olmalıdır. "Alakasız" gerekçe kabul edilmez.

### 7. deduplication (Yinelenen Kayıtların Silinmesi)

DOI önce karşılaştırılır; DOI yoksa başlık + ilk yazar + yıl
üçlüsü. Yinelenen sayısı `prisma_flow.duplicates_removed` alanına yazılır.

### 8. screening (Eleme)

Başlık/özet ve ardından tam metin iki aşamalı eleme. Her aşamanın
sayısı ayrı kaydedilir. **Eleme kararı gerekçesi olmadan kaydedilemez.**

### 9. Tam Metin

`reports_sought` sayısına ulaşılamayan raporların sayısı
`reports_not_retrieved` alanına yazılır. Bu sayı sıfır değilse,
erişim engelinin nedeni `open_questions`'a da yazılır.

### 10. quality_assessment (Kalite Değerlendirmesi)

Tek bir `quality_score` yerine **ayrık boyutlar** kullanılır:

| Boyut | Nitel ölçüt | Nicel ölçüt |
|-------|-------------|-------------|
| Bibliyografik doğruluk | `verification.status` | `verification.status` |
| Kanıt gücü | `evidence.strength` | `evidence.strength` |
| Yöntemsel sağlamlık | Araştırma tasarımı + güvenilirlik | Gözden geçirme + yöntem |
| İlgililik | Araştırma sorusuna uygunluk | Araştırma sorusuna uygunluk |
| Güncellik | `source.year` | `source.year` |
| Hakemli yayın | `source.peer_reviewed` | `source.peer_reviewed` |
| Retraksiyon durumu | `source.retraction_status` | `source.retraction_status` |

Tek puan haline getirmek boyutları gizler; ayrı tutulmalıdır.

### 11. extraction (Veri Çıkarımı)

`evidence.json` kaydı üretilir. Her kanıtta sayfa ve bölüm zorunludur:

```json
{
  "id": "EVD-001",
  "source_id": "SRC-001",
  "location": { "page": 17, "section": "3.2", "paragraph": null },
  "text": "Alinti metni",
  "evidence_type": "literature",
  "supports_claim": "CLM-001",
  "strength": "direct",
  "extracted_at": "2026-09-26T10:15:00+00:00",
  "extraction_method": "pdf_text_layer"
}
```

### 12. synthesis (Sentez)

Sentez kaynak listelemek değildir. Üç sonuç biçiminden en az biri
üretilmelidir:

- **Uzlaşma:** bulguların çoğu aynı yönde
- **Çelişki:** farklı sonuçlar → `contradiction-analyzer.md`
- **Boşluk:** hiçbir çalışma belirli soruyu cevaplamıyor →
  `research_gap.json`

## PRISMA Akış Denetimi

`prisma_flow` alanındaki sayımlar aritmetik olarak tutarlı olmalıdır:

```
records_identified - duplicates_removed = records_screened
records_screened   - records_excluded   = reports_sought
reports_sought     - reports_not_retrieved
                   = reports_excluded + studies_included
```

Bu denetim `tools.atw.state.validate_prisma_flow(flow)` ile yapılır.
Tutarsızlık varsa tarama **tamamlanmış sayılmaz**.

## Yayın Öncesi Kaynaklar

Deneme yayın (preprint), hakemli sürüm yayınlanmamışsa:

- `source_type` = `preprint`
- `publication_status` = `preprint`
- `peer_reviewed` = `false`

Preprint, hakemli sürümü yayınlanmış kaynağın yerine
**ikame edilmez**. İkisi aynı çalışmanın farklı sürümüdür ve
`citation.json` hangi sürümün alıntılandığını göstermelidir.

## İnsan Onayı

| Adım | `human_approvals` alanı |
|------|--------------------------|
| 2. search_strategy | `search_strategy` |
| 5-6. dahil/dışlama ölçütleri | `search_strategy` |
| 9. tam metin | `source_set` |

## Bağlı Olduğu Şemalar

- `schemas/search_run.json` — arama kaydı ve PRISMA sayımları
- `schemas/source.json` — kaynak durumu
- `schemas/evidence.json` — kanıt çıkarımı
- `schemas/research_gap.json` — sentez sonucu
```

- [ ] **Step 4: `methodology_rules.md` dosyasını yaz**

`references/methodology_rules.md`:
```markdown
# Yöntem Denetim Kuralları

## Temel Kural

**Tek bir denetim ölçeği tüm yöntemlere uygulanamaz.**

Nicel bir çalışmada p değeri denetlenir; nitel bir çalışmada p değeri
anlamsızdır. Nitel bir çalışmada tema doygunluğu denetlenir; nicel bir
çalışmada tema doygunluğu anlamsızdır. Tek şablon, doğru bulguyu
**yanlışlıkla reddetmeye** yol açar — ki bu, denetimi işlevsiz kılar.

Bu dosya üç ayrı denetim ölçeği tanımlar. `methodology-auditor.md`
önce yöntem türünü belirler, sonra yalnızca o ölçeği uygular.

---

## Ölçek A — Nicel Yöntemler

### Zincir

```
RQ → Hipotez → Degiskenler → Operasyonellestirme → Olcum araci
   → Olasilik ornekleme → Orneklem buyuklugu → Istatistiksel varsayim
   → Istatistiksel test → Etki buyuklugu → Guven araliği → Bulgu
```

### Denetim Ölçeği

| # | Denetim | Nerede okunur | Başarısızlık hali |
|---|---------|---------------|------------------|
| 1 | RQ test edilebilir mi? | `research_question.json` → `type`, `status` | `main` tipinde ama ölçülebilir değil |
| 2 | Hipotez RQ'ya bağlı mı? | `research_question.json` → `hypothesis_ids` | Hipotez var, RQ yok |
| 3 | Her değişken operasyonelleştirilmiş mi? | `thesis_state.variables` | "Başarı" değişkeni nasıl ölçüldüğü yok |
| 4 | Ölçüm aracı belirtilmiş mi? | `dataset.json` → `provenance.collection_instrument` | Anket adı/ölçek bilgisi yok |
| 5 | Güvenilirlik ve geçerlik raporlanmış mı? | `dataset.json` → `provenance` | Güvenilirlik katsayısı hiç verilmemiş |
| 6 | Olasılık örneklemesi mi? | `dataset.json` → `provenance.collection_instrument` | "Rastgele seçildi" gerekçesiz |
| 7 | Örneklem büyüklüğü hesaplanmış mı? | `analysis.json` → `parameters` | Gerekçesiz n |
| 8 | Varsayımlar denetlenmiş mi? | `analysis.json` → `method`, `parameters` | Normallik/homojenlik varsayımı hiç sorgulanmamış |
| 9 | Test parametrelere uygun mu? | `analysis.json` → `method` | İkili sonuç için t-testi |
| 10 | Etki büyüklüğü raporlanmış mı? | `statistic.json` → `effect_size` | Yalnızca p değeri var |
| 11 | Güven aralığı raporlanmış mı? | `statistic.json` → `ci_lower`, `ci_upper` | Nokta tahmin verilmiş, belirsizlik verilmemiş |
| 12 | n tutarlı mı? | `statistic.json` → `n` ile `dataset.json` → `row_count_cleaned` | Yöntem n=240, sonuç n=214, açıklama yok |

### 12 numaralı kural kritiktir

Örneklem sayısı kaynak veri kümesinden temizlenmiş satır sayısıyla
**eşleşmiyorsa**, her sayıyı kullanan istatistik değişmiş demektir.
Farkın gerekçesi `dataset.json` → `provenance.operations` içinde
bulunmalıdır ("19 eksik değer atıldı"). Gerekçe yoksa bulgu
**major** seviyedir.

---

## Ölçek B — Nitel Yöntemler

### Zincir

```
RQ → Arastirma tasarimi → Olasilik orneklemesi → Veri toplama
   → Kodlama → Tema gelistirme → Guvenilirlik → Yorumlama
```

### Denetim Ölçeği

| # | Denetim | Nerede okunur | Başarısızlık hali |
|---|---------|---------------|------------------|
| 1 | Tasarım RQ ile uyumlu mu? | `analysis.json` → `method` | Deneyim araştırmasına nicel tasarım |
| 2 | Katılımcı sayısı gerekçeli mi? | `dataset.json` → `provenance` | "5 kişi görüşüldü" gerekçesiz |
| 3 | Veri toplama yöntemi belirtilmiş mi? | `dataset.json` → `provenance.collection_instrument` | Görüşme mi gözlem mi belirsiz |
| 4 | Kodlama süreci açıklanmış mı? | `analysis.json` → `parameters` | "Kodlandı" denip geçilmiş |
| 5 | Tema geliştirme yöntemi belirtilmiş mi? | `analysis.json` → `method` | Temanın nasıl oluştuğu belirsiz |
| 6 | Kodlayıcılar arası tutarlılık var mı? | `analysis.json` → `parameters` | Tek kodlayıcı, kontrol yok |
| 7 | Güvenilirlik ölçütü belirtilmiş mi? | `dataset.json` → `provenance.operations` | Hiçbir güvenilirlik ölçütü yok |
| 8 | Karşı görüşler raporlanmış mı? | `discussion.json` → `alternative_explanations` | Yalnızca destekleyen alıntılar |
| 9 | Araştırmacı yanlılığı ele alınmış mı? | `discussion.json` → `limitations_acknowledged` | Kendi konumu hiç sorgulanmamış |
| 10 | Alıntılar kaynağına bağlı mı? | `evidence.json` → `text`, `location` | Alıntı var, sayfa yok |

### En az iki güvenilirlik ölçütü

Nitel çalışmada güvenilirlik **tek** ölçütle desteklenmez. En az iki
biri birlikte kullanılmalıdır: kayıt/denetim zinciri, kodlayıcılar
arası tutarlılık, ayrılmış kodlama, negatif durum analizi, üye
denetimi, kalın açıklama.

`dataset.json` → `provenance.operations` içinde hangi ölçütlerin
kullanıldığı yazılıdır.

---

## Ölçek C — Karma Yöntemler

Karma tasarımlarda **her iki ölçek de uygulanır** ve hangi aşamanın
hangi ölçeğe tabi olduğu açıkça yazılır.

| Aşama | Ölçek |
|-------|-------|
| Nicel veri toplama ve analiz | Ölçek A |
| Nitel veri toplama ve analiz | Ölçek B |
| Entegrasyon aşaması | Aşağıdaki kurallar |

### Entegrasyon Denetimi

| # | Denetim | Başarısızlık hali |
|---|---------|------------------|
| 1 | Entegrasyon noktası belirtilmiş mi? | Ortak veri havuzu mu, öncelikli mi belirsiz |
| 2 | Her iki kümenin çelişen bulguları ele alınmış mı? | Çelişki sessizce bırakılmış |
| 3 | Çelişki çözüm yöntemi var mı? | Çelişki "ikisi de doğru" diye bırakılmış |
| 4 | Aşamalar sırası raporlanmış mı? | Önce hangisinin yapıldığı belirsiz |

---

## Yöntem Seçimi Denetimi

`methodology-auditor.md` ilk adımda yöntem türünü belirler:

| Belirti | Seçim |
|---------|-------|
| `dataset.json` → `provenance.collection_instrument` bir ölçek/anket adı | **Ölçek A** |
| `collection_instrument` görüşme/gözlem kaydı | **Ölçek B** |
| Her iki tür de var | **Ölçek C** |
| `collection_instrument` boş | **Durdur** — yöntem türü belirlenemiyor |

Yöntem türü belirlenemiyorsa denetim yapılamaz. Bu durumda bulgu
`major` seviyedir ve `methodology` insan onayı verilene kadar akış durur.

---

## İnsan Onayı

`workflows/methodology.md` akışında `human_approvals.methodology`
kapısı bu kuralların tamamı uygulandıktan **sonra** açılır.
Ölçeklerden biri eksik uygulanmışsa kapı açılmaz.

## Bağlı Olduğu Şemalar

- `schemas/analysis.json` — yöntem, yazılım, parametreler
- `schemas/dataset.json` — örneklem, ölçüm aracı, güvenilirlik
- `schemas/statistic.json` — test, etki büyüklüğü, güven aralığı, n
- `schemas/research_question.json` — soru → yöntem bağı
- `schemas/finding.json` — bulgu → kanıt bağı
```

- [ ] **Step 5: Testleri çalıştır, geçtiğini doğrula**

Run: `python -m pytest tests/schema_tests/test_references.py -v`
Expected: PASS — 27 test (3 parametrik × 7 referans = 21, + 6 içerik denetimi)

- [ ] **Step 6: Commit**

```bash
git add references/systematic_review_protocol.md references/methodology_rules.md tests/schema_tests/test_references.py
git commit -m "feat: sistematik derleme protokolu ve yontem denetim kurallari referanslari eklendi"
```

---

## Task 10: Bütünleşik Doğrulama ve Senkronizasyon

**Files:**
- Create: `tests/integration_tests/test_plan1_integrity.py`
- Modify: `.opencode/skill/academic-thesis-writer/SKILL.md` (kök `SKILL.md` ile aynı)
- Modify: `.opencode/skill/academic-thesis-writer/agents/` (kök `agents/` ile aynı)
- Modify: `README.md`

**Interfaces:**
- Consumes: tüm önceki görevlerin çıktıları
- Produces: uçtan uca doğrulama testi + senkron kopyalar

- [ ] **Step 1: Bütünleşik testi yaz**

`tests/integration_tests/test_plan1_integrity.py`:
```python
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
SKILL_COPY = REPO_ROOT / ".opencode" / "skill" / "academic-thesis-writer"


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
    """
    sonuc = subprocess.run(
        [
            sys.executable, "-m", "pytest", "-q", "--collect-only",
            "-p", "no:cacheprovider",
            "--ignore", str(REPO_ROOT / "tests" / "integration_tests"),
        ],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    sayi = 0
    for satir in sonuc.stdout.splitlines():
        if "test collected" in satir or "tests collected" in satir:
            sayi = int(satir.split()[0])
    assert sayi > 100, f"Alt kumede yalnizca {sayi} test toplandi, beklenen >100"


def test_gercek_ag_cagrisi_yapilmiyor():
    """P0-1 testleri ag bagimliliği olmadan calismalidir."""
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


def _kaynaktan_oku(alt_dizin: str) -> str:
    parcalar = []
    for yol in sorted((REPO_ROOT / alt_dizin).rglob("*.py")):
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


def test_readme_p0_1_mimarisini_anlatiyor():
    metin = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "jsonschema" in metin
    assert "pytest" in metin
    for ajan in ["contradiction-analyzer", "integrity-auditor"]:
        assert ajan in metin, ajan


def test_planda_surum_ibaresi_yok():
    """Planin kendisi de surum soyutlamasi yasagina tabidir."""
    plan = REPO_ROOT / "docs" / "superpowers" / "plans" / "2026-09-26-p0-1-core-data-model.md"
    assert plan.is_file()
    metin = plan.read_text(encoding="utf-8")
    desen = re.compile(r"(?<![\w/.])v(?:ersion)?\s*[0-9]+(?!\w)", re.IGNORECASE)
    eslesme = desen.search(metin)
    assert eslesme is None, f"Planda surum ibaresi: {eslesme.group(0)!r}"
```

- [ ] **Step 2: Testleri çalıştır, başarısız olduğunu doğrula**

Run: `python -m pytest tests/integration_tests/test_plan1_integrity.py -v`
Expected: FAIL — kopya ajan dosyaları eksik

- [ ] **Step 3: `.opencode` kopyasını senkronize et**

```bash
New-Item -ItemType Directory -Force -Path ".opencode/skill/academic-thesis-writer/agents" | Out-Null
Copy-Item "SKILL.md" ".opencode/skill/academic-thesis-writer/SKILL.md" -Force
Copy-Item "agents/*.md" ".opencode/skill/academic-thesis-writer/agents/" -Force
```

- [ ] **Step 4: `README.md`'yi güncelle**

`README.md` dosyasına yeni bir bölüm ekle:

```markdown
## P0-1: Çekirdek ve Veri Modeli

Bu katman, tezin tüm varlıklarını tanımlayan veri modelini ve bunu
doğrulayan çalıştırılabilir test altyapısını kurar.

### Doğruluk Kaynağı

Kalıcı varlıkların tek doğruluk kaynağı `schemas/*.json` dosyalarıdır
(JSON Schema draft 2020-12). Python tarafında şemaların kopyası
tutulmaz; `tools/atw/` yalnızca şemaları okur.

### Çalıştırma

```bash
pip install -r requirements.txt
python -m pytest -q
```

### Kimlik Standardı

`<PREFIX>-<NNN>` — üç haneli sıfır dolgulu. Prefiksler: `SRC`, `EVD`,
`CLM`, `CIT`, `P`, `RQ`, `HYP`, `FND`, `DSC`, `CON`, `GAP`, `AUD`,
`SEARCH`, `DS`, `ANL`, `STAT`, `TBL`, `FIG`.

### Ajanlar

| Ajan | Görev |
|------|-------|
| `researcher` | Kaynak keşfi ve arama stratejisi |
| `source-verifier` | Crossref + OpenAlex ile kaynak doğrulama |
| `evidence-extractor` | PDF'ten sayfa düzeyinde kanıt çıkarma |
| `gap-analyzer` | Araştırma boşluğu sınıflandırması |
| `contradiction-analyzer` | Çelişki tespiti ve boyut karşılaştırması |
| `writer` | Kanıt ve onay kapılarına bağlı yazım |
| `citation-auditor` | Atıf biçim ve tutarlılık denetimi |
| `methodology-auditor` | Yöntem–bulgu uyumu denetimi |
| `consistency-auditor` | Terminoloji, sayı, tarih tutarlılığı |
| `integrity-auditor` | Uydurma kaynak, kanıtsız iddia, retraksiyon denetimi |
```

- [ ] **Step 5: Bütünleşik testleri çalıştır, geçtiğini doğrula**

Run: `python -m pytest tests/integration_tests/test_plan1_integrity.py -v`
Expected: PASS — 11 test

- [ ] **Step 6: Tüm test paketini çalıştır**

Run: `python -m pytest -q`
Expected: PASS — tüm testler yeşil

Doğrulama:
```bash
python -m pytest -q -m xfaz
```
Expected: `no tests ran` (artık hiçbir test `xfaz` işaretli değil; bu komut
`xfaz` tanımı da silindiği için uyarı vermelidir — uyarı verirse
`pytest.ini`'deki `markers` bloğundan `xfaz` satırının kaldırıldığını doğrula)

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: P0-1 butunlugu - opencode kopyasi senkron, README guncel, butunlesik dogrulama testleri"
git push origin main
```

---

## Plan 1 Tamamlandıktan Sonra

Bu plan tamamlandığında:

- 18 şema `jsonschema` ile doğrulanır
- `python -m pytest -q` tamamen yeşildir
- 10 ajan ve 7 referans dosyası yerindedir
- `tools/atw/` çekirdeği sonraki planların beklediği arayüzü sunar

**Sonraki planlar (bu planda kapsam dışı):**

| Plan | Kapsam |
|------|--------|
| P0-2 | Kaynak Doğrulama Motoru — `source_search` (Crossref + OpenAlex + cache + rate limit + retry) ve `source_verify` (metadata eşleştirme + retraksiyon) |
| P0-3 | Kanıt Motoru — `pdf_extract` (extractor + ocr + passage localizer + evidence builder) |
| P0-4 | Atıf ve Onay Motoru — `citation_check` (5 stil + üniversite override) ve `tools/atw/approval.py` |
| P0-5 | Bütünleşik Test ve Dokümantasyon — uçtan uca akış, `README.md`, `.opencode` senkronizasyonu |
