# Metodoloji Çalışma Akışı

## Genel Bakış
Bu çalışma akışı araştırma metodoloji bölümünüzün geliştirilmesini, katı ve savunulabilir metodolojik seçimler sağlayarak rehberlik eder.

## Aşama 1: Araştırma Tasarımı Seçimi

### Nicel Yaklaşımlar
- **Deneysel tasarım**: Kontrol grupları, randomizasyon
- **Anket araştırması**: Örnekleme stratejisi, ölçüm araçları
- **Veri analizi**: İstatistiksel yöntemler, yazılım paketleri
- **Geçerlilik ölçümleri**: İç/dış geçerlilik stratejileri

### Nitel Yaklaşımlar
- **Fenomenoloji**: Deneyimlerin derinlemesine anlaşılması
- **Etnografi**: Kültürel bağlam ve dalış
- **Olgu çalışması**: Belirli olgu(lar)ın ayrıntılı incelemesi
- **Yerel teori**: Veriden teori geliştirme
- **Geçerlilik ölçümleri**: Güvenilirlik, transfer edilebilirlik

### Karma Yöntemler
- **Eşzamanlı paralel**: Her ikisi toplanır, ayrı analiz edilir, sonuçlar birleştirilir
- **Açıklayıcı sıralı**: Nicel → Nitel açıklama için
- **Keşifsel sıralı**: Nitel → Nicel genelleme için

## Aşama 2: Veri Toplama Planlaması

### Örnekleme Stratejisi
```markdown
## Örnekleme Planı
### Evren
- Hedef evren tanımı
- Erişilebilirlik değerlendirmeleri

### Örnekleme Yöntemi
- Olasılıksal örnekleme: Basit tesadüfi, tabakalı, küme
- Olasılıksal olmayan: Amaçlı, kartopu, kolaylık (gerekçelendirin)

### Örneklem Büyüklüğü
- Gerekçe (nicel için güç analizi)
- Doyma noktası (nitel için)
- Dahil/hariç tutma kriterleri

### Veri Toplama Dönemi
- Başlangıç tarihi: YYYY-AA-GG
- Bitiş tarihi: YYYY-AA-GG
- Zaman aralığı gerekçesi
```

## Aşama 3: Ölçüm Araçları

### Nicel Ölçümler
```markdown
## Alet Tanımı
### Kavramsal Operasyonelleştirme
- [Kavram]: Nasıl ölçülür, neden bu ölçüm

### Ölçek/Alet Özellikleri
- Adı: [Alet adı]
- Geliştirici: [Kim geliştirdi]
- Madde sayısı: Soru sayısı
- Yanıt formatı: Likert aralığı, çoktan seçmeli, vb.
- Güvenirlik (α): Daha önce belirlenmiş veya pilot test edilmiş
- Geçerlilik kanıtı: İçerik, yapısal, kriter
```

### Nitel Ölçümler
```markdown
## Görüşme Rehberi / Odak Grup Protokolü
### Araştırma Soruları (görüşme için)
1. [Soru 1]
2. [Soru 2]
3. [Soru 3]

### Soru Geliştirme
- Literatür incelemesi bulgularından türetilmiş
- Mümkünse pilot görüşmelerde test edilmiş
- Açık uçlu vs. spesifik sorular

### Görüşme Lojistiği
- Beklenen süre: X dakika
- Format: Yüz yüze, sanal, hibrit
- Kayıt izinleri alındı
```

## Aşama 4: Veri Analiz Planı

### Nicel Analiz
```markdown
## İstatistiksel Analiz Planı
### Yazılım
- Birincil: [SPSS/R/Python/Stata/vb.]
- İkincil: [Uygunsa]

### Prosedürler
1. Betimsel istatistikler
2. Varsayım kontrolleri (normalite, homoskedastisite)
3. Çıkarımsal testler (t-test, ANOVA, regresyon, vb.)
4. Etki büyüklüğü hesaplamaları
5. Uygunsa duyarlılık analizleri
```

### Nitel Analiz
```markdown
## Nitel Analiz Yaklaşımı
### Yazılım (uygunsa)
- NVivo, MAXQDA, Dedoose, veya manuel kodlama

### Kodlama Süreci
1. Veriyle tanışma
2. Başlangıç/açık kodlama
3. Tema/kategori geliştirme
4. Tema iyileştirme ve doğrulama
5. İllüstrasyon için alıntı seçimi

### Katılık Ölçümleri
- Üye kontrolü
- Akran danışmanlığı
- Kalıntı betimleme
- Denetim izi
```

## Aşama 5: Etik Hususlar

### Gerekli Belgeler
- ETK/Etik kurul onay durumu
- Aydınlatılmış onay prosedürleri
- Veri gizliliği ve güvenliği önlemleri
- Hassas bilgi işleme
- Çıkar çatışması açıklaması

## Aşama 6: Geçerlilik ve Güvenirlik Stratejileri

### Nicel
- İç geçerlilik kontrolleri
- Dış geçerlilik stratejileri (genelleme)
- Ölçüm güvenirlik belgelenmesi
- Yanıt önyargısı azaltma

### Nitel
- Güvenilirlik stratejileri (triangülasyon, üye kontrolü)
- Transfer edilebilirlik (kalıntı betimleme)
- Bağlanılabilirlik (denetim izi)
- Onaylanabilirlik (refleksivite bildirimi)

## Aşama 7: Zaman Çizelgesi ve Kilometre Taşları

```markdown
## Metodoloji Uygulama Zaman Çizelgesi
| Görev | Süre | Başlangıç Tarihi | Bitiş Tarihi |
|------|----------|------------|----------|
| [Görev 1] | X hafta | YYYY-AA-GG | YYYY-AA-GG |
| [Görev 2] | X hafta | | |
```

## Çıktı Ürünleri
Bu çalışma akışı şunu üretmelidir:
1. Tam metodoloji bölümü taslağı
2. Yöntem detaylarıyla güncellenmiş `schemas/thesis_state.json`
3. Veri toplama araçları (anketler, görüşme rehberleri)
4. Etik onay belgeleri referansı

## Kalite Kontrol Listesi
- [ ] Araştırma tasarımı gerekçelendirilmiş ve uygun
- [ ] Örnekleme stratejisi net tanımlanmış
- [ ] Ölçüm araçları doğrulanmış
- [ ] Analiz planı ayrıntılı
- [ ] Etik hususlar adreslenmiş
- [ ] Geçerlilik/güvenirlik stratejileri belirtilmiş
- [ ] Zaman çizelgesi gerçekçi ve ulaşılabilir
- [ ] Tüm kaynaklar `references/citation_rules.md` per atıflanmış

## Sonraki Adımlar
Metodoloji tamamlandıktan sonra:
1. Metodoloji bölümünü gözden geçirin ve sonlandırın
2. Veri toplama başlatın (uygunsa)
3. Bölüm yazımı için `workflows/chapter_writing.md` akışına geçin