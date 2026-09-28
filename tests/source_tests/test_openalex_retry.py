"""OpenAlex 429 (Too Many Requests) geçici bir hata; yeniden deneme gerekli.

Neden bu test
-------------
Ölçüldü (canlı, 2026-09-28): anonim havuzda OpenAlex periyodik 429
döndürüyor. İstemcii tek atışta `raise_for_status` ile hata fırlatınca
`run_systematic_search`'ün hata yolu `records=[]` yazıyor ve arama kaydı
"openalex: 0 kayıt" görünüyor — meşru boş sonuç SANILAN bir veri kaybı
(SEARCH-1724/4775: openalex kayıt=0).

429'lar havuz kotası dolunca bir süre sonra kendiliğinden düzelir; bu
yüzden sınırlı geri çekilme (backoff) + yeniden deneme doğru davranıştır.
Diğer hata kodları (4xx/5xx) yeniden denenmez — kalıcı hatadır.

Ağ YOK: `session.get` sahte oturumla değiştirilir, `time.sleep` kaydedilir.
"""
from __future__ import annotations

import pytest

from tools.source_search.openalex import OpenAlexClient


class _Yanit:
    def __init__(self, status: int, veri: dict | None = None) -> None:
        self.status_code = status
        self._veri = veri if veri is not None else {}

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            raise requests.HTTPError(f"{self.status_code} Client Error")

    def json(self) -> dict:
        return self._veri


class _SahteOturum:
    """Sırayla yanıt döndürür; son yanıt tekrarlanır."""

    def __init__(self, yanitlar: list[_Yanit]) -> None:
        self.yanitlar = list(yanitlar)
        self.cagrilar = 0

    def get(self, url, params=None, timeout=30) -> _Yanit:
        yanit = self.yanitlar[min(self.cagrilar, len(self.yanitlar) - 1)]
        self.cagrilar += 1
        return yanit


class TestOpenAlex429YenidenDeneme:
    def _istemci(self, monkeypatch, yanitlar, **kwargs):
        uykular: list[float] = []
        monkeypatch.setattr(
            "tools.source_search.openalex.time.sleep", uykular.append
        )
        c = OpenAlexClient(retry_deneme=kwargs.pop("retry_deneme", 3), **kwargs)
        c.session = _SahteOturum(yanitlar)
        return c, uykular

    def test_429_iki_kez_sonra_basarili_olur(self, monkeypatch):
        c, uykular = self._istemci(
            monkeypatch,
            [
                _Yanit(429),
                _Yanit(429),
                _Yanit(200, {"meta": {"count": 1}, "results": [{"id": "W1"}]}),
            ],
            retry_deneme=3,
            retry_gecikme_sn=2.0,
        )

        veri = c._get("/works", {"search": "alectoris"})

        assert veri["meta"]["count"] == 1
        assert c.session.cagrilar == 3
        assert uykular == [2.0, 4.0], "geri çekilme üstel büyümeli (2sn, 4sn)"

    def test_429_denemeler_tukenince_hata_firlar(self, monkeypatch):
        import requests

        c, uykular = self._istemci(
            monkeypatch,
            [_Yanit(429), _Yanit(429), _Yanit(200, {})],
            retry_deneme=2,
            retry_gecikme_sn=1.0,
        )

        with pytest.raises(requests.HTTPError):
            c._get("/works", {})

        assert c.session.cagrilar == 2, "deneme sayısı kadar istek atılmalı"

    def test_429_basariyla_donerse_sayi_artmaz(self, monkeypatch):
        c, _ = self._istemci(
            monkeypatch,
            [_Yanit(429), _Yanit(200, {"meta": {"count": 0}, "results": []})],
            retry_deneme=3,
            retry_gecikme_sn=1.0,
        )

        veri = c._get("/works", {})

        assert veri["meta"]["count"] == 0
        assert c.session.cagrilar == 2

    def test_429_disi_hata_yeniden_denenmez(self, monkeypatch):
        import requests

        c, _ = self._istemci(
            monkeypatch,
            [_Yanit(500, {"error": "kalici"})],
            retry_deneme=3,
            retry_gecikme_sn=1.0,
        )

        with pytest.raises(requests.HTTPError):
            c._get("/works", {})

        assert c.session.cagrilar == 1, "5xx kalıcıdır, yeniden denenmez"

    def test_hata_yoksa_tek_istek_yeter(self, monkeypatch):
        c, uykular = self._istemci(
            monkeypatch,
            [_Yanit(200, {"meta": {"count": 0}, "results": []})],
            retry_deneme=3,
            retry_gecikme_sn=1.0,
        )

        c._get("/works", {})

        assert c.session.cagrilar == 1
        assert uykular == []