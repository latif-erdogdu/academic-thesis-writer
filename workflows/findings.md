# Bulgular Çalışma Akışı

> **Bu akış bir komut dizisidir.** Ana zincir: `workflows/thesis_creation.md`
> Bu dosya 6. kapının (`findings`) kayıtlarını kapsar.

## Kural: bulgu yorum değildir

| | Örnek |
|---|---|
| **BULGU** | "Katılımcıların %62'si X seçeneğini belirtmiştir." |
| **YORUM** | "Bu sonuç X eğiliminin örneklemde baskın olduğunu göstermektedir." |

Yorum `discussion_registry`'ye gider (`workflows/discussion.md`).
`finding.json`'ın `statement` alanı yalnızca verinin söylediğini içerir.

## Kayıt

```bash
thesis:record findings_registry --file <BULGULAR.json>
```

Şema: `schemas/finding.json`

```json
[
  {
    "id": "FND-001",
    "rq_id": "RQ-001",
    "statement": "Gözlenen olgu. Yorum yok.",
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
]
```

Zorunlu alanlar: `id`, `rq_id`, `statement`, `evidence_ids`.
`evidence_ids` **en az bir** kayıt içermelidir (`minItems: 1`) — veriye
dayanmayan bulgu yazılamaz.

`rq_id` şeması gereği `^RQ-\d{3,}$` ve registry'de var olmalıdır; bulgu
kaydedilmeden önce sorunun tanımlı olması gerekir.

### `direction` ne anlama geliyor

| Değer | Anlam |
|---|---|
| `supported` | Veri iddiayı destekliyor |
| `refuted` | Veri iddiayı çürütüyor |
| `mixed` | Hem destekleyen hem çürüten kanıt var |
| `inconclusive` | Sonuç belirsiz — **bu da bir sonuçtur, saklama** |

`refuted` bulguları silinmez. Bir hipotezin çürütülmesi de bulgudur.

## İddialar

```bash
thesis:record claims_registry --file <IDDIALAR.json>
```

`finding` ve `claim` arasındaki bağlar çift yönlüdür: bulgu
`supported_claim_ids` ile iddiayı destekler, iddia da bulguyu
`evidence_ids` ile taşır. `thesis:audit --type evidence` yön uyuşmazlığını
bulur.

## Tartışma

```bash
thesis:record discussion_registry --file <TARTISMA.json>
```

Ayrıntı: `workflows/discussion.md`

## Kapıyı aç

```bash
thesis:approve findings
```

Kapı hazırlığı: `findings_registry` ve `claims_registry` dolu olmalıdır.
Boş listede onay vermek, hiçbir bulgu üretmeden "bulgular üretildi" demektir;
`approval.py:kontrol_yaz` bunu reddeder.

## Denetim

```bash
thesis:audit --type evidence    # kanıt zinciri
thesis:audit --type integrity   # kopuk referans, kanıtsız iddia, retraksiyon
```

## Şablonlar

- `references/evidence_rules.md` — kanıt kuralları
- `templates/evidence_matrix.md` — kanıt matrisi
- `templates/gap_analysis.md` — boşluk analizi (4. kapı için)
