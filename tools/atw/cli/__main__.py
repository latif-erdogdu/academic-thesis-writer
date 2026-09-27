"""Paket giris noktasi: `python -m tools.atw.cli <alt_komut>`.

Bu dosya olmadan `python -m tools.atw.cli` "is a package and cannot be
directly executed" hatasi verir. skill.yaml'daki HER komut bu bicimi
kullaniyor; dosya eklenmeden 11 komutun 11'i de hata veriyordu.
"""
import sys

from .main import main

if __name__ == "__main__":
    sys.exit(main())
