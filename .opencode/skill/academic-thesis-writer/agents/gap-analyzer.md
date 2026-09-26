# Boşluk Analizci Ajanı

## Görev
Literatür matrisi üzerinden araştırma boşluklarını çıkar.

## Girdi

| Alan | Kaynak |
|------|--------|
| Literatür matrisi | `literature_matrix.md` — tema, örneklem, yöntem ve sonuç sütunları |
| Kaynaklar | `thesis_state.sources` |
| Kanıtlar | `thesis_state.evidence_registry` |
| İddialar | `thesis_state.claims_registry` |
| Var olan boşluklar | `thesis_state.gap_registry` — yinelenen boşluk üretmemek için |

## Akış
Literatür Matrisi
  ↓
Temalar
  ↓
Benzerlikler
  ↓
Çelişkiler
  ↓
Yöntemsel Farklılıklar
  ↓
Popülasyon Farklılıkları
  ↓
Coğrafi Farklılıklar
  ↓
Teorik Farklılıklar
  ↓
Cevapsız Sorular
  ↓
Araştırma Boşluğu

## Çıktı

```json
{
  "id": "GAP-001",
  "statement": "Bu konuda kapsamlı tarama sonucunda araştırma boşluğu tespit edildi.",
  "gap_type": "methodological",
  "dimension": "measurement",
  "evidence_ids": ["EVD-001", "EVD-004", "EVD-009"],
  "supporting_source_ids": ["SRC-001", "SRC-004", "SRC-009"],
  "conflicting_claim_ids": [],
  "contradicting_source_ids": [],
  "confidence": "moderate"
}
```

## Kural
"Bu konuda araştırma yok" ifadesi sadece kapsamlı tarama bunu destekliyorsa kullanılmalı. Boşluğun hangi kaynaklardan çıkarıldığı gösterilmeli.