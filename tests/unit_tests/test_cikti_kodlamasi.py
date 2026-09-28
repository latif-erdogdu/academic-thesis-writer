"""CLI çıktısı Türkçe Windows konsolunda patlıyor.

Neden bu test
-------------
CLI'in her cıktısı Türkçe karakterler (ğ ü ş İ ç ö) ve durum glifleri
(✅ U+2705, ❌ U+274C, ✗ U+2717, ⚠ U+26A0) içeriyor. Windows'ta
`sys.stdout.encoding` varsayılan olarak konsol kod sayfasıdır; Türkçe
kurulumda bu **cp1254**'tür. Bu gliflerin hiçbiri cp1254'te yok.

Sonuç: `thesis:new` bile `print` aşamasında `UnicodeEncodeError`
fırlatıyor ve süreç 1 ile çıkıyordu. `thesis:approve` durumu başarıyla
yazdı, sonra aynı hata yüzünden "başarısız" göründü. `PYTHONIOENCODING=utf-8`
ile aynı komutlar sorunsuz çalışıyor. Yani araç, tam olarak hedeflediği
ortamda (Türkçe Windows) varsayılan ayarlarla kullanılamaz durumdaydı.

Bu testler şunları bağlar:

  1. `_cikti_kodlamasini_ayarla` dar kodlamalı akışı UTF-8'e çevirir.
  2. Çevirdikten sonra ✅ yazdırılabilir.
  3. Yeniden yapılandırılamayan akışta CLI istisna atmaz.
  4. Gerçek alt süreç, `PYTHONIOENCODING=cp1254` ile hata vermez.
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tools.atw.cli import main as cli


# CLI'in kullandigi durum glifleri. Hepsi cp1254'te YOK.
DURUM_GLIFLERI = "\u2705\u274c\u2717\u26a0"

REPO_KOK = Path(__file__).resolve().parents[2]


def _dar_akis(encoding: str = "cp1254") -> io.TextIOWrapper:
    """`encoding` kodlamasiyla yazan, icerigi byte olarak tutan sahte akis."""
    return io.TextIOWrapper(io.BytesIO(), encoding=encoding, errors="strict")


# ---------------------------------------------------------------------------
# Kontrol: duzeltme OLMADAN gercekten patliyor mu?
# ---------------------------------------------------------------------------


def test_glifler_dar_kodlamada_kendiliginden_patlar():
    """Beklenen kotu yol. Yukaridaki duzeltme testinin yesil olmasi
    tesaduf degil, gercek bir davranis degisikligi olarak olcer."""
    akis = _dar_akis("cp1254")
    with pytest.raises(UnicodeEncodeError):
        akis.write(DURUM_GLIFLERI)
        akis.flush()


# ---------------------------------------------------------------------------
# Duzeltme
# ---------------------------------------------------------------------------


def test_dar_kodlamali_akis_utf8e_cevrilir():
    """Varsayilan kodlama cp1254 olan akis, ayar sonrasi UTF-8 olur."""
    akis = _dar_akis("cp1254")
    assert akis.encoding.lower() == "cp1254"

    cli._cikti_kodlamasini_ayarla(stdout=akis)

    assert akis.encoding.lower().replace("-", "") == "utf8"


def test_ayarladiktan_sonra_glifler_yazdirilabilir():
    """Duzeltmeden sonra tum durum glifleri akisa yazilabilir."""
    akis = _dar_akis("cp1254")
    cli._cikti_kodlamasini_ayarla(stdout=akis)

    akis.write(DURUM_GLIFLERI)
    akis.flush()  # yazma burada gercekten olur


def test_zaten_utf8_olan_akisa_dokunulmaz():
    """Gereksiz yeniden yapilandirma yapilmaz; encoding korunur."""
    akis = _dar_akis("utf-8")
    cli._cikti_kodlamasini_ayarla(stdout=akis)
    assert akis.encoding.lower().replace("-", "") == "utf8"


def test_yeniden_yapilandirilamayan_akis_ustunde_istisna_atilmaz():
    """`reconfigure` desteklemeyen akista CLI istisna atmaz.

    Ciktı akisi her ortamda yeniden yapilandirilabilir degil. Bu yardimci
    cikti tarafinda oldugu icin hata vermesi durumunda CLI komutu
    calistiramaz hale gelirdi — duzeltilen kusurun aynisi.
    """

    class _YenidenYapilandirilamaz:
        encoding = "cp1254"

    akis = _YenidenYapilandirilamaz()
    cli._cikti_kodlamasini_ayarla(stdout=akis)  # istisna atmamali

    assert akis.encoding == "cp1254"  # degistirilemedi, olmasi da gerekmiyor


def test_reconfigure_istisna_atarsa_da_komut_calisir():
    """`reconfigure` hata firlatan akista da CLI kendi yolunda devam eder."""

    class _Patlayan:
        encoding = "ascii"

        def reconfigure(self, **kwargs):
            raise ValueError("yeniden yapilandirilamaz")

    akis = _Patlayan()
    cli._cikti_kodlamasini_ayarla(stdout=akis)  # istisna atmamali

    assert akis.encoding == "ascii"


def test_yok_olan_akis_yok_sayilir():
    """`sys.stdout` yerine None gelebilir (gofake sunucu); sorun degil."""
    cli._cikti_kodlamasini_ayarla(stdout=None, stderr=None)


# ---------------------------------------------------------------------------
# Uctan uca: gercek alt surec, kodlama acikca cp1254 verilerek
# ---------------------------------------------------------------------------


def _calistir(argv, cwd, ortam) -> subprocess.CompletedProcess:
    """Alt sureci calistirip ciktisini UTF-8 olarak coz.

    Kodlama iki ayri sey:

      * Cocuk `PYTHONIOENCODING=cp1254` ile BASLAR — Turkce Windows
        konsolunun kodlamasi. Duzeltme onu UTF-8'e cevirir.
      * Cocuk bu yuzden UTF-8 byte'lari yazar; ebeveyn de UTF-8 cozer.

    Yani ebeveyni cp1254 ile cozmek, cocugun duzeltmeden sonraki
    ciktisini yanlis okur; testin kendi hatasidir.
    """
    return subprocess.run(
        argv,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=ortam,
    )


def test_uctan_uca_cp1254_konsolunda_komutlar_calisir(tmp_path):
    """Kullanici makinenizi birebir taklit eden alt surec.

    `PYTHONIOENCODING=cp1254` verilir; boylece alt surec de Turkce
    Windows konsolundaki kodlamayi kullanir. Zincirin uc adimi
    calistirilir: `new` -> `record` -> `approve`. `new` dogrudan basari
    isareti yazdigi icin sorun tam olarak orada cikiyordu; `approve`
    hazirlik eksikliginde uyari tiskartisi yazdigi icin ayni sey.

    Calisma dizini `tmp_path`: `veri_koku()` varsayilan olarak `Path.cwd()`
    kullaniyor, yani `cwd` degistirilmezse `thesis new` depo kokune
    `thesis_state.json` yazar. Semalar `state.py:SCHEMA_DIR` uzerinden
    `__file__`ten mutlak cozuluyor; bu yuzden gecici dizinden calismak
    sema erisimini bozmaz.
    """
    ortam = {
        **os.environ,
        "PYTHONIOENCODING": "cp1254",
        "PYTHONUTF8": "0",
        "PYTHONPATH": str(REPO_KOK),
    }
    adimlar = []

    def calis(*argv, basari_beklenir=True):
        sonuc = _calistir([sys.executable, "-m", "tools.atw.cli", *argv], tmp_path, ortam)
        adimlar.append((argv, sonuc.returncode, sonuc.stdout, sonuc.stderr))
        assert "UnicodeEncodeError" not in sonuc.stderr, f"{argv}: {sonuc.stderr}"
        if basari_beklenir:
            assert sonuc.returncode == 0, (
                f"{argv} -> rc={sonuc.returncode}\n"
                f"stdout={sonuc.stdout!r}\nstderr={sonuc.stderr!r}"
            )
        return sonuc

    # 1) Tezi baslat.
    calis("new", "THESIS-2026-001", "Deneme Tezi")
    assert "\u2705" in adimlar[0][2], "basari isareti ciktiya tasinmali"

    # 2) Arastirma sorusunu kaydet (bos registry kapiyi acmaz).
    soru = tmp_path / "rq.json"
    soru.write_text(
        json.dumps(
            {
                "id": "RQ-001",
                "text": "Kurgusal ornek soru: yontemin etkisi nedir?",
                "type": "main",
                "status": "pending",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    calis("record", "research_questions", "--file", "rq.json")
    assert "\u2705" in adimlar[1][2]

    # 3) Kapiyi ac.
    calis("approve", "research_question")
    assert "\u2705" in adimlar[2][2]

    # Depo kokune sizmis olmamali: `thesis new` asla orada calistirilmaz.
    assert not (REPO_KOK / "thesis_state.json").exists(), (
        "alt surec depo kokune thesis_state.json yazdi — calisma dizini "
        "tmp_path olmaliydi"
    )
