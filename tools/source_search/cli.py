"""CLI wrapper for source_search."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .search_run import run_systematic_search, SystematicSearchOrchestrator, PICO, parse_pico


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="source-search",
        description="Sistematik kaynak arama (Crossref, OpenAlex, Semantic Scholar, PubMed)"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # search komutu
    p_search = sub.add_parser("search", help="Kaynak arama yap")
    p_search.add_argument("--rq", required=True, help="Araştırma sorusu ID (RQ-XXX)")
    p_search.add_argument("--pico", help="PICO metni (RQ verilmemişse zorunlu)")
    p_search.add_argument("--databases", default="crossref,openalex,pubmed,semantic_scholar",
                          help="Veritabanları (virgülle ayrılmış)")
    p_search.add_argument("--year-from", type=int, help="Başlangıç yılı")
    p_search.add_argument("--year-to", type=int, help="Bitiş yılı")
    p_search.add_argument("--max-results", type=int, default=100, help="Veritabanı başına max sonuç")
    p_search.add_argument("--output", help="Çıktı dosyası (JSON)")

    # build-query komutu
    p_query = sub.add_parser("build-query", help="PICO'dan Boolean query oluştur")
    p_query.add_argument("--pico", required=True, help="PICO metni")
    p_query.add_argument("--database", choices=["crossref", "openalex", "pubmed", "semantic_scholar", "all"],
                         default="all", help="Hedef veritabanı")

    args = parser.parse_args()

    if args.cmd == "search":
        return cmd_search(args)
    elif args.cmd == "build-query":
        return cmd_build_query(args)
    else:
        parser.print_help()
        return 1


def cmd_search(args) -> int:
    pico = parse_pico(args.pico) if args.pico else None

    if not args.rq and not pico:
        print("Hata: --rq veya --pico zorunlu")
        return 1

    databases = [db.strip() for db in args.databases.split(",")]

    result = run_systematic_search(
        pico=pico or args.rq,
        databases=databases,
        year_from=args.year_from,
        year_to=args.year_to,
        max_results_per_db=args.max_results,
    )

    # Çıktı
    output_data = {
        "search_run_id": result.search_run_id,
        "timestamp": result.timestamp,
        "databases": result.databases_searched,
        "prisma_flow": result.prisma_flow,
        "deduplication": result.deduplication.stats,
        "included_count": len(result.included_source_ids),
    }

    if args.output:
        Path(args.output).write_text(json.dumps(output_data, ensure_ascii=False, indent=2))
        print(f"Sonuç kaydedildi: {args.output}")
    else:
        print(json.dumps(output_data, ensure_ascii=False, indent=2))

    print(f"\nArama tamamlandı: {result.search_run_id}")
    print(f"  Kayıtlar: {result.prisma_flow['records_identified']}")
    print(f"  Kopya kaldırıldı: {result.deduplication.stats['removed']}")
    print(f"  Dahil edilen: {len(result.included_source_ids)}")

    return 0


def cmd_build_query(args) -> int:
    pico = parse_pico(args.pico)

    if args.database == "all":
        from .query_builder import build_multi_database_queries
        queries = build_multi_database_queries(pico)
        for db, query in queries.items():
            print(f"\n=== {db.upper()} ===")
            print(f"Boolean: {query.boolean_string}")
            print(f"Synonyms: {query.synonyms_used}")
    else:
        from .query_builder import build_boolean_query
        query = build_boolean_query(pico, database=args.database)
        print(f"Boolean: {query.boolean_string}")
        print(f"Synonyms: {query.synonyms_used}")

    return 0


if __name__ == "__main__":
    sys.exit(main())