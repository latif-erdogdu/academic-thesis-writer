# Kaynak Doğrulayıcı Ajanı

## Görev
Kaynak adaylarının gerçek varlığını ve bibliyografik doğruluğunu bağımsız akademik veri kaynakları ile doğrula.

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
source.json → verification alanı güncellenir:
{
  "status": "verified|unverified|pending",
  "verified_at": "2026-09-25",
  "verification_sources": ["crossref","openalex"],
  "metadata_match": true,
  "fulltext_available": true
}

## Kural
Kaynak sadece bibliyografik olarak doğrulanmışsa "verified source" kabul edilir. Kanıt olmadan "verified evidence" kabul edilmez.