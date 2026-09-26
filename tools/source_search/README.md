# Kaynak Arama Aracı (source_search)

## Amaç

Araştırma sorusuna (RQ) uygun akademik kaynakları, tanımlı veritabanlarında
sistematik olarak keşfetmek ve `source.json` aday kayıtları üretmek.

## Veritabanları

| Veritabanı | Erişim | Notlar |
|------------|--------|--------|
| **Crossref** | REST API (ücretsiz) | DOI, bibliyografik metadata; `mailto` parametresi ile polite pool |
| **OpenAlex** | REST API (ücretsiz) | 200M+ kayıt, kurum/author/concept filtreleri |
| **Semantic Scholar** | REST API (ücretsiz, rate-limited) | AI tabanlı semantik arama, citation graph |
| **PubMed/MEDLINE** | E-utilities (NCBI) | Biyomedikal odaklı, MeSH terimleri |
| **Google Scholar** | Resmi API yok; serpapi/scholarly kütüphaneleri | Kapsam geniş; rate limiting katı |

## Arama Stratejisi

1. **RQ → Anahtar Kelime Çıkarımı**
   - PICO/PECO çerçevesi: Population, Intervention, Comparison, Outcome
   - Boolean operatörler: AND, OR, NOT
   - Truncation/wildcard: `educat*` → education, educational, educator

2. **Veritabanı Bazlı Sorgu Çevirimi**
   - Her veritabanın sözdizimine uyarlama (MeSH, Field tags, vb.)
   - Crossref: `query.bibliographic`, `filter=type:journal-article`
   - OpenAlex: `filter=concepts.id:C12345,publication_year:>2010`
   - PubMed: `[MeSH Terms]`, `[Title/Abstract]`

3. **Dahil/Hariç Tutma Kriterleri (İnclusion/Exclusion Criteria)**
   - Yıl aralığı, dil, çalışma türü, peer-review durumu
   - PRISMA akışı için belgeleme

4. **Tekrar Giderme (Deduplication)**
   - DOI bazlı (birincil), başlık+yazar+yıl benzerliği (ikincil)
   - `source.json` `supersedes_source_id` ile zincirleme

## Çıktı

`source.json` aday kayıtları (henüz doğrulanmamış):

```json
{
  "id": "SRC-XXX",
  "title": "...",
  "authors": ["..."],
  "year": 2024,
  "journal": "...",
  "doi": "10.xxxx/...",
  "source_type": "article|book|conference|preprint|...",
  "verification": {
    "status": "pending",
    "bibliographic_match": 0.0,
    "verified_at": "2026-09-26T10:12:00+00:00",
    "verification_sources": []
  },
  "retraction_status": "unknown",
  "access_date": "2026-09-26"
}
```

## Entegrasyon

- `researcher` ajanı tarafından çağrılır
- `workflows/systematic_review.md` protokolünün 2. aşaması
- Sonraki adım: `source_verify` (DOI/bibliyografik doğrulama)

## Rate Limiting ve Etiket

- Crossref: polite pool (`mailto=email@domain`), 50 req/s
- OpenAlex: 10 req/s (polite), 100 req/s (authenticated)
- Semantic Scholar: 100 req/5dk (API key ile daha yüksek)
- PubMed: 3 req/s (API key ile 10 req/s)
- Google Scholar: resmi API yok; scraping riskli, serpapi önerilir

## Hata Yönetimi

- Ağ hatalarında exponential backoff (max 3 deneme)
- API yanıt kodları: 429 → bekle, 5xx → tekrar dene
- Kısmi sonuçlar kaydedilir, hata loglanır