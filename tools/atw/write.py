"""Yazım birimi: yazarlık ajanına brifing üretmek, yazdığını denetlemek.

Kapsam
------
`agents/writer.md` "Yazar sadece doğrulanmış girdilerle çalışır" diyor
ama hangi kaynakların doğrulanmış olduğu tek bir yerde yazılı değil.
`references/*.md` KURAL verir, tezin KAYITLARINI vermez; ajanın elinde
`references/` var, `thesis_state.json` yok.

Bu modül o boşluğu doldurur ve yazım girdisini denetler:

  * `brifing_uret` / `brifing_metni` — ajana verilecek doğrulanmış girdi
    kümesi. **Türkçe metin üretmez.** Metin yazmak `agents/writer.md`
    ajanının işidir; CLI'nin işi girdiyi hazırlamak ve çıktıyı denetlemek.
  * `bolum_dogrula` — ajanın ürettiği bölüm dosyasını denetler.
  * `bolumu_kaydet` — geçerse tez durumuna yazar.

Politika uydurulmadı
--------------------
Her kural mevcut koddan türer:

  * `hooks/writing_gate.py` — atıfın `source_id`'si tez durumunda olmalı,
    `style` `apa7` olmalı. Burada **canlı** duruma göre yeniden denetlenir;
    hook dosya yazımında, durum o sırada başka olabilir.
  * `tools/citation_check/checker.py:58` — `retraction_status ==
    "retracted"` olan kaynakla atıf yapılmaz. Aynı eşik: `expression_of_
    concern` ve `unknown` elenmez, çünkü depodaki tek mevcut retraksiyon
    kuralı yalnızca `retracted`'i kritik sayıyor. Genişletmek buradaki
    `audit` ile çelişen ikinci bir politika olurdu.
  * `graph.celiskili_iddialar` (satır 402-404) — çelişkinin **iki tarafı
    da** çelişkilidir. Daha dar bir kural aynı kaynağa ikinci, daha gevşek
    bir politika koymak olurdu.
  * `graph.retraksiyona_ugrayan_iddialar` — geri çekilmiş kaynağa dayanan
    iddia yazım girdisi olamaz.
  * `schemas/chapter.json` + `paragraph.json` — biçim, alan ve enum kısıtları.
  * `state.empty_state()` yorumu — `citation.paragraph_id` çözülebilmesi
    için `state["paragraphs"]` düz kayıtçısı dolu olmalı. Bu yüzden
    `bolumu_kaydet` paragrafları hem `chapter.paragraphs` içine hem düz
    kayıtçıya yazar. `graph._kayitlar` bu ikili yerleşimi zaten varsayıyor
    ("İç içe koleksiyonlar da dahil").

Hook katmanında kalan kurallar
------------------------------
`hooks/evidence_gate.py` bölüm DOSYASINDAN en az bir `CLM-` ve en az bir
`EVD-`/`SRC-` referansı ister. O kural hook katmanında kalır ve burada
**tekrar uygulanmaz**: aynı kararı iki yerde vermek ikinci bir
uygulama olurdu, ve hook'un regex'i ikinci uygulamadan daha zayıftır
(`.lower()`/birebir arama yerine canlı duruma karşı çözümleme yapar).
`skill.yaml` üzerinden dosya yazımında çalışır.

Burada `evidence_gate`'in KURAM güçlendirilmedi: "her paragraf en az bir
iddiaya atıf yapar" kuralı buraya alınmadı, çünkü hook bunu dosya düzeyinde
ister ve paragraf düzeyine taşımak yeni politika olurdu. `YAZIM_KURALLARI`
içinde ajana TAVSİYE olarak verilir, denetim olarak değil.
"""
from __future__ import annotations

import json
from typing import Any

from jsonschema import Draft202012Validator

from . import graph
from .state import load_schema, schema_registry

__all__ = [
    "YAZIM_KURALLARI",
    "YazimHatasi",
    "bolum_dogrula",
    "bolumu_kaydet",
    "brifing_metni",
    "brifing_uret",
    "haric_eden_iddialar",
    "haric_eden_kaynaklar",
]


class YazimHatasi(Exception):
    """Brifing üretilemeyecek durum (örneğin bilinmeyen araştırma sorusu)."""


#: Ajanın uyması gereken, CLI'nin DENETLEMEDİĞİ kurallar. Her biri
#: `references/` ya da mevcut kodla gerekçelendirilmiştir; brifing metninde
#: birebir basılır.
YAZIM_KURALLARI: tuple[str, ...] = (
    "Yeni SRC-, EVD-, CLM-, CIT- veya RQ- kimliği OLUŞTURMA; "
    "brifingdeki kimlikler tek doğruluk kaynağıdır.",
    "Doğrulanmış kaynak, kanıt veya iddiayı DEĞİŞTİRME; bu kayıtları yalnızca oku.",
    "Her paragrafın `text` alanı dolu olmalı; boş ya da yalnızca boşluklu "
    "paragraf yazma.",
    "Her paragrafta şu alanlar zorunludur: id, chapter, type, text, "
    "research_questions.",
    "Yazdığın her iddianın dayanağını göster: iddia için CLM-, kanıt için "
    "EVD-, kaynak için SRC- referansı yaz.",
)

#: Paragrafın bölüme geri bağlandığı alan (`graph.kenar_tablosu` bu kenarı
#: izler).
_BOLUM_ALANI = "chapter"

#: Paragrafta bulunabilecek referans alanları -> hedef varlık tipi.
#: `graph.registry_haritasi()`'nın kayıtçı adlarıyla eşleşir.
_REFERANS_ALANLARI: dict[str, str] = {
    "claims": "claim",
    "evidence": "evidence",
    "sources": "source",
    "citations": "citation",
    "research_questions": "research_question",
}

#: Kaynağın yazıma girememe nedeni. `tools/citation_check/checker.py:58`.
_RETRAKSIYON_DEGERI = "retracted"


# --- yardimcilar ------------------------------------------------------------

def _kayitlar(durum: dict[str, Any], alan: str) -> list[dict[str, Any]]:
    """Durumdaki bir kayıtçı alanının kayıtları (yoksa boş liste)."""
    deger = durum.get(alan)
    if not isinstance(deger, list):
        return []
    return [k for k in deger if isinstance(k, dict)]


def _kimlikle_esles(kayitlar: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Kimlik -> kayit haritası. Kimliği olmayan kayıtlar atlanır."""
    harita: dict[str, dict[str, Any]] = {}
    for kayit in kayitlar:
        kimlik = kayit.get("id")
        if isinstance(kimlik, str) and kimlik:
            harita[kimlik] = kayit
    return harita


def _metin(kayit: dict[str, Any], alan: str) -> str:
    deger = kayit.get(alan)
    return deger.strip() if isinstance(deger, str) else ""


def _haric(harita: dict[str, str]) -> list[dict[str, str]]:
    """``{id: neden}`` -> ``[{"id":..., "neden":...}]``, kimliğe göre sıralı."""
    return [{"id": kimlik, "neden": neden} for kimlik, neden in sorted(harita.items())]


# --- kaynak filtresi --------------------------------------------------------

def haric_eden_kaynaklar(durum: dict[str, Any]) -> tuple[list[dict], list[dict]]:
    """Yazıma girebilen kaynaklar ve giremeyenler.

    Girebilmek için: ``retraction_status`` ``retracted`` DEĞİL ve
    ``verification.status`` ``verified``.

    Returns:
        ``(verilen, haric)``. ``haric`` öğeleri ``{"id", "neden"}``.
    """
    verilen: list[dict[str, Any]] = []
    haric: dict[str, str] = {}
    for kaynak in _kayitlar(durum, "sources"):
        kimlik = kaynak.get("id")
        if not (isinstance(kimlik, str) and kimlik):
            continue
        if kaynak.get("retraction_status") == _RETRAKSIYON_DEGERI:
            haric[kimlik] = "retraksiyon: geri çekilmiş kaynak"
            continue
        dogrulama = kaynak.get("verification")
        dogrulama = dogrulama if isinstance(dogrulama, dict) else {}
        durum_degeri = dogrulama.get("status")
        if durum_degeri != "verified":
            haric[kimlik] = f"doğrulanmamış (verification.status={durum_degeri!r})"
            continue
        verilen.append(kaynak)
    return verilen, _haric(haric)


# --- iddia filtresi ---------------------------------------------------------

def haric_eden_iddialar(durum: dict[str, Any]) -> tuple[list[dict], list[dict]]:
    """Yazıma girebilen iddialar ve giremeyenler.

    Girebilmek için: ``verification_status == "verified"``, çelişkili
    olmamak (``graph.celiskili_iddialar``) ve dayandığı kaynak geri
    çekilmemiş olmak (``graph.retraksiyona_ugrayan_iddialar``).
    """
    celiskili = set(graph.celiskili_iddialar(durum))
    retraksiyonda = set(graph.retraksiyona_ugrayan_iddialar(durum))

    verilen: list[dict[str, Any]] = []
    haric: dict[str, str] = {}
    for iddia in _kayitlar(durum, "claims_registry"):
        kimlik = iddia.get("id")
        if not (isinstance(kimlik, str) and kimlik):
            continue
        if kimlik in celiskili:
            haric[kimlik] = "çelişkili (graph.celiskili_iddialar)"
            continue
        if kimlik in retraksiyonda:
            haric[kimlik] = "dayandığı kaynak geri çekilmiş"
            continue
        durum_degeri = iddia.get("verification_status")
        if durum_degeri != "verified":
            haric[kimlik] = f"doğrulanmamış (verification_status={durum_degeri!r})"
            continue
        verilen.append(iddia)
    return verilen, _haric(haric)


# --- kanit filtresi ---------------------------------------------------------

def _kanitlari_ayir(
    durum: dict[str, Any],
    iddia_kimlikleri: set[str],
    kaynak_kimlikleri: set[str],
) -> tuple[list[dict], list[dict]]:
    """Yazıma girebilen kanıtlar ve giremeyenler.

    Kanıt iki koşul birden sağlamalı: bir yazılabilir iddiaya bağlı
    olmalı (``supports_claim``) ve kaynağı yazılabilir kaynaklar
    arasında olmalı. Aksi halde brifing, ajana verilmemiş bir kaynak
    kimliğini sızdırırdı.
    """
    verilen: list[dict[str, Any]] = []
    haric: dict[str, str] = {}
    for kanit in _kayitlar(durum, "evidence_registry"):
        kimlik = kanit.get("id")
        if not (isinstance(kimlik, str) and kimlik):
            continue
        hedef = kanit.get("supports_claim")
        if not (isinstance(hedef, str) and hedef):
            haric[kimlik] = "bir iddiaya bağlı değil (supports_claim yok)"
            continue
        if hedef not in iddia_kimlikleri:
            haric[kimlik] = f"iddiası yazıma giremiyor ({hedef})"
            continue
        kaynak_id = kanit.get("source_id")
        if kaynak_id not in kaynak_kimlikleri:
            haric[kimlik] = f"kaynağı yazıma giremiyor ({kaynak_id})"
            continue
        verilen.append(kanit)
    return verilen, _haric(haric)


# --- brifing ----------------------------------------------------------------

def brifing_uret(durum: dict[str, Any], bolum_id: str, rq_id: str) -> dict[str, Any]:
    """Yazar ajanına verilecek doğrulanmış girdi kümesini üretir.

    Kapsam dahil her kayıt üç gruba ayrılır: **verilen**, **hariç
    tutulanlar** (nedeniyle birlikte) ve kurallar. Hariç tutulanların
    nedeni yazılmazsa ajan aynı kaynağı tez durumundan bulup kullanır;
    bu yüzden neden zorunludur.

    Args:
        durum: Tez durumu.
        bolum_id: Yazılacak bölüm (``CH-\\d{3,}``).
        rq_id: Yanıtlanacak araştırma sorusu (``RQ-\\d{3,}``).

    Returns:
        Brifing sözlüğü. Şemalar altında serbest bırakılmıştır; anahtarlar
        ``bolum``, ``arastirma_sorusu``, ``iddialar``, ``kanitlar``,
        ``kaynaklar``, ``haric_tutulanlar`` ve ``kurallar``.

    Raises:
        YazimHatasi: ``rq_id`` tez durumunda yoksa.
    """
    soru = _kimlikle_esles(_kayitlar(durum, "research_questions")).get(rq_id) if rq_id else None
    if soru is None and rq_id is not None:
        raise YazimHatasi(f"Araştırma sorusu bulunamadı: {rq_id}")

    iddialar, haric_iddia = haric_eden_iddialar(durum)
    kaynaklar, haric_kaynak = haric_eden_kaynaklar(durum)
    kanitlar, haric_kanit = _kanitlari_ayir(
        durum,
        {i["id"] for i in iddialar},
        {k["id"] for k in kaynaklar},
    )

    bolum = _kimlikle_esles(_kayitlar(durum, "chapters")).get(bolum_id) or {}

    return {
        "bolum": {
            "id": bolum_id,
            "var": bool(bolum),
            "number": bolum.get("number"),
            "title": bolum.get("title") or "",
            "goal": bolum.get("goal") or "",
        },
        "arastirma_sorusu": soru,
        "iddialar": iddialar,
        "kanitlar": kanitlar,
        "kaynaklar": kaynaklar,
        "haric_tutulanlar": {
            "iddialar": haric_iddia,
            "kanitlar": haric_kanit,
            "kaynaklar": haric_kaynak,
        },
        "kurallar": list(YAZIM_KURALLARI),
    }


def _kaynak_etiketi(kaynak: dict[str, Any]) -> str:
    """APA'ya yakın tek satırlık etiket: `Orman, A. (2023) — başlık`."""
    yazarlar = kaynak.get("authors")
    yazar = ", ".join(str(a) for a in yazarlar) if isinstance(yazarlar, list) else "—"
    yil = kaynak.get("year")
    return f"{yazar} ({yil}) — {kaynak.get('title') or '(başlıksız)'}"


def brifing_metni(brifing: dict[str, Any]) -> str:
    """Brifingi ajanın okuyacağı düz metne çevirir.

    Kullanılabilir her kimlik metinde AÇIKÇA yer alır: kimliği metinde
    olmayan kaynak ya da iddia, ajanın kullanımına sunulmuş sayılmaz.
    """
    bolum = brifing["bolum"]
    soru = brifing["arastirma_sorusu"]
    satirlar: list[str] = []

    satirlar.append(f"YAZIM BRİFİNGİ — bölüm {bolum['id']} — soru {soru['id']}")
    satirlar.append("")

    satirlar.append(f"  Soru ({soru['id']}, {soru.get('type')}, {soru.get('status')}):")
    satirlar.append(f"    {soru.get('text') or ''}")
    if soru.get("method"):
        satirlar.append(f"    yöntem: {soru['method']}")
    satirlar.append("")

    satirlar.append(f"  Bölüm: var={_evet_hayir(bolum['var'])}")
    if bolum["var"]:
        satirlar.append(f"    numara: {bolum['number']}")
        satirlar.append(f"    başlık: {bolum['title'] or '—'}")
        if bolum.get("goal"):
            satirlar.append(f"    amaç: {bolum['goal']}")
    else:
        satirlar.append("    Henüz kayıtlı değil; numarayı ve başlığı sen seç.")
    satirlar.append("")

    satirlar.append(f"  İDDİALAR ({len(brifing['iddialar'])})")
    if not brifing["iddialar"]:
        satirlar.append("    (yazılabilir doğrulanmış iddia yok)")
    for iddia in brifing["iddialar"]:
        satirlar.append(
            f"    {iddia['id']}  [{iddia.get('importance')}]  {iddia.get('text') or ''}"
        )
        for kimlik in iddia.get("evidence_ids") or []:
            satirlar.append(f"        kanıt: {kimlik}")
        for kimlik in iddia.get("sources") or []:
            satirlar.append(f"        kaynak: {kimlik}")
    satirlar.append("")

    satirlar.append(f"  KANITLAR ({len(brifing['kanitlar'])})")
    if not brifing["kanitlar"]:
        satirlar.append("    (yazılabilir kanıt yok)")
    for kanit in brifing["kanitlar"]:
        konum = kanit.get("location") or {}
        yer = ", ".join(
            f"{anahtar}={deger}"
            for anahtar, deger in sorted(konum.items())
            if deger is not None
        )
        satirlar.append(
            f"    {kanit['id']} ← {kanit.get('source_id')}"
            f"  [{kanit.get('strength')}/{kanit.get('evidence_type')}]"
        )
        if yer:
            satirlar.append(f"        konum: {yer}")
        alinti = _metin(kanit, "text")
        if alinti:
            satirlar.append(f"        alıntı: {alinti}")
    satirlar.append("")

    satirlar.append(f"  KAYNAKLAR ({len(brifing['kaynaklar'])})")
    if not brifing["kaynaklar"]:
        satirlar.append("    (yazılabilir doğrulanmış kaynak yok)")
    for kaynak in brifing["kaynaklar"]:
        satirlar.append(f"    {kaynak['id']}  {_kaynak_etiketi(kaynak)}")
        if kaynak.get("doi"):
            satirlar.append(f"        doi: {kaynak['doi']}")
    satirlar.append("")

    haric = brifing["haric_tutulanlar"]
    satirlar.append(
        f"  HARİÇ TUTULANLAR "
        f"(iddia {len(haric['iddialar'])}, kanıt {len(haric['kanitlar'])}, "
        f"kaynak {len(haric['kaynaklar'])})"
    )
    gruplar = (("iddia", "iddialar"), ("kanıt", "kanitlar"), ("kaynak", "kaynaklar"))
    for etiket, anahtar in gruplar:
        for giris in haric[anahtar]:
            satirlar.append(f"    {etiket} {giris['id']}: {giris['neden']}")
    satirlar.append("")

    satirlar.append("  KURALLAR")
    for sira, kural in enumerate(brifing["kurallar"], 1):
        satirlar.append(f"    {sira}. {kural}")
    satirlar.append("")
    satirlar.append("  Çıktı: `chapter.json` biçiminde TEK bölüm dosyası.")
    satirlar.append("  Denetim sonrası kaydedilir: thesis write <CH-ID> --rq <RQ-ID> --file <yol>")

    return "\n".join(satirlar)


def _evet_hayir(deger: bool) -> str:
    return "evet" if deger else "hayır"


# --- dogrulama --------------------------------------------------------------

def _sema_denetleyicisi() -> Draft202012Validator:
    """`chapter.json` belge denetleyicisi.

    `FormatChecker` bilerek bağlanmıyor: `chapter.json` / `paragraph.json`
    / `citation.json` hiçbir `format` anahtarı içermiyor, yani bağlamak
    ölü ağırlık olurdu. Tarih biçimi kısıtı olan belgeler (`source.json`
    `verified_at` gibi) `state.validate_state` içinde, kendi
    denetleyicisiyle zaten denetleniyor.
    """
    return Draft202012Validator(
        load_schema("chapter.json"),
        registry=schema_registry(),
    )


def _yol_adimlari(denetim: Any) -> str:
    adimlar = [str(adim) for adim in denetim.absolute_path]
    return "/".join(adimlar) if adimlar else "bölüm"


def bolum_dogrula(
    bolum: dict[str, Any],
    durum: dict[str, Any],
    bolum_id: str,
    rq_id: str,
) -> list[str]:
    """Ajanın ürettiği bölüm dosyasını denetler.

    Denetlenenler:

      1. **Sema** — `schemas/chapter.json` (paragraflar dahil).
      2. **Kimlik** — dosyadaki `id` istenen `bolum_id` ile aynı, `number`
         geçerli, `title` boş değil. `write CH-002` çağrısı CH-003 dosyasını
         kabul etmez: ajan yanlış dosyayı yazmış olabilir ve kaydetmek tezi
         sessizce yanlış bölümle değiştirirdi.
      3. **Paragraf metadata'sı** — `text` dolu, `chapter` geri bağlantısı
         doğru, kimlikler bölüm içinde tekrar etmiyor. Kimlik biçimi şemanın
         işidir (``^P-\\d{3,}$``); burada yalnızca tekrarlanır.
      4. **Uydurma kimlik yok** — her `CLM-`/`EVD-`/`SRC-`/`CIT-`/`RQ-`
         referansı CANLI durumda çözülebiliyor. Bu, `hooks/writing_gate.py`
         denetimini durum o an için yeniden yapar.
      5. **Atıf kuralları** — atıf `apa7`; kaynağı var, geri çekilmemiş ve
         doğrulanmış; atfın `paragraph_id`'si bu bölümdeki bir paragrafa
         işaret ediyor.
      6. **Soru bağı** — bölüm en az bir paragraf yazdıysa, istenen
         araştırma sorusunu anmalı.

    Args:
        bolum: Denetlenecek bölüm sözlüğü.
        durum: Tez durumu (referansların çözüleceği kaynak).
        bolum_id: Yazılması istenen bölüm. Dosya bu kimliği taşımıyorsa
            reddedilir.
        rq_id: Yanıtlanması istenen araştırma sorusu.

    Returns:
        Hata mesajları listesi. Sorun yoksa boş liste. Tüm sorunlar
        bildirilir; ilk hatada durulmaz.
    """
    hatalar: list[str] = []

    for denetim in _sema_denetleyicisi().iter_errors(bolum):
        hatalar.append(f"sema: {_yol_adimlari(denetim)}: {denetim.message}")

    hatalar.extend(_kimlik_hatalari(bolum, bolum_id))
    hatalar.extend(_paragraf_hatalari(bolum, bolum_id))
    hatalar.extend(_referans_hatalari(bolum, durum))
    hatalar.extend(_atif_hatalari(bolum, durum, bolum_id))
    hatalar.extend(_soru_hatalari(bolum, durum, rq_id))

    return hatalar


def _kimlik_hatalari(bolum: dict[str, Any], bolum_id: str) -> list[str]:
    """Bölümün kimliği: istenen `id`, `number`, `title`."""
    hatalar: list[str] = []

    gercek = bolum.get("id")
    if not isinstance(gercek, str) or not gercek:
        hatalar.append(f"bölüm: kimlik (id) eksik: {gercek!r}")
    elif gercek != bolum_id:
        hatalar.append(
            f"bölüm: kimlik uyuşmuyor — istenen {bolum_id}, dosyada {gercek}"
        )

    numara = bolum.get("number")
    if not isinstance(numara, int) or isinstance(numara, bool) or numara < 1:
        hatalar.append(f"bölüm: numara (number) eksik veya geçersiz: {numara!r}")

    if not _metin(bolum, "title"):
        hatalar.append("bölüm: başlık (title) boş")

    return hatalar


def _paragraf_hatalari(bolum: dict[str, Any], bolum_id: str) -> list[str]:
    """Paragraf metadata'sı: metin dolu mu, geri bağlantı doğru mu, tekrar var mı."""
    paragraflar = bolum.get("paragraphs")
    if not isinstance(paragraflar, list):
        return []

    hatalar: list[str] = []
    gorulen: dict[str, int] = {}
    for sira, paragraf in enumerate(paragraflar, 1):
        if not isinstance(paragraf, dict):
            hatalar.append(f"paragraphs/{sira}: paragraf bir JSON nesnesi değil")
            continue
        kimlik = paragraf.get("id")
        etiket = kimlik if isinstance(kimlik, str) and kimlik else f"paragraphs/{sira}"

        if not _metin(paragraf, "text"):
            hatalar.append(f"{etiket}: paragraf metni boş")

        geri = paragraf.get(_BOLUM_ALANI)
        if geri != bolum_id:
            hatalar.append(
                f"{etiket}: {_BOLUM_ALANI} alanı {geri!r}, bölüm {bolum_id} olmalı"
            )

        if isinstance(kimlik, str) and kimlik:
            if kimlik in gorulen:
                hatalar.append(
                    f"{etiket}: paragraf kimliği bölüm içinde tekrar ediyor "
                    f"(ilk kez paragraphs/{gorulen[kimlik]})"
                )
            else:
                gorulen[kimlik] = sira

    return hatalar


def _referans_hatalari(bolum: dict[str, Any], durum: dict[str, Any]) -> list[str]:
    """Paragraflardaki her kimlik referansı tez durumunda çözülebiliyor mu?

    `hooks/writing_gate.py` `source_id`'yi dosya yazımında denetler; burada
    aynı denetim CANLI duruma göre yapılır. Durum değişmiş olabilir
    (kaynak silinmiş), o yüzden iki katman aynı şeyi farklı anda kontrol
    eder.
    """
    paragraflar = bolum.get("paragraphs")
    if not isinstance(paragraflar, list):
        return []

    cozulmus: dict[str, set[str]] = {}
    for alan, tip in _REFERANS_ALANLARI.items():
        kayitci = _kayitci_adi(tip)
        cozulmus[alan] = set(_kimlikle_esles(_kayitlar(durum, kayitci)))

    hatalar: list[str] = []
    for sira, paragraf in enumerate(paragraflar, 1):
        if not isinstance(paragraf, dict):
            continue
        kimlik = paragraf.get("id")
        etiket = kimlik if isinstance(kimlik, str) and kimlik else f"paragraphs/{sira}"
        for alan, var_idler in cozulmus.items():
            referanslar = paragraf.get(alan)
            if not isinstance(referanslar, list):
                continue
            for referans in referanslar:
                if isinstance(referans, str) and referans not in var_idler:
                    hatalar.append(
                        f"{etiket}: {alan} referansı {referans} tez durumunda "
                        f"bulunamadı (uydurulmuş olabilir)"
                    )
    return hatalar


def _kayitci_adi(varlik_tipi: str) -> str:
    """Varlık tipi -> durum alanı (``graph.registry_haritasi``).

    Bulunamazsa yer tutucu döner; `_kayitlar` onu boş sayar, yani
    bilinmeyen bir tip sessizce "hiçbir referans çözülemez" gibi davranır
    ve `_referans_hatalari` her referansı uydurma olarak bildirir. Bu,
    sessiz geçişten iyidir.
    """
    for alan, tip in graph.registry_haritasi().items():
        if tip == varlik_tipi:
            return alan
    return f"__cozulmeyen_tip__{varlik_tipi}"


def _atif_hatalari(
    bolum: dict[str, Any],
    durum: dict[str, Any],
    bolum_id: str,
) -> list[str]:
    """Atıfların Writing Gate kuralları: `apa7`, kaynak var/geçerli, paragraf bağlı."""
    paragraflar = bolum.get("paragraphs")
    if not isinstance(paragraflar, list):
        return []

    atiflar = _kimlikle_esles(_kayitlar(durum, "citations"))
    kaynaklar = _kimlikle_esles(_kayitlar(durum, "sources"))
    bolum_paragraf_kimlikleri = {
        p.get("id") for p in paragraflar if isinstance(p, dict) and p.get("id")
    }

    hatalar: list[str] = []
    for sira, paragraf in enumerate(paragraflar, 1):
        if not isinstance(paragraf, dict):
            continue
        paragraf_kimlik = paragraf.get("id")
        etiket = (
            paragraf_kimlik
            if isinstance(paragraf_kimlik, str) and paragraf_kimlik
            else f"paragraphs/{sira}"
        )
        referanslar = paragraf.get("citations")
        if not isinstance(referanslar, list):
            continue
        for atif_id in referanslar:
            if not isinstance(atif_id, str):
                continue
            atif = atiflar.get(atif_id)
            if atif is None:
                # Varlıksızlık `_referans_hatalari`'nde bildirildi.
                continue
            hatalar.extend(_tek_atif_hatalari(atif, atif_id, kaynaklar))
            hedef = atif.get("paragraph_id")
            if hedef not in bolum_paragraf_kimlikleri and bolum_paragraf_kimlikleri:
                hatalar.append(
                    f"{etiket}: atıf {atif_id} paragraf {hedef!r} için kayıtlı, "
                    f"bölüm {bolum_id} içindeki paragraflarda yok"
                )
    return hatalar


def _tek_atif_hatalari(
    atif: dict[str, Any],
    atif_id: str,
    kaynaklar: dict[str, dict[str, Any]],
) -> list[str]:
    hatalar: list[str] = []

    stil = atif.get("style")
    if stil != "apa7":
        hatalar.append(f"atıf {atif_id}: stili {stil!r} değil, 'apa7' olmalı")

    kaynak_id = atif.get("source_id")
    kaynak = kaynaklar.get(kaynak_id) if isinstance(kaynak_id, str) else None
    if kaynak is None:
        return hatalar

    if kaynak.get("retraction_status") == _RETRAKSIYON_DEGERI:
        hatalar.append(
            f"atıf {atif_id}: kaynağı {kaynak_id} geri çekilmiş "
            f"(retraksiyon: {_RETRAKSIYON_DEGERI}), atıf yapılamaz"
        )
        return hatalar

    dogrulama = kaynak.get("verification")
    dogrulama = dogrulama if isinstance(dogrulama, dict) else {}
    dogrulama_durumu = dogrulama.get("status")
    if dogrulama_durumu != "verified":
        hatalar.append(
            f"atıf {atif_id}: kaynağı {kaynak_id} doğrulanmamış "
            f"(verification.status={dogrulama_durumu!r})"
        )

    return hatalar


def _soru_hatalari(
    bolum: dict[str, Any],
    durum: dict[str, Any],
    rq_id: str,
) -> list[str]:
    """Bölüm, istenen araştırma sorusunu anıyor mu?

    Kural komutun KENDİ imzasından gelir: `write <CH-ID> --rq <RQ-ID>`
    "bu bölüm bu soruyu yanıtlasın" demektir. Hiçbir paragraf soruyu
    anmıyorsa bölüm başka bir soruyu yanıtlıyordur.

    Paragrafsız bölümde kural uygulanmaz: yazı henüz başlamamış olabilir
    ve `write` ilk çalıştırmada boş bölüm üretmekten de sorumlu değil.

    RQ'suz bölümde (giriş/literatür/yöntem/sonuç) kural uygulanmaz: bölüm
    bir RQ'ya bağlı değil, RQ anması hata değil.
    """
    if not rq_id:
        return []

    if _kimlikle_esles(_kayitlar(durum, "research_questions")).get(rq_id) is None:
        return [f"araştırma sorusu tez durumunda bulunamadı: {rq_id}"]

    paragraflar = bolum.get("paragraphs")
    if not isinstance(paragraflar, list) or not paragraflar:
        return []

    for paragraf in paragraflar:
        if not isinstance(paragraf, dict):
            continue
        referanslar = paragraf.get("research_questions")
        if isinstance(referanslar, list) and rq_id in referanslar:
            return []

    return [f"bölüm, istenen araştırma sorusunu ({rq_id}) hiçbir paragrafında anmıyor"]


# --- kayit ------------------------------------------------------------------

def bolumu_kaydet(durum: dict[str, Any], bolum: dict[str, Any]) -> dict[str, Any]:
    """Bölümü tez durumuna yazar (aynı `id` ile değiştirir).

    Paragraflar İKİ yere yazılır:

      * ``durum["chapters"][i]["paragraphs"]`` — metnin yaşadığı yer,
        `tools/atw/export.py` buradan okur.
      * ``durum["paragraphs"]`` — düz kayıtçı. `citation.paragraph_id`
        bu kayıtçıya çözülür; `state.empty_state()` yorumu bunu açıkça
        belirtir ("Bu registry olmadan atıfların paragraf referansı
        ÇÖZÜMSÜZ kalır"). `graph._kayitlar` ikili yerleşimi zaten
        varsayıyor.

    Bölümden silinen paragraflar düz kayıtçıdan da silinir; aksi halde
    bölümde olmayan bir paragrafa atıf bırakılmış olurdu.

    Args:
        durum: Değiştirilecek tez durumu (yerinde).
        bolum: `bolum_dogrula`'dan geçmiş bölüm.

    Returns:
        Yazılan bölüm.
    """
    bolum_id = bolum["id"]
    paragraflar = [p for p in (bolum.get("paragraphs") or []) if isinstance(p, dict)]

    duz = [
        p
        for p in _kayitlar(durum, "paragraphs")
        if p.get(_BOLUM_ALANI) != bolum_id
    ]
    for paragraf in paragraflar:
        kayit = dict(paragraf)
        kayit.setdefault(_BOLUM_ALANI, bolum_id)
        duz.append(kayit)
    durum["paragraphs"] = duz

    bolumler = durum.setdefault("chapters", [])
    for sira, mevcut in enumerate(bolumler):
        if isinstance(mevcut, dict) and mevcut.get("id") == bolum_id:
            bolumler[sira] = bolum
            break
    else:
        bolumler.append(bolum)

    return bolum
