# Academic Thesis Writer

Akademik tezlerin planlanması, literatür araştırması, kaynak doğrulama, bölüm yazımı, metodoloji oluşturma, akademik atıf yönetimi ve tez kalite denetimi için kapsamlı akademik araştırma ve yazım sistemi.

## 🎯 Amaç

Bu proje, akademik tez yazımında **doğruluk** ve **kaynak güvenilirliği** önceliğiyle çalışan bir agent skill mimarisi sunar. Metin üretimi hızından ziyade, kaynak doğrulanabilirliği ve metodolojik tutarlılık odaklı tasarlanmıştır.

## ⚠️ Temel Prensipler

- **Kaynak uydurma YOK**: Makale, kitap, tez, DOI, yazar, yıl, dergi, cilt, sayı, sayfa veya istatistik asla uydurulmaz
- **Her iddia kaynaklı olmalı**: Önemli akademik iddialar mümkün olduğunda doğrulanabilir kaynağa dayanmalı
- **İzlenebilirlik**: CLAIM → SOURCE → EVIDENCE → CHAPTER → CITATION zinciri korunmalı
- **Metodolojik tutarlılık**: Araştırma soruları, hipotezler, yöntem ve bulgular arasında uyum sağlanmalı

## 📁 Repo Yapısı

```
academic-thesis-writer/
│
├── SKILL.md                          # Agent mimarisi ve kuralları
├── references/                       # Akademik bütünlük referansları
│   ├── citation_rules.md            # Atıf kuralları (APA, MLA, Chicago, IEEE)
│   ├── source_verification.md       # Kaynak doğrulama süreçleri
│   └── academic_integrity.md        # Akademik dürüstlük prensipleri
│
├── workflows/                        # Çalışma akışları
│   ├── thesis_creation.md           # Tez oluşturma akışı
│   ├── literature_review.md         # Literatür taraması
│   ├── methodology.md               # Metodoloji geliştirme
│   ├── chapter_writing.md           # Bölüm yazımı
│   └── thesis_audit.md              # Tez denetimi
│
├── schemas/                          # Veri şemaları
│   ├── thesis_state.json            # Tez durumu takibi
│   ├── source.json                  # Kaynak şeması
│   └── claim.json                   # İddia şeması
│
└── templates/                        # Şablonlar
    ├── thesis_structure.md          # Tez bölüm yapısı
    ├── literature_matrix.md         # Literatür matrisi
    └── quality_report.md            # Kalite denetim raporu
```

## 🏗️ Mimarisi

### 6 Katmanlı Sistem

```
                    THESIS AGENT
                         │
          ┌──────────────┼──────────────┐
          │              │              │
     RESEARCHER       WRITER        AUDITOR
          │              │              │
     kaynak bulma    metin üretme   hata bulma
          │              │              │
          └──────────────┼──────────────┘
                         │
                    THESIS STATE
                         │
                  SOURCE / CLAIM DB
```

- **Researcher**: Kaynak bulma ve doğrulama
- **Writer**: Metin üretimi (Thesis State'e dayanır)
- **Auditor**: Hata bulma ve tutarlılık denetimi

## 📋 Kullanım

### Yeni Tez Başlatma

1. `schemas/thesis_state.json` dosyasını doldurun
2. Araştırma problemini ve sorularını tanımlayın
3. `workflows/thesis_creation.md` akışını takip edin

### Literatür Taraması

```bash
workflows/literature_review.md
```

Kaynaklar tematik olarak gruplanır, her kaynak için:
- Yazar, yıl, başlık
- Araştırma amacı ve yöntem
- Temel bulgular ve sınırlılıklar
- Tezle ilişkisi

### Bölüm Yazımı

Her bölüm için:
1. Thesis State kontrolü
2. Kaynak/iddia denetimi
3. Paragraf metadata etiketleme (P-XXX)
4. Kalite kontrolü

### Tez Denetimi

```bash
workflows/thesis_audit.md
```

4 bileşenli denetim:
- Terminology (Kavramsal tutarlılık)
- Numbers (Veri tutarlılığı)
- Sample/Population (Örneklem tutarlılığı)
- Method vs. Results (Yöntem-bulgu uyumu)

## 🔍 Özellikler

- ✅ **Kaynak doğrulama sistemi**: Her iddia izlenebilir
- ✅ **Paragraf metadata**: P-XXX etiketleme ile iddia-kaynak eşleşmesi
- ✅ **Çoklu atıf stili**: APA, MLA, Chicago, IEEE, Harvard
- ✅ **Tez State persistence**: Oturumlar arası tutarlılık
- ✅ **6 katmanlı mimari**: Researcher/Writer/Auditor ayrımı
- ✅ **Kalite denetim raporu**: Yapısal, atıf, metodoloji ve tutarlılık denetimleri

## 🚀 Başlangıç

```bash
# Repo'yu klonla
git clone https://github.com/latif-erdogdu/academic-thesis-writer.git

# Thesis State'i başlat
cp schemas/thesis_state.json thesis_state.json

# İlk tez için bilgileri doldur
# workflows/thesis_creation.md akışını takip et
```

## 📖 Dokümantasyon

- [SKILL.md](./SKILL.md) - Agent mimarisi ve detaylı kurallar
- [workflows/](./workflows/) - Tüm çalışma akışları
- [templates/](./templates/) - Kullanıma hazır şablonlar
- [schemas/](./schemas/) - Veri şemaları
- [references/](./references/) - Akademik bütünlük referansları

## 🤝 Katkı

Bu proje akademik dürüstlük ve kaynak doğrulanabilirliği ilkelerine bağlıdır. Katkı yapmadan önce:

1. Kaynak uydurma yapmayın
2. Mevcut mimariyi koruyun
3. Thesis State tutarlılığını gözetin

## 📄 Lisans

Akademik kullanım için. Kaynak doğrulama ve akademik bütünlük kurallarına uyum zorunludur.

---

**Not**: Bu sistem metin üretimi hızından ziyade akademik kalite ve doğruluk odaklı tasarlanmıştır. Her önemli iddia mümkün olduğunda doğrulanabilir bir kaynağa dayanmalıdır.
