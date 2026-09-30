"""workflows/*.md gercekten CLI'yi anlatıyor mu, yoksa kâğıt üstünde mi?

Neden bu test
-------------
`workflows/` altındaki 8 dosya SKILL.md §7'de listelenir ve ajana
"şunu çalıştır" diye verilir. Ama sekizinin de içeriği salt prosedür:
HİÇBİRİ tek bir `thesis:` komutu anmıyor. Yani ajan bu dosyaları okuyup
neyi hangi komutla yazacağını bulamıyor.

Bu, kilitlenmenin BELGESEL nedeni. `research_questions` registry'sini
dolduran komut (`thesis:record`) vardı ama hiçbir akış dosyasında geçmiyordu;
`research_question` kapısının hazırlığı sağlanmadığı için yedi kapılı
akış ilk adımda kilitleniyordu.

Dahası, akışlar var OLMAYAN dosyaları da vaat ediyordu:
`methodology_state.json`, `literature_matrix.md`, `Kaynarca.bib`,
`01_Giris.md`…`06_Sonuc_Oneri.md`, `Kalite_Raporu.md`. CLI'nin ürettiği
tek çıktı `tez_<thesis_id>.{md,docx,pdf}` (export.py:537). Yani akışlar,
ajanın bulamayacağı bir çıktı ağacını tarif ediyordu.

Bu testler dört kural koyar. Hepsi kuraldır, yasak listesi değil — yeni
bir akış dosyası eklendiğinde de aynı ölçüt geçerli olur:

  1. Akışlarda anılan her `thesis:X` komutu skill.yaml'da gerçekten var.
  2. Her akış EN AZ BİR gerçek komut anar (boş kalmak serbest değil).
  3. Akışların atıf yaptığı her dosya gerçekten var (temsilî çıktı adları
     hariç: `<...>` yer tutucular ve `thesis_state.json`).
  4. Yedi kapının adı ve SIRASI `thesis_creation.md` içinde bulunur; akış
     zinciri tek yerden okunabilir olmalı.
  5. Kod bloğundaki her `thesis:approve` çağrısı onaylayan taşır (`--by`);
     yalnız sorgu (`--list`) ve geri alma (`--revoke`) muaftır. Kimliksiz
     onay `onay_ver` tarafından reddedilir, yani bu satırlar çalışmaz.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_YAML = REPO_ROOT / ".opencode" / "skills" / "academic-thesis-writer" / "skill.yaml"
WORKFLOW_DIZIN = REPO_ROOT / "workflows"
ANA_AKIS = WORKFLOW_DIZIN / "thesis_creation.md"

# `thesis:record research_questions` gibi bir yazım.
_KOMUT_DESEN = re.compile(r"\bthesis:([a-z][a-z-]*)")

# Bir dosya yolu gibi görünen şey: dizin/veya noktasuz dosya adı.
_DOSYA_DESEN = re.compile(
    r"(?<![\w/.-])"
    r"((?:[\w-]+/)*[\w-]+\.(?:json|md|bib|docx|pdf|yaml|yml))"
    r"(?![\w-])"
)

# Akışların atıf yapabildiği kök dizinler. SKILL.md §7 ve §10 bu
# yolların depo köküne göre yazıldığını söylüyor.
_KOK_DIZINLER = ("schemas", "references", "templates", "workflows", "agents")

# Gerçekten var olmayan ve var OLMAYACAK dosyalar: CLI bunları üretmez.
# Temsili adlar (köşeli parantez, `<...>`) kural dışıdır.
_TEMSILI = re.compile(r"[\[\]<>{}]")

def _skill() -> dict:
    return yaml.safe_load(SKILL_YAML.read_text(encoding="utf-8"))


def _gercek_komutlar() -> set[str]:
    return {k["name"].split(":", 1)[1] for k in _skill()["commands"] if ":" in k["name"]}


def _akis_dosyalari() -> list[Path]:
    dosyalar = sorted(WORKFLOW_DIZIN.glob("*.md"))
    assert dosyalar, f"{WORKFLOW_DIZIN} altında akış dosyası yok"
    return dosyalar


@pytest.fixture(scope="module")
def akislar() -> dict[str, str]:
    return {f.name: f.read_text(encoding="utf-8") for f in _akis_dosyalari()}


# --- 1. anilan komutlar gercek mi --------------------------------------------


def test_akislarda_anilan_komutlar_gercek(akislar: dict[str, str]) -> None:
    """Akışlarda geçen her `thesis:X`, skill.yaml'da ilan edilmiş olmalı."""
    gercek = _gercek_komutlar()
    hayalet: list[str] = []
    for ad, metin in akislar.items():
        for komut in _KOMUT_DESEN.findall(metin):
            if komut not in gercek:
                hayalet.append(f"{ad}: thesis:{komut}")
    assert not hayalet, (
        "Akışlar CLI'da olmayan komutları anıyor:\n  " + "\n  ".join(sorted(hayalet))
    )


# --- 2. her akis en az bir komut anyor mu ------------------------------------


def test_her_akis_en_az_bir_gercek_komut_aniyor(akislar: dict[str, str]) -> None:
    """Sekiz akışın hiçbiri tek bir komut anmıyordu; ajana ne yapacağını söylemiyordu."""
    gercek = _gercek_komutlar()
    susuz = [
        ad
        for ad, metin in akislar.items()
        if not (_KOMUT_DESEN.findall(metin) and set(_KOMUT_DESEN.findall(metin)) & gercek)
    ]
    assert not susuz, (
        "Hiçbir gerçek komut anmayan akışlar: " + ", ".join(susuz)
        + "\n  Her akış, verdiği adımın HANGİ komutla yapılacağını söylemelidir."
    )


# --- 3. atif yapilan dosyalar gercek mi --------------------------------------


def test_akislar_var_olmayan_dosya_adi_adreslemez(akislar: dict[str, str]) -> None:
    """`methodology_state.json`, `Kaynarca.bib`, `01_Giris.md` … hiçbir zaman yok.

    Kural: akışın atıf yaptığı her dosya gerçekten var olmalıdır.

    İki istisna:

    * **Temsili ad** — `<BULGULAR.json>`, `[X]`, `tez_<id>.md`. Köşeli
      parantezin İÇİNDEKİ yol bir taslaktır, dosya değil; ajanın dolduracağı
      bir girdidir ve depoda durmasının sebebi yoktur. `_DOSYA_DESEN` köşeli
      parantezi yakalamadığı için kontrol, eşleşmenin **çevresindeki
      karakterlere** bakılır. (Bu ilk yazımda kontrol yakalanan yolun
      kendisine bakıyordu ve `<BULGULAR.json>` içindeki 11 yeri yanlışlıkla
      gerçek çıktı sayıyordu.)
    * **Tez verisinin kendisi** — `thesis_state.json`, izlenmeyen kullanıcı
      verisi; `thesis:new` üretir.

    Bir çıktı ağacı vaat eden akış (`01_Giris.md`, `methodology_state.json`,
    `Kaynarca.bib`) köşeli parantez kullanmaz, bu yüzden yakalanmaya devam eder.
    """
    hayalet: list[str] = []
    for ad, metin in akislar.items():
        for eslesme in _DOSYA_DESEN.finditer(metin):
            yol = eslesme.group(1)
            cevre = metin[eslesme.start() - 1:eslesme.end() + 1]
            if _TEMSILI.search(cevre) or yol == "thesis_state.json":
                continue
            adaylar = [REPO_ROOT / yol]
            if "/" not in yol:
                adaylar += [REPO_ROOT / d / yol for d in _KOK_DIZINLER]
            if not any(a.exists() for a in adaylar):
                hayalet.append(f"{ad}: {yol}")
    assert not hayalet, (
        "Akışlar CLI'nin üretmediği dosyaları vaat ediyor:\n  "
        + "\n  ".join(sorted(set(hayalet)))
        + "\n  export.py:537 tek çıktıyı üretir: tez_<thesis_id>.{md,docx,pdf}"
    )


# --- 4. kapi zinciri tek yerde okunabiliyor mu -------------------------------


def test_ana_akis_yedi_kapiyi_sirasiyla_belgiler() -> None:
    """Ajan akışı tek yerden öğrenebilmeli: kapı adları + sıra."""
    from tools.atw.state import APPROVAL_GATES

    assert ANA_AKIS.exists(), f"{ANA_AKIS} yok — SKILL.md §7 listeliyor"
    metin = ANA_AKIS.read_text(encoding="utf-8")

    konumlar: list[int] = []
    for kapi in APPROVAL_GATES:
        i = metin.find(f"`{kapi}`")
        assert i != -1, (
            f"thesis_creation.md '{kapi}' kapısını anmıyor. Ajan yedi kapılı "
            f"akışın sırasını buradan öğrenemez."
        )
        konumlar.append(i)

    assert konumlar == sorted(konumlar), (
        "Kapılar yanlış sırada listelenmiş. Akış sırası şu: "
        + " -> ".join(APPROVAL_GATES)
    )


# --- 5. akislardaki onay cagrilari kimlik tasiyor mu ----------------------


def _kod_bloklari(metin: str) -> list[tuple[int, str]]:
    """Markdown kod bloklarindaki satirlari `(satir_no, metin)` dondurur.

    Kapali uc backtick isaretleri arasini alir. Blok DILI (bash/sh/
    console) ayrimi yapilmaz: bu testin konusu dil degil
    kopyalanabilirlik.
    """
    kapali = False
    cikti: list[tuple[int, str]] = []
    for n, satir in enumerate(metin.splitlines(), 1):
        if satir.lstrip().startswith("```"):
            kapali = not kapali
            continue
        if kapali:
            cikti.append((n, satir))
    return cikti


#: `--by` istemeyen alt komutlar ve muafiyet gerekceleri. Gerekce
#: sozlesmesi degil, kararin GEREKCESIDIR: yarin kapiyi kapatma
#: yonu degisse muafiyet de birlikte dusunmelidir.
KIMLIK_ISTEMEYENLER: dict[str, str] = {
    "--list": "sorgudur, karar degildir, durumu degistirmez",
    "--revoke": "kapiyi KAPATIR; geri alma muafiyeti bilincli (bkz. onay_geri_al)",
}

#: `--by` istemeyen alt komutlar ve muafiyet gerekceleri. Gerekce
#: sozlesmesi degil, kararin GEREKCESIDIR: yarin kapiyi kapatma
#: yonu degisse muafiyet de birlikte dusunmelidir.
KIMLIK_ISTEMEYENLER: dict[str, str] = {
    "--list": "sorgudur, karar degildir, durumu degistirmez",
    "--revoke": "kapiyi KAPATIR; geri alma muafiyeti bilincli (bkz. onay_geri_al)",
}

#: Kabuk AYIRACLARI. Acik bir `thesis:approve a && thesis:approve b`
#: yaziminda ikinci cagrinin `--by` degeri birincisine TASMAMALIDIR;
#: bu yuzden belirtecler ilk ayiracida kesilir.
_KABUK_AYIRACI = frozenset({"&&", "||", ";", "|", "&"})

#: Ayristiricinin basladigi yer. Duz kelime degil, kapi adinin basinda
#: biten bir `thesis:approve` gecerlilik sinifidir; `thesis:approvex`
#: eslesmez. Yorum satirinda (`#` ile baslayan) `_cagrilari` icinde
#: elenir.
_CAGRI_BASI = re.compile(r"thesis:approve(?=\s|$)")


def _ayikla(satir: str) -> list[tuple[str, bool]]:
    """Satiri `(deger, tirnakli_mi)` ciftlerine boler.

    Neden `shlex.split` DEGIL: shlex tirnagi SILER, boylece
    `--comment "--by"` ile `--by "x"` ayni belirteclere duser. Bu
    kuralin butun varlik sebebi kimligi baska bir bayragin degerinin
    icine gizlemektir; ayristirici tirnagin var oldugunu BILMELIDIR.
    Ikinci neden: shlex'in yorum kesme (`#`) bir degeri de keser
    (`--by "Dr. #1"`).

    Tirnak disinda kalan bir `#` yorumu baslatir ve satirin kalanini
    komut saymaz. Tirkaclar kapatilmamissa satir sonuna kadar devam
    edilir: yarim kalmis bir ornek sessizce gecmeye devam etsin
    istemiyoruz, cagiran taraf zaten ayristirmada hata alacak.
    """
    cikti: list[tuple[str, bool]] = []
    tampon: list[str] = []
    tirnak: str | None = None
    tirnakli = False

    def kapat() -> None:
        nonlocal tampon, tirnakli
        if tampon or tirnakli:
            cikti.append(("".join(tampon), tirnakli))
        tampon = []
        tirnakli = False

    for karakter in satir:
        if tirnak is not None:
            if karakter == tirnak:
                tirnak = None
            else:
                tampon.append(karakter)
            continue
        if karakter in "\"'":
            tirnak = karakter
            tirnakli = True
            continue
        if karakter == "#" and not tampon:
            break
        if karakter.isspace():
            kapat()
            continue
        # `=` tirnak disinda bir ayiracdir: `--by=deger` -> `--by`, `deger`
        if karakter == "=":
            kapat()
            continue
        tampon.append(karakter)
    kapat()
    return cikti


def _bayrak_degeri(
    belirtecler: list[tuple[str, bool]], ad: str
) -> str | None:
    """`ad` bayraginin DEGERINI doner; yoksa/boşsa None.

    TIRNAKLI bir belirtec ASLA bayrak sayilmaz. `--comment "--by"`
    yaziminda `--by` bir degerdir; onu bayrak saymak, kurali sessizce
    atlatmanin en kolay yoluydu.

    `--by=value` soz dizimi de desteklenir (shlex bunu tek belirtec
    yapar; bu ayristirici ayri boslukla yazimi destekler).
    """
    for i, (deger, tirnakli) in enumerate(belirtecler):
        # Normal: `--by "deger"` -> iki ayri belirtec
        if deger == ad and not tirnakli:
            if i + 1 >= len(belirtecler):
                return None
            sonraki_deger, sonraki_tirnakli = belirtecler[i + 1]
            if sonraki_deger == ad and not sonraki_tirnakli:
                return None                 # `--by --by`: deger verilmemis
            return sonraki_deger
        # Eslesik: `--by="deger"` veya `--by=deger` -> tek belirtec
        if not tirnakli and deger.startswith(ad + "="):
            return deger[len(ad) + 1 :]
    return None


def _karar_mi(belirtecler: list[tuple[str, bool]]) -> bool:
    """Bu cagri bir KARAR mi, yoksa sorgu/geri alma mi?

    Kapi adi, `--` ile baslamayan ve tirnakli OLMAYAN ilk belirtecidir.
    `thesis:approve --list` gibi yalniz bayrakli bir cagrida kapi
    yoktur: bu bir sorgudur, durumu degistirmez.
    """
    for deger, tirnakli in belirtecler:
        if tirnakli or deger.startswith("-"):
            continue
        if deger in _KABUK_AYIRACI:
            return False
        return True
    return False


def _cagrilari(satir: str) -> list[list[tuple[str, bool]]]:
    """Bu satirdaki HER `thesis:approve` cagrisinin belirteclerini doner.

    Satir basina birden fazla cagri desteklenir (`a && b`). Her cagri
    kendi ayiracinda KESILIR, boylece bir cagrinin `--by` degeri
    digerine tasmaz.
    """
    cagrilar: list[list[tuple[str, bool]]] = []
    for es in _CAGRI_BASI.finditer(satir):
        govde = _ayikla(satir[es.end():])
        kesilmis: list[tuple[str, bool]] = []
        for belirtec in govde:
            deger, tirnakli = belirtec
            if not tirnakli and deger in _KABUK_AYIRACI:
                break
            kesilmis.append(belirtec)
        cagrilar.append(kesilmis)
    return cagrilar


def _kimliksiz_cagrilar(ad: str, metin: str) -> list[str]:
    """Bu akista kimliksiz onay KARARLARINI `dosya:satir: metin` doner.

    `akislar` fixture'i dosyayi ZATEN okunmus halde verir; ikinci kez
    okumak ayni dosyanin iki farkli surumunu denetlemek anlamina
    gelirdi. Bu yuzden burada yalniz metin uzerinde calisilir.
    """
    bulunan: list[str] = []
    for n, satir in _kod_bloklari(metin):
        # Yorum satırını atla (bazında boşluk ile başlayabilir)
        if satir.lstrip().startswith("#"):
            continue
        for belirtecler in _cagrilari(satir):
            if not _karar_mi(belirtecler):
                continue
            if any(
                not tirnakli and deger in KIMLIK_ISTEMEYENLER
                for deger, tirnakli in belirtecler
            ):
                continue
            deger = _bayrak_degeri(belirtecler, "--by")
            if deger is not None and deger.strip():
                continue
            bulunan.append("%s:%d: %s" % (ad, n, satir.strip()))
            break                       # satir basina tek kayit yeter
    return bulunan


def test_akislarda_onay_cagrisi_kimlik_tasiyor(akislar: dict[str, str]) -> None:
    """Kopyalanabilir her `thesis:approve` KARARI kimlik tasimalidir.

    Bu olmadan `onay_ver`in zorlamasi kullaniciya ilk hatayi CALISTIRMA
    aninda gosterir: akis dokumani calistirilamaz hale gelir ve hata
    "belge hatasi" degil "yazilim hatasi" gibi gorunur.
    """
    supheli: list[str] = []
    for ad, metin in akislar.items():
        supheli.extend(_kimliksiz_cagrilar(ad, metin))

    assert not supheli, (
        "Kod blogunda bos `--by` vermeyen onay cagrisi var. `onay_ver` "
        "onaylayan zorunlu kiliyor; bu satirlar calistirildiginda hata "
        "verir:\n  " + "\n  ".join(supheli)
    )
    assert akislar, "akislar fixture'i bos — tarama anlamsizlasir"


def test_denetleyici_ornekleri() -> None:
    """Kâhin tablosu: dedetleyici EL YAZIMI beklenisler karsilastirir.

    Neden ayri bir test gerekiyor
    -----------------------------
`test_akis_taramasi_bos_cikmaz` bir ALT DIZE ile olcuyordu; bu
    ASIMETRIK bir korumadir (ayristirici bozulursa yakalamaz, blok
    ayiklayici bozulursa yakalar). Uzerine "alt dize sayisi = cagri
    sayisi" nöbetçisi kurulamaz: olculdu, **14 != 13** — fark `--list`
    sorgusu, ki meşru olarak atlanir. Boyle bir nöbetci calisan kurali
    kirmiziya dusururdu.

    Buradaki beklenisler LITERAL'dir; dedetleyiciden hesaplanmaz. Bu
    yuzden ayristirici ayni yonde bozulsa bile kirmizi olur. Her
    satir `(girdi, kimliksiz_sayisi)` ciftidir: 1 = yakalanmali,
    0 = gecmeli.
    """
    ORNEKLER: list[tuple[str, int]] = [
        # --- kimliksiz KARAR: yakalanmali --------------------------------
        ("thesis:approve findings", 1),
        ("thesis:approve research_question", 1),
        ('thesis:approve findings --comment "iyi"', 1),
        ('thesis:approve findings --reject --reason "eksik"', 1),
        # --- BOS deger de kimlik degildir (B7) ---------------------------
        ('thesis:approve findings --by ""', 1),
        ("thesis:approve findings --by ''", 1),
        ('thesis:approve findings --by "   "', 1),
        # --- tirlakli `--by` bir DEGERDIR, bayrak degil (B3) ------------
        ('thesis:approve findings --comment "--by"', 1),
        ('thesis:approve findings --reason "a && --by b"', 1),
        # --- kimlikli: gecmeli ------------------------------------------
        ('thesis:approve findings --by "Dr. Danışman Adı"', 0),
        ('thesis:approve findings --by="Dr. A"', 0),
        ('thesis:approve findings --comment "x" --by "Dr. A"', 0),
        # --- muafiyetler -------------------------------------------------
        ("thesis:approve --list", 0),
        ("thesis:approve --list      # kapinin durumunu ogren", 0),
        ("thesis:approve findings --revoke", 0),
        ('thesis:approve findings --revoke --by "Dr. A"', 0),
        # --- zincirleme: ikinci cagrinin --by degeri birinciye TASMAMALI
        ('thesis:approve a && thesis:approve b --by "Dr. A"', 1),
        ('thesis:approve a --by "Dr. A" && thesis:approve b', 1),
        # --- ilgisiz yuzeyler: gecmeli -----------------------------------
        ("thesis:record research_questions", 0),
        ("thesis:approvex findings --by", 0),
        ("# thesis:approve findings", 0),
        ('thesis:approve findings --by "Dr. #1"', 0),
    ]
    kacar = [
        "%-52s -> %d (beklenen %d)" % (girdi, len(_kimliksiz_cagrilar("x", f"```\n{girdi}\n```")), beklenen)
        for girdi, beklenen in ORNEKLER
        if len(_kimliksiz_cagrilar("x", f"```\n{girdi}\n```")) != beklenen
    ]
    assert not kacar, "dedetleyici beklenenden sapti:\n  " + "\n  ".join(kacar)


def test_kimlik_istemeyen_bayraklar_hazir() -> None:
    """Muafiyetler ve `--by` GERCEKTEN parser'da tanimli olmalidir.

    `KIMLIK_ISTEMEYENLER` bir istisna listesi; liste yanlislikla
    genislerse sessizce gercek bir acik yolu kapatir. `--by` ise
    listenin disinda ama kuralin dayandigi anahtardir: yeniden
    adlandirilirsa dedetleyici hicbir seyi bulmaz ve tum akislar
    sessizce denetimsiz kalir. Ikisi de parser'a baglanir — yani
    muafiyet, kodu okuyanin sandigi sey degil, AYRISTIRICININ
    bildirdigi seydir.
    """
    from tools.atw.cli.main import build_parser

    alt = None
    for aksiyon in build_parser()._actions:
        secenekler = getattr(aksiyon, "choices", None)
        if isinstance(secenekler, dict) and "approve" in secenekler:
            alt = secenekler["approve"]
            break
    assert alt is not None, "build_parser() 'approve' alt komutunu uretmiyor"

    bilinen: set[str] = set()
    for aksiyon in alt._actions:
        bilinen.update(aksiyon.option_strings)

    yabanci = sorted(set(KIMLIK_ISTEMEYENLER) - bilinen)
    assert not yabanci, (
        f"KIMLIK_ISTEMEYENLER'de parser'da tanimli olmayan bayrak: {yabanci}. "
        f"approve alt komutunda bulunanlar: {sorted(bilinen)}"
    )
    assert "--by" in bilinen, (
        "`--by` artik approve alt komutunda degil. Bu kuralin dayandigi "
        "anahtar budur; ad degistiyse `_bayrak_degeri` de guncellenmeli."
    )


def test_akis_taramasi_bos_cikmaz(akislar: dict[str, str]) -> None:
    """Kontrol: tarama BOS KALMIYOR (kapsam olcumu).

    Yukaridaki kural, hicbir akis dosyasi kod blogu icermeseydi de
    yesil kalirdi: bos tarama hatasizdir. Bu test DENETLEYICININ
    KENDI cikti sayisini olcer — en az bir akis dosyasinda bir
    `thesis:approve` cagrisi taninmali.

    Alt dize degil, dedetleyici olculur: boylece bu nöbetci de
    ayristiriciyla ayni yonde sessizlesmez. Iki testin isi FARKLIDIR:
    `test_denetleyici_ornekleri` "dedetleyici dogru mu" diye sorar
    (elle yazilmis beklenislerle), bu test "kapsam var mi" diye.
    """
    gecen = [
        ad
        for ad, metin in akislar.items()
        if any(_cagrilari(satir) for _, satir in _kod_bloklari(metin))
    ]
    assert gecen, (
        "Hicbir akis dosyasinda kod blogu icinde `thesis:approve` cagrisi "
        "TANINMADI. `test_akislarda_onay_cagrisi_kimlik_tasiyor` bos liste "
        "uzerinde yesil kalir ve gercek bir belge ihlalini yakalayamaz. "
        "Once `test_denetleyici_ornekleri`yi calistirin: ayristirici mi "
        "koptu, kapsam mi kayboldu?"
    )
