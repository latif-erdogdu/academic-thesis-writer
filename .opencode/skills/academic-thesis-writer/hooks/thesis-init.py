#!/usr/bin/env python3
"""Hook: Yeni tez başlatıldığında thesis_state.json oluştur.

DURUMUN TEK KAYNAĞI: boş durum, tools.atw.state.empty_state() ile üretilir.
Daha önce bu betik `schemas/thesis_state.json` dosyasını kopyalıyordu; ancak o
dosya bir JSON *şema* (draft 2020-12), bir durum örneği değil. Kopyalanan dosya
`$schema`, `$id`, `properties`, `required` anahtarlarıyla bir şema olarak
kalıyordu: doğrulanabilir bir tez durumu değil, 7 onay kapısının hiçbiri yok.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# parents[4] = depo kökü. Bu değer hem sys.path'e hem de varsayılan
# thesis_state.json konumuna giriyor; parents[3] (.opencode) kullanılırsa
# tez durumu .opencode/thesis_state.json altına yazılırdı.
REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from tools.atw.state import empty_state  # noqa: E402


def main(state_path: Path | str | None = None) -> int:
    """thesis_state.json dosyasini olusturur; varsa dokunmaz.

    state_path verilmezse depo kokundeki thesis_state.json kullanilir.
    Test edilebilirlik icin parametre alir; hook olarak cagrilirken verilmez.
    """
    hedef = Path(state_path) if state_path is not None else REPO_ROOT / "thesis_state.json"

    if hedef.exists():
        print(f"⏭  thesis_state.json zaten mevcut: {hedef}")
        return 0

    durum = empty_state("THESIS-2026-001", "Yeni Tez")
    durum.pop("updated_at", None)  # henüz yazılmadı; zaman damgası anlamsız

    try:
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(
            json.dumps(durum, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    except OSError as hata:
        print(f"❌ thesis_state.json yazılamadı: {hedef} — {hata}")
        return 1

    onay_kapilari = sorted(durum["human_approvals"])
    print(f"✅ thesis_state.json oluşturuldu: {hedef}")
    print(f"   {len(onay_kapilari)} onay kapısı kapalı başladı: {', '.join(onay_kapilari)}")
    return 0


if __name__ == "__main__":
    exit(main())
