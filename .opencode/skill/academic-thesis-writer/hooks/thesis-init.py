#!/usr/bin/env python3
"""Hook: Yeni tez başlatıldığında thesis_state.json şablonu kopyala."""
from __future__ import annotations

import shutil
from pathlib import Path


def main():
    repo_root = Path(__file__).resolve().parents[3]  # .opencode/skill/.../hooks -> repo root
    thesis_state = repo_root / "thesis_state.json"
    template = repo_root / "schemas" / "thesis_state.json"

    if thesis_state.exists():
        print(f"⏭  thesis_state.json zaten mevcut: {thesis_state}")
        return 0

    if not template.exists():
        print(f"❌ Şablon bulunamadı: {template}")
        return 1

    shutil.copy2(template, thesis_state)
    print(f"✅ thesis_state.json oluşturuldu: {thesis_state}")
    return 0


if __name__ == "__main__":
    exit(main())