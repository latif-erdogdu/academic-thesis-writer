# -*- coding: utf-8 -*-
"""`tools/source_verify` — 429 yeniden deneme testleri.

Neden bu test
-------------
Anonim havuzda OpenAlex (ve ara sıra Crossref) periyodik 429 dondurur.
`verify_openalex` / `verify_crossref` tek atista hata yiyince ayak
'errors' ile doner; `verify_source` o ayagi listeye koymaz (skor 0 +
hata sicili = 'eslesme yok' sayilmaz) ve kaynak spurious `unverified`
olur. Canli kusur (olculdu, 2026-09-28): 52'si openalex kaynakli 72
kaydin tumu dogrulama bekliyor; tikanik havuzda tek atis yeterli
olmuyor.

Duzeltme oncesi davranis (`_get_with_retry` yokken):
  429 -> `raise_for_status` HTTPError -> `except Exception` -> errors
  -> kaynak "eslesme bulunamadi" gibi gorunur.

Beklenen davranis:
  429 gecicidir; sinirli geri cekilme + yeniden deneme (varsayilan 3)
  ile ayak kurtarilir. Diger 4xx/5xx kalicidir; yeniden denenmez.
"""
from __future__ import annotations

import unittest
from unittest import mock

import requests

from tools.source_verify.verify import SourceVerifier, VerificationSource, _get_with_retry


def _yanit(durum: int, json_verisi: dict | None = None) -> mock.Mock:
    """Sahte HTTP yaniti: status_code + raise_for_status + json."""
    yanit = mock.Mock()
    yanit.status_code = durum
    if durum >= 400:
        yanit.raise_for_status.side_effect = requests.exceptions.HTTPError(
            f"{durum} Hata"
        )
    else:
        yanit.raise_for_status.return_value = None
    yanit.json.return_value = json_verisi or {}
    return yanit


def _crossref_yaniti() -> mock.Mock:
    """Skoru >= 0.60 yapan gercekci Crossref yaniti."""
    return _yanit(200, {"message": {
        "DOI": "10.1002/hbm.23730",
        "issued": {"date-parts": [[2017]]},
        "title": [
            "Deep learning with convolutional neural networks for "
            "EEG decoding and visualization"
        ],
        "container-title": ["Human Brain Mapping"],
        "author": [{"family": "Schirrmeister", "given": "Robin T."}],
    }})


def _openalex_yaniti() -> mock.Mock:
    """Skoru >= 0.60 yapan gercekci OpenAlex yaniti."""
    return _yanit(200, {
        "doi": "https://doi.org/10.1002/hbm.23730",
        "display_name": (
            "Deep learning with convolutional neural networks for "
            "EEG decoding and visualization"
        ),
        "publication_year": 2017,
        "primary_location": {"source": {"display_name": "Human Brain Mapping"}},
        "authorships": [{"author": {"display_name": "Robin T. Schirrmeister"}}],
        "biblio": {"volume": "38", "issue": "11",
                   "first_page": "5391", "last_page": "5420"},
    })


def _kayit() -> dict:
    return {
        "id": "SRC-0001",
        "doi": "10.1002/hbm.23730",
        "title": (
            "Deep learning with convolutional neural networks for "
            "EEG decoding and visualization"
        ),
        "authors": ["Schirrmeister, Robin T."],
        "year": 2017,
        "journal": "Human Brain Mapping",
    }


class TestGetWithRetry(unittest.TestCase):
    """Yardimci `_get_with_retry` — 429'a karsi sinirli geri cekilme."""

    def test_429_iki_kez_sonra_basarili_olur(self):
        """429, 429, 200 -> uc istek; geri cekilme gecikme*deneme olmali."""
        yanitlar = [_yanit(429), _yanit(429), _crossref_yaniti()]
        with mock.patch("requests.get", side_effect=yanitlar) as istek, mock.patch(
            "tools.source_verify.verify.time.sleep"
        ) as uyku:
            sonuc = _get_with_retry(
                requests, "https://api.crossref.org/works/x",
                timeout=30, retry_deneme=3, retry_gecikme_sn=0.01,
            )
            self.assertEqual(istek.call_count, 3)

        self.assertEqual(sonuc.status_code, 200)
        self.assertEqual(
            [c.args[0] for c in uyku.call_args_list], [0.01, 0.02],
            "geri cekilme gecikme * deneme olarak buyumeli",
        )

    def test_429_tukenince_son_yanit_doner_yukseltme_cagiriciya_kalir(self):
        """Tum denemeler 429 -> son yanit doner; caller raise eder."""
        yanitlar = [_yanit(429), _yanit(429), _yanit(429)]
        with mock.patch("requests.get", side_effect=yanitlar):
            sonuc = _get_with_retry(
                requests, "https://api.openalex.org/works/x",
                timeout=30, retry_deneme=3, retry_gecikme_sn=0.01,
            )
        self.assertEqual(sonuc.status_code, 429)
        with self.assertRaises(requests.exceptions.HTTPError):
            sonuc.raise_for_status()

    def test_429_disI_hata_yeniden_denenmez(self):
        """500 kalicidir: tek istek, caller raise eder."""
        with mock.patch("requests.get", return_value=_yanit(500)) as istek:
            sonuc = _get_with_retry(
                requests, "https://api.crossref.org/works/x",
                timeout=30, retry_deneme=3, retry_gecikme_sn=0.01,
            )
        self.assertEqual(istek.call_count, 1)
        with self.assertRaises(requests.exceptions.HTTPError):
            sonuc.raise_for_status()

    def test_hata_yoksa_tek_istek_yeter(self):
        """200'de yeniden deneme devreye girmemeli."""
        with mock.patch("requests.get", return_value=_crossref_yaniti()) as istek:
            sonuc = _get_with_retry(
                requests, "https://api.crossref.org/works/x",
                timeout=30, retry_deneme=3, retry_gecikme_sn=0.01,
            )
        self.assertEqual(istek.call_count, 1)
        self.assertEqual(sonuc.status_code, 200)


class TestVerifyOpenalex429(unittest.TestCase):
    """`verify_openalex` 429'ları yeniden denemeyle emmeli."""

    def test_429_transient_iken_dogrulama_basarir(self):
        """429, 429, 200 -> hata yok, skor hesaplanir."""
        with mock.patch(
            "requests.get",
            side_effect=[_yanit(429), _yanit(429), _openalex_yaniti()],
        ), mock.patch(
            "tools.source_verify.retraction.check_openalex_retraction",
            return_value=None,
        ):
            sonuc = SourceVerifier(
                retry_deneme=3, retry_gecikme_sn=0.01
            ).verify_openalex(_kayit())

        self.assertIsInstance(sonuc, VerificationSource)
        self.assertNotIn("429", "; ".join(sonuc.errors))
        self.assertGreater(sonuc.match.overall_score, 0.0)

    def test_429_tukenirse_hata_kayda_duser(self):
        """Tum denemeler 429 -> errors ajana yazilir, skor 0 kalir."""
        with mock.patch(
            "requests.get",
            side_effect=[_yanit(429), _yanit(429), _yanit(429)],
        ):
            sonuc = SourceVerifier(
                retry_deneme=3, retry_gecikme_sn=0.01
            ).verify_openalex(_kayit())
        self.assertEqual(sonuc.match.overall_score, 0.0)
        self.assertTrue(sonuc.errors, "hata ajana yazilmalı")


class TestVerifySource429Kurtarir(unittest.TestCase):
    """`verify_source` 429 geçiciyse kaynağı `verified` saymalı."""

    def test_openalex_429_kurtarilir_iki_bagimsiz_kaynak_korunur(self):
        """crossref 200 + openalex 429,429,200 -> verified, 2 kaynak."""
        with mock.patch(
            "requests.get",
            side_effect=[
                _crossref_yaniti(), _yanit(429), _yanit(429), _openalex_yaniti(),
            ],
        ), mock.patch(
            "tools.source_verify.retraction.check_crossref_retraction",
            return_value=None,
        ), mock.patch(
            "tools.source_verify.retraction.check_openalex_retraction",
            return_value=None,
        ):
            sonuc = SourceVerifier(
                min_match=0.60, min_sources=2,
                retry_deneme=3, retry_gecikme_sn=0.01,
            ).verify_source(_kayit())

        self.assertEqual(sonuc.status, "verified")
        self.assertEqual(
            sorted(sonuc.verification_sources), ["crossref", "openalex"],
        )


if __name__ == "__main__":
    unittest.main()