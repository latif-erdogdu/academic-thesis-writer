# Sertleştirme ve Bütünlük Onarımı — Tasarım

**Tarih:** 2026-09-26
**Durum:** Tasarım onaylandı, uygulama planı bekliyor
**Kapsam:** P0-2 (Kaynak Doğrulama Motoru) öncesi sertleştirme
**İlgili plan:** `docs/superpowers/plans/2026-09-26-p0-1-core-data-model.md` (tamamlandı, 65/65 adım)

---

## 1. Özet

P0-1 bir veri modeli ve şema katmanı kurdu: 18 JSON Şeması, 10 ajan belgesi, 7 referans
dosyası, 226 test. P0-2'ye geçmeden önce bu katmanın **kendisinin** taşıdığı üç
gerçek eksik kapatılacak:

1. **Sözleşme bütünlüğü yok.** 10 ajan belgesi ve `SKILL.md`, şemaya karşı hiç
   doğrulanmıyor. Doğrulandığında 4 belge geçersiz çıktı — bunlardan biri
   (`SKILL.md`) skill'in giriş noktası ve **geçersiz durum dosyası üretmeyi öğretiyor**.
2. **Şemada iki doğrulama deliği var.** `chapters` ve `variables`, içi boş
   `{"type": "object"}` tanımlarıyla geçiyor — istendiği her şey doğruluyor. `hypotheses`
   ise 15 kardeş `$ref` kullanırken elle gömülü.
3. **Var olan bütünlük denetimi fiilen çalışmıyor.** `find_dangling_references()`
   18 şemadaki 69 kimlik referansı alanının **5'ini** denetliyor. Kopuk bir
   `claim.evidence_ids` sessizce geçiyor.

Ayrıca dokümantasyon gerçekliği (F5, F6, F7, F8), çalışma zamanı dayanıklılığı
(F13, F14) ve kapsam ölçümü (F17) ele alınacak.

**Bu spec bir araç katmanı değildir.** `source_search`, `source_verify`,
`pdf_extract`, `citation_check` P0-2…P0-5'te kalır; bu spec onların üzerine
oturacak zemini hazırlar.

---

## 2. Bağlam

### 2.1 Doğrulanmış bulgular

Aşağıdaki tablo, `sorun.md` ve bu oturumda tespit edilen iddiaların **kod ve
şema üzerinde doğrulanmış** hâlidir. "Kanıt" sütunu her satırın nasıl
doğrulandığını gösterir.

| # | Bulgu | Kanıt | Etki |
|---|---|---|---|
| F1 | `source-verifier.md` `## Çıktı` bloğu geçersiz | `Draft202012Validator(source.json)` → 5 hata: `metadata_match` ve `fulltext_available` şemada yok; `verification` içeriği kök düzeyde yazılmış; `status` pipe-birleştirilmiş string | Ajan geçersiz kayıt yazar |
| F2 | `gap-analyzer.md` alan adları şemayla uyumsuz | `gap_id`→`id`, `description`→`statement`, `evidence`→`evidence_ids`; 5 alanın 3'ü yanlış | Ajan geçersiz kayıt yazar |
| F3 | `contradiction-analyzer.md` `statistic.json → power` diyor | `statistic.json` 20 alan; `power` yok | Ajan var olmayan alanı okur |
| F4 | `SKILL.md:242-270` "Minimum veri" örneği geçersiz | `Draft202012Validator(thesis_state.json)` → 12 hata: `claims` şemada yok (`claims_registry` var), 11 zorunlu alan eksik | **Skill'in giriş noktası geçersiz durum dosyası üretiyor** |
| F5 | `citation_rules.md:54` APA kuralı hatalı | "3+ yazar: ikinci yazardan sonra et al." → `Yazar1, Yazar2, et al.` üretir. APA 7: ilk yazarın soyadı + et al., ilk atıftan itibaren | Ajanlar hatalı atıf üretir |
| F6 | `README.md` 8 ajan diyor | 8 ajan ifadesi satır 257, 277, 290; `agents/` altında 10 dosya | Belgeler tutarsız |
| F7 | `README.md:248-251` uygulanmamış özellikleri ✅ işaretliyor | Kaynak doğrulama motoru, PDF→kanıt, boşluk motoru, bilgi grafiği — dördü de belge + boş stub | Yanlış yetenek izlenimi |
| F8 | P0 tasarım spec'i `evidence_type` listesi sürüklenmiş | Spec `:291` 5 değer (`data`); kod 6 (`primary_data`, `literature` ek). Spec `:107` zaten `[GÜNCELLEME]` işaretlemiş, işaretlenmemiş | Tekrar eden sapma kaynağı |
| F9 | `chapters` doğrulama deliği | `items: {"type": "object"}` — `properties`/`required` yok | Herhangi bir nesne geçer |
| F10 | `variables` doğrulama deliği | `items: {"type": "object"}` — `properties`/`required` yok. `consistency-auditor.md:11` ve `methodology_rules.md:33` bu alanı okuyor | Herhangi bir nesne geçer |
| F11 | `hypotheses` elle gömülü | 15 kardeş alan `$ref` kullanırken `hypotheses` tam tanımlı inline | Tutarsızlık, ajan dosya yolu gösteremiyor |
| F12 | Tarih alanlarında `format` yok | `created_at`, `updated_at` çıplak `string`; `source.access_date` de formatsız | Tarih doğrulanmıyor |
| F13 | Python 3.12 tabanı zorunlu, beyan edilmemiş | `state.py:249-269` içinde 10 PEP 701 f-string (`f"...{sayi("x")}..."`); `requirements.txt` Python tabanı belirtmiyor | Python 3.11'de **paketin tamamı** `SyntaxError` |
| F14 | `FormatChecker` bağlı değil | `state.py:93` `Draft202012Validator(...)` → `format_checker` yok | `search_run.timestamp` `format: date-time` taşıyor ama zorunlu değil |
| F15 | `find_dangling_references()` kapsamı %7 (S2 öncesi ölçüm) | 18 şemada 69 kimlik referansı alanı; fonksiyon (`state.py:166`) yalnız `f"{ad}_id"` arıyor, 15 isim denetliyor, bu isimlerden şemalarda yalnız 5'i var (`source_id`×2, `dataset_id`, `finding_id`, `analysis_id`, `audit_id`) | **Kopuk bağlar sessizce geçiyor** |
| F16 | `fulltext_available` şemada yok | `source.json` 32 alan; yok. `source-verifier.md:43` yazıyor | P0-3'ün üreteceği bilginin yeri yok |
| F17 | Coverage hedefi yok | `pytest-cov` `requirements.txt`'te, `pytest.ini`'de `fail_under` yok | Regresyon ölçümü yok |

### 2.2 `sorun.md` için düzeltmeler

Bu spec, `sorun.md`'yi harfi harfine uygulamaz. İki iddia yanlıştır ve biri
yıkıcı olurdu.

**`sorun.md` #1 — "P0-CRITICAL: `thesis_state.json` hâlâ eski V1 modeli, gerçek
JSON Schema header'ı ve yapısal validation kuralları yok." → YANLIŞ.**

Doğrulanan durum:

- `schemas/thesis_state.json` `draft/2020-12`, `$id` GitHub'a bakıyor, 39 üst düzey
  alan, 14 zorunlu, `additionalProperties: false`.
- `tools/atw/state.py:92` bir `Draft202012Validator` kuruyor; `validate_state()`
  ve `validate_prisma_flow()` çalışıyor.

"Eski V1 alanları"nın durumu:

| Katman | `$ref`'lediği şemalar |
|---|---|
| Betimleyici (V1 izinden) | `research_question`, `source`, `citation` |
| Kanıt zinciri (P0-1'in eklediği) | `claim`, `evidence`, `finding`, `discussion`, `conclusion`, `research_gap`, `audit`, `search_run`, `analysis`, `dataset`, `statistic`, `table`, `figure` |

**Kesişim boş.** Bu iki katman tasarım gereği ayrık: biri tezenin betimleyici
yüzünü, diğeri kanıt izini taşır. `sorun.md`'nin ima ettiği düzeltme (V1
alanlarını temizleme) `state.py`'nin 13 alanını ve **10 ajanın 9'unu** kırardı.

Sonuç olarak #1'in altında bir şey yok; onun yerine F9, F10, F11, F12 vardır —
gerçek delikler, ama tamamen farklı bir sebepten.

**`sorun.md` #10 — "Nitel araştırmada olasılıksal örnekleme uygulanıyor." → YANLIŞ ALARM.**

`references/methodology_rules.md:36` (`| 6 | Olasılık örneklemesi mi? | ...`) satırı
`## Ölçek A — Nicel Yöntemler` başlığının (satır 17) altındadır. Dosyanın ayrı bir
`## Ölçek B — Nitel Yöntemler` ölçeği (satır 54) ve kendi denetim tablosu vardır.
Kapsam doğru yazılmıştır; değiştirilecek bir şey yok.

### 2.3 P0-1'den kalan ve burada ele alınan konu

P0-1'in Task 5'inde "zincirin bütünlüğünü uçtan uca doğrula" adımı
`validate_prisma_flow()` ve `find_dangling_references()` ile karşılanmıştı. F15,
ikinci fonksiyonun bu karşılığı **olmadığını** gösteriyor. Bu spec onu düzeltir.

---

## 3. Kapsam

### 3.1 Kapsam içi

- 4 belgenin şemaya karşı doğrulanması ve onarılması (F1, F2, F3, F4)
- `chapter.json`, `variable.json`, `hypothesis.json` (F9, F10, F11)
- `fulltext_available` alanı (F16)
- Tarih `format` zorlaması (F12, F14)
- Python sürüm bağımlılığının kaldırılması (F13)
- Tüm referans alanlarını kapsayan, şemadan türetilen kenar tablosu (F15)
- Kanıt grafiği sorgu katmanı (§4, D4)
- Dokümantasyon gerçekliği (F5, F6, F7, F8)
- Sözleşme testi (§5, S1)

### 3.2 Kapsam dışı (bilinçli)

| Konu | Neden dışarıda |
|---|---|
| `source_search`, `source_verify` | P0-2 |
| `pdf_extract` | P0-3 |
| `citation_check`, `tools/atw/approval.py` | P0-4 |
| `.opencode/` senkronu | P0-5 |
| `methodology` nesnesini şemaya çıkarmak | 6 alanı var, `additionalProperties: false`, sıkıntısı yok; kazanç yok |
| Grafik materyalizasyonu (ayrı depo) | `thesis_state.json` tek doğruluk kaynağı kalmalı |
| Coverage hedefi sayısı | Önce ölçülür, sonra kararlaştırılır (§10) |
| APA dışı atıf stilleri (MLA/Chicago/IEEE/Harvard) | `citation_rules.md` tek bir stili kapsıyor; genişletme ayrı iş |

---

## 4. Mimari kararlar

| # | Karar | Gerekçe |
|---|---|---|
| D1 | **Sözleşme testi ilk dilim.** | F1–F4'ün *sebebi* belirsiz: belge mi yanlış, şema mı eksik, araç mı yok? Sıralamayı bu bilgi belirliyor; belirsizlik varken sıra seçmek tahmindir. |
| D2 | **Şema kazanır, belge düzeltilir.** Tek istisna: belge şemada gerçekten eksik bir kavram adlandırıyorsa şema genişler. | 18 şema 226 test ile doğrulanıyor; 10 belge hiç doğrulanmıyordu. Doğrulanmış taraf kazanmalı. |
| D3 | **`fulltext_available` → `source.json` üst düzey, nullable boolean.** | P0-3 üretir, P0-2 doldurmaz ve `null` bırakır. Ajanın belgelediği bilgi şemada yaşar; `additionalProperties: false` yüzünden reddedilmez. |
| D4 | **Kanıt grafiği = sorgu katmanı.** Kenar tablosu **şemadan türetilir**, elle yazılmaz. | Yeni şema eklendiğinde denetici kendiliğinden genişler; tutmama riski ortadan kalkar. |
| D5 | **`hypothesis.json` mevcut inline tanımı birebir taşır.** | Kanıtsız alan eklemek, alan/şema sözleşmesini sezgisel kılar. |
| D6 | **`find_dangling_references()` `state.py`'de geriye uyumlu sarmalayıcı olarak kalır.** | 2 mevcut test kırılmaz; çağıran ajanlar etkilenmez. |
| D7 | **`.opencode` senkronu P0-5'te.** | 38 dosya eksik; P0-2…P0-4 bu alanı büyütecek, erken senkronizasyon yinelenir. |

---

## 5. Dilimler

### S1 — Sözleşme testi

**Amaç:** Belge–şema sapmalarını mekanik olarak yakalamak.

**Yeni dosya:** `tests/contract_tests/test_agent_schema_agreement.py`

**Denetlenen üç sınıf:**

1. **Gömülü JSON örnekleri.** Her ajan `.md` dosyasındaki ve `SKILL.md`'deki
   ```json blokları, metinde adı geçen şemaya karşı `Draft202012Validator` ile
   doğrulanır.
2. **Alan referansları.** Belgedeki `şema.json → alan` ve `` `alan` `` biçimindeki
   atıfların hedef alanı şemada var mı kontrol edilir. Enum *değerleri* de
   doğrulanır.
3. **Kimlik önekleri.** Belgede geçen `XX-XXX` kalıpları `ID_PREFIXES`'te var mı
   kontrol edilir.

**Uygulama sırası:** Test önce yazılır ve **kırmızı doğrulanır**. F1 (5 hata) ve
F2 (3 hata) kırmızı çıkmalıdır. Test yeşile dönmeden S2'ye geçilmez.

**Onarım (D2 kuralıyla):**

| Dosya | Sapma | Karar |
|---|---|---|
| `source-verifier.md` | `metadata_match` | **Kes** — `bibliographic_match` zaten karşılıyor |
| `source-verifier.md` | `fulltext_available` | **Şemaya ekle** (D3) |
| `source-verifier.md` | `verification` kök düzeyde | **İç içe al** — `verification` nesnesinin içeriği |
| `source-verifier.md` | `status: "verified\|unverified\|pending"` | **5 enum değerinin tamamı** |
| `gap-analyzer.md` | `gap_id`, `description`, `evidence` | **Alan adlarını düzelt** |
| `contradiction-analyzer.md` | `statistic.json → power` | **Gerçek alanlar:** `n`, `effect_size`, `p_value` |
| `SKILL.md` | 12 hata | **`empty_state()` çıktısıyla değiştir** |

**`SKILL.md` için özel kural:** Örnek elle yazılmaz. `tools/atw/state.py:95`
`empty_state()` tam olarak bu kaydı üretir; `SKILL.md` bu fonksiyonun gerçek
çıktısını gösterir. Böylece şema değişirse örnek değişir — sürüklenme imkânı
ortadan kalkar.

**Kabul kriteri:** `python -m pytest tests/contract_tests/ -q` yeşil. Doğrulama
sırası zorunludur ve kayda geçirilir:

1. Test yazılır, belgeler **onarılmadan önce** çalıştırılır.
2. F1 ve F2 için **kırmızı** olduğu gözlenir ve çıktı commit mesajına yazılır.
3. Belgeler onarılır.
4. Test **yeşil** olur.

Bu sıra tersine çevrilirse testin gerçekten sürüklemeyi yakaladığı
kanıtlanmamış olur — kabul kriteri bu nedenle iki aşamalıdır.

---

### S2 — Şema onarımı

**Yeni şemalar (18 → 21):**

#### `chapter.json`

Kanıt: `agents/citation-auditor.md:10` — *"Paragraflar | `thesis_state.chapters`
içindeki `paragraph.json` kayıtları"*

| Alan | Tip | Zorunlu |
|---|---|---|
| `id` | `^CH-\d{3,}$` | ✓ |
| `number` | `integer`, `minimum: 1` | ✓ |
| `title` | `string`, `minLength: 1` | ✓ |
| `goal` | `string` | — |
| `paragraphs` | `array` of `$ref: paragraph.json` | — |

P0 tasarım spec'indeki `chapter_order` **buraya girmez** — doğrulandı, o
`university_overrides` içindeki biçimlendirici ayarıdır, tez durumu değildir.

#### `variable.json`

Kanıt: `references/methodology_rules.md:33` (*"Her değişken operasyonelleştirilmiş
mi? ... 'Başarı' değişkeni nasıl ölçüldüğü yok"*), `agents/consistency-auditor.md:11`

| Alan | Tip | Zorunlu |
|---|---|---|
| `id` | `^VAR-\d{3,}$` | ✓ |
| `name` | `string`, `minLength: 1` | ✓ |
| `definition` | `string` | — |
| `operationalization` | `string`, `minLength: 1` | **✓** |
| `measurement_scale` | `nominal`, `ordinal`, `interval`, `ratio`, `none` | — |
| `value_type` | `numeric`, `categorical`, `temporal`, `boolean`, `text` | — |
| `dataset_ids` | `array` of `^DS-\d{3,}$` | — |
| `claim_ids` | `array` of `^CLM-\d{3,}$` | — |

`operationalization` zorunludur: bu, `methodology_rules.md`'nin 3 numaralı
denetimini şema seviyesine indirir. "Değişken nasıl ölçüldü" artık ajan
isteğine bırakılmaz.

#### `hypothesis.json`

`thesis_state.json`'daki inline tanımın **birebir** kopyası (D5):

| Alan | Tip | Zorunlu |
|---|---|---|
| `id` | `^HYP-\d{3,}$` | ✓ |
| `text` | `string`, `minLength: 1` | ✓ |
| `status` | `supported`, `rejected`, `pending` | ✓ |
| `related_research_questions` | `array` of `^RQ-\d{3,}$` | — |
| `finding_ids` | `array` of `^FND-\d{3,}$` | — |

Bu şema `additionalProperties: false` ile yazılır (18 kayıt şemasıyla tutarlı;
mevcut inline tanımda bu kısıt yoktu — kasıtlı sıkılaştırma). Uygulamada
mevcut fixture ve test verisinde fazla alan varsa S2 kapsamında uyumlanır.

**`thesis_state.json` değişiklikleri:**

- `chapters`, `variables`, `hypotheses` → `$ref` ile bağlanır
- `created_at`, `updated_at` → `format: date-time`
- `source.json` → `fulltext_available` (`["boolean","null"]`, `default: null`)

**`access_date` için ayrı karar:** `source.access_date` 4 fixture'da
`2026-09-26` biçiminde **yalnız tarih**. `format: date-time` eklensydi bu 4
fixture kırılırdı. **`format: date` eklenir** — bu değerler `date` olarak geçerli.

**`ID_PREFIXES` genişletmesi:** `CH: "chapter"`, `VAR: "variable"`. 18 önekten
20'ye çıkar. `HYP` zaten var.

**Kabul kriteri:** 21 şema geçerli; `CH-001` / `VAR-001` üretilebiliyor; eski 226
test yeşil.

---

### S3 — Çalışma zamanı dayanıklılığı

| # | Değişiklik | Gerekçe |
|---|---|---|
| 1 | `state.py:249-269` içindeki 10 f-string'in tırnağı değiştirilir | PEP 701 iç içe tırnak yalnız 3.12+'da geçerli. Tırnak değiştirince 3.9+ uyumlu olur. |
| 2 | `Draft202012Validator(..., format_checker=FormatChecker())` | `format` anahtarı şu anda sessizce yok sayılıyor |
| 3 | `fulltext_available` → `source.json` | D3 |
| 4 | `CH`, `VAR` → `ID_PREFIXES` | S2 ön koşulu |
| 5 | Python tabanı beyanı | `requirements.txt` bunu ifade edemez; README'de açık taban belirtilir |
| 6 | Coverage ölçümü | `pytest-cov` ile gerçek oran ölçülür, sonra §10 |

**Değişiklik 2'nin güvenlik ölçümü (yapıldı):**

- Şemaların tamamında `format` anahtarı taşıyan alan sayısı: **1**
  (`search_run.timestamp`)
- 7 fixture'ın hiçbirinde bu alanın geçişi: **0**
- `schemas/search_run.json` örnek kaydının `timestamp` değeri:
  `2026-09-26T09:00:00+00:00` → geçerli

`FormatChecker` bağlanması hiçbir mevcut veriyi kırmaz.

**Kabul kriteri:** Tüm testler yeşil; `python -c "import tools.atw.state"` 3.9+
sözdizimiyle uyumlu (f-string taraması boş döner); bir `search_run.timestamp`
alanına `"2026-09-26"` yazıldığında doğrulama hata verir.

---

### S4 — Kanıt grafiği

**Problem (F15):** `find_dangling_references()` (`state.py:149-179`) kayıtlar
arası `<ad>_id` alanlarını arar. 18 şemada 69 kimlik referansı alanı var;
fonksiyonun aradığı 15 isimden yalnız 5'i şemalarda gerçekten bulunuyor:

| Denetlenen ad | Gerçekten var mı | Nerede |
|---|---|---|
| `source_id` | ✓ | `citation.source_id`, `evidence.source_id` |
| `dataset_id` | ✓ | `analysis.dataset_id` |
| `finding_id` | ✓ | `statistic.finding_id` |
| `analysis_id` | ✓ | `statistic.analysis_id` |
| `audit_id` | ✓ | `audit.audit_id` |

**Denetlenmeyen 63 alan** içinde: tüm çoğul `<ad>_ids` alanları
(`claim.evidence_ids`, `finding.evidence_ids`, `search_run.included_source_ids`,
`research_gap.evidence_ids`, `source.evidence_ids`, `conclusion.finding_ids`,
`table.statistic_ids`, …) ve tüm özel adlandırılmış bağlar
(`evidence.supports_claim`, `claim.contradicted_by`, `claim.counter_claims`,
`discussion.agrees_with` / `disagrees_with`, `research_question.answered_by`,
`paragraph.claims` / `evidence` / `citations` / `sources`,
`figure.original_source_id`, `source.supersedes_source_id`).

**Çözüm (D4):** Kenar tablosu **elle yazılmaz, şemadan türetilir.**

```
schemas/*.json  ∪  ID_PREFIXES  ──►  KenarTablosu
```

Her alanın `pattern` değeri öneki verir (`^EVD-\d{3,}$` → `EVD`),
`ID_PREFIXES` öneği varlık adına çevirir (`EVD` → `evidence`). 69 alanın
tamamı önek deseni taşıdığı doğrulandı; kenar kümesi tamamen hesaplanabilir.
Yeni şema eklendiğinde denetici kendiliğinden genişler.

**Kenar türleri ikili ayrılır:**

| Tür | Örnek | Sorduğu soru |
|---|---|---|
| **yapısal** | `finding.evidence_ids`, `paragraph.claims`, `evidence.source_id` | "bu kayıt nereye bağlı?" |
| **anlamsal** | `claim.contradicted_by`, `discussion.agrees_with`, `source.supersedes_source_id`, `source.supports_claims` | "bu kayıt neyi destekliyor / çürütüyor?" |

Ayrım işlevseldir: `retraksiyona_ugrayan_iddialar` yapısal kenardan,
`celiskili_iddialar` anlamsal kenardan yürür. Bu yüzden yürüyüş
fonksiyonları `tur` parametresi alır.

**Yeni dosya:** `tools/atw/graph.py`

```
Kenar          = (kayit_tipi, alan_adi, hedef_tipi, coklu_mu, tur)
kenar_tablosu()                  -> list[Kenar]        # şemalardan türetilir, önbellekli
kopuk_baglari(state)             -> list[str]          # tüm referans alanları
source_kullanan_iddialar(state, source_id)  -> list[str]
iddiyanin_dayandigi_kaynaklar(state, claim_id) -> list[str]
bulgunun_kanit_zinciri(state, finding_id)     -> Zincir
rq_dan_kaynakca(state, rq_id)                 -> Zincir
retraksiyona_ugrayan_iddialar(state)          -> list[str]
kanitsiz_iddialar(state)                      -> list[str]
celiskili_iddialar(state)                     -> list[str]   # anlamsal kenardan
```

`Zincir`, adım listesi taşıyan sade bir veri sınıfıdır
(`adim, kimlik, tur` üçlüleri) — metin biçimlendirme bu katmanın işi değildir;
`README.md:251`'in vaat ettiği iki zinciri adım listesi olarak verir.

**D6:** `state.py:find_dangling_references()` `graph.kopuk_baglari(state)`'a
yönlendiren ince bir sarmalayıcı olur. Mevcut 2 test kırılmaz.

**Kabul kriteri:** `kenar_tablosu()` şemalardaki **her** kimlik referansı alanını
kapsar ve test bunu iki yönlü doğrular — tabloda olan her alan şemada vardır,
şemada olan her alan tablodadır. `claim.evidence_ids` içine sahte `EVD-999`
konunca kopuk bildirilir; mevcut 2 test yeşil kalır.

> **Sayı sabitlenmez.** 69 sayısı S2 **öncesi** ölçümdür ve yalnız teşhis
> amacıyla burada geçer. S2 `chapter.paragraphs`, `variable.dataset_ids` ve
> `variable.claim_ids` alanlarını eklediği için toplam **72'ye** çıkar. Bu
> yüzden test sabit bir sayıyla değil, **şemadan türetilen sayıyla** karşılaştırır;
> yeni şema eklendiğinde kabul kriteri kendiliğinden geçerli kalır.

---

### S5 — Dokümantasyon gerçekliği

| Dosya | Değişiklik |
|---|---|
| `README.md:257, 277, 290` | 8 → 10 ajan |
| `README.md:248-251` | 4 uygulanmamış özelliğin ✅ işareti kaldırılır; P0-2…P0-5'e bağlı olarak işaretlenir |
| `citation_rules.md:54` | "3+ yazar: **ilk yazarın soyadı + et al.**, ilk atıftan itibaren" (APA 7) |
| `citation_rules.md:46` | "3+ yazar" ifadesi APA 7 ile tutarlı hâle getirilir |
| `contradiction-analyzer.md` | `statistic.json → power` → `n`, `effect_size`, `p_value` |
| P0 tasarım spec `:291` | `evidence_type` 5 → 6 değer (`data` → `primary_data`, `literature` ek) |
| P0 tasarım spec `:107` | `[GÜNCELLEME]` işareti kalkar |
| `SKILL.md:242-270` | `empty_state()` çıktısıyla değiştirilir (S1 ile aynı iş) |
| Yeni: alan taksonomisi | `README.md`'ye veya `references/` altına betimleyici katman / kanıt zinciri katmanı ayrımının açıklaması |
| `.opencode/` | **P0-5'te kalır** (D7) |

**Kabul kriteri:** S1'in sözleşme testi `SKILL.md` ve 10 ajan belgesini geçirir;
`README.md`'de hiçbir uygulanmamış özellik ✅ işaretli değildir.

---

## 6. Test stratejisi

| Test modülü | Kapsam |
|---|---|
| `tests/contract_tests/` | S1 — belge/şema sözleşmesi (yeni) |
| `tests/schema_tests/` | S2 — 21 şema, `CH-`/`VAR-` kimlikleri, tarih biçimleri |
| `tests/schema_tests/` | S3 — `FormatChecker` bağlı; bozuk tarih reddediliyor |
| `tests/unit_tests/test_graph.py` | S4 — kenar tablosu türetimi, kopuk bağ, 6 sorgu |
| `tests/integration_tests/` | S5 + bütünlük — 21 şema, 10 ajan, 7 referans senkron |

**Ağ bağımlılığı yok.** Bu spec'in hiçbir testi ağ çağrısı yapmaz. `pytest.ini`'de
tanımlı `live` marker'ı P0-2'nin konusudur; `test_gercek_ag_cagrisi_yapilmiyor`
P0-2'de `live` işaretli test eklendiğinde devreye girecek ve `addopts`'a
`-m "not live"` eklenmesini zorunlu kılacak.

**Test-first:** S1 dışındaki her dilimde önce yazılan test kırmızı doğrulanır,
sonra düzeltme yapılır. S1'de de kırmızı doğrulama zorunlud (§5, S1).

---

## 7. Kabul kriterleri

Tümü sağlanmadan spec tamamlanmış sayılmaz.

1. `python -m pytest tests/ -p no:cacheprovider` → 0 başarısız, 0 hata
2. 21 şema `Draft202012Validator` ile geçerli; her birinin `$id`'si GitHub'a bakıyor
3. 21 kayıt şemasında örnek ve/veya `$comment` mevcut
4. S1'in sözleşme testi `SKILL.md` + 10 ajan belgesini geçirir
5. `CH-001` ve `VAR-001` üretilebiliyor; `ID_PREFIXES` 20 önek
6. `graph.kenar_tablosu()` şemalardaki her kimlik referansı alanını kapsıyor
   (iki yönlü doğrulama: tablo ⊆ şema ve şema ⊆ tablo)
7. `claim.evidence_ids` içine sahte kimlik konunca kopuk bağ bildiriliyor
8. `find_dangling_references()` geriye uyumlu — mevcut 2 test yeşil
9. Python 3.9+ uyumlu: f-string taraması iç içe tırnak bulamıyor
10. Bozuk `date-time` reddediliyor (`FormatChecker`)
11. `README.md` 10 ajan diyor; uygulanmamış hiçbir özellik ✅ değil
12. `citation_rules.md` APA 7 kuralını doğru ifade ediyor
13. Çalışma ağacı temiz; her dilim ayrı commit; her sapma commit mesajında kayıtlı

---

## 8. Riskler

| Risk | Etki | Azaltma |
|---|---|---|
| `hypothesis.json`'a `additionalProperties: false` eklenmesi mevcut veriyi kırar | S2'de test kırılması | S2 uygulamasında önce fixture taranır; fazla alan varsa S2 kapsamında uyumlanır |
| S1 kırmızı çıkmaz (test yanlış yazıldı) | Yanlış güvenlik hissi | S1 kabul kriteri, düzeltilmiş hâli de geçmeyi ve F1/F2'nin kırmızı olduğunu içerir |
| `graph.py` şema yükleme maliyeti | Yavaş testler | `kenar_tablosu()` `lru_cache` ile bir kez hesaplanır |
| 21 şema + yeni testler kapsam düşüşü | coverage regression | `pytest-cov` ile ölçülür; sayı §10'da birlikte kararlaştırılır |
| Belge onarımları yeni sürüklenme üretir | Tekrar | S1'in sözleşme testi kalıcı denetim; `.opencode` kopyası P0-5'te senkronlanacak |

---

## 9. P0-2…P0-5 ile ilişki

| Plan | Bu spec'in sağladığı |
|---|---|
| **P0-2** Kaynak Doğrulama | `source-verifier.md` geçerli sözleşmeyle çalışır; `fulltext_available` yerini alır; `graph.py` `source_kullanan_iddialar` sunar |
| **P0-3** PDF → Kanıt | `graph.py` `bulgunun_kanit_zinciri` ve `rq_dan_kaynakca` sunar |
| **P0-4** Atıf + Onay | `citation_rules.md` doğru kuralla çalışır; `graph.py` `celiskili_iddialar` sunar |
| **P0-5** Uçtan uca + senkron | `.opencode` senkronu (D7) ve kapsam tablosu |

P0-2'ye geçiş bu spec uygulandıktan **sonra** yapılır. Araç katmanı hâlâ
stub'dır; bu spec araçları yazmaz, onların üzerine oturacak zemini hazırlar.

---

## 10. Açık kalan kararlar

Spec yazılırken tek bir karar ertelendi ve uygulama sırasında verilecek:

**Coverage hedefi (`fail_under`).** `pytest-cov` kurulu, hedef yok. S1…S5
bittikten sonra gerçek oran ölçülür; hedef sayı o ölçüme göre birlikte
kararlaştırılır. Önceden konan bir sayı, ölçülmemiş bir vaat olurdu.
