# -*- coding: utf-8 -*-
"""Tez içeriği bölüm 2: YZ algoritmaları (B3), klinik uygulamalar (B4)."""

# --------------------------------------------- B3 YZ DESTEKLI ISLEME
B3 = [
    ("h1", "ÜÇÜNCÜ BÖLÜM"),
    ("h1", "YAPAY ZEKÂ DESTEKLİ NÖRAL SİNYAL İŞLEME VE DÜŞÜNCE ÇÖZME"),
    ("h2", "3.1. Geleneksel Yöntemler ve Temel Sınırları"),
    ("p",
     "BCI sınıflandırmasında geleneksel yaklaşım, karar fonksiyonunu basit ve "
     "özellik uzayında doğrusal varsayar. En yaygın kullanılan özellik çıkarımı "
     "yöntemi Ortak Ortak Uzaysal Desenlerdir (Common Spatial Patterns, CSP). "
     "CSP, iki sınıf arasındaki varyans farkını maksimize eden ve sınıf "
     "ortalarini birleştiren bir çift yönlü projeksiyon bulur. Düşük sınıf "
     "sayılı, iyi özellik ayrımı olan problemlerde CSP tabanlı sistemler, "
     "doğrusal diskriminant analizi ile birlikte hâlâ güçlü bir kıyas ölçüsüdür."),
    ("p",
     "Ancak bu yöntemlerin dört temel sınırı vardır."),
    ("bullet",
     "(i) Özellik uzayı zorunludur. Sistem yalnızca önceden seçilmiş özellikler "
     "üzerinden öğrendiği için, seçim yanlışsa performans tavana çarpar."),
    ("bullet",
     "(ii) Bilgi kazanımı yoktur. Özellik çıkarımı, sınıflandırıcıdan bağımsız "
     "ve gözlemeden bağımsız yapıldığı için öğrenme ile özellikler arasındaki "
     "Uyumsuzluk doğrudan gözlenmez."),
    ("bullet",
     "(iii) Sabit uzunluk penceresi kullanılır. Zaman-frekans özelliklerde "
     "pencere boyu sabit tutulduğu için, kısa süreli ve uzun süreli normal "
     "olaylar aynı çözünürlükte temsil edilir."),
    ("bullet",
     "(iv) İstatistiksel varsayımlardır. Çıkarınım modelleri şüphesiz dağılım "
     "ve sınıf dengesi varsayımına dayanır; gerçek EEG verisi ikisini de "
     "ihlal eder."),
    ("p",
     "Bu sınırlar, BCI'de derin öğrenmeye ilgiyi artırmış ve bu ilgi literatürde "
     "belirgin bir şekilde büyümüştür."),

    ("h2", "3.2. Derin Öğrenme: Mimari Duruş"),
    ("h2", "3.2.1. Girdi Temsilleri"),
    ("p",
     "Derin öğrenme modellerinin girdi temsili, BCI'de en kritik tasarım "
     "kararıdır ve literatürde en az model mimarisi kadar tartışılmıştır. Beş "
     "ana yaklaşım vardır."),
    ("table", [
        ["Temsil", "Girdi Şekli", "Avantaj", "Dezavantaj"],
        ["Ham zaman serisi",
         "[kanal x zaman]",
         "Bilgi kaybı yok",
         "Öğrenmesi zor, veri sınırlı"],
        ["Zaman-frekans (STFT)",
         "[kanal x zaman x frekans]",
         "Zamanı frekans ile eşleştirir",
         "Pencere seçimi kritik"],
        ["Dalgacık (wavelet)",
         "[kanal x zaman x ölçek]",
         "Çok ölçeklilik, zaman-özel",
         "Analitik işlem maliyeti"],
        ["Tüketilmiş özellik haritası",
         "[özellik x kanal]",
         "Ritim ve müzikâlik ilişkileri",
         "Biçimsel bilgi kaybı"],
        ["Kafes tabanlı öğrenme",
         "[kanal x zaman x frekans]",
         "Uzaysal-zamansal birliktelik",
         "Hesaplama yoğun"],
    ]),
    ("caption", "Tablo 3.1. BCI'de derin öğrenme girdi temsilleri."),

    ("h2", "3.2.2. Uygulanan Mimariler"),
    ("p",
     "Bozulmuş sınıftan öğrenme (BOS) tabanlı konvolüsyonel sinir ağları, EEG "
     "verisinde en yaygın kullanılan mimaridir. Temel fikir, konvolüsyon "
     "katmanlarının hem zaman hem de frekans ekseninde yerel desenleri "
     "çevirdiği ve sınıflandırma katmanına kadar bu desenlerin hiyerarşisini "
     "kurduğudur. Derin konvolüsyonel sinir ağları (DKSA) bu temele ek olarak "
     "her katmanda özellik haritalarını ilerleterek, özellik çıkarımı ile "
     "sınıflandırmayı birlikte öğrenen bütünleşik bir model kurar. Bir "
     "sonraki adım olarak, özellik haritalarının kanal uzayında özelleştirilmesi "
     "(KSA = kanal-uzay özelleştirme) eklenmiştir; bu aşama, EEG'de "
     "kanallar arasındaki bölgesel ilişkilerin modele girmesini sağlar."),
    ("p",
     "Bunun yanında iki farklı yönelim gelişmiştir."),
    ("bullet",
     "Graf tabanlı sinir ağları: kanal ilişkilerini bir komşuluk grafında "
     "temsil ederek, elektrot konumundan gelen ek bilgiyi modele entegre eder. "
     "Bu yaklaşım, anatomik komşuluğun sınıf ayrımına katkıda bulunduğu için "
     "özellikle yakın elektrotlarda kaydedilen çözünürlük düşük sinyallerde "
     "avantajlıdır."),
    ("bullet",
     "Dönüşümcü (transformer) tabanlı modeller: çok başlı öz-dikkat "
     "mekanizmasiyla kanal ve zaman boyutlarındaki uzak bağımlılıkları yakalar. "
     "EEG özgelliğinde, zaman-serisi modellerinin görüntü modellerine göre "
     "belirgin bir başarı farkı gösterdiğini ortaya koyan ilk çalışma 2021'de "
     "yayımlanmış ve alanın yönünü değiştirmiştir."),

    ("h2", "3.3. Öğrenme Stratejileri"),
    ("p",
     "Veri miktarından çok, verinin nasıl kullanıldığı belirleyicidir. BCI'de "
     "her kullanıcı için etiketli veri sınırlı olduğundan, transfer ve "
     "yararlanma temelli stratejiler temel tasarım kararıdır."),
    ("table", [
        ["Strateji", "Yaklaşım", "Gereksinim", "Klinik Uygunluk"],
        ["Denetimli öğrenme",
         "Etiketli veri ile doğrudan eğitim",
         "Yeterli oturum (>= 20)",
         "Orta"],
        ["Transfer öğrenme",
         "Önceden eğitilmiş ağın yeni kullanıcıya uyarlanması",
         "Hedef veri (az etiketle)",
         "Yüksek"],
        ["Öykülmüş öğrenme",
         "Etiketli/etiketsiz verinin birlikte kullanılması",
         "Yeterli etiketsiz veri",
         "Orta-yüksek"],
        ["Yarı-denetimli öğrenme",
         "Sınıf etiketlerinin kısmi kullanımı",
         "Kısmi etiket",
         "Orta"],
        ["Kendi kendine denetimli öğrenme",
         "Çift görüntü kullanımı, etiketsiz veriden temsil öğrenme",
         "Yeterli etiketsiz veri",
         "Yüksek"],
        ["Federe öğrenme",
         "Cihazda yerel eğitim, merkezi biriktirme olmadan",
         "Ortak model yapisı",
         "Yüksek (gizlilik)"],
    ]),
    ("caption", "Tablo 3.2. Öğrenme stratejileri ve klinik uygulanabilirlik."),
    ("p",
     "Kendi kendine denetimli öğrenme, EEG verisinin en doğru kozmetiği olduğu "
     "gerçeğine dayanır: iki kanal görüntüsü, ortak bir temsil çıkarım "
     "oluşturacaktır. Bu strateji, 2023 yılında yayımlanan kapsamlı bir "
     "taramada, denetimli öğrenmenin hâlâ çoğu çalışmada esas yöntem olduğunu "
     "ancak kendi kendine denetimli öğrenmenin metriklerde rekabet ciddi "
     "olduğunu göstererek raporlamıştır. Federe öğrenme ise sağlık "
     "verisinin gizlilik kısıtları nedeniyle BCI alanında giderek daha fazla "
     "önem kazanmaktadır: model, hastane sınırlarından çıkmadan kurulabilmektedir."),

    ("h2", "3.4. Değerlendirme Sorunları"),
    ("p",
     "BCI'de derin öğrenme literatürünün en ciddi yarışı, metodolojiktir. "
     "Aşağıdaki sorunlar gözlemlenmiştir."),
    ("bullet",
     "(1) Karşılaştırmalı benchmark eksikliği: çok sayıda çalışma, verisini "
     "özel olarak biriktirdiği bir veri kümesiyle, sözde gerçek zamanli "
     "(pseudo-online) döngüyle, ciddi bir temel çizgi (baseline) olmadan "
     "sunmaktadır."),
    ("bullet",
     "(2) Üzerinde çıkış (overfitting) ve tekrar kullanım (leakage): özellik "
     "seçimi ve hiperparametre ayarı aynı doğrulama kümesinde yapıldığında, "
     "test sonuçları sistematik olarak iyimserleşir."),
    ("bullet",
     "(3) Küçük örnek sorunu: onlarca katılımcıdan oluşan veri kümesi, milyonlarca "
     "parametreli bir ağın genellenmesi için yetersizdir; birçok çalışma bu "
     "nedenle az parametreli ya da transfer öğrenmeye dayalı modellerle "
     "karşılaştırmayı tercih etmektedir."),
    ("bullet",
     "(4) Kısıtlı gerçekçilik: laboratuvar verisi, gerçek kullanımdaki dikkat "
     "dağılımı, yorgunluk ve ev ortamı değişkenlerini yansıtmaz."),
    ("p",
     "Bu sorunlara karşı geliştirilen önlemler önceden test edilmiş protokol, "
     "bağımsız test kümesi, yeterli katılımcı sayısı ve önceden kaydedilmiş "
     "analiz planıdır. Alanın olgunlaşması, bu önlemlerin zorunlu hâle "
     "gelmesiyle ölçümlenmektedir."),

    ("h2", "3.5. Açıklanabilirlik Sorunu"),
    ("p",
     "Derin öğrenme modellerinin klinik kullanıma en önemli engeli açıklanabilirlik "
     "eksikliğidir. Bir sınıflandırıcının 'sol el hareketi' sınıfını neden "
     "seçer bilmek, sistemin güvenilirliği için zorunludur; aksi halde hata "
     "teşhisi ve hasta öncesi bilgilendirme mümkün değildir. Bu alanda "
     "geliştirilen yaklaşımlar şu yöneldedir."),
    ("bullet",
     "Girdi katmanı açıklanabilirliği: modelin hangi zaman aralıklarına ve "
     "hangi frekans bantlarına duyarlı olduğunu gösterir; alan sağlamlığı (spatial "
     "sensitivity) haritaları burada üretilir."),
    ("bullet",
     "Değer temelli açıklamalar: her bir özniteliğin karara katkısını dörtlü "
     "değerlerle (W, S, B, E) raporlar."),
    ("bullet",
     "Konsept tabanlı açıklamalar: model kararını, insan tarafından anlaşılır "
     "klinik özelliklerle bağlar; ör. 'güç artışı ve yavaşlatma' veya "
     "'motor hazırlık müfredatı'."),
    ("bullet",
     "Sürekli izleme (monitoring) tabanlı açıklamalar: gerçek kullanım sırasında "
     "performans düşüsü, öznitelik dağılımının kayması (concept drift) ile "
     "izlenir."),
    ("p",
     "Sürekli izlemenin klinik açıdan özel bir değeri vardır: bir BCI sistemi "
     "yıllarca sürekli çalışır ve kullanıcının nörolojik durumu değişebilir. "
     "Model güncellenmezse, kullanıcı cihaza bağımlı hâle gelir; izleme ise bu "
     "bağımlılığı erken fark etmeyi mümkün kılar."),

    ("h2", "3.6. Değerlendirme ve Ara Boşluk"),
    ("p",
     "Bu bölümdeki literatür taraması, şu boşluğu ortaya çıkarmaktadır: BCI'de "
     "derin öğrenme çalışmalarının başarısı, çoğu zaman donanım platformuna özgüdür; "
     "aynı model, farklı bir montaj veya farklı bir filtreleme zinciriyle "
     "tutarlı performans göstermemektedir. Yani literatürdeki 'sıfır bir artışı "
     "nitelendirilmesi', karşılaştırmaların çoğunun aynı kanal sayısı, aynı filtre "
     "ve aynı bölme protokolüne göre kurulmasından kaynaklanmaktadır. Bu durum, "
     "inceleme hipotezi H-1'i destekleyen bir gözlemdir: derin öğrenme getirisi "
     "laboratuvar sınırları için geçerli olabilir, klinik taşınabilirlik için "
     "geçerli olmak zorunda değildir."),
]

# --------------------------------------- B4 KLINIK UYGULAMALAR
B4 = [
    ("h1", "DÖRDÜNCÜ BÖLÜM"),
    ("h1", "KLİNİK UYGULAMALAR: NÖRODEJENERATİF HASTALIKLAR, FELÇ VE "
           "İLETİŞİM BOZUKLUKLARI"),
    ("h2", "4.1. Uygunluk Kriterleri"),
    ("p",
     "BCI'nin klinik kullanımı, bir cihazın alet olması değil, klinik kararı "
     "desteklemesi meselesidir. Bu nedenle değerlendirme dört kriter üzerinde "
     "yapılmalıdır."),
    ("table", [
        ["Kriter", "Sorulması Gereken Soru", "Ölçüm Yöntemi"],
        ["Güvenlik",
         "Yaralanma, enfeksiyon veya kayıpta yeni risk var mi?",
         "Yan etki kaydı, olay oranı"],
        ["Fayda",
         "Hastanın yaşam kalitesinde anlamlı iyileşme var mi?",
         "Yaşam kalitesi ölçekleri (QOL)"],
        ["Faydalılık",
         "Sağlık sistemi açısından maliyet-fayda dengesi var mi?",
         "Maliyet-etkinlik analizi"],
        ["Kullanılabilirlik",
         "Hasta ve bakım veren günlük hayatta başarılı kullanabiliyor mu?",
         "Kullanılabilirlik çalışmaları, sürekli kullanım"],
    ]),
    ("caption", "Tablo 4.1. Klinik değerlendirme kriterleri."),

    ("h2", "4.2. İletişim Kurtarma Sistemleri"),
    ("p",
     "BCI'nin en olgun klinik uygulama alanı iletişimdir. 1990'lardan bu yana "
     "geliştirilen yazım sistemleri, ümes ve mesajlaşma araçları, fare ve "
     "işaretleme kumandaları ve robotik kol kontrol sistemleri, farklı olgunluk "
     "düzeylerinde uygulanmaktadır. İletişim sistemlerinin tercih edilme nedeni, "
     "bu alanda başarı sınırının nispeten iyi tanımlanmış olmasıdır: alfabe "
     "dikkati sınırlı bir küme değildir ve doğruluk abartilmayabilir."),
    ("p",
     "Metin tabanlı iletişim sistemlerinin temel tasarım kararı, isabet oranı "
     "(characters per minute, CPM) ile yazım hızının yanında şu ölçüdür. Bilgi "
     "kurgattığı (speller) tabanlı sistemler harf sırasıyla harf tarama "
     "yapar; satrıksiyonu verimleştirmek için sözlük, özgünlük sırası ve "
     "kelime tamamlama kullanır. Grafik tabanlı sistemler ise kullanıcıya bir "
     "harf kümesi gösterip seçim yapmasına izin verir; SECA gibi yeni "
     "yaklaşımlar, harf seçimini fiziksel bir eyleme çevirerek kas "
     "tortuluğunu azaltmayı hedefler. Ses tabanlı sistemler ise kullanıcıya "
     "kendi sesiyle konuşma geri bildirimi verir ve gözle bağımlılığı "
     "ortadan kaldırarak iletişim ozgurluğunu artırır."),
    ("p",
     "Bu alandaki somut bir bulgu, sadece klinik olmayan durumdaki sistemlerin "
     "ticarileştirildiğini, oysa felc hastalarındaki veriyle yapılan ciddi "
     "arayüz çalışmalarının akademik aşamada kaldığını göstermektedir. Bu, "
     "teknolojinin laboratuvar ve pazar arasındaki kopukluğunun somut bir "
     "örneğidir."),

    ("h2", "4.3. Hareket Kontrolü ve Rehabilitasyon"),
    ("p",
     "Bozulmuş sinir sistemi ile bilgisayar arasında bir kontrol döngüsü "
     "kurmak, felc sonrası kol hareketinin geri kazanılmasında kullanılır. "
     "Kilit bulgu, geri bildirimin noktasal olması değil, anlamlı ve zamanli "
     "olması oldu: kullanıcı, cihazdan gelen geri bildirimi bir yeni öğrenme "
     "sinyali olarak yorumladığında motor korteks yeniden katlanır. Aynı "
     "bulgu, doğal hareket geri besleme ile yapay geri beslemenin karşılaştırıldığı "
     "sağlam gösterimlerde teyit edilmektedir."),
    ("p",
     "Ancak robotik kol sistemlerinin klinik transferi sınırlı kalmıştır. "
     "Yüksek kesinlik gerektiren günlük yaşam görevlerinde performans, klinik "
     "faydayı destekleyecek düzeye ulaşamamıştır. Bu durum, alanın önemli bir "
     "gerilimidir: mekanik olarak ikna edici sonuçlar, günlük yaşamda ölçümlenen "
     "faydayı yansıtmamaktadır."),

    ("h2", "4.4. Nörodejeneratif Hastalıklar"),
    ("p",
     "Alzheimer, Parkinson, multipl skleroz ve ALS gibi hastalıklarda BCI iki "
     "farklı rolde kullanılmaktadır. İlk rol, iletişim ve kontrol aracı; ikinci "
     "rol, tanı ve izleme aracı. Birinci rolde klinik kanıt en güçlüdür. "
     "İkincil rolde ise, normal işaretlerin hastalık evreleriyle ilişkisi "
     "incelenmiş olsa da, tanı kararı vermek için gereken duyarlılık ve "
     "özgüllük seviyelerine ulaşılmamış; bu alan şu an araştırma aşamasındadır."),
    ("p",
     "Yinelenen (closed-loop) uyaranlama, nörodejeneratif alanda BCI'nin en "
     "umut verici yeni yönüdür: normal işaret ile eş zamanli sunulan hedefli "
     "uyaranlar, kortikal uyarlanabilirliği yeniden kurmayı hedefler. Bu "
     "yaklaşım, BCI'yi yalnızca bir çıkarım cihazı değil, tedavi aracı haline "
     "getirme potansiyeli taşıyan bir genişlemedir."),

    ("h2", "4.5. Kognitif Yardım ve Sağlıklı Bireyler"),
    ("p",
     "Sağlıklı bireylerde kullanılan tüketici BCI ürünleri, istenen kanalda "
     "belirgin bir beyin durumu saptamaya (dikkati ölçme, yoğunlaşma, iş "
     "yükü, hafıza) yöneliktir. Bu yönelim, hasta grubundaki uygulamalardan "
     "yapısal olarak farklıdır ve araştırma sorusunun (RQ-003) merkezindedir."),
    ("table", [
        ["Ölçüt", "Hasta Grubu Uygulamaları", "Sağlıklı Birey Uygulamaları"],
        ["Ödzorluk",
         "Orta-yüksek: kullanım için teyit gerekli",
         "Düşük: belirsizliği tolere edilebilir"],
        ["Yanlış kabul",
         "Yüksek: iletişim hatası kritik",
         "Düşük-orta: kullanıcı zaten konuşabilir"],
        ["Ödeme",
         "Toplum sağlığı / sigorta",
         "Kullanıcının kendisi"],
        ["Gereklilik",
         "Alternatif iletişim yolu yok",
         "Konfor ve optimize amacı"],
        ["Risk yanlılığı",
         "Yanlış sınıf alarmı kararı bozar",
         "Yanlış sınıf yalnızca motivasyonu etkiler"],
    ]),
    ("caption", "Tablo 4.2. Hasta grubu ve sağlıklı birey BCI uygulamalarının "
                "karşılaştırması."),
    ("p",
     "Bu karşılaştırma, dördüncü ve beşinci bölümler arasındaki bağın neden "
     "önemli olduğunu gösterir: aynı teknik hata, iki farklı bağlamda iki "
     "farklı ahlakî ve hukukî sonuç doğurur."),

    ("h2", "4.6. Performans Değerlendirme Metrikleri"),
    ("p",
     "BCI klinik çalışmalarında performans, literatürda çoğu zaman 'doğruluk' "
     "(accuracy) olarak raporlanır. Ancak yanlış ölçü nedeniyle yanlış "
     "sonuca varma riski vardır. Özellikle sınıf dengesizliği olan motor "
     "imagery çalışmalarında iki sınıflı bir sistem %50 doğrulukla çalışıp "
     "hiçbir şey öğrenmemiş olabilir; bu durum yalnızca başarı oranına "
     "(bit rate) ve eşiğe bağlı değerlendirmeyle yakalanir."),
    ("p",
     "Alanın yerleşmeye başladığı iyi uygulama, doğruluk yanında Cohen'in kappa "
     "katsayısı, eşiğe bağlı değerlendirme (e.g. ITR, mutluluk matrisi) ve "
     "kullanılabilirlik ölçülerini birlikte raporlamaktır. Bir sistemin "
     "klinik olarak anlamlı sayılması için, yalnızca modelin değil, kullanıcının "
     "sistemle kurduğu süre de ölçülmelidir."),

    ("h2", "4.7. Karşılaştırmalı Kanıt Değerlendirmesi"),
    ("p",
     "Bu bölümün birincil bulgusu şu olmuştur: BCI'nin klinik faydası, teknolojinin "
     "karma sıklığı değil, klinik gereksinim ile teknolojik sınırlar arasındaki "
     "eşleşme derecesiyle ölçülür. İletişim sistemlerinde bu eşleşme en yüksek, "
     "hareket kontrolünde orta, tanı ve rehabilitasyon uygulamalarında en düştür. "
     "Bu bulgu, inceleme hipotezi H-2'yi desteklemektedir: başarılı sistemlerin "
     "ortak özelliği algoritma değil, kullanım süreci tasarımıdır."),
]
