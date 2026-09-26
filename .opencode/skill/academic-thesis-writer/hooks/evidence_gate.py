#!/usr/bin/env python3
"""Hook: Bölüm yazımından önce Evidence Gate kontrolü."""
from __future__ import annotations

import sys
from pathlib import Path


def main(file_path: str):
    repo_root = Path(__file__).resolve().parents[3]
    chapter_file = repo_root / file_path

    if not chapter_file.exists():
        print(f"⚠️  Dosya yok: {chapter_file}")
        return 0

    # Basit kontrol: bölüm dosyasında claim/evidence/source referansları var mı?
    content = chapter_file.read_text(encoding="utf-8")

    # Claim referansı kontrolü (CLM-XXX)
    import re
    claims = re.findall(r"CLM-\d{3,}", content)
    evidence = re.findall(r"EVD-\d{3,}", content)
    sources = re.findall(r"SRC-\d{3,}", content)

    if not claims:
        print(f"⚠️  Evidence Gate: {file_path} — hiçbir claim (CLM-XXX) referansı yok")
        print("   Yazım kapısı: Her paragraf en az bir iddiaya (CLM-XXX) atıf yapmalı")
        return 1

    if not evidence and not sources:
        print(f"⚠️  Evidence Gate: {file_path} — claimler var ama kanıt (EVD-XXX) veya kaynak (SRC-XXX) yok")
        print("   Yazım kapısı: İddialar kanıt veya kaynakla desteklenmeli")
        return 1

    print(f"✅ Evidence Gate geçti: {len(claims)} claim, {len(evidence)} kanıt, {len(sources)} kaynak")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python evidence_gate.py <dosya_yolu>")
        exit(1)
    exit(main(sys.argv[1]))