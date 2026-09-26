# Atıf Kontrol Aracı (citation_check)

## Amaç

Tez metnindeki atıflar ile kaynakça (bibliyografi) arasındaki **bütünlüğü**
denetlemek; eksik, fazladan, tutarsız veya sahte atıfları tespit etmek.

## Denetim Kapsamı

| Denetim Türü | Açıklama | Ciddiyet |
|--------------|----------|----------|
| **Metin→Kaynakça** | Metinde geçen her atıf (Yazar, Yıl) kaynakçada var mı? | Critical |
| **Kaynakça→Metin** | Kaynakçadaki her kayıt metinde en az bir kez atıflı mı? | Major |
| **Kaynak Varlığı** | Atıflı kaynak `sources` registry'de gerçekten var mı? | Critical |
| **İddia Desteği** | Atıflı kaynak, atıflandığı iddayı (`claim`) destekliyor mu? | Major |
| **Format Tutarlılığı** | Seçili stil (APA 7, MLA, vb.) tüm atıflarda tutarlı mı? | Minor |
| **Yıl/Yazar Tutarlılığı** | Metindeki yıl/yazar, kaynakça kayıtla birebir mi? | Major |
| **Sayfa Numarası** | Doğrudan alıntılarda sayfa numarası var mı? | Minor |

## Girdi

- **Tez metni** (bölüm/paragraf düzeyinde, `paragraph.json` via `citation.json`)
- `citation.json` kayıtları (metin atıf ↔ kaynak kimliği eşleşmesi)
- `sources` registry (doğrulanmış kaynak kayıtları)
- `claims` registry (iddialar ve atıfları)

## Çıktı

`audit.json` kaydı (`audit_type: "citation"`) + `open_questions`/`quality_issues` güncellemesi.

```json
{
  "audit_id": "AUD-001",
  "thesis_id": "THESIS-2026-001",
  "audit_type": "citation",
  "date": "2026-09-26",
  "integrity_checks": {
    "fabricated_sources": 0,
    "unsupported_claims": 2,
    "retracted_sources_in_use": 0,
    "orphaned_citations": 1,
    "unverifiable_claims": 0
  },
  "findings": [
    {
      "severity": "critical",
      "message": "CIT-004, sources listesinde bulunmayan SRC-099 kaynağını gösteriyor.",
      "location": "Bölüm 3.2 Yöntem",
      "entity_id": "CIT-004"
    },
    {
      "severity": "major",
      "message": "Kaynakçada SRC-015 var ama metinde hiç atıflanmamış.",
      "location": "Kaynakça",
      "entity_id": "SRC-015"
    }
  ],
  "critical_issues": ["Uydurma atıf: CIT-004"],
  "deferred_minors": ["APA formatında virgül eksikliği: 3 atıf"]
}
```

## Denetim Akışı

```
1. Citation Kaydı Toplama
   ├─ paragraph.citations → citation.json → source_id
   ├─ claim.sources → source_id
   └─ evidence.source_id → source_id

2. Her source_id İçin:
   ├─ sources registry'de var mı? (yoksa: fabricated_sources++)
   ├─ verification.status nedir? (retracted → retracted_sources_in_use++)
   └─ claim destekleniyor mu? (claim.verification_status kontrolü)

3. Metin Atıfları (citation.json):
   ├─ Her citation_id için: paragraph metninde atıf formatı var mı?
   ├─ Yazar/Yıl formatı stil (APA 7) ile uyumlu mu?
   └─ Sayfa numarası doğrudan alıntıda var mı?

4. Çapraz Referans:
   ├─ Metinde geçen her (Yazar, Yıl) → sources registry'de var mı?
   ├─ sources registry'deki her kayıt → metinde en az 1 atıf var mı?
   └─ claim.sources ↔ citation.source_id tutarlılığı

5. Format Denetimi (Seçili Stil):
   ├─ APA 7: (Yazar, Yıl) / Yazar (Yıl)
   ├─ MLA: (Yazar Sayfa)
   ├─ IEEE: [1], [2-4]
   └─ Chicago: Dipnot / Yazar-Tarih

6. Raporlama:
   ├─ critical → open_questions + quality_issues + audit.findings
   ├─ major → quality_issues + audit.findings
   └─ minor → deferred_minors
```

## Sahte/Uydurma Atıf Tespiti (Fabricated Sources)

| Belirti | Tespit Yöntemi |
|---------|----------------|
| DOI çözümlenmiyor | Crossref/OpenAlex sorgulama |
| Yazar/Yıl/BAŞLIK kombinasyonu hiçbir veritabanında yok | 3+ veritabanı paralelleştirme |
| İddia ile kaynak konusu uyuşmuyor | Claim metni ↔ source title/abstract embedding benzerliği < 0.3 |
| Aynı kaynak birden fazla sahte iddiada kullanılıyor | Grafik analizi: `source → claims` out-degree anomalisi |

## Retraksiyon / Düzeltme Takibi

- `retraction_status: "retracted"` kaynak metinde kullanılıyorsa → **Critical**
- `correction_status: "corrected|erratum"` → atıf metninde not düşülmeli (örn: "corrected 2024")
- `expression_of_concern` → uyarı (Major)

## Stil Doğrulama (APA 7 Örneği)

| Durum | Doğru | Yanlış |
|-------|-------|--------|
| 2 yazar | (Yazar1 & Yazar2, Yıl) | (Yazar1, Yazar2, Yıl) |
| 3+ yazar | (Yazar1 et al., Yıl) | (Yazar1, Yazar2, Yazar3, Yıl) |
| Kurumsal yazar | (Kurum Adı, Yıl) | (Kurum, Yıl) |
| Doğrudan alıntı | (Yazar, Yıl, s. 15) | (Yazar, Yıl) |
| Parafraz | (Yazar, Yıl) | (Yazar, Yıl, s. 15) |

## Entegrasyon

- `citation-auditor` ajanı tarafından çağrılır
- `workflows/thesis_audit.md` protokolünün 2. aşaması (Atıf Denetimi)
- Girdi: `paragraph.json`, `citation.json`, `sources`, `claims`
- Çıktı: `audit.json` + `open_questions`/`quality_issues` güncellemesi
- Tetiklenen aksiyon: Eksik atıflar için `writer` ajanı uyarılır

## Performans ve Ölçeklenebilirlik

- `citation.json` indeksli arama (source_id, paragraph_id)
- `sources` registry DOI/Title indeksi
- Paralel denetim: Her `citation_id` bağımsız doğrulanabilir
- Önbellek: Crossref/OpenAlex sorguları 24h TTL ile önbelleklenir