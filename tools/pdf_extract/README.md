# PDF Çıkarma Aracı (pdf_extract)

## Amaç

Doğrulanmış (`verification.status: "verified"`) ve tam metin erişimi olan
(`fulltext_available: true`) kaynaklardan; **sayfa/bölüm düzeyinde** kanıt
(`evidence.json`) çıkarmak.

## Girdi

- `source.json` kayıtları (doğrulanmış, `fulltext_available: true`)
- PDF dosyası (yerel, URL, veya kurumsal erişim üzerinden)
- Hedef: Belirli bir `claim` (iddia) için destekleyici kanıt bulmak

## Çıkarma Süreci

```
1. PDF İndirme / Erişim
   ├─ Açık erişim (Unpaywall, OpenAlex OA URL)
   ├─ Kurumsal proxy / kütüphane erişimi
   └─ Yazar preprint (arXiv, bioRxiv, SSRN)

2. PDF Parsing
   ├─ pdfplumber / PyMuPDF (fitz) / pdfminer.six
   ├─ Sayfa metni + yapı (başlıklar, tablolar, şekiller)
   └─ OCR (tarandır PDF için): Tesseract / paddleocr

3. Bölüm Tespiti
   ├─ Başlık hiyerarşisi: Abstract, Introduction, Methods, Results, Discussion, Conclusion
   ├─ Alt bölümler: Participants, Procedure, Statistical Analysis, vb.
   └─ Sayfa numarası eşleştirme

4. İddia–Kanıt Eşleştirme (Claim–Evidence Linking)
   ├─ Girdi: Hedef claim (CLM-XXX) metni + anahtar kelimeler
   ├─ Benzerlik: TF-IDF / BM25 / embedding cosine similarity
   ├─ Kanditat cümle/paragraf seçimi (top-k)
   └─ Manuel/ajanı onayı: "Bu kanıt iddiayı destekliyor mu?"

5. Kanıt Kaydı Oluşturma (evidence.json)
```

## Çıktı: `evidence.json` Kayıt Yapısı

```json
{
  "id": "EVD-001",
  "source_id": "SRC-001",
  "location": {
    "page": 17,
    "section": "Results",
    "subsection": "Primary Outcome Analysis",
    "paragraph_index": 3,
    "char_start": 12450,
    "char_end": 12890
  },
  "text": "The intervention group showed significantly higher scores (M=4.2, SD=0.8) compared to control (M=3.1, SD=0.9), t(98)=5.67, p<.001, d=1.15.",
  "evidence_type": "statistical",
  "strength": "direct",
  "supports_claim": "CLM-001",
  "verified": true,
  "extracted_at": "2026-09-26T10:15:00+00:00",
  "extraction_method": "pdfplumber+embedding",
  "notes": "Primary outcome Table 3, row 2"
}
```

## Alan Açıklamaları

| Alan | Zorunlu | Açıklama |
|------|---------|----------|
| `id` | Evet | `EVD-NNN` formatı |
| `source_id` | Evet | Kaynağın `SRC-XXX` kimliği |
| `location` | Evet | Sayfa, bölüm, alt bölüm, paragraf indeksi, karakter ofsetleri |
| `text` | Evet | Kanıt metni (alıntı/parafraz) |
| `evidence_type` | Evet | `literature|primary_data|statistical|finding|method|theory` |
| `strength` | Evet | `direct|indirect` (iddiayı doğrudan mı dolaylı mı destekliyor) |
| `supports_claim` | Evet | İddia kimliği (`CLM-XXX`) |
| `verified` | Evet | Çıkarma doğrulaması yapıldı mı |
| `extracted_at` | Evet | ISO 8601 zaman damgası |
| `extraction_method` | Hayır | `pdfplumber|pymupdf|ocr|manual` |
| `notes` | Hayır | Tablo/şekil referansı, ek notlar |

## Kanıt Türleri ve Kullanımı

| Tür | Açıklama | Örnek |
|-----|----------|-------|
| `literature` | Literatür taraması/arı planı bölümünden | "Önceki çalışmalar X gösterdi" |
| `primary_data` | Ham veri / gözlem | "Katılımcı sayısı N=120" |
| `statistical` | İstatistiksel test sonucu | "t(98)=5.67, p<.001, d=1.15" |
| `finding` | Çalışmanın ana bulgusu | "Müdahale grubunda anlamlı artış" |
| `method` | Yöntem detayı | "Rastgele atama, çift kör" |
| `theory` | Teorik çerçeve/hipotez | "Sosyal bilişsel teori öngörür ki..." |

## Güç (Strength) Kriterleri

- **`direct`**: Kanıt metni iddiayı **doğrudan, açıkça** destekliyor
  - Örn: İddia "X artırır" → Kanıt "X %25 arttırıldı (p<.01)"
- **`indirect`**: Kanıt **dolaylı/çevresel** destek veriyor
  - Örn: İddia "X artırır" → Kanıt "Y arttı ve X ile Y korelasyonlu"

## Kalite Kontrolleri

1. **Kaynak–Kanıt Tutarlılığı**: `source_id` ↔ `evidence.location` PDF'te gerçekten var mı?
2. **İddia–Kanıt Uyumu**: `supports_claim` hedef iddiası gerçekten destekleniyor mu?
3. **Sayfa Doğrulaması**: Sayfa numarası PDF sayfa sayısı içinde mi?
4. **Bölüm Doğrulaması**: Bölüm adı PDF başlıklarıyla eşleşiyor mu?
5. **Çift Onay**: İki bağımsız çıkarma (veya ajan + insan) karşılaştırması

## Hata Yönetimi

- PDF indirilemez / erişilemez: `fulltext_available: false` güncelle, atla
- Parsing hatası: OCR dene, başarısızsa logla, manuel kuyruğa al
- Bölüm tespiti başarısız: Tüm metni "Full Text" bloğu olarak kaydet, `location.section: "unknown"`
- Benzerlik skoru düşük (<0.3): Manuel inceleme kuyruğuna al

## Entegrasyon

- `evidence-extractor` ajanı tarafından çağrılır
- Girdi: `source_verify` çıktısı (doğrulanmış + fulltext) + hedef `claim` listesi
- Çıktı: `evidence.json` kayıtları → `claim.evidence_ids` güncellenir
- Sonraki: `writer` (kanıtlı iddialarla yazım), `citation-auditor` (atıf kontrolü)