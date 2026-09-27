# -*- coding: utf-8 -*-
"""Tez içeriği bölüm 1: on bilgiler, Giriş (B1), BCI teknolojileri (B2).

Her öğe (tur, metin) tuple'idir:
  ("h1", metin) / ("h2", metin) / ("p", metin) / ("bullet", metin)
  / ("table", [[hücre, ...], ...]) / ("quote", metin) / ("caption", metin)
"""

FRONT = [
    ("başlık", "İNSAN BEYNİNİN VE DÜŞÜNCELERİNİN YAZILIMLA OKUNMASI"),
    ("altbaşlık",
     "Nörobilimsel sinyal işleme, yapay zeka destekli çıkarım ve etik "
     "sınırların birlikte incelenmesi"),
    ("tur", "Yüksek Lisans Tezi"),
    ("tur", "Program: Bilgisayar Mühendisliği / Bilişim Sistemleri"),
    ("tur", "Danışman: —"),
    ("tur", "Yıl: 2026"),
]

# ---------------------------------------------------------------- B1 GIRIS
B1 = [
    ("h1", "BİRİNCİ BÖLÜM"),
    ("h1", "GİRİŞ"),

    ("h2", "1.1. Konunun Önemi ve Kapsamı"),
    ("p",
     "Beyin-bilgisayar arayüzü (brain-computer interface, BCI), canlı bir organizmanın "
     "merkezi sinir sistemi ile haricî bir hesaplama birimi arasında doğrudan iletişim "
     "kuran sistemler için kullanılan genel terimdir. Bu terim altı ana özelliği tanımlar: "
     "(a) iletişim kanalının fiziksel olarak başka bir ortamdan geçmesi, (b) özel bir "
     "yönlendirme protokolünün bulunması, (c) çıkarımının başında kullanıcının niyetinin yer "
     "alması, (d) çıkarım sonucunun kullanıcıya geri bildirilmesi ve (e) sistemin öğrenme "
     "süreci içinde bireysel kullanıcılık özelleştirilmesi. Bu beş özelliğin birlikte "
     "bulunması, BCI'yi yalnızca bir girdi-ikti cihazından ayırır ve onu bir "
     "duruşum-aktarım sistemi haline getirir."),
    ("p",
     "Konunun önemi üç ayrı katmandan gelir. Birincisi, BCI teknolojileri motor "
     "nörodejeneratif hastalıklar ve felc sonrası iletişim kaybı olan bireyler için "
     "pratik bir kurtarma aracı sunar. İkincisi, aynı teknolojiler sağlıklı bireylerde "
     "bilişsel yardım, dikkat artırma ve rehabilitasyon amacıyla kullanılmaya "
     "başlamıştır; bu durum klinik sınırı aşma sorusunu gündeme getirmektedir. "
     "Uçuncusu, okunan verinin gerçekten bir düşünce olup olmadığı meselesi, doğasın "
     "tanımına ve makine öğrenmesinin sınırlarına dayanan teknik bir sorunun yanında "
     "felsefi ve hukukî bir soruna dönüşmektedir."),
    ("p",
     "Bu çalışma konunun dört temel boyutunu birlikte ele alır: nörobilimsel temeller "
     "(Bölüm 2), yapay zeka destekli çıkarım yöntemleri (Bölüm 3), klinik uygulamalar "
     "(Bölüm 4) ve etik-hukukî sınırlar (Bölüm 5). Bölüm 6 ise gelecek yönelimleri "
     "değerlendirir. Yöntem olarak nitel kaynak temelli derleme benimsenmiştir; çalışma "
     "yalnızca literatürde kanıtlanmış bulgularla sınırlı kalmakta, özgün ampirik veri "
     "üretmemektedir."),

    ("h2", "1.2. Problem Durumu"),
    ("p",
     "Kamusal alanda BCI teknolojileri hakkında yaygın iki şey karşılaşmaktadır. "
     "Birincisi, teknolojinin düşünce okuma kapasitesine sahip olduğu yönündeki "
     "popüler anlatı. Bu anlatı, felc ve nörodejeneratif hastalarda gerçekten var olan "
     "hoş bir uygulamayı, sağlıklı bireylerde her türlü zihinsel içeriği işleyebilen "
     "bir sistem imajına dönüştürür. İkincisi, teknolojinin klinik geçerliliği "
     "konusundaki aşırı iyimserlik. İkincisi, alanda görülen gerçek sınırlamaları "
     "görmezden gelir: gözleme yüzeyi yoğunluğu, şartlara bağlı performans, eğitim "
     "sürelerinin uzunluğu ve klinik ortam ile laboratuvar arasındaki "
     "aktarılabilirlik açığı."),
    ("p",
     "Bu ispatlanmamış iyimserlik, uygulamada iki somut risk doğurur. İlki, hasta ve "
     "hasta ailelerinin beklentilerinin gerçekçi olmayan bir seviyeye çekilmesi ve "
     "klinik kararların gerçekçi olmayan beklentiler üzerine kurulması. İkincisi, "
     "mevzuat ve etik çerçevelerin vaatlerden hareketle değil, fiilî klinik "
     "yeteneklerden hareketle tasarlanması. Bu iki risk, konunun yalnızca teknik "
     "değil, aynı zamanda yönetimsel ve etik bir problem olduğunu gösterir."),

    ("h2", "1.3. Amaç"),
    ("p",
     "Çalışmanın amacı şu döndür:"),
    ("bullet",
     "BCI sistemlerinin temel sınıflandırmasını ve sinyal alım yöntemlerinin "
     "klinik-özel ilişkilerini ortaya koymak;"),
    ("bullet",
     "Modern makine öğrenmesi ve derin öğrenme yöntemlerinin normal sinyal çıkarımına "
     "katkısını, elde edilen kazanımlar ve sınırlamalarla birlikte değerlendirmek;"),
    ("bullet",
     "BCI'nin klinik uygulamalardaki kanıt temelini ve yararlılık sınırlarını "
     "değerlendirmek;"),
    ("bullet",
     "Bireysel verinin zihinsel içerik olarak okunması meselesinin etik, hukukî ve "
     "toplumsal sonuçlarını analiz etmek."),

    ("h2", "1.4. Araştırma Soruları"),
    ("p",
     "Çalışma şu araştırma sorularını yanıtlamaya çalışır:"),
    ("bullet",
     "RQ-001. Yapay zeka destekli sinyal işleme, BCI tabanlı sınıflandırma "
     "sistemlerinde geleneksel yöntemlere göre ne ölçüde doğruluk ve dayanıklılık "
     "kazancı sağlamaktadır?"),
    ("bullet",
     "RQ-002. EEG tabanlı girişimsiz BCI sistemlerinin klinik uygulamalardaki "
     "gerçek başarı oranları ve başarısı sınırlayan etkenler nelerdir?"),
    ("bullet",
     "RQ-003. Sağlıklı bireylerde kognitif yardım amaçlı BCI uygulamaları, hasta "
     "grubundaki klinik uygulamalardan hangi yönlerle ayrılır ve ayrılmaktadır?"),
    ("bullet",
     "RQ-004. Nöroveri meselesi, veri sahipliği ve erişim denetimi bakımından "
     "mevcut hukukî ve etik çerçeveler BCI'ye ne ölçüde uyumludur?"),

    ("h2", "1.5. Hipotezler"),
    ("p",
     "Bu çalışma nicel bir ampirik araştırma olmadığı için deneysel hipotez "
     "testi yapılmaz. Bunun yerine literatürde gözlenen ve birbirleriyle yarışan "
     "iddialar, inceleme hipotezi (H) olarak aşağıda ifade edilir; her biri "
     "inceleme bölümünde kanıtla karşılaştırılır."),
    ("table", [
        ["No", "İnceleme Hipotezi", "Yönelim"],
        ["H-1",
         "Derin öğrenme, geleneksel sınıflandırıcı kombinasyonları üzerinde "
         "ölçülü bir doğruluk kazancı sağlar; ancak bu kazanc klinik "
         "uygulamaya taşınabilir değildir.",
         "Kısmen desteklenir"],
        ["H-2",
         "Başarılı BCI uygulamalarının ortak özelliği, sinyal kalitesinden çok "
         "kullanıcı deneyimi ve öğretim sürelerinin uzunluğudur.",
         "Desteklenir"],
        ["H-3",
         "Etik ve hukukî tartışma, veri gizliliği çerçevesinde toplanırken "
         "asıl gerilimi zihinsel özgürlüğü ilgilendirir.",
         "Desteklenir"],
    ]),
    ("caption", "Tablo 1.1. İnceleme hipotezleri ve değerlendirme yönelimi."),

    ("h2", "1.6. Yöntem"),
    ("p",
     "Çalışma nitel kaynak temelli derleme (narrative literature review) yöntemiyle "
     "yürütülmüştür. Yöntem iki aşamalı ve açıkça sınırlı bırakılmıştır. Birinci "
     "aşamada veri tabanları (Crossref, OpenAlex) üzerinden taranmış arama "
     "protokolü kaydı oluşturulmuş ve dâhil etme-dışlama etme kriterleri "
     "uygulanmıştır. İkinci aşamada kaynakça girdileri araç tarafından "
     "doğrulanmıştır: 37 kaynağın 13'u Crossref ve OpenAlex arasında iki "
     "bağımsız kaynakla eşleşme eşiğini geçmiş, kalan 24 kaynak doğrulanmamış "
     "ve kaynakçada DOI'siz bırakılmıştır. Doğrulama sırasında aracın beş "
     "kusuru tespit edilip düzeltilmiştir; ayrıntılı kayıt ve düzeltme sonrası "
     "ölçümler EK-2'de verilmiştir."),
    ("p",
     "Yöntemin sınırları açıkça belirtilmelidir. Birincisi, çalışma yalnızca açık "
     "erişime sahip İngilizce ve Türkçe literatürle sınırlıdır; konu alanı geniş "
     "olduğundan bu bir eksikliktir. İkincisi, incelenen çalışmalarda yayınlanma "
     "yanlılığı (olumlu sonuç gösteren çalışmaların daha fazla yayınlanması) "
     "kontrol edilememiştir. Üçüncüsü, BCI alanındaki teknik ilerleme hızlı "
     "olduğundan bazı tespitlerin çalışma tarihî itibarıyla geçmiş olabilir."),

    ("h2", "1.7. Çalışmanın Katkısı"),
    ("p",
     "Çalışmanın beklenen katkısı şudur: teknik yetenek sınırları ile etik-hukukî "
     "beklentiler arasındaki boşluğu tek bir çerçevede göstermek; BCI uygulamaları "
     "için acele karar vermeyi engelleyen bir karar çerçevesi sunmak; ve "
     "zihinsel veri koruması için somut bir politika çerçevesi önerisi geliştirmek. "
     "Çalışma özgün ampirik veri üretmez ve klinik karar yerine geçmez."),

    ("h2", "1.8. Kapsam ve Sınırlar"),
    ("p",
     "Çalışma invaziv sistemleri yalnızca ilke düzeyde ele alır; cerrahi detay ve "
     "klinik protokol bilgisi dışarıda bırakılmıştır. Elektriksel beyin aktivitesi "
     "odaklı alınmıştır; MEG ve fNIRS yöntemleri yalnızca karşılaştırma amacıyla "
     "geçmektedir. Sağlıklı bireylerde uygulanan ticari ürünler yalnızca risk "
     "analizi çerçevesinde ele alınmıştır; belirli bir ürün için yazılım tanıtımı "
     "veya kullanılabilirlik değerlendirmesi yapılmamıştır."),
]

# ------------------------------------------------- B2 BCI TEKNOLOJILERI
B2 = [
    ("h1", "İKİNCİ BÖLÜM"),
    ("h1", "BEYİN-BİLGİSAYAR ARAYÜZÜ TEKNOLOJİLERİ"),
    ("h2", "2.1. Tarihsel Gelişim"),
    ("p",
     "BCI düşüncesinin doğrudan deneysel kökleri 1920'lere dayanır. Hans Berger, "
     "insan elektroensefalografisini (EEG) kaydeden ilk sistemi geliştirdi ve "
     "çalışmaları, beyin aktivitesinin kaydedilip analiz edilebileceğini "
     "gösterdi. Berger'in kayıtları 1924'te bir insan uyaranlara bağlı olarak "
     "belirgin bir elektriksel cevap ürettiğini ortaya koydu. 1930'larda Edgar "
     "Adrian ve GVL Baseline okuma, normal ritmin bir ölçüm aracı değil, "
     "beynin uyanıklık durumunu yansıtan bir fizyolojik süreç olduğunu "
     "göstererek EEG'nin işlevsel yorumunu başlattı."),
    ("p",
     "Bilgisayar teknolojisinin devreye girdiği dönem 1970'lerdir. Jacques "
     "Vidal'in 1973 tarihli çalışması, bir insanın komut sinyali olarak "
     "kullanılabilecek sinirsel bir dalga formu tespit etmesi ve bu dalgadan "
     "hareketle bir bilgisayar imlecinin yönlendirilebileceğini göstermesiyle "
     "alanın kurucu metni kabul edilir. Vidal'in bulgusu bugünkü BCI sistemlerinin "
     "temiş ettiği iki temel varsayımı — çıkarım bir sınıflandırma problemidir ve "
     "öğrenme kullanıcıya göre uyarlanabilir — birlikte kurmuştur."),
    ("p",
     "1990'larda bir başka kilometre taşı aydınlatıldı: beyin bir bilgisayara "
     "komut gönderen bir çevre değil, ortamdan bağımsız bir tuş olarak "
     "kullanılabilir. Nierenberg ve colleagues'in P300 tabanlı yazım sistemi, "
     "katılımcı kullanıcıya belirli harflerin zihinsel olarak "
     "vurgulanmasını (oddball paradigm) ve uyaranla eşleşen bir zihinsel "
     "ölçüme bağlı olarak harfi seçmesini mümkün kıldı. Bu çalışma, "
     "beyin-bilgisayar iletişimin 'okuma' değil, 'öğrenme' problemi olduğunu "
     "göstererek sonraki iki dekadın yol haritasını belirledi."),
    ("p",
     "2000'li yıllarda alan kurumsallaşti. 2002'de Wolpaw ve arkadaşları BCI "
     "sistemlerini sınıflandıran ve alanın ortak dilini belirleyen bir çerçeve "
     "yayımladı. Aynı dönemde klinik uygulamalar doğrulandı: BrainGate ekibi "
     "felc hastalarında istenen hareketin sinirsel öncüsünü tespit ederek "
     "robotik kolu kontrol etmeyi başardı. Üç boyutlu baskılar arayan ve "
     "hedefi sıfırlanan geri besleme araçlarının geliştirilmesi, BCI'yi "
     "laboratuvar nesnesi olmaktan çıkarıp kullanıcı odaklı bir asistif teknoloji "
     "haline dönüştürdü."),
    ("p",
     "2010'lardan itibaren iki belirgin yönelim birlikte ilerledi. Birincisi, "
     "derin öğrenmenin devreye girmesiyle sınıflandırma performansındaki "
     "artıştırır. İkincisi, gözleme taşınabilir (portable) sistemlerin yaygınlaşması "
     "ve tüketici elektro-nörolojisi (consumer neurotechnology) kavramının "
     "doğması. 2019'daki bir derleme, özellikle invaziv görüntü motoru yorumlama "
     "çalışmalarında tek katılımlı derin mimarilerin çok katmanlı modelleri "
     "geçtiğini ve birçok çalışmada karşılaştırma metodolojisinin zayıf kaldığını "
     "bildirmiştir. 2020'li yıllar ise alanın metodolojik olgunlaşmasıyla "
     "nispeten ayırt edilebilir: onaylı çalışma tasarımı, raporlanma "
     "standartları ve klinik kanıt toplama gereklilikleri konusunda belirgin "
     "bir farkındalık oluşmuştur."),

    ("h2", "2.2. Tanım ve Sınıflandırma"),
    ("h2", "2.2.1. BCI Teknolojisi Nedir?"),
    ("p",
     "Bir BCI sistemi, merkezi sinir sistemi ile haricî bir sistem arasındaki "
     "iletişimi, biyolojik olmayan bir çıktı ve girdi yoluyla sağlayan sistemdir. "
     "Bu tanım, yalnızca 'beyin okuyan' cihazları kapsamaz; tersine, cihazın "
     "beyne geri bildirim gönderdiği çift yönlü sistemleri de kapsar. Geri "
     "bildirim döngüsü bir BCI'yi pasif bir kaydediciden ayıran temel özelliktir: "
     "kullanıcı, sistemin çıkarımını görerek kendi çıktısını ayarlar ve sistem "
     "bu ayarlamaya göre güncellenir."),
    ("p",
     "Sınıflandırmada iki kriter kullanılır. Birincisi, örnekleme yöntemidir. "
     "İnvaziv sistemler elektrotları doğrudan korteks veya korteks yüzeyine "
     "yerleştirir; girişimsiz sistemler elektrotları kafa derisinden dışarıda "
     "tutar. İkincisi, geri bildirimin doğasıdır: geri besleme (kullanıcı kendi "
     "motor çıktısını görür) veya geri beslemesiz (yalnızca bilgi döndürülür) "
     "sistemler. Bu iki kriter birlikte dörtlü bir sınıflandırma üretir."),

    ("h2", "2.2.2. Sınıflandırma Tablosu"),
    ("table", [
        ["Sınıf", "Örnekleme", "Geri Bildirim", "Güçlü Yönü", "Zayıf Yönü"],
        ["İnvaziv (implant)",
         "Korteks / korteks yüzeyi",
         "Hareket geri besleme",
         "Yüksek sinyal-gürültü oranı",
         "Cerrahi risk, uzunsüreli kabul sorunu"],
        ["Yarı invaziv",
         "Korteks üzeri elektrot (ECoG)",
         "Hareket geri besleme",
         "Yüksek çözünürlük, görüntü hareketi",
         "Cerrahi gerektirir, sınırlı süre"],
        ["Girişimsiz (EEG)",
         "Kafa derisi dışı",
         "Geri besleme / geri beslemesiz",
         "Non-invaziv, ucuz, tekrar edilebilir",
         "Düşük sinyal-gürültü, coğrafi sınırlı"],
        ["Hibrit / pasif",
         "İmplant + girişimsiz",
         "Geri besleme",
         "Aktif ve pasif bölgeleri birlikte çıkarır",
         "En yüksek maliyet, en yüksek entegrasyon riski"],
    ]),
    ("caption", "Tablo 2.1. BCI sistemlerinin sınıflandırması."),

    ("h2", "2.3. Sinyal Alım Yöntemleri"),
    ("h2", "2.3.1. Elektriksel Yöntemler"),
    ("p",
     "Elektriksel kayıt, beyin aktivitesinin en yaygın ve en ucuz kaydedilme "
     "biçimidir. Elektrot yüzeyiyle elektrolit arası iletkenlik sayesinde hücre "
     "dışı akım potansiyelleri ölçülür. Ölçümün gücü, önce frekans bant genişliği, "
     "sonra uzaysal çözünürlük sırasıyla azalır: EEG geniş bantlı ve yüksek "
     "uzaysal çözünürlüktür, ECoG daha dar bantlı ve daha iyi çözünürlüktür, "
     "intrakortikal kayıt ise en dar bantlı ve en yüksek çözünürlüktür."),
    ("p",
     "EEG'de gözleme, yalnızca alınabilen sinyali değil, aynı zamanda "
     "konumlandırılabilen sinyali ifade eder. İki temel yaklaşım vardır. Birincisi "
     "uzamsal (spatial filter) tabanlı yaklaşımdır: gözleme, özellik vektörler "
     "üzerinden kanal ağırlıklarının hesaplanması ile yapılır. Ortak Ortak Uzaysal "
     "Desenler (CSP) ve bunun varyantları bu ailedendir. İkincisi, kafa derisinin "
     "hacim iletkenliği nedeniyle sinyallerin karıştığını kabul edip modelleme "
     "temelli (kaynak yerelleştirme, ters modelleme) yaklaşımdır. İki yaklaşım "
     "birlikte kullanılabilir; ilki iyi özellik ayrımı, ikincisi fizyolojik "
     "yorumluluk sağlar."),

    ("h2", "2.3.2. Kayıt Kalitesi ve Yüz Yüklemesi"),
    ("p",
     "Girişimsiz kayıtta en belirleyici sınırlandırma yüz yüklemesidir. Elektrot "
     "sayısı doğrusal olarak artsa bile, elektrot sayısının karesiyle orantili "
     "serbestlik derecesi sınırlı kaldığı için özelliklerin belirginliği "
     "sınırlanır. Ayrıca kırpma, göz kasları aktivitesi ve terleme kaynaklı "
     "hareket artefaktları sinyali bozar. Bu nedenle konumlandırılabilir ve "
     "güçlendirilmiş elektrotlar, yoğun montajlara göre uygulamalarda tercih "
     "edilebilir."),
    ("p",
     "Artefakt yönetimi, BCI süreçlerinin ayrılmaz parçasıdır. Göz kasları "
     "aktivitesi aslında sinyali değil, ortam bilgisini taşır; bu nedenle "
     "doğru bir tanımlayıcı (örneğin yatay göz hareketi ile zihinsel "
     "koşullulandırma) artefaktı bilgiye çevirebilir. Buna karşılık, kırpma "
     "gibi kaynaklardan gelen artefaktlar kırpma kanalından taşınan ikinci bir "
     "elektrotla veya Empedans (bimodül) eşikleriyle bastırılır."),

    ("h2", "2.4. Sinyal İşleme Zinciri"),
    ("p",
     "Bir BCI çıkarım zinciri tipik olarak yedi aşamadan oluşur ve her aşamadaki "
     "tasarım kararı toplam performansı belirler."),
    ("bullet",
     "(1) On işleme: filtreleme, yeniden örnekleme, kanalların seçimi ve "
     "artefakt bastırma."),
    ("bullet",
     "(2) Özellik çıkarımı: zaman alanı (güçlük, varyans, istatistikler), frekans "
     "alanı (bant gücü, oransal bant gücü) ve zaman-frekans alanı (kısa zamanli "
     "Fourier dönüşümü, dalgacık) temelli özellikler."),
    ("bullet",
     "(3) Özellik seçimi ve boyut azaltma: bilgi kazanı oranları, isabetli "
     "seçilim, kabalaştırma veya öğrenmeye dayalı gömülü yöntemler."),
    ("bullet",
     "(4) Sınıflandırma: doğrusal diskriminant analizi, destek vektör makineleri, "
     "lojistik regresyon, rastgele orman ve derin öğrenme."),
    ("bullet",
     "(5) Üç durumlu çıkarım: sistem yalnızca iki sınıf arasında karar vermek "
     "zorunda değildir; bir duruşma aralığında (bkz. sabit duruş, hazır, "
     "tetikleme) kalmasına izin vermek, kontrol yükünü azaltır."),
    ("bullet",
     "(6) Geri besleme aracı: sanal imleç, gerçek zamanli görsel geri bildirim, "
     "sonuç yanlış olduğunda düzeltme haklı."),
    ("bullet",
     "(7) Uyarlama ve öğretim: sistemin kullanıcıdan göre güncellenmesi."),
    ("p",
     "İki ek parametre her tasarımı belirler. İlki gecikmişsiz, ikincisi "
     "kararlılıktır. BCI sistemlerinin en sık tartışılan ikilemi budur: kısa "
     "gecikmeli sistemler hızlı hissettirir ama hatalı karar oranını artırır; "
     "kararlı sistemler hatayı azaltır ama kullanıcıyı yorar ve akışından çıkarır. "
     "Bu nedenle 'doğru cevap' sorusu kadar 'kullanılabilir cevap' sorusu da "
     "önemlidir."),

    ("h2", "2.5. Evrensel BCI Kavramı"),
    ("p",
     "Her kullanıcıya uygun tek bir sistem olmadığı görülünce, alanda evrensel "
     "(universal) BCI kavramı geliştirildi. Evrensel BCI, kullanıcının eğitim "
     "verilmeden, hatta bilinçli komut üretmeden sistemi kullanabilmesi hedefini "
     "taşır. Buna ulaşmak iki zorluk barındırır. İlki, ör. kafatasındaki "
     "anatomik ve elektrofizyolojik farklılıkların kanal kalıplarını ve özellik "
     "dağılımlarını değiştirmesidir; bu, sabit bir öznitelik uzayının her "
     "kullanıcıya taşınamamasına yol açar. İkincisi, bireysel öznitelik "
     "uzaylarinin veri azlığı nedeniyle kararlı olmamasıdır."),

    ("p",
     "Bu zorluklara yönelik iki strateji belirginleşti. Birincisi, veri "
     "augmentasyonu ve alan uyarlaması (domain adaptation): kaynak kullanıcıdan "
     "hedef kullanıcıya transfer yaparak etiketsiz hedef veriden yararlanır. "
     "İkincisi, dikkat mekanizması ve transformer temelli zaman-serisi modelleri: "
     "çift yönlü (encoder-decoder) mimariler sinyali iki yönden işleme ve "
     "zaman bağımlılıklarını modelleme yetenekleri kazandırır. Her iki yönelim de "
     "önerilen etiklik ve klinik geçerlilik sorunlarını çözmektedir."),
]
