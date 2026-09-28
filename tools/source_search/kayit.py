"""`source.json` ile uyumlu kayıt üretimi.

Neden var
---------
Beş arama istemcisinin `to_source_dict` metodu aynı üç hatayı aynı
biçimde üretiyordu:

  1. `journal` / `volume` / `issue` / `pages` için `None`
     Semada bu alanlar **`string`**. `None` yazmak kaydı geçersiz kılar.
     Ölçüldü: 72 kayıtta 153 hata (`None is not of type 'string'`).
     Alanlar zorunlu DEĞİL; burada düşürülmek yerine boş dize
     yazılıyor, çünkü `edition`/`isbn`/`publisher` zaten bu geleneği
     kullanıyor ve `record` komutu da aynı şekli üretiyor.

  2. `access_date` için `""`
     Semada `date` ya da `null`. Boş dize `date` formatını sağlamaz.
     Erişim henüz olmadıysa `null` DOĞRU değerdir.

  3. `verification.verified_at` için `""`
     Semada **zorunlu** ve `date-time`. Boş dize reddedilir. Kayıt
     `pending` olsa bile bu alan dolu olmak zorunda; aramanın yapıldığı
     an, kaydın alındığı an olarak kullanılır.

Bu üç hata `thesis_state.json`'a **sessizce** yazılıyordu, çünkü
`tools/atw/cli/main.py` içindeki `save_state` doğrulama yapmıyor.
Ölçülen sonuç: `validate_state` 312 hata döndürdü.

Ayrıca `source.json` `additionalProperties: false` kullanıyor. Sızan bir
anahtar kaydı geçersiz kılar ve veri sessizce kaybolur. Bu yüzden
bilinmeyen anahtar **sessizce atılmaz, hata verir**: alan eşleme
hattası yazma anında görünür olmalı.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

#: Semada `string` olan, API'den `None` gelebilen alanlar.
STRING_ALANLAR: tuple[str, ...] = (
    "title",
    "journal",
    "publisher",
    "doi",
    "url",
    "volume",
    "issue",
    "pages",
    "edition",
    "isbn",
    "language",
    "verification_notes",
)

#: `verification` içinde zorunlu olan alanlar (schemas/source.json).
VERIFICATION_ZORUNLU: tuple[str, ...] = (
    "status",
    "bibliographic_match",
    "verified_at",
    "verification_sources",
)


def _simdi() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


#: DOI çözümleyici önekleri. Bazı veritabanları (OpenAlex) DOI'yi
#: `https://doi.org/10.xxxx/yyy` biçiminde döndürür. `source.json`
#: deseni `^$|^10\.\d{4,9}/\S+$` yani ÇIP formu ister. Önek kalırsa
#: kayıt geçersiz olur ve `verify` (DOI eşleşmesi yapar) hedefi bulamaz.
DOI_ONEKLERI: tuple[str, ...] = (
    "https://doi.org/",
    "http://doi.org/",
    "https://dx.doi.org/",
    "http://dx.doi.org/",
    "https://www.doi.org/",
    "doi:",
    "doi/",
)


def duzelt_doi(deger: Any) -> str:
    """DOI'yi şemanın beklediği çıplak biçime getirir.

    DOI olmayan bir değer boş dize döner: şema `^$`'a izin verir ve
    özgün tanımlayıcı `url` alanında zaten durur. `doi` alanına URL
    yazmak kaydı geçersiz kılar ve sessizce yanlış eşleştirmeye yol açar.
    """
    if not deger:
        return ""
    metin = str(deger).strip()
    for onek in DOI_ONEKLERI:
        if metin.lower().startswith(onek):
            metin = metin[len(onek):]
            break
    metin = metin.strip()
    return metin if metin.lower().startswith("10.") else ""


def sema_uyumlu(kayit: dict[str, Any], *, simdi: str | None = None) -> dict[str, Any]:
    """`source.json` sözleşmesine uyan bir kayıt döndürür.

    Args:
        kayit: `to_source_dict` çıktısı.
        simdi: `verified_at` için kullanılacak zaman damgası. Verilmezse
            UTC şimdi. Testlerin sabit değer kullanabilmesi içindir.

    Returns:
        Aynı kayıt, şemayı ihlal etmeyecek biçimde düzeltilmiş olarak.

    Raises:
        KeyError: Semada tanımsız bir anahtar varsa. Alan eşleme hatası
            yazma anında görünmelidir, kaybolmamalıdır.
        ValueError: `verification` zorunlu alanları taşımıyorsa.
    """
    from tools.atw.state import load_schema

    izinli = set(load_schema("source.json")["properties"])

    fazla = sorted(set(kayit) - izinli)
    if fazla:
        raise KeyError(
            f"source.json'da tanımsız alan(lar): {fazla}. "
            "Alan eşlemesi hatası; kayıt sessizce yazılırsa veri kaybolur."
        )

    duzeltilmis = dict(kayit)

    for alan in STRING_ALANLAR:
        if alan in duzeltilmis and duzeltilmis[alan] is None:
            duzeltilmis[alan] = ""

    if "doi" in duzeltilmis:
        duzeltilmis["doi"] = duzelt_doi(duzeltilmis["doi"])

    # `year` şemada isteğe bağlı ama varsa `integer` olmalı. Bazı
    # kayıtlarda yıl bilinmiyor; uydurma bir yıl yazmak yanlış künye
    # demektir, bu yüzden alan DÜŞÜRÜLÜR (şemada zorunlu değil).
    if duzeltilmis.get("year") is None:
        duzeltilmis.pop("year", None)
    elif isinstance(duzeltilmis["year"], str):
        if duzeltilmis["year"].strip().isdigit():
            duzeltilmis["year"] = int(duzeltilmis["year"].strip())
        else:
            duzeltilmis.pop("year")

    # `access_date`: erişim tarihi bilinmiyorsa `null`. Boş dize `date`
    # formatını sağlamaz.
    if duzeltilmis.get("access_date") == "":
        duzeltilmis["access_date"] = None

    dogrulama = duzeltilmis.get("verification")
    if not isinstance(dogrulama, dict):
        raise ValueError(
            "verification bir nesne olmalı; eksik alanlar: "
            f"{[a for a in VERIFICATION_ZORUNLU if not (dogrulama or {}).get(a)]}"
        )
    eksik = [a for a in VERIFICATION_ZORUNLU if a not in dogrulama]
    if eksik:
        raise ValueError(f"verification zorunlu alanları eksik: {eksik}")
    if not dogrulama["verified_at"]:
        dogrulama["verified_at"] = simdi or _simdi()

    return duzeltilmis
