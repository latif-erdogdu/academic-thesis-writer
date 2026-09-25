# Tez Oluşturma Çalışma Akışı

## Genel Bakış
Bu çalışma akışı literatür incelemesi, metodoloji ve yazım aşamalarını entegre ederek kapsamlı bir akademik tezin uçtan uca oluşturulmasını koordine eder.

## Ön Koşullar
Bu çalışma akışını çalıştırmadan önce:
- ✓ Literatür taraması tamamlandı (`workflows/literature_review.md`)
- ✓ Araştırma metodolojisi sonlandırıldı (`workflows/methodology.md`)
- ✓ Bölüm yapısı tanımlandı

## Yürütme Sırası
1. Literatür Sentez Analizi → `literature_matrix.md` çıktısı
2. Metodoloji Planlaması → `methodology_state.json` güncellemeleri
3. Tez Yapısı Oluşturma → `templates/thesis_structure.md` kullanarak
4. Bölüm Bazlı Yazım → `workflows/chapter_writing.md` üzerinden
5. Entegrasyon ve Sentez → Tüm bölümleri giriş/sonuç ile birleştir
6. Kalite İncelemesi → `workflows/thesis_audit.md` çalıştır

## Durum Yönetimi
Durum şurada takip edilir:
- `schemas/thesis_state.json` - Genel ilerleme ve metadata
- `references/source_verification.md` - Kaynak kalite takibi

## Çalışma Akışı Adımları

### Adım 1: Literatür Sentezi
```markdown
## Bölüm 1: Giriş
- Araştırma arka planı
- Problem durumu
- Araştırma soruları/amaçları
- Çalışmanın önemi
- Tez yapısına genel bakış

Bkz: tasarım için templates/thesis_structure.md
```

### Adım 2: Metodoloji Entegrasyonu
- Metodoloji bölümü çıktısını gözden geçirin
- Araştırma tasarımıyla tutarlılığı sağlayın
- Araştırma sorularıyla uyumu doğrulayın

### Adım 3: Bulgular ve Tartışma Üretimi
- Literatür içgörülerini bulgularla entegre edin
- Tüm iddiaların düzgün atıflandığından emin olun
- Doğrulanmış kaynakları çapraz referanslayın

### Adım 4: Sonuç Sentezi
- Ana katkıları özetleyin
- Her araştırma sorusunu adresleyin
- Etkileri ve sınırlılıkları tartışın
- Gelecek araştırma yönlerini önerin

## Çıktı Yapısı
```
Tez/
├── 01_Giris.md
├── 02_Literatur_Taramasi.md
├── 03_Yontem.md
├── 04_Bulgular.md
├── 05_Tartisma.md
├── 06_Sonuc_Oneri.md
├── Kaynarca.bib
└── Kalite_Raporu.md
```

## Atıf Entegrasyonu
- Tüm iddialar atıflanmalı (bkz `references/citation_rules.md`)
- Tüm kaynakları kaynak doğrulama kontrol listesiyle doğrulayın
- Tutarlı atıf stilini tez boyunca koruyun

## Kalite Kapıları
Bölümler arası geçişten önce:
1. Önceki bölümü tamamlanma açısından gözden geçirin
2. Atıf doğruluğunu kontrol edin
3. Durum dosyasının güncellendiğini doğrulayın (`schemas/thesis_state.json`)
4. Bölümler arası sorunsuz geçişleri sağlayın

## Sonraki Adım
Tez oluşturma tamamlandıktan sonra denetim çalışma akışını çalıştırın:
```bash
# Tez denetimini çalıştır
workflows/thesis_audit.md
```