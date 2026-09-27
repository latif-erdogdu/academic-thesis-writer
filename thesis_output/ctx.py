# -*- coding: utf-8 -*-
"""Belirsiz ASCII token'lerin baglamini goster."""
from __future__ import annotations

import re
import sys
from pathlib import Path

KUTU = Path(__file__).resolve().parent
DOSYALAR = ["content_a", "content_b", "content_c", "content_d"]

BELIRSIZ = sys.argv[1:]


def main() -> int:
    for ad in DOSYALAR:
        yol = KUTU / f"{ad}.py"
        if not yol.exists():
            continue
        satirlar = yol.read_text(encoding="utf-8").splitlines()
        for no, satir in enumerate(satirlar, 1):
            for tok in BELIRSIZ:
                if re.search(rf"\b{re.escape(tok)}\b", satir):
                    print(f"{ad}.py:{no}  [{tok}]  {satir.strip()[:150]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
