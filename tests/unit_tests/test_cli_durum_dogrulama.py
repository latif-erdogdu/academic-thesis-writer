"""CLI, yazdığı tez durumunu şemaya göre doğrulamalı.

Neden bu test
-------------
`tools/atw/cli/main.py` içindeki `save_state` düz `write_text` ile
yazıyordu. Aynı ada sahip `tools/atw/state.py::save_state` ise
`validate_state` çağırıp hatalı durumda `ValueError` fırlatıyor.

İki farklı davranış, hatanın hangi yoldan geldiğini gizliyordu:
kütüphane yolu reddediyor, CLI sessizce yazıyordu. Ölçülen sonuç —
`thesis:search` üç kez çalıştıktan sonra gerçek tez durumu
**312 şema hatası** taşıyordu ve kimse bunu görmemişti; `audit`
kayıtları okuyor ama şema ihlalini denetlemiyor.

Bu test kütüphane yolunun zaten doğruladığını, CLI yolunun da
DOĞRULAMASI GEREKTİĞİNİ bağlar.
"""
from __future__ import annotations

import pytest


class TestCLIYazimiDogrular:
    """CLI, yazdığı durumu doğrulamalı — yoksa hatalar birikir.

    `cli/main.py:213 save_state` düz `write_text` ile yazıyordu. Kütüphane
    yolundaki `state.save_state` doğruluyor. Aynı ada sahip iki farklı
    davranış, hatanın hangi yoldan geldiğini gizledi.
    """

    def test_save_state_gecersiz_durumu_reddeder(self, tmp_path, monkeypatch):
        from tools.atw.cli import main as cli

        monkeypatch.setattr(cli, "durum_yolu", lambda: tmp_path / "t.json", raising=False)
        monkeypatch.chdir(tmp_path)

        with pytest.raises(ValueError):
            cli.save_state({"thesis_id": "THESIS-1"})

    def test_save_state_hatasi_dosyaya_yazmaz(self, tmp_path, monkeypatch):
        """Doğrulama başarısızsa HİÇBİR dosya yazılmamalı.

        Kısmi yazım, sonraki koşuda okunamayan durum bırakır.
        """
        from tools.atw.cli import main as cli

        monkeypatch.chdir(tmp_path)
        hedef = tmp_path / "thesis_state.json"

        with pytest.raises(ValueError):
            cli.save_state({"thesis_id": "THESIS-1"})

        assert not hedef.exists()
