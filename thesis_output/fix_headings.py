# -*- coding: utf-8 -*-
"""Basliklari Turkce karakterli ve numaralandirmali bicime cevirir.

Kullanim: python thesis_output/fix_headings.py
Idempotenttir: ikinci calistirmada degisiklik yapmaz.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Eski (ASCII) baslik -> Yeni (Turkce) baslik
HARITA: dict[str, str] = {
    "BIRINCI BOLUM": "BİRİNCİ BÖLÜM",
    "GIRIS": "GİRİŞ",
    "IKINCI BOLUM": "İKİNCİ BÖLÜM",
    "BEYIN-BILGISAYAR ARAYUZU TEKNOLOJILERI": "BEYİN-BİLGİSAYAR ARAYÜZÜ TEKNOLOJİLERİ",
    "UCUNCU BOLUM": "ÜÇÜNCÜ BÖLÜM",
    "YAPAY ZEKA DESTEKLI NORAL SINYAL ISLEME VE DUSUNCE COZME":
        "YAPAY ZEKÂ DESTEKLİ NÖRAL SİNYAL İŞLEME VE DÜŞÜNCE ÇÖZME",
    "DORDUNCU BOLUM": "DÖRDÜNCÜ BÖLÜM",
    "KLINIK UYGULAMALAR: NORODEJENERATIF HASTALIKLAR, FELC VE ILETISIM BOZUKLUKLARI":
        "KLİNİK UYGULAMALAR: NÖRODEJENERATİF HASTALIKLAR, FELÇ VE "
        "İLETİŞİM BOZUKLUKLARI",
    "BESINCI BOLUM": "BEŞİNCİ BÖLÜM",
    "ETIK, HUKUKI VE TOPLUMSAL BOYUTLAR": "ETİK, HUKUKÎ VE TOPLUMSAL BOYUTLAR",
    "ALTINCI BOLUM": "ALTINCI BÖLÜM",
    "GELECEK PERSPEKTIFLERI": "GELECEK PERSPEKTİFLERİ",
    "SONUC": "SONUÇ",
}

# "1.1  Konunun Onemi ve Kapsami" gibi tek sayili numarali basliklar
IKILI = re.compile(r'^(?P<no>\d)\.(?P<no2>\d)(?P<bos>  +)(?P<metin>.+)$')
UCULU = re.compile(r'^(?P<no>\d)\.(?P<no2>\d)\.(?P<no3>\d)(?P<bos> +)(?P<metin>.+)$')

DUZELTMELER = {
    "Konunun Onemi ve Kapsami": "Konunun Önemi ve Kapsamı",
    "Amac": "Amaç",
    "Arastirma Sorulari": "Araştırma Soruları",
    "Yontem": "Yöntem",
    "Calismanin Katkisi": "Çalışmanın Katkısı",
    "Kapsam ve Sinirlar": "Kapsam ve Sınırlar",
    "Tarihsel Gelisim": "Tarihsel Gelişim",
    "Tanim ve Siniflandirma": "Tanım ve Sınıflandırma",
    "Siniflandirma Tablosu": "Sınıflandırma Tablosu",
    "Sinyal Alim Yontemleri": "Sinyal Alım Yöntemleri",
    "Elektriksel Yontemler": "Elektriksel Yöntemler",
    "Kayit Kalitesi ve Yuz Yuklemesi": "Kayıt Kalitesi ve Yüz Yüklemesi",
    "Sinyal Isleme Zinciri": "Sinyal İşleme Zinciri",
    "Evrensel BCI Kavrami": "Evrensel BCI Kavramı",
    "Geleneksel Yontemler ve Temel Sinirlari": "Geleneksel Yöntemler ve Temel Sınırları",
    "Derin Ogrenme: Mimari Durus": "Derin Öğrenme: Mimari Duruş",
    "Girdi Temsilleri": "Girdi Temsilleri",
    "Uygulanan Mimariler": "Uygulanan Mimariler",
    "Ogrenme Stratejileri": "Öğrenme Stratejileri",
    "Degerlendirme Sorunlari": "Değerlendirme Sorunları",
    "Aciklanabilirlik Sorunu": "Açıklanabilirlik Sorunu",
    "Degerlendirme ve Ara Bosluk": "Değerlendirme ve Ara Boşluk",
    "Uygunluk Kriterleri": "Uygunluk Kriterleri",
    "Iletisim Kurtarma Sistemleri": "İletişim Kurtarma Sistemleri",
    "Hareket Kontrolu ve Rehabilitasyon": "Hareket Kontrolü ve Rehabilitasyon",
    "Norodejeneratif Hastaliklar": "Nörodejeneratif Hastalıklar",
    "Kognitif Yardim ve Saglikli Bireyler": "Kognitif Yardım ve Sağlıklı Bireyler",
    "Performans Degerlendirme Metrikleri": "Performans Değerlendirme Metrikleri",
    "Karsilastirmali Kanit Degerlendirmesi": "Karşılaştırmalı Kanıt Değerlendirmesi",
    "Cercevenin Degismezleri": "Çerçevenin Değişmezleri",
    "Veri Gizliligi ve Mülkiyet": "Veri Gizliliği ve Mülkiyet",
    "Noroveri: Beyin Ozelligi mi, Kisisel Veri mi?":
        "Nöroözerki: Beyin Özelliği mi, Kişisel Veri mi?",
    "Adalet ve Erisilebilirlik": "Adalet ve Erişilebilirlik",
    "Bilisiksel Ozgurluk": "Bilişsel Özgürlük",
    "Sosyal ve Psikolojik Etkiler": "Sosyal ve Psikolojik Etkiler",
    "Duzenleyici Cerceve Olarak Oneri": "Düzenleyici Çerçeve Olarak Öneri",
    "Yaklasan ve Uzak Alan": "Yaklaşan ve Uzak Alan",
    "Ongorulenen Teknik Yonelimler": "Öngörülen Teknik Yönelimler",
    "Olasi Riskler": "Olası Riskler",
    "Arastirma Oncelikleri": "Araştırma Öncelikleri",
    "Veri Tabani ve Arama Protokolu Ozeti": "Veri Tabanı ve Arama Protokolü Özeti",
    "Kaynak Dogrulama Kaydi": "Kaynak Doğrulama Kaydı",
    "Kisaltmalar": "Kısaltmalar",
}


def duzelt(metin: str) -> str:
    if metin in HARITA:
        return HARITA[metin]
    m = UCULU.match(metin)
    if m:
        yeni = DUZELTMELER.get(m.group("metin"), m.group("metin"))
        return f'{m.group("no")}.{m.group("no2")}.{m.group("no3")}. {yeni}'
    m = IKILI.match(metin)
    if m:
        yeni = DUZELTMELER.get(m.group("metin"), m.group("metin"))
        return f'{m.group("no")}.{m.group("no2")}. {yeni}'
    return DUZELTMELER.get(metin, metin)


def main() -> int:
    kok = Path(__file__).resolve().parent
    toplam = 0
    for ad in ("content_a.py", "content_b.py", "content_c.py"):
        yol = kok / ad
        kaynak = yol.read_text(encoding="utf-8")
        satirlar = kaynak.splitlines(keepends=True)
        yeni_satirlar = []
        for satir in satirlar:
            m = re.match(r'^\s*\("h[12]", "(?P<metin>[^"]+)"\),?\s*$', satir)
            if m:
                hedef = duzelt(m.group("metin"))
                if hedef != m.group("metin"):
                    satir = satir.replace(f'"{m.group("metin")}"', f'"{hedef}"')
                    toplam += 1
            yeni_satirlar.append(satir)
        yeni = "".join(yeni_satirlar)
        if yeni != kaynak:
            yol.write_text(yeni, encoding="utf-8")
    print(f"{toplam} baslik duzeltildi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
