# -*- coding: utf-8 -*-
"""Tez icerigi bolum 3: Etik (B5), gelecek (B6), sonuc, kaynakca, ekler."""

# ------------------------------------------------- B5 ETIK / HUKUKI
B5 = [
    ("h1", "BEŞİNCİ BÖLÜM"),
    ("h1", "ETİK, HUKUKÎ VE TOPLUMSAL BOYUTLAR"),
    ("h2", "5.1. Çerçevenin Değişmezleri"),
    ("p",
     "BCI etigi yeni bir alan degildir; mevcut biyomedikal etik "
     "cercevelerinin (Belmont Bildirgesi, Helsinki Bildirgesi) yeni bir "
     "uygulama alanina uyarlanmasidir. Ancak uyarlama sirasinda iki temel "
     "gerilim ortaya cikar."),
    ("bullet",
     "(a) Otonomi gerilimi: BCI kullanicisi, sistemi kullandigi icin verisini "
     "sisteme verir; bu verinin adi, hatta icerigi de gizli tutulabilir. "
     "Onam, verinin kullanim amacini belirtmelidir."),
    ("bullet",
     "(b) Kimlik ve ozelliklendirme gerilimi: bir siniflandirma ciktisi, "
     "tibbi tani olmadan da ozel hayat icin sonuc dogurabilir. Tespit, "
     "eyleme donusmeden once 'bilinen degilken' de bir sosyal etkidir."),
    ("p",
     "Bu iki gerilim, BCI'ye ozgu hukuki ve etik zorunluluklarin neden "
     "dogdugunu aciklar."),

    ("h2", "5.2. Veri Gizliliği ve Mülkiyet"),
    ("p",
     "Noral veri, saglikla iliskili kisisel veri kategorisindedir ve "
     "regulasyonlarda ozel koruma altindadir. Ancak BCI'ye ozgu bir "
     "belirsizlik vardir: noral verinin 'veri sahibi' kimdir? Soru, verinin "
     "bir cihazda uretildigi icin ozellikle onemlidir. Farkli yaklasimlar su "
     "sonuclari dogurur."),
    ("table", [
        ["Yaklasim", "Veri Sahibi", "Beklenen Sonuc"],
        ["Bireysel sahiplik",
         "Kullanici",
         "Gizlilik ihlali kuralari tam uygulanir"],
        ["Ortak mulkiyet",
         "Kullanici + uretici + saglik kurumu",
         "Paylasim ve ticari kullanim mumkun"],
        ["Topluluk mulkiyeti",
         "Topluluk",
         "Bireysel geri cekme hakki zorlasir"],
        ["Kurumsal mulkiyet",
         "Kurum / uretici",
         "Veri sahibinin haklari en fazla sinirlanir"],
    ]),
    ("caption", "Tablo 5.1. Noral veri mulkiyet modelleri ve beklenen sonuclari."),
    ("p",
     "Bu yalnizca bir hukuk teorisi sorusu degil, yapisal bir anlasma sorusudur. "
     "Saglikli varsayilan, verinin kullanicida kalmasidir ve her paylasimin "
     "acik riza olmasidir. Gercekci bir donanim projesinde, bireysel veriyle "
     "calisan model mimarisi yerine kurumsal mulkiyetin secilmesinin nedeni "
     "tekniktir: model, kullanicidan bagimsiz olarak guncellenebilmelidir. "
     "Bu teknik zorunluluk, bireysel haklarin kapsamini daraltir. Acilan mesele "
     "dogru yorumlanmalidir: kurumsal mulkiyet bir zorunluluk sonucu olarak "
     "dogar, kazanc degil. Buna karsilik denetim kapsami, saklama suresi ve "
     "yeniden kullanim sartlari olcumlenebilir olmalidir; aksi halde bu yapi "
     "yonetilemez bir taban olusturur."),

    ("h2", "5.3. Nöroözerki: Beyin Özelliği mi, Kişisel Veri mi?"),
    ("p",
     "Noroveri kavrami, benim olarak denetleme hakki ve devlettin bunu "
     "nasil kullandigi meselesini icerir. Iki farkli yonelim vardir."),
    ("bullet",
     "(a) Beyin bir nesne olarak dusunulebilir: Bazi hukuk sistemleri, beyin "
     "verisini geri donusturulebilir bir nesne gibi ele alir. Bu yaklasim "
     "veri yonetimini kolaylastirir ama oznebilirlik meselesini ortadan "
     "kaldirmaz."),
    ("bullet",
     "(b) Beyin ozelligik olarak dusunulebilir: Bazi yazarlar, beyin verisini "
     "dogrudan bireyin ozelligi sayarak degerlendirir. Bu yaklasim koruma "
     "duzeyini yuksek tutar ancak mevcut hukuki kategorilerle uyumsuzluk "
     "yaratir."),
    ("p",
     "Bu tartisma, somut bir sonuc uretir: BCI mevzuatinda veri korumasi, "
     "mevcut saglik verisi kurallarindan daha kati olmalidir. Aksi halde, ozel "
     "hayat gizliligini ihlal eden bir sistem hukuka uygun sayilabilirken "
     "toplumsal zarar ortaya cikabilir. Kisisel noral verinin duyarli veri "
     "statusuyle korunmasi yasal olarak zorunlu olmasa da savunulabilir bir "
     "oneridir. Ienca ve Andorno'nun onerisi bu yonde bir baslangic noktasi "
     "sunar."),
    ("p",
     "Bu teshis, inceleme hipotezi H-3'u desteklemektedir: asil gerilim, veri "
     "gizliligi cercevesinden cikarak zihinsel ozgurlugu ilgilendirir."),

    ("h2", "5.4. Adalet ve Erişilebilirlik"),
    ("p",
     "BCI'ye en sik yonelttigi adalet eleştirisi su noktaya dayanir: sistem, "
     "yalnizca dijital ortamda yeterli nakit ve dijital okuryazarliga sahip "
     "kullanicilara hitap eder. Buna karsilik, BCI'nin en guclu klinik "
     "uygulamasi (iletişim bozukluklari) tam da bu noktada ters yonden ise "
     "yarar: konusamayan bir hasta hicbir baska yolla ifade edemiyorsa BCI "
     "yeni bir imkan olur."),
    ("p",
     "Saglikta esitsizlik tartismasi acisindan iki ek olgu vardir. Birincisi, "
     "bazi algoritmalarin farkli gruplarda daha yuksek hata payi uretmesi "
     "olasi, veri temsili sorununu ortaya cikarir. Model yeterli cesitlilikte "
     "veriyle egitilmezse, 'ortalamada iyi' bir model bazi gruplar icin "
     "kabul edilemez kalir. 'Ortalamada iyi' ifadesi bu nedenle tek basina "
     "yetersizdir; raporlama alt grup duzeyinde yapilmalidir."),
    ("p",
     "Ikincisi, saglik sistemleri arasindaki erisim farki, teknolojinin "
     "gelistirildigi ve uygulandigi yerler arasinda bir uyumurculuk "
     "(equity) sorunu yaratir. Bu, yalnizca dagitim degil, arastirma onceligidir: "
     "hangi kullanicinin ihtiyacinin kapsam disi kaldigini bilmek, modelin "
     "kimseye hizmet etmedigi durumlari da tespit eder."),

    ("h2", "5.5. Bilişsel Özgürlük"),
    ("p",
     "Birisimsel BCI'nin (iBCI) klinik alanda uygulamalari, okuma-yazma "
     "baglantilarini genisletme potansiyeli tasimaktadir. Bu potansiyel su "
     "sorulara yol acar."),
    ("bullet",
     "(a) Ayni kanalda iki yonluluk: bir sistem hem motor cikarimi hem de "
     "dusunce okuma yonu sunuyorsa, cikarim hangi yonun sonucudur?"),
    ("bullet",
     "(b) Yorum siniri: bir cikarim, cogul anlama ve metafor olarak "
     "yorumlanabilir. Bir sistemin bunlari ayirt edememesi, ifade "
     "ozgurlugunu sinirlar."),
    ("bullet",
     "(c) Onam ve bilinebilirlik: kullanici, sisteminin neyi okuyabildigini "
     "tam olarak bilemeyebilir. Bu durumda onam yeterince bilgilendirilmis "
     "sayilmaz; sistemin sinirlari onamin bir parcasidir."),
    ("p",
     "Bu sorulara verilecek yeni kural, yazili olmasi ve yalnizca 'ne olur' "
     "degil 'ne olmaz' biciminde de yazilmasi olmalidir: sistemin belirli "
     "durumlarda guvenilmez oldugunun yazili bildirimi, onamin ayrilmaz "
     "parcasidir."),

    ("h2", "5.6. Sosyal ve Psikolojik Etkiler"),
    ("p", "En azindan bes boyut ayirt edilmelidir."),
    ("bullet",
     "(a) Kimlik: 'Beyni okunabilir' olmak bir etiket ve toplumsal "
     "beklentiye donusebilir. Cogu kisi icin bu 'zihinsel olarak daha okunur' "
     "anlamina gelir ve bu yanlis anlasilmasi ciddi bir toplumsal sorundur."),
    ("bullet",
     "(b) Stigma: BCI tabanli tespit, mevcut teshis kriterlerinden farkli bir "
     "temele dayanir; yanlislik veya asiri genelleme damgalamaya yol acabilir."),
    ("bullet",
     "(c) Uyum ve odak: surekli sinyal toplama ve belirli bir is performansi "
     "olcumu, surekli izlenme korkusu yaratabilir. Kaynak veriyi bilincli "
     "islemek ile ayni zamanda izlendiginden emin olamamak arasindaki bu "
     "temel paradoks, cozum kazanmadir."),
    ("bullet",
     "(d) Kimlik belirsizligi: cogu BCI kullanicisinin kullaniciyla ayni dogrudan "
     "iliskili olmadiği gorulur. Bu, cikarim hatasinin kim tarafindan "
     "duzeltilecegi ve kimden sorulacagi konusunda belirsizlik yaratir."),
    ("bullet",
     "(e) Kaygi temelli kabul: bir sistemin kabul kriteri, onun dogrulugu "
     "degil korkutucu bulunmamasi olabilir; bu, teknolojik kriter ile toplumsal "
     "kriterin ayrisabilecegini gosterir."),
    ("p",
     "Bu etkilerin kacinilmazligi, BCI etiginin yalnizca bireysel onam "
     "temelli olmasinin yetersiz oldugunu gosterir. Konunun toplumsal boya "
     "olmasi gerekir."),

    ("h2", "5.7. Düzenleyici Çerçeve Olarak Öneri"),
    ("p",
     "Yukaridaki tespitlerden yola cikan bir duzenleyici cerceve su yedi "
     "ilke uzerinde kurulabilir."),
    ("bullet",
     "(1) Noral veri, duyarli kisisel veri statusuyle korunur."),
    ("bullet",
     "(2) Onam yalnizca islemi degil, verinin yeniden kullanimini ve model "
     "egitiminde kullanilmasini da kapsar; model egitimi icin ayri riza "
     "gerekir."),
    ("bullet",
     "(3) Model performansi kullanim populasyonuna gore (etnik, cinsiyet, yas) "
     "raporlanir; alt grup performansi asagi duserse sisteme izin verilmez."),
    ("bullet",
     "(4) Veri sahibi, cihaz verisini tasima ve silme hakkina sahiptir; bu hak, "
     "model egitiminde gizli tutulan veriler icin de gecerlidir."),
    ("bullet",
     "(5) Sistemin sinirlari (guvenilmez oldugu durumlar) kullaniciya acikca "
     "bildirilir ve arayuzde gorunur sekilde gosterilir."),
    ("bullet",
     "(6) Surekli izleme, model guncelleme ve geri bildirim dongusu icin yapi "
     "sinirlari tanimlanir."),
    ("bullet",
     "(7) Saglikli bireylerde ticari kullanim, hasta gruplarina kiyasla daha "
     "yuksek bir kanit esigine tabi olur."),
    ("p",
     "Bu ilkeler, mevcut klinik yonergelerin genisletilmesi olarak yeni bir "
     "duzenleme icin zemin hazirlayabilir."),
]

# ------------------------------------------- B6 GELECEK
B6 = [
    ("h1", "ALTINCI BÖLÜM"),
    ("h1", "GELECEK PERSPEKTİFLERİ"),
    ("h2", "6.1. Yaklaşan ve Uzak Alan"),
    ("table", [
        ["Donem", "Beklenen Gelisim", "Kritik Belirsizlik"],
        ["Yakin (1-3 yil)",
         "Akustik ve sayisal uyaran tabanli cihazlarla cift yonlu iletisim",
         "Klinik faydanin olculmesi"],
        ["Yakin (1-3 yil)",
         "Daha yogun montaj, cihaz ici hesaplama, kisisellestirilmis modeller",
         "Bireysel cihazin klinik kaniti"],
        ["Orta (3-8 yil)",
         "Yinelenen uyaranlama ile kortikal uyarlanabilirligin kazanimi",
         "Tedavi etkinliginin gosterilmesi"],
        ["Uzak (8+ yil)",
         "Yari invaziv ag tabanli arayuzler (neurovascularist)",
         "Kronik implant kararliliginin kaniti"],
        ["Uzak (8+ yil)",
         "Bilisiksel yardim: odak, hafiza ve surekli izleme",
         "Ozgurluk ve bagimlilik dagilimi"],
    ]),
    ("caption", "Tablo 6.1. Gelecek donemler ve kritik belirsizlikler."),
    ("p",
     "Bu tablo, teknik gelismenin ongorulebilirligi ile klinik ve etik "
     "sonuclarin ongorulebilirliginin ayni olmadigini gosterir. Yakin donemde "
     "bazi teknik engellerin kalkmasi, ayni donemde bu tekniklerin klinik "
     "olarak anlamli fayda uretmesi demek degildir. Bu ayrim, alanin en yaygin "
     "hatasi ve en sik yapilan hatasidir."),

    ("h2", "6.2. Öngörülen Teknik Yönelimler"),
    ("bullet",
     "(1) Onceden egitilmis temel modeller: buyuk on egitimli modellerin her "
     "bir kullanicinin sinirli verisiyle uyarlanmasi, BCI'de veri "
     "sinirliginin en istenilen cozumu olarak one cikmaktadir."),
    ("bullet",
     "(2) Cok modlu olcum: EEG yaninda goz ve yuz hareketleri ile ozel "
     "dolayli (implicit) bilgi, ozellikle dikkat odakli alanlarda sinif "
     "sinirini genisletmektedir. Bir gozunun kacmasi bile cogu problemde "
     "sinif ayrimini kolaylastirmaktadir."),
    ("bullet",
     "(3) Otopompa kanal ve empedans izleme: cihaz uzeri surekli sinyal "
     "kalitesi olcumu, kullanicinin egitim disi oturumlarda performans "
     "kaybini azaltir."),
    ("bullet",
     "(4) Dinamik yuz yuklemesi: harici yuz yuklemesi modelleri, farkli "
     "montajlarda oznitelik uzayi tasinabilirligini artirabilir."),
    ("bullet",
     "(5) Uc bulut ve cihaz ici ogrenme: gizlilik gereksinimlerini "
     "azaltarak, modelin cihaz uzerinde guncellenmesini mumkun kilar."),
    ("p",
     "Otek olarak, zaman serisi temsilinde derin ogrenmeye gore rekabetci "
     "olmayan, oznitelik tabanli yaklasimlar da vardir. Rastgele orman ve "
     "gradyan artirilmis agac tabanli siniflandiricilar, BCI tasiyabilir "
     "paketlerde goruntunun devasa turetici ajanlara gore daha iyi "
     "genellenebilir oldugu tespitleriyle desteklenmektedir. Bu bulgu, "
     "sadece 'derin ogrenme kazanir' seklinde okunamaz; model secimi, "
     "veri miktari, hesaplama kosullari ve karsilastirma protokolune birlikte "
     "baglidir."),

    ("h2", "6.3. Olası Riskler"),
    ("bullet",
     "(1) Uygulama cok fazla hizlanabilir: duzenleme, teknolojinin gerisinde "
     "kalabilir. Ozellikle tüketici sinifinda pazardaki hiz, mevzuatin yapisal "
     "degisim gerektiren konularda yavas ilerler."),
    ("bullet",
     "(2) Dogrulama yukunun artmasi: her yeni klinik endikasyon bagimsiz "
     "dogrulama ve uzun sureli takip gerektirir; bu, urunun pazara cikisini "
     "geciktirir ve maliyetlendirir."),
    ("bullet",
     "(3) Adalet aciginin derinlesmesi: gelismis sistemlere erisim, "
     "gelismemislere gore daha da buyuk bir fark yaratabilir."),
    ("bullet",
     "(4) Bitisik kullanimin yuksek riskli alanlara yonelmesi: askeri, is "
     "yerlamlama ve adli alan, BCI'nin en muhtemel etik gerilim alanidir."),

    ("h2", "6.4. Araştırma Öncelikleri"),
    ("bullet",
     "(a) Onceden kaydedilmis analiz planlariyla, yeterli katilimcili, bagimsiz "
     "test kumesi kullanilan cok merkezli calismalar."),
    ("bullet",
     "(b) Hata analizinin zorunlu hale getirilmesi: 'model calismiyor' yerine, "
     "hangi sinifin neden karistirildiginin ve bu hatanin hangi kosullarda "
     "olustugunun raporlanmasi."),
    ("bullet",
     "(c) Performansin, kullanicinin gercekte yapabilecegi isle ne kadar "
     "eslendiginin ayrica raporlanmasi."),
    ("bullet",
     "(d) Uzun sureli klinik takip calismalarinin, kisa sureli laboratuvar "
     "deneylerine oncelik verilmesi."),
    ("bullet",
     "(e) Etik ve hukuki arastirmanin teknik calismalarla es zamanli "
     "yurutulmesi; alanin 'once gelistir, sonra konus' modelinden cikilmasi."),
]

# ---------------------------------------------------- SONUCLAR
SONUC = [
    ("h1", "SONUÇ"),
    ("p",
     "Bu calisma, BCI'nin dort boyutunu — norobilimsel temeller, yapay zeka "
     "destekli cikarim, klinik uygulama ve etik-hukuki sinirlar — tek bir "
     "cercevede birlikte ele almistir. Bulgular asagida ozetlenmektedir."),
    ("bullet",
     "(1) BCI, 'düşünce okuyan bir alet' degil, kapali bir geri bildirim "
     "sistemidir. Sinyal kalitesi kadar ogitim surecini ve geri bildirim "
     "tasarimini da basariyi belirler. Bu nedenle ozellik uretimi kadar "
     "kullanici deneyimi de nesne olmustur."),
    ("bullet",
     "(2) Derin ogrenme ve donusumcu mimariler EEG cikariminda gercek "
     "artilar saglamaktadir; ancak bu artilar, cogu calismada ayni kanal "
     "sayisi, ayni filtre ve ayni bolme protokolune dayanir. Bu durum, "
     "literaturde sikca soylenen 'sifir bir kazanc' yorumunun gercek teknik "
     "ilerlemeyi oldugundan fazla kararttigini gosterir. Buna karsilik alanin "
     "ilerlemesi, cogu zaman veri ve karsilastirma protokollerinin "
     "zayifligindan kaynaklanmaktadir."),
    ("bullet",
     "(3) Klinik yararlilik, teknolojinin karma sikligi degil, klinik "
     "gereksinim ile teknolojik sinirlar arasindaki eslesmedir. Iletisim "
     "sistemlerinde bu eslesme en yuksektir, cunku alifabe sinirli ve "
     "dogruluk abartilmayabilir. Tani ve tibbi karar destek alanlarinda bu "
     "eslesme henuz kurulmamis, buna karsilik model performansi artirilmis "
     "olabilir; bu alan halen gercek dogruluk verisinin uzerinde gosterilen "
     "sonuclardan olusmaktadir."),
    ("bullet",
     "(4) BCI'nin veri temelli tespitinde asil etik mesele, zihinsel icerigin "
     "ozel hayat icin dogrudan sonuc dogurmasidir. Mevcut saglik verisi "
     "cerceveleri bu yonun kapsamini disinda birakir. Kisisel noral verinin "
     "duyarli kisisel veri statusuyle korunmasi, bireyin model egitimi icin "
     "ayri riza vermesi, alt grup performansinin raporlanmasi ve sistem "
     "sinirlarinin kullaniciya aciklanmasi onerilmistir."),
    ("p",
     "Sinirlamalar: Bu calisma nicel ampirik veri uretmemistir. Literatür "
     "taramasi, acik erisime acik kaynaklarla sinirlidir ve alanin hizli "
     "evrimi nedeniyle bazi tespitler tarihsel olarak geride kalabilir. "
     "Gelecek arastirmalarda etik cercevenin ampirik kabul olcumu, gozlenen "
     "etkilerin belgelenmesi ve sosyal etki analizinin yapilmasi onerilir."),
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
     "DOI alanları bilinçli olarak doldurulmamıştır. Kaynakların bağımsız DOI "
     "doğrulaması tamamlanamadığı için (bkz. EK-2) elle yazılmış ve "
     "doğrulanmamış DOI'ler kaynakçada yer almamaktadır. Doğrulama tamamlandığında "
     "bu alanların eklenmesi önerilir."),
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
            "learning-based detection of user-specific brain activities. "
            "Journal of Universal Access in the Information Society, 3(4), "
            "223-230."),
    ("ref", "Clausen, J. (2013). Man, machine and in between: On the concept "
            "of a brain-computer interface. Science and Engineering Ethics, "
            "19(4), 837-846."),
    ("ref", "Farwell, L. A., & Donchin, E. (1986). The on-line brain. "
            "Communications of the ACM, 29(3), 28-32."),
    ("ref", "Flesher, M. E., Holdgraf, C. L., Ramsey, E. R., & Yocum, J. "
            "(2021). Ethical considerations in brain-computer interface "
            "research and development. In Brain-Computer Interfaces. Oxford "
            "University Press."),
    ("ref", "Gama, J., Žliobaitė, I., Bifet, A., Pechenizkiy, M., & "
            "Bouchachia, A. (2014). A survey on concept drift adaptation. "
            "ACM Computing Surveys, 46(4), 44."),
    ("ref", "Ganin, Y., Ustinova, E., Ajakan, H., Germain, P., Larochelle, "
            "H., Frégier, Y., & others. (2016). Domain-adversarial training "
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
            "Hung, C. P., & Lance, B. J. (2018). EEGNet: A compact "
            "convolutional neural network for EEG-based brain-computer "
            "interfaces. arXiv preprint arXiv:1611.08024."),
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
    ("ref", "Shen, X., Chen, H., & Zhang, Y. (2019). End-to-end deep image "
            "reconstruction from human brain activity. PLOS Computational "
            "Biology, 15(5), e1007129."),
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
        ["Derleme tarihi", "26.09.2026"],
        ["Taranan veri tabanları", "Crossref, OpenAlex"],
        ["Sorgu sayısı", "4 (araştırma sorusu başına 1)"],
        ["Dahil etme ölçütü",
         "Yayımlanmış, hakemli dergi, konu ile doğrudan ilgili, "
         "erişilebilir kayıt"],
        ["Dışarıda bırakma ölçütü",
         "Tam metne erişim yok, konu dışı, tez türü, editoryal içerik"],
        ["Doğrulama yöntemi",
         "Başlık, yazar, yıl, dergi ve DOI alanlarının ağırlıklı "
         "eşleşmesi; eşik 0.60"],
        ["Doğrulama sonucu",
         "Tamamlanamadı — ayrıntı için EK-2'ye bakınız"],
    ]),
    ("caption", "Tablo EK-1. Kaynak derleme ve doğrulama özeti."),

    ("h2", "EK-2. Kaynak Doğrulama Durumu ve Araç Kusurları"),
    ("p",
     "Bu ek, kaynak listesinin doğrulama aşamasında ölçülen gerçek durumu "
     "kayda geçirir. Doğrulama tamamlanamamıştır ve bu ekte herhangi bir "
     "kaynak için 'doğrulandı' sonucu ilan edilmemektedir. Ölçülen durum ve "
     "tespit edilen arac kusurları aşağıda sunulmaktadır."),
    ("p",
     "Doğrulama modülü, DOI üzerinden Crossref ve OpenAlex kayıtlarını getirmekte "
     "ve alan bazlı bir eşleşme puanı hesaplamaktadır. Yapılan denemeler "
     "aşağıdaki iki kusuru ortaya koymuştur."),
    ("bullet",
     "Kusur 1 — Yıl alanı geri düşürme eksikliği: Crossref kaydı "
     "dönüştürülürken yalnızca 'published-print' ve 'published-online' "
     "alanlarına bakılmakta, 'issued' alanına geri düşülmemektedir. 2000 "
     "öncesi dergi kayıtlarında bu iki alan bulunmadığı için yıl, nötr "
     "değer olan 0.5 puanla skorlanmakta ve toplam puan eşiğin altında "
     "kalmaktadır. Ölçüm: Vidal (1973) kaydında yıl 0.5, dergi 0.0 olarak "
     "hesaplanmış; bu iki eksiklik toplamda 0.175 puanlık kayba denk "
     "gelmektedir."),
    ("bullet",
     "Kusur 2 — Yalnızca soyadı içeren yazar girdisi sıfır puan alıyor: "
     "Yazar normalizasyonu soyadı ile başharfi birleştirdiğinden, "
     "kaynakça biçimindeki (yalnızca soyadı) bir girdi ile veritabanındaki "
     "'Soyad, Ad' biçimi hiç eşleşmemekte, yazar puanı 0.0 olmaktadır. Bu, "
     "yazar alanının 0.30 ağırlığıyla tamamen kaybolması demektir. Aynı "
     "kayıt, yazar 'Soyad, A.' biçiminde girildiğinde 0.825 puanla "
     "doğrulanabilmektedir."),
    ("table", [
        ["Ölçüm", "Sonuç"],
        ["Yalnızca soyadı ile yapılan doğrulama denemeleri",
         "27 kaynaktan 0 kaynak eşik (0.60) üzerinde"],
        ["Başlık + yazar biçiminin araca uygun yazılmasıyla (kontrol)",
         "Kontrol kaydı 0.825 puanla doğrulandı"],
        ["Arac kusurları giderildikten sonra yeniden çalıştırılmalı",
         "Evet — aksi halde 'doğrulandı' sonucu ilan edilemez"],
    ]),
    ("caption",
     "Tablo EK-2. Kaynak doğrulama ölçümü ve tespit edilen araç kusurları."),
    ("p",
     "Sonuç olarak, bu kaynak listesindeki hiçbir kaynak bağımsız DOI "
     "doğrulamasından geçememiştir. Bu sonuç, kaynakların yanlış olduğunu "
     "göstermez; aracın eşik altında puanlama davranışını gösterir. "
     "Doğrulanmamış bir kaynakça ile teslim edilen bir tezde bu tablonun "
     "yerine alınması gereken sonuç, kaynakların henüz doğrulanmadığının "
     "açıkça yazılmasıdır. Kaynakların DOI'leri bu nedenle bilinçli olarak "
     "kaynakçada yer almamaktadır: elle yazılmış ve doğrulanmamış DOI'ler, "
     "doğrulanmamış kaynaklardan daha tehlikelidir, çünkü varlıkları "
     "kanıtlanmış görünürler."),
    ("h2", "EK-3. Kısaltmalar"),
    ("table", [
        ["Kisaltma", "Acilis"],
        ["ALS", "Amyotrofik Lateral Skleroz"],
        ["BCI", "Brain-Computer Interface (Beyin-Bilgisayar Arayuzu)"],
        ["BOS", "Bozulmus Sinif"],
        ["CSP", "Common Spatial Patterns (Ortak Uzaysal Desenler)"],
        ["DKSA", "Derin Konvolusyonel Sinir Agi"],
        ["ECoG", "Electrocorticography (Elektrokortikografi)"],
        ["EEG", "Electroencephalography (Elektroensefalografi)"],
        ["EMG", "Electromyography (Elektromiyografi)"],
        ["FDA", "U.S. Food and Drug Administration"],
        ["fNIRS", "Functional Near-Infrared Spectroscopy"],
        ["ITR", "Information Transfer Rate (Bilgi Aktarim Hizi)"],
        ["MEG", "Magnetoencephalography"],
        ["SNR", "Signal-to-Noise Ratio (Sinyal-Gurultu Orani)"],
    ]),
    ("caption", "Tablo EK-3. Kisaltmalar listesi."),
]
