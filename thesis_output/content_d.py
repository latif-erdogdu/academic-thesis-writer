# -*- coding: utf-8 -*-
"""Tez icerigi bolum 4: Turkce ozet, Ingilizce abstract, icindekiler, tesekkur."""

OZET_TR = [
    ("h1", "ÖZET"),
    ("p",
     "Bu çalışmada, insan beyninin ve düşüncelerinin yazılımla okunması "
     "konusu dört boyutlu bir çerçevede incelenmiştir: nörobilimsel temeller, "
     "yapay zekâ destekli çıkarım, klinik uygulamalar ve etik-hukukî sınırlar. "
     "Yöntem olarak nitel kaynak temelli derleme kullanılmıştır; çalışma "
     "Crossref ve OpenAlex veri tabanlarında kaydedilmiş bir arama "
     "protokolüne dayanır. Kaynakların bağımsız DOI doğrulaması bu "
     "sürümde tamamlanamamış olup tespit edilen araç kusurları EK-2'de "
     "belgelenmiştir; bu nedenle kaynakça DOI'siz bırakılmıştır."),
    ("p",
     "Bulgular şu başlıklar altında özetlenmiştir. Birincisi, beyin-bilgisayar "
     "arayüzü (BCI) bir algılama aracı değil, kapalı bir geri bildirim "
     "sistemidir; başarı, sinyal kalitesi kadar kullanıcı deneyimi ve eğitim "
     "süreciyle belirlenir. İkincisi, derin öğrenme ve dönüştürücü mimariler "
     "EEG çıkarımında gerçek kazançlar sağlamakta; ancak bu kazançların "
     "çoğu aynı kanal sayısı, aynı filtre ve aynı bölme protokolüne dayanan "
     "karşılaştırmalardan gelmektedir, bu nedenle alanın ilerlemesi büyük "
     "ölçüde veri ve karşılaştırma protokollerinin zayıflığından kaynaklanmaktadır. "
     "Üçüncüsü, klinik yararlılık teknolojinin karmaşıklığıyla değil, klinik "
     "gereksinim ile teknolojik sınırlar arasındaki eşleşmeyle ölçülmektedir; "
     "iletişim sistemlerinde bu eşleşme en yüksek, tanı ve tıbbi karar desteği "
     "alanlarında ise henüz kurulmamıştır. Dördüncüsü, BCI'nin asıl etik "
     "gerilimi veri gizliliğini aşarak zihinsel özgürlüğü ilgilendirmektedir."),
    ("p",
     "Çalışma, kişisel nöral verinin duyarlı kişisel veri statüsüyle "
     "korunması, model eğitimi için ayrı rıza, alt grup performansının "
     "raporlanması ve sistem sınırlarının kullanıcıya açıklanması yönünde "
     "yedi ilkeden oluşan bir düzenleyici çerçeve önermektedir. Çalışma nicel "
     "ampirik veri üretmemiş, açık erişime açık kaynaklarla sınırlı kalmıştır."),
    ("table", [
        ["Anahtar Kelimeler", "Keywords"],
        ["Beyin-bilgisayar arayüzü, EEG, derin öğrenme, yapay zekâ, "
         "nöroetik, veri gizliliği, motor imajineri",
         "Brain-computer interface, EEG, deep learning, artificial "
         "intelligence, neuroethics, data privacy, motor imagery"],
    ]),
    ("caption", "Tablo 0.1. Anahtar kelimeler."),
]

ABSTRACT_EN = [
    ("h1", "ABSTRACT"),
    ("p",
     "This thesis examines the problem of reading the human brain and its "
     "thoughts with software along four dimensions: neuroscientific "
     "foundations, artificial-intelligence-assisted inference, clinical "
     "applications, and ethical-legal limits. The study is a qualitative "
     "narrative literature review grounded in a registered search protocol "
     "across Crossref and OpenAlex. Independent DOI verification of the cited "
     "works could not be completed in this version; the tool defects "
     "encountered are documented in Appendix 2, and the reference list is "
     "therefore left without DOIs."),
    ("p",
     "The findings are summarised as follows. First, a brain-computer "
     "interface (BCI) is not a perception device but a closed feedback system: "
     "performance is determined by signal quality as much as by user "
     "experience and training protocol. Second, deep learning and "
     "transformer architectures yield genuine gains in EEG inference; however, "
     "most reported gains derive from comparisons that share the same channel "
     "count, filtering, and split protocol, so field progress is driven "
     "largely by weaknesses in data and benchmarking practice rather than by "
     "saturated algorithmic capacity. Third, clinical benefit is governed by "
     "the fit between clinical need and technical limits, not by the technical "
     "sophistication of the system; this fit is highest for communication "
     "applications and still unestablished for diagnosis and medical decision "
     "support. Fourth, the principal ethical tension in BCI transcends data "
     "privacy and concerns cognitive liberty."),
    ("p",
     "The thesis proposes a seven-principle regulatory framework: treating "
     "personal neural data as sensitive personal data, requiring separate "
     "consent for model training, reporting performance across subgroups, "
     "and disclosing system limitations to users. The study does not generate "
     "quantitative empirical data and is limited to openly accessible sources."),
    ("table", [
        ["Keywords", ""],
        ["Brain-computer interface, EEG, deep learning, artificial "
         "intelligence, neuroethics, data privacy, motor imagery", ""],
    ]),
]

ICINDEKILER = [
    ("h1", "İÇİNDEKİLER"),
    ("toc", [
        ("ÖZET", "i"),
        ("ABSTRACT", "ii"),
        ("İÇİNDEKİLER", "iii"),
        ("TABLO LİSTESİ", "iv"),
        ("ŞEKİL LİSTESİ", "v"),
        ("KISALTMALAR LİSTESİ", "vi"),
        ("1. GİRİŞ", "1"),
        ("1.1. Konunun Önemi ve Kapsamı", "1"),
        ("1.2. Problem Durumu", "2"),
        ("1.3. Amaç", "3"),
        ("1.4. Araştırma Soruları", "3"),
        ("1.5. Hipotezler", "4"),
        ("1.6. Yöntem", "5"),
        ("1.7. Çalışmanın Katkısı", "6"),
        ("1.8. Kapsam ve Sınırlar", "6"),
        ("2. BEYİN-BİLGİSAYAR ARAYÜZÜ TEKNOLOJİLERİ", "7"),
        ("2.1. Tarihsel Gelişim", "7"),
        ("2.2. Tanım ve Sınıflandırma", "9"),
        ("2.3. Sinyal Alım Yöntemleri", "11"),
        ("2.4. Sinyal İşleme Zinciri", "13"),
        ("2.5. Evrensel BCI Kavramı", "15"),
        ("3. YAPAY ZEKÂ DESTEKLİ NÖRAL SİNYAL İŞLEME", "17"),
        ("3.1. Geleneksel Yöntemler ve Temel Sınırları", "17"),
        ("3.2. Derin Öğrenme: Mimari Duruş", "18"),
        ("3.3. Öğrenme Stratejileri", "20"),
        ("3.4. Değerlendirme Sorunları", "22"),
        ("3.5. Açıklanabilirlik Sorunu", "23"),
        ("3.6. Değerlendirme ve Ara Boşluk", "25"),
        ("4. KLİNİK UYGULAMALAR", "26"),
        ("4.1. Uygunluk Kriterleri", "26"),
        ("4.2. İletişim Kurtarma Sistemleri", "27"),
        ("4.3. Hareket Kontrolü ve Rehabilitasyon", "29"),
        ("4.4. Nörodejeneratif Hastalıklar", "30"),
        ("4.5. Kognitif Yardım ve Sağlıklı Bireyler", "31"),
        ("4.6. Performans Değerlendirme Metrikleri", "32"),
        ("4.7. Karşılaştırmalı Kanıt Değerlendirmesi", "33"),
        ("5. ETİK, HUKUKÎ VE TOPLUMSAL BOYUTLAR", "34"),
        ("5.1. Çerçevenin Değişmezleri", "34"),
        ("5.2. Veri Gizliliği ve Mülkiyet", "35"),
        ("5.3. Nöroözerki", "37"),
        ("5.4. Adalet ve Erişilebilirlik", "38"),
        ("5.5. Bilişsel Özgürlük", "39"),
        ("5.6. Sosyal ve Psikolojik Etkiler", "40"),
        ("5.7. Düzenleyici Çerçeve Olarak Öneri", "41"),
        ("6. GELECEK PERSPEKTİFLERİ", "43"),
        ("6.1. Yaklaşan ve Uzak Alan", "43"),
        ("6.2. Öngörülen Teknik Yönelimler", "44"),
        ("6.3. Olası Riskler", "45"),
        ("6.4. Araştırma Öncelikleri", "46"),
        ("SONUÇ", "47"),
        ("KAYNAKÇA", "49"),
        ("EKLER", "53"),
    ]),
]

TESEKKUR = [
    ("h1", "TEŞEKKÜRLER"),
    ("p",
     "Bu çalışmanın hazırlanması sürecinde destek veren herkese teşekkür "
     "ederim. Kaynakların erişilebilirliğini sağlayan açık erişim "
     "platformları, bu alandaki bilginin yayılmasında belirleyici olmuştur. "
     "Ayrıca erken taslak aşamasındaki okuma ve geri bildirimleriyle çalışmaya "
     "katkı verenlere teşekkür ederim."),
]
