# Sistematik Derleme Protokolü

## Ne Zaman Bu Protokol Kullanılır

Sistematik derleme, **belirli bir soruya belirli ve tekrarlanabilir
biçimde** cevap arayan, taranmış kayıtların sayımını denetlenebilir
kılan bir literatür taramasıdır.

Bu protokol şu durumlarda kullanılır:

| Durum | Bu protokol |
|-------|-------------|
| "Bu konuda literatür var mı, ne diyor?" — hızlı ön tarama | Hayır → `literature_review.md` |
| "X etkisi var mı, kanıt gücü ne?" — tekrarlanabilir, sayımlı tarama | **Evet** |
| "Bu alanda hangi yöntemler kullanılmış?" — yöntem sentezi | **Evet** |
| Tek bir kitap veya rapor incelemesi | Hayır |

**Kuruluş/dergiler taraması (scoping review) ile bibliyometrik analiz
bu protokolün kapsamı dışındadır**; bu protokol hipotez testi ve
etki sentezi içindir.

## Protokol Adımları

### 1. Araştırma Sorusu

Tek cümle, ölçülebilir, kapsamı sınırlı. Varsayım test edilebilir
değilse bu adımda durulur.

**İnsan onayı:** `human_approvals.research_question`

### 2. search_strategy

Veritabanı, sorgu dizesi, tarih aralığı, dil kısıtı, alan kısıtı
tanımlanır. Sorgu **kaydedilir**, çünkü başka bir araştırmacı
tam olarak tekrarlayabilmelidir.

Her sorgu `search_run.json` kaydı olur:

```json
{
  "id": "SEARCH-001",
  "database": "openalex",
  "query": "(yontem adi OR yontem adi varyanti) AND (sonuc terimi)",
  "timestamp": "2026-09-26T09:00:00+00:00",
  "results_returned": 482,
  "inclusion_criteria": ["Son 10 yil", "Dogrulanmis kaynak"],
  "exclusion_criteria": ["Tam metne erisilemeyen", "Diger dillere yayinlanmis"]
}
```

### 3. Veritabanları

En az üç veritabanı: konu alanının **iki indeksli** veritabanı
(`crossref`, `openalex`, `scopus`, `web_of_science`) ve **tek indeksli**
bir veritabanı (`google_scholars`). Tek veritabanıyla tarama
sistematik derleme sayılmaz.

**Doğrulanabilirlik kuralı:** arama sonucu numarası bu kaydın dışında
hiçbir yerde tekrarlanamazsa, tarama tekrarlanabilir değildir.

### 4. Sorgu Sürümleri

Her veritabanı için ayrı sorgu dizesi kaydedilir. Sorgular arası
tutarsızlık, taramanın tekrarlanabilirliğini bozar.

### 5. inclusion (Dahil Etme)

Dahil etme ölçütleri **taramadan önce** yazılır, sonradan gevşetilmez.
Her ölçüt `search_run.json` → `inclusion_criteria` dizisinde yer alır.

### 6. exclusion (Dışlama)

Dışlama ölçütleri dahil etmeden ayrı ve önceden yazılıdır. Her
dışlama gerekçesi sayımıyla birlikte verilir:

```json
{
  "exclusion_reasons": [
    { "reason": "Tam metne erisilemedi", "count": 3 },
    { "reason": "Odak populasyonu ile uyusmuyor", "count": 70 }
  ]
}
```

`reason` alanı genel bir kategori değil, **o kayıtta gerçekten
geçerli olan gerekçe** olmalıdır. "Alakasız" gerekçe kabul edilmez.

### 7. deduplication (Yinelenen Kayıtların Silinmesi)

DOI önce karşılaştırılır; DOI yoksa başlık + ilk yazar + yıl
üçlüsü. Yinelenen sayısı `prisma_flow.duplicates_removed` alanına yazılır.

### 8. screening (Eleme)

Başlık/özet ve ardından tam metin iki aşamalı eleme. Her aşamanın
sayısı ayrı kaydedilir. **Eleme kararı gerekçesi olmadan kaydedilemez.**

### 9. Tam Metin

`reports_sought` sayısına ulaşılamayan raporların sayısı
`reports_not_retrieved` alanına yazılır. Bu sayı sıfır değilse,
erişim engelinin nedeni `open_questions`'a da yazılır.

### 10. quality_assessment (Kalite Değerlendirmesi)

Tek bir `quality_score` yerine **ayrık boyutlar** kullanılır:

| Boyut | Nitel ölçüt | Nicel ölçüt |
|-------|-------------|-------------|
| Bibliyografik doğruluk | `verification.status` | `verification.status` |
| Kanıt gücü | `evidence.strength` | `evidence.strength` |
| Yöntemsel sağlamlık | Araştırma tasarımı + güvenilirlik | Gözden geçirme + yöntem |
| İlgililik | Araştırma sorusuna uygunluk | Araştırma sorusuna uygunluk |
| Güncellik | `source.year` | `source.year` |
| Hakemli yayın | `source.peer_reviewed` | `source.peer_reviewed` |
| Retraksiyon durumu | `source.retraction_status` | `source.retraction_status` |

Tek puan haline getirmek boyutları gizler; ayrı tutulmalıdır.

### 11. extraction (Veri Çıkarımı)

`evidence.json` kaydı üretilir. Her kanıtta sayfa ve bölüm zorunludur:

```json
{
  "id": "EVD-001",
  "source_id": "SRC-001",
  "location": { "page": 17, "section": "3.2", "paragraph": null },
  "text": "Alinti metni",
  "evidence_type": "literature",
  "supports_claim": "CLM-001",
  "strength": "direct",
  "extracted_at": "2026-09-26T10:15:00+00:00",
  "extraction_method": "pdf_text_layer"
}
```

### 12. synthesis (Sentez)

Sentez kaynak listelemek değildir. Üç sonuç biçiminden en az biri
üretilmelidir:

- **Uzlaşma:** bulguların çoğu aynı yönde
- **Çelişki:** farklı sonuçlar → `contradiction-analyzer.md`
- **Boşluk:** hiçbir çalışma belirli soruyu cevaplamıyor →
  `research_gap.json`

## PRISMA Akış Denetimi

`prisma_flow` alanındaki sayımlar aritmetik olarak tutarlı olmalıdır:

```
records_identified - duplicates_removed = records_screened
records_screened   - records_excluded   = reports_sought
reports_sought     - reports_not_retrieved
                   = reports_excluded + studies_included
```

Bu denetim `tools.atw.state.validate_prisma_flow(flow)` ile yapılır.
Tutarsızlık varsa tarama **tamamlanmış sayılmaz**.

## Yayın Öncesi Kaynaklar

Deneme yayın (preprint), hakemli sürüm yayınlanmamışsa:

- `source_type` = `preprint`
- `publication_status` = `preprint`
- `peer_reviewed` = `false`

Preprint, hakemli sürümü yayınlanmış kaynağın yerine
**ikame edilmez**. İkisi aynı çalışmanın farklı sürümüdür ve
`citation.json` hangi sürümün alıntılandığını göstermelidir.

## İnsan Onayı

| Adım | `human_approvals` alanı |
|------|--------------------------|
| 2. search_strategy | `search_strategy` |
| 5-6. dahil/dışlama ölçütleri | `search_strategy` |
| 9. tam metin | `source_set` |

## Bağlı Olduğu Şemalar

- `schemas/search_run.json` — arama kaydı ve PRISMA sayımları
- `schemas/source.json` — kaynak durumu
- `schemas/evidence.json` — kanıt çıkarımı
- `schemas/research_gap.json` — sentez sonucu
