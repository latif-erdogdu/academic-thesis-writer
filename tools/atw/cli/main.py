#!/usr/bin/env python3
"""CLI komutları: thesis:new, thesis:search, thesis:verify, thesis:extract, thesis:write, thesis:audit, thesis:status, thesis:export."""
from __future__ import annotations

import argparse
import functools
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from tools.atw.audit import UYARILACAK_TURLER, denetim_kimligi_ata, tum_denetimler
from tools.atw.state import empty_state, validate_state


# Skill'in kurulu oldugu depo (semalar, sablonlar).
#
# DIKKAT: burasi VERI yolu olarak KULLANILMAZ. Semalar
# tools.atw.state.SCHEMA_DIR'den gelir. Bu sabit bir surecler boyunca
# tes durumu dosyasi icin kullaniliyordu ve CLI hangi dizinden
# calistirilirsa calistirilsin hep skill'in deposuna yaziyordu; yani
# `thesis:new` skill'in git deposunu kirlettiriyordu. Bkz. veri_koku().
REPO_ROOT = Path(__file__).resolve().parents[3]  # tools/atw/cli -> repo root

DURUM_DOSYASI = "thesis_state.json"

# Veri koku. None ise calisma dizini (varsayilan). Testler bu degere
# yazmak sureci gecici bir dizine baglar; ileride `--state` ile de
# ayrilabilir.
VERI_KOKU: Path | None = None


def _cikti_kodlamasini_ayarla(stdout=None, stderr=None) -> None:
    """Çıktı akışlarını UTF-8'e çevirir; dar kodlamada glif kaybını önler.

    Neden var
    ---------
    Windows'ta `sys.stdout.encoding` konsol kod sayfasıdır ve Türkçe
    kurulumda cp1254'tür. CLI'in kullandığı durum gliflerinin (✅ U+2705,
    ❌ U+274C, ✗ U+2717, ⚠ U+26A0) hiçbiri cp1254'te yoktur. Bu yüzden
    `thesis:new` bile `print` aşamasında `UnicodeEncodeError` fırlatıyor,
    süreç 1 ile çıkıyordu — durum dosyası yazılmış olsa bile. `approve`
    ise durumu başarıyla yazıp sonra aynı hatayla "başarısız" görünüyordu.
    `PYTHONIOENCODING=utf-8` ile hepsi sorunsuz çalışıyor. Yani araç, tam
    olarak hedeflediği ortamda (Türkçe Windows) varsayılan ayarlarla
    kullanılamaz durumdaydı.

    Neden `errors="replace"`
    ----------------------
    UTF-8'e çevirmek tek başına yeterli değil: `stdout` bir dosyaya ya da
    başka bir akışa yönlendirilmişse, o akışın kodlaması başka bir şey
    olabilir ve glif yine de kaybolabilir. `replace` ile yazma hiçbir
    koşulda patlamaz; glif yerine `?` düşer. Bir CLI'nin kullanıcıyı
    kilitlemesine kıyasla `?` kabul edilebilir bir kayıptır.

    Neden sessizce yutuyor
    ---------------------
    Bu, çıktı tarafında bir konfor ayarıdır. Yeniden yapılandırma
    desteklenmeyen ya da hata fırlatan bir akışta **istisna atmaz** —
    atsaydı, düzeltilen kusurun aynısı oluşurdu: komut hiç çalışmazdı.
    """
    for akis in (stdout if stdout is not None else sys.stdout,
                 stderr if stderr is not None else sys.stderr):
        if akis is None:
            continue
        kodlama = (getattr(akis, "encoding", "") or "").lower().replace("-", "")
        if kodlama in ("utf8", ""):
            continue
        yeniden = getattr(akis, "reconfigure", None)
        if yeniden is None:
            continue
        try:
            yeniden(encoding="utf-8", errors="replace")
        except (ValueError, OSError, LookupError):
            # Akış yapılandırılamıyorsa çıktı kodlaması neyse onunla devam et.
            pass


def veri_koku() -> Path:
    """Tez verisinin bulunacagi dizin: varsayilan calisma dizini.

    Neden calisma dizini: CLI, kullanicinin tez dizininde calisir. Skill'in
    kuruldugu depo kullanilsaydi iki sonuc olusurdu:

      1. `thesis:new` skill'in git deposunu kirletirdi.
      2. `thesis_state.json` izlenen bir dosya OLMADIGI icin (dogru bir
         karar: kullanici verisi kaynak deposuna karismamali) skill'i
         guncellediginizde tez verisi hicbir yerden kurtarilamazdi.

    Yol modul yuklenirken degil, CAGRIDA cozulur; boylece `os.chdir`
    calisma aninda yapildiginda da dogru yere bakilir.
    """
    return VERI_KOKU if VERI_KOKU is not None else Path.cwd()


def durum_yolu() -> Path:
    """thesis_state.json dosyasinin tam yolu."""
    return veri_koku() / DURUM_DOSYASI


def _cozumle(yol: str) -> Path:
    """Nispi yollari veri kokune gore cozumler; mutlak yollara dokunmaz."""
    aday = Path(yol)
    return aday if aday.is_absolute() else veri_koku() / aday


def _secili_dosya(deger: str | None) -> str | None:
    """`--file` degerini yola uygun hale getirir; yoksa `None` doner.

    Skill.yaml'daki handler sablonu (`write {args[0]} --rq {options.rq}
    --file {options.file}`) secenek verilmediginde ne yaptigini bu depo
    belgelemiyor; ayni kalip `thesis:verify --all {options.all}` ve
    `thesis:extract --pdf {options.pdf}` icinde de var. Uc olasilik da
    bu komut icin elde tutuluyor:

      * bos dize  -> `None` (brifing kipi)
      * bayrak    -> `None` (brifing kipi)
      * `{options.file}` gibi COZULMEMIS sablon -> `None` (brifing kipi)

    Ucuncu durum sessizce gecilmez: cozulmemis `{...}` bir yol DEGILDIR,
    onu dosya adi sanmak "Bölüm dosyası bulunamadı: {options.file}"
    demektir. Yok saymak, kullanicinin yazmak istemedigi bir ikinci
    kipi calistirmaktir.
    """
    if not deger or "{" in deger:
        return None
    return deger

# Cikis kodlari. Ucuncu ayri bir kod, cunku "calistim ve sorun buldum" ile
# "hic baslayamadim" ayni sey degildir.
CIKIS_OK = 0
CIKIS_SORUN = 1
CIKIS_BASLAMADI = 2


class TezYok(FileNotFoundError):
    """thesis_state.json hic olusmamis: tez baslatilmamis.

    ``FileNotFoundError`` alt sinifi: bu hatayi yakalamak isteyen JENERIK
    kodun (ornegin bir arac zincirinin hata ayiklayicisi) degismemesi icin.
    """


class BozukTezDurumu(ValueError):
    """thesis_state.json var ama okunamıyor: JSON bozuk ya da duzey degil.

    ``TezYok`` ile AYRI tutulur cunku kullaniciya verilecek tavsiye tam
    tersidir:

      TezYok           -> "thesis:new calistir"        (veri kaybi yok)
      BozukTezDurumu   -> "dosyayi ONAR, thesis:new CALISTIRMA" (veri silinir)

    Ikisi birlestirilseydi, bozuk dosyasi olan bir kullaniciya verisini
    silen bir komut onerilirdi.
    """


def load_state() -> dict:
    """thesis_state.json yukler.

    Dosya yoksa ``TezYok``, okunamıyorsa ``BozukTezDurumu`` firlatir.

    Daha once dosya yoksa ``empty_state(...)`` donduruyordu. Bu, "tez var
    ama 0 kaynak" ile "tez dosyasi hic yok" durumlarini ayirt edilemez
    hale getiriyordu; `cmd_audit` bu hayali durumu diske de yaziyordu.
    """
    state_file = durum_yolu()
    if not state_file.exists():
        raise TezYok(
            f"thesis_state.json bulunamadı: {state_file}. "
            f'Henüz tez başlatılmamış. Başlatmak için: thesis:new <ID> "<Başlık>"'
        )
    try:
        durum = json.loads(state_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as hata:
        raise BozukTezDurumu(
            f"thesis_state.json bozuk ({state_file}): {hata}. "
            f"Dosyadaki veri kurtarılabilir — silmeyin."
        ) from hata
    if not isinstance(durum, dict):
        raise BozukTezDurumu(
            f"thesis_state.json beklenen biçimde değil ({state_file}): "
            f"nesne yerine {type(durum).__name__} bulundu."
        )
    return durum


def _durum_gerekir(fn):
    """Durum dosyası gerektiren komutları sarmalar.

    Sarmalayıcı, gövde çalışmadan ÖNCE durumu yükler. Böylece hem
    dosya yoksa erken çıkılır (gereksiz iş yapılmaz, `cmd_search`'in
    pahalı içe aktarmaları dahil), hem de dosya yokken hiçbir komut
    `thesis_state.json` YAZAMAZ.
    """

    @functools.wraps(fn)
    def sarmalayici(args):
        try:
            durum = load_state()
        except TezYok as hata:
            print(f"❌ {hata}")
            return CIKIS_BASLAMADI
        except BozukTezDurumu as hata:
            print(f"❌ {hata}")
            print("   ⚠️  Dosyayı elle onarın veya yedekten geri yükleyin.")
            return CIKIS_BASLAMADI
        return fn(args, durum)

    return sarmalayici


def save_state(state: dict) -> None:
    """thesis_state.json kaydet — DOĞRULAMAYLA.

    Bu fonksiyon düz `write_text` ile yazıyordu. `tools/atw/state.py`
    içindeki eş adlı fonksiyon ise `validate_state` çağırıp hatalı
    durumda `ValueError` fırlatıyor. Aynı ada sahip iki farklı
    davranış, hatanın hangi yoldan geldiğini gizliyordu: kütüphane
    yolu reddediyor, CLI sessizce yazıyordu.

    Ölçülen sonuç: `thesis:search` üç kez çalıştıktan sonra gerçek
    tez durumu 312 şema hatası taşıyordu ve kimse bunu görmemişti.
    Arama katmanı `journal`/`volume`/`issue`/`pages` için `None`,
    `access_date` ve `verified_at` için `""` yazıyordu; `search_run`
    kayıtları da dört ayrı ihlal içeriyordu.

    Doğrulama BAŞARISIZ olursa hiçbir dosya yazılmaz. Kısmi yazım,
    sonraki koşuda okunamayan bir durum bırakır ve bu durumu üreten
    komutun çıktısındaki hata mesajı yanıltıcı olur.
    """
    hatalar = validate_state(state)
    if hatalar:
        detay = "; ".join(hatalar[:5])
        raise ValueError(
            f"Durum semaya uymuyor ({len(hatalar)} hata), dosyaya yazılmadı: {detay}"
        )
    state_file = durum_yolu()
    state["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    state["version"] = state.get("version", 0) + 1
    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_new(args) -> int:
    """Yeni tez başlat.

    Var olan bir tez durumu ÜZERİNE YAZILMAZ. `save_state` düz `write_text`
    ile yazdığı için, eski davranışta `thesis:new` mevcut tezi sessizce
    eziyordu: kaynaklar, iddialar, atıflar ve onay kayıtları kalıcı olarak
    gidiyordu. `thesis_state.json` izlenen bir dosya olmadığından geri alma
    yolu da yoktu.

    Ezmeyi kast eden kullanıcı `--force` verir; o zaman kayıp bilinçlidir.
    Bozuk dosya da ezilmez: bozukluğu gidermek veriyi silmekten iyidir.
    """
    state_file = durum_yolu()
    if state_file.exists() and not getattr(args, "force", False):
        print(f"❌ Mevcut tez durumu bulundu, üzerine yazılmadı: {state_file}")
        try:
            mevcut = json.loads(state_file.read_text(encoding="utf-8"))
            print(f"   Mevcut tez: {mevcut.get('thesis_id', '?')} — {mevcut.get('title', '?')}")
            print(f"   Kaynak sayısı: {len(mevcut.get('sources', []))}")
        except json.JSONDecodeError:
            print("   Dosya bozuk görünüyor. Bozukluğu gidermek için dosyayı elle incele;")
            print("   thesis:new çalıştırmak veriyi siler.")
        print("   Yine de sıfırlamak istiyorsan: --force")
        return 1

    state = empty_state(args.id, args.title)
    save_state(state)
    print(f"✅ Yeni tez oluşturuldu: {args.id} — {args.title}")
    print(f"📄 thesis_state.json güncellendi")
    return 0


@_durum_gerekir
def cmd_search(args, durum) -> int:
    """Kaynak arama başlat.

    Boş PICO reddi
    --------------
    Bu komut bilinmeyen RQ'yu bir uyarıyla geçiyordu: "boş PICO ile devam
    ediliyor". Bu bir uyarı değil, bir kirlilik kaynağıydı — boş PICO
    Crossref/OpenAlex/PubMed'e genel bir sorgu gönderir ve sonuçları
    `sources`'a yazar. Yani "RQ-001" yerine "RQ-01" yazan kullanıcı,
    "100 kaynak buldum" sanarken tezin kaynak kütüphanesine alakasız
    kaynakları doldurur. Ölçüldü: 100 kaynak.

    Artık arama iki koşulla başlar:

      * `--pico` verilmişse metin doğrudan kullanılır (ön tarama).
      * `--rq` verilmişse RQ `research_questions` içinde BULUNMALI ve
        metni en az bir PICO bileşeni üretmeli.

    Boş PICO'nun reddi ayrı bir ölçüt: `PICO()` bir dataclass olduğu için
    her zaman doğrudur; gerçek boşluk `PICO.non_empty()` ile anılır.
    Kayıtlı ama içeriği olmayan bir RQ, kaydı bulmakla arama yapmak
    arasındaki farkı kapatmaz.
    """
    from tools.source_search import run_systematic_search, parse_pico

    pico, hata = _aramaya_pico(args, durum)
    if hata:
        print(hata)
        return CIKIS_SORUN

    veritabanlari = [db.strip() for db in (args.databases or "").split(",") if db.strip()]
    if not veritabanlari:
        print("❌ --databases boş olamaz (örn: --databases crossref,openalex)")
        return CIKIS_SORUN

    result = run_systematic_search(
        pico=pico,
        databases=veritabanlari,
        year_from=args.year_from,
        year_to=args.year_to,
        max_results_per_db=args.max_results,
    )

    print(f"\n✅ Arama tamamlandı: {result.search_run_id}")
    if args.rq:
        # Hangi sorunun arandığı çıktıda görünmeli: `search_runs` kaydı
        # `rq`'yu taşımıyor, sonraki bir denetimde hangi aramanın
        # hangisine ait olduğu anlaşılamıyor.
        print(f"   Soru: {args.rq}")
    print(f"   Kayıtlar: {result.prisma_flow['records_identified']}")
    print(f"   Kopya kaldırıldı: {result.deduplication.stats['removed']}")
    print(f"   Dahil edilen: {len(result.included_source_ids)}")

    # State'e kaydet. `result.to_dict()` burada KULLANILMAZ: o yalnızca
    # İLK veritabanının kaydını döndürür — iki veritabanlı bir koşuda
    # ikinci veritabanının kaydı sessizce kaybolur (ölçüldü: 3 arama ->
    # 3 kayıt, üçü de crossref). `to_state_records()` veritabanı başına
    # kayıt üretir ve `included_source_ids`'i doldurur; `included_records`
    # ise TEKİLLEŞTİRİLMİŞ, kimlikli kayıtlardır (ham `database_results`
    # listesi veritabanı başına kopya taşır).
    durum["search_runs"].extend(result.to_state_records())

    varolan = {kayit.get("id") for kayit in durum["sources"] if kayit.get("id")}
    eklenen = [kayit for kayit in result.included_records if kayit.get("id")]
    cakisan = sorted({kayit["id"] for kayit in eklenen} & varolan)
    if cakisan:
        print(f"✗ Kaynak kimliği çakışıyor: {cakisan}.")
        print("   Arama, durumda kullanılan kimlikleri görmüyor; hiçbir şey yazılmadı.")
        return CIKIS_SORUN

    durum["sources"].extend(eklenen)

    # Şema kapısı: `save_state` doğrular ama istisnayla değil, açık
    # mesajla dönmek daha iyidir (`cmd_exclude` ile aynı biçim).
    durum_hatalari = validate_state(durum)
    if durum_hatalari:
        print(f"✗ Arama sonrası durum şemaya uymuyor ({len(durum_hatalari)} hata):")
        for satir in durum_hatalari[:5]:
            print(f"   • {satir}")
        print("   Hiçbir şey yazılmadı.")
        return CIKIS_SORUN

    save_state(durum)

    return CIKIS_OK


def _aramaya_pico(args, durum: dict) -> tuple:
    """Aramanın PICO'su ve kullanıcıya gösterilecek hata mesajı.

    Hata varsa PICO ``None`` döner ve mesaj boş ``None`` değildir; çağıran
    tek bir `if hata` ile hem durdurur hem açıklar. Ayrı bir istisna
    sınıfı burada gereksiz: `write.brifing_uret`'in `YazimHatasi`'ndan
    farklı olarak bu bir kullanım hatası, yakalanıp ekrana basılması
    gereken bir program hatası değil.
    """
    from tools.source_search import parse_pico

    if getattr(args, "pico", None):
        # Boşluk denetimi `--rq` dalıyla AYNI olmalı. Ölçülen arıza:
        # `--pico "alelik analizi"` gibi anahtar kelimesiz bir metin boş
        # PICO'ya dönüşüyordu ve arama sessizce genel sorguyla çalışıyor,
        # "arama tamamlandı" diye yeşil çıkıyordu. `--rq` dalı bunu zaten
        # reddediyordu; iki dalın farklı davranması kural değil, eksiklikti.
        pico = parse_pico(args.pico)
        if not pico.non_empty():
            return None, (
                "❌ --pico metninden arama terimi üretilemedi.\n"
                f"   Verilen: {args.pico!r}\n"
                "   Etiketli yazım kullan ya da terim içeren serbest metin ver\n"
                '   (örn. --pico "pop: Alectoris chukar, outcome: survival").'
            )
        return pico, None

    rq_id = getattr(args, "rq", None)
    sorular = durum.get("research_questions") or []
    if not rq_id:
        kayitli = ", ".join(s.get("id", "?") for s in sorular if isinstance(s, dict))
        return None, (
            "❌ Araştırma sorusu verilmedi.\n"
            f"   Kayıtlı sorular: {kayitli or '(hiç kayıt yok — research_questions boş)'}\n"
            "   Kullanım: search <RQ-ID>  |  search <RQ-ID> --pico \"pop: …, outcome: …\""
        )

    rq = _kayit_bul(sorular, rq_id)
    if rq is None:
        kayitli = ", ".join(s.get("id", "?") for s in sorular if isinstance(s, dict))
        return None, (
            f"❌ Araştırma sorusu bulunamadı: {rq_id}\n"
            f"   Kayıtlı sorular: {kayitli or '(hiç kayıt yok — research_questions boş)'}\n"
            "   Arama yapılmadı; boş PICO ile 100 alakasız kaynak yazılması engellendi."
        )

    pico = parse_pico(rq.get("text", "") or "")
    if not pico.non_empty():
        return None, (
            f"❌ {rq_id} metninden arama terimi üretilemedi.\n"
            f"   Soru metni: {rq.get('text')!r}\n"
            "   `tools.source_search.parse_pico` yalnızca İngilizce anahtar\n"
            "   kelimelere bakar (patients, treatment, randomized …); terim\n"
            "   bulunmayan bir metin boş PICO'ya dönüşür ve arama genel bir\n"
            "   sorguya dönüşür. Arama yapılmadı — alakasız kaynak yazılmadı.\n"
            "   Çözüm: `--pico` ile özgün PICO ver\n"
            "   (örn. --pico \"pop: …, intervention: …, outcome: …\")."
        )

    return pico, None


@_durum_gerekir
def cmd_verify(args, durum) -> int:
    """Kaynak doğrulaması — `tools.source_verify` motoruna bağlı.

    Neden bağlandı
    --------------
    Bu komut iki satırdı: "Henüz implemente edilmedi (tools/source_verify)"
    basıp 0 dönüyordu. Oysa `tools/source_verify/` tam uygulanmış ve
    24 testi var: Crossref + OpenAlex, en az 2 bağımsız kaynak, skor ≥ 0.60,
    retraksiyon ve korizyon. Yani CLI'daki yüzey GERÇEK OLMAYAN taraftı.
    Aynı "ikinci yüzey" hastalığı: iki şema ağacı, iki `empty_state`, ölü
    `pdf_extract` test dizini, eksik `__main__.py`, `skill.yaml`'nın var
    olmayan CLI yüzeyini göstermesi.

    Çıkış kodu
    ----------
    0 yalnız "doğrulanan kaynak var" demektir. Bir kaynak `unverified`,
    `pending` ya da `retracted` ise 1 döner: `thesis:write` yalnızca
    `verification.status == "verified"` kaynakları brifinge koyar
    (`write.haric_eden_kaynaklar`), yani 0 dönmek "yazılabilir" izlenimi
    verirdi.

    Retraksyon yalnızca yukarı gider
    -------------------------------
    `retraction_status` ve `correction_status` alanları yeni bir
    doğrulamayla temizlenmez. Tek bir veritabanının yanlış/eksik
    yanıtı, geri çekilmiş bir kaynağı akta sokardı. Depodaki tek retraksiyon
    kuralı `citation_check/checker.py:58` yalnız `== "retracted"` diyor;
    burada da aynısı uygulanır, `expression_of_concern` genişletilmez.
    """
    from tools.source_verify import MIN_BIBLIOGRAPHIC_MATCH, verify_sources_batch

    kaynaklar = [k for k in (durum.get("sources") or []) if isinstance(k, dict)]

    secilen = _dogrulanacak_kaynaklar(args, kaynaklar)
    if secilen is None:
        return CIKIS_SORUN

    if not secilen:
        print("✅ Doğrulanacak kaynak yok — tüm kaynaklar zaten 'verified'.")
        for kaynak in kaynaklar:
            dogrulama = kaynak.get("verification")
            durum_degeri = dogrulama.get("status") if isinstance(dogrulama, dict) else None
            print(f"   {kaynak.get('id')}  {durum_degeri}")
        return CIKIS_OK

    print(f"🔍 Kaynak doğrulama başlatılıyor: {len(secilen)} kaynak…")
    sonuclar = verify_sources_batch(secilen)

    # `verify_batch` kayıt sırasını korur; yine de kimlikle eşleştirilir.
    sonuc_haritasi = {s.source_id: s for s in sonuclar if getattr(s, "source_id", None)}

    dogrulanan: list[str] = []
    sorunlu: list[tuple[str, str]] = []
    for kaynak in secilen:
        kimlik = kaynak.get("id")
        sonuc = sonuc_haritasi.get(kimlik)
        if sonuc is None:
            sorunlu.append((kimlik, "doğrulama sonucu dönmedi"))
            continue
        _dogrulama_uygula(kaynak, sonuc, MIN_BIBLIOGRAPHIC_MATCH)
        durum_degeri = sonuc.status
        if durum_degeri == "verified":
            dogrulanan.append(kimlik)
        else:
            sorunlu.append((kimlik, _DOGRULAMA_SONUCU.get(durum_degeri, durum_degeri)))

    save_state(durum)

    for kaynak in secilen:
        dogrulama = kaynak.get("verification") or {}
        durum_degeri = dogrulama.get("status")
        skor = dogrulama.get("bibliographic_match")
        aciklama = _DOGRULAMA_SONUCU.get(durum_degeri, durum_degeri)
        print(f"   {kaynak.get('id')}  {aciklama}  (skor={skor})")

    if sorunlu:
        print(f"\n⚠️  {len(sorunlu)} kaynak doğrulanmadı:")
        for kimlik, sebep in sorunlu:
            print(f"   • {kimlik}: {sebep}")
        print("   Doğrulanmayan kaynak thesis:write brifingine GİRMEZ.")
    if dogrulanan:
        print(f"\n✅ {len(dogrulanan)} kaynak doğrulandı → sources")
    return CIKIS_SORUN if sorunlu else CIKIS_OK


#: `VerificationStatus` değerleri -> kullanıcının göreceği Türkçe sonuç.
#: Çıktıda İngilizce enum bırakmak, en kritik sonucu (geri çekilmiş kaynak)
#: okunması en zor şekilde gösterirdi.
_DOGRULAMA_SONUCU: dict[str, str] = {
    "verified": "doğrulandı",
    "unverified": "eşleşme eşiğin altında (en az 2 bağımsız kaynak gerekli)",
    "pending": "hiçbir veritabanı eşleşme bulamadı (DOI yok ya da ulaşılamadı)",
    "retracted": "⚠️  GERİ ÇEKİLMİŞ — bu kaynakla atıf yapılamaz",
    "corrected": "⚠️  DÜZELTME/KORİZYON YAYIMLANDI — kaynak gözden geçirilmeli",
}


def _dogrulanacak_kaynaklar(args, kaynaklar: list) -> list[dict] | None:
    """Hangi kaynaklar doğrulanacak? Hatalı girdide ``None``.

    ``--all`` DOĞRULANMAMIŞ kaynakları seçer, hepsini değil: doğrulanmış bir
    kaynağı yeniden ağa göndermek onu gereksiz yere düşürme riskine sokar.
    """
    istenen = getattr(args, "source", None)
    hepsi = getattr(args, "all", False)

    if isinstance(istenen, str):
        istenen = [istenen] if istenen else []
    elif istenen is None:
        istenen = []

    if hepsi:
        secilen = [
            k for k in kaynaklar
            if not _dogrulanmis(k)
        ]
    elif istenen:
        secilen = []
        for kimlik in istenen:
            kaynak = _kayit_bul(kaynaklar, kimlik)
            if kaynak is None:
                print(f"❌ Kaynak bulunamadı: {kimlik}")
                return None
            secilen.append(kaynak)
    else:
        print("❌ Hangi kaynak doğrulanacak belirtilmedi.")
        bekleyen = [k for k in kaynaklar if not _dogrulanmis(k)]
        for kaynak in bekleyen:
            print(f"   bekleyen: {kaynak.get('id')}")
        if not bekleyen:
            print("   (tüm kaynaklar zaten doğrulanmış)")
        print("   Kullanım: verify <SRC-ID> [<SRC-ID>…]  |  verify --all")
        return None

    # Ayni kaynak iki kez gonderilmesin.
    gorulen: set[str] = set()
    benzersiz: list[dict] = []
    for kaynak in secilen:
        kimlik = kaynak.get("id")
        if kimlik in gorulen:
            continue
        gorulen.add(kimlik)
        benzersiz.append(kaynak)
    return benzersiz


def _dogrulanmis(kaynak: dict) -> bool:
    dogrulama = kaynak.get("verification")
    return isinstance(dogrulama, dict) and dogrulama.get("status") == "verified"


def _dogrulama_uygula(kaynak: dict, sonuc, esik: float) -> None:
    """`VerificationResult` -> `source.verification` (yalnız şema alanları).

    `verification_details` bilerek KOPYALANMAZ: `source.json`
    `additionalProperties: false` ve o alanın karşılığı yok. Detay
    (veritabanı başına ham skor) yalnız ekranda okunabilir olur.
    """
    detay = sonuc.verification_details or {}
    # En yüksek `overall` skorlu veritabanı: karşılaştırma işaretleri
    # ("başlık tuttu mu?") EN İYİ kanıttan gelmelidir, ortalamadan değil.
    en_iyi_ad = ""
    en_iyi_skor = -1.0
    for ad, deger in detay.items():
        if isinstance(deger, dict):
            skor = deger.get("overall")
            if isinstance(skor, (int, float)) and skor > en_iyi_skor:
                en_iyi_ad, en_iyi_skor = ad, float(skor)
    en_iyi = detay.get(en_iyi_ad) if en_iyi_ad else None
    en_iyi = en_iyi if isinstance(en_iyi, dict) else {}

    # `title_match` vb. boolean/null. Skor -> boolean ESIGI UYDURULMAZ:
    # motorun kendi `min_match` degeri kullanilir (MIN_BIBLIOGRAPHIC_MATCH).
    esik_gecer = lambda ad: (  # noqa: E731
        None if en_iyi.get(ad) is None else float(en_iyi[ad]) >= esik
    )

    kaynak["verification"] = {
        "status": sonuc.status,
        "bibliographic_match": sonuc.bibliographic_match,
        "verified_at": sonuc.verified_at,
        "verification_sources": list(sonuc.verification_sources or []),
        "doi_match": _isaret(en_iyi.get("doi_match")),
        "title_match": esik_gecer("title"),
        "author_match": esik_gecer("author"),
        "year_match": esik_gecer("year"),
        "journal_match": esik_gecer("journal"),
    }

    # Ust duzey `verified` bayragı: yalnız gerçekten dogrulanmışsa true.
    # RETRAKSIYONLU KAYNAKTA ISE ASLA true DEGIL. Geri cekilmis bir
    # kayit "dogrulanmis" olarak sunulamaz; tek bir veritabaninin yanlis
    # ya da eksik yaniti bu bayragi tekrar true yapamaz, cunku
    # `retraction_status` geri alinmaz.
    kaynak["verified"] = (
        sonuc.status == "verified" and kaynak.get("retraction_status") != "retracted"
    )

    if sonuc.status == "retracted":
        kaynak["retraction_status"] = "retracted"
    if sonuc.status == "corrected":
        kaynak["correction_status"] = "corrected"


def _isaret(deger) -> bool | None:
    """`doi_match` zaten boolean; bilinmiyorsa ``None`` (sema izin verir)."""
    return deger if isinstance(deger, bool) else None


@_durum_gerekir
def cmd_extract(args, durum) -> int:
    """PDF'ten kanıt çıkar."""
    from tools.pdf_extract import find_evidence_for_claim

    if _kayit_bul(durum.get("sources", []), args.source) is None:
        print(f"❌ Kaynak bulunamadı: {args.source}")
        return 1

    iddia = _kayit_bul(durum.get("claims_registry", []), args.claim)
    if iddia is None:
        print(f"❌ İddia bulunamadı: {args.claim}")
        return 1

    # source.json'da yerel dosya yolu alanı yok; yol CLI'den verilir.
    if not getattr(args, "pdf", None):
        print("❌ --pdf zorunlu (source.json'da yerel dosya yolu alanı yok)")
        return 1
    pdf_yolu = _cozumle(args.pdf)
    if not pdf_yolu.exists():
        print(f"❌ PDF bulunamadı: {pdf_yolu}")
        return 1

    # Ajan-küratörlüğü: ajan PDF'i okuyup doğruladığı alıntıyı doğrudan
    # kaydet (matcher yerine). İki aşamalı akışın ikinci aşaması: motor
    # aday üretir, ajan en iyisini seçip doğrular.
    if getattr(args, "quote", None):
        sira = _sonraki_kanit_sirasi(durum.get("evidence_registry", []))
        kayit = {
            "id": f"EVD-{sira:03d}",
            "source_id": args.source,
            "location": {
                "page": args.page or 1,
                "section": args.section or "",
                "paragraph": 1,
            },
            "text": args.quote,
            "evidence_type": "literature",
            "strength": "direct",
            "supports_claim": args.claim,
            "verified": True,
            "extracted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "extraction_method": "manual",
            "notes": "Ajan PDF'i okuyup doğruladı",
        }
        durum["evidence_registry"].append(kayit)
        save_state(durum)
        print(f"✅ {kayit['id']} kaydedildi (ajan-küratörlüğü, verified: true)")
        return 0

    print(f"📄 Kanıt aranıyor: {args.source} → {args.claim}")
    bulgular = find_evidence_for_claim(pdf_yolu, iddia.get("text", ""))

    if not bulgular:
        print(f"⚠️  {args.claim} iddiasını destekleyen kanıt bulunamadı ({pdf_yolu.name})")
        return 1

    sira = _sonraki_kanit_sirasi(durum.get("evidence_registry", []))
    for bulgu in bulgular:
        kayit = _kanit_kaydi(bulgu, args.source, args.claim, sira)
        durum["evidence_registry"].append(kayit)
        konum = f"s.{kayit['location']['page']}" if kayit["location"]["page"] else "s.?"
        print(f"   {kayit['id']}  {konum}  ({kayit['strength']})")
        sira += 1

    save_state(durum)
    print(f"✅ {len(bulgular)} kanıt eklendi → evidence_registry")
    print(f"   Kanıtlar 'verified: false' olarak işaretlendi — elle doğrulama gerekli.")
    return 0


def _kayit_bul(kayitlar: list, kimlik: str) -> dict | None:
    """Listede verilen kimliğe sahip ilk kaydı döndürür."""
    for kayit in kayitlar or []:
        if kayit.get("id") == kimlik:
            return kayit
    return None


def _sonraki_kanit_sirasi(kayitlar: list) -> int:
    """Bir sonraki EVD-NNN numarasını hesaplar."""
    en_yuksek = 0
    for kayit in kayitlar or []:
        kimlik = kayit.get("id", "")
        if isinstance(kimlik, str) and kimlik.startswith("EVD-"):
            try:
                en_yuksek = max(en_yuksek, int(kimlik[4:]))
            except ValueError:
                continue
    return en_yuksek + 1


def _kanit_kaydi(bulgu, source_id: str, claim_id: str, sira: int) -> dict:
    """ExtractedEvidence nesnesini evidence.json kaydına dönüştürür."""
    return {
        "id": f"EVD-{sira:03d}",
        "source_id": source_id,
        "location": {
            "page": bulgu.page,
            "section": bulgu.section or "",
            # paragraph_index 0-bazlidir; evidence semasi (min 1) 1-bazli
            # insan-okur konum bekler. (Regresyon: 0 yazilinca kayit semadan
            # dusup dosyaya hic yazilmiyordu.)
            "paragraph": bulgu.paragraph_index + 1,
        },
        "text": bulgu.text,
        "evidence_type": bulgu.evidence_type,
        "supports_claim": claim_id,
        "strength": bulgu.strength,
        "verified": False,
        "extracted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "extraction_method": "pdf_text_layer",
        "notes": bulgu.subsection or "",
    }


def _kapi_raporu(durum: dict, kapi: str) -> bool:
    """Kapiyi kontrol eder; engel varsa ekrana basar ve False doner.

    Bu, onay motorunun CLI'daki TEK giriş noktasidir. Yazim ve ihracat
    kapilari sormadan ilerlemez.
    """
    from tools.atw.approval import kontrol_yaz

    engeller = kontrol_yaz(durum, kapi)
    if not engeller:
        return True

    print(f"🚧 '{kapi}' kapısı kapalı — işlem durduruldu:")
    for engel in engeller:
        print(f"   • {engel}")
    print("   İnsan onayı gerekiyor; kapıyı tez durumundan açın.")
    return False


@_durum_gerekir
def cmd_write(args, durum) -> int:
    """Bölüm yaz: brifing üret, yazılanı denetle, geçerse kaydet.

    Önce 'methodology' kapısı sorulur: yazım yöntem onayından geçmeden
    yapılırsa, sonradan yöntem değişince tüm bölümler geçersiz olur.

    İki kip:

      * ``--file`` YOK: brifing basılır, tez durumu **değişmez**. Metni
        `agents/writer.md` ajanı üretir — CLI Türkçe metin üretmez.
      * ``--file`` VAR: ajanın bölüm dosyası denetlenir. Tüm sorunlar
        bildirilir; tek bir sorun bile varsa **hiçbir şey yazılmaz**, ki
        dosya elle düzeltilip yeniden denenebilsin.
    """
    from tools.atw.state import validate_state
    from tools.atw.write import (
        YazimHatasi,
        bolum_dogrula,
        bolumu_kaydet,
        brifing_metni,
        brifing_uret,
    )

    if not _kapi_raporu(durum, "methodology"):
        return CIKIS_SORUN

    bolum_id, rq_id = args.chapter, args.rq
    dosya = _secili_dosya(getattr(args, "file", None))

    if not dosya:
        try:
            brifing = brifing_uret(durum, bolum_id, rq_id)
        except YazimHatasi as hata:
            print(f"✗ {hata}")
            return CIKIS_SORUN
        if getattr(args, "json", False):
            print(json.dumps(brifing, ensure_ascii=False, indent=2))
        else:
            print(brifing_metni(brifing))
        return CIKIS_OK

    yol = _cozumle(dosya)
    try:
        metin = yol.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        print(f"✗ Bölüm dosyası bulunamadı: {dosya}")
        return CIKIS_SORUN
    except OSError as hata:
        print(f"✗ Bölüm dosyası okunamadı: {yol} ({hata})")
        return CIKIS_SORUN

    try:
        bolum = json.loads(metin)
    except json.JSONDecodeError as hata:
        print(f"✗ Geçersiz JSON: {yol.name} (satır {hata.lineno}, sütun {hata.colno})")
        return CIKIS_SORUN

    if not isinstance(bolum, dict):
        print(f"✗ Bölüm dosyası bir JSON nesnesi olmalı: {yol.name}")
        return CIKIS_SORUN

    hatalar = bolum_dogrula(bolum, durum, bolum_id, rq_id)
    if hatalar:
        print(f"✗ Bölüm denetimi başarısız — {bolum_id}, {len(hatalar)} sorun:")
        for hata in hatalar:
            print(f"   • {hata}")
        print("   Dosya yerinde bırakıldı; düzeltip yeniden çalıştır.")
        return CIKIS_SORUN

    bolumu_kaydet(durum, bolum)

    # Kaydedilmeden önce durumun şemaya uyduğunu doğrula. `save_state`
    # (aşağıda) doğrulama yapmıyor; sessizce bozuk durum yazmamak için
    # burada açıkça deniyor.
    durum_hatalari = validate_state(durum)
    if durum_hatalari:
        detay = "; ".join(durum_hatalari[:5])
        print(f"✗ Kaydedilecek durum şemaya uymuyor ({len(durum_hatalari)} hata): {detay}")
        print(f"   {bolum_id} kaydedilmedi.")
        print("   Bu hatalar bölüm dosyasından DEĞİL, tez durumunun başka")
        print("   registry'lerinden geliyor olabilir; yolundaki alanı düzelt.")
        return CIKIS_SORUN

    save_state(durum)
    paragraf_sayisi = len(bolum.get("paragraphs") or [])
    print(f"✅ Bölüm kaydedildi: {bolum_id} · {paragraf_sayisi} paragraf")
    return CIKIS_OK


@_durum_gerekir
def cmd_approve(args, durum) -> int:
    """Onay kapısını aç, kapat ya da akışı göster.

    Neden bu komut ayrı bir birim
    --------------------------
    `tools.atw/approval.py` `onay_ver`/`onay_geri_al` uygular ve 7 kapının
    adını bilir. Ama `human_approvals` alanını DOLDURAN hiçbir komut yoktu:
    `empty_state()` hepsini `False` üretiyor, `cmd_status` yalnızca
    gösteriyordu. Kapı hiçbir yoldan açılamadığı için `cmd_write` ve
    `cmd_export` hiçbir koşulda ilerleyemiyordu.

    İki denetim ayrıdır
    -------------------
      1. SIRA   — `onay_ver` önceki kapıların onaylı olmasını ister
         (atlanmış akış).
      2. HAZIRLIK — `approval.hazirlik_engelleri` o aşamanın verisinin
         gerçekten üretilmiş olmasını ister. Kapı boş bir belgeye
         verilmez.

    `hazirlik_engelleri` `--revoke` yolunda BİLEREK sorulmaz: onay geri
    almak veri üretmekten kolaydır, yoksa geri alınamayan kapılar birikir.
    """
    from tools.atw.approval import (
        OnayHatasi,
        acik_olanlar,
        hazirlik_engelleri,
        onay_geri_al,
        onay_ver,
        ozet,
    )

    if getattr(args, "list", False):
        print("🔐 Onay kapıları (PRISMA):")
        for kapi, acik_mi, engeller in ozet(durum):
            isaret = "✅" if acik_mi else "⬜"
            print(f"   {isaret} {kapi}")
            # TÜM engeller, ilki değil. `thesis:status` özet (tek engel)
            # gösterir; `--list` niyeti teşhistir: "neden açılmıyor?"
            # sorusunun cevabı ikinci engelde olabilir.
            for engel in engeller:
                print(f"       • {engel}")
        print(f"   → {len(acik_olanlar(durum))}/{len(durum.get('human_approvals') or {})} aşama onaylı")
        return CIKIS_OK

    kapi = getattr(args, "kapi", None)
    if not kapi:
        print("❌ Kapı adı gerekli. Örnek: approve methodology")
        print(f"   Akışı görmek için: approve --list")
        return CIKIS_SORUN

    if kapi not in durum.get("human_approvals", {}):
        # `onay_ver` de ValueError fırlatır; ama burada liste kullanıcıya
        # gösterilir, yazım hatası sessizce geçmez.
        gecerli = ", ".join(durum.get("human_approvals") or {})
        print(f"❌ Bilinmeyen onay kapısı: {kapi}")
        print(f"   Geçerli kapılar: {gecerli}")
        return CIKIS_SORUN

    if getattr(args, "revoke", False):
        kapanan = [
            k
            for k, acik_mi, _ in ozet(durum)
            if acik_mi and _kapi_sirasi(k) > _kapi_sirasi(kapi)
        ]
        onay_geri_al(durum, kapi)
        save_state(durum)
        print(f"🔒 '{kapi}' kapısı geri alındı.")
        if kapanan:
            print(f"   Bağımlı olduğu kapılar da kapatıldı: {', '.join(kapanan)}")
        return CIKIS_OK

    engeller = hazirlik_engelleri(durum, kapi)
    if engeller:
        print(f"🚧 '{kapi}' kapısı açılamaz — hazırlık eksik:")
        for engel in engeller:
            print(f"   • {engel}")
        print("   Önce bu veriyi üret, sonra kapıyı aç.")
        return CIKIS_SORUN

    try:
        onay_ver(durum, kapi)
    except OnayHatasi as hata:
        print(f"🚧 {hata}")
        return CIKIS_SORUN

    save_state(durum)
    print(f"✅ '{kapi}' kapısı açıldı.")
    return CIKIS_OK


def _kapi_sirasi(kapi: str) -> int:
    """Kapının akış sırasındaki yeri. Bilinmeyen ad sona konur."""
    from tools.atw.state import APPROVAL_GATES

    return APPROVAL_GATES.index(kapi) if kapi in APPROVAL_GATES else len(APPROVAL_GATES)


@_durum_gerekir
def cmd_record(args, durum) -> int:
    """Ajanın ürettiği JSON kaydını denetleyip registry'ye yaz.

    Neden ayrı komutlar değil
    --------------------------
    `research_questions`, `hypotheses`, `claims_registry`, `citations`,
    `gap_registry`, `findings_registry` ve ölçüm koleksiyonlarının
    yazıcısı YOKTU. `research_questions` boş kaldığı için
    `research_question` kapısı hiç açılamıyor, sonraki altı kapı da
    sırayla kilitleniyor ve `write`/`export` erişilemiyordu.

    Her registry için ayrı komut, her biri kendi testine sahip ikinci
    birer yüzey olurdu. Tek komut: tek denetim, tek hata biçimi.

    Doğrulama sırası: varlık şeması → kimlik (ön ek/biçim/tekrar) →
    kaydın eklenmesiyle oluşan YENİ kopuk referanslar. Son adım
    `graph.kopuk_baglari` ile yapılır; ikinci bir kopukluk denetimi
    yazılmaz, çünkü o tablo zaten şemadan türüyor ve her bütünlük
    denetiminde raporlanıyor.

    Kısmi yazma yoktur: dosyadaki kayıtlar ya hep yazılır ya hiç.
    """
    from tools.atw.record import (
        KayitHatasi,
        kaydet,
        kayitlari_oku,
        ozet,
        varlik_tipi,
        yazilabilir_registryler,
    )

    registry = getattr(args, "registry", None)
    if not registry:
        gecerli = ", ".join(sorted(yazilabilir_registryler()))
        print("❌ Registry adı gerekli.")
        print(f"   Yazılabilir: {gecerli}")
        print("   Kullanım: record <REGISTRY> --file <KAYIT.json>")
        return CIKIS_SORUN

    # Registry adı ve sahiplik burada çözülür; `kayitlari_oku` hatası
    # ile karışmasın diye dosya okunmadan ÖNCE.
    try:
        tip = varlik_tipi(registry)
    except KayitHatasi as hata:
        for satir in hata.mesajlar:
            print(f"❌ {satir}")
        return CIKIS_SORUN

    yol = getattr(args, "file", None)
    if not yol:
        print("❌ --file gerekli (ajanın ürettiği JSON dosyası).")
        print(f"   Örnek: record {registry} --file sorular.json")
        return CIKIS_SORUN

    cozulmus = _cozumle(yol)
    if not cozulmus.exists():
        print(f"❌ Dosya bulunamadı: {cozulmus}")
        return CIKIS_SORUN

    try:
        kayitlar = kayitlari_oku(cozulmus)
    except KayitHatasi as hata:
        for satir in hata.mesajlar:
            print(f"❌ {satir}")
        return CIKIS_SORUN

    try:
        sonuc = kaydet(durum, registry, kayitlar)
    except KayitHatasi as hata:
        print(f"✗ {registry} kaydı reddedildi — {len(hata.mesajlar)} sorun:")
        for satir in hata.mesajlar:
            print(f"   • {satir}")
        print("   Hiçbir kayıt yazılmadı.")
        return CIKIS_SORUN

    # Kaydedilmeden önce durumun şemaya uyduğunu doğrula. CLI'nin kendi
    # `save_state`'i doğrulama yapmıyor; `cmd_write` ile aynı gerekçe.
    durum_hatalari = validate_state(durum)
    if durum_hatalari:
        durum[registry] = [k for k in durum[registry] if k.get("id")
                           not in set(sonuc["eklendi"] + sonuc["degistirildi"])]
        print(f"✗ Kaydedilecek durum şemaya uymuyor ({len(durum_hatalari)} hata):")
        for satir in durum_hatalari[:5]:
            print(f"   • {satir}")
        print(f"   {tip} kaydı geri alındı. Bu hatalar {registry} dosyasından")
        print("   değil, tez durumunun başka registry'lerinden geliyor olabilir.")
        return CIKIS_SORUN

    save_state(durum)

    for kayit in kayitlar:
        etiket = "yeni" if kayit.get("id") in sonuc["eklendi"] else "güncel"
        print(f"   {etiket:>6}  {ozet(kayit)}")
    print(f"\n✅ {registry}: {len(sonuc['eklendi'])} eklendi, "
          f"{len(sonuc['degistirildi'])} güncellendi → {len(durum[registry])} kayıt")
    if registry == "research_questions":
        print("   Sonraki adım: thesis:approve research_question")
    return CIKIS_OK


#: Eleme koruması tablosu: elenen kaynaklara referans veren registry alanları.
#: (registry alanı, varlık adı, referans alanları). Tekil alanlar
#: (source_id) ve dizi alanlar (supporting_source_ids) aynı biçimde
#: taranır; `tools.atw.state.find_dangling_references` yalnızca tekil
#: `<varlık>_id` mekanizmasını kapsadığı için dizi alanlar burada açıkça
#: denetlenir.
_KAYNAK_REFERANSLARI: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("citations", "citation", ("source_id",)),
    ("evidence_registry", "evidence", ("source_id",)),
    ("gap_registry", "research_gap",
     ("supporting_source_ids", "contradicting_source_ids")),
    ("discussion_registry", "discussion", ("compared_source_ids",)),
    ("figures", "figure", ("original_source_id",)),
    ("tables", "table", ("original_source_id",)),
    ("sources", "source", ("supersedes_source_id",)),
)


def _kaynak_baglari(
    durum: dict, elenen: set[str], birlikte_elenen: set[str]
) -> list[str]:
    """Elenecek kaynaklara başka kayıtların verdiği referansları listeler.

    `birlikte_elenen`: aynı çağrıda birlikte elenen kimlikler. O kayıt da
    kaldırılacağı için kopuk bağ oluşmaz; örneğin SRC-002'nin
    `supersedes_source_id` döndürdüğü SRC-001 ile SRC-002 birlikte
    eleniyorsa referans koruması takılmaz.
    """
    bagli: list[str] = []
    for alan, varlik, referans_alanlari in _KAYNAK_REFERANSLARI:
        for kayit in durum.get(alan, []) or []:
            if not isinstance(kayit, dict):
                continue
            kimlik = kayit.get("id")
            if kimlik in birlikte_elenen:
                continue
            for referans_alan in referans_alanlari:
                deger = kayit.get(referans_alan)
                if isinstance(deger, str):
                    if deger in elenen:
                        bagli.append(
                            f"{varlik} {kimlik} -> {referans_alan}={deger}"
                        )
                elif isinstance(deger, list):
                    for ref in deger:
                        if ref in elenen:
                            bagli.append(
                                f"{varlik} {kimlik} -> {referans_alan}={ref}"
                            )
    return bagli


@_durum_gerekir
def cmd_exclude(args, durum) -> int:
    """Elenecek kaynakları kaynak kümesinden çıkar (PRISMA tarama kararı).

    Neden var
    ---------
    Skill'in sistematik inceleme protokolü (SKILL.md 2.3) başlık/özet
    taraması ve hariç tutma kriterlerini zorunlu kılar. Gerçek bir
    koşuda üç arama 80 kayıt getirdi ve küme tarama olmadan `source_set`
    kapısına gidemez: 25 çakışan DOI (aynı çalışma her aramada ayrı SRC
    kimliği aldı) ve `fig-*`/`supp-*` ek-materyal DOI'leri vardı. Kayıt
    elenecek bir komut yoktu (`record sources` sahiplik nedeniyle
    reddediliyor).

    Davranış
    --------
    1. Verilen kimlikler `sources`'dan çıkarılır; diğer kayıtlar
       korunur.
    2. Kimliği `included_source_ids`'ta olan HER arama kaydının PRISMA
       akışı yeniden türetilir: `studies_included` azalır,
       `records_excluded` (başlık/özet tarama) artar ve `reports_sought`
       aynı miktar azalır. Gerekçe `exclusion_reasons`'a yazılır; aynı
       gerekçe varsa `count` birikir.
       `reports_excluded` (tam metin uygunluk) ve `reports_not_retrieved`
       (alınamayan) kademelerine DOKUNULMAZ: `exclude` yalnızca
       başlık/DOI/özet TARAMA kararıdır — hiçbir raporun tam metni
       alınmaz, o rapor tam metin aşamasına hiç girmemiştir.
       (Ölçülen-bozuk aşama eşlemesi düzeltildi, 2026-09-28: eski
       davranış her tarama elemesini `reports_excluded`'a yazıyor,
       PRISMA diyagramı tam metni hiç alınmamış raporlar için 'tam
       metin dışlanan N rapor' iddiası üretiyordu.)
    3. Referans koruması: elenen kaynağa başka bir kayıt referans
       veriyorsa (citation, evidence, gap, discussion, figure/table,
       supersedes) hiçbir şey YAZILMAZ.
    4. Yazım yalnızca `validate_state` temizse yapılır.

    Hiçbir adımda kısmi yazım yoktur.
    """
    kimlikler = list(dict.fromkeys(args.ids or []))
    if not kimlikler:
        print("❌ En az bir SRC kimliği gerekli.")
        print("   Kullanım: exclude SRC-001 SRC-002 … --reason <GEREKÇE>")
        return CIKIS_SORUN

    sebep = (getattr(args, "reason", "") or "").strip()
    if not sebep:
        print("❌ --reason gerekli (boş olamaz).")
        print("   Tarama kararının gerekçesi arama kayıtlarının "
              "`exclusion_reasons`'ına yazılır.")
        return CIKIS_SORUN

    mevcut = {kayit.get("id") for kayit in durum["sources"]}
    bilinmeyen = [k for k in kimlikler if k not in mevcut]
    if bilinmeyen:
        print("❌ Bilinmeyen kaynak kimlikleri: " + ", ".join(bilinmeyen))
        return CIKIS_SORUN

    elenen = set(kimlikler)
    bagli = _kaynak_baglari(durum, elenen, elenen)
    if bagli:
        print(f"✗ {len(kimlikler)} kaynak elenemedi — referans veren kayıtlar var:")
        for satir in bagli:
            print(f"   • {satir}")
        print("   Önce referansları çözün ya da elenecek kümeyi değiştirin.")
        print("   Hiçbir şey yazılmadı.")
        return CIKIS_SORUN

    durum["sources"] = [
        kayit for kayit in durum["sources"] if kayit.get("id") not in elenen
    ]

    degisen_kayitlar = 0
    for kosu in durum.get("search_runs", []) or []:
        dahil = kosu.get("included_source_ids", []) or []
        kesilen = [k for k in kimlikler if k in dahil]
        if not kesilen:
            continue
        kosu["included_source_ids"] = [k for k in dahil if k not in elenen]
        akis = kosu["prisma_flow"]
        akis["records_excluded"] = akis.get("records_excluded", 0) + len(kesilen)
        akis["reports_sought"] = akis.get("reports_sought", 0) - len(kesilen)
        akis["studies_included"] = akis.get("studies_included", 0) - len(kesilen)
        # `reports_excluded` (tam metin uygunluk) ve `reports_not_retrieved`
        # (alınamayan) kademelerine dokunulmaz: tarama kararı hiçbir raporun
        # tam metnini görmeden verilir (kopya/yayın türü/konu dışı →
        # başlık, DOI ve özet düzeyinde).
        nedenler = kosu.get("exclusion_reasons", []) or []
        for neden in nedenler:
            if neden.get("reason") == sebep:
                neden["count"] = neden.get("count", 0) + len(kesilen)
                break
        else:
            nedenler.append({"reason": sebep, "count": len(kesilen)})
        kosu["exclusion_reasons"] = nedenler
        degisen_kayitlar += 1

    durum_hatalari = validate_state(durum)
    if durum_hatalari:
        print(f"✗ Eleme sonrası durum şemaya uymuyor ({len(durum_hatalari)} hata):")
        for satir in durum_hatalari[:5]:
            print(f"   • {satir}")
        print("   Hiçbir şey yazılmadı.")
        return CIKIS_SORUN

    save_state(durum)

    print(f"✅ {len(kimlikler)} kaynak elendi: {', '.join(kimlikler)}")
    print(f"   Gerekçe: {sebep}")
    if degisen_kayitlar:
        print(f"   {degisen_kayitlar} arama kaydının PRISMA akışı güncellendi.")
    else:
        print("   Hiçbir arama kaydı bu kaynakları dahil etmemişti.")
    print(f"   Kaynak kümesi: {len(durum['sources'])} kayıt")
    return CIKIS_OK


@_durum_gerekir
def cmd_audit(args, durum) -> int:
    """Tez denetimi.

    Denetim kayitlari audit_registry'ye yazilir. En az bir 'critical' bulgusu
    varsa 1 doner; boylece bir denetim dogrudan CI'da gate olabilir.

    Uygulanmayan turler (consistency) sessizce gecmez: acikca uyari yazilir.
    Sahte bir denetim yazmak, denetimi olmayan bir alani denetlenmis
    gostermekten kotudur.
    """
    tur = args.type or "all"

    if tur in UYARILACAK_TURLER:
        print(f"⚠️  '{tur}' denetimi bu CLI'de YOK — skill.yaml'daki "
              f"{tur}-auditor ajanının işidir. Atlandı.")
        return CIKIS_OK

    kayitlar = tum_denetimler(durum, [tur])
    denetim_kimligi_ata(durum, kayitlar)
    durum.setdefault("audit_registry", []).extend(kayitlar)
    save_state(durum)

    kritik_toplam = 0
    for kayit in kayitlar:
        bulgular = kayit["findings"]
        kritik = kayit["critical_issues"]
        kritik_toplam += len(kritik)
        print(f"\n🔍 {kayit['audit_id']} — {kayit['audit_type']} denetimi")
        print(f"   Bulgu: {len(bulgular)}  (critical: {len(kritik)})")
        for bulgu in bulgular:
            isaret = {"critical": "🔴", "major": "🟠", "minor": "🟡"}.get(
                bulgu["severity"], "⚪"
            )
            print(f"   {isaret} [{bulgu['severity']}] {bulgu['message']}")
        sayaclar = kayit["integrity_checks"]
        ozet = "  ".join(f"{k}={v}" for k, v in sayaclar.items() if v)
        print(f"   Sayımlar: {ozet or 'hepsi sıfır'}")

    print(f"\n✅ {len(kayitlar)} denetim kaydı → audit_registry")
    if kritik_toplam:
        print(f"🔴 {kritik_toplam} kritik bulgu — tez onaya hazır değil.")
        return CIKIS_SORUN
    return CIKIS_OK


@_durum_gerekir
def cmd_status(args, durum) -> int:
    """Tez durumu özeti."""
    state = durum
    print(f"📋 Tez: {state.get('thesis_id')} — {state.get('title')}")
    print(f"   Araştırma Soruları: {len(state.get('research_questions', []))}")
    print(f"   Hipotezler: {len(state.get('hypotheses', []))}")
    print(f"   Bölümler: {len(state.get('chapters', []))}")
    print(f"   Kaynaklar: {len(state.get('sources', []))}")
    print(f"   İddialar: {len(state.get('claims_registry', []))}")
    print(f"   Kanıtlar: {len(state.get('evidence_registry', []))}")
    print(f"   Bulgular: {len(state.get('findings_registry', []))}")
    print(f"   Boşluklar: {len(state.get('gap_registry', []))}")
    print(f"   Denetimler: {len(state.get('audit_registry', []))}")

    # Onay akisi: bu blok daha once YALNIZCA sayi yaziyordu, kapilarin
    # gercekten zorlandigi yeri degil. Simdi akis motorundan tek kaynak
    # alinir.
    from tools.atw.approval import acik_olanlar, ozet

    print("\n🔐 Onay kapıları (PRISMA):")
    for kapi, acik_mi, engeller in ozet(state):
        isaret = "✅" if acik_mi else "⬜"
        satir = f"   {isaret} {kapi}"
        if engeller and acik_mi:
            satir += f"  ⚠️  {engeller[0]}"
        elif not acik_mi and engeller:
            satir += f"  — {engeller[0]}"
        print(satir)
    print(f"   → {len(acik_olanlar(state))}/7 aşama onaylı")
    return 0


@_durum_gerekir
def cmd_export(args, durum) -> int:
    """Tezi md / docx / pdf olarak dışa aktarır.

    Dışa aktarma, tezin İNSAN ONAYLI bitmiş halini paylaşmak demektir.
    Bu yüzden en katı kapı sorulur: 'final_thesis' — bütünlük, kanıtsız
    iddia ve retraksiyon denetimi de burada devreye girer.

    Çıktı dizini varsayılan olarak veri kökünün kendisidir; `--out` ile
    başka bir dizin verilebilir. Dizin yoksa oluşturulur.
    """
    from tools.atw.export import (
        DESTEKLENEN_BICIMLER,
        ExportHatasi,
        disa_aktar,
    )

    if not _kapi_raporu(durum, "final_thesis"):
        return CIKIS_SORUN

    fmt = args.format or "md"
    if fmt not in DESTEKLENEN_BICIMLER:
        # argparse `choices` zaten eler; bu yol programatik cagri icin.
        print(
            "✗ Desteklenmeyen biçim: {0}. Desteklenen: {1}".format(
                fmt, ", ".join(sorted(DESTEKLENEN_BICIMLER))
            )
        )
        return CIKIS_SORUN

    dizin = _cozumle(args.out) if getattr(args, "out", None) else veri_koku()

    try:
        dizin.mkdir(parents=True, exist_ok=True)
        yol, notlar = disa_aktar(durum, fmt, dizin)
    except ExportHatasi as hata:
        # Disa aktarim hicbir dosya yazmadan once reddedilir; yarim dosya
        # birakilmaz.
        print("✗ {0}".format(hata))
        return CIKIS_SORUN
    except OSError as hata:
        print("✗ Dosya yazılamadı: {0}".format(hata))
        return CIKIS_SORUN

    print("📤 Dışa aktarıldı: {0}".format(yol))
    for not_ in notlar:
        print("   - {0}".format(not_))
    return CIKIS_OK


def build_parser() -> argparse.ArgumentParser:
    """CLI argüman ayrıştırıcısını kurar.

    Ayrı bir fabrika olarak tutulur çünkü sözleşme testleri (bkz.
    tests/contract_tests/test_skill_yaml_contracts.py) skill.yaml'da ilan
    edilen her alt komutun gercekten kayitli oldugunu bu parser'a bakarak
    dogrulamak zorunda. main() icinde gizli kalsaydi, ilan edilen bir
    komutun yok olmasi hicbir testte yakalanamazdi.
    """
    parser = argparse.ArgumentParser(prog="thesis", description="Akademik tez yazım CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # thesis:new
    p_new = sub.add_parser("new", help="Yeni tez başlat")
    p_new.add_argument("id", help="Tez ID (örn: THESIS-2026-001)")
    p_new.add_argument("title", help="Tez başlığı")
    p_new.add_argument(
        "--force",
        action="store_true",
        help="Var olan tez durumunun ÜZERİNE yaz (veri kaybı yapar)",
    )
    p_new.set_defaults(func=cmd_new)

    # thesis:search
    p_search = sub.add_parser("search", help="Kaynak arama başlat")
    p_search.add_argument("rq", help="Araştırma sorusu ID (örn: RQ-001)")
    p_search.add_argument("--databases", default="crossref,openalex,pubmed", help="Veritabanları (virgülle ayrılmış)")
    p_search.add_argument("--year-from", type=int, help="Başlangıç yılı")
    p_search.add_argument("--year-to", type=int, help="Bitiş yılı")
    p_search.add_argument("--max-results", type=int, default=100, help="Veritabanı başına max sonuç")
    p_search.add_argument("--pico", help="PICO metni (RQ yerine doğrudan)")
    p_search.set_defaults(func=cmd_search)

    # thesis:verify
    p_verify = sub.add_parser("verify", help="Kaynak doğrulama")
    p_verify.add_argument(
        "source",
        nargs="*",
        help="Doğrulanacak kaynak kimlikleri (örn: SRC-001 SRC-002)",
    )
    p_verify.add_argument(
        "--all",
        action="store_true",
        help="DOĞRULANMAMIŞ tüm kaynakları doğrula",
    )
    p_verify.set_defaults(func=cmd_verify)

    # thesis:extract
    p_extract = sub.add_parser("extract", help="PDF'ten kanıt çıkar")
    p_extract.add_argument("source", help="Kaynak ID (SRC-XXX)")
    p_extract.add_argument("--claim", required=True, help="Hedef iddia ID (CLM-XXX)")
    p_extract.add_argument("--pdf", help="Yerel PDF dosya yolu (source.json'da yol alanı yok)")
    # Ajan-küratörlüğü: ajan PDF'i okuyup doğruladığı alıntıyı doğrudan
    # kaydedebilir (matcher yerine). İki aşamalı akışın ikinci aşaması.
    p_extract.add_argument("--quote", help="Ajanın doğruladığı alıntı metni (matcher yerine)")
    p_extract.add_argument("--page", type=int, default=0, help="Alıntının sayfa numarası")
    p_extract.add_argument("--section", default="", help="Alıntının bölüm başlığı")
    p_extract.set_defaults(func=cmd_extract)

    # thesis:write
    p_write = sub.add_parser("write", help="Bölüm yaz")
    p_write.add_argument("chapter", help="Bölüm ID (CH-XXX)")
    p_write.add_argument("--rq", required=True, help="Araştırma sorusu ID (RQ-XXX)")
    p_write.add_argument(
        "--file",
        help=(
            "Yazar ajanının ürettiği bölüm dosyası. Verilmezse brifing "
            "basılır ve durum değişmez; verilirse dosya denetlenir ve "
            "geçerse tez durumuna yazılır."
        ),
    )
    p_write.add_argument(
        "--json",
        action="store_true",
        help="Brifingi JSON olarak bas (ajanın okuması için)",
    )
    p_write.set_defaults(func=cmd_write)

    # thesis:approve
    p_approve = sub.add_parser("approve", help="Onay kapısı aç/kapat")
    p_approve.add_argument(
        "kapi",
        nargs="?",
        help="Kapı adı (research_question, search_strategy, source_set, "
             "research_gap, methodology, findings, final_thesis)",
    )
    p_approve.add_argument(
        "--revoke",
        action="store_true",
        help="Kapıyı kapat; ona dayanan kapılar da kapanır",
    )
    p_approve.add_argument(
        "--list",
        action="store_true",
        help="Akışı ve engelleri göster; durumu değiştirmez",
    )
    p_approve.set_defaults(func=cmd_approve)

    # thesis:record
    p_record = sub.add_parser(
        "record",
        help="Registry'ye kayıt yazar (şema + kopuk referans denetimiyle)",
    )
    p_record.add_argument(
        "registry",
        help="Registry adı (research_questions, hypotheses, claims_registry, "
             "citations, gap_registry, findings_registry, …)",
    )
    p_record.add_argument(
        "--file",
        help="Ajanın ürettiği JSON dosyası (tek kayıt nesnesi ya da dizi)",
    )
    p_record.set_defaults(func=cmd_record)

    # thesis:audit
    p_audit = sub.add_parser("audit", help="Tez denetimi")
    # Secenekler tools.atw.audit.DESTEKLENEN_TURLER ile ayni olmali; liste
    # ayrisirsa CLI bir turu kabul edip modul sessizce atlar.
    p_audit.add_argument("--type", choices=["citation", "methodology", "consistency", "integrity", "evidence", "all"], default="all")
    p_audit.set_defaults(func=cmd_audit)

    # thesis:exclude
    p_exclude = sub.add_parser(
        "exclude",
        help="Kaynak kümesinden kayıt ele (PRISMA tarama kararı)",
    )
    p_exclude.add_argument(
        "ids",
        nargs="+",
        metavar="SRC-ID",
        help="Kaynak kümesinden çıkarılacak kimlikler",
    )
    p_exclude.add_argument(
        "--reason",
        required=True,
        help="Eleme gerekçesi — arama kayıtlarının `exclusion_reasons`'ına yazılır",
    )
    p_exclude.set_defaults(func=cmd_exclude)

    # thesis:status
    p_status = sub.add_parser("status", help="Tez durumu özeti")
    p_status.set_defaults(func=cmd_status)

    # thesis:export
    p_export = sub.add_parser("export", help="Tez dışa aktar")
    p_export.add_argument("--format", choices=["md", "docx", "pdf"], default="md")
    p_export.add_argument(
        "--out",
        help="Çıktı dizini (varsayılan: tez durumunun bulunduğu dizin)",
    )
    p_export.set_defaults(func=cmd_export)

    return parser


def main() -> int:
    # Sıralama önemli: çıktı kodlaması, argparse'nin hata çıktısından ve
    # her komutun `print` çağrısından ONCE ayarlanmalıdır.
    _cikti_kodlamasini_ayarla()
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())