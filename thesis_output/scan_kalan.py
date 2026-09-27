# -*- coding: utf-8 -*-
"""Goc sonrasi **kalan** ASCII jetonlarini doker (frekansa gore).

`scan_ascii_sentences.py` yalnizca *tamamen* ASCII satirlari yakalar; oysa
goc sonrasi asil risk **karisik** satirlardir ("temiş ettigi iki temel
varsayimi — çıkarım ..."). Bu betik, icerik dizelerinde hayatta kalan her
ASCII jetonu tek tek listeler; gozle denetlenir.

Ayirici kurallar:
  * Jeton Turkce'ye ozgu bir diyakritik *icermeyen* ASCII harflerden
    olusur (yani duzeltilmesi mumkun olan bir kelime adayi).
  * `tr_diacritics.ESLESME` icinde olan jetonlar **hatadir**: goc
    uygulanmamis demektir. Ayri olarak isaretlenir.
  * Rakam, noktalama, tek harfli kisaltmalar ve kod tanimlayicilari elenir.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

KUTU = Path(__file__).resolve().parent
sys.path.insert(0, str(KUTU))

import tr_diacritics as td  # noqa: E402

DOSYALAR = ("content_a", "content_b", "content_c", "content_d")
#: Jeton siniri Turkce harfleri de icermelidir. Aksi halde "aracin" gibi
#: kelimeler "arac" + "in" diye kirilir ve **zaten duzeltilmis** bir metin
#: "kalan" sanilir. Duz-ASCII sinirla tarama, gocun bittigini kanitlamaz.
JETON_RE = td._KELIME_RE
KORUNAN_RE = re.compile(r"10\.\d{4,9}/\S+|https?://\S+")

#: Kisa, teknik veya Ingilizce oldugu **gözle dogrulanmis** jetonlar.
#: Bunlar Turkce yazim kuralina tabi degildir; listede gormek beklenmez.
INGILIZCE = {
    # kurumsal / yayin / standart
    "pl", "plos", "one", "ieee", "acm", "iso", "who", "un", "nih", "ninds",
    "nature", "science", "sciences", "journal", "reviews", "review", "frontiers",
    "frontiersin", "psychology", "neuroscience", "neurosciences", "neuron",
    "biomedical", "engineering", "technology", "technologies", "quarterly",
    "psychological", "psychiatry", "neurology", "clinical", "physiology",
    "cambridge", "oxford", "university", "press", "mit", "wiley", "springer",
    "elsevier", "taylor", "francis", "annual", "reviews", "proceedings",
    "international", "conference", "workshop", "symposium", "volume", "vol",
    "issue", "pages", "pp", "ed", "eds", "vol", "no", "doi", "url", "isbn",
    # teknik terimler
    "bci", "eeg", "ecog", "meg", "fmri", "mri", "iep", "erp", "emg", "eog",
    "nir", "fnirs", "ssvep", "p300", "n170", "n400", "lrp", "erp", "cvep",
    "ssvec", "saccade", "latency", "amplitud", "frequency", "bandwidth",
    "sampling", "sensor", "sensors", "impedance", "electrode", "electrodes",
    "channel", "channels", "artifact", "artifacts", "artifact", "epoch",
    "epochs", "window", "baseline", "classifier", "classifiers", "dataset",
    "datasets", "feature", "features", "training", "test", "accuracy", "f1",
    "auc", "precision", "recall", "tensor", "tensors", "vector", "vectors",
    "matrix", "matrices", "gradient", "loss", "layer", "layers", "kernel",
    "convolution", "pooling", "dropout", "activation", "softmax", "relu",
    "lstm", "gru", "transformer", "transformers", "attention", "embedding",
    "embeddings", "logit", "softmax", "encoder", "decoder", "latent",
    "supervised", "unsupervised", "reinforcement", "transfer", "self",
    "weakly", "zero", "shot", "few", "domain", "adaptation", "augmentation",
    "synthetic", "recorded", "invasive", "noninvasive", "wearable",
    "portable", "handheld", "real", "time", "online", "offline", "batch",
    "mini", "backpropagation", "optimization", "gradient", "descent",
    "learning", "rate", "scheduler", "epoch", "dropout", "weight", "bias",
    "normalization", "augment", "inception", "resnet", "vgg", "u", "net",
    "interpretation", "explainable", "xai", "latency", "throughput",
    "motor", "imagery", "perception", "cognitive", "neural", "network",
    "networks", "deep", "machine", "learning", "artificial", "intelligence",
    "brain", "computer", "interface", "interfaces", "speller", "spellers",
    "cursor", "keyboard", "screen", "text", "letters", "letter", "word",
    "words", "character", "characters", "symbol", "symbols", "gaze",
    "cursor", "pointing", "selection", "command", "commands", "control",
    "display", "visual", "auditory", "tactile", "feedback", "motor",
    "imagery", "ssvep", "speller", "cued", "spelling", "typing", "gaming",
    "communication", "restoration", "prosthesis", "prostheses", "wheelchair",
    "cursor", "homecare", "home", "care", "rehabilitation", "rehab",
    "lockedin", "als", "stroke", "spinal", "paralysis", "tetraplegia",
    "epilepsy", "seizure", "seizures", "parkinson", "parkinson", "als",
    "diagnostic", "imaging", "tomography", "magnetoencephalography",
    "functional", "anatomy", "anatomical", "cortex", "cortical", "gyrus",
    "hemisphere", "hemispheres", "electrode", "impedance", "position",
    "positions", "coherence", "connectivity", "graph", "graphs",
    "state", "space", "representation", "representations", "token",
    "tokens", "sequence", "sequences", "model", "models", "inference",
    "inferencing", "decoding", "classifier", "classification", "regression",
    "supervised", "learning", "machine", "support", "vector", "machines",
    "naive", "bayes", "hidden", "markov", "monte", "carlo", "expectation",
    "maximization", "principal", "component", "analysis", "linear",
    "discriminant", "logistic", "perceptron", "backpropagation",
    # yabanci oz ad / etiket
    "vidal", "nierenberg", "colleagues", "blankertz", "schafer", "krauledt",
    "middleton", "driscoll", "donchin", "wolpaw", "wolpert", "pfurtscheller",
    "birbaumer", "lotte", "gtec", "nihon", "kohden", "biosemi", "biosig",
    "open", "source", "bci", "illinois", "purdue", "washington", "berlin",
    "graz", "tubingen", "stuttgart", "ghent", "tue", "espoo", "helsinki",
    "utrecht", "nijmegen", "leuven", "delft", "amsterdam", "rotterdam",
    "harvard", "stanford", "yale", "columbia", "cornell", "princeton",
    "caltech", "mit", "cmu", "upenn", "ucla", "ucsd", "usc", "utexas",
    "and", "the", "for", "with", "from", "that", "this", "these", "those",
    "not", "but", "are", "was", "were", "has", "have", "had", "can", "could",
    "may", "might", "will", "would", "shall", "should", "must", "do", "does",
    "did", "been", "being", "such", "than", "then", "when", "where", "which",
    "who", "whom", "whose", "what", "why", "how", "all", "any", "each",
    "both", "few", "more", "most", "other", "some", "only", "own", "same",
    "too", "very", "just", "also", "into", "over", "under", "out", "up",
    "about", "after", "before", "between", "during", "above", "below",
    "again", "further", "once", "here", "there", "why", "while", "because",
    "if", "of", "at", "by", "in", "on", "to", "as", "is", "be", "or", "an",
    "a", "no", "yes",
    # kisisel ad / atif
    "vd", "vs", "etc", "al", "hon", "cihan", "a", "k",
    "oz", "ve", "icin", "ile", "da", "de",
}


def _icerik_dizeleri(yol: Path) -> list[str]:
    """Dosyadaki tum dize sabitlerini dondurur (tokenize ile)."""
    import io
    import tokenize

    out: list[str] = []
    with io.open(yol, "r", encoding="utf-8") as fh:
        for tok in tokenize.generate_tokens(fh.readline):
            if tok.type == tokenize.STRING:
                out.append(tok.string)
    return out


#: Turkce eklerine benzeyen bitisler. Goc sonrasi **kalan** ASCII kelimeler
#: arasinda Turkce olup diakritik bekleyenleri yakalamak icin kullanilir.
#:
#: Neden elle bir "Ingilizce kelimeler" listesi tutulmuyor? Onceki denemede
#: (bkz. eski `check_diacritics.py`) 180 girislik oyle bir liste hataya
#: yol acti: kimlik eslemeleri ve yanlis anlamlar uretiyordu. Burada sozluk
#: yerine **bicimsel bir sinyal** kullanilir; yanlis pozitifler olur ama
#: gozle elenir, yanlis negatif uretmez.
TURKCE_EK = re.compile(
    r"(lar|ler|lari|leri|larin|lerin|nda|nde|dan|den|ta|te|tan|ten"
    r"|ci|cu|si|su|nun|nin|un|in|ile|y|la|le|ki|ce|ca|mi|mu|ya|ye"
    r"|mis|mus|dir|dur|dus|lik|likler|likleri|likta|likci|cilik"
    r"|abilir|iyor|iyorlar|ecek|acak|mal|miş|muş)$"
)

#: Metni **ingilizce** olmasi gereken bloklar.
#:
#: Neden ayri bir denetim gerekiyor? :data:`tr_diacritics.ESLESME` bir *duz*
#: sozluktur; hangi metnin Turkce, hangisinin Ingilizce oldugunu **bilmez**.
#: Turkce `is` -> `iş` eslesmesi bu yuzden Ingilizce ozete de uygulandi ve
#: "The study iş a qualitative ..." gibi bozuk cumleler uretildi. Tablo
#: duzeltmesi jeton duzeyinde calistigi icin bu tur hatalari gormez; ancak
#: blok dili **bilinen** oldugundan, Turkce'ye ozgu bir harf icermemesi
#: gerekli ve denetlenebilir bir ozelliktir.
#:
#: Bicim: ``{modul_adi: (blok_adi, ...)}``. Blok, icerigi string/list
#: icerebilir; ic ice listeler de duz metne acilir.
INGILIZCE_BLOKLAR: dict[str, tuple[str, ...]] = {
    "content_d": ("ABSTRACT_EN",),
}

#: Turkce'ye ozgu buyuk/kucuk harfler.
TURK_HARF_RE = re.compile(r"[ÇĞİÖŞÜçğıöşü]")

#: Yukaridaki bloklarda gerekce gore istisna tutulan jetonlar. Bos olmasi
#: beklenir; bir istisna eklenirse gerekcesiyle birlikte yazilir.
INGILIZCE_ISTISNA: frozenset[str] = frozenset()


def _duz_metin(ogeler: list) -> str:
    """Ic ice listeleri de acarak blok metnini duz bir stringe cevirir."""
    parcalar: list[str] = []

    def gez(obj) -> None:
        if isinstance(obj, str):
            parcalar.append(obj)
        elif isinstance(obj, (list, tuple)):
            for oge in obj:
                gez(oge)
        else:
            parcalar.append(str(obj))

    gez(ogeler)
    return " ".join(parcalar)


def denetle_ingilizce() -> list[str]:
    """Ingilizce olmasi gereken bloklardaki Turkce harfleri raporlar.

    Donus: ``"content_d.ABSTRACT_EN: 'iş'"`` biciminde aciklama satirlari.
    """
    import importlib

    sorunlar: list[str] = []
    for modul_adi, blok_adlari in INGILIZCE_BLOKLAR.items():
        mod = importlib.import_module(modul_adi)
        for blok_adi in blok_adlari:
            metin = _duz_metin(getattr(mod, blok_adi))
            for jeton in sorted(set(JETON_RE.findall(metin))):
                if jeton in INGILIZCE_ISTISNA:
                    continue
                if TURK_HARF_RE.search(jeton):
                    sorunlar.append(f"{modul_adi}.{blok_adi}: {jeton!r}")
    return sorunlar



def main() -> int:
    sayac: Counter[str] = Counter()
    kacirilan: Counter[str] = Counter()
    for ad in DOSYALAR:
        yol = KUTU / f"{ad}.py"
        if not yol.exists():
            continue
        for dize in _icerik_dizeleri(yol):
            temiz = KORUNAN_RE.sub(" ", dize)
            for jeton in JETON_RE.findall(temiz):
                if not jeton.isascii():
                    continue
                sayac[jeton] += 1
                # Gocun yakalayip yakalamadigi: duzelt() bu jetonu degistirir
                # ama metinde degismemis kalirsa, goc bu dosyaya
                # uygulanmamis demektir (KRITIK).
                if td._jeton_duzelt(jeton) != jeton:
                    kacirilan[jeton] += 1

    # -- Blok dili denetimi: Turkce metne Turkce, Ingilizce metne Ingilizce
    #    yazilmalidir. Duz sozluk bunu ayirt edemez; bilesik sozluk de
    #    (ESLESME) her zaman edemez.
    yanlis_dil = denetle_ingilizce()
    if yanlis_dil:
        print("=" * 72)
        print("!! INGILIZCE OLMASI GEREKEN BLOKTA TURKCE HARFI (KRITIK):")
        print("=" * 72)
        for satir in yanlis_dil:
            print(f"   {satir}")

    print("=" * 72)
    print(
        f"KALAN TAM-ASCII JETONLAR: {len(sayac)} farkli / {sum(sayac.values())} adet"
    )
    print("=" * 72)
    if kacirilan:
        print()
        print("!! GOC YAKALAMIS AMA DUZELTMEMIS (KRITIK):")
        for jeton, adet in kacirilan.most_common():
            print(f"   {jeton} ({adet}) -> {td._jeton_duzelt(jeton)}")
    else:
        print("  Gocun yakalamasi gereken hicbir jeton kalmadi.")

    # Turkce eklerine benzeyen kalan jetonlar: gozle elenir.
    supheli = {
        j: a for j, a in sayac.items() if len(j) > 3 and TURKCE_EK.search(j.lower())
    }
    print()
    print("=" * 72)
    print(f"TURKCE EKI TASIYAN KALAN ASCII JETONLAR: {len(supheli)}")
    print("=" * 72)
    for jeton, adet in sorted(supheli.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {jeton} ({adet})")

    # -- TAMAMINI yaz: ek süzgeci delik birakir ("sekli", "kaybi" gibi
    #    bitisler listede yoktur ve gözden kacar). Son denetimde **butun**
    #    liste gozle okunur; suzgec yalnizca ilk taslak icindir.
    tam = Path(__file__).resolve().parent / "_kalan_tam.txt"
    with open(tam, "w", encoding="utf-8", newline="\n") as fh:
        for jeton, adet in sorted(sayac.items(), key=lambda kv: kv[0].lower()):
            fh.write(f"{jeton} ({adet})\n")
    print()
    print(f"Tam liste yazildi: {tam} ({len(sayac)} jeton)")
    return 1 if kacirilan else 0


if __name__ == "__main__":
    raise SystemExit(main())
