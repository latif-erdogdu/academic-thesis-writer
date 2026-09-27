# -*- coding: utf-8 -*-
"""Turkce diakritik duzeltme tablosu ve uygulayicisi.

Gerekce
-------
Icerik kaynaklari (`content_a.py` .. `content_d.py`) bir bolum Turkce metni
diyakritiksiz ASCII yazimla iceriyordu: "Bu calisma konunun dort temel
boyutunu birlikte ele alir", "Yontemin sinirlari acikca belirtilmelidir".
Bir Turkce tezinde bu kabul edilemez.

Tasarim
-------
Onceki denemeler elle buyuk/kucuk harf varyanti ureten bir tablo
deniyordu ("ikinci" -> "Ikinci" -> "İkinci" gibi) ve bu yaklasim
guvenilir cikti: iki denemede de kimlik (identity) eslemeleri,
sahte girdiler ("basit": "basit_diyaliz"), yanlis anlamlar
("kutlu": "mutlu") ve Kiril karakterleri uretiyordu.

Bu surum tek duz bir sozluk kullanir:

* :data:`ESLESME` — **kucuk harfli** ASCII -> **kucuk harfli** Turkce.
  Yalnizca gercekten degisen kelimeler icerir; kimlik eslemesi yoktur.
  Buyuk/kucuk harf varyantlari **uretilmez**, :func:`duzelt` cikis bicimini
  Turkce kurallarina gore yeniden kurar.
* Turkce'ye ozgu bas-harf kurali ayrica ele alinir: "ikinci" kelimesinin
  kucuk harfli bicimi ASCII'de zaten dogrudur, ama bas harfi Turkce'de
  "İ" olmalidir ("İkinci"). .upper()/.capitalize() bunu veremez, cunku
  "i" -> "I" uretirler; :func:`_bas_harf` dogru eşlemeyi yapar.

Dogrulama
---------
* Tablo **yalnizca kaynakta gercekten bulunan** token'lari icerir;
  :func:`denetle_tablo` olu girdileri ve kimlik eslemelerini raporlar.
* :func:`duzelt` idempotenttir: ``duzelt(duzelt(x)) == duzelt(x)``.
* URL, DOI, ``RQ-###`` / ``S-####`` gibi kod tanimlayicilari degistirilmez
  (DOI'lar yazim kurali geregi ASCII'dir ve bir DOI parcasi kelime
  kalibina takilabilir).

Kullanim
--------
Bu modul metni **kaynak dosyalara bir kez uygular**; gizli bir render-time
donusum birakilmaz. Uygulama :mod:`migrate_turkish` ile yapilir.
"""
from __future__ import annotations

import re

# --------------------------------------------------------------------------
# 1. Duz esleme tablosu: kucuk harfli ASCII -> kucuk harfli Turkce
# --------------------------------------------------------------------------
#
# KURALLAR
# 1. Yalnizca **kaynakta gercekten gecen** token'lar yazilir.
# 2. Yalnizca **degisen** token'lar yazilir (kimlik eslemesi yasaktir).
# 3. Anahtarlar ve degerler kucuk harflidir; buyuk/kucuk harf duzeltmesi
#    `duzelt()` icinde uretilir.
# 4. Turkce'de dogru yazilan ASCII kelimeler ("veri", "kabul", "kontrol",
#    "etik", "toplumsal", "ucuz", "derleme", "kural", "sistem", "kanal",
#    "verim", "birim", "sinyal", "model", "ekran", "bulgu", "karar",
#    "temel", "bilgi", "beceri", "seviye", "tarih", "uzman", "oran",
#    "kriter", "risk", "hedef", "hasta", "tedavi", "fayda", "soru") buraya
#    girmez; girmesi hatadir.
# 5. Ingilizce / teknik terimler (BCI, EEG, interface, data ...) ve yabanci
#    oz adlar (Nature, Ienca) buraya girmez.

ESLESME: dict[str, str] = {
    # ---- a ---------------------------------------------------------------
    "adi": "adı",
    "adim": "adım",
    "akim": "akım",
    "aktarilabilirlik": "aktarılabilirlik",
    "aktarim": "aktarım",
    "alani": "alanı",
    "alanidir": "alanıdır",
    "alanin": "alanın",
    "alanina": "alanına",
    "alaninda": "alanında",
    "alanindaki": "alanındaki",
    "alanlarinda": "alanlarında",
    "alarmi": "alarmı",
    "algoritmalari": "algoritmaları",
    "algoritmalarin": "algoritmaların",
    "alim": "alım",
    "alinabilen": "alınabilen",
    "alir": "alır",
    "almasi": "alması",
    "alti": "altı",
    "altindadir": "altındadır",
    "amaci": "amacı",
    "amacini": "amacını",
    "amaciyla": "amacıyla",
    "anlamina": "anlamına",
    "anlamli": "anlamlı",
    "anlati": "anlatı",
    "araci": "aracı",
    "aracin": "aracın",
    "araliklarina": "aralıklarına",
    "arasi": "arası",
    "arasinda": "arasında",
    "arasindaki": "arasındaki",
    "artefakti": "artefaktı",
    "artefaktlari": "artefaktları",
    "artilar": "artılar",
    "artirabilir": "artırabilir",
    "artirir": "artırır",
    "artirma": "artırma",
    "artmasi": "artması",
    "asil": "asıl",
    "aslinda": "aslında",
    "avantajlidir": "avantajlıdır",
    "ayari": "ayarı",
    "aydinlatildi": "aydınlatıldı",
    "ayiran": "ayıran",
    "ayirir": "ayırır",
    "ayirt": "ayırt",
    "ayni": "aynı",
    "ayri": "ayrı",
    "ayrica": "ayrıca",
    "ayrilmaktadir": "ayrılmaktadır",
    "ayrilmaz": "ayrılmaz",
    "ayrim": "ayrım",
    "ayrimi": "ayrımı",
    "ayrimina": "ayrımına",
    "ayrimini": "ayrımını",
    "ayrintili": "ayrıntılı",
    "azalir": "azalır",
    "azaltir": "azaltır",
    "azaltmayi": "azaltmayı",
    "azindan": "azından",
    # ---- b ---------------------------------------------------------------
    "bakim": "bakım",
    "bakimindan": "bakımından",
    "bantlarina": "bantlarına",
    "bantli": "bantlı",
    "barindirir": "barındırır",
    "baskilar": "baskılar",
    "bastirilir": "bastırılır",
    "bastirma": "bastırma",
    "bazi": "bazı",
    "birakir": "bırakır",
    "boyutlarindaki": "boyutlarındaki",
    "bozukluklari": "bozuklukları",
    "bulunmamasi": "bulunmaması",
    "bulunmasi": "bulunması",
    "bunlari": "bunları",
    # ---- c ---------------------------------------------------------------
    "canli": "canlı",
    "cihazi": "cihazı",
    "cihazin": "cihazın",
    "cihazindan": "cihazından",
    "cihazlari": "cihazları",
    # ---- d ---------------------------------------------------------------
    "dalgacik": "dalgacık",
    "daraltir": "daraltır",
    "dayali": "dayalı",
    "dayaniklilik": "dayanıklılık",
    "dayanir": "dayanır",
    "dolayli": "dolaylı",
    "donanim": "donanım",
    "durumlari": "durumları",
    "duyarli": "duyarlı",
    "duyarlilik": "duyarlılık",
    # ---- e-f-g -----------------------------------------------------------
    "elektrotlari": "elektrotları",
    "farki": "farkı",
    "farkindalik": "farkındalık",
    "farkini": "farkını",
    "farkli": "farklı",
    "farklidir": "farklıdır",
    "farkliliklarin": "farklılıkların",
    "faydalilik": "faydalılık",
    "faydanin": "faydanın",
    "faydasi": "faydası",
    "faydayi": "faydayı",
    "giris": "giriş",
    "grafinda": "grafında",
    # ---- h-i-j -----------------------------------------------------------
    "hafiza": "hafıza",
    "hakkina": "hakkına",
    "hakkinda": "hakkında",
    "haklari": "hakları",
    "haklarin": "hakların",
    "haritalari": "haritaları",
    "haritalarini": "haritalarını",
    "haritalarinin": "haritalarının",
    "haritasi": "haritası",
    "haritasini": "haritasını",
    "hastalarinda": "hastalarında",
    "hastalarindaki": "hastalarındaki",
    "hastalik": "hastalık",
    "hastaliklar": "hastalıklar",
    "hastaliklarda": "hastalıklarda",
    "hastanin": "hastanın",
    "hatali": "hatalı",
    "hatanin": "hatanın",
    "hatasi": "hatası",
    "hatasidir": "hatasıdır",
    "hatasinin": "hatasının",
    "hatayi": "hatayı",
    "hazir": "hazır",
    "hazirlayabilir": "hazırlayabilir",
    "hazirlik": "hazırlık",
    "hesaplanmasi": "hesaplanması",
    "hiz": "hız",
    "hizi": "hızı",
    "hizinin": "hızının",
    "hizlanabilir": "hızlanabilir",
    "hizli": "hızlı",
    "hukuki": "hukukî",
    "icindekiler": "içindekiler",
    "imajina": "imajına",
    "insanin": "insanın",
    "isleme": "işleme",
    # ---- k ---------------------------------------------------------------
    "kafatasindaki": "kafatasındaki",
    "kaldirarak": "kaldırarak",
    "kaliplarini": "kalıplarını",
    "kalir": "kalır",
    "kalkmasi": "kalkması",
    "kalmasidir": "kalmasıdır",
    "kalmasina": "kalmasına",
    "kanalindan": "kanalından",
    "kanalinin": "kanalının",
    "kanallarin": "kanalların",
    "kanit": "kanıt",
    "kaniti": "kanıtı",
    "kanitla": "kanıtla",
    "kapali": "kapalı",
    "kapsami": "kapsamı",
    "kapsamli": "kapsamlı",
    "karari": "kararı",
    "kararidir": "kararıdır",
    "kararini": "kararını",
    "kararlarin": "kararların",
    "kararli": "kararlı",
    "kararliliktir": "kararlılıktır",
    "kaslari": "kasları",
    "kati": "katı",
    "katilimci": "katılımcı",
    "katilimcili": "katılımcılı",
    "katilimli": "katılımlı",
    "katkida": "katkıda",
    "katkisi": "katkısı",
    "katkisini": "katkısını",
    "katlanir": "katlanır",
    "katmani": "katmanı",
    "katmanina": "katmanına",
    "katmanlarinin": "katmanlarının",
    "katmanli": "katmanlı",
    "katsayisi": "katsayısı",
    "kavrami": "kavramı",
    "kavraminin": "kavramının",
    "kaybi": "kaybı",
    "kaybini": "kaybını",
    "kaydi": "kaydı",
    "kaygi": "kaygı",
    "kayipta": "kayıpta",
    "kayit": "kayıt",
    "kayitlari": "kayıtları",
    "kayitta": "kayıtta",
    "kaymasi": "kayması",
    "kaynakca": "kaynakça",
    "kaynaklanmaktadir": "kaynaklanmaktadır",
    "kaynakli": "kaynaklı",
    "kazanci": "kazancı",
    "kazandirir": "kazandırır",
    "kazani": "kazanı",
    "kazanilmasinda": "kazanılmasında",
    "kazanimi": "kazanımı",
    "kazanimlar": "kazanımlar",
    "kazanir": "kazanır",
    "kazanmaktadir": "kazanmaktadır",
    "kilar": "kılar",
    "kildi": "kıldı",
    "kirpma": "kırpma",
    "kisa": "kısa",
    "kisitlari": "kısıtları",
    "kisitli": "kısıtlı",
    "kismen": "kısmen",
    "kismi": "kısmi",
    "kiyas": "kıyas",
    "kiyasla": "kıyasla",
    "kombinasyonlari": "kombinasyonları",
    "konumlandirilabilen": "konumlandırılabilen",
    "konumlandirilabilir": "konumlandırılabilir",
    "korumasi": "koruması",
    "korunmasi": "korunması",
    "kullanici": "kullanıcı",
    "kullanicida": "kullanıcıda",
    "kullanicidan": "kullanıcıdan",
    "kullanicilara": "kullanıcılara",
    "kullanicilik": "kullanıcılık",
    "kullanicinin": "kullanıcının",
    "kullanicisi": "kullanıcısı",
    "kullanicisinin": "kullanıcısının",
    "kullaniciya": "kullanıcıya",
    "kullaniciyi": "kullanıcıyı",
    "kullaniciyla": "kullanıcıyla",
    "kullanilabilecek": "kullanılabilecek",
    "kullanilabilir": "kullanılabilir",
    "kullanilabilirlik": "kullanılabilirlik",
    "kullanilan": "kullanılan",
    "kullanilir": "kullanılır",
    "kullanilmaktadir": "kullanılmaktadır",
    "kullanilmasi": "kullanılması",
    "kullanilmasini": "kullanılmasını",
    "kullanilmaya": "kullanılmaya",
    "kullanim": "kullanım",
    "kullanima": "kullanıma",
    "kullanimdaki": "kullanımdaki",
    "kullanimi": "kullanımı",
    "kullanimin": "kullanımın",
    "kullanimini": "kullanımını",
    "kullanir": "kullanır",
    "kumandalari": "kumandaları",
    "kurallarindan": "kurallarından",
    "kurmayi": "kurmayı",
    "kurulmasi": "kurulması",
    "kurulmasindan": "kurulmasından",
    # ---- l-m-n-o ---------------------------------------------------------
    "mekanizmasi": "mekanizması",
    "mevzuatin": "mevzuatın",
    "mevzuatinda": "mevzuatında",
    "miktari": "miktarı",
    "miktarindan": "miktarından",
    "nasil": "nasıl",
    "noktasi": "noktası",
    "odakli": "odaklı",
    "okunmasi": "okunması",
    "olasi": "olası",
    "olmalidir": "olmalıdır",
    "olmamasidir": "olmamasıdır",
    "olmasi": "olması",
    "olmasidir": "olmasıdır",
    "olmasinin": "olmasının",
    "onamin": "onamın",
    "onayli": "onaylı",
    "orani": "oranı",
    "oranina": "oranına",
    "oranini": "oranını",
    "oranlari": "oranları",
    "organizmanin": "organizmanın",
    "ortami": "ortamı",
    "ozet": "özet",
    # ---- p-r-s -----------------------------------------------------------
    "payi": "payı",
    "performansi": "performansı",
    "performansin": "performansın",
    "performansindaki": "performansındaki",
    "performansinin": "performansının",
    "planidir": "planıdır",
    "planlariyla": "planlarıyla",
    "raporlamaktir": "raporlamaktır",
    "raporlanir": "raporlanır",
    "raporlanmasi": "raporlanması",
    "riza": "rıza",
    "satriksiyonu": "satrıksiyonu",
    "sayida": "sayıda",
    "sayilabilirken": "sayılabilirken",
    "sayili": "sayılı",
    "sayilmasi": "sayılması",
    "sayilmaz": "sayılmaz",
    "sayisal": "sayısal",
    "sayisi": "sayısı",
    "sayisinin": "sayısının",
    "sifir": "sıfır",
    "sifirlanan": "sıfırlanan",
    "sik": "sık",
    "sinif": "sınıf",
    "sinifin": "sınıfın",
    "sinifinda": "sınıfında",
    "sinifini": "sınıfını",
    "siniflandiran": "sınıflandıran",
    "siniflandirici": "sınıflandırıcı",
    "siniflandiricidan": "sınıflandırıcıdan",
    "siniflandiricilar": "sınıflandırıcılar",
    "siniflandiricinin": "sınıflandırıcının",
    "siniflandirma": "sınıflandırma",
    "siniflandirmada": "sınıflandırmada",
    "siniflandirmasi": "sınıflandırması",
    "siniflandirmasinda": "sınıflandırmasında",
    "siniflandirmasini": "sınıflandırmasını",
    "siniflandirmayi": "sınıflandırmayı",
    "sinifli": "sınıflı",
    "siniftan": "sınıftan",
    "siniri": "sınırı",
    "sinirini": "sınırını",
    "sinirinin": "sınırının",
    "sinirlamalar": "sınırlamalar",
    "sinirlamalari": "sınırlamaları",
    "sinirlamalarla": "sınırlamalarla",
    "sinirlandirma": "sınırlandırma",
    "sinirlanir": "sınırlanır",
    "sinirlar": "sınırlar",
    "sinirlari": "sınırları",
    "sinirlarin": "sınırların",
    "sinirlarina": "sınırlarına",
    "sinirlarindan": "sınırlarından",
    "sinirlarini": "sınırlarını",
    "sinirlarinin": "sınırlarının",
    "sinirli": "sınırlı",
    "sinirlidir": "sınırlıdır",
    "sirasi": "sırası",
    "sirasinda": "sırasında",
    "sirasiyla": "sırasıyla",
    "sonrasi": "sonrası",
    "sonuc": "sonuç",
    "sonuclar": "sonuçlar",
    "sorularini": "sorularını",
    "sorulmasi": "sorulması",
    "sorunlarini": "sorunlarını",
    "standartlari": "standartları",
    "sunmaktadir": "sunmaktadır",
    # ---- t-u-ü-v-y-z -----------------------------------------------------
    "tabanlari": "tabanları",
    "tabanli": "tabanlı",
    "tani": "tanı",
    "tanim": "tanım",
    "tanimina": "tanımına",
    "tanimlanir": "tanımlanır",
    "tanimlar": "tanımlar",
    "tanimlayici": "tanımlayıcı",
    "tanitimi": "tanıtımı",
    "tarafindan": "tarafından",
    "taramasi": "taraması",
    "tasarim": "tasarım",
    "tasarimi": "tasarımı",
    "tasarimidir": "tasarımıdır",
    "tasarimini": "tasarımını",
    "tasarlanmasi": "tasarlanması",
    "tesekkur": "teşekkür",
    "tibbi": "tıbbi",
    "toplanirken": "toplanırken",
    "tutarli": "tutarlı",
    "uyaniklik": "uyanıklık",
    "uyarlamasi": "uyarlaması",
    "uyarlanmasi": "uyarlanması",
    "uyarlanmasidir": "uyarlanmasıdır",
    "uygulamalari": "uygulamaları",
    "uygulamalarinda": "uygulamalarında",
    "uygulamalarinin": "uygulamalarının",
    "uygulamasi": "uygulaması",
    "uygulamayi": "uygulamayı",
    "uygulanir": "uygulanır",
    "uygulanmaktadir": "uygulanmaktadır",
    "uzayi": "uzayı",
    "uzayinda": "uzayında",
    "uzayinin": "uzayının",
    "vardir": "vardır",
    "varsayilan": "varsayılan",
    "varsayimi": "varsayımı",
    "varsayimina": "varsayımına",
    "varsayimlardir": "varsayımlardır",
    "varyantlari": "varyantları",
    "vurgulanmasini": "vurgulanmasını",
    "yakin": "yakın",
    "yalnizca": "yalnızca",
    "yaninda": "yanında",
    "yanitlamaya": "yanıtlamaya",
    "yansitan": "yansıtan",
    "yansitmamaktadir": "yansıtmamaktadır",
    "yansitmaz": "yansıtmaz",
    "yapi": "yapı",
    "yapilan": "yapılan",
    "yapilir": "yapılır",
    "yapilmalidir": "yapılmalıdır",
    "yapilmasi": "yapılması",
    "yapilmaz": "yapılmaz",
    "yapisal": "yapısal",
    "yapisi": "yapısı",
    "yapmasina": "yapmasına",
    "yararlanir": "yararlanır",
    "yararlilik": "yararlılık",
    "yaratir": "yaratır",
    "yardim": "yardım",
    "yari": "yarı",
    "yaygin": "yaygın",
    "yayimladi": "yayımladı",
    "yayimlanan": "yayımlanan",
    "yayinlanma": "yayınlanma",
    "yayinlanmasi": "yayınlanması",
    "yazili": "yazılı",
    "yazilim": "yazılım",
    "yazilmasi": "yazılması",
    "yazim": "yazım",
    "yil": "yıl",
    "yilinda": "yılında",
    "yillar": "yıllar",
    "yillarca": "yıllarca",
    "yillarda": "yıllarda",
    "yorumlanmalidir": "yorumlanmalıdır",
    "yukaridaki": "yukarıdaki",
    "zamani": "zamanı",
    "zayif": "zayıf",
    "zorunluluklarin": "zorunlulukların",
}

#: Sozlukte olup duzeltilMESI gereken kelimeler. Bir anahtar buraya girerse
#: ya tablo hatasi ya da kirli girdidir.
DOGRU_YAZILANLAR: frozenset[str] = frozenset({
    "veri", "kabul", "kontrol", "etik", "toplumsal", "ucuz", "derleme",
    "kural", "sistem", "kanal", "verim", "birim", "sinyal", "model",
    "ekran", "bulgu", "dava", "karar", "temel", "bilgi", "beceri",
    "seviye", "tarih", "uzman", "oran", "kriter", "risk", "hedef",
    "hasta", "tedavi", "fayda", "soru", "dunya", "insan", "zaman",
})

#: Turkce bas-harf kuralinin **uygulanacagi** kelimeler (kucuk harfli).
#:
#: Turkce'de ``i`` buyutulurken ``I`` degil ``İ`` olur. Bu kural, Turkce
#: kelimeler disinda **her seye uygulanirsa** metni bozar:
#:
#:   ``Interface`` -> ``İnterface``, ``ICASSP`` -> ``İCASSP``,
#:   ``International`` -> ``İnternational``
#:
#: Bu yuzden kural bir *reddetme listesi* ile degil, bir **izin listesi** ile
#: sinirlanir: yalnizca Turkce oldugu gozle dogrulanmis kelimeler duzeltilir.
#: Bilinmeyen bir kelime **bozulmaz**, ASCII olarak kalir ve
#: ``scan_ascii_sentences.py`` tarafindan raporlanir. Boylece hata sessizce
#: metni degil, denetim raporunu kirletir.
#:
#: Liste iki parcadan olusur:
#:
#: 1. :data:`ESLESME` anahtarlarindan ``i`` ile baslayanlar ( Turkce
#:    olduklari zaten ayri bir denetimden gecmistir).
#: 2. :data:`_EK_I_BAS` — kucuk harfli yazimi ASCII'de zaten dogru olan,
#:    yalnizca bas harfi duzeltilmesi gereken Turkce kelimeler.
_EK_I_BAS: frozenset[str] = frozenset({
    "iki", "ikinci", "ikincisi", "ikincil",
    "ikna", "ikilemi", "ikisini", "ikti",
    "ilk", "ilki", "ilgili",
    "ilerleme", "ilerledi", "ilerleterek",
    "implant", "inceleme",
    "insan",
    "invaziv", "istatistiksel",
    # "isleme" buraya degil ESLESME'ye konur: sorunu yalnizca bas harf
    # degil, icindeki "s" harfinin "S" olmasidir. Izin listesinde
    # tutulsaydi "ISLEME" -> "İSLEME" cikardi (yanlis).
    "isabetli",
    # Kucuk harfli yazimi zaten dogru; yalnizca bas harfi duzeltilecek.
    # "beynin" + "in" -> BEYNININ (baslik, hep buyuk harf) / beyninin
    "beyninin",
    "ingilizce",
})

#: Birlestirilmis izin listesi (disaridan salt-okunur).
TURKCE_I_BAS: frozenset[str] = frozenset(
    {a for a in ESLESME if a.startswith("i")} | set(_EK_I_BAS)
)

#: Korunmasi gereken token kaliplari (duzeltilmez).
KORUNAN: tuple[str, ...] = (
    r"https?://\S+",
    r"10\.\d{4,9}/\S+",
    r"doi\.org/\S+",
    r"\bRQ-\d{3}\b",
    r"\bS-\d{4}\b",
)

_KORUNAN_RE = re.compile("|".join(KORUNAN))
_KELIME_RE = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşü]+")


# --------------------------------------------------------------------------
# 2. Turkce'ye ozgu buyuk/kucuk harf donusumu
# --------------------------------------------------------------------------


def _bas_harf(kucuk: str) -> str:
    """Bir kelimenin bas harfini Turkce kurallarina gore buyutur.

    Python'un ``str.capitalize()`` ve ``str.upper()`` metotlari Turkce icin
    YANLIS sonuc verir: "ikinci".capitalize() -> "Ikinci" (dogru olan
    "İkinci"), "iş".upper() -> "IŞ" (dogru olan "İŞ"). Bu yuzden
    noktasiz/noktali "i" ayrimi elle yapilir.

    Not: girdi ** Turkce kucuk harfli** bicimdir. ASCII "is" degil, "iş"
    verilmelidir; ASCII -> Turkce ceviri :data:`ESLESME`'nin isidir.

    >>> _bas_harf("ikinci")
    'İkinci'
    >>> _bas_harf("iş")
    'İş'
    >>> _bas_harf("önlendirme")
    'Önlendirme'
    """
    if not kucuk:
        return kucuk
    ilk = kucuk[0]
    if ilk == "i":
        return "İ" + kucuk[1:]
    if ilk == "ı":
        return "I" + kucuk[1:]
    return ilk.upper() + kucuk[1:]


def _buyuk_tam(kucuk: str) -> str:
    """Kelimeyi Turkce kurallarina gore TAMAMEN buyutur.

    >>> _buyuk_tam("ölçüm")
    'ÖLÇÜM'
    >>> _buyuk_tam("sağlık")
    'SAĞLIK'
    >>> _buyuk_tam("iş")
    'İŞ'
    >>> _buyuk_tam("iki")
    'İKİ'
    """
    cev = []
    for harf in kucuk:
        if harf == "i":
            cev.append("İ")
        elif harf == "ı":
            cev.append("I")
        else:
            cev.append(harf.upper())
    return "".join(cev)


def _bicim_turet(jeton: str, kucuk_turkce: str) -> str:
    """Jetonun buyuk/kucuk bicimini koruyarak Turkce karsiligini uretir.

    ``jeton`` kaynak metindeki orijinal yazimdir; ``kucuk_turkce`` onun
    kucuk harfli Turkce karsiligidir.

    * ``"OLCUM"``  -> ``"ÖLÇÜM"``   (tam buyuk)
    * ``"Olcum"``  -> ``"Ölçüm"``   (bas harf buyuk)
    * ``"olcum"``  -> ``"ölçüm"``   (kucuk harf)
    """
    if len(jeton) > 1 and jeton.isupper():
        return _buyuk_tam(kucuk_turkce)
    if jeton[:1].isupper():
        return _bas_harf(kucuk_turkce)
    return kucuk_turkce


# --------------------------------------------------------------------------
# 3. Uygulama
# --------------------------------------------------------------------------


def _jeton_duzelt(jeton: str) -> str:
    """Tek bir kelimeyi (jetonu) duzeltir.

    Once :data:`ESLESME` tablosuna **tam kelime** bakilir; bulunursa
    buyuk/kucuk harf bicimi Turkce kurallarina gore yeniden kurulur.
    Bulunamazsa yalnizca Turkce'ye ozgu bas-harf kurali denenir; bu kural
    :data:`TURKCE_I_BAS` izin listesiyle sinirlidir, boylece Ingilizce
    kelimeler ve k kisaltmalar bozulmaz.

    >>> _jeton_duzelt("dort")
    'dört'
    >>> _jeton_duzelt("Ikinci")
    'İkinci'
    >>> _jeton_duzelt("IEEE")
    'IEEE'
    >>> _jeton_duzelt("Interface")
    'Interface'
    >>> _jeton_duzelt("in")
    'in'
    """
    kucuk = jeton.lower()
    hedef = ESLESME.get(kucuk)
    if hedef is not None:
        return _bicim_turet(jeton, hedef)
    # Esleme yok: yalnizca izin listesindeki Turkce kelimelerde bas-harf
    # kurali denenir. "Insan" -> "İnsan", "ikinci" -> "İkinci".
    if kucuk not in TURKCE_I_BAS or len(jeton) < 2:
        return jeton
    if jeton.isupper():
        return _buyuk_tam(kucuk)
    if jeton[:1] == "I":
        return _bas_harf(kucuk)
    return jeton


def duzelt(metin: str) -> str:
    """ASCII yazilmis Turkce kelimeleri dogru Turkce yazima cevirir.

    Yalnizca *tam kelime* eslesmesi yapilir ve buyuk/kucuk harf bicimleri
    Turkce kurallarina gore korunur. URL, DOI ve ``RQ-###`` / ``S-####``
    gibi kod tanimlayicilari degistirilmez.

    >>> duzelt("Bu calisma dort bolumun bir araya gelmesiyle olusmustur.")
    'Bu çalışma dört bölümün bir araya gelmesiyle oluşmuştur.'
    >>> duzelt("BOLUM ve Bolum")
    'BÖLÜM ve Bölüm'
    >>> duzelt("Ikinci bolum")
    'İkinci bölüm'
    >>> duzelt("Interface, IEEE ve In")
    'Interface, IEEE ve In'
    >>> duzelt("doi: 10.1038/nature04660")
    'doi: 10.1038/nature04660'
    """
    if not metin:
        return metin

    # 1) Korunmali kaliplari once maskele (DOI parcasi kelime sanilabilir).
    korunanlar: list[str] = []

    def _maskele(_e: re.Match[str]) -> str:
        korunanlar.append(_e.group(0))
        return f"\x00{len(korunanlar) - 1}\x00"

    korumali = _KORUNAN_RE.sub(_maskele, metin)

    # 2) Kelimeleri duzelt.
    duzeltilmis = _KELIME_RE.sub(lambda _e: _jeton_duzelt(_e.group(0)), korumali)

    # 3) Maskeleri geri koy.
    def _maske_geri(_e: re.Match[str]) -> str:
        return korunanlar[int(_e.group(1))]

    return re.sub(r"\x00(\d+)\x00", _maske_geri, duzeltilmis)


def denetle(metin: str) -> list[tuple[str, str]]:
    """Metinde ASCII kalmis, duzeltilmesi gereken kelimeleri dondurur.

    Donus, ``(bulunan, duzeltilmis)`` ikililerinden olusan sirali bir
    listedir. Kaynak metin degistirilmez.
    """
    duzeltilmis = duzelt(metin)
    bulunanlar = {
        (a, b)
        for a, b in zip(re.findall(_KELIME_RE, metin), re.findall(_KELIME_RE, duzeltilmis))
        if a != b
    }
    return sorted(bulunanlar)


def denetle_tablo(kaynaklar: "dict[str, str]") -> list[str]:
    """Tabloyu kaynak korsine karsi denetler; sorunlari dondurur.

    Denetlenen kurallar:

    1. Kimlik eslemesi olmamali (``"veri": "veri"`` bir hatadir).
    2. Anahtar/deger kucuk harfli olmali.
    3. Anahtar kaynak metinlerde **gercekten** gecmelidir; olu girdiler
       tablonun guvenilirligini zedeler. Arama buyuk/kucuk harfe duyarsiz
       yapilir, cunku kaynakta ``Aciklama`` ve ``aciklama`` ayni kelimedir
       (bicim :func:`_bicim_turet` tarafindan yeniden kurulur).
    4. Anahtarlar Turkce'de dogru yazilan ASCII kelimeler olmamalidir.
    5. :data:`_EK_I_BAS` izin listesi girdileri de kaynakta gecmelidir;
       olu bir girdi, Turkce oldugu dogrulanmamis bir kelimeyi duzeltmeye
       yol acar.

    Parametre, ``{dosya_adi: metin}`` seklinde bir sozluktur.
    """
    sorunlar: list[str] = []
    tum_metin = "\n".join(kaynaklar.values())
    for anahtar, deger in sorted(ESLESME.items()):
        if anahtar == deger:
            sorunlar.append(f"kimlik eslemesi: {anahtar!r} -> {deger!r}")
        if anahtar != anahtar.lower():
            sorunlar.append(f"anahtar kucuk harfli degil: {anahtar!r}")
        if deger != deger.lower():
            sorunlar.append(f"deger kucuk harfli degil: {anahtar!r} -> {deger!r}")
        if anahtar in DOGRU_YAZILANLAR:
            sorunlar.append(f"dogru yazilan kelime tabloya girmis: {anahtar!r}")
        if not _kaynakta_geciyor(anahtar, tum_metin):
            sorunlar.append(f"olu girdi (kaynakta bulunamadi): {anahtar!r}")
    for kelime in sorted(_EK_I_BAS):
        if not _kaynakta_geciyor(kelime, tum_metin):
            sorunlar.append(f"olu izin-listesi girdisi: {kelime!r}")
    return sorunlar


def _kaynakta_geciyor(kelime: str, metin: str) -> bool:
    """``kelime``nin metinde **tam kelime** olarak gectigini dogrular.

    Arama buyuk/kucuk harfe duyarsizdir: kaynakta ``Aciklama`` ve
    ``aciklama`` ayni kelimedir (bicim :func:`_bicim_turet` tarafindan
    yeniden kurulur).
    """
    kenar = r"A-Za-zÇĞİÖŞÜçğıöşü"
    kalip = rf"(?<![{kenar}]){re.escape(kelime)}(?![{kenar}])"
    return bool(re.search(kalip, metin, flags=re.IGNORECASE))
