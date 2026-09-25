# Literatür Taraması Çalışma Akışı

## Genel Bakış
Bu çalışma akışı tez konunuzdaki mevcut araştırmaların sistematik incelemesini ve sentezlenmesini sağlar.

## Aşama 1: Konu Tanımı
### Kapsam Belirleme
- **Araştırma alanı**: Alan/etki alanını netleştirin
- **Temel kavramlar**: Çekirdek terminolojiyi belirleyin
- **Sınırlar**: Dahil etme/hariç tutma kriterlerini belirtin

### Arama Stratejisi
1. Akademik veritabanları (Google Scholar, Scopus, Web of Science)
2. Konferans bildirileri
3. Uygun olduğunda gri literatür
4. Alandaki anahtar yazarlar ve temel eserler

## Aşama 2: Kaynak Toplama
### Minimum Gereksinimler
- **Temel makaleler**: Temel eserler (öncelik verin)
- **Yayınlar**: Mümkünse son 5 yıl
- **Yöntemsel çeşitlilik**: Uygunsa birden fazla yaklaşım
- **Coğrafi/zamansal kapsam**: İlgiliyse net sınırlar

### Toplama Şablonu
```markdown
## Kaynak Girişi
### Atıf: [Tam atıf]
### İlgililik puanı: Yüksek/Orta/Düşük
### Temel katkı: [1-2 cümle]
### Metodoloji türü: [Nicel/Nitel/Karma]
### Tarih: YYYY
### Durum: ✓ Doğrulandı / ⚠ İnceleme gerekli / ✗ Atıldı
```

## Aşama 3: Sentez Matrisi
`templates/literature_matrix.md` kullanarak literatür matrisi oluşturun:

### Yapı
```markdown
# Literatür İnceleme Matrisi
## Konu Alanı
| Yazar (Yıl) | Temel Bulgular | Metodoloji | Sınırlılıklar | İlgililik Puanı |
|---------------|-------------|--------------|-------------|-----------------|
|               |             |              |             |                 |

## Belirlenen Temalar
1. Tema 1: [Özet]
2. Tema 2: [Özet]
3. Tema 3: [Özet]

## Belirlenen Boşluklar
- Boşluk 1: [Mevcut araştırmada eksik olan]
- Boşluk 2: [Daha fazla araştırma gerektiren]
- Boşluk 3: [Katkı fırsatları]
```

## Aşama 4: İnceleme Bölümü Yazımı
### Bölüm 1: Literatür Taramasına Giriş
- İnceleme amacı
- Kapsam ve organizasyon
- Seçim kriterleri

### Bölüm 2: Tematik Organizasyon
- Kaynakları kronolojik olarak değil, tematik olarak gruplayın
- Her tema içinde: sadece listelemeyin, sentezleyin
- Desenleri, çelişkileri, boşlukları belirleyin

### Bölüm 3: Eleştirel Analiz
- Metodolojik yaklaşımları karşılaştırın
- Kanıt gücünü değerlendirin
- Mevcut çalışma sınırlılıklarını belirtin
- Araştırmanızı manzarada konumlandırın

### Bölüm 4: Boşluk Belirleme
- Araştırma boşluklarını netleştirin
- Boşlukları araştırma sorularıyla bağlayın
- Bu tezin nasıl adreslediğini gerekçelendirin

## Aşama 5: Tez Durumu ile Entegrasyon
`schemas/thesis_state.json` şunu güncelleyin:
- Literatür tarama tamamlanma durumu
- Belirlenen temel temalar
- Belgelendiği boşluklar
- Doğrulanmış kaynak sayısı

## Kalite Kontrol Listesi
- [ ] Tüm kaynaklar düzgün atıflanmış
- [ ] Literatür kapsamında boşluk yok
- [ ] Temalar netleştirilmiş
- [ ] Eleştirel analiz var (sadece özet değil)
- [ ] Boşluklar araştırma sorularıyla net bağlantılı
- [ ] Literatür matrisi tamamlanmış ve doğru
- [ ] Tüm kaynaklar `references/source_verification.md` doğrulanmış

## Sonraki Adımlar
Literatür taraması tamamlandıktan sonra:
1. Tez durum dosyasını güncelleyin
2. Literatür bulgularına dayanarak metodolojiyi tanımlayın
3. `workflows/methodology.md` akışına geçin