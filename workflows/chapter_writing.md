# Bölüm Yazımı Çalışma Akışı

## Genel Bakış
Bu çalışma akışı tez bölümlerinin sistematik ve tutarlı şekilde yazılmasını sağlar. Her bölüm Tez Durumu ile uyumlu olmalı ve kaynak/iddia takibi gerektirir.

## Ön Koşullar
- `schemas/thesis_state.json` başlatılmış ve temel bilgiler doldurulmuş olmalı
- `templates/thesis_structure.md` gözden geçirilmiş olmalı
- Literatür araştırması tamamlanmış olmalı

## Bölüm Yazımı Adımları

### Adım 1: Bölüm Hazırlığı
1. Mevcut `thesis_state.json`'ı kontrol et
2. Bölüm hedeflerini belirle
3. Gerekli kaynakları ve iddiaları tanımla
4. Bölüm şablonu oluştur

### Adım 2: Taslak Oluşturma
1. Bölüm yapısını oluştur (alt başlıklar)
2. Her alt başlık için ana iddiaları belirle
3. İddia → Kaynak bağlantısını kur
4. Taslak metni yaz

### Adım 3: Kaynak Entegrasyonu
1. Her iddia için kaynak doğrula
2. Metin içi atıfları ekle
3. Kaynakça listesini güncelle
4. Atıf-kaynakça uyumunu kontrol et

### Adım 4: Kalite Kontrolü
1. Akademik dil kontrolü
2. Mantıksal akış denetimi
3. Kavramsal tutarlılık kontrolü
4. Araştırma sorusuyla uyum kontrolü
5. Tekrar kontrolü

### Adım 5: Bölüm İçi Metadata Etiketleme
Her paragraf için içsel olarak etiketle:
```
P-XXX
Type: İDDİA / KANIT / ANALİZ / BAĞLANTI
Claim: ...
Evidence: SRC-XXX
Citation: APA
Confidence: DOĞRULANDI / BEKLEYEN / DOĞRULANAMADI
Chapter: X
Section: X.Y
```

## Bölüm Başına Kontrol Listesi

- [ ] Akademik dil kullanılmış
- [ ] Mantıksal akış var
- [ ] Kaynaklandırma tamamlanmış
- [ ] Kaynak doğruluğu kontrol edilmiş
- [ ] Kavramsal tutarlılık sağlanmış
- [ ] Araştırma sorusuyla uyum var
- [ ] Metodolojik uyum var
- [ ] Tekrar kontrolü yapılmış
- [ ] Veri doğruluğu sağlanmış
- [ ] Atıf-kaynakça uyumu kontrol edilmiş

## Bölüm Yazımı İpuçları

### Paragraf Yapısı
Her paragraf tek ana düşünce etrafında kurulmalı.

**Kullanılacak yapı:**
```
İDDİA → KANIT → ANALİZ → BAĞLANTI
```

### Yazım Stili
- Açık ve sistematik
- Nesnel
- Terminolojik olarak tutarlı
- Gereksiz tekrar içermeyen
- Kanıta dayalı

### Bölümler Arası Tutarlılık
- Önceki bölümlerle çelişme olmamalı
- Tanımlar tutarlı kullanılmalı
- Sayılar aynı şekilde verilmeli
- Örneklem büyüklüğü sabit kalmalı

## Çıktı Formatı
```
Bölüm Başlığı
Alt Başlık

Akademik metin.

Alt Başlık

Akademik metin.

Kaynaklandırma
```

## Sonraki Adım
Bölüm yazımı tamamlandıktan sonra:
1. Bölüm arası tutarlılık denetimi yap
2. Tez Durumu'nu güncelle
3. Gerekirse düzeltme yap
4. Sonraki bölüme geç