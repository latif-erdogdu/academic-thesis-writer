# Kaynak Doğrulama Rehberi

## Amaç
Teze kullanılan tüm kaynakların güvenilir, erişilebilir ve akademik çalışma için uygun olmasını sağlamak.

## Doğrulama Kontrol Listesi

### Her Kaynak İçin
- [ ] **Yazar güvenilirliği**: Yazar alanda nitelikli/uzman mı?
- [ ] **Yayın yeri**: Hakemli mi, güvenilir bir yayınevi mi?
- [ ] **Tarih güncelliği**: Konu için yeterince güncel mi?
- [ ] **Erişilebilirlik**: Tam metin yasal yollarla erişilebilir mi?
- [ ] **Atıf bütünlüğü**: Atıf detayları tam ve doğru mu?

### Güvenilirlik Göstergeleri
#### Güçlü İşaretler (Dahil Et)
- Hakemli dergide yayınlanmış
- Üniversite basımevi veya akademik yayınevi tarafından yayınlanmış
- Yazarın ilgili kimlik bilgileri var (Doktora, profesor, araştırmacı)
- Kurum bağlamı açık
- DOI atanmış
- Diğer güvenilir kaynaklar tarafından atıflanmış

#### Zayıf İşaretler (Dikkatli kullanın veya hariç tutun)
- İncelemesiz kendi yayınladığı blog yazısı
- Yazar listelenmemiş
- Yayınevi bilinmiyor
- Aşırı reklam içeriyor
- Sadece ücretli duvar arkasında erişilebiliyor
- Aynı içeriğe birden fazla URL işaret ediyor

### Kırmızı Bayraklar (Hariç Tut)
- Birincil kaynak olarak Vikipedi (yerine orijinal kaynağı kullanın)
- Avcı dergiler
- İçeriği etkileyen açık ticari önyargılı siteler
- Zaman-hassas konularda güncelliği yitirilmiş bilgi
- Doğrulanamaz iddialar veya istatistikler
- Kırık linkler veya eksik sayfalar

## Kaynak Kategorileri

### Birincil Kaynaklar
- Orijinal araştırma makaleleri
- Resmi raporlar
- Nüfus sayımı verileri
- Arşiv materyalleri
- Doğrudan gözlem/deneyler

### İkincil Kaynaklar
- Derleme makaleler
- Ders kitapları
- Akademik kitaplar
- Birincil kaynaklar üzerindeki yorumlar

### Üçüncül Kaynaklar (Az kullanın)
- Ansiklopediler
- Sözlük girişleri
- Özet siteler

## Doğrulama Süreci

### Adım 1: İlk Değerlendirme
```markdown
Kaynak Adı: [Link/Başlık]
Yayın Tarihi: YYYY-AA-GG
Yazar: Ad, kimlik bilgileri
Yayıncı: Kurum adı
URL: DOI varsa tam URL
```

### Adım 2: Kalite Kontrolleri
- Hakemli bildirimi kontrol et
- Yayınevi itibarını doğrula
- Yazar bağlamlarını onayla
- Atıf geçmişini incele
- Potansiyel önyargıları değerlendir

### Adım 3: Çapraz Referans
- Bu esere yapılan atıfları ara
- Aynı konudaki diğer otoriter kaynaklarla karşılaştır
- Kaynağın büyük derlemeler/kitaplarda atıflanıp atıflanmadığını kontrol et

### Adım 4: Erişilebilirlik
- Tam metne erişebiliyor musunuz?
- DOI çözümlenebiliyor mu?
- Ücretli duvar kısıtlamaları var mı?

## Yaygın Yanlışlar

### Bu Hatalardan Kaçının
1. **Atıf zincirleme**: Her zaman orijinal kaynağı bulun ve atıflayın
2. **İkincil kaynaklara aşırı güvenme**: Birincil materyalleri arayın
3. **Yayın tarihini göz ardı etme**: Alan-spesifik güncelik ihtiyaçları değişir
4. **Ön baskıları eleştirisiz kabul etme**: Uygunsa "hakkailememiş" olarak belirtin
5. **Eksik atıf öğeleri**: Tüm gerekli alanların tamamlandığından emin olun

### Özel Durumlar
- **Konferans bildirileri**: Hakemli olabilirler ama mekan kalitesini doğrulayın
- **Çalışma kağıtları**: Önelimin olarak işaretleyin; nihai yayınlanmış versiyonu arayın
- **ArXiv ön baskıları**: Atıflarda durumu net belirtin
- **Gri literatür**: Sınırlılıkları olmasına rağmen neden uygun olduğunu belgelendirin

## Belgeler Şablonu
```markdown
## Kaynak: [Tam atıf]
### Doğrulama Durumu: ✓ Onaylandı / ⚠ Dikkatli kullan / ✗ Reddedildi
### Güçlü Yönler:
- [Güçlü yön 1]
- [Güçlü yön 2]
### Sınırlılıklar:
- [Sınırlılık 1]
- [Sınırlılık 2]
### Bulunan alternatif kaynaklar:
- [Alternatif 1]
- [Alternatif 2]
```

## Tez Yazarı ile Entegrasyon
Sistem otomatik olarak:
1. Tez ilerledikçe tüm kaynakları etiketler
2. Doğrulama bekleyen kaynakları işaretler
3. Her bölüm için doğrulama raporları üretir
4. İlgili doğrulanmış kaynaklara çapraz referanslar oluşturur