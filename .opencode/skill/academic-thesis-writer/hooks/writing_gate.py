#!/usr/bin/env python3
"""Hook: Atıf ekleme sonrası Writing Gate (APA 7 format + bütünlük kontrolü)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# parents[4] = depo kökü. parents[3] (.opencode) kullanılırsa nispi yollar
# .opencode/ altında aranır, bulunamaz ve betik sessizce 0 döner.
REPO_ROOT = Path(__file__).resolve().parents[4]


def _cozumle(yol: str) -> Path:
    """Nispi yolları depo köküne göre çözümler; mutlak yollara dokunmaz."""
    aday = Path(yol)
    return aday if aday.is_absolute() else REPO_ROOT / aday


def main(file_path: str):
    citation_file = _cozumle(file_path)

    if not citation_file.exists():
        print(f"⚠️  Dosya yok: {citation_file}")
        return 0

    try:
        data = json.loads(citation_file.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        print(f"❌ Geçersiz JSON: {e}")
        return 1

    # citation.json formatı: id, source_id, paragraph_id, style
    required = {"id", "source_id", "paragraph_id", "style"}
    missing = required - set(data.keys())
    if missing:
        print(f"❌ Eksik alanlar: {missing}")
        return 1

    # APA 7 stil kontrolü
    if data.get("style") != "apa7":
        print(f"⚠️  Stil 'apa7' değil: {data.get('style')} (APA 7 varsayılan)")

    # source_id formatı kontrolü
    if not re.match(r"^SRC-\d{3,}$", data.get("source_id", "")):
        print(f"⚠️  source_id formatı yanlış: {data.get('source_id')}")

    if not re.match(r"^P-\d{3,}$", data.get("paragraph_id", "")):
        print(f"⚠️  paragraph_id formatı yanlış: {data.get('paragraph_id')}")

    # source_id thesis_state.json'da var mı kontrolü
    #
    # Bu kontrol bir zamanlar HİÇ ÇALIŞMIYORDU: yol `parents[3] /
    # "thesis_state.json"` idi, yani `.opencode/thesis_state.json`. O dosya
    # hiç var olmadığı için `if ... .exists()` her zaman False dönüyor ve
    # denetim sessizce atlanıyordu. Sonuç: tezde olmayan `SRC-999` gibi
    # uydurma bir source_id taşıyan atıf Writing Gate'i geçiyordu.
    thesis_state_file = REPO_ROOT / "thesis_state.json"
    if thesis_state_file.exists():
        thesis_state = json.loads(thesis_state_file.read_text(encoding="utf-8-sig"))
        source_ids = {s.get("id") for s in thesis_state.get("sources", [])}
        if data.get("source_id") not in source_ids:
            print(f"⚠️  source_id thesis_state.json'da yok: {data.get('source_id')}")
            return 1

    print(f"✅ Writing Gate geçti: {data.get('id')}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python writing_gate.py <dosya_yolu>")
        exit(1)
    exit(main(sys.argv[1]))