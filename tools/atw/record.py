"""Registry yazımı: ajanın ürettiği JSON'u denetleyip tez durumuna yaz.

Neden bu modül
--------------
`empty_state()` 20 registry başlatıyor, ama çoğunun YAZICISI YOK.
Yazıcısı olanlar: ``search_runs`` + ``sources`` (``cmd_search``),
``evidence_registry`` (``cmd_extract``), ``chapters`` + ``paragraphs``
(``cmd_write``), ``audit_registry`` (``cmd_audit``).

Yazıcısı olmayanlardan biri ``research_questions``. Zincirleme sonuç:
soru kaydı yok → ``research_question`` kapısı hiç açılamaz → sonraki
altı kapı sırayla kilitli → ``write`` ve ``export`` erişilemez.
Ajanlar durumu göremez; ``agents/*.md`` yalnızca rapor üretir.

Tek komut, tek yazıcı
---------------------
Her registry için ayrı bir komut yazmak, her biri kendi testine sahip
birer ikinci yüzey olurdu. Bu depo tam olarak bu hastalıkla yaşıyor:
iki şema ağacı, iki ``empty_state``, ölü ``pdf_extract`` test dizini,
eksik ``__main__.py``, ``cmd_verify`` stub'ı. Bunun yerine tek bir
``record <registry> --file <json>`` yolu var: tek denetim, tek hata
biçimi, yeni registry eklemek = tabloya bir satır.

Tablo bile elle yazılmıyor: ``graph.registry_haritasi()`` eşleme
``thesis_state.json``'in ``$ref`` dizilerinden türetiliyor. Elle tablo,
yeni sema eklendiğinde sessizce eksik kalırdı.

``SAHIPLI_KOMUTLAR`` neden var
------------------------------
Bir registry'nin İKİ yazıcısı olmamalı. ``record sources`` ile
``search_runs`` eşlemesi atlanabilir, ``record chapters`` ile
``write``'ın kapı ve şema denetimi atlanabilirdi. Sahiplenilmiş
registry reddedilir ve SAHİBİ adıyla söylenir.

Kopuk referanslar neden reddediliyor
------------------------------------
Kayıt kendi şemasına uygun olsa bile var olmayan bir kayda işaret
ediyorsa yazılmaz. ``graph.kopuk_baglari`` bu kopukluğu zaten her
bütünlük denetiminde raporluyor; kayıt anında reddetmek "kopukluk ne
zaman oluştu" sorusuna da yanıt verir ve kökü tek yerde tutar.

Bu, ileri referansları da reddeder ve bu kasıtlıdır:

  * ``claim.contradicted_by`` — çelişen taraf önce yazılır, sonra
    karşı taraf bağlanır. ``graph.celiskili_iddialar`` çelişkinin
    **iki tarafını da** çelişkili sayar, dolayısıyla tek yönlü bir
    kayıt bırakmaya gerek yoktur.
  * ``research_question.answered_by`` — yalnızca bulgular yazıldıktan
    sonra doğru olabilir; erken doldurmak yanlışı kalıcılaştırır.
  * ``research_question.chapter`` — ilk soru bölüm alanını dolduramaz,
    çünkü ``chapters`` yazıcısı (``cmd_write``) soru kapısının ARKASINDA
    çalışır. Alan şemada zorunlu DEĞİLDİR; önce referanssız yazılır,
    bölüm oluşunca aynı kimlikle yeniden kaydedilir.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from tools.atw.graph import kopuk_baglari, registry_haritasi
from tools.atw.ids import ID_PREFIXES, next_id, parse_id
from tools.atw.state import load_schema


class KayitHatasi(ValueError):
    """Bir ya da birden çok kayıt yazılamadı.

    Mesaj tek satırdır ve TÜM hataları içerir; CLI hepsini basar.
    Kısmi yazma yapılmaz: dosyadaki kayıtlar ya hep yazılır ya hiç.
    """

    def __init__(self, mesajlar: list[str]) -> None:
        self.mesajlar = list(mesajlar)
        super().__init__("; ".join(self.mesajlar))


#: Başka bir komutun sahibi olduğu registry'ler. `record` bunları reddeder.
#: Değer, o registry'yi yazan komutun adıdır — hata mesajında kullanılır.
SAHIPLI_KOMUTLAR: dict[str, str] = {
    "sources": "thesis:search",
    "search_runs": "thesis:search",
    "evidence_registry": "thesis:extract",
    "chapters": "thesis:write",
    "paragraphs": "thesis:write",
    "audit_registry": "thesis:audit",
}


def yazilabilir_registryler() -> dict[str, str]:
    """`record` ile yazılabilen registry -> varlık tipi eşlemesi.

    `graph.registry_haritasi()` semadan türetilir; burada elle bir tablo
    yoktur. Sahiplenilmiş registry'ler çıkarılır.
    """
    return {
        alan: varlik
        for alan, varlik in registry_haritasi().items()
        if alan not in SAHIPLI_KOMUTLAR
    }


def yazilabilir_mi(registry: str) -> bool:
    return registry in yazilabilir_registryler()


def varlik_tipi(registry: str) -> str:
    """Registry'nin varlık tipini döner. Yazılabilir değilse hata verir.

    Raises:
        KayitHatasi: Bilinmeyen ya da sahiplenilmiş registry.
    """
    yazilabilir = yazilabilir_registryler()
    if registry not in yazilabilir:
        if registry in SAHIPLI_KOMUTLAR:
            raise KayitHatasi([
                f"{registry} registry'si thesis:record ile yazılamaz: "
                f"yazıcısı {SAHIPLI_KOMUTLAR[registry]}. İki yazıcı olursa "
                f"kapı ve şema denetimleri atlanır."
            ])
        gecerli = ", ".join(sorted(yazilabilir))
        raise KayitHatasi([
            f"Bilinmeyen registry: {registry}",
            f"Yazılabilir registry'ler: {gecerli}",
        ])
    return yazilabilir[registry]


#: Kayıt şeması doğrulayıcıları. Semalar değişmezse yeniden kurulmaz.
_DOGRULAYICILAR: dict[str, Draft202012Validator] = {}


def _dogrulayici(varlik: str) -> Draft202012Validator:
    if varlik not in _DOGRULAYICILAR:
        # `load_schema` dosya ADI ister: sonuna `.json` eklenir.
        sema = load_schema(f"{varlik}.json")
        # `format` denetleyicisi YOK: `tools.atw.state` bunu bilinçli
        # olarak ayrı bir kayıt defteri olarak kuruyor ve burada
        # `date-time` gibi anahtarlar sessizce geçmesin diye ikinci bir
        # kural kümesi kurmak yerine aynı yol izlenir: yalnız yapı ve
        # enum kısıtları burada denetlenir.
        _DOGRULAYICILAR[varlik] = Draft202012Validator(sema)
    return _DOGRULAYICILAR[varlik]


def kayitlari_oku(yol: Path | str) -> list[dict[str, Any]]:
    """JSON dosyasından kayıt listesini okur.

    İki biçim kabul edilir: tek bir kayıt nesnesi ya da kayıt dizisi.
    Ajan tek soru yazarken sarmalamak zorunda kalmamalı.

    Raises:
        KayitHatasi: Dosya okunamaz, JSON bozuk, içerik nesne değil ya da
            liste boş.
    """
    yol = Path(yol)
    try:
        ham = yol.read_text(encoding="utf-8-sig")
    except OSError as hata:
        raise KayitHatasi([f"Dosya okunamadı: {yol} ({hata})"]) from hata
    try:
        icerik = json.loads(ham)
    except json.JSONDecodeError as hata:
        raise KayitHatasi([f"JSON çözümlenemedi: {yol} ({hata})"]) from hata

    if isinstance(icerik, dict):
        kayitlar: list[Any] = [icerik]
    elif isinstance(icerik, list):
        kayitlar = icerik
    else:
        raise KayitHatasi([
            f"Beklenen kayıt nesnesi ya da dizi, bulunan: {type(icerik).__name__}"
        ])

    if not kayitlar:
        raise KayitHatasi([f"Dosya boş: {yol} (kayıt yok)"])
    return kayitlar


def _kimlik_uyarisi(kayit: dict, varlik: str, kayitlar: list[dict]) -> str | None:
    """Eksik ya da hatalı kimlik uyarısı. Sorun yoksa ``None``."""
    kimlik = kayit.get("id")
    if not kimlik:
        return None
    if not isinstance(kimlik, str):
        return f"id alanı metin olmalı, {type(kimlik).__name__} bulundu"
    try:
        prefiks, _ = parse_id(kimlik)
    except ValueError as hata:
        return f"id biçimi geçersiz: {kimlik} ({hata})"
    beklenen = {p for p, v in ID_PREFIXES.items() if v == varlik}
    if beklenen and prefiks not in beklenen:
        return (f"id ön eki yanlış: {kimlik} — {varlik} için "
                f"{'/'.join(sorted(beklenen))} beklenir")
    # Aynı dosyada iki kez aynı kimlik: hangisinin kazandığı belirsiz.
    ayni = sum(1 for k in kayitlar if isinstance(k, dict) and k.get("id") == kimlik)
    if ayni > 1:
        return f"dosyada yinelenen kimlik: {kimlik} ({ayni} kez)"
    return None


def dogrula(registry: str, kayitlar: list[dict], durum: dict) -> list[str]:
    """Kayıtları denetler. Hata yoksa boş liste döner.

    Üç denetim sırayla:

      1. SEMA — varlık şemasına karşı (`Draft202012Validator`).
      2. KİMLİK — ön ek, biçim, dosya içi tekrar.
      3. KOPUK REFERANS — kaydın TEK başına eklenmesiyle oluşan yeni
         kopukluk. Durumda zaten var olan kopukluklar kaydın suçu
         değildir ve sebep gösterilmez.

    Hiçbir hata varsa kayıt yazılmaz. Kısmi yazma yoktur.
    """
    varlik = varlik_tipi(registry)
    dogrulayici = _dogrulayici(varlik)
    hatalar: list[str] = []

    # Kimliksiz kayıtlar `kaydet` içinde atanır; burada atanmamış hâli
    # denetlenir. `dogrula` saf kalsın diye `durum` MUTASYONA UĞRAMAZ.
    onceki = durum.get(registry) or []
    kimlikler = [k.get("id") for k in onceki if isinstance(k, dict)]
    # Mevcut kayitlara YENI kayitlar EKLENMELI; registry'nin tamamini yeni
    # kayitlarla DEGISTIRMEK mevcut kayitlari siler ve kopuk_baglari kontrolunde
    # sahte 'kopuk referans' hatasi uretir. (Regresyon: ikinci citations kaydi
    # yapilamiyordu; mevcut CIT-001..008 kayboluyordu.)
    aday = dict(durum)
    aday[registry] = list(onceki) + [
        dict(k) if isinstance(k, dict) else k for k in kayitlar
    ]
    for kayit in kayitlar:
        if isinstance(kayit, dict) and not kayit.get("id"):
            kayit["id"] = next_id(kimlikler + [
                k.get("id") for k in kayitlar if isinstance(k, dict) and k.get("id")
            ], _onek(varlik))
    onceki_kopuk = set(kopuk_baglari(durum))

    for sira, kayit in enumerate(kayitlar, start=1):
        etiket = f"{registry}[{sira}]"
        if not isinstance(kayit, dict):
            hatalar.append(f"{etiket}: kayıt bir JSON nesnesi olmalı, "
                           f"{type(kayit).__name__} bulundu")
            continue
        uyari = _kimlik_uyarisi(kayit, varlik, kayitlar)
        if uyari:
            hatalar.append(f"{etiket}: {uyari}")
        for hata in dogrulayici.iter_errors(kayit):
            hatalar.append(f"{etiket}.{'.'.join(str(p) for p in hata.path) or ' kayıt'}: {hata.message}")

    # Kopuk referans: kayıt eklendikten SONRA oluşan yeni kopukluklar.
    yeni = [k for k in kopuk_baglari(aday) if k not in onceki_kopuk]
    for kopuk in yeni:
        hatalar.append(f"{registry}: kopuk referans — {kopuk}")

    return hatalar


def _onek(varlik: str) -> str:
    """Varlık tipinden kimlik ön eki. Bilinmiyorsa boş."""
    for prefiks, tip in ID_PREFIXES.items():
        if tip == varlik:
            return prefiks
    return ""


def kaydet(durum: dict, registry: str, kayitlar: list[dict]) -> dict[str, list[str]]:
    """Kayıtları duruma yazar. Aynı kimlik varsa DEĞİŞTİRİR.

    ``cmd_write``'ın bölüm/paragraf davranışıyla aynı: ikinci kayıt
    tekrardır, güncellemedir. Kimliksiz kayda ``ids.next_id`` ile bir
    sonraki boş kimlik atanır; numarayı ajan saymak zorunda değildir.

    Returns:
        ``{"eklendi": [...], "degistirildi": [...]}`` — kimlik listeleri.

    Raises:
        KayitHatasi: Doğrulama hatası varsa. Durum DEĞİŞTİRİLMEZ.
    """
    hatalar = dogrula(registry, kayitlar, durum)
    if hatalar:
        raise KayitHatasi(hatalar)

    mevcut = durum.get(registry)
    if not isinstance(mevcut, list):
        mevcut = []
    indeks = {
        k.get("id"): s
        for s, k in enumerate(mevcut)
        if isinstance(k, dict)
    }

    eklendi: list[str] = []
    degistirildi: list[str] = []
    for kayit in kayitlar:
        kimlik = kayit.get("id")
        konum = indeks.get(kimlik)
        if konum is None:
            mevcut.append(kayit)
            indeks[kimlik] = len(mevcut) - 1
            eklendi.append(kimlik)
        else:
            mevcut[konum] = kayit
            degistirildi.append(kimlik)

    durum[registry] = mevcut
    return {"eklendi": eklendi, "degistirildi": degistirildi}


def ozet(kayit: dict) -> str:
    """Kaydın insan tarafından okunur tek satırlık özeti.

    Nitelik alanı: `id` varsa o, yoksa kayıt sırası. `statement`/`text`
    varsa kısaltılmış metin eklenir. Alan adları varlık şemasından
    gelir; burada sabit bir liste yoktur.
    """
    kimlik = kayit.get("id", "?")
    for alan in ("statement", "text", "name", "title"):
        deger = kayit.get(alan)
        if isinstance(deger, str) and deger.strip():
            metin = " ".join(deger.split())
            if len(metin) > 72:
                metin = metin[:69] + "…"
            return f"{kimlik}  {metin}"
    return f"{kimlik}"
