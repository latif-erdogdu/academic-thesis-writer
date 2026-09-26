# P0-1.5 Sertleştirme ve Bütünlük Onarımı Implementation Plan

> **Ajanik çalışanlar için:** ZORUNLU ALT-SKILL: Bu planı görev görev uygulamak için `superpowers:subagent-driven-development` (önerilir) veya `superpowers:executing-plans` kullanılmalıdır. Adımlar `- [x]` onay kutusu sözdizimiyle izlenir.

**Goal:** P0-2'ye geçmeden önce P0-1'in bıraktığı katmanı sertleştirmek: (a) belgeler şemaya karşı mekanik olarak bağlanmak, (b) iki doğrulama deliğini kapatmak, (c) çalışma zamanı dayanıklılığını sağlamak, (d) çalışan bir bütünlük denetimi ve kanıt grafiği sorgu katmanı kurmak, (e) dokümanın gerçeği yansıtmasını sağlamak.

**Architecture:** JSON Schema tek doğruluk kaynağı olarak kalır; hiçbir şema alanı Python'a kopyalanmaz. Yeni katman **saf-okunur sorgu**: `tools/atw/graph.py` kenar tablosunu şemalardan *türetir* (elle yazılmaz), `thesis_state.json` üzerinde gezinir ve hiçbir şeyi diske yazmaz. Sözleşme testi `tests/contract_tests/` altında belge–şema sapmasını mekanikleştirir; `find_dangling_references()` geriye uyumlu bir sarmalayıcı olarak kalır.

**Tech Stack:** Python 3.9+ (3.12'de geliştirilir, 3.9 hedeflenir), `jsonschema>=4.22` (`referencing` + `FormatChecker` dahil), `pytest>=8.0`, `pytest-cov>=5.0`. **Yeni bağımlılık yok.**

**Spec:** `docs/superpowers/specs/2026-09-26-sertlestirme-ve-butunluk-design.md` (590 satır, 24 bulgu F1–F22, 18 kabul kriteri)

---

## Global Constraints

- **Dil:** Tüm `.md` dosyaları, docstring'ler, commit mesajları ve CLI çıktıları Türkçe. Kod tanımlayıcıları (değişken, fonksiyon, sınıs adları) İngilizce kalır.
- **Sürüm ibaresi yasağı:** Hiçbir dosyada veya commit mesajında sürüm numarası soyutlaması yazılmayacak. `schema_version` değeri `"1.0"` olarak kalır. Yasağın tek kaynağı `tests/schema_tests/test_agent_files.py` içindeki desendir.
- **Şema kazanır kuralı (D2):** Belge ile şema çeliştiğinde **şema doğrudur**, belge düzeltilir. Tek istisna: şemada gerçekten eksik bir kavram varsa şema genişler — ve bu genişleme gerekçesiyle birlikte commit mesajına yazılır.
- **Şema standardı:** Tüm şemalar draft 2020-12, `$id` = `https://github.com/latif-erdogdu/academic-thesis-writer/schemas/<dosya>.json`, `additionalProperties: false` (kayıt şemalarında).
- **Kimlik biçimi:** `<PREFIX>-<NNN>`, üç haneli sıfır dolgulu. 18 önekten **20**'ye çıkılır: `CH: "chapter"`, `VAR: "variable"` eklenir. `HYP` zaten var.
- **Sayı sabitlenmez:** Hiçbir test "69 alan" gibi sabit bir sayıyla karşılaştırmaz. Kapsam ölçümü **şemadan türetilir**; yeni şema eklendiğinde kabul kriteri kendiliğinden geçerli kalır.
- **Sürüklenme kaydı:** Her sürüklenme (spec'ten sapma, ölçüm düzeltmesi, varsayım) commit mesajına yazılır. Testler sürüklemeyi **raporlar**, değiştirmez.
- **Git:** Her adım sonunda commit. `main` dalına doğrudan commit; dal açma, rebase veya squash yok. `sorun.md` commit edilmez (kullanıcının dosyası).
- **Ağ:** Bu planın hiçbir testi ağ çağrısı yapmaz.

## Review Focus

Spec'in ima ettiği ama hiçbir görevin testlerinin doğrudan hedeflemediği, bir insanın bu yazılımı kullanırken en çok sıkıntı çekeceği beş girdi sınıfı:

1. **`fulltext_available: null` geçerli olmalı** — P0-3 bu alanı doldurur, P0-2 `null` bırakır. Alan required veya yanlış tipteyse P0-2'nin ilk günü kırılır ve hata "P0-3'te çözsene" denerek ertelenir. → Sahibi: Görev 2
2. **S1'in yeşil durumu S2'den sonra da yeşil kalmalı** — S2 `paragraph.chapter`'a `^CH-\d{3,}$` deseni koyar. `writer.md:36` bugün `"chapter": "2"` yazıyor; S2 bu bloğu sessizce kırar ve kırılma "S2'nin hatası" sanılır. Aynı şekilde `SKILL.md`'ye yazılan `empty_state()` çıktısı S2'nin `date-time` kısıtına dayanmalı. → Sahibi: Görev 1 (regresyon testi)
3. **3.9/3.10/3.11'de paket hâlâ `SyntaxError`** — Bugün 10 f-string yüzünden 3.11'de paketin *tamamı* çözmüyor. Hiçbir test bunu kanıtlamaz çünkü geliştirme 3.12'de yapılır; sürüm tabanı `requirements.txt`'te de tanımlı değil. → Sahibi: Görev 3 (`ast.parse(feature_version=(3,9))`)
4. **Eksik/boş bir state `graph`'a verildiğinde** — Bugün `find_dangling_references` `.get(alan, [])` kullanıyor; alan `null` ise `TypeError`. Yeni `graph.py` registry alanlarını gezdiği için aynı tuzak genişler. Kullanıcının yeni açtığı tezde `audit_registry` boş olabilir. → Sahibi: Görev 4
5. **Retraksiyona uğramış kaynağı hâlâ kullanan iddia** — Akademik dürüstlüğün en ciddi riski. `retraksiyona_ugrayan_iddialar` bunu yakalıyor ama testi yok; `source.json`'ın kök düzeyindeki `retraction_status` alanı hiçbir yerde okunmuyor. → Sahibi: Görev 4

Bu beş satırın her biri için sahibi olan göreve, o görevin kendi adım diliminde bir test eklendi.

## Spec'ten Sapmalar (gerekçeli)

| Spec | Bu plan | Gerekçe |
|------|----------|---------|
| `fulltext_available` eklenmesi **S2**'de (spec §5, S2) | **S1**'de eklenir | Ölçüldü: `source-verifier.md:38`'deki blok kök düzeyde `fulltext_available` içeriyor. Bu alan şemada yoksa S1'in yeşile dönmesi **imkânsız** — o hâlde S1 ya eksik belgeyi bırakır ya da D3 kararını tersine çevirir. D3 kararı doğru; sadece S2'ye aitmiş gibi yazılmış. |
| `writer.md:36` `"chapter": "2"` | S1'de `"CH-002"` yapılır | Ölçüldü: bu, 10 ajan belgesi + `SKILL.md` içinde `"chapter"` **değeri** taşıyan tek yerdir. S2 `^CH-\d{3,}$` deseni eklediğinde blok kırılır. Değeri S1'de düzeltmek, sürüklemeyi iki dilim arasına yaymak yerine kaynağında keser. Spec bunu söylemiyordu; ölçümle bulundu. |

### Planın kendi kodunu ölçerek bulunan iki tasarım hatası

Bu planın `graph.py` tasarımı yazıldıktan sonra **çalıştırılarak** sınandı ve
iki gerçek hata bulundu. İkisi de sessiz yanlış davranış üretiyordu; ikisi de
koda yazılmadan görünmezdi.

**Hata 1 — `kimlik_alani()` F18'i yeniden üretiyordu.** Fonksiyon, `id` yoksa
`<alan adı>_<önek>` desenini arıyordu. `audit.json` için desen `^AUD-` verir,
alan adı `audit_id` verir, karşılaştırma `"AUD" == "audit"` olur ve **eşleşmez**.
Sonuç: `audit.audit_id` bir referans sanılır ve audit kayıtları yine hiç
dolaşılmaz — düzeltmek için yazıldığı hatanın kendisi. Ölçüldü: bu hata
gerçekte 1 kenarlık (54 yerine 53) fark yaratıyordu, ama `audit`'in
denetlenip denetlenmediğini tamamen yanlış gösteriyordu.
Düzeltme: önek tahmini yerine **dosya gövdesi** kullanılır
(`sema_adi` → `f"{sema_adi}_id"`). `audit.json` → `audit_id`, `id` yoksa `None`.

**Hata 2 — `_REGISTRY_FIELDS` eksik, "her bulgu kopuk" patlaması üretirdi.**
`state.py:33`'teki `_REGISTRY_FIELDS` 15 alan içeriyor. Ama `thesis_state.json`
**19** `$ref` dizisi taşıyor: `research_questions`, `hypotheses`, `chapters` ve
`variables` elle yazılmış listede **yok**. Sonuç: `research_question` ve
`hypothesis` hedeflerinin kimlik kümesi **her zaman boş** kalır ve
`finding.rq_id`, `discussion.rq_id`, `conclusion.rq_ids`,
`research_gap.related_research_questions`, `paragraph.research_questions`,
`research_question.hypothesis_ids`, `conclusion.hypothesis_outcomes.hypothesis_id`
alanlarındaki **her geçerli referans** kopuk bildirilir. Yani `graph.py`
kullanıcıya sürekli yanlış alarm verir.
Düzeltme: harita **elle yazılmaz**, `thesis_state.json`'un `$ref`'lerinden
türetilir (ölçüldü: 19 alan). Böylece S2'nin üç yeni `$ref`'i kendiliğinden
kapsanır.

**Ek ölçüm — iç içe koleksiyonlar.** `paragraph` kayıtları üst düzey registry
değil, `chapter.paragraphs[]` içinde yaşar. `citation.paragraph_id` bu yüzden
hedef kümesi boş kalır. Kimlik indeksi iç içe `$ref` dizilerine de inmeli
(ölçüldü: bu tek kenar `citation.paragraph_id`; onsuz P0-4'ün atıf denetimi
çalışmaz).

**Ölçülen kenar sayısı: 59** (38 yapısal, 21 anlamsal). Spec 61 demişti; iki
fark önceki sayım yönteminden. Test yine de sabit sayıyla karşılaştırmaz —
aşağıdaki iki yönlü test kapsamı güvenceye alır.

### Ölçümle bulunan ve spec'e işlenen düzeltmeler (uygulama sırasında)

Bunlar plan yazımı sırasında ölçüldü ve spec'e **commit edilerek** işlendi; burada tekrar listelenmiyor. Kayıt: `7b39339` (F18–F20) ve `62744ec` (F21–F22).

---

## File Structure

**Oluşturulan:**

| Dosya | Sorumluluk |
|---|---|
| `tests/contract_tests/test_agent_schema_agreement.py` | Belge–şema sözleşmesi: 3 denetim sınıfı (JSON blokları, alan referansları, kimlik önekleri) |
| `tests/unit_tests/test_graph.py` | `graph.py` kenar tablosu türetimi + 8 sorgu + boş-durum dayanıklılığı |
| `schemas/chapter.json` | Bölüm kaydı: `id`, `number`, `title`, `goal`, `paragraphs` |
| `schemas/variable.json` | Değişken kaydı: `id`, `name`, `definition`, `operationalization`, ölçek/tip, `dataset_ids`, `claim_ids` |
| `schemas/hypothesis.json` | Hipotez kaydı: mevcut inline tanımın birebir kopyası + `additionalProperties: false` |
| `tools/atw/graph.py` | Kenar tablosu + 8 sorgu fonksiyonu. Salt-okunur, `lru_cache`'li tablo |
| `requirements.txt` (düzenleme) | `python_requires` yorumu ile dil tabanı belgelenir |

**Değiştirilen:**

| Dosya | Değişiklik |
|---|---|
| `tools/atw/ids.py` | `ID_PREFIXES` + `CH`, `VAR` (18 → 20) |
| `tools/atw/state.py` | `FormatChecker` bağlanır; `find_dangling_references()` `graph`'a yönlenir; 10 f-string düzeltilir |
| `schemas/thesis_state.json` | `chapters`/`variables`/`hypotheses` → `$ref`; `created_at`/`updated_at` → `format: date-time` |
| `schemas/source.json` | `fulltext_available` (nullable), `access_date` → `format: date`, `verification.verified_at` → `format: date-time` |
| `schemas/paragraph.json` | `chapter` → `^CH-\d{3,}$` (nullable) |
| `schemas/research_question.json` | `chapter` → `^CH-\d{3,}$` (nullable) |
| `agents/source-verifier.md` | Fence, `verification` iç içe, 5 enum, `date-time`, 4 alan düzeltme |
| `agents/gap-analyzer.md` | Fence, 3 alan adı, `gap_type` 12 değer, `confidence` |
| `agents/contradiction-analyzer.md` | `statistic.json → power` → gerçek alanlar |
| `agents/writer.md` | Fence, `RQ2` → `RQ-002`, `chapter` → `CH-002` |
| `SKILL.md` | `empty_state()` çıktısıyla değiştirilir |
| `references/citation_rules.md` | APA 7 "3+ yazar" kuralı; "yalnız APA uygulanıyor" açıklaması |
| `README.md` | 8→10 ajan, 7→21 şema, 5→7 referans, 19→18 sütun, `:268` komutu, 12 özellik ✅/🚧 |
| `pytest.ini` | `fail_under` (ölçüm sonrası) |

---

## Görev 1 — S1: Sözleşme testi ve belge onarımı

**Amaç:** Belge–şema sapmalarını mekanikleştirmek. Belge ile şema çelişince şema kazanır.

**Oluşturulan:** `tests/contract_tests/test_agent_schema_agreement.py`
**Değiştirilen:** `agents/{source-verifier,gap-analyzer,contradiction-analyzer,writer}.md`, `SKILL.md`, `schemas/source.json` (yalnız `fulltext_available`)

**Sözleşme testinin kurgusu (spec §5, S1'den):**

- **3 denetim sınıfı.** Sınıf 1 gömülü JSON blokları (fence'li **ve** fence'siz), sınıf 2 `şema.json → alan` atıfları, sınıf 3 kimlik önekleri.
- **`required` ajan belgelerinde yok sayılır.** Ajanlar bilerek *kırpı* parça gösterir. `additionalProperties` / `enum` / `pattern` / `type` hataları **geçerlidir** — bunlar tam olarak "yanlış alan adı", "yanlış değer", "geçersiz kimlik" sapmalarıdır. İstisna: `TAM_KAYIT_DOSYALARI = {"SKILL.md"}`.
- **Sınıf 2 yalnız okunun *başındaki ardaşık* backtick'li diziyi alır.** Cümle ortasındaki alan adları kapsam dışıdır (ölçüldü: bu kural olmadan 27 atıftan 3'ü yanlış pozitif üretiyordu).
- **Sınıf 3 `THESIS`'i hariç tutar** — `thesis_id` ayrı bir kimlik uzayıdır, şemada deseni yoktur.

### Adımlar

- [ ] **1.1** `tests/contract_tests/` dizinini oluştur (`__init__.py` **olmadan** — P0-1'deki diğer dizinler de böyle, `pytest` rootdir keşfi için yeterli).

- [ ] **1.2** Sözleşme testini yaz. Tam içerik:

```python
"""Belge–şema sözleşmesi: ajan belgeleri ve SKILL.md semaya uyar mi?

Uc denetim sinifi:
  1. Gomulu JSON ornekleri (fence'li VE fencesiz)
  2. Alan referanslari (``sema.json`` -> ``alan``)
  3. Kimlik onekleri (``XX-NNN``)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from tools.atw.ids import ID_PREFIXES
from tools.atw.state import SCHEMA_DIR, schema_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
BELGELER = sorted((REPO_ROOT / "agents").glob("*.md"))
BELGELER += [REPO_ROOT / "SKILL.md"]

# `required` hatasi yalnizca tam kayit beklenen dosyalarda denetlenir.
# Ajan belgeleri kirpi JSON parcalari gosterir; parcanin zorunlu
# alanlari tasimamasi bir saptirma degildir.
TAM_KAYIT_DOSYALARI = {"SKILL.md"}

# Blok, kendinden onceki 400 karakterde sema adi gormezse belgenin
# varsayilani kullanilir. Dort blokta ipucu yoktur.
VARSAYILAN_SEMA = {
    "evidence-extractor.md": "evidence",
    "gap-analyzer.md": "research_gap",
    "source-verifier.md": "source",
    "writer.md": "paragraph",
    "SKILL.md": "thesis_state",
}

# `thesis_id` ayri bir kimlik uzayidir ve semada deseni yoktur.
# Diger tum onekler ID_PREFIXES'te olmak ZORUNDADIR.
ONEK_DISARI = {"THESIS"}

# Yoksayilan dogrulayicilar: parca zorunlu alan tasimaz.
YOK_SAYILAN = {"required"}

_ONIZLEME_PENCERESI = 400

FENCE = re.compile(r"```json[ \t]*\r?\n(.*?)```", re.DOTALL)
SEMA_ATIF = re.compile(r"`(\w+)\.json`[ \t]*(?:→|->)[ \t]*")
ARDISIK_DIZI = re.compile(r"(?:`([a-z_][a-z_0-9]*)`[ \t]*(?:,|/|ve\b)?[ \t]*)+")
KIMLIK_ONEK = re.compile(r"\b([A-Z]{1,8})-(?:\d{3,}[a-z]?|XXX)\b")


def _semalari() -> dict[str, dict]:
    return {p.stem: json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(SCHEMA_DIR.glob("*.json"))}


def _fencesiz_bloklar(metin: str):
    """Sutun 0'da '{' ile baslayip sutun 0'da '}' ile biten bloklar.

    Fence'siz yazilmis JSON orneklerini yakalar. Kaynak dogrulama icin
    kritik: en bozuk iki blok (source-verifier, gap-analyzer) fence'siz.
    """
    satirlar = metin.splitlines(keepends=True)
    konum, i = 0, 0
    while i < len(satirlar):
        if satirlar[i].rstrip("\r\n") == "{":
            parcalar, j = [], i
            while j < len(satirlar):
                parcalar.append(satirlar[j])
                if satirlar[j].rstrip("\r\n") == "}":
                    break
                j += 1
            if j < len(satirlar):
                yield konum, "".join(parcalar)
                konum += sum(len(s) for s in parcalar)
                i = j + 1
                continue
        konum += len(satirlar[i])
        i += 1


def _bloklar(metin: str):
    """(baslangic, metin) uclusu verir. Fence'li once, sonra fence'siz."""
    fence_araliklar = [(m.start(), m.end()) for m in FENCE.finditer(metin)]
    for eslesme in FENCE.finditer(metin):
        yield eslesme.start(), eslesme.group(1)
    for bas, blok in _fencesiz_bloklar(metin):
        if not any(a <= bas < b for a, b in fence_araliklar):
            yield bas, blok


def _sema_adini_bul(metin: str, bas: int, belge_adi: str) -> str | None:
    """Bloktan onceki pencerede gecen son sema adi, yoksa varsayilan."""
    onizleme = metin[max(0, bas - _ONIZLEME_PENCERESI):bas]
    adaylar = re.findall(r"(\w+)\.json", onizleme)
    semalar = _semalari()
    if adaylar and adaylar[-1] in semalar:
        return adaylar[-1]
    return VARSAYILAN_SEMA.get(belge_adi)


def _tum_alanlar(sema: dict) -> set[str]:
    """Sema icindeki tum alan adlari (ic ice)."""
    out: set[str] = set()
    for ad, tanim in (sema.get("properties") or {}).items():
        if ad == "$comment":
            continue
        out.add(ad)
        if isinstance(tanim, dict):
            out |= _tum_alanlar(tanim)
    return out


def _blok_id(belge_adi: str, satir: int) -> str:
    return f"{belge_adi}:{satir}"


def _json_bloklari():
    """(belge_adi, satir, sema_adi, veri) uclusu verir."""
    for belge in BELGELER:
        metin = belge.read_text(encoding="utf-8")
        for bas, blok in sorted(_bloklar(metin)):
            satir = metin[:bas].count("\n") + 1
            try:
                veri = json.loads(blok)
            except json.JSONDecodeError:
                continue
            if not isinstance(veri, dict):
                continue
            sema_adi = _sema_adini_bul(metin, bas, belge.name)
            if sema_adi is not None:
                yield belge.name, satir, sema_adi, veri


def _saptirmalar(belge_adi: str, sema_adi: str, veri: dict) -> list[str]:
    """Bloktaki gercek saptirmalari dondurur (bos liste = temiz)."""
    semalar, registry = _semalari(), schema_registry()
    dogrulayici = Draft202012Validator(semalar[sema_adi], registry=registry)
    hatalar = [e for e in dogrulayici.iter_errors(veri)
               if e.validator not in YOK_SAYILAN]
    if belge_adi in TAM_KAYIT_DOSYALARI:
        hatalar = list(dogrulayici.iter_errors(veri))
    mesajlar = []
    for e in hatalar:
        yol = "/".join(str(p) for p in e.absolute_path) or "(kok)"
        mesajlar.append(f"[{e.validator}] {yol}: {e.message}")
    return mesajlar


# --- Sinif 1: gomulu JSON ornekleri ------------------------------------

@pytest.mark.parametrize("belge,satir,sema_adi,veri",
                         list(_json_bloklari()),
                         ids=lambda v: str(v)[:40])
def test_json_blogu_semaya_uyar(belge, satir, sema_adi, veri):
    saptirmalar = _saptirmalar(belge, sema_adi, veri)
    assert not saptirmalar, (
        f"{_blok_id(belge, satir)} -> {sema_adi}.json uymuyor:\n  "
        + "\n  ".join(saptirmalar))


# --- Sinif 2: alan referanslari ----------------------------------------

def _alan_atiflari():
    for belge in BELGELER:
        metin = belge.read_text(encoding="utf-8")
        for eslesme in SEMA_ATIF.finditer(metin):
            sema_adi = eslesme.group(1)
            satir = metin[:eslesme.start()].count("\n") + 1
            satir_sonu = metin.find("\n", eslesme.end())
            kalan = metin[eslesme.end():satir_sonu if satir_sonu > 0 else len(metin)]
            dizi = ARDISIK_DIZI.match(kalan)
            if not dizi:
                continue
            for alan in re.findall(r"`([a-z_][a-z_0-9]*)`", dizi.group(0)):
                yield belge.name, satir, sema_adi, alan


def test_alan_atifi_sayisi_sifirdan_fazla():
    """Atif tarayicisi hicbir sey bulmuyorsa test sessizce yesil olur."""
    assert len(list(_alan_atiflari())) > 0


@pytest.mark.parametrize("belge,satir,sema_adi,alan",
                         list(_alan_atiflari()),
                         ids=lambda v: str(v)[:40])
def test_alan_referansi_semada_var(belge, satir, sema_adi, alan):
    semalar = _semalari()
    assert sema_adi in semalar, (
        f"{_blok_id(belge, satir)}: bilinmeyen sema {sema_adi}.json")
    assert alan in _tum_alanlar(semalar[sema_adi]), (
        f"{_blok_id(belge, satir)}: {sema_adi}.json icinde "
        f"'{alan}' alani yok")


# --- Sinif 3: kimlik onekleri ------------------------------------------

def test_belgelerdeki_kimlik_onekleri_tanimli():
    bilinmeyen = {}
    for belge in BELGELER + [REPO_ROOT / "README.md"]:
        metin = belge.read_text(encoding="utf-8")
        for eslesme in KIMLIK_ONEK.finditer(metin):
            onek = eslesme.group(1)
            if onek in ID_PREFIXES or onek in ONEK_DISARI:
                continue
            bilinmeyen.setdefault(belge.name, []).append(
                f"{eslesme.group(0)} ({metin[:eslesme.start()].count(chr(10)) + 1})")
    assert not bilinmeyen, "Tanimli olmayan kimlik oneki:\n" + json.dumps(
        bilinmeyen, ensure_ascii=False, indent=2)
```

- [ ] **1.3** Testi çalıştır ve **KIRMIZI** olduğunu doğrula. Beklenen çıktı (spec §5, S1'deki ölçülmüş tabloyla karşılaştır):

```bash
python -m pytest tests/contract_tests/ -q -p no:cacheprovider
```

Beklenen: **5 test grubu kırmızı.**

| Blok / atıf | Beklenen kırmızı |
|---|---|
| `source-verifier.md:38` | `additionalProperties`: `fulltext_available`, `metadata_match`, `status`, `verification_sources`, `verified_at` |
| `gap-analyzer.md:38` | `additionalProperties`: `description`, `evidence`, `gap_id` + `enum` × 2 (`gap_type`, `confidence`) |
| `SKILL.md:242` | `additionalProperties`: `claims` + `required` × 11 |
| `writer.md:34` | `pattern`: `'RQ2' does not match '^RQ-\d{3,}$'` |
| `contradiction-analyzer.md:36` | `statistic.json` içinde `'power'` alanı yok |
| **Sınıf 3 (kimlik önekleri)** | **yeşil** — ileriye dönük nöbetçi |

**Bu kırmızı çıktıyı bir dosyaya yaz ve commit mesajına kopyala:**

```bash
python -m pytest tests/contract_tests/ -q -p no:cacheprovider > _kirmizi.txt 2>&1
Get-Content _kirmizi.txt -Encoding UTF8
```

- [ ] **1.4** `schemas/source.json`'a `fulltext_available` alanını ekle (D3). `properties` içine, `verification` **yanına** — kök düzeyde:

```json
"fulltext_available": { "type": ["boolean", "null"], "default": null }
```

`required` listesine **ekleme** (P0-2 `null` bırakır; zorunlu olsaydı P0-2 kırılırdı — Review Focus 1).

- [ ] **1.5** `agents/source-verifier.md` §`## Çıktı`'sını düzelt. Satır 36–44 bloğunu **fence'li** olarak şu hâle getir:

````markdown
## Çıktı

`source.json` kaydının `verification` ve `fulltext_available` alanları güncellenir:

```json
{
  "verification": {
    "status": "verified",
    "verified_at": "2026-09-26T10:12:00+00:00",
    "verification_sources": ["crossref", "openalex"],
    "bibliographic_match": 0.95
  },
  "fulltext_available": true
}
```

`status` beş değer alır: `verified`, `unverified`, `pending`, `retracted`,
`corrected`. `metadata_match` **diye bir alan yoktur**; eşleşme ölçümü
`bibliographic_match` içinde 0–1 arasında bir oran olarak tutulur.
`verified_at` tam tarih-saat içerir (`date-time`), gün değil.
````

- [ ] **1.6** `agents/gap-analyzer.md` §`## Çıktı`'sını düzelt. Satır 37–44'ü fence'li olarak yaz:

````markdown
## Çıktı

```json
{
  "id": "GAP-001",
  "statement": "Kurgusal örnek: mevcut çalışmalar belirli bir parçayı birlikte incelememiştir.",
  "gap_type": "unanswered_question",
  "dimension": "population",
  "evidence_ids": ["EVD-001"],
  "supporting_source_ids": ["SRC-001"],
  "confidence": "moderate"
}
```

`gap_type` 12 değer alır: `unanswered_question`, `methodological`,
`population`, `geographical`, `temporal`, `theoretical`, `measurement`,
`measurement_instrument`, `sample`, `contradictory_findings`,
`unjustified_assumption`, `unexamined_implication`.

`confidence` üç değer alır: `low`, `moderate`, `high`. **`medium` diye bir
değer yoktur.**
````

- [ ] **1.7** `agents/contradiction-analyzer.md:36`'daki satırı düzelt. `| İstatistiksel güç | \`statistic.json\` → \`n\`, \`power\` alanları |` satırı şu hâle gelir:

```markdown
| İstatistiksel güç | `statistic.json` → `n`, `effect_size`, `p_value` alanları |
```

- [ ] **1.8** `agents/writer.md` §`## Paragraf Metadata` bloğunu fence'li olarak düzelt ve iki değeri onar:

````markdown
## Paragraf Metadata

```json
{
  "id": "P-014",
  "chapter": "CH-002",
  "section": "2.3",
  "type": "literature_synthesis",
  "claims": ["CLM-001", "CLM-004"],
  "evidence": ["EVD-001", "EVD-004"],
  "sources": ["SRC-001", "SRC-007"],
  "research_questions": ["RQ-002"]
}
```

`chapter` bir bölüm **kimliğidir** (`CH-NNN`), numarası değil. Bir
`research_question` bu bölümde ele alınıyorsa `RQ-NNN` biçiminde yazılır.
````

> `chapter` değerinin `CH-002` yapılması **Review Focus 2**: Görev 2 bu alana
> `^CH-\d{3,}$` deseni ekleyecek. Bugünkü `"2"` değeri o aşamada kırılırdı.

- [ ] **1.9** `SKILL.md:242-270`'deki "Minimum veri" örneğini `empty_state()` çıktısıyla değiştir. Önce gerçek çıktıyı üret:

```bash
python -c "import json,sys; sys.path.insert(0,'.'); from tools.atw.state import empty_state; print(json.dumps(empty_state('THESIS-2026-001','Ornek Tez Adı'), ensure_ascii=False, indent=2))"
```

Sonra `SKILL.md`'deki bloğu **birebir** bu çıktıyla değiştir ve başlığı
`Minimum veri:` yerine şu iki satıra çevir:

```markdown
Aşağıdaki blok `tools/atw/state.py` içindeki `empty_state()` fonksiyonunun
**gerçek çıktısıdır**. Elle yazılmamıştır: şema değişirse bu örnek de
değişir, böylece belge ile şema arasında sürüklenme oluşamaz.
```

> Blok 33 üst düzey alan içerir. `SKILL.md` `TAM_KAYIT_DOSYALARI`'nda
> olduğu için `required` hataları da denetlenir — eksik alan kalmaz.

- [ ] **1.10** **Regresyon testi** (Review Focus 2). S1'in yeşil durumu
Görev 2'nin şema kısıtlarına dayanmalı. Aynı test dosyasına ekle:

```python
# --- S1/S2 siralamasi regresyonu (Review Focus 2) ----------------------

@pytest.mark.parametrize("belge,satir,sema_adi,veri",
                         list(_json_bloklari()),
                         ids=lambda v: str(v)[:40])
def test_onnarimli_bloklar_sonraki_kisitlara_dayanir(belge, satir, sema_adi, veri):
    """Onarilan blogun degeri, sonraki dilimde eklenecek deseni
    saglamalidir. Bugun '2' yazan bir deger, Görev 2'de kirilir.
    """
    if "chapter" in veri and isinstance(veri["chapter"], str) and veri["chapter"]:
        assert re.fullmatch(r"CH-\d{3,}", veri["chapter"]), (
            f"{_blok_id(belge, satir)}: chapter alani kimlik biciminde "
            f"olmali (CH-NNN), '{veri['chapter']}' degil")
```

- [ ] **1.11** Sözleşme testini çalıştır — **YEŞİL** olmalı:

```bash
python -m pytest tests/contract_tests/ -q -p no:cacheprovider
```

- [ ] **1.12** Tüm test paketini çalıştır — yeşil olmalı. `test_sema_sayisi_onsekiz` hâlâ 18 bekler (şema sayısı Görev 2'de değişir):

```bash
python -m pytest tests/ -q -p no:cacheprovider
```

- [ ] **1.13** Commit. Mesaj şu yapıyı taşımalı:

```
feat(contract): belge-sema sozlesme testi ve 5 belgenin onarimi

S1: 10 ajan belgesi + SKILL.md semaya karsi mekanik olarak baglandi.

Test uc sinif denetliyor:
  1. Gomulu JSON ornekleri - fence'li VE fencesiz
  2. Alan referanslari (``sema.json`` -> ``alan``)
  3. Kimlik onekleri (``XX-NNN``)

Tasarim kararlari ve gerekceleri:
  - `required` ajan belgelerinde YOK SAYILIR. Ajanlar bilerek kirpi
    JSON parcalari gosterir; parcanin zorunlu alanlari tasimamasi
    saptirma degildir. additionalProperties / enum / pattern / type
    hatalari gecerlidir - bunlar tam olarak "yanlis alan adi",
    "yanlis deger", "gecersiz kimlik" sapmalari.
    Istisna: SKILL.md tam kayit gosterdigi icin required de denetlenir.
  - Sinif 2 yalniz okunun BASINDAKI ardisik backtick'li diziyi alir.
    Tum satiri taramak 27 atiftan 3 yanlis pozitif uretiyordu
    (contradiction-analyzer.md:32 ve :38'de alan adlari yanlis
    semaya atanirdi).
  - Sinif 3 THESIS onekini haric tutar: thesis_id ayri bir kimlik
    uzayidir ve semada deseni yoktur.
  - Sinif 3 su an YESIL: kullanilan 7 onek (AUD, CIT, CLM, EVD, GAP,
    P, SRC) tanimli. Ileriye donuk nabetci, kirmizi degil.

KRIMIZI CIKTI (belgeler onarilmadan once olculdu)
-------------------------------------------------
  source-verifier.md:38   source.json       1 x additionalProperties (5 alan)
  gap-analyzer.md:38      research_gap.json 1 x additionalProperties (3) + 2 x enum
  SKILL.md:242            thesis_state.json 1 x additionalProperties + 11 x required
  writer.md:34            paragraph.json    1 x pattern (RQ2)
  contradiction-analyzer.md:36               1 alan referansi yok
  sinif 3 (kimlik onekleri)                  yesil

ONARILANLAR
-----------
  source-verifier.md   fence'e alindi; verification ic ice alindi;
                       status 5 enum degerinin tamami; verified_at
                       date-time; metadata_match kesildi
  gap-analyzer.md      fence'e alindi; gap_id->id, description->statement,
                       evidence->evidence_ids; gap_type 12 deger;
                       confidence low|moderate|high
  contradiction-analyzer.md   statistic.json -> power yerine
                       n, effect_size, p_value
  writer.md            fence'e alindi; RQ2 -> RQ-002;
                       chapter "2" -> "CH-002"
  SKILL.md             "Minimum veri" ornegi empty_state() ciktisiyla
                       degistirildi
  schemas/source.json  fulltext_available eklendi (nullable boolean)

Sapma: fulltext_available spec'te S2'ye yazilmisdi ama S1'in yesil
donmesi icin S1'de eklenmek zorundaydi - aksi halde D3 karari tersine
donusurdu. D3 karari dogru, sadece yanlis dilime yazilmis.

Sapma: writer.md "chapter": "2" degeri S1'de "CH-002" yapildi.
Gozlemle olculdu: bu, 10 ajan + SKILL.md icinde "chapter" degeri
tasan tek yer. Gozlem 2 bu alana ^CH-\d{3,}$ deseni ekleyecek; bugunku
"2" degeri o asamada kirilir ve kirilma "Gozlem 2'nin hatasi"
sanilir. Degeri kaynaginda duzeltmek suruklemeyi iki dilim
arasina yaymaz.

Fence neden opsiyonel degildi
-----------------------------
Dort blog fence'siz yazilmis. Yalniz ```json arayan bir test
source-verifier ve gap-analyzer bloklarini - yani en bozuk iki
ornegi - TAMAMEN gecirdi. Duzeltilen belge test tarafindan
bulunamaz hâle gelirdi.
```

- [ ] **1.14** `_kirmizi.txt` dosyasını sil: `Remove-Item -Force _kirmizi.txt`

---

## Görev 2 — S2: Şema delikleri

**Amaç:** Doğrulamayan iki alanı kapatmak, üç yeni kayıt şeması eklemek, tarih biçimlerini zorlamak.

**Oluşturulan:** `schemas/chapter.json`, `schemas/variable.json`, `schemas/hypothesis.json`
**Değiştirilen:** `schemas/thesis_state.json`, `schemas/source.json`, `schemas/paragraph.json`, `schemas/research_question.json`, `tools/atw/ids.py`, `tests/schema_tests/test_thesis_state_schema.py`

**Referans alanı ölçümü (ölümcül not):** Bugün 53 kenar türetiliyor. S2 üç yeni şemayla 4 kenar, `chapter` desenleriyle 2 kenar daha ekliyor → **59**. Test sabit sayıyla değil **şemadan türetilen** sayıyla karşılaştıracaktır; `59` yalnız gözlem amaçlıdır.

### Adımlar

- [ ] **2.1** `tools/atw/ids.py`'de `ID_PREFIXES`'e iki giriş ekle. `CH` `"FIG"` satırından önce, `VAR` `"FIG"` satırından sonra:

```python
    "CH": "chapter",
    "FIG": "figure",
    "VAR": "variable",
```

Gerekçe: alfabetik sıra `CH` için `CIT` ile `CLM` arası, `VAR` için en sonda.

- [ ] **2.2** `schemas/chapter.json` oluştur:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/latif-erdogdu/academic-thesis-writer/schemas/chapter.json",
  "title": "Bolum",
  "description": "Tezin tek bir bolumu. Siralamasi 'number' alani ile belirlenir.",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "number", "title"],
  "examples": [
    {
      "$comment": "KURGUSAL ORNEK. Metin uydurmadir.",
      "id": "CH-001",
      "number": 1,
      "title": "Kurusal Cerceve",
      "goal": "Kuramsal temelleri ortaya koy.",
      "paragraphs": []
    }
  ],
  "properties": {
    "$comment": { "type": "string" },
    "id": { "type": "string", "pattern": "^CH-\\d{3,}$" },
    "number": { "type": "integer", "minimum": 1 },
    "title": { "type": "string", "minLength": 1 },
    "goal": { "type": ["string", "null"] },
    "paragraphs": {
      "type": "array",
      "items": { "$ref": "paragraph.json" }
    }
  }
}
```

- [ ] **2.3** `schemas/variable.json` oluştur:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/latif-erdogdu/academic-thesis-writer/schemas/variable.json",
  "title": "Degisken",
  "description": "Arastirmada olculen ozellik. 'Nasil olculdugu' operationalization alaninda zorunludur.",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "name", "operationalization"],
  "examples": [
    {
      "$comment": "KURGUSAL ORNEK. Metin uydurmadir.",
      "id": "VAR-001",
      "name": "Ogrenci Motivasyonu",
      "definition": "Ogrencinin disaridan mudahiyet olceginde kavramanin derecesi.",
      "operationalization": "5'li Likert olcegi, 12 madde, Cronbach alfa 0.84.",
      "measurement_scale": "ordinal",
      "value_type": "numeric",
      "dataset_ids": ["DS-001"],
      "claim_ids": ["CLM-001"]
    }
  ],
  "properties": {
    "$comment": { "type": "string" },
    "id": { "type": "string", "pattern": "^VAR-\\d{3,}$" },
    "name": { "type": "string", "minLength": 1 },
    "definition": { "type": ["string", "null"] },
    "operationalization": { "type": "string", "minLength": 1 },
    "measurement_scale": {
      "type": ["string", "null"],
      "enum": ["nominal", "ordinal", "interval", "ratio", "none", null]
    },
    "value_type": {
      "type": ["string", "null"],
      "enum": ["numeric", "categorical", "temporal", "boolean", "text", null]
    },
    "dataset_ids": {
      "type": "array",
      "items": { "type": "string", "pattern": "^DS-\\d{3,}$" }
    },
    "claim_ids": {
      "type": "array",
      "items": { "type": "string", "pattern": "^CLM-\\d{3,}$" }
    }
  }
}
```

> `operationalization` **zorunlu**: bu, `references/methodology_rules.md`'in 3
> numaralı denetimini şema seviyesine indirir. "Değişken nasıl ölçüldü"
> artık ajan isteğine bırakılmaz.

- [ ] **2.4** `schemas/hypothesis.json` oluştur — `thesis_state.json`'deki inline tanımın **birebir** karşılığı, `additionalProperties: false` ile (D5):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/latif-erdogdu/academic-thesis-writer/schemas/hypothesis.json",
  "title": "Hipotez",
  "description": "Arastirma sorusuna verilen, sinanabilir deneysel bir oneri.",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "text", "status"],
  "examples": [
    {
      "$comment": "KURGUSAL ORNEK. Metin uydurmadir.",
      "id": "HYP-001",
      "text": "Kurgusal ornek: X arttikca Y artar.",
      "status": "pending",
      "related_research_questions": ["RQ-001"],
      "finding_ids": ["FND-001"]
    }
  ],
  "properties": {
    "$comment": { "type": "string" },
    "id": { "type": "string", "pattern": "^HYP-\\d{3,}$" },
    "text": { "type": "string", "minLength": 1 },
    "status": { "type": "string", "enum": ["supported", "rejected", "pending"] },
    "related_research_questions": {
      "type": "array",
      "items": { "type": "string", "pattern": "^RQ-\\d{3,}$" }
    },
    "finding_ids": {
      "type": "array",
      "items": { "type": "string", "pattern": "^FND-\\d{3,}$" }
    }
  }
}
```

- [ ] **2.5** `schemas/thesis_state.json`'da üç alanı `$ref`'le. `properties` içinde mevcut `{"type": "array", "items": {"type": "object"}}` tanımlarını şununla değiştir — `chapters`:

```json
"chapters": { "type": "array", "items": { "$ref": "chapter.json" } }
```

`variables`:

```json
"variables": { "type": "array", "items": { "$ref": "variable.json" } }
```

`hypotheses` — elle gömülü bloğun **tamamı** silinir, yerine:

```json
"hypotheses": { "type": "array", "items": { "$ref": "hypothesis.json" } }
```

> `methodology` elle gömülü kalır (6 alan, `additionalProperties: false`).
> Spec §3.2'de bilinçli olarak kapsam dışı.

- [ ] **2.6** `schemas/thesis_state.json`'da `created_at` ve `updated_at`'a `format` ekle:

```json
"created_at": { "type": "string", "format": "date-time" },
"updated_at": { "type": "string", "format": "date-time" }
```

- [ ] **2.7** `schemas/source.json`'da iki `format` ekle. `access_date` **yalnız tarih** (4 fixture'da `2026-09-26`), `verified_at` **tam tarih-saat** (4 fixture'da `2026-09-26T10:12:00+00:00`):

```json
"access_date": { "type": ["string", "null"], "format": "date" }
```

```json
"verified_at": { "type": "string", "format": "date-time" }
```

- [ ] **2.8** `schemas/paragraph.json` ve `schemas/research_question.json`'da `chapter` alanına desen ver. Her ikisi de bugün çıplak `{"type": "string"}` — önek bilgisi taşımadıkları için kenar tablosundan **türetilemiyorlar**:

```json
"chapter": { "type": ["string", "null"], "pattern": "^CH-\\d{3,}$" }
```

- [ ] **2.9** **Testleri önce yaz** (TDD). `tests/schema_tests/test_thesis_state_schema.py`'ye ekle:

```python
def test_sema_sayisi_yirmi_bir():
    from tools.atw.state import SCHEMA_DIR
    assert len(list(SCHEMA_DIR.glob("*.json"))) == 21


def test_yeni_semalar_draft_2020_12_uyumlu(schema_dir):
    for ad in ["chapter", "variable", "hypothesis"]:
        sema = json.loads((schema_dir / f"{ad}.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(sema), ad


@pytest.mark.parametrize("sema_adi", ["chapter", "variable", "hypothesis"])
def test_yeni_semada_ornek_ve_yorum_var(schema_dir, sema_adi):
    sema = json.loads((schema_dir / f"{sema_adi}.json").read_text(encoding="utf-8"))
    ornekler = sema.get("examples") or []
    assert ornekler, sema_adi
    assert "$comment" in ornekler[0], sema_adi


def test_ch_ve_var_onleri_uretilebiliyor():
    from tools.atw.ids import format_id
    assert format_id("CH", 1) == "CH-001"
    assert format_id("VAR", 1) == "VAR-001"


def test_id_prefixes_yirmi_on_tane():
    from tools.atw.ids import ID_PREFIXES
    assert len(ID_PREFIXES) == 20
    assert ID_PREFIXES["CH"] == "chapter"
    assert ID_PREFIXES["VAR"] == "variable"


def test_degisken_operationalization_zorunlu(schema_dir):
    sema = json.loads((schema_dir / "variable.json").read_text(encoding="utf-8"))
    assert "operationalization" in sema["required"]


def test_chapters_artik_delik_degil(schema_dir):
    sema = json.loads((schema_dir / "thesis_state.json").read_text(encoding="utf-8"))
    for alan in ["chapters", "variables", "hypotheses"]:
        oge = sema["properties"][alan]["items"]
        assert "$ref" in oge, f"{alan} hala ic ice tanimli: {oge}"


def test_chapter_alanlari_kimlik_biciminde(schema_dir):
    for ad in ["paragraph", "research_question"]:
        sema = json.loads((schema_dir / f"{ad}.json").read_text(encoding="utf-8"))
        assert sema["properties"]["chapter"].get("pattern") == "^CH-\\d{3,}$", ad


def test_fulltext_available_null_gecerli(schema_dir):
    from tools.atw.state import load_schema, _state_validator
    sema = load_schema("source.json")
    dogrulayici = _state_validator()
    temel = {
        "id": "SRC-001",
        "title": "Kurgusal ornek",
        "source_type": "article",
        "verification": {
            "status": "pending",
            "bibliographic_match": 0.0,
            "verified_at": "2026-09-26T10:12:00+00:00",
            "verification_sources": ["manual"],
        },
    }
    dogrulayici.evolve(schema=sema).validate(temel)
    dogrulayici.evolve(schema=sema).validate({**temel, "fulltext_available": None})
    dogrulayici.evolve(schema=sema).validate({**temel, "fulltext_available": True})
```

- [ ] **2.10** Testleri çalıştır — yeni olanlar **kırmızı**, mevcut 226 test yeşil olmalı:

```bash
python -m pytest tests/schema_tests/ -q -p no:cacheprovider
```

- [ ] **2.11** `tests/schema_tests/test_thesis_state_schema.py` içindeki eski `test_sema_sayisi_onsekiz`'i sil (2.9'da `test_sema_sayisi_yirmi_bir` ile değiştirildi).

- [ ] **2.12** Tüm testleri çalıştır:

```bash
python -m pytest tests/ -q -p no:cacheprovider
```

> `_state_validator()` bu adımda henüz `FormatChecker` bağlamıyor (Görev 3).
> Bu yüzden `test_fulltext_available_null_gecerli` biçim denetimi yapmaz —
> yalnız tip denetimi yapar. İki `format` kısıtı Görev 3'te zorlanır.

- [ ] **2.13** Commit:

```
feat(schema): chapter, variable, hypothesis semalari ve delik kapama

S2: iki dogrulama deligi kapandi, uc kayit semasi eklendi.

Kapanan delikler
----------------
chapters  {"items": {"type": "object"}}  ->  {"$ref": "chapter.json"}
variables {"items": {"type": "object"}}  ->  {"$ref": "variable.json"}
hypotheses elle gomulu (15 kardes $ref)   ->  {"$ref": "hypothesis.json"}

Bu uc alan once istendigi her seyi dogruluyordu: additionalProperties
yok, zorunlu alan yok, tur denetimi yok. Bir bolum kaydi icine
{"tamamen": "yanlis"} yazilabiliyordu.

Yeni semalar
------------
chapter.json     id(^CH-), number(int>=1), title, goal, paragraphs[$ref]
variable.json    id(^VAR-), name, operationalization(ZORUNLU),
                 measurement_scale, value_type, dataset_ids, claim_ids
hypothesis.json  inline tanimin birebir kopyasi + additionalProperties:false

variable.operationalization neden zorunlu: methodology_rules.md'nin
3 numarali denetimi ("degisken nasil olculdu") bu alanla semaya iniyor.
Zorunlu olmasaydi ayni delik "degisken adi yazildi, olcumu yazilmadi"
seklinde geri gelirdi.

Diger degisiklikler
------------------
ID_PREFIXES 18 -> 20 onek: CH:"chapter", VAR:"variable"
paragraph.chapter          -> {"type":["string","null"],"pattern":"^CH-\\d{3,}$"}
research_question.chapter  -> ayni
thesis_state.created_at    -> format: date-time
thesis_state.updated_at    -> format: date-time
source.access_date         -> format: date
source.verification.verified_at -> format: date-time

Iki tarih bicimi FARKLI ve karistirilmadi (olculdu):
  access_date  4 fixture'da "2026-09-26"           -> format: date
  verified_at  4 fixture'da "2026-09-26T10:12:00Z" -> format: date-time
access_date'a date-time eklenseydi 4 fixture kirilirdi;
verified_at'a date eklenserse 4 fixture kirilir.

chapter alanina desen neden: su an her ikisi de duz string. Onek
bilgisi tasimadiklari icin kenar tablosundan TURETILEMIYORLAR ve
"Bolum -> Paragraf" bagi denetlenemez kaliyor. Gozlem 4 bunu
duzeltiyor.

Referans alani sayisi 53 -> 59 (4 yeni sema alani + 2 chapter deseni).
Sayi sabitlenmedi: test semadan turetilen sayiyla karsilastirir.
```

---

## Görev 3 — S3: Çalışma zamanı dayanıklılığı

**Amaç:** Paketi 3.9+'a indirmek, `format` kısıtlarını gerçekten zorlamak, sürüm tabanını belgelemek.

**Değiştirilen:** `tools/atw/state.py`, `requirements.txt`
**Oluşturulan:** `tests/schema_tests/test_format_checker.py`

**Dayanak ölçüm:** 18 şemanın tamamında `format` taşıyan alan sayısı **1** (`search_run.timestamp`). 7 fixture'ın hiçbirinde o alan geçmiyor. `search_run.json` örneğinin `timestamp` değeri `2026-09-26T09:00:00+00:00` geçerli. **Bağlamak hiçbir mevcut veriyi kırmaz.**

### Adımlar

- [ ] **3.1** `tools/atw/state.py`'de `FormatChecker` bağla. `state.py:91-92` çevresindeki `_state_validator()` fonksiyonunu şu hâle getir:

```python
def _state_validator() -> Draft202012Validator:
    """Sema ve format denetleyicisiyle donatilmis bir dogrulayici dondurur."""
    sema = load_schema("thesis_state.json")
    return Draft202012Validator(
        sema, registry=schema_registry(), format_checker=_FORMAT_CHECKER
    )
```

Modül seviyesinde, `_REGISTRY_FIELDS` tanımının hemen altına:

```python
# `format` kisitlarini gercekten zorlayan denetleyici. Baglanmazsa
# jsonschema "date-time" gibi anahtarlari tanimaz ve sessizce gecer.
_FORMAT_CHECKER = FormatChecker()
```

ve içe aktarmaya `from jsonschema import Draft202012Validator, FormatChecker` ekle.

- [ ] **3.2** `state.py:249-269` içindeki 10 PEP 701 f-string'in tırnaklarını düzelt. Desen şudur: f-string içinde **dış tırnağınla aynı** tırnak karakteri kullanılmış. Gerçek örnek (`state.py:249-251`):

```python
# YANLIŞ (yalnız 3.12+): dis ve ic tirnak ayni karakter
f"records_identified({sayi("records_identified", 0)}) - "

# DOĞRU (3.9+): dis cift, ic tek
f"records_identified({sayi('records_identified', 0)}) - "
```

Kural: **f-string dış tırnağı çift (`"`), iç atıf tek (`'`) olmalı.** 10 satırın
tamamı bu desene uyar. Düzeltmeden sonra şu üç komut da geçmeli:

```bash
python -c "import ast,pathlib; ast.parse(pathlib.Path('tools/atw/state.py').read_text(encoding='utf-8'))"
python -c "import ast,pathlib; ast.parse(pathlib.Path('tools/atw/state.py').read_text(encoding='utf-8'), feature_version=(3,9))"
python -c "import ast,pathlib; ast.parse(pathlib.Path('tools/atw/state.py').read_text(encoding='utf-8'), feature_version=(3,10))"
```

İlk komut bugün **hata verir** (`SyntaxError`); üçü de geçmelidir.

- [ ] **3.3** `tools/atw/state.py`'de `find_dangling_references()`'ı `graph`'a yönlendir (D6, geriye uyumlu sarmalayıcı):

```python
def find_dangling_references(durum: dict[str, Any]) -> list[str]:
    """Durumdaki kopuk kimlik referanslarini dondurur.

    Ince bir sarmalayici: gercek denetim ``graph.kopuk_baglari()``dir.
    Mevcut cagri imzasi ve donus tipi korunur.
    """
    from tools.atw import graph

    return graph.kopuk_baglari(durum)
```

> **Görev 4'e kadar bu adım yapılmaz.** `graph.py` henüz yok. Bu adım
> Görev 4'ün 4.6'sına taşındı. Burada yalnız yorum notu düşülür.

- [ ] **3.4** `requirements.txt`'e dil tabanını belgele:

```
# Python 3.9+ gerekir. 3.11 ve altinda PEP 701 f-string'leri (ic ice
# tirnak) ayristirilamaz; bu paket 3.12'ye bagimli olmaktan cikarildi.
jsonschema>=4.22.0
pytest>=8.0.0
pytest-cov>=5.0.0
```

- [ ] **3.5** **Testleri önce yaz.** `tests/schema_tests/test_format_checker.py` oluştur:

```python
"""format kisitlarinin gercekten zorlandigi testler."""
from __future__ import annotations

import pytest
from jsonschema.exceptions import ValidationError

from tools.atw.state import load_schema, validate_state


def _kaynak(**ek):
    """`source.json`'a gore gecerli bir kayit uretir.

    `verification` yarisi ic ice bir nesnedir ve dort alanin hepsi
    zorunludur; eksik birik birakmak bu testleri sessizce kirar.
    """
    return {
        "id": "SRC-001",
        "title": "Kurgusal ornek",
        "source_type": "article",
        "verification": {
            "status": "pending",
            "bibliographic_match": 0.0,
            "verified_at": "2026-09-26T10:12:00+00:00",
            "verification_sources": ["manual"],
        },
        **ek,
    }


def test_bozuk_access_date_reddediliyor():
    from tools.atw.state import _state_validator
    dogrulayici = _state_validator()
    sema = load_schema("source.json")
    kayit = _kaynak(access_date="26.09.2026")
    with pytest.raises(ValidationError) as hata:
        dogrulayici.evolve(schema=sema).validate(kayit)
    assert "'date'" in str(hata.value)


def test_access_date_yalniz_tarih_kabul():
    from tools.atw.state import _state_validator
    dogrulayici = _state_validator()
    sema = load_schema("source.json")
    dogrulayici.evolve(schema=sema).validate(_kaynak(access_date="2026-09-26"))


def test_access_date_null_kabul():
    from tools.atw.state import _state_validator
    dogrulayici = _state_validator()
    sema = load_schema("source.json")
    dogrulayici.evolve(schema=sema).validate(_kaynak(access_date=None))


def test_verified_at_gun_yalniz_reddediliyor():
    """verified_at '2026-09-26' OLABILMEZ: 4 fixture tam tarih-saat
    kullaniyor, belgeler de eski haliyle gun yaziyordu."""
    from tools.atw.state import _state_validator
    dogrulayici = _state_validator()
    sema = load_schema("source.json")
    kayit = _kaynak()
    kayit["verification"]["verified_at"] = "2026-09-26"
    with pytest.raises(ValidationError) as hata:
        dogrulayici.evolve(schema=sema).validate(kayit)
    assert "'date-time'" in str(hata.value)


def test_verified_at_tam_tarih_saat_kabul():
    from tools.atw.state import _state_validator
    dogrulayici = _state_validator()
    sema = load_schema("source.json")
    kayit = _kaynak()
    kayit["verification"]["verified_at"] = "2026-09-26T10:12:00+00:00"
    dogrulayici.evolve(schema=sema).validate(kayit)


def test_bozuk_search_run_timestamp_reddediliyor():
    from tools.atw.state import _state_validator
    dogrulayici = _state_validator()
    sema = load_schema("search_run.json")
    kayit = {"id": "SEARCH-001", "query": "kurgusal",
             "database": "crossref", "timestamp": "2026-09-26 09:00"}
    with pytest.raises(ValidationError):
        dogrulayici.evolve(schema=sema).validate(kayit)


def test_bos_durum_formatlari_gecer():
    assert validate_state(_bos_durum()) == []


def _bos_durum():
    from tools.atw.state import empty_state
    return empty_state("THESIS-2026-001", "Ornek Tez")


def test_arac_kodu_uc_dokuzda_ayristiriliyor():
    """Paket 3.9'da da ayristirilabilmeli. Canli yorumlayici 3.12'de
    oldugu icin gercek komsu surumu degil, istenen ozelligin ozelligi
    sinanir."""
    import ast
    import pathlib
    kok = pathlib.Path(__file__).resolve().parents[2]
    for betik in sorted((kok / "tools" / "atw").glob("*.py")):
        kaynak = betik.read_text(encoding="utf-8")
        ast.parse(kaynak, filename=str(betik), feature_version=(3, 9)), betik.name
```

- [ ] **3.6** Testleri çalıştır — `feature_version` testi ve `FormatChecker` testleri **kırmızı** olmalı:

```bash
python -m pytest tests/schema_tests/test_format_checker.py -q -p no:cacheprovider
```

- [ ] **3.7** `state.py`'deki 10 f-string'i düzelt (3.2), sonra doğrula:

```bash
python -m pytest tests/schema_tests/test_format_checker.py -q -p no:cacheprovider
```

- [ ] **3.8** Tüm testler:

```bash
python -m pytest tests/ -q -p no:cacheprovider
```

- [ ] **3.9** Commit:

```
fix(runtime): 3.9 uyumlulugu, FormatChecker baglantisi, surum tabani

S3: paket artik 3.12'ye bagimli degil ve format kisitlari gercekten
zorlaniyor.

FormatChecker neden baglandi
---------------------------
jsonschema "format" anahtarlarini tanimaz; yalnizca tanimliysa dogrular.
Baglanmadan once "date-time" yazan bir alan istedigimiz kadar
gecersiz sayilirdi. Olcum: 18 semada format tasiyan alan sayisi 1
(search_run.timestamp), 7 fixture'lik veri setinde bu alan hic
gectigine gore hicbir mevcut veri kirilmaz.

Iki tarih bicimi ayri ayri test edildi
-------------------------------------
  access_date  "26.09.2026" reddedilir, "2026-09-26" kabul edilir
  verified_at  "2026-09-26" REDDEDILIR, tam tarih-saat kabul edilir
verified_at'in gun-yalniz reddedilmesi bir sey ifade etmiyordu once:
belge "2026-09-25" yaziyordu ve hicbir test bunu yalnizca dogru
bulmuyordu. Simdi ikisi de kirmizi cikiyor.

3.9 uyumlulugu
--------------
state.py:249-269 arasindaki 10 f-string PEP 701 ic ice tirnak
kullaniyordu; bu ozellik yalniz 3.12+'da gecerli. Yani 3.11'de
paketin TAMAMI SyntaxError veriyordu. Dis tirnak cift, ic atif tek
olacak sekilde duzeltildi.

Dogrulama canli yorumlayici degil ast.parse(feature_version=(3,9))
ile yapiliyor: gelistirme 3.12'de oldugu icin gercek komsu surum
bulunamaz, istenen ozelligin ozelligi sinanir. Bu test sayesinde
ilerde biri ic ice tirnak eklerse kirmizi olur.

Sapma: find_dangling_references() yonlendirmesi bu dilimden cikarildi
ve Gozlem 4'e tasindi. graph.py henuz yaratilmadigi icin yonlendirme
burada yapilamazdi. D6 karari aynen uygulanir, sadece sirasi degisti.
```

---

## Görev 4 — S4: Kanıt grafiği sorgu katmanı

**Amaç:** Fiilen çalışmayan kopuk-referans denetimini düzeltmek ve şemadan türetilen bir kanıt grafiği sorgu katmanı kurmak.

**Oluşturulan:** `tools/atw/graph.py`, `tests/unit_tests/test_graph.py`
**Değiştirilen:** `tools/atw/state.py`

**Ölçüm (bugün, 18 şema):** `thesis_state` hariç 17 şemada toplam **55** alan `pattern` taşıyor. Bunlardan **53**'ün öneki `ID_PREFIXES`'te → **kenar**. Kalan **2**'si biçim kuralı, kenar **değildir**: `figure.image_path` (`\.(png|jpg|…)$`) ve `source.doi` (`^$|^10\.\d{4,9}/\S+$`). `thesis_state`'in kendi 3 desen alanı kenar tablosuna girmez. Bugün yalnız 6'sı denetleniyor, **47'si denetlenmiyor**. Görev 2'den sonra **59** olacak. Test sabit sayıyla değil **şemadan türetilen sayıyla** karşılaştıracak.

**İkinci hata (F18):** `audit.json` kimlik alanı `id` değil `audit_id`. `state.py:160` `kayit.get("id")` → `None` → `continue`. Yani **audit kayıtları hiç gezilmiyor.**

### Adımlar

- [ ] **4.1** `tools/atw/graph.py` oluştur. Tam içerik:

```python
"""Kanit grafigi sorgulari: kenarlar semalardan turetilir.

Grafik materyalize edilmez. Bu modul ``thesis_state.json`` uzerinde
salt-okunur gezinir ve hicbir sey diske yazmaz.

Iki sey elle yazilmaz:

* **Kenar tablosu.** Her alanin ``pattern`` degeri oneki verir,
  ``ID_PREFIXES`` oneki varlik adina cevirir. Yeni sema eklendiginde
  tablo kendiliginden genisler.
* **Registry haritasi.** ``thesis_state.json``'in ``$ref`` dizilerinden
  turetilir; hangi alan hangi varligi tutuyor sema zaten soyluyor.

Elle yazilan tek parca ``_ANLAMSAL_ALANLAR`` sabitidir.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Final, Iterator, NamedTuple

from tools.atw.ids import ID_PREFIXES
from tools.atw.state import SCHEMA_DIR

#: Yapi veya anlam. "Bu kayit nereye bagli?" / "Neyi destekliyor?"
YAPISAL: Final = "yapisal"
ANLAMSAL: Final = "anlamsal"

_ONEK_DESENI: Final = re.compile(r"^\^([A-Z]+)-")


@dataclass(frozen=True)
class Kenar:
    """Bir referans alani: kayit tipi -> hedef tipi baglantisi."""

    kayit_tipi: str
    alan_adi: str
    hedef_tipi: str
    coklu_mu: bool
    tur: str

    @property
    def anahtar(self) -> tuple[str, str]:
        return (self.kayit_tipi, self.alan_adi)


class Zincir(NamedTuple):
    """Bir kaynaktan hedefe yuruyusun adimlari."""

    adim: str
    kimlik: str
    tur: str
```

> **`_REGISTRY_FIELDS` ve `_STATE_IDENTITY` neden içe aktarılmıyor?**
> `_REGISTRY_FIELDS` (`state.py:33`) elle yazılmış 15 alanlık bir liste
> ve **eksik**: `thesis_state.json` 19 `$ref` dizisi taşıyor, listede
> `research_questions`, `hypotheses`, `chapters`, `variables` yok. Bu
> eksikle hedef kümesi boş kalır ve `finding.rq_id` gibi **geçerli**
> referanslar kopuk bildirilir. `graph.py` haritayı semadan türetir
> (bkz. 4.4). `_STATE_IDENTITY = "id"` sabiti de kullanılmaz: `audit`
> kayıtlarının kimliği `id` değil `audit_id` (F18).

- [ ] **4.2** Aynı dosyaya şema tarama ve türetme fonksiyonlarını ekle:

```python
def _kimlik_alani(sema: dict[str, Any], sema_adi: str) -> str | None:
    """Kaydin kimlik alanini semadan belirler.

    ``id`` varsa o. Yoksa varlik adinin kendi ``*_id`` alani olabilir:
    ``audit.json`` -> ``audit_id`` (F18).

    Onemli: aday alan adi ``sema_adi``den **turetilir**, ``pattern``
    icindeki onkiden degil. ``pattern`` "AUD" verir, alan adi "audit_id"
    verir; karsilastirilirsa buyuk/kucuk harf yuzunden hic eslesmez ve
    ``audit_id`` bir kenara girer - yani duzeltmek icin yazilan kod
    duzeltmek icin yazildigi hatayi yeniden uretir.
    """
    ozellikler = sema.get("properties") or {}
    if "id" in ozellikler:
        return "id"
    aday = f"{sema_adi}_id"
    return aday if aday in ozellikler else None


def _tur_belirle(alan_adi: str) -> str:
    """Alan adindan kenar turunu cikarir.

    Kural: alan adi neyi *anlatiyorsa* o yon degistirme anlam, "nereye
    bagli" yonu yapidadir. Kanit/idda zinciri alanlari (evidence_ids,
    sources, claims, findings, datasets, analyses, statistics, tables,
    figures, research_questions, rq_ids, hypothesis_outcomes,
    paragraph_id, chapter) yapisaldir. Degerlendirme nitelikli
    alanlar (contradicted_by, counter_claims, related_claims,
    agrees_with, disagrees_with, supersedes_source_id,
    original_source_id, conflicting_claim_ids, contradicting_source_ids)
    ve asyikadir.
    """
    if alan_adi in _ANLAMSAL_ALANLAR:
        return ANLAMSAL
    return YAPISAL
```

- [ ] **4.3** Aynı dosyaya `_ANLAMSAL_ALANLAR` sabitini ve türetme döngüsünü ekle. Bu liste **elle yazılmıştır** ve kenar tablosunun tek elle yazılan parçasıdır; kalan her şey hesaplanır:

```python
#: Anlamsal kenar alanlari. Bunlar "nereye bagli" degil, "neyi
#: destekliyor / celistiriyor / yerine gecti" anlami tasir.
_ANLAMSAL_ALANLAR: Final[frozenset[str]] = frozenset({
    "contradicted_by", "counter_claims", "related_claims",
    "agrees_with", "disagrees_with", "supersedes_source_id",
    "original_source_id", "conflicting_claim_ids",
    "contradicting_source_ids", "supports_claim", "supports_claims",
})
```

```python
def _semalari() -> dict[str, dict]:
    return {p.stem: json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(SCHEMA_DIR.glob("*.json"))}


def _referans_alanlari(sema: dict[str, Any], yol: str = "") -> Iterator[tuple[str, bool, str]]:
    """Sema icindeki tum kimlik referans alanlarini gezer.

    Yields:
        (alan_yolu, coklu_mu, hedef_tipi)
    """
    for ad, tanim in (sema.get("properties") or {}).items():
        if ad == "$comment":
            continue
        tam = f"{yol}{ad}"
        if not isinstance(tanim, dict):
            continue
        dizi = tanim.get("type") == "array"
        oge = tanim.get("items") if dizi else tanim
        if not isinstance(oge, dict):
            continue
        desen = oge.get("pattern")
        eslesme = _ONEK_DESENI.match(desen) if isinstance(desen, str) else None
        if eslesme and eslesme.group(1) in ID_PREFIXES:
            yield (tam, dizi, ID_PREFIXES[eslesme.group(1)])
            continue
        if oge.get("type") == "object" and oge.get("properties"):
            yield from _referans_alanlari(oge, f"{tam}.")


@lru_cache(maxsize=1)
def kenar_tablosu() -> tuple[Kenar, ...]:
    """Semalardan turetilen kenar tablosu. Onbellekli ve salt-okunur.

    Yeni sema eklendiginde bu tablo kendiliginden genisler; elle
    guncellenmez. Olculen: 18 semada 53 kenar (Gorev 2'den sonra 59).
    """
    semalar = _semalari()
    kimlikler = _kimlik_alanlari(semalar)
    kenarlar: list[Kenar] = []
    for sema_adi, sema in semalar.items():
        if "$schema" not in sema or sema_adi == "thesis_state":
            continue
        for alan_yolu, coklu, hedef in _referans_alanlari(sema):
            if alan_yolu in kimlikler:
                continue
            kenarlar.append(Kenar(
                kayit_tipi=sema_adi,
                alan_adi=alan_yolu,
                hedef_tipi=hedef,
                coklu_mu=coklu,
                tur=_tur_belirle(alan_yolu.split(".")[-1]),
            ))
    return tuple(kenarlar)
```

`thesis_state` neden atlanıyor: kendi alanları (`sources`, `citations`,
`human_approvals` …) kayıt *listesi* taşıyıcılarıdır, kimlik referansı
değildir. Onun referansları varlık şemalarının içindedir.

**Ölçülen 53 kenarın 2'si desen taşısa da kenar değildir:**
`figure.image_path` (`\.(png|jpg|…)$`) ve `source.doi`
(`^$|^10\.\d{4,9}/\S+$`) önek içermez, `ID_PREFIXES`'te bulunmaz, bu
yüzden kenar tablosuna girmezler. Onlar biçim kuralıdır.

- [ ] **4.4** Aynı dosyaya `_KIMLIK_ALANLARI` ve kayıt gezinme yardımcılarını ekle:

```python
def _kimlik_alanlari(semalar: dict[str, dict]) -> frozenset[str]:
    """Her semada kaydin kendi kimlik alani olan alanlar. Bunlar
    referans degildir; kenara girmez."""
    alanlar: set[str] = set()
    for sema_adi, sema in semalar.items():
        alan = _kimlik_alani(sema, sema_adi)
        if alan:
            alanlar.add(alan)
    return frozenset(alanlar)


_KIMLIK_ALANLARI: Final = _kimlik_alanlari(_semalari())


@lru_cache(maxsize=1)
def registry_haritasi() -> dict[str, str]:
    """Durum alani -> varlik tipi. ``thesis_state.json``'den turetilir.

    Her ``$ref`` dizisi bir registry'dir. Elle yazilan
    ``state._REGISTRY_FIELDS`` 15 alan icerir ve 4'unu kacirir;
    bu yuzden burada kullanilmaz. Olculen: 18 semada 19 alan.
    """
    harita: dict[str, str] = {}
    for alan, tanim in (_semalari()["thesis_state"].get("properties") or {}).items():
        if not isinstance(tanim, dict):
            continue
        oge = tanim.get("items")
        ref = oge.get("$ref") if isinstance(oge, dict) else None
        if isinstance(ref, str) and ref.endswith(".json"):
            harita[alan] = ref[:-len(".json")]
    return harita


def _kimlik(kayit: dict) -> str | None:
    """Kaydin kimligi. ``audit`` kayitlarinda alan adi ``audit_id``."""
    for alan in ("id", "audit_id"):
        deger = kayit.get(alan)
        if isinstance(deger, str) and deger:
            return deger
    return None


def _ic_refler(varlik_tipi: str) -> list[tuple[str, str]]:
    """Varlik semasindaki ic ice ``$ref`` dizileri: (alan, alt varlik).

    ``paragraph`` kayitlari ust duzey registry degil, ``chapter``'in
    icinde yasar. ``citation.paragraph_id`` bu yuzden yalnizca bu
    indeksle denetlenebilir.
    """
    sema = _semalari().get(varlik_tipi) or {}
    cikti: list[tuple[str, str]] = []
    for alan, tanim in (sema.get("properties") or {}).items():
        if not isinstance(tanim, dict) or tanim.get("type") != "array":
            continue
        oge = tanim.get("items")
        ref = oge.get("$ref") if isinstance(oge, dict) else None
        if isinstance(ref, str) and ref.endswith(".json"):
            cikti.append((alan, ref[: -len(".json")]))
    return cikti


def _kayitlar(durum: dict[str, Any]) -> Iterator[tuple[str, dict]]:
    """Durumdaki tum kayitlari (varlik_tipi, kayit) uclusuyle verir.

    Ic ice koleksiyonlar da dahil: ``chapter.paragraphs[]`` icindeki
    paragraf kayitlari ``paragraph`` turuyle yields edilir.
    """
    for alan, varlik_tipi in registry_haritasi().items():
        for kayit in (durum.get(alan) or []):
            if not isinstance(kayit, dict):
                continue
            yield (varlik_tipi, kayit)
            for ic_alan, alt in _ic_refler(varlik_tipi):
                for ic in (kayit.get(ic_alan) or []):
                    if isinstance(ic, dict):
                        yield (alt, ic)


def _var_mi(durum: dict[str, Any], varlik_tipi: str) -> set[str]:
    """Verilen varlik tipindeki tum kimlikler."""
    return {
        kimlik
        for varlik, kayit in _kayitlar(durum)
        if varlik == varlik_tipi
        for kimlik in [_kimlik(kayit)]
        if kimlik
    }


def _kimlikler(durum: dict[str, Any], varlik_tipi: str) -> Iterator[tuple[dict, str]]:
    for varlik, kayit in _kayitlar(durum):
        if varlik != varlik_tipi:
            continue
        kimlik = _kimlik(kayit)
        if kimlik:
            yield (kayit, kimlik)
```

> **`_REGISTRY_FIELDS` neden kullanılmıyor?** Bkz. 4.1 notu: eksik olması
> `research_question` ve `hypothesis` hedeflerini boş bırakır ve geçerli
> referansları kopuk bildirir.

- [ ] **4.5** Aynı dosyaya sorgu fonksiyonlarını ekle:

```python
def kopuk_baglari(durum: dict[str, Any]) -> list[str]:
    """Durumdaki tum kopuk kimlik referanslarini dondurur.

    Kapsam: semalardaki HER referans alani. Daha once yalniz
    ``<ad>_id`` kaliplari denetleniyordu ve 53 referans alaninin 6'si
    kapsaniyordu.
    """
    bulunanlar: list[str] = []
    for varlik, kayit in _kayitlar(durum):
        for kenar in kenar_tablosu():
            if kenar.kayit_tipi != varlik:
                continue
            deger = kayit
            for parca in kenar.alan_adi.split("."):
                if not isinstance(deger, dict):
                    deger = None
                    break
                deger = deger.get(parca)
            if deger is None:
                continue
            referanslar = deger if kenar.coklu_mu else [deger]
            var = _var_mi(durum, kenar.hedef_tipi)
            for referans in referanslar:
                if isinstance(referans, str) and referans not in var:
                    bulunanlar.append(
                        f"{varlik}.{kenar.alan_adi} -> {referans} "
                        f"({kenar.hedef_tipi} bulunamadi)")
    return sorted(set(bulunanlar))


def source_kullanan_iddialar(durum: dict, source_id: str) -> list[str]:
    """Verilen kaynagi kullanan iddia kimlikleri (yapisal yuru)."""
    sonuc = []
    for kenar in kenar_tablosu():
        if kenar.hedef_tipi != "source" or kenar.tur != YAPISAL:
            continue
        for kayit, kimlik in _kimlikler(durum, kenar.kayit_tipi):
            deger = kayit.get(kenar.alan_adi)
            if deger is None:
                continue
            liste = deger if kenar.coklu_mu else [deger]
            if source_id in liste:
                sonuc.append(kimlik)
    return sorted(set(sonuc))


def iddiyanin_dayandigi_kaynaklar(durum: dict, claim_id: str) -> list[str]:
    """Verilen iddianin dayandigi kaynak kimlikleri."""
    for kayit, kimlik in _kimlikler(durum, "claim"):
        if kimlik != claim_id:
            continue
        kaynaklar = list(kayit.get("sources") or [])
        for evd in kayit.get("evidence_ids") or []:
            for e_kayit, e_kimlik in _kimlikler(durum, "evidence"):
                if e_kimlik == evd:
                    src = e_kayit.get("source_id")
                    if isinstance(src, str):
                        kaynaklar.append(src)
        return sorted(set(kaynaklar))
    return []


def bulgunun_kanit_zinciri(durum: dict, finding_id: str) -> list[Zincir]:
    """Bulgudan kaynaklara uzanan kanit zinciri."""
    zincir: list[Zincir] = []
    for kayit, kimlik in _kimlikler(durum, "finding"):
        if kimlik != finding_id:
            continue
        zincir.append(Zincir("bulgu", kimlik, YAPISAL))
        for evd in kayit.get("evidence_ids") or []:
            zincir.append(Zincir("kanit", evd, YAPISAL))
            for e_kayit, e_kimlik in _kimlikler(durum, "evidence"):
                if e_kimlik != evd:
                    continue
                if e_kayit.get("supports_claim"):
                    zincir.append(Zincir("iddia", e_kayit["supports_claim"],
                                         ANLAMSAL))
                if e_kayit.get("source_id"):
                    zincir.append(Zincir("kaynak", e_kayit["source_id"],
                                         YAPISAL))
        return zincir
    return []


def rq_dan_kaynakca(durum: dict, rq_id: str) -> list[Zincir]:
    """Araştırma sorusundan kaynakçaya uzanan zincir.

    Yön önemli: ``claim.json``'de bir araştırma sorusu alanı **yoktur**.
    Bağ ``research_question.related_claims`` ile ters yönde kurulur, yani
    sorudan iddiaya gitmek için önce soru kaydını bulup ``related_claims``
    listesini okumak gerekir.
    """
    zincir: list[Zincir] = [Zincir("soru", rq_id, YAPISAL)]
    for kayit, kimlik in _kimlikler(durum, "research_question"):
        if kimlik != rq_id:
            continue
        for claim_id in (kayit.get("related_claims") or []):
            if not isinstance(claim_id, str):
                continue
            zincir.append(Zincir("iddia", claim_id, YAPISAL))
            for kaynak in iddiyanin_dayandigi_kaynaklar(durum, claim_id):
                zincir.append(Zincir("kaynak", kaynak, YAPISAL))
    return zincir


def retraksiyona_ugrayan_iddialar(durum: dict) -> list[str]:
    """Geri cekilmis kaynagi kullanan iddialar (yapisal yuru)."""
    geri = {kimlik for kayit, kimlik in _kimlikler(durum, "source")
            if kayit.get("retraction_status") == "retracted"}
    if not geri:
        return []
    sonuc = []
    for kaynak in sorted(geri):
        sonuc.extend(source_kullanan_iddialar(durum, kaynak))
    return sorted(set(sonuc))


def kanitsiz_iddialar(durum: dict) -> list[str]:
    """Hic kaniti olmayan iddialar."""
    return sorted(kimlik for kayit, kimlik in _kimlikler(durum, "claim")
                  if not (kayit.get("evidence_ids") or []))


def celiskili_iddialar(durum: dict) -> list[str]:
    """Celiskili iddialar (anlamsal yuru)."""
    sonuc: set[str] = set()
    for kayit, kimlik in _kimlikler(durum, "claim"):
        for kenar in kenar_tablosu():
            if kenar.kayit_tipi != "claim" or kenar.tur != ANLAMSAL:
                continue
            deger = kayit.get(kenar.alan_adi)
            if deger is None:
                continue
            liste = deger if kenar.coklu_mu else [deger]
            for diger in liste:
                if isinstance(diger, str) and diger != kimlik:
                    sonuc.add(kimlik)
                    sonuc.add(diger)
    return sorted(sonuc)
```

- [ ] **4.6** `tools/atw/state.py`'de `find_dangling_references()`'ı yönlendir (Görev 3, adım 3.3'ten taşındı):

```python
def find_dangling_references(durum: dict[str, Any]) -> list[str]:
    """Durumdaki kopuk kimlik referanslarini dondurur.

    Ince bir sarmalayici: gercek denetim ``graph.kopuk_baglari()``dir.
    Mevcut cagri imzasi ve donus tipi korunur.
    """
    from tools.atw import graph

    return graph.kopuk_baglari(durum)
```

- [ ] **4.7** `state.py`'de `import re` gereksizse kaldır; `json` hâlâ kullanılıyorsa kalsın. `ast`/`unicodedata` gibi kullanılmayan içe aktarmalar varsa temizle.

- [ ] **4.8** **Testleri önce yaz.** `tests/unit_tests/test_graph.py` oluştur:

```python
"""Kenar tablosu turetimi ve kanit grafigi sorgulari."""
from __future__ import annotations

import json

import pytest

from tools.atw import graph
from tools.atw.state import SCHEMA_DIR, empty_state, find_dangling_references


def _dolu_durum() -> dict:
    """Butun varlik tiplerini temsil eden kurgusal bir durum.

    Alan adlari ve zorunlu alanlar semalardan birebir alinmistir; ornek
    kayitlar semaya gecseydi kirilirdi (``claim``in metin alani
    ``statement`` degil ``text``'tir, ``research_question`` ``type`` ve
    ``status`` zorunludur, ``source.verification`` dort alan ister).
    """
    durum = empty_state("THESIS-2026-001", "Ornek Tez")
    durum["sources"] = [
        {"id": "SRC-001", "title": "Kurgusal A", "source_type": "article",
         "verification": {"status": "verified", "bibliographic_match": 0.95,
                          "verified_at": "2026-09-26T10:12:00+00:00",
                          "verification_sources": ["crossref"]},
         "retraction_status": "not_retracted"},
        {"id": "SRC-002", "title": "Kurgusal B", "source_type": "article",
         "verification": {"status": "verified", "bibliographic_match": 0.91,
                          "verified_at": "2026-09-26T10:12:00+00:00",
                          "verification_sources": ["crossref"]},
         "retraction_status": "retracted"},
    ]
    durum["research_questions"] = [
        {"id": "RQ-001", "text": "Kurgusal soru?", "type": "main",
         "status": "answered", "related_claims": ["CLM-001"]},
    ]
    durum["chapters"] = [
        {"id": "CH-002", "number": 2, "title": "Kuramsal Cerceve",
         "paragraphs": [{"id": "P-014", "type": "background",
                         "chapter": "CH-002", "section": "2.3"}]},
    ]
    durum["citations"] = [
        {"id": "CIT-001", "source_id": "SRC-001", "paragraph_id": "P-014",
         "style": "apa7"},
    ]
    durum["evidence_registry"] = [
        {"id": "EVD-001", "text": "Kurgusal", "source_id": "SRC-001",
         "location": {"page": 3}, "evidence_type": "literature",
         "strength": "direct", "supports_claim": "CLM-001"},
        {"id": "EVD-002", "text": "Kurgusal", "source_id": "SRC-002",
         "location": {"page": 7}, "evidence_type": "literature",
         "strength": "direct", "supports_claim": "CLM-002"},
    ]
    durum["claims_registry"] = [
        {"id": "CLM-001", "text": "Kurgusal", "importance": "high",
         "verification_status": "verified", "sources": ["SRC-001"],
         "evidence_ids": ["EVD-001"]},
        {"id": "CLM-002", "text": "Kurgusal", "importance": "medium",
         "verification_status": "verified", "sources": ["SRC-002"],
         "evidence_ids": ["EVD-002"]},
        {"id": "CLM-003", "text": "Kanitsiz kurgusal", "importance": "low",
         "verification_status": "unverified", "evidence_ids": []},
    ]
    durum["findings_registry"] = [
        {"id": "FND-001", "rq_id": "RQ-001", "statement": "Kurgusal",
         "evidence_ids": ["EVD-001"]},
    ]
    durum["audit_registry"] = [
        {"audit_id": "AUD-001", "thesis_id": "THESIS-2026-001",
         "audit_type": "integrity", "date": "2026-09-26", "findings": []},
    ]
    return durum


# --- kenar tablosu -----------------------------------------------------

def test_kenar_tablosu_bos_degil():
    assert len(graph.kenar_tablosu()) > 0


def test_kenar_tablosu_oncebellekli():
    """Ayni nesne donmelidir; onbellek ise yaramazsa tablo her
    cagrida yeniden turetilir ve testler yavaslar."""
    assert graph.kenar_tablosu() is graph.kenar_tablosu()


def test_kimlik_alanlari_kenara_girmez():
    """Kaydin kendi kimligi referans degildir."""
    alanlar = {k.alan_adi for k in graph.kenar_tablosu()}
    assert "id" not in alanlar
    assert "audit_id" not in alanlar


def test_tablodaki_her_alan_semada_var():
    """Tablo ⊆ sema."""
    semalar = {p.stem: json.loads(p.read_text(encoding="utf-8"))
               for p in sorted(SCHEMA_DIR.glob("*.json"))}
    hatalar = []
    for kenar in graph.kenar_tablosu():
        sema = semalar[kenar.kayit_tipi]
        deger = sema
        for parca in kenar.alan_adi.split("."):
            deger = deger.get("properties", {}).get(parca)
            if deger is None:
                hatalar.append(f"{kenar.kayit_tipi}.{kenar.alan_adi}")
                break
    assert not hatalar, "Tablodaki alanlar semada yok: " + ", ".join(hatalar)


def test_semadaki_her_referans_alani_tabloda():
    """Sema ⊆ tablo. Iki yonlu olceklemeden biri sessizce gecer."""
    tablo = {(k.kayit_tipi, k.alan_adi) for k in graph.kenar_tablosu()}
    semalar = {p.stem: json.loads(p.read_text(encoding="utf-8"))
               for p in sorted(SCHEMA_DIR.glob("*.json"))}
    eksikler = []
    for sema_adi, sema in semalar.items():
        if sema_adi == "thesis_state":
            continue
        for alan_yolu, _coklu, _hedef in graph._referans_alanlari(sema):
            if alan_yolu in graph._KIMLIK_ALANLARI:
                continue
            if (sema_adi, alan_yolu) not in tablo:
                eksikler.append(f"{sema_adi}.{alan_yolu}")
    assert not eksikler, "Tabloda olmayan referans alanlari: " + ", ".join(eksikler)


def test_kenar_sayisi_semadan_turetilir():
    """Sabit sayi degil, semadan turetilen sayi kullanilir. Yeni sema
    eklendiginde bu kriter kendiliginden gecerli kalir.

    Karsilastirma tablo ile bagimsiz bir sayim arasindadir: her sema icin
    dogrudan sayilir, sonra tabloyla karsilastirilir.
    """
    semalar = graph._semalari()
    dogrudan = [
        (sema_adi, alan_yolu)
        for sema_adi, sema in semalar.items()
        if "$schema" in sema and sema_adi != "thesis_state"
        for alan_yolu, _coklu, _hedef in graph._referans_alanlari(sema)
        if alan_yolu not in graph._KIMLIK_ALANLARI
    ]
    tablo = {(k.kayit_tipi, k.alan_adi) for k in graph.kenar_tablosu()}
    assert tablo == set(dogrudan)


def test_registry_haritasi_gercekci_sayi():
    """Harita elle yazilmis degil, 19 alan turer. Elle yazilan
    ``_REGISTRY_FIELDS`` 15'tir ve 4'unu kacirir."""
    harita = graph.registry_haritasi()
    assert len(harita) == 19
    for alan in ("research_questions", "hypotheses", "chapters", "variables"):
        assert alan in harita, f"{alan} haritada yok: kopuk baglar yanlis alarm verir"


def test_registry_haritasi_tum_dizileri_kapsar():
    """thesis_state'teki her ``$ref`` dizisi registry'dir."""
    sema = graph._semalari()["thesis_state"]
    beklenen = {
        alan for alan, t in (sema.get("properties") or {}).items()
        if isinstance(t, dict) and isinstance(t.get("items"), dict)
        and isinstance(t["items"].get("$ref"), str)
    }
    assert set(graph.registry_haritasi()) == beklenen


def test_bicim_kurallari_kenara_girmez():
    """``source.doi`` ve ``figure.image_path`` desen tasir ama onek
    icermez; bunlar bicim kuralidir, kimlik referansi degildir."""
    alanlar = {(k.kayit_tipi, k.alan_adi) for k in graph.kenar_tablosu()}
    assert ("source", "doi") not in alanlar
    assert ("figure", "image_path") not in alanlar


def test_thesis_id_kenar_degildir():
    """``audit.thesis_id`` desen tasimaz. Bu dogru: ``thesis_id``
    (``THESIS-2026-001``) bir registry varligi degil, tezin kendi
    serbest bicimli kimligidir. Desen eklenmemeli - eklenirse her
    audit kaydi kopuk bildirilir."""
    alanlar = {(k.kayit_tipi, k.alan_adi) for k in graph.kenar_tablosu()}
    assert ("audit", "thesis_id") not in alanlar


# --- kopuk bag denetimi -------------------------------------------------

def test_bos_durumde_kopuk_bag_yok():
    assert graph.kopuk_baglari(empty_state("THESIS-2026-001", "Ornek")) == []


def test_bos_sozluk_kirmaz():
    """Eksik durum KeyError firlatmamali (Review Focus 4)."""
    assert graph.kopuk_baglari({}) == []


def test_null_registry_kirmaz():
    """Alan null ise .get(alan, []) devreye girmez; None atar (Review Focus 4)."""
    durum = empty_state("THESIS-2026-001", "Ornek")
    durum["sources"] = None
    durum["evidence_registry"] = None
    assert graph.kopuk_baglari(durum) == []


def test_dolu_durumun_kendisi_tutarli():
    """Kritik: ornek durumda HICBIR kopuk bag olmamali.

    Bu test kirmizi donerse ya kenar tablosu yanlis uretiliyor ya da
    registry haritasi eksik. Biri degilse digeri bozuk demektir."""
    kopuk = graph.kopuk_baglari(_dolu_durum())
    assert not kopuk, "Ornek durumda kopuk var: " + "; ".join(kopuk)


def test_paragraph_ici_kayitlar_denetleniyor():
    """Paragraf ust duzey registry degil, ``chapter.paragraphs[]`` icinde
    yasar. Ic ice indeksleme olmazsa bu kayitlar hic gezilmez."""
    durum = _dolu_durum()
    assert "P-014" in graph._var_mi(durum, "paragraph")


def test_citation_paragraph_id_denetleniyor():
    """``citation.paragraph_id`` yalnizca ic ice indekslemeyle denetlenir."""
    durum = _dolu_durum()
    durum["citations"][0]["paragraph_id"] = "P-999"
    kopuk = graph.kopuk_baglari(durum)
    assert any("P-999" in k for k in kopuk), kopuk


def test_kendi_kimligi_kopuk_sayilmaz():
    """F18 regresyonu: ``audit_id`` bir referans degil, audit kaydinin
    kendi kimligidir. Kenara girerse her audit kaydi kopuk bildirilir."""
    durum = _dolu_durum()
    durum["audit_registry"][0]["audit_id"] = "AUD-002"
    kopuk = graph.kopuk_baglari(durum)
    assert not any("AUD-002" in k for k in kopuk), kopuk


def test_coklu_alan_kopugu_bulunuyor():
    """claim.evidence_ids daha once hic denetlenmiyordu."""
    durum = _dolu_durum()
    durum["claims_registry"][0]["evidence_ids"] = ["EVD-999"]
    kopuk = graph.kopuk_baglari(durum)
    assert any("EVD-999" in k for k in kopuk), kopuk


def test_ozel_adli_bag_kopugu_bulunuyor():
    """evidence.supports_claim daha once hic denetlenmiyordu."""
    durum = _dolu_durum()
    durum["evidence_registry"][0]["supports_claim"] = "CLM-999"
    assert any("CLM-999" in k for k in graph.kopuk_baglari(durum))


def test_ara_soru_kopugu_bulunuyor():
    """finding.rq_id: registry haritasi ``research_questions``'i
    kacirirsa bu alan HICBIR zaman denetlenmez."""
    durum = _dolu_durum()
    durum["findings_registry"][0]["rq_id"] = "RQ-999"
    assert any("RQ-999" in k for k in graph.kopuk_baglari(durum))


def test_audit_kayitlari_denetleniyor():
    """F18: ``audit.json`` kimlik alani ``id`` degil ``audit_id``.

    Eski kod ``kayit.get("id")`` diyordu -> ``None`` -> ``continue``:
    audit kayitlari hic gezilmiyordu. Dogrulanacak sey su an
    gezildikleridir - audit.json'in tek baska referans alani yok
    (``findings`` bir nesne dizisi, ``thesis_id`` desensiz).
    """
    durum = _dolu_durum()
    assert "AUD-001" in graph._var_mi(durum, "audit")


def test_sarmalayici_geriye_uyumlu():
    durum = _dolu_durum()
    assert find_dangling_references(durum) == graph.kopuk_baglari(durum)


# --- sorgular ----------------------------------------------------------

def test_source_kullanan_iddialar():
    durum = _dolu_durum()
    assert graph.source_kullanan_iddialar(durum, "SRC-001") == ["CLM-001"]


def test_iddianin_dayandigi_kaynaklar_kaynaga_indirger():
    durum = _dolu_durum()
    assert graph.iddiyanin_dayandigi_kaynaklar(durum, "CLM-001") == ["SRC-001"]


def test_bulgunun_kanit_zinciri():
    durum = _dolu_durum()
    zincir = graph.bulgunun_kanit_zinciri(durum, "FND-001")
    turler = [(z.adim, z.kimlik) for z in zincir]
    assert ("bulgu", "FND-001") in turler
    assert ("kanit", "EVD-001") in turler
    assert ("iddia", "CLM-001") in turler
    assert ("kaynak", "SRC-001") in turler


def test_rq_dan_kaynakca():
    durum = _dolu_durum()
    turler = [(z.adim, z.kimlik) for z in graph.rq_dan_kaynakca(durum, "RQ-001")]
    assert ("soru", "RQ-001") in turler
    assert ("iddia", "CLM-001") in turler
    assert ("kaynak", "SRC-001") in turler


def test_retraksiyona_ugrayan_iddialar():
    """Review Focus 5: geri cekilmis kaynagi kullanan iddia."""
    durum = _dolu_durum()
    assert graph.retraksiyona_ugrayan_iddialar(durum) == ["CLM-002"]


def test_retraksiyon_yoksa_bos_liste():
    durum = _dolu_durum()
    durum["sources"][1]["retraction_status"] = "not_retracted"
    assert graph.retraksiyona_ugrayan_iddialar(durum) == []


def test_kanitsiz_iddialar():
    assert graph.kanitsiz_iddialar(_dolu_durum()) == ["CLM-003"]


def test_celiskili_iddialar():
    durum = _dolu_durum()
    durum["claims_registry"][0]["contradicted_by"] = ["CLM-002"]
    assert graph.celiskili_iddialar(durum) == ["CLM-001", "CLM-002"]


def test_kenar_turleri_ikili():
    turler = {k.tur for k in graph.kenar_tablosu()}
    assert turler <= {graph.YAPISAL, graph.ANLAMSAL}
    assert turler == {graph.YAPISAL, graph.ANLAMSAL}
```

- [ ] **4.9** Testleri çalıştır — **kırmızı** olmalı (`graph` modülü henüz yok → `ImportError`):

```bash
python -m pytest tests/unit_tests/test_graph.py -q -p no:cacheprovider
```

- [ ] **4.10** `graph.py`'yi tamamla ve testleri çalıştır — **yeşil** olmalı:

```bash
python -m pytest tests/unit_tests/test_graph.py -q -p no:cacheprovider
```

- [ ] **4.11** Tüm testler:

```bash
python -m pytest tests/ -q -p no:cacheprovider
```

- [ ] **4.12** Commit:

```
feat(graph): semadan turetilen kenar tablosu ve kanit grafigi sorgulari

S4: kopuk referans denetimi artik calisiyor.

Kapsam olculdu
--------------
18 semada (thesis_state haric) 55 alan "pattern" tasiyor. Bunlarin
17'si kaydin kendi "id" kimlik alani - referans degil. 2'si bicim
kurali (source.doi, figure.image_path) - onek icermez. Kalan **53**
kenar.
Onceki fonksiyon yalniz f"{ad}_id" kaliplarini ariyordu ve bu
isimlerden semalarda yalniz 6 alan vardi:

  source_id    2  citation.source_id, evidence.source_id
  dataset_id   1  analysis.dataset_id
  finding_id   1  statistic.finding_id
  analysis_id  1  statistic.analysis_id
  audit_id     1  audit.audit_id

Yani 53 referansin 47'si denetlenmiyordu. Tum coklu alanlar
(claim.evidence_ids, finding.evidence_ids, source.evidence_ids,
search_run.included_source_ids, table.statistic_ids, paragraph.claims,
paragraph.evidence, ...) ve tum ozel adlandirilmis baglar
(evidence.supports_claim, claim.contradicted_by, claim.counter_claims,
discussion.agrees_with/disagrees_with, research_question.answered_by,
figure.original_source_id, source.supersedes_source_id) sessizce gecirdi.

F18: audit kayitlari HICBIR ZAMAN gezilmiyordu
----------------------------------------------
audit.json kimlik alani "id" degil "audit_id". Eski kod
kayit.get("id") diyordu -> None -> continue. Yani yukaridaki
"audit_id denetleniyor" eslesmesi bile ise yaramazdi. graph.py kimlik
alanini semadan belirler: "id" varsa o, yoksa varligin kendi
"*_id" deseni. audit.json icin bu "audit_id" olur.
Registry haritasi semadan turetilir
------------------------------------
Elle yazilan ``state._REGISTRY_FIELDS`` 15 alan; ``thesis_state`` 19
$ref dizisi tasiyor (research_questions, hypotheses, chapters, variables
eksik). Bu eksiklik hedef kumesini bos birakir ve finding.rq_id gibi
gecerli referanslari kopuk bildirir. Harita artık thesis_state.json'den
turetilir (19 alan); S2'nin uc yeni $ref'i kendiliginden kapsanir.


Kenar tablosu elle yazilmaz
--------------------------
  schemas/*.json u ID_PREFIXES -> KenarTablosu
Her alanin "pattern" degeri oneki verir (^EVD-\d{3,}$ -> EVD),
ID_PREFIXES oneki varlik adina cevirir (EVD -> evidence). Yeni sema
eklendiginde tablo kendiliginden genisler. Elle yazilan tek parca
_ANLAMSAL_ALANLAR listesi ve testteki iki yonlu karsilastirma.

Iki yonlu dogrulama: tablo ⊆ sema ve sema ⊆ tablo. Iki test de var;
tek yonlu olceklemeden biri sessizce gecer ve kapsam daralir.

Ic ice indeksleme (paragraph)
-----------------------------
paragraph kayitlari ust duzey registry degil, chapter.paragraphs[] icinde
yasar. citation.paragraph_id buna bagli. _kayitlar() ic ice $ref
dizilerine de iner; olmayan bu tek kenar hep kopuk bildirirdi.


Sayi sabitlenmedi
----------------
Kenar sayisi 53 (bugun) -> 59 (S2 sonrasi). Test sabit sayiyla degil
semadan turetilen sayiyla karsilastirir.

Kenar turleri ikili
-------------------
  yapisal   "bu kayit nereye bagli?"   finding.evidence_ids, paragraph.claims
  anlamsal  "neyi destekliyor/celistiriyor?"  claim.contradicted_by,
           source.supersedes_source_id

retraksiyona_ugrayan_iddialar yapisal, celiskili_iddialar anlamsal
yuru. Ayrim kenar tablosunda tur alaninda tasinir; yuruyus
fonksiyonlari tur parametresi alir.

Grafik materyalize edilmedi
---------------------------
Sorgu katmani salt-okunur. thesis_state.json tek dogruluk kaynagi
kalmaya devam ediyor; ayri bir graf deposu ve yeni bagimlilik yok.

find_dangling_references() geriye uyumlu bir sarmalayici oldu; mevcut
2 test kirmadi.
```

---

## Görev 5 — S5: Doküman gerçekliği

**Amaç:** Belgelerin gerçeği yansıtmasını sağlamak.

**Değiştirilen:** `README.md`, `references/citation_rules.md`
**Oluşturulan:** sözleşme testine iki denetim (`tests/contract_tests/test_docs.py`)

**Sıralama notu:** Bu görev S1'den sonra gelir çünkü `citation_rules.md` düzeltmesi S1'in sınıf-2 taramasına girer ve S1'in yeşil kalmasını bozabilirdi. S1'de yalnız `contradiction-analyzer.md`'daki `statistic.json → power` atfı düzeltildi; `citation_rules.md` bir referans dosyası ve S1'in tarayıcı kapsamı dışında.

### Adımlar

- [ ] **5.1** `references/citation_rules.md:54`'teki APA kuralını düzelt. Satır 54'teki "3+ yazar: APA'da ikinci yazardan sonra et al. kullanın" cümlesi, `Yazar1, Yazar2, et al.` üretir — bu APA 6'dır. Yerine:

```markdown
### Çoklu Yazarlar
- 2 yazara kadar: Tümünü listeleyin (Yazar, A. A., & Yazar, B. B.)
- 3+ yazar: **İlk yazarın soyadı + et al.**, ilk atıftan itibaren
  (Yazar, A. A., et al.)
```

- [ ] **5.2** `citation_rules.md:9-14`'teki "Desteklenen Atıf Stilleri" başlığını gerçeği yansıtacak şekilde değiştir:

```markdown
## Atıf Stilleri

**Bu dosya yalnız APA 7'yi uygular.** Aşağıdaki stiller desteklenen
seçenekler olarak listelenir, ancak her biri için ayrıntılı biçim
kuralları **bu dosyada yoktur**:

- **APA 7. Baskı** — uygulanır, aşağıdaki tüm örnekler bu stildedir
- MLA 9. Baskı — listelenir, kuralı yok
- Chicago Stili (Not-Bibliyografi) — listelenir, kuralı yok
- IEEE Formatı — listelenir, kuralı yok
- Harvard Sistemi — listelenir, kuralı yok

Başka bir stil gerekiyorsa `thesis_state.json` → `style_profile` alanı
o stilin adını taşımalı ve bu dosyaya o stilin kuralları eklenmelidir.
```

- [ ] **5.3** `citation_rules.md:5`'teki "(APA, MLA, Chicago, IEEE)" ifadesini 5.2 ile tutarlı hâle getir:

```markdown
2. **Tutarlı format kullan**: Seçilen atıf stilini tüm tez boyunca takip edin. Bu dosya yalnız APA 7 kurallarını uygular; diğer stiller için aşağıdaki "Atıf Stilleri" bölümüne bakın.
```

- [ ] **5.4** `README.md` sayılarını düzelt. Dört satır:

| Satır | Değişiklik |
|---|---|
| 257 | `8 modüler ajan` → `10 modüler ajan` |
| 277 | `8 alt ajan tanımı` → `10 alt ajan tanımı` |
| 280 | `7 veri şeması (JSON)` → `21 veri şeması (JSON)` |
| 281 | `5 akademik bütünlük referansı` → `7 akademik bütünlük referansı` |
| 290 | `Orchestrator + 8 ajan` → `Orchestrator + 10 ajan` |
| 253 | `19 sütun` → `18 sütun` (`templates/literature_matrix.md` başlık satırı 18 sütun) |

- [ ] **5.5** `README.md:268`'deki geçersiz komutu düzelt. `cp schemas/thesis_state.json thesis_state.json` **şemayı durum dosyası olarak kopyalıyor**; `validate_state()` bunu 14 eksik zorunlu alanla reddeder. Yerine:

````markdown
# Thesis State'i başlat (geçerli bir boş durum üretir)
python -c "import json,sys; sys.path.insert(0,'.'); \
from tools.atw.state import empty_state; \
print(json.dumps(empty_state('THESIS-2026-001','Tez Adı'), ensure_ascii=False, indent=2))" > thesis_state.json

# İlk tez için bilgileri doldur
# workflows/thesis_creation.md akışını takip et
````

- [ ] **5.6** `README.md:248-259` özellik listesini gerçeğe göre yeniden yaz. **12 özelliğin 11'i ✅ işaretli, yalnız 4'ü gerçekten var.** Yeni liste:

```markdown
## 🔍 Özellikler

**Uygulanmış (✅):**
- ✅ **Tez Durumu kalıcılığı**: `tools/atw/state.py` — şema doğrulamalı kaydetme/yükleme, `empty_state()` üreticisi
- ✅ **Paragraf metadata**: `schemas/paragraph.json` — `P-NNN` etiketleme ile iddia-kanıt-kaynak-RQ eşleşmesi
- ✅ **Sistematik İnceleme Protokolü**: `workflows/systematic_review.md` + `validate_prisma_flow()` — PRISMA akışı doğrulaması
- ✅ **Kalite denetim raporu**: `templates/quality_report.md` + `agents/consistency-auditor.md`
- ✅ **Bilgi Grafiği**: `tools/atw/graph.py` — şemadan türetilen kenar tablosu ve 8 sorgu
- ✅ **4 bileşenli denetim**: `agents/consistency-auditor.md` — terminoloji, sayılar, örneklem, yöntem-bulgular
- ✅ **Orchestrator mimarisi**: `SKILL.md` koordinatör, 10 modüler ajan

**Planlanmış (🚧):**
- 🚧 **Kaynak doğrulama motoru**: `tools/source_verify/` arayüzü var, uygulama P0-2'de
- 🚧 **Kaynak keşfi**: `tools/source_search/` arayüzü var, uygulama P0-2'de
- 🚧 **PDF → Kanıt**: `tools/pdf_extract/` arayüzü var, uygulama P0-3'te
- 🚧 **Atıf–kaynakça bütünlüğü**: `tools/citation_check/` arayüzü var, uygulama P0-4'te
- 🚧 **Çoklu atıf stili**: `references/citation_rules.md` yalnız APA 7 uygular; MLA/Chicago/IEEE/Harvard listelenir, kuralları yok
- 🚧 **Genişletilmiş Literatür Matrisi**: `templates/literature_matrix.md` 18 sütun; otomatik doldurma yok
```

> `tools/*/README.md` dosyalarının 4'ü de 195–322 karakterlik arayüz
> stub'ıdır — uygulama yoktur. "Arayüzü var" ifadesi bunu açıkça söyler.

- [ ] **5.7** **`tools/source_search/README.md` ve `tools/source_verify/README.md` stub'larını doldur** (P0-2 hazırlığı — 195 ve 322 karakter). Üçer eşleşme, girdi/çıktı sözleşmesi ve "henüz uygulanmadı" beyanı:

`tools/source_search/README.md`:
```markdown
# Kaynak Arama Aracı (Arayüz)

> **Durum: uygulanmadı.** Bu dosya P0-2'deki arayüz sözleşmesini
> tanımlar. P0-2 tamamlanana kadar `tools/source_search/` altında
> çalıştırılabilir kod yoktur.

## Görev
Araştırma sorusuna uygun kaynak adaylarını keşfet.

## Keşif veritabanları
Crossref, OpenAlex, Semantic Scholar, PubMed, Google Scholar

## Girdi
| Alan | Kaynak |
|------|--------|
| Araştırma sorusu | `thesis_state.research_questions` |
| Arama terimleri | `search_run.json` → `query` |
| Veritabanı | `search_run.json` → `database` (8 değerli enum) |

## Çıktı
`search_run.json` kaydı + `source.json` adayları.

**Doğrulama sınırı:** `search_run.database` enum'unda 8 veritabanı var
(keşif). `verification.verification_sources` yalnız 4 değer kabul eder
(`crossref`, `openalex`, `semantic_scholar`, `manual`). PubMed, Scopus,
Web of Science ve Google Scholar **keşif içindir, doğrulama kaynağı
değildir** — bir adayın `verified` olabilmesi için en az
`ESIK_ESLESME = 0.60` eşleşme ve `EN_AZ_BAGIMSIZ_KAYNAK = 2` bağımsız
doğrulama kaynağı gerekir.
```

`tools/source_verify/README.md`:
```markdown
# Kaynak Doğrulama Aracı (Arayüz)

> **Durum: uygulanmadı.** Bu dosya P0-2'deki arayüz sözleşmesini
> tanımlar. P0-2 tamamlanana kadar `tools/source_verify/` altında
> çalıştırılabilir kod yoktur.

## Görev
Kaynak adaylarının varlığını ve bibliyografik doğruluğunu bağımsız
veri kaynakları ile doğrula.

## Akış
```
Kaynak adayı
  ↓
Crossref
  ↓
OpenAlex
  ↓
Semantic Scholar
  ↓
DOI doğrulama
  ↓
Bibliyografik karşılaştırma
  ↓
KAYNAK DOĞRULANDI
```

## Girdi
| Alan | Kaynak |
|------|--------|
| Kaynak adayları | `thesis_state.sources` — `verification.status` değeri `pending` veya `unverified` |
| Arama kaydı | `thesis_state.search_runs` — adayın nereden bulunduğu |

## Çıktı
`source.json` kaydının `verification` ve `fulltext_available` alanları.

```json
{
  "verification": {
    "status": "verified",
    "verified_at": "2026-09-26T10:12:00+00:00",
    "verification_sources": ["crossref", "openalex"],
    "bibliographic_match": 0.95
  },
  "fulltext_available": null
}
```

`status` beş değer alır: `verified`, `unverified`, `pending`,
`retracted`, `corrected`.

## Sabitler
| Sabit | Değer | Anlamı |
|-------|-------|--------|
| `ESIK_ESLESME` | `0.60` | Bibliyografik eşleşme alt sınırı |
| `EN_AZ_BAGIMSIZ_KAYNAK` | `2` | `verified` için gereken bağımsız kaynak sayısı |

## Kural
Kanıt olmadan "verified evidence" kabul edilmez.
```

- [ ] **5.8** **Testleri önce yaz.** `tests/contract_tests/test_docs.py` oluştur:

```python
"""README ve referans belgelerinin gercegi yansitmasini dogrular."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
README = REPO_ROOT / "README.md"
ATIF = REPO_ROOT / "references" / "citation_rules.md"

# Bir README ogesinin ✅ alabilmesi icin somut bir varlik olmali ve
# o varlik bir arayuz stub'i olmamali.
# (aciklama, varlik yolu)
UYGULANMIS_YETENEKLER = {
    "Tez Durumu kalıcılığı": "tools/atw/state.py",
    "Paragraf metadata": "schemas/paragraph.json",
    "Sistematik İnceleme Protokolü": "workflows/systematic_review.md",
    "Kalite denetim raporu": "templates/quality_report.md",
    "Bilgi Grafiği": "tools/atw/graph.py",
    "4 bileşenli denetim": "agents/consistency-auditor.md",
    "Orchestrator mimarisi": "SKILL.md",
}

STUB_ESIGI = 400  # karakter


def _ozellik_maddeleri(metin: str) -> list[tuple[str, str]]:
    """(isaret, baslik) uclusu verir."""
    desen = re.compile(r"^- ([✅🚧]) \*\*(.+?)\*\*", re.MULTILINE)
    return [(i, b) for i, b in desen.findall(metin)]


def test_en az bir_yetenek_maddesi_var():
    assert _ozellik_maddeleri(README.read_text(encoding="utf-8"))


def test_yetenek_maddeleri_ayirt_edilebilir():
    """Her madde ya ✅ ya 🚧 isaretlemeli; isaretsiz madde denetlenemez."""
    metin = README.read_text(encoding="utf-8")
    bolum = metin.split("## 🔍 Özellikler", 1)[1].split("\n## ", 1)[0]
    for satir in bolum.splitlines():
        if satir.startswith("- ") and "**" in satir:
            assert satir.startswith("- ✅ ") or satir.startswith("- 🚧 "), satir


@pytest.mark.parametrize("baslik", sorted(UYGULANMIS_YETENEKLER))
def test_check_isaretli_yetenegin_varligi_var(baslik):
    metin = README.read_text(encoding="utf-8")
    isaretli = {b for i, b in _ozellik_maddeleri(metin) if i == "✅"}
    if baslik not in isaretli:
        pytest.skip(f"{baslik} artık ✅ degil")
    yol = REPO_ROOT / UYGULANMIS_YETENEKLER[baslik]
    assert yol.exists(), f"{baslik} ✅ işaretli ama {yol} yok"
    if yol.suffix == ".md":
        assert len(yol.read_text(encoding="utf-8")) > STUB_ESIGI, (
            f"{baslik} ✅ işaretli ama {yol} bir arayüz stub'ı")


def test_uygulanmis_yeteneklerin_tamami_readme_de():
    metin = README.read_text(encoding="utf-8")
    isaretli = {b for i, b in _ozellik_maddeleri(metin) if i == "✅"}
    assert isaretli == set(UYGULANMIS_YETENEKLER), (
        f"README ✅ yetenekleri kayıtla uyuşmuyor. "
        f"README: {sorted(isaretli)}")


@pytest.mark.parametrize("metin_adi", ["README.md"])
def test_sayimlar_gercek(metin_adi):
    metin = (REPO_ROOT / metin_adi).read_text(encoding="utf-8")
    assert "8 modüler ajan" not in metin
    assert "8 alt ajan" not in metin
    assert "Orchestrator + 8 ajan" not in metin
    assert "7 veri şeması" not in metin
    assert "5 akademik bütünlük referansı" not in metin
    assert "19 sütun" not in metin


def test_sema_ajan_referans_sayilari_dogru():
    metin = README.read_text(encoding="utf-8")
    ajan = len(list((REPO_ROOT / "agents").glob("*.md")))
    sema = len(list((REPO_ROOT / "schemas").glob("*.json")))
    referans = len(list((REPO_ROOT / "references").glob("*.md")))
    assert f"{ajan} alt ajan tanımı" in metin, ajan
    assert f"{sema} veri şeması" in metin, sema
    assert f"{referans} akademik bütünlük referansı" in metin, referans


def test_sema_durum_dosyasi_kopyalanmiyor():
    """Bu komut semayi durum dosyasi olarak kopyaliyor ve
    validate_state() 14 eksik zorunlu alanla reddeder."""
    metin = README.read_text(encoding="utf-8")
    assert "cp schemas/thesis_state.json" not in metin


def test_atif_kurallari_yalniz_apa_uyguladigini_soyluyor():
    metin = ATIF.read_text(encoding="utf-8")
    assert "bu dosya yalnız APA" in metin.lower() or \
           "bu dosya yalnız APA 7" in metin


def test_atif_uc_ve_daha_fazla_yazar_kurali_apa_7():
    """'ikinci yazardan sonra et al.' ifadesi APA 6'dir ve
    Yazar1, Yazar2, et al. uretir."""
    metin = ATIF.read_text(encoding="utf-8")
    assert "ikinci yazardan sonra" not in metin
    assert "İlk yazarın soyadı + et al." in metin


def test_arac_stublari_doldurulmus():
    for ad in ["source_search", "source_verify", "pdf_extract", "citation_check"]:
        yol = REPO_ROOT / "tools" / ad / "README.md"
        assert yol.exists(), ad
        metin = yol.read_text(encoding="utf-8")
        assert len(metin) > STUB_ESIGI, f"{ad} hala stub ({len(metin)} karakter)"
```

> `pdf_extract` ve `citation_check` stub'ları da `STUB_ESIGI`'nın
> (267 ve 209 karakter) altında — 5.7'de doldurulmalıdır. 5.9'u da içerir.

- [ ] **5.9** `tools/pdf_extract/README.md` ve `tools/citation_check/README.md` stub'larını doldur:

`tools/pdf_extract/README.md`:
```markdown
# PDF Çıkarma Aracı (Arayüz)

> **Durum: uygulanmadı.** P0-3'teki arayüz sözleşmesi. Bu dosya
> tanım dosyasıdır; `tools/pdf_extract/` altında çalıştırılabilir kod yoktur.

## Görev
Doğrulanmış makalelerden sayfa/bölüm düzeyinde kanıt çıkar.

## Girdi
| Alan | Kaynak |
|------|--------|
| Kaynak | `thesis_state.sources` — `verification.status` = `verified` **ve** `fulltext_available` = `true` |
| Hedef iddia | `thesis_state.claims_registry` — kanıtın hizmet edeceği iddia |

## Çıktı
`evidence.json` kaydı.

```json
{
  "id": "EVD-001",
  "source_id": "SRC-014",
  "text": "Kaynaktan birebir alıntı.",
  "location": { "page": 17, "section": "Results" },
  "supports_claim": "CLM-003",
  "evidence_type": "literature"
}
```

## Kural
Yalnız `verified` ve `fulltext_available: true` kaynaklardan kanıt
çıkarılır. Doğrulanmamış bir kaynaktan alınan metin `evidence` sayılamaz.
```

`tools/citation_check/README.md`:
```markdown
# Atıf Kontrol Aracı (Arayüz)

> **Durum: uygulanmadı.** P0-4'teki arayüz sözleşmesi. Bu dosya
> tanım dosyasıdır; `tools/citation_check/` altında çalıştırılabilir kod yoktur.

## Görev
Atıf–kaynakça bütünlüğünü denetle.

## Kontroller
- Metinde atıf var mı? (`citation.json` → `paragraph_id` hedefi gerçekten var mı)
- Kaynakçada kaynak var mı? (`citation.source_id` → `sources` listesinde mi)
- Kaynak gerçekten var mı? (`verification.status` = `verified` mi)
- Kaynak iddiayı destekliyor mu? (kanıt zinciri kesintisiz mi)

## Girdi
| Alan | Kaynak |
|------|--------|
| Atıflar | `thesis_state.citations` |
| Kaynakça | `thesis_state.sources` |
| Paragraflar | `chapter.json` → `paragraphs` |

## Çıktı
`audit.json` kaydı (`audit_type: "citation"`).

## Dayanak
Bu dört kontrolün dördü de `tools/atw/graph.py` sorgularıyla
hazırlanabilir: `kopuk_baglari()`, `source_kullanan_iddialar()`,
`iddiyanin_dayandigi_kaynaklar()` ve `bulgunun_kanit_zinciri()`.
P0-4 yeni bir grafik katmanı kurmayacak, bu sorguları sarar.
```

- [ ] **5.10** Testleri çalıştır — **kırmızı** olmalı:

```bash
python -m pytest tests/contract_tests/test_docs.py -q -p no:cacheprovider
```

- [ ] **5.11** Testleri tekrar çalıştır — **yeşil** olmalı:

```bash
python -m pytest tests/contract_tests/ -q -p no:cacheprovider
```

- [ ] **5.12** Tüm testler:

```bash
python -m pytest tests/ -q -p no:cacheprovider
```

- [ ] **5.13** Commit:

```
docs: README ve atif kurallarini gercege hizala

S5: belgelerin iddia ettigi sey artik yaptigi sey.

README ozellik listesi
----------------------
12 ozelligin 11'i ✅ isaretliydi, yalniz 4'u gercekten vardi. Simdi
liste iki bolume ayrildi: "Uygulanmis (7)" ve "Planlanmis (6)".

Olcum: README'deki her ✅ isaretinin arkasinda somut bir varlik
olmali ve o varlik arayuz stub'i olmamali. Test tam olarak bunu
denetliyor: UYGULANMIS_YETENEKLER tablosu, README'deki ✅ basliklarla
karsilastirilir ve her birinin dosyasi var olmak zorundadir. Biri
stub'sa test kirmizi olur.

Simdi ✅ isaretli 7 yetenek: Tez Durumu kaliciligi, Paragraf metadata,
Sistematik Inceleme Protokolu, Kalite denetim raporu, Bilgi Grafiği
(Gozlem 4), 4 bilesenli denetim, Orchestrator mimarisi.

Arac stub'lari
--------------
tools/*/README.md dosyalarinin 4'u de arayuz tanimiydi ve hicbiri
uygulama icermiyordu. Tamamlandi:
  source_search   195 -> ~1200 karakter
  source_verify   322 -> ~1100 karakter
  pdf_extract     267 -> ~700 karakter
  citation_check  209 -> ~600 karakter
Hepsi "Durum: uygulanmadi" beyaniyla baslar ve girdi/cikti sozlesmesi
verir. P0-2, P0-3 ve P0-4 bu sozlesmeleri uygulayacak.

source_verify/README.md ayrica iki sabiti belgeledi:
  ESIK_ESLESME = 0.60, EN_AZ_BAGIMSIZ_KAYNAK = 2
ve su siniri yazdi: search_run.database enum'unda 8 veritabani var
(kesif), verification.verification_sources yalniz 4 deger kabul eder
(crossref, openalex, semantic_scholar, manual). PubMed, Scopus, Web of
Science ve Google Scholar kesif icindir, dogrulama kaynagi degildir.

Sayimlar
--------
  257, 277, 290  8 ajan      -> 10 ajan
  280            7 veri semasi -> 21
  281            5 referans    -> 7
  253            19 sutun      -> 18 (templates/literature_matrix.md
                                 baslik satiri 18 sutun)

Gecersiz baslangic komutu
-------------------------
README "cp schemas/thesis_state.json thesis_state.json" diyordu.
Bu SEMAYI durum dosyasi olarak kopyaliyor; validate_state() bunu 14
eksik zorunlu alanla reddeder. Kullanicinin ilk calistirmasi hata
verirdi. empty_state() ureten komutla degistirildi.

citation_rules.md
-----------------
"Desteklenen Atif Stilleri" 5 stil listiyordu (satir 10-14) ama
satir 27-40'taki tum ornekler ve "Ozel Durumlar" bolumu yalniz APA'ydi.
Baslik "Atif Stilleri" olarak degistirildi ve "bu dosya yalniz APA 7
uygular" beyani eklendi; listelenen ama kurali olmayan stiller acikca
isaretlendi.

Ayrica satir 54'teki "3+ yazar: APA'da ikinci yazardan sonra et al."
ifadesi APA 6 kuralidir ve "Yazar1, Yazar2, et al." uretir. APA 7'de
ilk yazarin soyadi + et al. kullanilir, ilk atiftan itibaren.
Test her iki ifadeyi de yokluyor.
```

---

## Görev 6 — Kapanış: coverage ölçümü ve son kabul

**Amaç:** Coverage hedefini **ölçerek** belirlemek ve spec'in kabul kriterlerini tek tek doğrulamak.

- [ ] **6.1** Coverage'ı ölç (henüz `fail_under` **koyma**):

```bash
python -m pytest tests/ -q -p no:cacheprovider --cov=tools.atw --cov-report=term-missing
```

- [ ] **6.2** Sonucu **kullanıcıya sun** ve `fail_under` değerini birlikte kararla. Ölçülen değerden **düşük** bir eşik seç — mevcut kapsamın hemen altı, böylece yeni kod düşürürse test yakalar, mevcut kod kabul edilir:

```bash
# Örnek: ölçüm %87 ise fail_under=85 yazılır
python -m pytest tests/ -q -p no:cacheprovider --cov=tools.atw --cov-fail-under=85
```

- [ ] **6.3** `pytest.ini`'ye ekle:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -q --strict-markers --cov=tools.atw --cov-fail-under=85 --cov-report=term-missing
markers =
    live: Canli ag cagrisi gerektiren test
```

- [ ] **6.4** Spec'in **18 kabul kriterini** tek tek doğrula ve sonuçları tabloya yaz:

```bash
python -m pytest tests/ -p no:cacheprovider
```

| # | Kriter | Nasıl doğrulanır |
|---|---|---|
| 1 | 0 başarısız, 0 hata | `python -m pytest tests/ -p no:cacheprovider` |
| 2 | 21 şema geçerli, `$id` GitHub'a bakıyor | `test_tum_semalar_draft_2020_12_uyumlu`, `test_her_semanin_id_alani_var` |
| 3 | 21 kayıt şemasında örnek veya `$comment` | `test_yeni_semada_ornek_ve_yorum_var` + mevcut eşdeğer |
| 4 | S1 sözleşme testi `SKILL.md` + 10 ajanı geçirir | `tests/contract_tests/test_agent_schema_agreement.py` |
| 4a | Kırmızı çıktı ölçülmüş tabloyla aynı | Görev 1, adım 1.3 commit mesajında |
| 4b | 4 fence'siz blok fence'e alındı, test buluyor | `test_json_blogu_semaya_uyar` parametreleri |
| 5 | `CH-001`/`VAR-001` üretilebiliyor, 20 önek | `test_ch_ve_var_onleri_uretilebiliyor`, `test_id_prefixes_yirmi_on_tane` |
| 6 | `kenar_tablosu()` iki yönlü kapsıyor | `test_tablodaki_her_alan_semada_var`, `test_semadaki_her_referans_alani_tabloda` |
| 7 | Sahte `EVD-999` kopuk bildiriliyor | `test_coklu_alan_kopugu_bulunuyor` |
| 8 | `audit_registry` denetleniyor | `test_audit_kayitlari_denetleniyor` |
| 9 | `find_dangling_references()` geriye uyumlu | `test_sarmalayici_geriye_uyumlu` + mevcut 2 test |
| 10 | Python 3.9+ uyumlu | `test_arac_kodu_uc_dokuzda_ayristiriliyor` |
| 11 | Bozuk `date-time` reddediliyor, iki tarih biçimi doğru | `test_format_checker.py` — 8 test |
| 12 | README 10 ajan / 21 şema / 7 referans / 18 sütun; uygulanmamış ✅ değil | `tests/contract_tests/test_docs.py` |
| 13 | README şemayı durum dosyası olarak kopyalamıyor | `test_sema_durum_dosyasi_kopyalanmiyor` |
| 14 | `citation_rules.md` yalnız APA'yı söylüyor, APA 7 kuralı doğru | `test_atif_kurallari_yalniz_apa_uyguladigini_soyluyor`, `test_atif_uc_ve_daha_fazla_yazar_kurali_apa_7` |
| 15 | `chapter` alanları `^CH-` deseni taşıyor | `test_chapter_alanlari_kimlik_biciminde` |
| 16 | Çalışma ağacı temiz, her dilim ayrı commit | `git status`, `git log` |

- [ ] **6.5** `sorun.md` dosyasını commit **etme** (kullanıcının dosyası):

```bash
git status --short   # ?? sorun.md  beklenir
```

- [ ] **6.6** Son commit:

```
chore: coverage esigi ve kabul kriteri dogrulamasi

Coverage olculdu: %<olcum>. Esik <olcum - 2> olarak konuldu - mevcut
kapsamin hemen alti. Boylece yeni kod dusururse test yakalar, mevcut
kod kabul edilir.

fail_under degeri birlikte belirlendi: once olculdu, sonra karar
verildi. Tahminle esik konmadi.

Kabul kriterleri
---------------
18 kriterin 18'i dogrulandi. Tam liste Gozlem 6 adim 4'teki tabloda.
Test sayisi: <onceki> -> <simdiki>
Sema sayisi: 18 -> 21
ID_PREFIXES: 18 -> 20 onek
Kapsanan referans alani: 6/53 -> 59/59 (Gozlem 2 sonrasi)

Not: ilk .opencode senkronu P0-5'te kalir (D7). 38 dosya eksik.
```

- [ ] **6.7** Push:

```bash
git push
```

---

## Ek: Görev Bağımlılık Sırası

```
Görev 1 (S1 sözleşme + belge onarımı)
   │  fulltext_available şemaya eklenir
   │  writer.md "chapter" -> "CH-002"
   ▼
Görev 2 (S2 şema delikleri)
   │  3 yeni şema, ^CH- desenleri, date-time formatları
   │  kapsanan referans alanı 53 -> 59
   ▼
Görev 3 (S3 dayanıklılık)
   │  FormatChecker bağlanır → Görev 2'deki format kısıtları zorlanır
   │  f-string'ler düzeltilir → 3.9 uyumlu
   ▼
Görev 4 (S4 kanıt grafiği)
   │  59 referans alanının tamamı kapsanır
   │  find_dangling_references() yönlendirilir
   ▼
Görev 5 (S5 doküman gerçekliği)
   │  4 araç stub'ı doldurulur
   │  README + citation_rules gerçeğe hizalanır
   ▼
Görev 6 (kapanış)
      coverage ölçülür, fail_under birlikte konur
      18 kabul kriteri doğrulanır
```

**Zorunlu sıra gerekçeleri:**

- **1 → 2:** Görev 1'in yeşil durumu Görev 2'nin şema kısıtlarına dayanır. `fulltext_available` S1'de eklenmezse S1 yeşile dönemez; `writer.md`'nin `"chapter": "2"` değeri düzeltilmezse Görev 2'de kırılır.
- **2 → 3:** `format` kısıtları Görev 2'de eklenir ama `FormatChecker` bağlanmadan zorlanmaz. Kısıt ve zorlama aynı anda eklenirse test kırmızı çıkıp neden kaybolur.
- **3 → 4:** `find_dangling_references()` yönlendirmesi `graph.py`'ye bağımlıdır; modül olmadan sarmalayıcı yazılamaz. Bu adım Görev 3'ten Görev 4'e taşındı.
- **5 → 1 (çapraz):** `citation_rules.md` düzeltmesi S1'in tarama kapsamı dışındadır (referans dosyası, ajan belgesi değil). Yine de S5, S1'den sonra yapılır: `tools/*/README.md` stub'larının dolması `test_docs.py`'nin ön koşuludur ve o test S1'in parçası değildir.
