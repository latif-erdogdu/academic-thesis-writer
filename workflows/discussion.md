# Tartışma Çalışma Akışı

> **Bu akış bir komut dizisidir.** Ana zincir: `workflows/thesis_creation.md`
> Tartışma 6. kapıya (`findings`) yazılır; ayrı kapısı yoktur.

## Kural: bulguyu tekrarlama, yorumla ve bağla

Bir tartışma kaydı **kendi bulgusunu tekrar etmez**. `interpretation`
alanı, bulgunun ne anlama geldiğini söyler.

## Kayıt

```bash
thesis:record discussion_registry --file <TARTISMA.json>
```

Şema: `schemas/discussion.json`

```json
[
  {
    "id": "DSC-001",
    "finding_ids": ["FND-001"],
    "rq_id": "RQ-001",
    "literature_evidence_ids": ["EVD-002"],
    "compared_source_ids": ["SRC-001"],
    "interpretation": "Bulgunun ne anlama geldiği ve neden önemli olduğu.",
    "alternative_explanations": ["Olası alternatif açıklama 1"],
    "limitations_acknowledged": ["Kabul edilen sınırlılık 1"],
    "agrees_with": ["DSC-000"],
    "disagrees_with": [],
    "notes": ""
  }
]
```

Zorunlu: `id`, `finding_ids`, `interpretation`.
`finding_ids` **en az bir** bulgu içermelidir — bulgusuz tartışma yazılamaz.

## Adımlar

1. **Karşılaştır** — her bulguyu literatürdeki benzer/çelişen çalışmalara
   bağla (`compared_source_ids`, `agrees_with`, `disagrees_with`)
2. **Beklenmedik bulguları açıkla** — çelişen sonucu
   `alternative_explanations` ile ele al
3. **Sınırlılıkları kabul et** — `limitations_acknowledged`; sınırlılığı
   saklamak, bulguyu olduğundan güçlü göstermektir
4. **Teorik katkıyı tanımla** — bu tezin literatüre ne kattığı

## Kapı

```bash
thesis:approve findings --by "Dr. Danışman Adı"
```

Tartışma kayıtları `findings` kapısının **isteğe bağlı** girdisidir;
kapının zorunlu girdisi `findings_registry` ve `claims_registry`'dir. Yani
tartışma kaydı yazılmadan da kapı açılabilir. Yazılmadıysa tartışma bölümü
kanıtsız yorumdan ibaret kalır — denetlenebilir olmayan iddia.

## Denetim

```bash
thesis:audit --type evidence
```

Tartışmada dayanılan kaynaklar `verified` değilse metinde
kullanılamazlar (`tools/atw/write.py:haric_eden_kaynaklar`).

## Şablon

- `references/evidence_rules.md` — yorum sınırı kuralları
- `agents/contradiction-analyzer.md` — çelişki çözümleme ajanı
