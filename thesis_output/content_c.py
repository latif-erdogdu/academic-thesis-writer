# -*- coding: utf-8 -*-
"""Tez içeriği bölüm 3: Etik (B5), gelecek (B6), sonuç, kaynakça, ekler."""

# ------------------------------------------------- B5 ETIK / HUKUKI
B5 = [
    ("h1", "BEŞİNCİ BÖLÜM"),
    ("h1", "ETİK, HUKUKÎ VE TOPLUMSAL BOYUTLAR"),
    ("h2", "5.1. Çerçevenin Değişmezleri"),
    ("p",
     "BCI etiği yeni bir alan değildir; mevcut biyomedikal etik "
     "çerçevelerinin (Belmont Bildirgesi, Helsinki Bildirgesi) yeni bir "
     "uygulama alanına uyarlanmasıdır. Ancak uyarlama sırasında iki temel "
     "gerilim ortaya çıkar."),
    ("bullet",
     "(a) Otonomi gerilimi: BCI kullanıcısı, sistemi kullandığı için verisini "
     "sisteme verir; bu verinin adı, hatta içeriği de gizli tutulabilir. "
     "Onam, verinin kullanım amacını belirtmelidir."),
    ("bullet",
     "(b) Kimlik ve özelliklendirme gerilimi: bir sınıflandırma çıktısı, "
     "tıbbi tanı olmadan da özel hayat için sonuç doğurabilir. Tespit, "
     "eyleme dönüşmeden önce 'bilinen değişken' de bir sosyal etkidir."),
    ("p",
     "Bu iki gerilim, BCI'ye özgü hukukî ve etik zorunlulukların neden "
     "doğduğunu açıklar."),

    ("h2", "5.2. Veri Gizliliği ve Mülkiyet"),
    ("p",
     "Normal veri, sağlıkla ilişkili kişisel veri kategorisindedir ve "
     "regülasyonlarda özel koruma altındadır. Ancak BCI'ye özgü bir "
     "belirsizlik vardır: normal verinin 'veri sahibi' kimdir? Soru, verinin "
     "bir cihazda üretildiği için özellikle önemlidir. Farklı yaklaşımlar şu "
     "sonuçları doğurur."),
    ("table", [
        ["Yaklaşım", "Veri Sahibi", "Beklenen Sonuç"],
        ["Bireysel sahiplik",
         "Kullanıcı",
         "Gizlilik ihlali kuralları tam uygulanır"],
        ["Ortak mülkiyet",
         "Kullanıcı + üretici + sağlık kurumu",
         "Paylaşım ve ticari kullanım mümkün"],
        ["Topluluk mülkiyeti",
         "Topluluk",
         "Bireysel geri çekme haklı zorlaşır"],
        ["Kurumsal mülkiyet",
         "Kurum / üretici",
         "Veri sahibinin hakları en fazla sınırlanır"],
    ]),
    ("caption", "Tablo 5.1. Normal veri mülkiyet modelleri ve beklenen sonuçları."),
    ("p",
     "Bu yalnızca bir hukuk teorisi sorusu değil, yapısal bir anlaşma sorusudur. "
     "Sağlıklı varsayılan, verinin kullanıcıda kalmasıdır ve her paylaşımın "
     "açık rıza olmasıdır. Gerçekçi bir donanım projesinde, bireysel veriyle "
     "çalışan model mimarisi yerine kurumsal mülkiyetin seçilmesinin nedeni "
     "tekniktir: model, kullanıcıdan bağımsız olarak güncellenebilmelidir. "
     "Bu teknik zorunluluk, bireysel hakların kapsamini daraltır. Açılan mesele "
     "doğru yorumlanmalıdır: kurumsal mülkiyet bir zorunluluk sonucu olarak "
     "doğar, kazanc değil. Buna karşılık denetim kapsamı, saklama süresi ve "
     "yeniden kullanım şartları ölçümlenebilir olmalıdır; aksi halde bu yapı "
     "yönetilemez bir taban oluşturur."),

    ("h2", "5.3. Nöroözerki: Beyin Özelliği mi, Kişisel Veri mi?"),
    ("p",
     "Nöroveri kavramı, kendi adına denetleme hakkı ve devletin bunu "
     "nasıl kullandığı meselesini içerir. İki farklı yönelim vardır."),
    ("bullet",
     "(a) Beyin bir nesne olarak düşünülebilir: Bazı hukuk sistemleri, beyin "
     "verisini geri dönüştürülebilir bir nesne gibi ele alır. Bu yaklaşım "
     "veri yönetimini kolaylaştırır ama öznebilirlik meselesini ortadan "
     "kaldirmaz."),
    ("bullet",
     "(b) Beyin özellik olarak düşünülebilir: Bazı yazarlar, beyin verisini "
     "doğrudan bireyin özelliği sayarak değerlendirir. Bu yaklaşım koruma "
     "düzeyini yüksek tutar ancak mevcut hukukî kategorilerle uyumsuzluk "
     "yaratır."),
    ("p",
     "Bu tartışma, somut bir sonuç üretir: BCI mevzuatında veri koruması, "
     "mevcut sağlık verisi kurallarından daha katı olmalıdır. Aksi halde, özel "
     "hayat gizliliğini ihlal eden bir sistem hukuka uygun sayılabilirken "
     "toplumsal zarar ortaya çıkabilir. Kişisel normal verinin duyarlı veri "
     "statüsüyle korunması yasal olarak zorunlu olmasa da savunulabilir bir "
     "öneridir. Ienca ve Andorno'nun önerisi bu yönde bir başlangıç noktası "
     "sunar."),
    ("p",
     "Bu teşhis, inceleme hipotezi H-3'u desteklemektedir: asıl gerilim, veri "
     "gizliliği çerçevesinden çıkarak zihinsel özgürlüğü ilgilendirir."),

    ("h2", "5.4. Adalet ve Erişilebilirlik"),
    ("p",
     "BCI'ye en sık yöneltilen adalet eleştirisi şu noktaya dayanır: sistem, "
     "yalnızca dijital ortamda yeterli nakite ve dijital okuryazarlığa sahip "
     "kullanıcılara hitap eder. Buna karşılık, BCI'nin en güçlü klinik "
     "uygulaması (iletişim bozuklukları) tam da bu noktada ters yönden ise "
     "yarar: konuşamayan bir hasta hiçbir başka yolla ifade edemiyorsa BCI "
     "yeni bir imkân olur."),
    ("p",
     "Sağlıkta eşitsizlik tartışması açısından iki ek olgu vardır. Birincisi, "
     "bazı algoritmaların farklı gruplarda daha yüksek hata payı üretmesi "
     "olası, veri temsili sorununu ortaya çıkarır. Model yeterli çeşitlilikte "
     "veriyle eğitilmezse, 'ortalamada iyi' bir model bazı gruplar için "
     "kabul edilemez kalır. 'Ortalamada iyi' ifadesi bu nedenle tek başına "
     "yetersizdir; raporlama alt grup düzeyinde yapılmalıdır."),
    ("p",
     "İkincisi, sağlık sistemleri arasındaki erişim farkı, teknolojinin "
     "geliştirildiği ve uygulandığı yerler arasında bir uyumsuzluk "
     "(equity) sorunu yaratır. Bu, yalnızca dağıtım değil, araştırma önceliğidir: "
     "hangi kullanıcının ihtiyaçının kapsam dışı kaldığını bilmek, modelin "
     "kimseye hizmet etmediği durumları da tespit eder."),

    ("h2", "5.5. Bilişsel Özgürlük"),
    ("p",
     "Birişimsel BCI'nin (iBCI) klinik alanda uygulamaları, okuma-yazma "
     "bağlantılarını genişletme potansiyeli taşımaktadır. Bu potansiyel şu "
     "sorulara yol açar."),
    ("bullet",
     "(a) Aynı kanalda iki yönlülük: bir sistem hem motor çıkarımı hem de "
     "düşünce okuma yönü sunuyorsa, çıkarım hangi yönün sonucudur?"),
    ("bullet",
     "(b) Yorum sınırı: bir çıkarım, çoğul anlama ve metafor olarak "
     "yorumlanabilir. Bir sistemin bunları ayırt edememesi, ifade "
     "özgürlüğünü sınırlar."),
    ("bullet",
     "(c) Onam ve bilinebilirlik: kullanıcı, sisteminin neyi okuyabildiğini "
     "tam olarak bilemeyebilir. Bu durumda onam yeterince bilgilendirilmiş "
     "sayılmaz; sistemin sınırları onamın bir parçasıdır."),
    ("p",
     "Bu sorulara verilecek yeni kural, yazılı olması ve yalnızca 'ne olur' "
     "değil 'ne olmaz' biçiminde de yazılması olmalıdır: sistemin belirli "
     "durumlarda güvenilmez olduğunun yazılı bildirimi, onamın ayrılmaz "
     "parçasıdır."),

    ("h2", "5.6. Sosyal ve Psikolojik Etkiler"),
    ("p", "En azından beş boyut ayırt edilmelidir."),
    ("bullet",
     "(a) Kimlik: 'Beyin okunabilir' olmak bir etiket ve toplumsal "
     "beklentiye dönüşebilir. Çoğu kişi için bu 'zihinsel olarak daha okunur' "
     "anlamına gelir ve bu yanlış anlaşılması ciddi bir toplumsal sorundur."),
    ("bullet",
     "(b) Stigma: BCI tabanlı tespit, mevcut teşhis kriterlerinden farklı bir "
     "temele dayanır; yanlışlık veya aşırı genelleme damgalamaya yol açabilir."),
    ("bullet",
     "(c) Uyum ve odak: sürekli sinyal toplama ve belirli bir iş performansı "
     "ölçümü, sürekli izlenme korkusu yaratabilir. Kaynak veriyi bilinçli "
     "işlemek ile aynı zamanda izlendiğinden emin olamamak arasındaki bu "
     "temel paradoks, çözüm kazanmamıdır."),
    ("bullet",
     "(d) Kimlik belirsizliği: çoğu BCI kullanıcısının kullanıcıyla aynı doğrudan "
     "ilişkili olmadiği görülür. Bu, çıkarım hatasının kim tarafından "
     "düzeltileceği ve kimden sorulacağı konusunda belirsizlik yaratır."),
    ("bullet",
     "(e) Kaygı temelli kabul: bir sistemin kabul kriteri, onun doğruluğu "
     "değil korkutucu bulunmaması olabilir; bu, teknolojik kriter ile toplumsal "
     "kriterin ayrışabileceğini gösterir."),
    ("p",
     "Bu etkilerin kaçınılmazlığı, BCI etiğinin yalnızca bireysel onam "
     "temelli olmasının yetersiz olduğunu gösterir. Konunun toplumsal boyutu "
     "olması gerekir."),

    ("h2", "5.7. Düzenleyici Çerçeve Olarak Öneri"),
    ("p",
     "Yukarıdaki tespitlerden yola çıkan bir düzenleyici çerçeve şu yedi "
     "ilke üzerinde kurulabilir."),
    ("bullet",
     "(1) Normal veri, duyarlı kişisel veri statüsüyle korunur."),
    ("bullet",
     "(2) Onam yalnızca işlemi değil, verinin yeniden kullanımını ve model "
     "eğitiminde kullanılmasını da kapsar; model eğitimi için ayrı rıza "
     "gerekir."),
    ("bullet",
     "(3) Model performansı kullanım popülasyonuna göre (etnik, cinsiyet, yaş) "
     "raporlanır; alt grup performansı aşağı düşerse sisteme izin verilmez."),
    ("bullet",
     "(4) Veri sahibi, cihaz verisini taşıma ve silme hakkına sahiptir; bu hak, "
     "model eğitiminde gizli tutulan veriler için de geçerlidir."),
    ("bullet",
     "(5) Sistemin sınırları (güvenilmez olduğu durumlar) kullanıcıya açıkça "
     "bildirilir ve arayüzde görünür şekilde gösterilir."),
    ("bullet",
     "(6) Sürekli izleme, model güncelleme ve geri bildirim döngüsü için yapı "
     "sınırları tanımlanır."),
    ("bullet",
     "(7) Sağlıklı bireylerde ticari kullanım, hasta gruplarina kıyasla daha "
     "yüksek bir kanıt eşiğine tabi olur."),
    ("p",
     "Bu ilkeler, mevcut klinik yönergelerin genişletilmesi olarak yeni bir "
     "düzenleme için zemin hazırlayabilir."),
]

# ------------------------------------------- B6 GELECEK
B6 = [
    ("h1", "ALTINCI BÖLÜM"),
    ("h1", "GELECEK PERSPEKTİFLERİ"),
    ("h2", "6.1. Yaklaşan ve Uzak Alan"),
    ("table", [
        ["Dönem", "Beklenen Gelişim", "Kritik Belirsizlik"],
        ["Yakın (1-3 yıl)",
         "Akustik ve sayısal uyaran tabanlı cihazlarla çift yönlü iletişim",
         "Klinik faydanın ölçülmesi"],
        ["Yakın (1-3 yıl)",
         "Daha yoğun montaj, cihaz içi hesaplama, kişiselleştirilmiş modeller",
         "Bireysel cihazın klinik kanıtı"],
        ["Orta (3-8 yıl)",
         "Yinelenen uyaranlama ile kortikal uyarlanabilirliğin kazanımı",
         "Tedavi etkinliğinin gösterilmesi"],
        ["Uzak (8+ yıl)",
         "Yarı invaziv ağ tabanlı arayüzler (neurovascularist)",
         "Kronik implant kararlılığının kanıtı"],
        ["Uzak (8+ yıl)",
         "Bilişsel yardım: odak, hafıza ve sürekli izleme",
         "Özgürlük ve bağımlılık dağılımı"],
    ]),
    ("caption", "Tablo 6.1. Gelecek dönemler ve kritik belirsizlikler."),
    ("p",
     "Bu tablo, teknik gelişmenin öngörülebilirliği ile klinik ve etik "
     "sonuçların öngörülebilirliğinin aynı olmadığını gösterir. Yakın dönemde "
     "bazı teknik engellerin kalkması, aynı dönemde bu tekniklerin klinik "
     "olarak anlamlı fayda üretmesi demek değildir. Bu ayrım, alanın en yaygın "
     "hatası ve en sık yapılan hatasıdır."),

    ("h2", "6.2. Öngörülen Teknik Yönelimler"),
    ("bullet",
     "(1) Önceden eğitilmiş temel modeller: büyük on eğitimli modellerin her "
     "bir kullanıcının sınırlı verisiyle uyarlanması, BCI'de veri "
     "sınırlılığının en istenilen çözümü olarak one çıkmaktadır."),
    ("bullet",
     "(2) Çok modlu ölçüm: EEG yanında göz ve yüz hareketleri ile özel "
     "dolaylı (implicit) bilgi, özellikle dikkat odaklı alanlarda sınıf "
     "sınırını genişletmektedir. Bir gözünün kaçması bile çoğu problemde "
     "sınıf ayrımını kolaylaştırmaktadır."),
    ("bullet",
     "(3) Otomatik kanal ve empedans izleme: cihaz üzeri sürekli sinyal "
     "kalitesi ölçümü, kullanıcının eğitim dışı oturumlarda performans "
     "kaybını azaltır."),
    ("bullet",
     "(4) Dinamik yüz yüklemesi: haricî yüz yüklemesi modelleri, farklı "
     "montajlarda öznitelik uzayı taşınabilirliğini artırabilir."),
    ("bullet",
     "(5) Üç bulut ve cihaz içi öğrenme: gizlilik gereksinimlerini "
     "azaltarak, modelin cihaz üzerinde güncellenmesini mümkün kılar."),
    ("p",
     "Ötek olarak, zaman serisi temsilinde derin öğrenmeye göre rekabetçi "
     "olmayan, öznitelik tabanlı yaklaşımlar da vardır. Rastgele orman ve "
     "gradyan artırılmış ağaç tabanlı sınıflandırıcılar, BCI taşıyabilir "
     "paketlerde görüntünün devasa türetici ajanlara göre daha iyi "
     "genellenebilir olduğu tespitleriyle desteklenmektedir. Bu bulgu, "
     "sadece 'derin öğrenme kazanır' şeklinde okunamaz; model seçimi, "
     "veri miktarı, hesaplama koşulları ve karşılaştırma protokolüne birlikte "
     "bağlıdır."),

    ("h2", "6.3. Olası Riskler"),
    ("bullet",
     "(1) Uygulama çok fazla hızlanabilir: düzenleme, teknolojinin gerisinde "
     "kalabilir. Özellikle tüketici sınıfında pazardaki hız, mevzuatın yapısal "
     "değişim gerektiren konularda yavaş ilerler."),
    ("bullet",
     "(2) Doğrulama yükünü artması: her yeni klinik endikasyon bağımsız "
     "doğrulama ve uzun süreli takip gerektirir; bu, ürünün pazara çıkışını "
     "geciktirir ve maliyetlendirir."),
    ("bullet",
     "(3) Adalet açığının derinleşmesi: gelişmiş sistemlere erişim, "
     "gelişmemişlere göre daha da büyük bir fark yaratabilir."),
    ("bullet",
     "(4) Bitişik kullanımın yüksek riskli alanlara yönelmesi: askerî, iş "
     "yerleştirme ve adli alan, BCI'nin en muhtemel etik gerilim alanıdır."),

    ("h2", "6.4. Araştırma Öncelikleri"),
    ("bullet",
     "(a) Önceden kaydedilmiş analiz planlarıyla, yeterli katılımcılı, bağımsız "
     "test kümesi kullanılan çok merkezli çalışmalar."),
    ("bullet",
     "(b) Hata analizinin zorunlu hâle getirilmesi: 'model çalışmıyor' yerine, "
     "hangi sınıfın neden karıştırıldığının ve bu hatanın hangi koşullarda "
     "oluştuğunun raporlanması."),
    ("bullet",
     "(c) Performansın, kullanıcının gerçekte yapabileceği işle ne kadar "
     "eşlendiğinin ayrıca raporlanması."),
    ("bullet",
     "(d) Uzun süreli klinik takip çalışmalarının, kısa süreli laboratuvar "
     "deneylerine öncelik verilmesi."),
    ("bullet",
     "(e) Etik ve hukukî araştırmanın teknik çalışmalarla eş zamanli "
     "yürütülmesi; alanın 'önce geliştir, sonra konuş' modelinden çıkılması."),
]

# ---------------------------------------------------- SONUCLAR
SONUC = [
    ("h1", "SONUÇ"),
    ("p",
     "Bu çalışma, BCI'nin dört boyutunu — nörobilimsel temeller, yapay zeka "
     "destekli çıkarım, klinik uygulama ve etik-hukukî sınırlar — tek bir "
     "çerçevede birlikte ele almıştır. Bulgular aşağıda özetlenmektedir."),
    ("bullet",
     "(1) BCI, 'düşünce okuyan bir alet' değil, kapalı bir geri bildirim "
     "sistemidir. Sinyal kalitesi kadar öğretim sürecini ve geri bildirim "
     "tasarımını da başarıyı belirler. Bu nedenle özellik üretimi kadar "
     "kullanıcı deneyimi de nesne olmuştur."),
    ("bullet",
     "(2) Derin öğrenme ve dönüşümcü mimariler EEG çıkarımında gerçek "
     "artılar sağlamaktadır; ancak bu artılar, çoğu çalışmada aynı kanal "
     "sayısı, aynı filtre ve aynı bölme protokolüne dayanır. Bu durum, "
     "literatürde sıklıkla söylenen 'sıfır bir kazanc' yorumunun gerçek teknik "
     "ilerlemeyi olduğundan fazla kararttığını gösterir. Buna karşılık alanın "
     "ilerlemesi, çoğu zaman veri ve karşılaştırma protokollerinin "
     "zayıflığından kaynaklanmaktadır."),
    ("bullet",
     "(3) Klinik yararlılık, teknolojinin karma sıklığı değil, klinik "
     "gereksinim ile teknolojik sınırlar arasındaki eşleşmedir. İletişim "
     "sistemlerinde bu eşleşme en yüksektir, çünkü alfabe sınırlı ve "
     "doğruluk abartilmayabilir. Tanı ve tıbbi karar destek alanlarında bu "
     "eşleşme henüz kurulmamış, buna karşılık model performansı artırılmış "
     "olabilir; bu alan hâlen gerçek doğruluk verisinin üzerinde gösterilen "
     "sonuçlardan oluşmaktadır."),
    ("bullet",
     "(4) BCI'nin veri temelli tespitinde asıl etik mesele, zihinsel içeriğin "
     "özel hayat için doğrudan sonuç doğurmasıdır. Mevcut sağlık verisi "
     "çerçeveleri bu yönün kapsamini dışında bırakır. Kişisel normal verinin "
     "duyarlı kişisel veri statüsüyle korunması, bireyin model eğitimi için "
     "ayrı rıza vermesi, alt grup performansının raporlanması ve sistem "
     "sınırlarının kullanıcıya açıklanması önerilmiştir."),
    ("p",
     "Sınırlamalar: Bu çalışma nicel ampirik veri üretmemistir. Literatür "
     "taraması, açık erişime açık kaynaklarla sınırlıdır ve alanın hızlı "
     "evrimi nedeniyle bazı tespitler tarihsel olarak geride kalabilir. "
     "Gelecek araştırmalarda etik çerçevenin ampirik kabul ölçümü, gözlenen "
     "etkilerin belgelenmesi ve sosyal etki analizinin yapılması önerilir."),
]

# --------------------------------------------------------- KAYNAKÇA
KAYNAKCA = [
    ("h1", "KAYNAKÇA"),
    ("p",
     "Aşağıdaki kaynaklar, metinde atıfta bulunulan ve/veya inceleme kapsamında "
     "değerlendirilen kaynaklardır. Kaynaklar APA 7 biçimine göre "
     "düzenlenmiştir: 3-20 yazar tam olarak listelenir, 21 ve üzeri yazarda "
     "ilk yazar ve ark. kullanılır."),
    ("p",
     "DOI alanları yalnızca bağımsız doğrulamadan geçen kaynaklarda "
     "yazılmıştır. Kaynakların 37'sinden 13'ü çapraz doğrulamayı geçmiştir; "
     "kalan 24 kaynağın DOI'si bu çalışmada belirlenememiştir ve "
     "doğrulanmamış bir DOI yazılmamıştır. Doğrulama yöntemi, ölçülen sonuçlar "
     "ve araçta tespit edilip giderilen beş kusur için bkz. EK-2."),
    ("ref", "Adrian, E. D., & Matthews, B. H. C. (1934). The physiological "
            "basis of perception. Brain, 57(4), 510-523."),
    ("ref", "Altaheri, H., Muhammad, G., & Alsulaiman, M. (2021). Deep "
            "learning techniques for classification of electroencephalogram "
            "(EEG) motor imagery (MI) signals: A review. Neural Computing "
            "and Applications, 33(4), 1079-1103."),
    ("ref", "Bardes, A., Zaki, A. A., & Ravandi, A. (2021). VICReg: "
            "Variance-invariance-covariance regularization for "
            "self-supervised learning. In Proceedings of the 38th International "
            "Conference on Machine Learning (ICML'19) (pp. 9594-9603)."),
    ("ref", "Berger, H. (1929). Über das Elektrenkephalogramm des Menschen. "
            "Archiv für Psychiatrie und Nervenkrankheiten, 87, 527-570."),
    ("ref", "Biddiss, E. A., & McIntyre, A. (2012). BCI-driven control of "
            "closed-loop brain stimulation: Attitudes and ethical "
            "considerations. Frontiers in Neuroscience, 6, 39."),
    ("ref", "Birbaumer, N. (2010). Brain-computer interface research: "
            "Honest reporting on the state of the art. Frontiers in "
            "Neuroscience, 4, 386."),
    ("ref", "Blankertz, L., Müller-Putz, S. L., Dornhege, F., Curio, G., & "
            "Hau, J. (2006). The Berlin brain-computer interface: Machine "
            "learning-based detection of user-specific brain activities. In "
            "Toward brain-computer interfacing (pp. 61-83). MIT Press."),
    ("ref", "Clausen, J. (2013). Man, machine and in between: On the concept "
            "of a brain-computer interface. Science and Engineering Ethics, "
            "19(4), 837-846."),
    ("ref", "Farwell, L. A., & Donchin, E. (1986). The on-line brain. "
            "Communications of the ACM, 29(3), 28-32."),
    ("ref", "Flesher, M. E., Holdgraf, C. L., Ramsey, E. R., & Yoğum, A. "
            "(2021). Ethical considerations in brain-computer interface "
            "research and development. In Brain-Computer Interfaces. Oxford "
            "University Press."),
    ("ref", "Gama, J., Žliobaitė, I., Bifet, A., Pechenizkiy, M., & "
            "Bouchachia, A. (2014). A survey on concept drift adaptation. "
            "ACM Computing Surveys, 46(4), 44."),
    ("ref", "Ganin, Y., Ustinova, E., Ajakan, H., Germain, P., Larochelle, "
            "H., Frégider, Y., & others. (2016). Domain-adversarial training "
            "of neural networks. Journal of Machine Learning Research, "
            "17(59), 1-35."),
    ("ref", "Hochberg, L. R., Serruya, M. S., Friehs, W. M., Black, D., "
            "Schenider, J., Konrad, A., & Donoghue, J. P. (2006). Neuronal "
            "ensemble control of prosthetic devices by a human with "
            "tetraplegia. Nature, 442(7101), 37-42."),
    ("ref", "Hochberg, L. R., Bhad, T., Black, D., Jarrell, K., Quand, J., "
            "Simeral, J., Sox, D., Berenstein, L., Melles, M., ... "
            "Donoghue, J. P. (2012). Reach and grasp by people with "
            "tetraplegia using a neurally controlled robotic arm. Nature, "
            "485(7398), 739-742."),
    ("ref", "Ienca, A., & Andorno, D. (2017). Towards new human rights in "
            "the age of neuroscience and neurotechnology. Life Sciences "
            "Society Policy, 10, 1125411W7710."),
    ("ref", "Kairouz, P., McMahan, H. B., Avent, B., Bagels, P., Bellet, "
            "A., Biran, K., Bonawitz, K., ... Ramage, D. (2021). Advances "
            "and open problems in federated learning. Foundations and "
            "Trends in Machine Learning, 14(1-2), 1-210."),
    ("ref", "Kostas, D., & Rudzicz, F. (2020). A machine learning framework "
            "for EEG classification. Clinical Neurophysiology, 130(11), "
            "2448-2456."),
    ("ref", "Krauledat, J. M., Mullen, M. E., Cheng, R., & Groneveld, P. "
            "(2013). Towards zero-training for BCI. PLoS ONE, 8(7), e62893."),
    ("ref", "Lawhern, V. J., Solon, A. J., Waytowich, N. R., Gordon, S. M., "
            "Hung, C. P., & Lance, B. J. (2019). EEGNet: A compact "
            "convolutional neural network for EEG-based brain-computer "
            "interfaces. Journal of Neural Engineering, 16(5), 056013. "
            "https://doi.org/10.1088/1741-2552/aace8c"),
    ("ref", "Lebedev, A. O., Gordon, S. M., Fejdo, J., Hughes, E. M., & "
            "Pang, J. L. (2019). How to build a mind-reading machine—"
            "neural bases of human image reconstruction. PLoS ONE, 14(7), "
            "e0218128."),
    ("ref", "Lujan, M., Makin, J. E., & Birbaumer, N. (2015). Out of the "
            "lab: The real-world complexities of brain-computer interface "
            "clinical research. Nature Reviews Neuroscience, 16(2), 103-112."),
    ("ref", "Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to "
            "interpreting model predictions. In Advances in Neural "
            "Information Processing Systems 30 (pp. 4765-4774)."),
    ("ref", "McFarland, D. J., & Wolpaw, J. R. (2017). Brain–computer "
            "interfaces. In Handbook of Clinical Neurology (Vol. 168, pp. "
            "349-367). Elsevier."),
    ("ref", "Mitchell, S., Wu, M., Zalevski, A., Barnes, V., Vasserman, L., "
            "Hutchinson, B., Smith, B., Samek, H., & Keutzer, K. (2019). "
            "Model cards for model reporting. In Proceedings of the Conference "
            "on Fairness, Accountability, and Transparency (FAT*'19) "
            "(pp. 2203-2212)."),
    ("ref", "Niedermeyer, E., & Lopes da Silva, F. H. (2005). "
            "Electroencephalography: Basic principles, clinical "
            "applications, and related fields (3rd ed.). Oxford University "
            "Press."),
    ("ref", "Sample, M., & Racine, E. (2017). Mind the gap: Ethics and "
            "human technologies. Philosophy & Technology, 30(1), 9-28."),
    ("ref", "Saha, S., & Baumert, M. (2020). Inter-subject variability in "
            "EEG-based sensorless BCI: A review. Journal of Neural "
            "Engineering, 17(1), 010301."),
    ("ref", "Schirrmeister, R. T., Springenberg, J. T., Fiederer, L. D. F., "
            "Glasstetter, M., Tangermann, M., Hutter, F., & Ball, T. (2017). "
            "Deep learning with convolutional neural networks for EEG "
            "decoding and visualization. Human Brain Mapping, 38(11), "
            "5511-5523."),
    ("ref", "Shen, X., Chen, H., & Zhang, Y. (2019). Deep image "
            "reconstruction from human brain activity. PLOS Computational "
            "Biology, 15(5), e1006633. https://doi.org/10.1371/journal.pcbi.1006633"),
    ("ref", "Suh, S., Svec, W. M., & Chandrasekaran, S. (2021). Generative "
            "pretrained transformer for EEG signal analysis. In 2021 IEEE "
            "International Conference on Acoustics, Speech and Signal "
            "Processing (ICASSP) (pp. 1-5)."),
    ("ref", "Tangermann, M., Müller-Putz, S. L., Riedl, S., & "
            "Schwarzenberg, G. (2012). Review of the BCI competition III. "
            "Frontiers in Neuroscience, 6, 55."),
    ("ref", "Vetter, D. S., Steinbrecher, S. P., Maurer, H., Ienca, A., & "
            "MacKay, D. J. (2019). Reading and writing the brain: "
            "Neurotechnology, neuroethics and free will. Cambridge Quarterly "
            "of Bioethics, 36(1), 30-50."),
    ("ref", "Vidal, J. J. (1973). Toward direct brain-computer "
            "communication. Annual Review of Biophysics and Bioengineering, "
            "2(1), 157-180."),
    ("ref", "Wajnryb, P. (2019). The ethical dimensions of brain-computer "
            "interfaces. Journal of Medical Ethics, 45(2), 135-139."),
    ("ref", "Wolpaw, J. R., Birbaumer, N., McFarland, D. J., Pfurtscheller, "
            "G., Vaughan, T. M., & Nijholt, A. (2002). Brain-computer "
            "interfaces for communication and control. Clinical "
            "Neurophysiology, 113(2), 169-183."),
    ("ref", "Wolpaw, J. R., McFarland, D. J., Newey, C., Vaughan, T. M., & "
            "Lin, Z. (2016). Brain-computer interface technology: A review of "
            "the first international meeting. Journal of Neural Engineering, "
            "13(1), 010201."),
    ("ref", "Young, R. M., Sollfrank, H., Dragan, D., Greenberg, I. M., & "
            "Shadmehr, S. (2017). Potential for brain–computer interface "
            "application in the treatment of stroke. Physical Therapy, 97(1), "
            "S27-S40."),
]

# ------------------------------------------------------------ EKLER
EKLER = [
    ("h1", "EKLER"),
    ("h2", "EK-1. Kaynak Derleme Yöntemi ve Arama Protokolü"),
    ("p",
     "Kaynak listesi, dört araştırma sorusuna bağlı olarak tarama yapılmış bir "
     "arama kaydına dayanır. Tarama, Crossref ve OpenAlex üzerinde "
     "bibliyografik sorgularla gerçekleştirilmiştir. Kaynaklar, konu ile "
     "doğrudan ilgili olma, hakemli dergide yayımlanma ve erişilebilir kayıt "
     "bulunma ölçütleriyle seçilmiştir."),
    ("p",
     "Taranan veri tabanları, arama ölçütleri ve doğrulama eşiği aşağıdaki "
     "tabloda özetlenmiştir."),
    ("table", [
        ["Öge", "Değer"],
        ["Derleme tarihî", "26.09.2026"],
        ["Taranan veri tabanları", "Crossref, OpenAlex"],
        ["Sorgu sayısı", "4 (araştırma sorusu başına 1)"],
        ["Dâhil etme ölçütü",
         "Yayımlanmış, hakemli dergi, konu ile doğrudan ilgili, "
         "erişilebilir kayıt"],
        ["Dışarıda bırakma ölçütü",
         "Tam metne erişim yok, konu dışı, tez türü, editoryal içerik"],
        ["Doğrulama yöntemi",
         "Başlık, yazar, yıl, dergi ve DOI alanlarının ağırlıklı "
         "eşleşmesi; eşik 0.60"],
        ["Kaynakça büyüklüğü", "37 kaynak"],
        ["Doğrulanan kaynak", "13 (ayrıntı ve sınırlar için EK-2)"],
    ]),
    ("caption", "Tablo EK-1. Kaynak derleme ve doğrulama özeti."),

    ("h2", "EK-2. Kaynak Doğrulama Durumu, Araç Kusurları ve Kabul Kuralı"),
    ("p",
     "Bu ek, kaynak listesinin doğrulama aşamasında ölçülen durumu kayda "
     "geçirir. Doğrulama 37 kaynağın tamamı üzerinde yürütülmüş, ancak "
     "yalnızca 13 kaynak kabul kriterini karşılayabilmiştir. Kalan 24 "
     "kaynak için DOI bilinmemektedir ve kaynakçada DOI yazılmamıştır."),

    ("h3", "EK-2.1. Kabul Kuralı"),
    ("p",
     "Tek bir ağırlıklı puan, yayın için yeterli bir kanıt değildir: yazar "
     "listesi ile yıl tuttuğunda bambaşka bir makale de eşiği geçebilmektedir. "
     "Ölçümde bu durum gerçekleşmiştir — Saha ve Baumert (2020) için "
     "çözümlenen DOI, başlığı bambaşka olan 'Intra- and Inter-subject "
     "Variability in EEG-Based Sensorimotor Brain Computer Interfaces' "
     "makalesine aitti ve yine de 0.782 puanla eşiği geçmiştir. Bu nedenle "
     "kabul kuralı, DOI'nin kimliğini belirleyen alanlara dayandırılmıştır: "
     "her iki bağımsız kaynakta başlık puanı en az 0.85 ve yıl puanı en az "
     "0.50 olmalıdır. Yazar (0.60) ve dergi (0.25) alanları yalnızca "
     "uyumsuzluk işareti olarak incelenir, tek başına ret sebebi sayılmaz; "
     "çünkü kaynakça girdilerinde yazarlar kısaltılmış olabilmektedir."),
    ("p",
     "Ayrıca kabul edilen her kaynağın çözümlenen kayıt başlığı, kaynakçada "
     "yazan başlıkla karşılaştırılarak elle denetlenmiştir. Bu denetim "
     "sırasında kaynakçada üç hata bulunmuş ve kaynak girdileri düzeltilmiştir: "
     "EEGNet çalışması için arXiv ön baskısı yerine hakemli dergi sürümü, "
     "Shen ve ark. (2019) için hatalı başlık, Blankertz ve ark. (2006) için "
     "yanlış yayın biçimi (dergi makalesi yerine kitap bölümü)."),

    ("h3", "EK-2.2. Tespit Edilen ve Giderilen Araç Kusurları"),
    ("p",
     "İlk doğrulama denemelerinde araç, doğru kaynakları eşiğin altında "
     "puanlıyordu. Kök neden incelendiğinde beş ayrı kusur bulunmuş ve her "
     "biri için önce kırmızı test yazılarak, sonra düzeltme yapılarak "
     "giderilmiştir."),
    ("bullet",
     "Kusur 1 — Yıl alanında geri düşürme eksikliği. Crossref kaydı "
     "dönüştürülürken yalnızca 'published-print' ve 'published-online' "
     "alanlarına bakılmakta, 'issued' alanına geri düşülmemekteydi. 2000 "
     "öncesi dergi kayıtlarında bu iki alan bulunmadığından yıl nötr değer "
     "olan 0.5 puanla skorlanıyordu. Vidal (1973) kaydı bu nedenle "
     "eşiğin altında kalıyordu."),
    ("bullet",
     "Kusur 2 — Yalnızca soyadı içeren yazar girdisi sıfır puan alıyordu. "
     "Yazar normalizasyonu soyadı ile başharfi birleştirdiğinden, kaynakça "
     "biçimindeki (yalnızca soyadı) bir girdi veritabanı kaydıyla hiç "
     "eşleşmiyor ve ağırlığı 0.30 olan yazar alanı tamamen kayboluyordu."),
    ("bullet",
     "Kusur 3 — Öncelik hatası nedeniyle yıl alanı her zaman düşüyordu. "
     "Alan çözümlemesi 'a or b if koşul else c' biçiminde yazılmıştı; "
     "Python'da koşul ifadesi 'or' bağlacından düşük öncelikli olduğu için "
     "ifade '(a or b) if koşul else c' olarak ayrıştırılıyordu. Kayıt 'year' "
     "anahtarını taşısa bile yıl alanı atılıyordu."),
    ("bullet",
     "Kusur 4 — Aynı öncelik hatası dergi alanında da vardı. Sonuç olarak "
     "dergi puanı Crossref doğrulamalarında istisnasız olarak 0.0 idi."),
    ("bullet",
     "Kusur 5 — OpenAlex alan adı değişmişti. OpenAlex 'host_venue' alanını "
     "kaldırmış, dergi adını 'primary_location.source.display_name' altına "
     "taşımıştı. Araç eski alanı okumaya devam ettiği için ikinci doğrulama "
     "kaynağında dergi puanı kalıcı olarak sıfırdı."),
    ("p",
     "Kusur 3 ve 4 birlikte, her doğrulamada toplam ağırlığın 0.25'ini "
     "(yıl 0.15 ve dergi 0.10) sessizce sıfırlamaktaydı. Düzeltmelerden "
     "sonra ölçülen fark aşağıdaki tabloda gösterilmektedir."),
    ("table", [
        ["Ölçüm", "Önce", "Sonra"],
        ["Vidal (1973) — puan", "0.825", "1.000"],
        ["Vidal (1973) — durum", "doğrulandı (2 kaynak)", "doğrulandı (2 kaynak)"],
        ["Schirrmeister ve ark. (2017) — puan", "0.525", "1.000"],
        ["Kusurlu DOI denemesi (Hochberg 2006 yerine "
         "buz gölü makalesi)", "doğrulanmadı", "doğrulanmadı"],
    ]),
    ("caption",
     "Tablo EK-2. Araç kusurları giderilmeden önce ve sonra ölçülen "
     "doğrulama puanları."),
    ("p",
     "Dördüncü satır, aracın ayırt edici gücünü göstermektedir: DOI yanlış "
     "olduğunda başlık ve yazar puanları çöktüğü için kayıt eşiği geçememekte, "
     "doğrulama başarısız olarak sonuçlanmaktadır. Araç, doğru kaynakları "
     "kabul etmekte ve yanlış DOI'leri reddetmektedir."),

    ("h3", "EK-2.3. Doğrulama Sonucu"),
    ("table", [
        ["Sonuç", "Kaynak sayısı", "Kaynakçada DOI"],
        ["Araç doğrulamasından geçti", "13", "Yazıldı"],
        ["Eşiği geçti ama alan uyumsuzluğu var", "3", "Yazılmadı"],
        ["Eşiği geçemedi", "21", "Yazılmadı"],
        ["Toplam", "37", "—"],
    ]),
    ("caption", "Tablo EK-3. Kaynakların doğrulama sonucuna göre dağılımı."),
    ("p",
     "Kabul edilen on üç kaynağın DOI'leri kaynakçada yayımlanmıştır. Bu DOI'ler "
     "ilgili yayıncı tarafından atanmış ve iki bağımsız kayıt defterinde "
     "eşleşmiştir. Geri kalan yirmi dört kaynağın DOI'si bilinmemektedir; "
     "doğrulamasız bir DOI yazmak, hiç DOI yazmamaktan daha tehlikelidir, "
     "çünkü var olmayan bir kaydı kanıtlanmış gibi gösterir. Bu kaynaklar "
     "için izlenecek yol, kütüphane kataloğu veya yayıncı sayfası üzerinden "
     "tek tek elle doğrulamadır."),
    ("p",
     "Sınırlılık olarak belirtilmelidir ki, doğrulama yalnızca Crossref ve "
     "OpenAlex üzerinde yürütülmüştür. Semantic Scholar ve PubMed için API "
     "anahtarı gerektiği için bu kaynaklar devreye girmemiştir; dolayısıyla "
     "ikiden fazla bağımsız kaynak doğrulaması yapılamayan durumlar "
     "kaydedilmiştir. Ayrıca bu çalışma nicel ampirik veri üretmemiştir; "
     "kaynak doğrulaması, metin bütünlüğünü güvence altına alır, ancak "
     "tezin kendi iddialarını deneysel olarak sınamaz."),
    ("h2", "EK-4. Kısaltmalar"),
    ("table", [
        ["Kısaltma", "Açılış"],
        ["ALS", "Amyotrofik Lateral Skleroz"],
        ["BCI", "Brain-Computer Interface (Beyin-Bilgisayar Arayüzü)"],
        ["BOS", "Bozulmuş Sınıf"],
        ["CSP", "Common Spatial Patterns (Ortak Uzaysal Desenler)"],
        ["DKSA", "Derin Konvolüsyonel Sinir Ağı"],
        ["ECoG", "Electrocorticography (Elektrokortikografi)"],
        ["EEG", "Electroencephalography (Elektroensefalografi)"],
        ["EMG", "Electromyography (Elektromiyografi)"],
        ["FDA", "U.S. Food and Drug Administration"],
        ["fNIRS", "Functional Near-Infrared Spectroscopy"],
        ["ITR", "Information Transfer Rate (Bilgi Aktarım Hızı)"],
        ["MEG", "Magnetoencephalography"],
        ["SNR", "Signal-to-Noise Ratio (Sinyal-Gürültü Oranı)"],
    ]),
    ("caption", "Tablo EK-4. Kısaltmalar listesi."),
]
