# Literatür Taraması Çalışma Akışı

> **Bu akış bir komut dizisidir.** Ana zincir: `workflows/thesis_creation.md`
> Bu dosya yalnızca 2. ve 3. kapının (`search_strategy`, `source_set`) detayını verir.

## Ön koşul

`research_question` kapısı açık olmalıdır. Arama, kaydedilmiş bir soruya
bağlanır; `thesis:search` verilen `RQ-XXX` kimliğini bulamazsa **arama yapmaz
ve reddeder** — sessizce boş sonuç üretmez.

```bash
thesis:approve --list      # kapının durumunu öğren
```

## Adım 1 — Arama stratejisi (`search_strategy` kapısı)

`thesis:search` bir **PICO** metnini veritabanlarına gönderir.

```bash
thesis:search RQ-001 \
  --pico "P: chukar I: reintroduction O: survival" \
  --databases crossref,openalex,pubmed \
  --year-from 2000 \
  --max-results 100
```

### `--pico` şarttır, lüks değildir

`tools/source_search/query_builder.py:parse_pico` PICO'yu **İngilizce
anahtar sözcük listesiyle** ayrıştırır. Türkçe bir sorudan boş PICO üretilir
ve arama hiç sonuç döndürmez. Türkçe araştırma sorusu kullanıyorsanız
`--pico` değerini **İngilizce** yazın; RQ metni Türkçe kalabilir.

Bu bir kusurdur, tasarım değil — düzeltilmedi. Arama terimini İngilizce
vermek, sorunun kendisinden ayrı bir karardır.

### Olası çıktı

`search_runs` registry'si dolar: hangi veritabanına, hangi sorguyla, kaç
sonuç geldi. Ham kayıtlar `sources`'a yazılmadan önce **incelenmelidir**.

## Adım 2 — Kaynak kümesi (`source_set` kapısı)

```bash
thesis:verify --all
```

`thesis:verify` her aday kaynağı Crossref ve OpenAlex'e sorar. Kabul
ölçütleri `tools/source_verify/verify.py` içinde:

- bibliyografik eşleşme ≥ **0.60** (`MIN_BIBLIOGRAPHIC_MATCH`)
- en az **2 bağımsız** kaynak (`MIN_INDEPENDENT_SOURCES`)

Doğrulanamayan kaynak `verified` işaretlenmez. **Geri çekilmiş (retract)
kaynak hiçbir koşulda doğrulanmış sayılmaz.** Bu kaynaklar
`tools/atw/write.py:haric_eden_kaynaklar` ile metinde kullanılamaz.

```bash
thesis:approve source_set
```

## Adım 3 — Kanıt çıkarımı (isteğe bağlı ama önerilir)

`references/source_verification.md` bir kaynağın doğrulanmış olmasının
**yeterli olmadığını**, iddiayı gerçekten desteklemesi gerektiğini söyler.
Yerel PDF'ten alıntı çıkarmak için:

```bash
thesis:extract SRC-001 --claim CLM-001 --pdf <dosya.pdf>
```

Bu komut `evidence_registry`'yi doldurur — `record` komutunun yazamadığı,
CLI'nin kendi sahibi olduğu tek registry budur.

## Çıktılar

| Registry | Komut | Sonraki kapı |
|---|---|---|
| `search_runs` | `thesis:search` | `search_strategy` |
| `sources` | `thesis:verify` | `source_set` |
| `evidence_registry` | `thesis:extract` | — (`research_gap` için girdi) |

## Şablonlar

- `templates/literature_matrix.md` — sentez matrisi
- `references/source_verification.md` — doğrulama kuralları

## Sık yapılan hata

**Soru yazıp hemen aramaya geçmek.** `research_question` kapısı kapanmadan
yapılan arama, kapı açıldığında geçersizdir: `thesis:approve` önceki kapılar
onaylı değilse reddeder. Önce soruyu kaydedin ve onaylayın.
