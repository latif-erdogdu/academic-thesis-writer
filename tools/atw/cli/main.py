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
from tools.atw.state import empty_state


REPO_ROOT = Path(__file__).resolve().parents[3]  # tools/atw/cli -> repo root

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
    state_file = REPO_ROOT / "thesis_state.json"
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
    """thesis_state.json kaydet."""
    state_file = REPO_ROOT / "thesis_state.json"
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
    state_file = REPO_ROOT / "thesis_state.json"
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
    """Kaynak arama başlat."""
    from tools.source_search import run_systematic_search, PICO, parse_pico

    # RQ'den PICO oluştur veya state'den al
    pico = None
    if hasattr(args, 'pico') and args.pico:
        pico = parse_pico(args.pico)
    elif args.rq:
        # State'den RQ'yi bul ve PICO'ya çevir
        rq_id = args.rq
        for rq in durum.get("research_questions", []):
            if rq.get("id") == rq_id:
                # RQ metninden PICO parse et
                pico = parse_pico(rq.get("text", ""))
                break
        if not pico:
            print(f"⚠️  RQ {args.rq} bulunamadı, boş PICO ile devam ediliyor")
            pico = PICO()

    databases = [db.strip() for db in args.databases.split(",")]

    result = run_systematic_search(
        pico=pico,
        databases=[db.strip() for db in args.databases.split(",")],
        year_from=args.year_from,
        year_to=args.year_to,
        max_results_per_db=args.max_results,
    )

    print(f"\n✅ Arama tamamlandı: {result.search_run_id}")
    print(f"   Kayıtlar: {result.prisma_flow['records_identified']}")
    print(f"   Kopya kaldırıldı: {result.deduplication.stats['removed']}")
    print(f"   Dahil edilen: {len(result.included_source_ids)}")

    # State'e kaydet
    durum["search_runs"].append(result.to_dict())
    for db_result in result.database_results:
        for record in db_result.records:
            if "id" in record and record["id"]:
                durum["sources"].append(record)
    save_state(durum)

    return 0


@_durum_gerekir
def cmd_verify(args, durum) -> int:
    """Kaynak doğrulama."""
    print("🔍 Kaynak doğrulama başlatılıyor...")
    print("⚠️  Henüz implemente edilmedi (tools/source_verify)")
    return 0


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
    pdf_yolu = Path(args.pdf)
    if not pdf_yolu.is_absolute():
        pdf_yolu = REPO_ROOT / pdf_yolu
    if not pdf_yolu.exists():
        print(f"❌ PDF bulunamadı: {pdf_yolu}")
        return 1

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
            "paragraph": bulgu.paragraph_index,
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
    """Bölüm yaz.

    Önce 'methodology' kapısı sorulur: yazım yöntem onayından geçmeden
    yapılırsa, sonradan yöntem değişince tüm bölümler geçersiz olur.
    """
    if not _kapi_raporu(durum, "methodology"):
        return CIKIS_SORUN

    print(f"✍️  Bölüm yazımı: Chapter={args.chapter}, RQ={args.rq}")
    print("⚠️  Henüz implemente edilmedi (agent/writer)")
    return 0


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
    """Tez dışa aktar.

    Dışa aktarma, tezin İNSAN ONAYLI bitmiş halini paylaşmak demektir.
    Bu yüzden en katı kapı sorulur: 'final_thesis' — bütünlük, kanıtsız
    iddia ve retraksiyon denetimi de burada devreye girer.
    """
    if not _kapi_raporu(durum, "final_thesis"):
        return CIKIS_SORUN

    fmt = args.format or "md"
    print(f"📤 Dışa aktarma: format={fmt}")
    print("⚠️  Henüz implemente edilmedi")
    return 0


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
    p_verify.add_argument("--all", action="store_true", help="Tüm bekleyen kaynakları doğrula")
    p_verify.set_defaults(func=cmd_verify)

    # thesis:extract
    p_extract = sub.add_parser("extract", help="PDF'ten kanıt çıkar")
    p_extract.add_argument("source", help="Kaynak ID (SRC-XXX)")
    p_extract.add_argument("--claim", required=True, help="Hedef iddia ID (CLM-XXX)")
    p_extract.add_argument("--pdf", help="Yerel PDF dosya yolu (source.json'da yol alanı yok)")
    p_extract.set_defaults(func=cmd_extract)

    # thesis:write
    p_write = sub.add_parser("write", help="Bölüm yaz")
    p_write.add_argument("chapter", help="Bölüm ID (CH-XXX)")
    p_write.add_argument("--rq", required=True, help="Araştırma sorusu ID (RQ-XXX)")
    p_write.set_defaults(func=cmd_write)

    # thesis:audit
    p_audit = sub.add_parser("audit", help="Tez denetimi")
    # Secenekler tools.atw.audit.DESTEKLENEN_TURLER ile ayni olmali; liste
    # ayrisirsa CLI bir turu kabul edip modul sessizce atlar.
    p_audit.add_argument("--type", choices=["citation", "methodology", "consistency", "integrity", "evidence", "all"], default="all")
    p_audit.set_defaults(func=cmd_audit)

    # thesis:status
    p_status = sub.add_parser("status", help="Tez durumu özeti")
    p_status.set_defaults(func=cmd_status)

    # thesis:export
    p_export = sub.add_parser("export", help="Tez dışa aktar")
    p_export.add_argument("--format", choices=["md", "docx", "pdf"], default="md")
    p_export.set_defaults(func=cmd_export)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())