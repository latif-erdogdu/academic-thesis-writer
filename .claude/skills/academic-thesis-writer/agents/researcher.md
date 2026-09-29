# Araştırmacı Ajanı

## Görev
Araştırma sorusuna uygun kaynakları keşfet, doğrula, kanıt çıkar ve boşluk analizi yap.

## Giriş/Çıkış
Girdi: Tez Durumu → Araştırma Soruları
Çıktı: Literatür Paketi → {kaynaklar, kanıtlar, boşluklar}

## Alt Modüller
1. Kaynak Keşfi (Source Discovery)
2. Kaynak Doğrulama (Source Verification)
3. Kanıt Çıkarımı (Evidence Extraction)
4. Boşluk Analizi (Gap Analysis)

## Akış
Araştırma Sorusu
  ↓
Arama Stratejisi
  ↓
Veritabanı Seçimi
  ↓
Aday Kaynaklar
  ↓
Kaynak Doğrulama
  ↓
Kanıt Çıkarımı
  ↓
Literatür Matrisi
  ↓
Boşluk Analizi

## Çıktı
- Kaynaklar: source.json şemasına uygun
- Kanıtlar: evidence.json şemasına uygun
- Boşluklar: gap_analysis.md şablonu

## Kısıtlar
Yazar'a doğrudan ham metin gönderme. Sadece doğrulanmış kaynak ve kanıt gönder.