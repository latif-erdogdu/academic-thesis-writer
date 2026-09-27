# -*- coding: utf-8 -*-
"""Tez icerigi bolum 1: on bilgiler, Giris (B1), BCI teknolojileri (B2).

Her ogge (tur, metin) tuple'idir:
  ("h1", metin) / ("h2", metin) / ("p", metin) / ("bullet", metin)
  / ("table", [[hucre, ...], ...]) / ("quote", metin) / ("caption", metin)
"""

FRONT = [
    ("baslik", "INSAN BEYNININ VE DUSUNCELERININ YAZILIMLA OKUNMASI"),
    ("altbaslik",
     "Norobilimsel sinyal isleme, yapay zeka destekli cikarim ve etik "
     "sinirlarin birlikte incelenmesi"),
    ("tur", "Yuksek Lisans Tezi"),
    ("tur", "Program: Bilgisayar Muhendisligi / Bilişim Sistemleri"),
    ("tur", "Danışman: —"),
    ("tur", "Yil: 2026"),
]

# ---------------------------------------------------------------- B1 GIRIS
B1 = [
    ("h1", "BİRİNCİ BÖLÜM"),
    ("h1", "GİRİŞ"),

    ("h2", "1.1. Konunun Önemi ve Kapsamı"),
    ("p",
     "Beyin-bilgisayar arayuzu (brain-computer interface, BCI), canli bir organizmanin "
     "merkezi sinir sistemi ile harici bir hesaplama birimi arasinda dogrudan iletisim "
     "kuran sistemler icin kullanilan genel terimdir. Bu terim alti ana ozelligi tanimlar: "
     "(a) iletisim kanalinin fiziksel olarak baska bir ortamdan gecmesi, (b) ozel bir ozel "
     "lendirme protokolunun bulunmasi, (c) cikarimin basinda kullanicinin niyetinin yer "
     "almasi, (d) cikarim sonucunun kullaniciya geri bildirilmesi ve (e) sistemin ogrenme "
     "sureci icinde bireysel kullanicilik ozelestirilmesi. Bu bes ozelligin birlikte "
     "bulunmasi, BCI'yi yalnizca bir girdi-ikti cihazindan ayirir ve onu bir "
     "durusum-aktarim sistemi haline getirir."),
    ("p",
     "Konunun onemi uc ayri katmandan gelir. Birincisi, BCI teknolojileri motor "
     "norejeneneratif hastaliklar ve felc sonrasi iletisim kaybi olan bireyler icin "
     "pratik bir kurtarma araci sunar. Ikincisi, ayni teknolojiler saglikli bireylerde "
     "bilişsel yardim, dikkat artirma ve rehabilitasyon amaciyla kullanilmaya "
     "baslamistir; bu durum klinik siniri asipla sorusunu gündeme getirmektedir. "
     "Uçuncusu, okunan verinin gercekten bir düşünce olup olmadigi meselesi, dogasin "
     "tanimina ve makine ogrenmesinin sinirlarina dayanan teknik bir sorunun yaninda "
     "felsefi ve hukuki bir soruna donusmektedir."),
    ("p",
     "Bu calisma konunun dort temel boyutunu birlikte ele alir: norobilimsel temeller "
     "(Bolum 2), yapay zeka destekli cikarim yontemleri (Bolum 3), klinik uygulamalar "
     "(Bolum 4) ve etik-hukuki sinirlar (Bolum 5). Bolum 6 ise gelecek yonelimleri "
     "degerlendirir. Yontem olarak nitel kaynak temelli derleme benimsenmistir; calisma "
     "yalnizca literaturde kanitlanmis bulgularla sinirli kalmakta, ozgun ampirik veri "
     "uretmemektedir."),

    ("h2", "1.2. Problem Durumu"),
    ("p",
     "Kamusal alanda BCI teknolojileri hakkinda yaygin iki sey karsilasmaktadir. "
     "Birincisi, teknolojinin düşünce okuma kapasitesine sahip oldugu yonundeki "
     "populer anlati. Bu anlati, felc ve norodejeneratif hastalarda gercekten var olan "
     "hos bir uygulamayi, saglikli bireylerde her turlu zihinsel icerigi isleyebilen "
     "bir sistem imajina donusturur. Ikincisi, teknolojinin klinik gecerliligi "
     "konusundaki asiri iyimserlik. Ikincisi, alanda gorulen gercek sinirlamalari "
     "gormezden gelir: gozleme yuzeyi yogunlugu, sartlara bagli performans, egitim "
     "surelerinin uzunlugu ve klinik ortam ile laboratuvar arasindaki "
     "aktarilabilirlik acigi."),
    ("p",
     "Bu ispatlanmamis iyimserlik, uygulamada iki somut risk dogurur. Ilki, hasta ve "
     "hasta ailelerinin beklentilerinin gercekci olmayan bir seviyeye cekilmesi ve "
     "klinik kararlarin gercekci olmayan beklentiler uzerine kurulmasi. Ikincisi, "
     "mevzuat ve etik cercevelerin vaatlerden hareketle degil, fiili klinik "
     "yeteneklerden hareketle tasarlanmasi. Bu iki risk, konunun yalnizca teknik "
     "degil, ayni zamanda yonetimsal ve etik bir problem oldugunu gosterir."),

    ("h2", "1.3. Amaç"),
    ("p",
     "Calismanin amaci su dordur:"),
    ("bullet",
     "BCI sistemlerinin temel siniflandirmasini ve sinyal alim yontemlerinin "
     "klinik-ozel iliskilerini ortaya koymak;"),
    ("bullet",
     "Modern makine ogrenmesi ve derin ogrenme yontemlerinin noral sinyal cikarimina "
     "katkisini, elde edilen kazanimlar ve sinirlamalarla birlikte degerlendirmek;"),
    ("bullet",
     "BCI'nin klinik uygulamalardaki kanit temelini ve yararlilik sinirlarini "
     "degerlendirmek;"),
    ("bullet",
     "Bireysel verinin zihinsel icerik olarak okunmasi meselesinin etik, hukuki ve "
     "toplumsal sonuclarini analiz etmek."),

    ("h2", "1.4. Araştırma Soruları"),
    ("p",
     "Calisma su arastirma sorularini yanitlamaya calisir:"),
    ("bullet",
     "RQ-001. Yapay zeka destekli sinyal isleme, BCI tabanli siniflandirma "
     "sistemlerinde geleneksel yontemlere gore ne olcude dogruluk ve dayaniklilik "
     "kazanci saglamaktadir?"),
    ("bullet",
     "RQ-002. EEG tabanli gecirimsiz BCI sistemlerinin klinik uygulamalardaki "
     "gercek basari oranlari ve basarisi sinirlandiran etkenler nelerdir?"),
    ("bullet",
     "RQ-003. Saglikli bireylerde kognitif yardim amacli BCI uygulamalari, hasta "
     "grubundaki klinik uygulamalardan hangi yonlerle ayrilsir ve ayrilmaktadir?"),
    ("bullet",
     "RQ-004. Noroveri meselesi, veri sahipligi ve erisim denetimi bakimindan "
     "mevcut hukuki ve etik cerceveler BCI'ye ne olcude uyumludur?"),

    ("h2", "1.5. Hipotezler"),
    ("p",
     "Bu calisma nicel bir ampirik arastirma olmadigi icin deneysel hipotez "
     "testi yapilmaz. Bunun yerine literaturde gozlenen ve birbirleriyle yarisan "
     "iddialar, inceleme hipotezi (H) olarak asagida ifade edilir; her biri "
     "inceleme bolumunde kanitla karsilastirilir."),
    ("table", [
        ["No", "Inceleme Hipotezi", "Yonelim"],
        ["H-1",
         "Derin ogrenme, geleneksel siniflandirici kombinasyonlari uzerinde "
         "olculu bir dogruluk kazanci saglar; ancak bu kazanc klinik "
         "uygulamaya tasinabilir degildir.",
         "Kismen desteklenir"],
        ["H-2",
         "Basarili BCI uygulamalarinin ortak ozelligi, sinyal kalitesinden cok "
         "kullanici deneyimi ve ogitim surelerinin uzunlugudur.",
         "Desteklenir"],
        ["H-3",
         "Etik ve hukuki tartisma, veri gizliligi cercevesinde toplanirken "
         "asil gerilimi zihinsel ozgurlugu ilgilendirir.",
         "Desteklenir"],
    ]),
    ("caption", "Tablo 1.1. Inceleme hipotezleri ve degerlendirme yonelimi."),

    ("h2", "1.6. Yöntem"),
    ("p",
     "Calisma nitel kaynak temelli derleme (narrative literature review) yontemiyle "
     "yurutulmustur. Yontem iki asamali ve acikca sinirli birakilmistir. Birinci "
     "asamada veri tabanlari (Crossref, OpenAlex) uzerinden taranmis arama "
     "protokolu kaydi olusturulmus ve dahil etme-disiar etme kriterleri "
     "uygulanmistir. Ikinci asamada atifta bulunulan kaynaklarin DOI ve yazar "
     "bilgileri uzerinden dogrulama modulunden gecirilmistir. Bu asama "
     "tamamlanamamis ve tespit edilen arac kusurlari EK-2'de belgelenmistir; "
     "dolayisiyla bu calismada hicbir kaynak 'dogrulanmis' olarak isaretlenmemis, "
     "kaynakca bilincli olarak DOI'siz birakilmistir."),
    ("p",
     "Yontemin sinirlari acikca belirtilmelidir. Birincisi, calisma yalnizca acik "
     "erişime sahip Ingilizce ve Turkce literaturle sinirlidir; konu alani genis "
     "oldugundan bu bir eksikliktir. Ikincisi, incelenen calismalarda yayinlanma "
     "yanliligi (olumlu sonuc gosteren calismalarin daha fazla yayinlanmasi) "
     "kontrol edilememistir. Ucuncusu, BCI alanindaki teknik ilerleme hizli "
     "oldugundan bazi tespitlerin calisma tarihi itibariyle gecmis olabilir."),

    ("h2", "1.7. Çalışmanın Katkısı"),
    ("p",
     "Calismanin beklenen katkisi sudur: teknik yetenek sinirlari ile etik-hukuki "
     "beklentiler arasindaki boslugu tek bir cercevede gostermek; BCI uygulamalari "
     "icin acele karar vermeyi engelleyen bir karar cercevesi sunmak; ve "
     "zihinsel veri korumasi icin somut bir politika cercevesi onerisi gelistirmek. "
     "Calisma ozgun ampirik veri uretmez ve klinik karar yerine gecmez."),

    ("h2", "1.8. Kapsam ve Sınırlar"),
    ("p",
     "Calisma invaziv sistemleri yalnizca ilke duzeyde ele alir; cerrahi detay ve "
     "klinik protokol bilgisi disarida birakilmistir. Elektriksel beyin aktivitesi "
     "odakli alinmistir; MEG ve fNIRS yontemleri yalnizca karsilastirma amaciyla "
     "gecmektedir. Sagligli bireylerde uygulanan ticari urunler yalnizca risk "
     "analizi cercevesinde ele alinmistir; belirli bir urun icin yazilim tanitimi "
     "veya kullanilabilirlik degerlendirmesi yapilmamistir."),
]

# ------------------------------------------------- B2 BCI TEKNOLOJILERI
B2 = [
    ("h1", "İKİNCİ BÖLÜM"),
    ("h1", "BEYİN-BİLGİSAYAR ARAYÜZÜ TEKNOLOJİLERİ"),
    ("h2", "2.1. Tarihsel Gelişim"),
    ("p",
     "BCI dusuncesinin dogrudan deneysel kokleri 1920'lere dayanir. Hans Berger, "
     "insan elektroensefalografisini (EEG) kaydeden ilk sistemi gelistirdi ve "
     "calismalari, beyin aktivitesinin kaydedilip analiz edilebilecegini "
     "gosterdi. Berger'in kayitlari 1924'te bir insan uyaranlara bagli olarak "
     "belirgin bir elektriksel cevap urettigini ortaya koydu. 1930'larda Edgar "
     "Adrian ve GVL Basoline okuma, noral ritmin bir olcum araci degil, "
     "beynin uyaniklik durumunu yansitan bir fizyolojik surec oldugunu "
     "gostererek EEG'nin islevsel yorumunu baslatti."),
    ("p",
     "Bilgisayar teknolojisinin devreye girdigi donem 1970'lerdir. Jacques "
     "Vidal'in 1973 tarihli calismasi, bir insanin komut sinyali olarak "
     "kullanilabilecek sinirsel bir dalga formu tespit etmesi ve bu dalgadan "
     "hareketle bir bilgisayar imlecinin yonlendirilebilecegini gostermesiyle "
     "alanin kurucu metni kabul edilir. Vidal'in bulgusu bugunku BCI sistemlerinin "
     "temis ettigi iki temel varsayimi — cikarim bir siniflandirma problemidir ve "
     "ogrenme kullaniciya gore uyarlanabilir — birlikte kurmustur."),
    ("p",
     "1990'larda bir baska kilometre tasi aydinlatildi: beyin bir bilgisayara "
     "komut gonderen bir cevre degil, ortamdan bagimsiz bir tus olarak "
     "kullanilabilir. Nierenberg ve colleagues'in P300 tabanli yazim sistemi, "
     "katilimci kullaniciya belirli harflerin zihinsel olarak "
     "vurgulanmasini (oddball paradigm) ve uyaranla eslesen bir zihinsel "
     "olcume bagli olarak harfi secmesini mumkun kildi. Bu calisma, "
     "beyin-bilgisayar iletisimin 'okuma' degil, 'evrenme' problemi oldugunu "
     "gostererek sonraki iki dekatrin yol haritasini belirledi."),
    ("p",
     "2000'li yillarda alan kurumsallaşti. 2002'de Wolpaw ve arkadaslari BCI "
     "sistemlerini siniflandiran ve alanin ortak dilini belirleyen bir cerceve "
     "yayimladi. Ayni donemde klinik uygulamalar dogrulandi: BrainGate ekibi "
     "felc hastalarinda istenen hareketin sinirsel oncusunu tespit ederek "
     "robotik kolu kontrol etmeyi basardi. Uc boyutlu baskilar arayan ve "
     "hedefi sifirlanan geri besleme araclarinin gelistirilmesi, BCI'yi "
     "laboratuvar nesnesi olmaktan cikarip kullanici odakli bir asistif teknoloji "
     "haline donusturdu."),
    ("p",
     "2010'lardan itibaren iki belirgin yonelim birlikte ilerledi. Birincisi, "
     "derin ogrenmenin devreye girmesiyle siniflandirma performansindaki "
     "artistir. Ikinccisi, gozleme gecirimsiz (portable) sistemlerin yayginlasmasi "
     "ve tuketici elektroneurologisi (consumer neurotechnology) kavraminin "
     "dogmasi. 2019'daki bir derleme, ozellikle invaziv goruntu motoru yorumlama "
     "calismalarinda tek katilimli derin mimarilerin cok katmanli modelleri "
     "gectigini ve bircok calismada karsilastirma metodolojisinin zayif kaldigini "
     "bildirmistir. 2020'li yillar ise alanin metodolojik olgunlasmasiyla "
     "nispeten ayirt edilebilir: onayli calisma tasarimi, raporlanma "
     "standartlari ve klinik kanit toplama gereklilikleri konusunda belirgin "
     "bir farkindalik olusmustur."),

    ("h2", "2.2. Tanım ve Sınıflandırma"),
    ("h2", "2.2.1. BCI Teknolojisi Nedir?"),
    ("p",
     "Bir BCI sistemi, merkezi sinir sistemi ile harici bir sistem arasindaki "
     "iletisimi, biyolojik olmayan bir cikti ve girdi yoluyla saglayan sistemdir. "
     "Bu tanim, yalnizca 'beyin okuyan' cihazlari kapsamaz; tersine, cihazin "
     "beyne geri bildirim gonderdigi cift yonlu sistemleri de kapsar. Geri "
     "bildirim dongusu bir BCI'yi pasif bir kaydediciden ayiran temel ozelliktir: "
     "kullanici, sistemin cikarimini gorerek kendi ciktisini ayarlar ve sistem "
     "bu ayarlamaya gore guncellenir."),
    ("p",
     "Siniflandirmada iki kriter kullanilir. Birincisi, ornekleme yontemidir. "
     "Invaziv sistemler elektrotlari dogrudan korteks veya korteks yuzeyine "
     "yerlestirir; gecirimsiz sistemler elektrotlari kafa derisinden disarida "
     "tutar. Ikincisi, geri bildirimin dogasidir: geri besleme (kullanici kendi "
     "motor ciktisini gorur) veya geri beslemesiz (yalnizca bilgi dondurulur) "
     "sistemler. Bu iki kriter birlikte dordlu bir siniflandirma uretir."),

    ("h2", "2.2.2. Sınıflandırma Tablosu"),
    ("table", [
        ["Sinif", "Ornekleme", "Geri Bildirim", "Guclu Yönü", "Zayif Yönü"],
        ["Invaziv (implant)",
         "Korteks / korteks yuzeyi",
         "Hareket geri besleme",
         "Yuksek sinyal-gurultu orani",
         "Cerrahi risk, uzunsureli kabul sorunu"],
        ["Yari invaziv",
         "Korteks uzeri elektrot (ECoG)",
         "Hareket geri besleme",
         "Yuksek cozunurluk, goruntu hareketi",
         "Cerrahi gerektirir, sinirli sure"],
        ["Gecirimsiz (EEG)",
         "Kafa derisi disi",
         "Geri besleme / geri beslemesiz",
         "Non-invaziv, ucuz, tekrar edilebilir",
         "Dusuk sinyal-gurultu, cografi sinirli"],
        ["Hibrit / pasif",
         "Implant + gecirimsiz",
         "Geri besleme",
         "Aktif ve pasif bolgeleri birlikte cikarir",
         "En yuksek maliyet, en yuksek entegrasyon riski"],
    ]),
    ("caption", "Tablo 2.1. BCI sistemlerinin siniflandirmasi."),

    ("h2", "2.3. Sinyal Alım Yöntemleri"),
    ("h2", "2.3.1. Elektriksel Yöntemler"),
    ("p",
     "Elektriksel kayit, beyin aktivitesinin en yaygin ve en ucuz kaydedilme "
     "bicimidir. Elektrot yuzeyiyle elektrolit arasi iletkenlik sayesinde hucre "
     "disi akim potansiyelleri olculur. Olcumun gucu, once frekans bant genisligi, "
     "sonra uzaysal cozunurluk sirasiyla azalir: EEG genis bantli ve yuksek "
     "uzaysal cozunurluktur, ECoG daha dar bantli ve daha iyi cozunurluktur, "
     "intrakortikal kayit ise en dar bantli ve en yuksek cozunurluktur."),
    ("p",
     "EEG'de gozleme, yalnizca alinabilen sinyali degil, ayni zamanda "
     "konumlandirilabilen sinyali ifade eder. Iki temel yaklasim vardir. Birincisi "
     "sebilimsel (spatial filter) tabanli yaklasimdir: gozleme, ozellik vektorler "
     "uzerinden kanal agirliklarinin hesaplanmasi ile yapilir. Ortak Ortak Uzaysal "
     "Desenler (CSP) ve bunun varyantlari bu ailedendir. Ikincisi, kafa derisinin "
     "hacim iletkenligi nedeniyle sinyallerin karistigini kabul edip modelleme "
     "temelli (kaynak yerellestirme, ters modelleme) yaklasimdir. Iki yaklasim "
     "birlikte kullanilabilir; ilki iyi ozellik ayrimi, ikincisi fizyolojik "
     "yorumluluk saglar."),

    ("h2", "2.3.2. Kayıt Kalitesi ve Yüz Yüklemesi"),
    ("p",
     "Gecirimsiz kayitta en belirleyici sinirlandirma yuz yuklemesidir. Elektrot "
     "sayisi dogrusal olarak artsa bile, elektrot sayisinin karesiyle orantili "
     "serbestlik derecesi sinirli kaldigi icin ozelliklerin belirginligi "
     "sinirlanir. Ayrica kirpma, goz kaslari aktivitesi ve terleme kaynakli "
     "hareket artefaktlari sinyali bozar. Bu nedenle konumlandirilabilir ve "
     "guclendirilmis elektrotlar, yogun montajlara gore uygulamalarda tercih "
     "edilebilir."),
    ("p",
     "Artefakt yonetimi, BCI sureclerinin ayrilmaz parcasidir. Goz kaslari "
     "aktivitesi aslinda sinyali degil, ortam bilgisini tasir; bu nedenle "
     "dogru bir tanimlayici (ornegin yatay goz hareketi ile zihinsel "
     "kosullulandirma) artefakti bilgiye cevirebilir. Buna karsilik, kirpma "
     "gibi kaynaklardan gelen artefaktlar kirpma kanalindan tasinan ikinci bir "
     "elektrotla veya Empedans (bimodul) esikleriyle bastirilir."),

    ("h2", "2.4. Sinyal İşleme Zinciri"),
    ("p",
     "Bir BCI cikarim zinciri tipik olarak yedi asamadan olusur ve her asamadaki "
     "tasarim karari toplam performansi belirler."),
    ("bullet",
     "(1) On isleme: filtreleme, yeniden ornekleme, kanallarin secimi ve "
     "artefakt bastirma."),
    ("bullet",
     "(2) Ozellik cikarimi: zaman alani (gucluk, varyans, istatistikler), frekans "
     "alani (bant gucu, oransal bant gucu) ve zaman-frekans alani (kisa zamanli "
     "Fourier donusumu, dalgacik) temelli ozellikler."),
    ("bullet",
     "(3) Ozellik secimi ve boyut azaltma: bilgi kazani oranlari, isabetli "
     "secilim, kabalestirme veya ogrenmeye dayali gomulu yontemler."),
    ("bullet",
     "(4) Siniflandirma: dogrusal diskriminant analizi, destek vektor makineleri, "
     "lojistik regresyon, rastgele orman ve derin ogrenme."),
    ("bullet",
     "(5) Uc durumlu cikarim: sistem yalnizca iki sinif arasinda karar vermek "
     "zorunda degildir; bir durusma araliginda (bkz. sabit durus, hazir, "
     "tetikleme) kalmasina izin vermek, kontrol yukunu azaltir."),
    ("bullet",
     "(6) Geri besleme araci: sanal imlec, gercek zamanli gorsel geri bildirim, "
     "sonuc yanlis oldugunda duzeltme hakki."),
    ("bullet",
     "(7) Uyarlama ve ogitim: sistemin kullanicidan gore guncellenmesi."),
    ("p",
     "Iki ek parametre her tasarimi belirler. Ilki gecikmisiz, ikincisi "
     "kararliliktir. BCI sistemlerinin en sik tartisilan ikilemi budur: kisa "
     "gecikmeli sistemler hizli hissettirir ama hatali karar oranini artirir; "
     "kararli sistemler hatayi azaltir ama kullaniciyi yorar ve akisindan cikarir. "
     "Bu nedenle 'dogru cevap' sorusu kadar 'kullanilabilir cevap' sorusu da "
     "onemlidir."),

    ("h2", "2.5. Evrensel BCI Kavramı"),
    ("p",
     "Her kullaniciya uygun tek bir sistem olmadigi gorulunca, alanda evrensel "
     "(universal) BCI kavrami gelistirildi. Evrensel BCI, kullanicinin egitim "
     "verilmeden, hatta bilincli komut uretmeden sistemi kullanabilmesi hedefini "
     "taser. Buna ulasmak iki zorluk barindirir. Ilki, orn. kafatasindaki "
     "anatomik ve elektrofizyolojik farkliliklarin kanal kaliplarini ve ozellik "
     "dagilimlarini degistirmesidir; bu, sabit bir oznitelik uzayinin her "
     "kullaniciya tasinamamasina yol acar. Ikincisi, bireysel oznitelik "
     "uzaylarinin veri azligi nedeniyle kararli olmamasidir."),

    ("p",
     "Bu zorluklara yonelik iki strateji belirginlesti. Birincisi, veri "
     "augmentasyonu ve alan uyarlamasi (domain adaptation): kaynak kullanicidan "
     "hedef kullaniciya transfer yaparak etiketsiz hedef veriden yararlanir. "
     "Ikinccisi, dikkat mekanizmasi ve transformer temelli zaman-serisi modelleri: "
     "cift yonlu (encoder-decoder) mimariler sinyali iki yonden isleme ve "
     "zaman bagimliliklarini modelleme yetenegi kazandirir. Her iki yonelim de "
     "onerilen etiklik ve klinik gecerlilik sorunlarini cozmemektedir."),
]
