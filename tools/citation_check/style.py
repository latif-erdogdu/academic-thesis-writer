"""APA 7 atif bicim denetimi.

tools/citation_check/README.md "Stil Dogrulama (APA 7 Ornegi)" bolumune gore
parantez ici atif bicimlerini dogrular.
"""
from __future__ import annotations

import re

_YIL_DESENI = re.compile(r"\b(?:19|20)\d{2}\b")
_ET_AL_DESENI = re.compile(r"\bet\s+al\.|\bvd\.|\bve\s+diğer", re.IGNORECASE)
_AYIRICI_DESENI = re.compile(r"\s*&\s*|\s+ve\s+|\s+and\s+", re.IGNORECASE)


def validate_apa7(in_text_form: str) -> list[str]:
    """APA 7 parenthetical atif bicimini dogrular.

    Donen liste bos ise bicim sorunsuzdur. Doluysa her oge bir sorun
    aciklamasidir ve dogrudan kullaniciya gosterilebilir.
    """
    metin = (in_text_form or "").strip()
    if not metin:
        return ["in_text_form alani bos."]

    sorunlar: list[str] = []
    for parca in metin.split(";"):
        temiz = parca.strip()
        sorun = _tek_girdi_dogrula(temiz)
        if sorun is not None:
            sorunlar.append(f"{temiz}: {sorun}")
    return sorunlar


def _tek_girdi_dogrula(girdi: str) -> str | None:
    """Tek bir atif girdisini dogrular; sorun yoksa None doner."""
    if not girdi:
        return "Atif parcasi bos."

    yil = _YIL_DESENI.search(girdi)
    if yil is None:
        return "Yil (19xx/20xx) bulunamadi."

    yazar_kismi = girdi[:yil.start()].strip().strip("(").strip().rstrip(",").strip()
    if not yazar_kismi:
        return "Yazar adi bulunamadi."

    # 3+ yazar kisa formu ("et al." / "vd.") ve 2 yazar ayiricisi ('&', 've') gecerli.
    if _ET_AL_DESENI.search(yazar_kismi):
        return None
    if _AYIRICI_DESENI.search(yazar_kismi):
        return None

    yazarlar = [a.strip() for a in yazar_kismi.split(",") if a.strip()]
    sayi = len(yazarlar)
    if sayi <= 1:
        return None
    if sayi == 2:
        return "Iki yazarli atif '&' veya 've' ile ayrilmali."
    return f"{sayi} yazarli atif 'et al.' ile kisaltilmalidir."
