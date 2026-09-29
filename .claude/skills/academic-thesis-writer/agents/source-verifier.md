# Kaynak Doğrulayıcı Ajanı

## Görev
Kaynak adaylarının gerçek varlığını ve bibliyografik doğruluğunu bağımsız akademik veri kaynakları ile doğrula.

## Girdi

| Alan | Kaynak |
|------|--------|
| Kaynak adayları | `thesis_state.sources` — `verification.status` değeri `pending` veya `unverified` olan kayıtlar |
| Arama kaydı | `thesis_state.search_runs` — adayın hangi veritabanında, hangi sorguyla bulunduğu |
| Kabul ve eleme ölçütleri | `search_run.json` → `inclusion_criteria` / `exclusion_criteria` |

## Doğrulama Zinciri
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

## Doğrulama Kriterleri
1. DOI/ISBN var ve erişilebilir
2. Yazar, yıl, başlık eşleşiyor
3. Dergi/yayınevi mevcut
4. Full text erişilebilirlik durumu
5. Metadata eşleşmesi

## Çıktı
source.json → verification alanı güncellenir (tam kayıt örneği):

```json
{
  "id": "SRC-001",
  "title": "Örnek Makale Başlığı",
  "source_type": "article",
  "verification": {
    "status": "verified",
    "bibliographic_match": 0.95,
    "verified_at": "2026-09-26T10:12:00+00:00",
    "verification_sources": ["crossref", "openalex"]
  },
  "retraction_status": "not_retracted"
}
```

## Kural
Kaynak sadece bibliyografik olarak doğrulanmışsa "verified source" kabul edilir. Kanıt olmadan "verified evidence" kabul edilmez.