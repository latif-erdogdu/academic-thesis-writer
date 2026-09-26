"""CLI wrapper for pdf_extract."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.pdf_extract import (
    download_pdf,
    check_unpaywall_oa,
    extract_text_from_pdf,
    find_evidence_for_claim,
    EvidenceExtractor,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="pdf-extract",
        description="PDF'ten kanıt çıkarma (sayfa/bölüm düzeyinde, claim-evidence linking)"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # extract-text komutu
    p_extract = sub.add_parser("extract-text", help="PDF'ten metin çıkar")
    p_extract.add_argument("pdf", help="PDF dosya yolu")
    p_extract.add_argument("--output", help="Çıktı dosyası (JSON)")
    p_extract.add_argument("--pages", action="store_true", help="Sayfa bazlı çıktı")

    # extract-evidence komutu
    p_evidence = sub.add_parser("extract-evidence", help="İddia için kanıt bul")
    p_evidence.add_argument("pdf", help="PDF dosya yolu")
    p_evidence.add_argument("--claim", required=True, help="İddia metni")
    p_evidence.add_argument("--claim-id", help="İddia ID (CLM-XXX)")
    p_evidence.add_argument("--keywords", help="Anahtar kelimeler (virgülle ayrılmış)")
    p_evidence.add_argument("--top-k", type=int, default=5, help="En iyi K sonuç")
    p_evidence.add_argument("--min-sim", type=float, default=0.3, help="Min benzerlik eşiği")
    p_evidence.add_argument("--output", help="Çıktı dosyası (JSON)")

    # download komutu
    p_download = sub.add_parser("download", help="PDF indir (OA kontrolü ile)")
    p_download.add_argument("--doi", help="DOI")
    p_download.add_argument("--url", help="Kaynak URL")
    p_download.add_argument("--output-dir", default="downloads/pdfs", help="İndirme dizini")
    p_download.add_argument("--output", help="Çıktı dosyası (JSON)")

    # oa-check komutu
    p_oa = sub.add_parser("oa-check", help="Unpaywall OA durumu kontrol et")
    p_oa.add_argument("--doi", required=True, help="DOI")
    p_oa.add_argument("--output", help="Çıktı dosyası (JSON)")

    # batch-evidence komutu
    p_batch = sub.add_parser("batch-evidence", help="Toplu kanıt çıkarma (state dosyasından)")
    p_batch.add_argument("--state", default="thesis_state.json", help="Tez durum dosyası")
    p_batch.add_argument("--claim-id", help="Belirli bir iddia (CLM-XXX)")
    p_batch.add_argument("--output", help="Çıktı dosyası (JSON)")

    args = parser.parse_args()

    if args.cmd == "extract-text":
        return cmd_extract_text(args)
    elif args.cmd == "extract-evidence":
        return cmd_extract_evidence(args)
    elif args.cmd == "download":
        return cmd_download(args)
    elif args.cmd == "oa-check":
        return cmd_oa_check(args)
    elif args.cmd == "batch-evidence":
        return cmd_batch_evidence(args)
    else:
        parser.print_help()
        return 1


def cmd_extract_text(args) -> int:
    """PDF'ten metin çıkar."""
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Hata: PDF dosyası bulunamadı: {pdf_path}")
        return 1

    if args.pages:
        pages = extract_text_from_pdf_with_pages(pdf_path)
        result = [{"page": p, "text": t} for p, t in pages]
    else:
        text = extract_text_from_pdf(pdf_path)
        result = {"text": text, "page_count": len(text.split("\n")) if text else 0}

    if args.output:
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"Sonuç kaydedildi: {args.output}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0


def cmd_extract_evidence(args) -> int:
    """İddia için kanıt bul."""
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Hata: PDF dosyası bulunamadı: {pdf_path}")
        return 1

    keywords = [k.strip() for k in args.keywords.split(",")] if args.keywords else None

    try:
        evidence_list = find_evidence_for_claim(
            pdf_path=pdf_path,
            claim_text=args.claim,
            claim_keywords=keywords,
            top_k=args.top_k,
            min_similarity=args.min_sim,
        )
    except Exception as e:
        print(f"Hata: {e}")
        return 1

    # Çıktı formatı
    result = {
        "claim": args.claim,
        "claim_id": args.claim_id,
        "evidence": [
            {
                "text": e.text,
                "page": e.page,
                "section": e.section,
                "subsection": e.subsection,
                "paragraph_index": e.paragraph_index,
                "evidence_type": e.evidence_type,
                "strength": e.strength,
                "supports_claim": e.supports_claim,
                "confidence": e.confidence,
            }
            for e in evidence_list
        ],
    }

    if args.output:
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"Sonuç kaydedildi: {args.output}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    print(f"\nBulunan kanıt sayısı: {len(evidence_list)}")
    return 0


def cmd_download(args) -> int:
    """PDF indir (OA kontrolü ile)."""
    if not args.doi and not args.url:
        print("Hata: --doi veya --url gerekli")
        return 1

    from tools.pdf_extract.downloader import PDFDownloader

    downloader = PDFDownloader(download_dir=args.output_dir)

    if args.doi:
        result = downloader.download_with_oa_check(args.doi, args.url or "")
    else:
        result = downloader.download(args.url)

    output = {
        "success": result.success,
        "file_path": str(result.file_path) if result.file_path else None,
        "file_size": result.file_size,
        "content_type": result.content_type,
        "source_url": result.source_url,
        "is_open_access": result.is_open_access,
        "oa_source": result.oa_source,
        "error": result.error,
        "download_time_ms": result.download_time_ms,
    }

    if args.output:
        Path(args.output).write_text(json.dumps(output, ensure_ascii=False, indent=2))
        print(f"Sonuç kaydedildi: {args.output}")
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))

    if not result.success:
        print(f"Hata: {result.error}")
        return 1

    return 0


def cmd_oa_check(args) -> int:
    """Unpaywall OA kontrolü."""
    from tools.pdf_extract.downloader import check_unpaywall_oa

    oa_status = check_unpaywall_oa(args.doi)

    if oa_status is None:
        print(f"Hata: Unpaywall sorgusu başarısız: {args.doi}")
        return 1

    output = {
        "doi": args.doi,
        "is_oa": oa_status.is_oa,
        "oa_status": oa_status.oa_status,
        "oa_url": oa_status.oa_url,
        "license": oa_status.license,
        "version": oa_status.version,
        "source": oa_status.source,
    }

    if args.output:
        Path(args.output).write_text(json.dumps(output, ensure_ascii=False, indent=2))
        print(f"Sonuç kaydedildi: {args.output}")
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))

    return 0


def cmd_batch_evidence(args) -> int:
    """State dosyasından toplu kanıt çıkarma."""
    state_file = Path(args.state)
    if not state_file.exists():
        print(f"Hata: {state_file} bulunamadı")
        return 1

    with open(state_file, "r", encoding="utf-8") as f:
        state = json.load(f)

    # Filtrele
    claims = state.get("claims_registry", [])
    if args.claim_id:
        claims = [c for c in claims if c.get("id") == args.claim_id]

    if not claims:
        print("İşlenecek iddia yok")
        return 0

    # Sources registry
    sources = state.get("sources", [])

    print(f"{len(claims)} iddia işlenecek...")
    all_evidence = []

    for claim in claims:
        claim_id = claim.get("id")
        claim_text = claim.get("text", "")
        if not claim_text:
            continue

        # İlgili kaynakları bul
        claim_sources = claim.get("sources", [])
        claim_evidence_ids = claim.get("evidence_ids", [])

        # Her kaynak için PDF'ten kanıt bul
        for src_id in claim_sources:
            source = next((s for s in sources if s.get("id") == src_id), None)
            if not source:
                continue

            # PDF dosyası var mı kontrol et (downloads/pdfs/SRC-XXX.pdf)
            pdf_path = Path(f"downloads/pdfs/{src_id}.pdf")
            if not pdf_path.exists():
                print(f"  ⚠️  PDF yok: {src_id} (indirilmedi)")
                continue

            print(f"  İşleniyor: {claim_id} <- {src_id}")
            try:
                evidence_list = find_evidence_for_claim(
                    pdf_path=pdf_path,
                    claim_text=claim_text,
                    top_k=5,
                    min_similarity=0.3,
                )
                for ev in evidence_list:
                    ev.supports_claim = claim_id
                    all_evidence.append({
                        "claim_id": claim_id,
                        "source_id": src_id,
                        "text": ev.text,
                        "page": ev.page,
                        "section": ev.section,
                        "subsection": ev.subsection,
                        "confidence": ev.confidence,
                    })
            except Exception as e:
                print(f"  ❌ Hata ({src_id}): {e}")

    # Sonuçları state'e ekle
    if all_evidence:
        # Mevcut evidence_registry'ye ekle
        existing = state.get("evidence_registry", [])
        # ID çakışmasını önle
        max_id = 0
        for ev in existing:
            try:
                num = int(ev.get("id", "EVD-000").split("-")[1])
                max_id = max(max_id, num)
            except (ValueError, IndexError):
                pass

        for i, ev in enumerate(all_evidence):
            max_id += 1
            ev["id"] = f"EVD-{max_id:03d}"
            ev["extracted_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(timespec="seconds")
            ev["extraction_method"] = "pdfplumber+tfidf"
            ev["verified"] = False
            existing.append(ev)

        state["evidence_registry"] = existing
        state["updated_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(timespec="seconds")

        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

        print(f"\n✅ {len(all_evidence)} kanıt eklendi, state güncellendi: {state_file}")

    if args.output:
        output_data = {"evidence": all_evidence}
        Path(args.output).write_text(json.dumps(output_data, ensure_ascii=False, indent=2))
        print(f"Sonuç kaydedildi: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())