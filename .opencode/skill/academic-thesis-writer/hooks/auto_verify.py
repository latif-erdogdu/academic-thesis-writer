#!/usr/bin/env python3
"""Hook: Yeni kaynak eklendiğinde otomatik DOI/bibliyografik doğrulama."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main(file_path: str):
    repo_root = Path(__file__).resolve().parents[3]
    source_file = repo_root / file_path

    if not source_file.exists():
        print(f"⚠️  Dosya yok: {source_file}")
        return 0

    try:
        data = json.loads(source_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"❌ Geçersiz JSON: {e}")
        return 1

    # Verification alanı var mı kontrol et
    verification = data.get("verification")
    if not verification:
        print(f"⚠️  verification alanı yok, pending olarak işaretleniyor")
        data["verification"] = {
            "status": "pending",
            "bibliographic_match": 0.0,
            "verified_at": "",
            "verification_sources": ["manual"]
        }
        source_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0

    # Eğer zaten verified ise atla
    if verification.get("status") == "verified":
        print(f"✅ Zaten verified: {data.get('id')}")
        return 0

    # DOI varsa Crossref/OpenAlex sorgula (stub - gerçek implementasyon tools/source_verify'da)
    doi = data.get("doi", "")
    if doi:
        print(f"🔍 DOI doğrulanıyor: {doi}")
        # Burada gerçek API çağrısı yapılacak (tools/source_verify modülü)
        # Şimdilik placeholder:
        verification["status"] = "pending"
        verification["verification_sources"] = ["crossref", "openalex"]
        source_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"📝 Doğrulama başlatıldı (pending): {data.get('id')}")
    else:
        print(f"⚠️  DOI yok, manuel doğrulama bekliyor: {data.get('id')}")
        verification["status"] = "pending"
        verification["verification_sources"] = ["manual"]
        source_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python auto_verify.py <dosya_yolu>")
        exit(1)
    exit(main(sys.argv[1]))