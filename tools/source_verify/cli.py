"""CLI wrapper for source_verify."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.source_verify import verify_source, verify_sources_batch, SourceVerifier


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="source-verify",
        description="Kaynak doğrulama (DOI, bibliyografik, retraksiyon)"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # verify komutu
    p_verify = sub.add_parser("verify", help="Kaynak doğrula")
    p_verify.add_argument("--doi", help="DOI ile doğrula")
    p_verify.add_argument("--pmid", help="PMID ile doğrula")
    p_verify.add_argument("--title", help="Başlık (DOI yoksa)")
    p_verify.add_argument("--authors", help="Yazarlar (virgülle ayrılmış)")
    p_verify.add_argument("--year", type=int, help="Yıl")
    p_verify.add_argument("--journal", help="Dergi adı")
    p_verify.add_argument("--output", help="Çıktı dosyası (JSON)")

    # batch-verify komutu
    p_batch = sub.add_parser("batch", help="Toplu doğrulama (source.json kayıtları)")
    p_batch.add_argument("--state", default="thesis_state.json", help="Tez durum dosyası")
    p_batch.add_argument("--pending-only", action="store_true", help="Sadece pending olanlar")
    p_batch.add_argument("--output", help="Çıktı dosyası (JSON)")

    args = parser.parse_args()

    if args.cmd == "verify":
        return cmd_verify(args)
    elif args.cmd == "batch":
        return cmd_batch(args)
    else:
        parser.print_help()
        return 1


def cmd_verify(args) -> int:
    """Tek kaynak doğrula."""
    # Source record oluştur
    source_record = {}
    if args.doi:
        source_record["doi"] = args.doi
    if args.pmid:
        source_record["pmid"] = args.pmid
    if args.title:
        source_record["title"] = args.title
    if args.authors:
        source_record["authors"] = [a.strip() for a in args.authors.split(",")]
    if args.year:
        source_record["year"] = args.year
    if args.journal:
        source_record["journal"] = args.journal

    if not any([args.doi, args.pmid, args.title]):
        print("Hata: En az --doi, --pmid veya --title gerekli")
        return 1

    # ID yoksa geçici oluştur
    if "id" not in source_record:
        from tools.atw.ids import format_id
        source_record["id"] = format_id("SRC", 999)

    verifier = SourceVerifier()
    result = verifier.verify_source(source_record)

    # Çıktı
    output = {
        "source_id": result.source_id,
        "status": result.status,
        "bibliographic_match": result.bibliographic_match,
        "verified_at": result.verified_at,
        "verification_sources": result.verification_sources,
        "verification_details": result.verification_details,
        "retraction_info": result.retraction_info,
        "correction_info": result.correction_info,
    }

    if args.output:
        Path(args.output).write_text(json.dumps(output, ensure_ascii=False, indent=2))
        print(f"Sonuç kaydedildi: {args.output}")
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))

    print(f"\nDurum: {result.status}")
    print(f"Skor: {result.bibliographic_match}")
    print(f"Kaynaklar: {result.verification_sources}")
    return 0


def cmd_batch(args) -> int:
    """Toplu doğrulama."""
    state_file = Path(args.state)
    if not state_file.exists():
        print(f"Hata: {state_file} bulunamadı")
        return 1

    import json
    state = json.loads(state_file.read_text(encoding="utf-8"))

    # Filtrele
    sources = state.get("sources", [])
    if args.pending_only:
        sources = [s for s in sources if s.get("verification", {}).get("status") == "pending"]

    if not sources:
        print("Doğrulanacak kaynak yok")
        return 0

    print(f"{len(sources)} kaynak doğrulanıyor...")
    verifier = SourceVerifier()
    results = verifier.verify_batch(sources)

    # Sonuçları yazdır
    verified = sum(1 for r in r if r.status == "verified")
    unverified = sum(1 for r in r if r.status == "unverified")
    retracted = sum(1 for r in r if r.status == "retracted")
    corrected = sum(1 for r in r if r.status == "corrected")
    pending = sum(1 for r in r if r.status == "pending")

    print(f"\nÖzet:")
    print(f"  Verified: {verified}")
    print(f"  Unverified: {unverified}")
    print(f"  Retracted: {retracted}")
    print(f"  Corrected: {corrected}")
    print(f"  Pending: {pending}")

    if args.output:
        output_data = {
            "results": [
                {
                    "source_id": r.source_id,
                    "status": r.status,
                    "bibliographic_match": r.bibliographic_match,
                    "verification_sources": r.verification_sources,
                }
                for r in r
            ],
            "summary": {
                "verified": verified,
                "unverified": unverified,
                "retracted": retracted,
                "corrected": corrected,
                "pending": pending,
            }
        }
        Path(args.output).write_text(json.dumps(output_data, ensure_ascii=False, indent=2))
        print(f"Sonuçlar kaydedildi: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())