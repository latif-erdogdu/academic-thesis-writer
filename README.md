# Akademik Tez Yazarı

Akademik tezlerin planlanması, literatür araştırması, kaynak doğrulama, bölüm yazımı, metodoloji oluşturma, akademik atıf yönetimi ve tez kalite denetimi için kapsamlı akademik araştırma ve yazım sistemi.

## 🎯 Amaç

Bu proje, akademik tez yazımında **doğruluk** ve **kaynak güvenilirliği** önceliğiyle çalışan bir agent skill mimarisi sunar. Metin üretimi hızından ziyade, kaynak doğrulanabilirliği ve metodolojik tutarlılık odaklı tasarlanmıştır.

## ⚠️ Temel Prensipler

- **Kaynak uydurma YOK**: Makale, kitap, tez, DOI, yazar, yıl, dergi, cilt, sayı, sayfa veya istatistik asla uydurulmaz
- **Her iddia kaynaklı olmalı**: Önemli akademik iddialar mümkün olduğunda doğrulanabilir kaynağa dayanmalı
- **İzlenebilirlik**: ARAŞTIRMA SORUSU → İDDİA → KANIT → KAYNAK → BÖLÜM → PARAGRAF → ATIF → KAYNAKÇA zinciri korunmalı
- **Metodolojik tutarlılık**: Araştırma soruları, hipotezler, yöntem ve bulgular arasında uyum sağlanmalı
- **Kanıt Kapısı**: Bir iddia kanıt, doğrulanmış veri veya teorik önerme olmadan final metne alınmaz
- **Yazım Kapısı**: KEŞİF → DOĞRULAMA → KANIT → İDDİA → YAZIM (Yazım → kaynak arama DEĞİL)

## 📁 Repo Yapısı

```
academic-thesis-writer/
│
├── SKILL.md                          # Orchestrator: Agent mimarisi ve kuralları
├── agents/                           # Alt ajanlar (modüler yapı)
│   ├── researcher.md                 # Araştırmacı Ajanı
│   ├── source-verifier.md            # Kaynak Doğrulayıcı Ajanı
│   ├── evidence-extractor.md         # Kanıt Çıkarıcı Ajanı
│   ├── gap-analyzer.md               # Boşluk Analizci Ajanı
│   ├── contradiction-analyzer.md     # Çelişki Analisti
│   ├── writer.md                     # Yazar Ajanı
│   ├── citation-auditor.md           # Atıf Denetçisi Ajanı
│   ├── methodology-auditor.md        # Yöntem Denetçisi Ajanı
│   ├── consistency-auditor.md        # Tutarlılık Denetçisi Ajanı
│   └── integrity-auditor.md          # Bütünlük Denetçisi
│
├── references/                       # Akademik bütünlük referansları
│   ├── citation_rules.md             # Atıf kuralları (APA, MLA, Chicago, IEEE, Harvard)
│   ├── source_verification.md        # Kaynak doğrulama süreçleri
│   ├── evidence_rules.md             # Kanıt kuralları (Evidence Gate, Writing Gate)
│   ├── academic_integrity.md         # Akademik dürüstlük prensipleri
│   ├── research_gap.md               # Araştırma boşluğu kuralları
│   ├── systematic_review_protocol.md # Sistematik derleme protokolü (PRISMA)
│   └── methodology_rules.md          # Yöntem denetim kuralları (nicel/nitel/karma)
│
├── workflows/                        # Çalışma akışları
│   ├── thesis_creation.md            # Tez oluşturma akışı
│   ├── literature_review.md          # Literatür taraması
│   ├── systematic_review.md          # Sistematik inceleme protokolü
│   ├── methodology.md                # Metodoloji geliştirme
│   ├── chapter_writing.md            # Bölüm yazımı
│   ├── findings.md                   # Bulgular yazımı
│   ├── discussion.md                 # Tartışma yazımı
│   └── thesis_audit.md               # Tez denetimi
│
├── schemas/                          # Veri şemaları (JSON Schema draft 2020-12)
│   ├── thesis_state.json             # Tez durumu takibi
│   ├── source.json                   # Kaynak şeması
│   ├── claim.json                    # İddia şeması
│   ├── evidence.json                 # Kanıt şeması
│   ├── paragraph.json                # Paragraf şeması
│   ├── research_question.json        # Araştırma sorusu şeması
│   ├── audit.json                    # Denetim şeması
│   ├── citation.json                 # Atıf kaydı
│   ├── research_gap.json             # Araştırma boşluğu
│   ├── finding.json                  # Bulgu
│   ├── discussion.json               # Tartışma
│   ├── conclusion.json               # Sonuç
│   ├── search_run.json               # PRISMA arama kaydı
│   ├── statistic.json                # İstatistik
│   ├── dataset.json                  # Veri kümesi
│   ├── analysis.json                 # Analiz
│   ├── table.json                    # Tablo
│   ├── figure.json                   # Şekil
│   ├── chapter.json                  # Bölüm
│   ├── variable.json                 # Değişken
│   └── hypothesis.json               # Hipotez
│
├── templates/                        # Şablonlar
│   ├── thesis_structure.md           # Tez bölüm yapısı
│   ├── literature_matrix.md          # Genişletilmiş literatür matrisi
│   ├── evidence_matrix.md            # Kanıt matrisi
│   ├── gap_analysis.md               # Boşluk analizi
│   └── quality_report.md             # Kalite denetim raporu
│
├── tools/                            # Araç arayüzleri (README)
│   ├── source_search/                # Kaynak arama (Crossref, OpenAlex, Semantic Scholar, PubMed, Google Scholar)
│   ├── source_verify/                # Kaynak doğrulama (DOI, bibliyografik karşılaştırma)
│   ├── pdf_extract/                  # PDF'ten kanıt çıkarma (sayfa/bölüm düzeyinde)
│   └── citation_check/               # Atıf-kaynakça bütünlük denetimi
│
└── tests/                            # Test senaryoları
    ├── fixtures/                     # Kurgusal örnek kayıtlar
    ├── schema_tests/                 # Şema ve durum testleri
    ├── contract_tests/               # Sözleşme testleri (ajan blokları)
    ├── unit_tests/                   # Birim testleri (graph, ids, state)
    └── integration_tests/            # Uçtan uca bütünlük testleri
```

## 🏗️ Mimarisi

### Orchestrator + 10 Alt Ajan

```
                    ┌──────────────────────┐
                    │     TEZ AJANI        │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        ARAŞTIRMACI         YAZAR          DENETÇİ
              │                │                │
       ┌──────┴──────┐         │        ┌───────┼────────┐
       │             │         │        │       │        │
   Literatür      Kaynak       │    Atıf    Yöntem   Tutarlılık
   Arama          Doğrula      │    Denetimi Denetimi  Denetimi
       │             │         │        │       │        │
       └──────┬──────┘         │        └───────┼────────┘
              │                │                │
              ▼                ▼                ▼
       KANIT VERİTABANI ──── TEZ DURUMU ──── DENETİM RAPORU
              │                │
              └────────┬───────┘
                       ▼
                  NİHAİ TEZ
```

### Görev Yönlendirme

```
Kullanıcı İsteği
     ↓
SKILL (Orchestrator)
     ↓
Görev Belirle
     ↓
Araştırma?
 ├── EVET → Araştırmacı
 └── HAYIR
     ↓
Yazım?
 ├── EVET → Yazar
 └── HAYIR
     ↓
Denetim?
 └── EVET → Denetçi
```

### Alt Ajan Görevleri

| Ajan | Görev |
|------|-------|
| **Araştırmacı** | Kaynak keşfi, doğrulama, kanıt çıkarma, boşluk analizi |
| **Kaynak Doğrulayıcı** | Crossref, OpenAlex, Semantic Scholar ile DOI/bibliyografik doğrulama |
| **Kanıt Çıkarıcı** | Doğrulanmış PDF'lerden sayfa/bölüm düzeyinde kanıt çıkarma |
| **Boşluk Analizci** | Literatür matrisinden araştırma boşluklarını çıkarma (yöntemsel, popülasyon, coğrafi, teorik) |
| **Çelişki Analisti** | Aynı konuda farklı sonuçlara varan çalışmaları bulma, çelişkinin kaynağını boyut boyunca karşılaştırma |
| **Yazar** | Sadece doğrulanmış girdilerle (kaynak+kanıt+iddia) tez bölümlerini yazma |
| **Atıf Denetçisi** | Metin-kaynakça bütünlüğü, format, kaynak varlığı kontrolü |
| **Yöntem Denetçisi** | Araştırma sorusu ↔ yöntem uyumu (RQ2 nitel ama yöntem nicel → hata) |
| **Tutarlılık Denetçisi** | 20 madde: terminoloji, sayılar, tarihler, örneklem, yöntem, bulgular, sonuçlar, atıflar, bölümler arası referanslar, araştırma boşluğu |
| **Bütünlük Denetçisi** | Uydurma kaynak, kanıtsız iddia, geri çekilmiş kaynak kullanımı, kopuk atıf |

**Toplam: 10 ajan**

## P0-1: Çekirdek ve Veri Modeli

Bu katman, tezin tüm varlıklarını tanımlayan veri modelini ve bunu
doğrulayan çalıştırılabilir test altyapısını kurar.

### Doğruluk Kaynağı

Kalıcı varlıkların tek doğruluk kaynağı `schemas/*.json` dosyalarıdır
(JSON Schema draft 2020-12). Doğrulama `jsonschema` paketiyle yapılır.
Python tarafında şemaların kopyası tutulmaz; `tools/atw/` yalnızca
şemaları okur.

### Çalıştırma

```bash
pip install -r requirements.txt
python -m pytest -q
```

### Kimlik Standardı

`<PREFIX>-<NNN>` — üç haneli sıfır dolgulu. Prefiksler: `SRC`, `EVD`,
`CLM`, `CIT`, `P`, `RQ`, `HYP`, `FND`, `DSC`, `CON`, `GAP`, `AUD`,
`SEARCH`, `DS`, `ANL`, `STAT`, `TBL`, `FIG`.

### Ajanlar

| Ajan | Görev |
|------|-------|
| `researcher` | Kaynak keşfi ve arama stratejisi |
| `source-verifier` | Crossref + OpenAlex ile kaynak doğrulama |
| `evidence-extractor` | PDF'ten sayfa düzeyinde kanıt çıkarma |
| `gap-analyzer` | Araştırma boşluğu sınıflandırması |
| `contradiction-analyzer` | Çelişki tespiti ve boyut karşılaştırması |
| `writer` | Kanıt ve onay kapılarına bağlı yazım |
| `citation-auditor` | Atıf biçim ve tutarlılık denetimi |
| `methodology-auditor` | Yöntem–bulgu uyumu denetimi |
| `consistency-auditor` | Terminoloji, sayı, tarih tutarlılığı |
| `integrity-auditor` | Uydurma kaynak, kanıtsız iddia, retraksiyon denetimi |

## 📋 Kullanım

### Yeni Tez Başlatma

1. `schemas/thesis_state.json` dosyasını kopyalayın ve doldurun
2. Araştırma problemini ve sorularını tanımlayın
3. `workflows/thesis_creation.md` akışını takip edin

### Literatür Taraması (Sistematik İnceleme)

`workflows/systematic_review.md` protokolünü izleyin:

```
Araştırma Sorusu
  ↓
Arama Stratejisi → Veritabanları (Crossref, OpenAlex, Semantic Scholar, PubMed, Google Scholar)
  ↓
Dahil/Hariç Tutma Kriterleri → Tekrar Giderme
  ↓
Başlık/Özet Tarama → Tam Metin İnceleme
  ↓
Kalite Değerlendirme → Veri Çıkarımı → Sentez
```

Çıktılar: Literatür Matrisi, Kanıt Matrisi, Boşluk Analizi, Kalite Değerlendirme Raporu

### Bölüm Yazımı

Her bölüm için (`workflows/chapter_writing.md`):
1. Tez Durumu kontrolü
2. Kaynak/iddia denetimi
3. Paragraf metadata etiketleme (P-XXX)
4. Kalite kontrolü (akademik dil, mantıksal akış, kavramsal tutarlılık, RQ uyumu)

**Paragraf Yapısı:** İDDİA → KANIT → ANALİZ → BAĞLANTI

### Tez Denetimi

`workflows/thesis_audit.md` - 5 aşamalı denetim:
1. Yapısal Denetim (bölümler, RQ, hipotezler, metodoloji, sonuçlar)
2. Atıf Denetimi (eksik/fazla atıflar, doğrulanmamış kaynaklar, tutarsızlıklar)
3. Metodoloji Denetimi (tasarım, örneklem, veri toplama, analiz, geçerlik/güvenirlik)
4. Tutarlılık Denetimi (kavramlar, sayılar, tarihler, örneklem, yöntem-bulgular, bulgular-RQ, sonuçlar-bulgular)
5. Akademik Yazım Denetimi (dil, tekrar, mantık, üslup)

Çıktı: `templates/quality_report.md` formatında kapsamlı rapor

## 🔍 Özellikler

- ✅ **Kaynak doğrulama motoru**: Crossref + OpenAlex + Semantic Scholar (en az 2 bağımsız kaynak)
- ✅ **PDF → Kanıt sistemi**: Sayfa/bölüm/alıntı/yorum zinciri (İddia → Makale → Sayfa → Bölüm → Kanıt)
- ✅ **Araştırma Boşluğu Motoru**: Tema → Benzer/Çelişen → Eksiklikler → Boşluk (kanıtla)
- ✅ **Bilgi Grafiği**: 59 referans kenarı, 19 registry alanı; RQ → İddia → Kanıt → Kaynak → Bölüm → Paragraf → Atıf → Kaynakça + RQ → Yöntem → Analiz → Bulgular → Tartışma → Sonuç
- ✅ **Sistematik İnceleme Protokolü**: PRISMA uyumlu 11 aşamalı akış
- ✅ **Genişletilmiş Literatür Matrisi**: 19 sütun (Ülke, Tasarım, Bağımsız/Bağımlı Değişkenler, Alet, Analiz, Teorik Çerçeve, Kanıt Konumu)
- ✅ **Paragraf metadata**: P-XXX etiketleme ile iddia-kanıt-kaynak-RQ eşleşmesi
- ✅ **Çoklu atıf stili**: APA, MLA, Chicago, IEEE, Harvard
- ✅ **Tez Durumu persistence**: Oturumlar arası tutarlılık (JSON)
- ✅ **Orchestrator mimarisi**: SKILL koordinatör, 10 modüler ajan
- ✅ **4 araç arayüzü**: source_search, source_verify, pdf_extract, citation_check
- ✅ **4 bileşenli denetim**: Terminoloji, Sayılar, Örneklem, Yöntem-Bulgular
- ✅ **Kalite denetim raporu**: Yapısal, atıf, metodoloji, tutarlılık, akademik yazım

## 🚀 Başlangıç

```bash
# Repo'yu klonla
git clone https://github.com/latif-erdogdu/academic-thesis-writer.git

# Thesis State'i başlat (cross-platform)
python -c "import shutil; shutil.copy('schemas/thesis_state.json', 'thesis_state.json')"

# İlk tez için bilgileri doldur
# workflows/thesis_creation.md akışını takip et
```

## 📖 Dokümantasyon

- [SKILL.md](./SKILL.md) - Orchestrator: Agent mimarisi, mimari, bilgi grafiği, kurallar
- [agents/](./agents/) - 10 alt ajan tanımı
- [workflows/](./workflows/) - 8 çalışma akışı
- [templates/](./templates/) - 5 kullanıma hazır şablon
- [schemas/](./schemas/) - 21 veri şeması (JSON)
- [references/](./references/) - 7 akademik bütünlük referansı
- [tools/](./tools/) - 4 araç arayüzü
- [tests/](./tests/) - 5 test kategorisi

## 🤝 Katkı

Bu proje akademik dürüstlük ve kaynak doğrulanabilirliği ilkelerine bağlıdır. Katkı yapmadan önce:

1. Kaynak uydurma yapmayın
2. Mevcut mimariyi koruyun (Orchestrator + 10 ajan)
3. Thesis State tutarlılığını gözetin
4. Evidence Gate ve Writing Gate prensiplerine uyun
5. Testleri güncelleyin/ekleyin

## 📄 Lisans

Akademik kullanım için. Kaynak doğrulama ve akademik bütünlük kurallarına uyum zorunludur.

---

**Not**: Bu sistem metin üretimi hızından ziyade akademik kalite ve doğruluk odaklı tasarlanmıştır. Her önemli iddia mümkün olduğunda doğrulanabilir bir kaynağa dayanmalıdır. **AI detection/humanizer** odaklı değil; **akademik doğruluk + kaynak doğrulanabilirliği + metodolojik tutarlılık + şeffaflık** odaklıdır.