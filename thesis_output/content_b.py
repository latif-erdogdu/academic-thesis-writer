# -*- coding: utf-8 -*-
"""Tez icerigi bolum 2: YZ algoritmalari (B3), klinik uygulamalar (B4)."""

# --------------------------------------------- B3 YZ DESTEKLI ISLEME
B3 = [
    ("h1", "ÜÇÜNCÜ BÖLÜM"),
    ("h1", "YAPAY ZEKÂ DESTEKLİ NÖRAL SİNYAL İŞLEME VE DÜŞÜNCE ÇÖZME"),
    ("h2", "3.1. Geleneksel Yöntemler ve Temel Sınırları"),
    ("p",
     "BCI siniflandirmasinda geleneksel yaklasim, karar fonksiyonunu basit ve "
     "ozellik uzayinda dogrusal varsayar. En yaygin kullanilan ozellik cikarimi "
     "yontemi Ortak Ortak Uzaysal Desenlerdir (Common Spatial Patterns, CSP). "
     "CSP, iki sinif arasindaki varyans farkini maksimize eden ve sinif "
     "ortalarini birlestiren bir cift yonlu projeksiyon bulur. Dusuk sinif "
     "sayili, iyi ozellik ayrimi olan problemlerde CSP tabanli sistemler, "
     "dogrusal diskriminant analizi ile birlikte hala guclu bir kiyas olcusudur."),
    ("p",
     "Ancak bu yontemlerin dort temel siniri vardir."),
    ("bullet",
     "(i) Ozellik uzayi zorunludur. Sistem yalnizca onceden secilmis ozellikler "
     "uzerinden ogrendigi icin, secim yanlissa performans tavana carpar."),
    ("bullet",
     "(ii) Bilgi kazanimi yoktur. Ozellik cikarimi, siniflandiricidan bagimsiz "
     "ve gozlemeden bagimsiz yapildigi icin ogrenme ile ozellikler arasindaki "
     "Uyusmazlik dogrudan gozlenmez."),
    ("bullet",
     "(iii) Sabit uzunluk penceresi kullanilir. Zaman-frekans ozelliklerde "
     "pencere boyu sabit tutuldugu icin, kisa sureli ve uzun sureli noral "
     "olaylar ayni cozunurlukte temsil edilir."),
    ("bullet",
     "(iv) Istatistiksel varsayimlardir. Cikarinim modelleri suphesiz dagilim "
     "ve sinif dengesi varsayimina dayanir; gercek EEG verisi ikisini de "
     "ihlal eder."),
    ("p",
     "Bu sinirlar, BCI'de derin ogrenmeye ilgiyi artirmis ve bu ilgi literaturde "
     "belirgin bir sekilde buyumustur."),

    ("h2", "3.2. Derin Öğrenme: Mimari Duruş"),
    ("h2", "3.2.1. Girdi Temsilleri"),
    ("p",
     "Derin ogrenme modellerinin girdi temsili, BCI'de en kritik tasarim "
     "kararidir ve literaturde en az model mimarisi kadar tartisilmistir. Bes "
     "ana yaklasim vardir."),
    ("table", [
        ["Temsil", "Girdi Sekli", "Avantaj", "Dezavantaj"],
        ["Ham zaman serisi",
         "[kanal x zaman]",
         "Bilgi kaybi yok",
         "Ogrenmesi zor, veri sinirli"],
        ["Zaman-frekans (STFT)",
         "[kanal x zaman x frekans]",
         "Zamani frekans ile eslestirir",
         "Pencere secimi kritik"],
        ["Dalgacik (wavelet)",
         "[kanal x zaman x olcek]",
         "Cok olceklilik, zaman-ozel",
         "Analitik islem maliyeti"],
        ["Tuketilmis ozellik haritasi",
         "[ozellik x kanal]",
         "Ritim ve muzikalik iliskiler",
         "Bicimsel bilgi kaybi"],
        ["Kafes tabanli ogrenme",
         "[kanal x zaman x frekans]",
         "Uzaysal-zamansal birliktelik",
         "Hesaplama yogun"],
    ]),
    ("caption", "Tablo 3.1. BCI'de derin ogrenme girdi temsilleri."),

    ("h2", "3.2.2. Uygulanan Mimariler"),
    ("p",
     "Bozulmus siniftan ogrenme (BOS) tabanli konvolusyonel sinir aglari, EEG "
     "verisinde en yaygin kullanilan mimaridir. Temel fikir, konvolusyon "
     "katmanlarinin hem zaman hem de frekans ekseninde yerel desenleri "
     "cevirdigi ve siniflandirma katmanina kadar bu desenlerin hiyerarsisini "
     "kurdugudur. Derin konvolusyonel sinir aglari (DKSA) bu temele ek olarak "
     "her katmanda ozellik haritalarini ilerleterek, ozellik cikarimi ile "
     "siniflandirmayi birlikte ogrenen butunlesik bir model kurar. Bir "
     "sonraki adim olarak, ozellik haritalarinin kanal uzayinda ozellestirilmesi "
     "(KSA = kanal-uzay-sel ozelliklestirme) eklenmistir; bu asama, EEG'de "
     "kanallar arasindaki bolgesel iliskilerin modele girmesini saglar."),
    ("p",
     "Bunun yaninda iki farkli yonelim gelismistir."),
    ("bullet",
     "Graf tabanli sinir aglari: kanal iliskilerini bir komsuluk grafinda "
     "temsil ederek, elektrot konumundan gelen ek bilgiyi modele entegre eder. "
     "Bu yaklasim, anatomik komsulugun sinif ayrimina katkida bulundugu icin "
     "ozellikle yakin elektrotlarda kaydedilen cozunurluk dusuk sinyallerde "
     "avantajlidir."),
    ("bullet",
     "Donusumcu (transformer) tabanli modeller: cok basli ozdikkat "
     "mekanizmasiyla kanal ve zaman boyutlarindaki uzak bagimliliklari yakalar. "
     "EEG ozgelliginde, zaman-serisi modellerinin goruntu modellerine gore "
     "belirgin bir basari farki gosterdigini ortaya koyan ilk calisma 2021'de "
     "yayimlanmis ve alanin yonunu degistirmistir."),

    ("h2", "3.3. Öğrenme Stratejileri"),
    ("p",
     "Veri miktarindan cok, verinin nasil kullanildigi belirleyicidir. BCI'de "
     "her kullanici icin etiketli veri sinirli oldugundan, transfer ve "
     "yararlanma temelli stratejiler temel tasarim kararidir."),
    ("table", [
        ["Strateji", "Yaklasim", "Gereksinim", "Klinik Uygunluk"],
        ["Denetimli ogrenme",
         "Etiketli veri ile dogrudan egitim",
         "Yeterli oturum (>= 20)",
         "Orta"],
        ["Transfer ogrenme",
         "Onceden egitilmis agin yeni kullaniciga uyarlanmasi",
         "Hedef veri (az etiketle)",
         "Yuksek"],
        ["Oykulmus ogrenme",
         "Etiketli/etiketsiz verinin birlikte kullanilmasi",
         "Yeterli etiketsiz veri",
         "Orta-yuksek"],
        ["Yari-denetimli ogrenme",
         "Sinif etiketlerinin kismi kullanimi",
         "Kismi etiket",
         "Orta"],
        ["Kendi kendine denetimli ogrenme",
         "Cift goruntu kullanimi, etiketsiz veriden temsil ogrenme",
         "Yeterli etiketsiz veri",
         "Yuksek"],
        ["Federe ogrenme",
         "Cihazda yerel egitim, merkezi biriktirme olmadan",
         "Ortak model yapisı",
         "Yuksek (gizlilik)"],
    ]),
    ("caption", "Tablo 3.2. Ogrenme stratejileri ve klinik uygulanabilirlik."),
    ("p",
     "Kendi kendine denetimli ogrenme, EEG verisinin en dogru kozmetigi oldugu "
     "gercegine dayanir: iki kanal goruntusu, ortak bir temsil cikarim "
     "olusturacaktir. Bu strateji, 2023 yilinda yayimlanan kapsamli bir "
     "taramada, denetimli ogrenmenin hala cogu calismada esas yontem oldugunu "
     "ancak kendi kendine denetimli ogrenmenin metriklerde rekabet ciddi "
     "oldugunu gostererek raporlamistir. Federe ogrenme ise saglik "
     "verisinin gizlilik kisitlari nedeniyle BCI alaninda giderek daha fazla "
     "onem kazanmaktadir: model, hastane sinirlarindan cikmadan kurulabilmektedir."),

    ("h2", "3.4. Değerlendirme Sorunları"),
    ("p",
     "BCI'de derin ogrenme literaturunun en ciddi yarasi, metodolojiktir. "
     "Asagidaki sorunlar gozlemlenmistir."),
    ("bullet",
     "(1) Karsilastirmali benchmark eksikligi: cok sayida calisma, verisini "
     "ozel olarak biriktirdigi bir veri kumesiyle, sozde gercek zamanli "
     "(pseudo-online) donguyle, ciddi bir temel cizgi (baseline) olmadan "
     "sunmaktadir."),
    ("bullet",
     "(2) Uzerinde cikis (overfitting) ve tekrar kullanim (leakage): ozellik "
     "secimi ve hiperparametre ayari ayni dogrulama kumesinde yapildiginda, "
     "test sonuclari sistematik olarak iyimserlesir."),
    ("bullet",
     "(3) Kucuk ornek sorunu: onlarca katilimciden olusan veri kumesi, milyonlarca "
     "parametreli bir agin genellenmesi icin yetersizdir; bircok calisma bu "
     "nedenle az parametreli ya da transfer ogrenmeye dayali modellerle "
     "karsilastirilmayi tercih etmektedir."),
    ("bullet",
     "(4) Kisitli gercekcilik: laboratuvar verisi, gercek kullanimdaki dikkat "
     "dagilimi, yorgunluk ve ev ortami degiskenlerini yansitmaz."),
    ("p",
     "Bu sorunlara karsi gelistirilen onlemler onceden test edilmis protokol, "
     "bagimsiz test kumesi, yeterli katilimci sayisi ve onceden kaydedilmis "
     "analiz planidir. Alanin olgunlasmasi, bu onlemlerin zorunlu hale "
     "gelmesiyle olcumlenmektedir."),

    ("h2", "3.5. Açıklanabilirlik Sorunu"),
    ("p",
     "Derin ogrenme modellerinin klinik kullanima en onemli engeli aciklanabilirlik "
     "eksikligidir. Bir siniflandiricinin 'sol el hareketi' sinifini neden "
     "secer bilmek, sistemin guvenilirligi icin zorunludur; aksi halde hata "
     "teshisi ve hasta oncesi bilgilendirme mümkün degildir. Bu alanda "
     "gelistirilen yaklasimlar su yoneldedir."),
    ("bullet",
     "Girdi katmani aciklanabilirligi: modelin hangi zaman araliklarina ve "
     "hangi frekans bantlarina duyarli oldugunu gosterir; alan saglamligi (spatial "
     "sensitivity) haritalari burada uretilir."),
    ("bullet",
     "Deger temelli aciklamalar: her bir ozniteliin karara katkisini dortlu "
     "degerlerle (W, S, B, E) raporlar."),
    ("bullet",
     "Konsept tabanli aciklamalar: model kararini, insan tarafindan anlasilir "
     "klinik ozelliklerle baglar; orn. 'guc artisi ve yavaslatma' veya "
     "'motor hazirlik mufredati'."),
    ("bullet",
     "Surekli izleme (monitoring) tabanli aciklamalar: gercek kullanim sirasinda "
     "performans dususu, oznitelik dagiliminin kaymasi (concept drift) ile "
     "izlenir."),
    ("p",
     "Surekli izlemenin klinik acidan ozel bir degeri vardir: bir BCI sistemi "
     "yillarca surekli calisir ve kullanicinin nörolojik durumu degisebilir. "
     "Model guncellenmezse, kullanici cihaza bagimli hale gelir; izleme ise bu "
     "bagimliligi erken fark etmeyi mumkun kilar."),

    ("h2", "3.6. Değerlendirme ve Ara Boşluk"),
    ("p",
     "Bu bolumdeki literatur taramasi, su boslugu ortaya cikarmaktadir: BCI'de "
     "derin ogrenme calismalarinin basarisi, cogu zaman donanim platformuna ozgudur; "
     "ayni model, farkli bir montaj veya farkli bir filtreleme zinciriyle "
     "tutarli performans gostermemektedir. Yani literaturdeki 'sifir bir artisi "
     "litelendirilmesi', karsilastirmalarin cogunun ayni kanal sayisi, ayni filtre "
     "ve ayni bolme protokolune gore kurulmasindan kaynaklanmaktadir. Bu durum, "
     "inceleme hipotezi H-1'i destekleyen bir gozlemdir: derin ogrenme getirisi "
     "laboratuvar sinirlari icin gecerli olabilir, klinik tasinabilirlik icin "
     "gecerli olmak zorunda degildir."),
]

# --------------------------------------- B4 KLINIK UYGULAMALAR
B4 = [
    ("h1", "DÖRDÜNCÜ BÖLÜM"),
    ("h1", "KLİNİK UYGULAMALAR: NÖRODEJENERATİF HASTALIKLAR, FELÇ VE "
           "İLETİŞİM BOZUKLUKLARI"),
    ("h2", "4.1. Uygunluk Kriterleri"),
    ("p",
     "BCI'nin klinik kullanimi, bir cihazin alet olmasi degil, klinik karari "
     "desteklemesi meselesidir. Bu nedenle degerlendirme dort kriter uzerinde "
     "yapilmalidir."),
    ("table", [
        ["Kriter", "Sorulmasi Gereken Soru", "Olcum Yontemi"],
        ["Guvenlik",
         "Yaralanma, enfeksiyon veya kayipta yeni risk var mi?",
         "Yan etki kaydi, olay orani"],
        ["Fayda",
         "Hastanin yasam kalitesinde anlamli iyilesme var mi?",
         "Yasam kalitesi olcekleri (QOL)"],
        ["Faydalilik",
         "Saglik sistemi acisindan maliyet-fayda dengesi var mi?",
         "Maliyet-etkinlik analizi"],
        ["Kullanilabilirlik",
         "Hasta ve bakim veren gunluk hayatta basarili kullanabiliyor mu?",
         "Kullanilabilirlik calismalari, surekli kullanim"],
    ]),
    ("caption", "Tablo 4.1. Klinik degerlendirme kriterleri."),

    ("h2", "4.2. İletişim Kurtarma Sistemleri"),
    ("p",
     "BCI'nin en olgun klinik uygulama alani iletisimdir. 1990'lardan bu yana "
     "gelistirilen yazim sistemleri, umes ve mesajlasma araclari, fare ve "
     "isaretleme kumandalari ve robotik kol kontrol sistemleri, farkli olgunluk "
     "duzeylerinde uygulanmaktadir. Iletisim sistemlerinin tercih edilme nedeni, "
     "bu alanda basari sinirinin nispeten iyi tanimlanmis olmasidir: alifabe "
     "dikkati sinirli bir kume degildir ve dogruluk abartilmayabilir."),
    ("p",
     "Metin tabanli iletisim sistemlerinin temel tasarim karari, isabet orani "
     "(characters per minute, CPM) ile yazim hizinin yaninda su odludur. Bilgi "
     "kuratigi (speller) tabanli sistemler harf sirasiyla harf tarama "
     "yapar; satriksiyonu verimlestirmek icin sozluk, ozgunluk sirasi ve "
     "kelime tamamlama kullanir. Grafik tabanli sistemler ise kullaniciya bir "
     "harf kumesi gosterip secim yapmasina izin verir; SECA gibi yeni "
     "yaklasimlar, harf secimini fiziksel bir eyleme cevirerek kas "
     "tortullugunu azaltmayi hedefler. Ses tabanli sistemler ise kullaniciya "
     "kendi sesiyle konusma geri bildirimi verir ve gozle bagimliligi "
     "ortadan kaldirarak iletisim ozgurluğunu artirir."),
    ("p",
     "Bu alandaki somut bir bulgu, sadece klinik olmayan durumdaki sistemlerin "
     "ticarilestirildigini, oysa felc hastalarindaki veriyle yapilan ciddi "
     "arayuz calismalarinin akademik aşamada kaldigini göstermektedir. Bu, "
     "teknolojinin laboratuvar ve pazar arasindaki kopuklugunun somut bir "
     "ornegidir."),

    ("h2", "4.3. Hareket Kontrolü ve Rehabilitasyon"),
    ("p",
     "Bozulmus sinir sistemi ile bilgisayar arasinda bir kontrol dongusu "
     "kurmak, felc sonrasi kol hareketinin geri kazanilmasinda kullanilir. "
     "Kilit bulgu, geri bildirimin noktasal olmasi degil, anlamli ve zamanli "
     "olmasi oldu: kullanici, cihazdan gelen geri bildirimi bir yeni ogrenme "
     "sinyali olarak yorumladiginda motor korteks yeniden katlanir. Ayni "
     "bulgu, dogal hareket geri besleme ile yapay geri beslemenin karsilastirildigi "
     "saglam gosterimlerde teyit edilmektedir."),
    ("p",
     "Ancak robotik kol sistemlerinin klinik transferi sinirli kalmistir. "
     "Yuksek kesinlik gerektiren gunluk yasam gorevlerinde performans, klinik "
     "faydayi destekleyecek duzeye ulasamamistir. Bu durum, alanin onemli bir "
     "gerilimidir: mekanik olarak ikna edici sonuclar, gunluk yasamda olcumlenen "
     "faydayi yansitmamaktadir."),

    ("h2", "4.4. Nörodejeneratif Hastalıklar"),
    ("p",
     "Alzheimer, Parkinson, multipl skleroz ve ALS gibi hastaliklarda BCI iki "
     "farkli rolde kullanilmaktadir. Ilk rol, iletisim ve kontrol araci; ikinci "
     "rol, tani ve izleme araci. Birinci rolde klinik kanit en gucludur. "
     "Ikincil rolde ise, noral isaretlerin hastalik evreleriyle iliskisi "
     "incelenmis olsa da, tani karari vermek icin gereken duyarlilik ve "
     "ozgulluk seviyelerine ulasilmamis; bu alan su an arastirma asamasindadir."),
    ("p",
     "Yinelenen (closed-loop) uyaranlama, norodejeneratif alanda BCI'nin en "
     "umut verici yeni yonudur: noral isaret ile es zamanli sunulan hedefli "
     "uyaranlar, kortikal uyarlanabilirligi yeniden kurmayi hedefler. Bu "
     "yaklasim, BCI'yi yalnizca bir cikarim cihazi degil, tedavi araci haline "
     "getirme potansiyeli tasiyan bir genislemedir."),

    ("h2", "4.5. Kognitif Yardım ve Sağlıklı Bireyler"),
    ("p",
     "Saglikli bireylerde kullanilan tuketici BCI urunleri, istenen kanalda "
     "belirgin bir beyin durumu saptamaya (dikkati olcme, yogunlasma, is "
     "yuku, hafiza) yoneliktir. Bu yonelim, hasta grubundaki uygulamalardan "
     "yapisal olarak farklidir ve arastirma sorusunun (RQ-003) merkezindedir."),
    ("table", [
        ["Olcut", "Hasta Grubu Uygulamalari", "Saglikli Birey Uygulamalari"],
        ["Odzorluk",
         "Orta-yuksek: kullanim icin teyit gerekli",
         "Dusuk: belirsizligi tolere edilebilir"],
        ["Yanlis kabul",
         "Yuksek: iletisim hatasi kritik",
         "Dusuk-orta: kullanici zaten konusabilir"],
        ["Odeme",
         "Toplum sagligi / sigorta",
         "Kullanicinin kendisi"],
        ["Gereklilik",
         "Alternatif iletisim yolu yok",
         "Konfor ve optimize amaci"],
        ["Risk yanliligi",
         "Yanlis sinif alarmi karari bozar",
         "Yanlis sinif yalnizca motivasyonu etkiler"],
    ]),
    ("caption", "Tablo 4.2. Hasta grubu ve saglikli birey BCI uygulamalarinin "
                "karsilastirmasi."),
    ("p",
     "Bu karsilastirma, dorduncu ve besinci bolumler arasindaki bagin neden "
     "onemli oldugunu gosterir: ayni teknik hata, iki farkli baglamda iki "
     "farkli ahlaki ve hukuki sonuc dogurur."),

    ("h2", "4.6. Performans Değerlendirme Metrikleri"),
    ("p",
     "BCI klinik calismalarinda performans, literaturda cogu zaman 'dogruluk' "
     "(accuracy) olarak raporlanir. Ancak yanlis olcu nedeniyle yanlis "
     "sonuca varma riski vardir. Ozellikle sinif dengesizligi olan motor "
     "imagery calismalarinda iki sinifli bir sistem %50 dogrulukla calisip "
     "hicbir sey ogrenmemis olabilir; bu durum yalnizca basari oranina "
     "(bit rate) ve eşiğe bagli degerlendirmeyle yakalanir."),
    ("p",
     "Alanin yerlesmeye basladigi iyi uygulama, dogruluk yaninda Cohen'in kappa "
     "katsayisi, eşiğe bagli degerlendirme (e.g. ITR, mutluluk matrisi) ve "
     "kullanilabilirlik olculerini birlikte raporlamaktir. Bir sistemin "
     "klinik olarak anlamli sayilmasi icin, yalnizca modelin degil, kullanicinin "
     "sistemle kurdugu sure de olculmelidir."),

    ("h2", "4.7. Karşılaştırmalı Kanıt Değerlendirmesi"),
    ("p",
     "Bu bolumun birincil bulgusu su olmustur: BCI'nin klinik faydasi, teknolojinin "
     "karma sikligi degil, klinik gereksinim ile teknolojik sinirlar arasindaki "
     "eslesme derecesiyle olculur. Iletisim sistemlerinde bu eslesme en yuksek, "
     "hareket kontrolunde orta, tani ve rehabilitasyon uygulamalarinda en dusuktur. "
     "Bu bulgu, inceleme hipotezi H-2'yi desteklemektedir: basarili sistemlerin "
     "ortak ozelligi algoritma degil, kullanim sureci tasarimidir."),
]
