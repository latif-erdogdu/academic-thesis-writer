# Tez Oluşturma Çalışma Akışı

> **Bu akış bir komut dizisidir.** Her adımda `thesis:X` komutu verilir.
> Ajan önce komutu çalıştırır, sonra *ajanın* ürettiği metni `--file` ile
> geri verir. CLI Türkçe tez metni **yazmaz** — Writing Gate'in amacı budur.

## Neden bu dosya var

Akış, tek bir yerde okunabilir olmalı: yedi kapılı zincirin sırası, hangi
adımda hangi komutun çağrıldığı ve hangi çıktının nereye yazıldığı. Bu
dosyada o üçü yan yana durur.

## Zincir

| # | Kapı | Komut | Kapan koşulu |
|---|------|-------|--------------|
| 1 | `research_question` | `thesis:new` → `thesis:record research_questions` → `thesis:approve research_question` | `research_questions` dolu |
| 2 | `search_strategy` | `thesis:search` → `thesis:approve search_strategy` | `search_runs` dolu |
| 3 | `source_set` | `thesis:verify` → `thesis:approve source_set` | `sources` dolu |
| 4 | `research_gap` | `thesis:record gap_registry` → `thesis:approve research_gap` | `gap_registry` dolu |
| 5 | `methodology` | `thesis:record variables` … `thesis:approve methodology` | hazırlık denetimi yok |
| 6 | `findings` | `thesis:record findings_registry` → `thesis:record claims_registry` → `thesis:approve findings` | `findings_registry` dolu |
| 7 | `final_thesis` | `thesis:audit` → `thesis:approve final_thesis` → `thesis:export` | bütünlük + kanıt taraması temiz |

**Sıra atlanamaz.** `thesis:approve` önceki kapılar onaylı değilse reddeder
(`tools/atw/approval.py:onay_ver`). Hazırlığı olmayan kapı da açılmaz: onay,
içliği boş bir belgeye verilmiş olur.

**Tek istisna:** `methodology` kapısının hazırlık denetimi **yoktur**.
Bölümleri dolduran `thesis:write` bu kapının arkasındadır; denetim
`chapters`'a baksa ilk bölüm hiç yazılamazdı (dairesel bağımlılık).

---

## Adım 1 — Araştırma soruları (`research_question`)

```bash
thesis:new THESIS-2026-001 "Tez başlığı"
```

`thesis:new` çalışma dizininde `thesis_state.json` oluşturur. Var olan bir
tezi **üzerine yazmaz**; kasıtlıysa `--force` gerekir.

Soruları bir JSON dosyasına yazın ve kaydedin:

```json
[
  {
    "id": "RQ-001",
    "text": "Araştırma sorusunun metni",
    "type": "main",
    "status": "pending"
  }
]
```

```bash
thesis:record research_questions --file <SORULAR.json>
thesis:approve research_question
```

`chapter` alanını **boş bırakın**. `research_question.chapter → chapter`
gerçek bir kenardır ve bölümler `thesis:write` ile, yani bu kapının
*sonrasında* yazılır; şimdi doldurulursa "kopuk referans" hatası verir.
Sonradan eklenebilir.

## Adım 2 — Arama stratejisi (`search_strategy`)

Ayrıntı: `workflows/literature_review.md`

```bash
thesis:search RQ-001 --pico "P: chukar I: reintroduction O: survival"
thesis:approve search_strategy
```

`thesis:search` `search_runs` registry'sini doldurur. Bilinmeyen bir RQ
verilirse **arama yapmaz ve reddeder**; sessizce boş sonuç üretmez.
`--pico` şarttır: `tools/source_search/query_builder.py:parse_pico` yalnızca
İngilizce anahtar sözcük listesi tanır, Türkçe bir sorudan boş PICO üretir.

## Adım 3 — Kaynak kümesi (`source_set`)

```bash
thesis:verify --all
thesis:approve source_set
```

`thesis:verify` her kaynağı Crossref + OpenAlex ile doğrular. Doğrulanmayan
kaynak `verified` işaretlenmez; geri çekilmiş (retract) kaynak hiçbir koşulda
doğrulanmış sayılmaz. `sources` dolmadan bu kapı açılmaz.

## Adım 4 — Araştırma boşluğu (`research_gap`)

```json
[
  {
    "id": "GAP-001",
    "text": "Boşluğun tanımı",
    "evidence_ids": ["EVD-001"]
  }
]
```

```bash
thesis:record gap_registry --file <BOSLUKLAR.json>
thesis:approve research_gap
```

`evidence_ids` en az bir kayıt içermelidir (`schemas/research_gap.json`).
Boşluğu kanıtsız ilan etmek, kanıtsız iddia demektir.

## Adım 5 — Metodoloji (`methodology`)

Ayrıntı: `workflows/methodology.md`

```bash
thesis:record variables  --file <DEGISKENLER.json>
thesis:record datasets   --file <VERI_KUMELERI.json>
thesis:record analyses   --file <ANALIZLER.json>
thesis:record statistics --file <ISTATISTIKLER.json>
thesis:approve methodology
```

## Adım 6 — Bulgular ve iddialar (`findings`)

Ayrıntı: `workflows/findings.md`, `workflows/discussion.md`

```bash
thesis:record findings_registry --file <BULGULAR.json>
thesis:record claims_registry    --file <IDDIALAR.json>
thesis:record discussion_registry --file <TARTISMA.json>
thesis:approve findings
```

## Adım 7 — Bölüm yazımı, denetim ve dışa aktarım (`final_thesis`)

Ayrıntı: `workflows/chapter_writing.md`, `workflows/thesis_audit.md`

```bash
thesis:write CH-001 --rq RQ-001                      # brifing basar, durum değişmez
thesis:write CH-001 --rq RQ-001 --file <BOLUM.json>  # ajanın yazdığı bölümü denetler
thesis:audit --type all
thesis:approve final_thesis
thesis:export --format docx
```

`thesis:write --file` verilmezse yalnızca brifing basılır ve tez durumu
**değişmez**. Bu ayrım bilinçlidir: bölüm metnini `agents/writer.md` ajanı
üretir, CLI yalnızca doğrular.

`thesis:export` tek dosya üretir:

```
tez_<thesis_id>.md      (--format md)
tez_<thesis_id>.docx    (--format docx)
tez_<thesis_id>.pdf     (--format pdf)
```

Bölüm başına ayrı dosya **yoktur** ve `.bib` **üretilmez**; kaynakça
belgenin içine gömülüdür. Ekler (appendix) bu sürümde dışa aktarılmaz:
durum şemasında `appendices` alanı yok.

---

## Her adım sonrası

```bash
thesis:status
```

Yedi kapının hangisinin açık, hangisinin neden kapalı olduğunu yazar. Bir
adımda takılırsanız `thesis:approve --list` engelleri döküm olarak verir.

## Durum ve şema

- `thesis_state.json` — çalışma dizininde, tek dosya. İzlenmez (skill'i
  güncellediğinizde tez verisi kaynak deposuna karışmasın).
- `schemas/thesis_state.json` — bu bir **şemadır**, durum şablonu değil.
  `thesis_state.json`'ı elle kopyalamayın; `thesis:new` üretir.

## Kalite kapıları

- Kaynak yalnızca `verification.status == "verified"` ise metinde
  kullanılabilir (`tools/atw/write.py:haric_eden_kaynaklar`).
- `final_thesis` kapısı en katısıdır: kopuk referans, kanıtsız iddia ve
  geri çekilmiş kaynağa dayanan iddia denetimini de yapar.
- `thesis:audit --type all` beş denetimi çalıştırır: yapısal, atıf,
  metodoloji, tutarlılık, bütünlük.
