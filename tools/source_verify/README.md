# Kaynak Doğrulama Aracı (source_verify)

## Amaç

`source_search` tarafından bulunan kaynak adaylarını, en az **2 bağımsız
veritabanı** ile bibliyografik ve DOI düzeyinde doğrulamak.
Sonuç `source.json` `verification` alanına yazılır.

## Doğrulama Kriterleri (Hepsi Zorunlu)

| Kriter | Açıklama | Eşik |
|--------|----------|------|
| **DOI Doğrulama** | DOI var ve Crossref/OpenAlex'te çözümleniyor | `doi_match: true` |
| **Yazar Eşleşmesi** | Yazar listesi (sırasızdan) ≥ 80% benzerlik | `author_match: true` |
| **Başlık Eşleşmesi** | Normalize edilmiş başlık ≥ 90% (Levenshtein/Jaro-Winkler) | `title_match: true` |
| **Yıl Eşleşmesi** | Tam yıl eşleşmesi | `year_match: true` |
| **Dergi/Yayıncı Eşleşmesi** | Dergi adı veya yayıncı ≥ 85% | `journal_match: true` |
| **Bibliyografik Skor** | Yukarıdaki 5 kriterin ağırlıklı ortalaması | `≥ 0.60` |

## Veritabanları ve Roller

| Veritabanı | Sağladığı Bilgi | Güvenilirlik |
|------------|----------------|--------------|
| **Crossref** | DOI metadata (yazar, başlık, yıl, derji, ISSN, type) | Birincil (DOI otoritesi) |
| **OpenAlex** | Açık erişim metadata, kurum/author ID, concepts | İkincil (Crossref ile çapraz) |
| **Semantic Scholar** | Paper ID, citation count, references, abstract | Üçüncü (semantik doğrulama) |
| **PubMed** (opsiyonel) | PMID, MeSH, journal metadata | Biyomedikal için dördüncü |

> **Kural**: En az **2 bağımsız veritabanı** eşleşmesi zorunludur.
> Crossref + OpenAlex minimum çift; PubMed/Semantic Scholar bonus.

## Akış

```
Kaynak Adayı (source_search çıktısı)
       ↓
1. DOI Çıkarma ve Normalizasyon
       ↓
2. Paralel Veritabanı Sorgulama (Crossref, OpenAlex, Semantic Scholar)
       ↓
3. Her Veritabanı İçin:
   - DOI çözümleme → metadata çekme
   - Yazar/başlık/yıl/derji karşılaştırma
   - Skor hesaplama (0.0–1.0)
       ↓
4. Çapraz Doğrulama:
   - En az 2 veritabanında bibliyografik skor ≥ 0.60
   - DOI eşleşmesi (Crossref + OpenAlex) → `doi_match: true`
       ↓
5. Karar:
   - TÜM kriterler geçti → status: "verified"
   - DOI eşleşti ama bibliyografik düşük → "unverified" (not: manual review)
   - DOI yok / çözümlenmedi → "pending" (manuel doğrulama bekliyor)
   - Geri çekilmiş tespit → status: "retracted", retraction_status: "retracted"
       ↓
6. Çıktı Yazma → source.json verification alanı
```

## Çıktı: `source.json` `verification` Alanı

```json
{
  "verification": {
    "status": "verified|unverified|pending|retracted|corrected",
    "bibliographic_match": 0.95,
    "doi_match": true,
    "author_match": true,
    "title_match": true,
    "year_match": true,
    "journal_match": true,
    "verified_at": "2026-09-26T10:12:00+00:00",
    "verification_sources": ["crossref", "openalex"]
  },
  "retraction_status": "not_retracted|retracted|expression_of_concern|unknown",
  "correction_status": "none|corrected|erratum|retracted_and_republished",
  "fulltext_available": true
}
```

## Retraksiyon / Düzeltme Taraması

- Crossref `relation.has-retraction` / `relation.is-retracted-by`
- OpenAlex `retracted` flag
- PubMed `Retracted Publication` tag
- Tespit edilirse: `retraction_status: "retracted"`, `verification.status: "retracted"`
- İlgili iddialar `retraksiyona_ugrayan_iddialar()` ile işaretlenir

## Hata Yönetimi

- DOI çözümlenemezse: `pending`, `verification_sources: ["manual"]`
- Ağ hatası: Exponential backoff (max 3), kısmi sonuçlarla devam
- Veritabanı API limiti: Sıralı sorgulama, rate limit sayacı

## Entegrasyon

- `source-verifier` ajanı tarafından çağrılır
- `workflows/systematic_review.md` protokolünün 3. aşaması
- Girdi: `source_search` adayları → Çıktı: `source.json` doğrulanmış kayıtlar
- Sonraki: `pdf_extract` (tam metin erişimi olanlar için)