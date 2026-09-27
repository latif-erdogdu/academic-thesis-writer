#!/usr/bin/env python3
"""CLI komutları: thesis:new, thesis:search, thesis:verify, thesis:extract, thesis:write, thesis:audit, thesis:status, thesis:export."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from tools.atw.state import empty_state


REPO_ROOT = Path(__file__).resolve().parents[3]  # tools/atw/cli -> repo root


def load_state() -> dict:
    """thesis_state.json yükle."""
    state_file = REPO_ROOT / "thesis_state.json"
    if not state_file.exists():
        return empty_state("THESIS-2026-001", "Yeni Tez")
    return json.loads(state_file.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    """thesis_state.json kaydet."""
    state_file = REPO_ROOT / "thesis_state.json"
    state["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    state["version"] = state.get("version", 0) + 1
    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_new(args) -> int:
    """Yeni tez başlat."""
    state = empty_state(args.id, args.title)
    save_state(state)
    print(f"✅ Yeni tez oluşturuldu: {args.id} — {args.title}")
    print(f"📄 thesis_state.json güncellendi")
    return 0


def cmd_search(args) -> int:
    """Kaynak arama başlat."""
    from tools.source_search import run_systematic_search, PICO, parse_pico

    state = load_state()

    # RQ'den PICO oluştur veya state'den al
    pico = None
    if hasattr(args, 'pico') and args.pico:
        pico = parse_pico(args.pico)
    elif args.rq:
        # State'den RQ'yi bul ve PICO'ya çevir
        rq_id = args.rq
        for rq in state.get("research_questions", []):
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
    state["search_runs"].append(result.to_dict())
    for db_result in result.database_results:
        for record in db_result.records:
            if "id" in record and record["id"]:
                state["sources"].append(record)
    save_state(state)

    return 0


def cmd_verify(args) -> int:
    """Kaynak doğrulama."""
    state = load_state()
    print("🔍 Kaynak doğrulama başlatılıyor...")
    print("⚠️  Henüz implemente edilmedi (tools/source_verify)")
    return 0


def cmd_extract(args) -> int:
    """PDF'ten kanıt çıkar."""
    from tools.pdf_extract import find_evidence_for_claim

    state = load_state()

    if _kayit_bul(state.get("sources", []), args.source) is None:
        print(f"❌ Kaynak bulunamadı: {args.source}")
        return 1

    iddia = _kayit_bul(state.get("claims_registry", []), args.claim)
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

    sira = _sonraki_kanit_sirasi(state.get("evidence_registry", []))
    for bulgu in bulgular:
        kayit = _kanit_kaydi(bulgu, args.source, args.claim, sira)
        state["evidence_registry"].append(kayit)
        konum = f"s.{kayit['location']['page']}" if kayit["location"]["page"] else "s.?"
        print(f"   {kayit['id']}  {konum}  ({kayit['strength']})")
        sira += 1

    save_state(state)
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


def cmd_write(args) -> int:
    """Bölüm yaz."""
    print(f"✍️  Bölüm yazımı: Chapter={args.chapter}, RQ={args.rq}")
    print("⚠️  Henüz implemente edilmedi (agent/writer)")
    return 0


def cmd_audit(args) -> int:
    """Tez denetimi."""
    audit_type = args.type or "all"
    print(f"🔍 Denetim başlatılıyor: {audit_type}")
    print("⚠️  Henüz implemente edilmedi (agents/*-auditor)")
    return 0


def cmd_status(args) -> int:
    """Tez durumu özeti."""
    state = load_state()
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
    return 0


def cmd_export(args) -> int:
    """Tez dışa aktar."""
    fmt = args.format or "md"
    print(f"📤 Dışa aktarma: format={fmt}")
    print("⚠️  Henüz implemente edilmedi")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="thesis", description="Akademik tez yazım CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # thesis:new
    p_new = sub.add_parser("new", help="Yeni tez başlat")
    p_new.add_argument("id", help="Tez ID (örn: THESIS-2026-001)")
    p_new.add_argument("title", help="Tez başlığı")
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
    p_audit.add_argument("--type", choices=["citation", "methodology", "consistency", "integrity", "all"], default="all")
    p_audit.set_defaults(func=cmd_audit)

    # thesis:status
    p_status = sub.add_parser("status", help="Tez durumu özeti")
    p_status.set_defaults(func=cmd_status)

    # thesis:export
    p_export = sub.add_parser("export", help="Tez dışa aktar")
    p_export.add_argument("--format", choices=["md", "docx", "pdf"], default="md")
    p_export.set_defaults(func=cmd_export)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())