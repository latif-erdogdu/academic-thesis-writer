#!/usr/bin/env python3
"""Hook: Yeni kaynak eklendiğinde otomatik DOI/bibliyografik doğrulama.

DURUŞT KURALI — bu betik SORGULAMADIĞI bir kaynağı asla yazmaz.
`verification_sources` alanı "hangi veritabanları sorgulandı" anlamına
gelir; bu betik `tools.source_verify.SourceVerifier` üzerinden gerçekten
sorgular ve yalnızca yanıt alan veritabanlarının adını yazar.

Geçmişte DOI dalı hiçbir ağ çağrısı yapmadan `["crossref", "openalex"]`
yazıyordu (kodun kendi yorumu: "# Şimdilik placeholder"). `status` değeri
`pending` olduğu için durustu, ama kaynak listesi kalıcı bir yalandı.

Yol çözümlemesi: bu betik `.opencode/skill/academic-thesis-writer/hooks/`
altındadır, yani değer zinciri 4 derinlikte:

    parents[0] = hooks
    parents[1] = academic-thesis-writer
    parents[2] = skill
    parents[3] = .opencode        <- YANLIŞ (eskiden burası kullanılıyordu)
    parents[4] = <depo kökü>      <- doğrusu

`parents[3]` kullanıldığında nispi yollar `.opencode/` altında aranıyor,
bulunamıyor ve betik "Dosya yok" deyip 0 dönerek sessizce hiçbir şey
yapmadan çıkıyordu.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
# Betik subprocess olarak, çalışma dizini ne olursa olsun çalıştırılabilir.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.source_verify.verify import SourceVerifier  # noqa: E402


# Doğrulama yapılmadığında yazılacak kaynak listesi. Enum'da "manual" var
# ama "elle doğrulandı" demektir; kimse doğrulamadığı halde yazmak yine
# sorgulanmamış bir kaynak bildirmektir.
SORGULANMADI: list[str] = []


def _cozumle(yol: str) -> Path:
    """Nispi yolları depo köküne göre çözümler; mutlak yollara dokunmaz."""
    aday = Path(yol)
    return aday if aday.is_absolute() else REPO_ROOT / aday


def _kaydet(yol: Path, veri: dict) -> None:
    # utf-8-sig: BOM'lu JSON'u da yazabilmek için. BOM'suz okumada sorun yok.
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=2), encoding="utf-8")


def main(file_path: str) -> int:
    source_file = _cozumle(file_path)

    if not source_file.exists():
        print(f"⚠️  Dosya yok: {source_file}")
        return 0

    try:
        # utf-8-sig: BOM'lu dosyalar da okunur, BOM'suz olanlar da.
        # PowerShell `Set-Content -Encoding UTF8`, Notepad ve Excel bu
        # formatı üretir; reddedilmemelidir.
        veri = json.loads(source_file.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        print(f"❌ Geçersiz JSON: {e}")
        return 1

    dogrulama = veri.get("verification")

    # Hiç doğrulama alanı yok: henüz sorgulanmadı.
    if not dogrulama:
        print("⚠️  verification alanı yok, sorgulanmadı olarak işaretleniyor")
        veri["verification"] = {
            "status": "pending",
            "bibliographic_match": 0.0,
            "verified_at": "",
            "verification_sources": list(SORGULANMADI),
        }
        _kaydet(source_file, veri)
        return 0

    if dogrulama.get("status") == "verified":
        print(f"✅ Zaten verified: {veri.get('id')}")
        return 0

    doi = veri.get("doi", "")
    if not doi:
        print(f"⚠️  DOI yok, elle doğrulama gerekiyor: {veri.get('id')}")
        dogrulama["status"] = "pending"
        dogrulama["verification_sources"] = list(SORGULANMADI)
        _kaydet(source_file, veri)
        return 0

    print(f"🔍 DOI doğrulanıyor: {doi}")
    try:
        sonuc = SourceVerifier().verify_source(veri)
    except Exception as e:  # ağ hatası, kod hatası, zaman aşımı
        # Kayda DOKUNULMAZ. Uydurma bir kaynak listesi yazmak, doğrulamadan
        # iyi bir şey değildir: kaydı olduğundan fazla doğrulanmış gösterir.
        print(f"❌ Doğrulama yapılamadı ({type(e).__name__}: {e}); kayıt değiştirilmedi")
        return 1

    # Yalnızca doğrulayıcının GERÇEKTEN yanıt alan veritabanları yazılır.
    kaynaklar = list(getattr(sonuc, "verification_sources", []) or [])
    dogrulama["status"] = sonuc.status
    dogrulama["bibliographic_match"] = sonuc.bibliographic_match
    dogrulama["verified_at"] = sonuc.verified_at or datetime.now(timezone.utc).isoformat()
    dogrulama["verification_sources"] = kaynaklar

    detay = getattr(sonuc, "verification_details", None) or {}
    for alan in ("doi_match", "author_match", "title_match", "year_match", "journal_match"):
        if alan in detay:
            dogrulama[alan] = detay[alan]

    _kaydet(source_file, veri)
    print(
        f"{'✅' if kaynaklar else '⚠️ '} {sonuc.status}: {veri.get('id')} "
        f"(skor {sonuc.bibliographic_match:.2f}, kaynak: {kaynaklar or 'sorgulanamadı'})"
    )
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python auto_verify.py <dosya_yolu>")
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
