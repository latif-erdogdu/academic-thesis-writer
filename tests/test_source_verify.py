# -*- coding: utf-8 -*-
"""tools/source_verify modülü için birim testleri.

Bu dosya canlı ağ çağrısı yapmaz; Crossref/OpenAlex yanıtları sahte
``VerificationSource`` nesneleriyle değiştirilir.

Kapsanan dört kusur (bkz. tez EK-2 bölümü):

D1  ``SourceVerifier.verify_crossref`` yılı yalnızca ``published-print``
    ve ``published-online`` alanlarından okur; ``issued`` alanına geri
    düşmez. 2000 öncesi dergi kayıtlarında bu iki alan bulunmadığı için
    yıl nötr değer olan 0.5 puanla skorlanır.

D2  ``compare_authors`` yazarı "soyadı + başharf" biçimine indirger.
    Kaynakça biçimindeki (yalnızca soyadı) bir girdi ile veritabanındaki
    "Soyad, Ad" biçimi hiç eşleşmez; yazar puanı 0.0 olur ve ağırlığı
    0.30 olan alan tamamen kaybolur.

D3  ``compute_bibliographic_match`` içindeki yıl çözümlemesi
    ``a or b or c if cond else None`` biçiminde yazılmıştır. Python'da
    koşul ifadesi ``or``dan düşük önceliklidir, bu yüzden ifade
    ``(a or b or c) if cond else None`` olarak ayrıştırılır. Sonuç:
    kayıt ``year`` / ``publication_year`` anahtarını taşısa bile yıl
    alanı düşürülür.

D4  Aynı öncelik hatası dergi alanında da var; ``container_title`` ya da
    ``host_venue`` anahtarı yoksa dergi boş stringe düşer.

D3 ve D4 birlikte toplam ağırlığın 0.25'ini (yıl 0.15 + dergi 0.10) her
doğrulamada sessizce sıfırlar.
"""
from __future__ import annotations

import json
import unittest
from unittest import mock

from tools.source_verify.bibliographic import (
    BibliographicMatch,
    compare_authors,
    compare_years,
    compute_bibliographic_match,
    normalize_author,
)
from tools.source_verify.verify import SourceVerifier, VerificationSource

SIFIR_ESLESME = BibliographicMatch(
    overall_score=0.0,
    title_score=0.0,
    author_score=0.0,
    year_score=0.0,
    journal_score=0.0,
    doi_match=False,
    details={},
)


def _bos_kaynak(ad: str) -> VerificationSource:
    """Veritabanı devre dışı bırakılmışsa dönecek kaynak."""
    return VerificationSource(
        source=ad,
        match=SIFIR_ESLESME,
        execution_time_ms=0,
        errors=["testte devre disi"],
    )


def _crossref_yaniti(mesaj: dict) -> mock.Mock:
    yanit = mock.Mock()
    yanit.raise_for_status.return_value = None
    yanit.json.return_value = {"message": mesaj}
    return yanit


# --------------------------------------------------------------------- D2
class TestCompareAuthors(unittest.TestCase):
    """D2: yalnızca soyadı içeren yazar girdisi sıfır puan almamalı."""

    def test_soyadi_tek_basina_veritabani_kaydiyla_eslesir(self):
        """Kaynakça girdisi ('Vidal') ile Crossref kaydı ('Vidal, Jean J.')."""
        skor = compare_authors(["Vidal"], ["Vidal, Jean J."])
        self.assertGreater(skor, 0.0)

    def test_soyadi_ile_basarili_yazar_ilki_eslesir(self):
        """İlk yazar örtüşüyorsa puan yüksek olmalı."""
        skor = compare_authors(
            ["Lujan", "Makin"],
            ["Lujan, Macy A.", "Makin, James E."],
        )
        self.assertGreater(skor, 0.8)

    def test_farkli_soyadi_eslesmez(self):
        """Soyadı gerçekten farklıysa puan 0.0 kalmalı (sonsuz kabul yok)."""
        self.assertEqual(compare_authors(["Vidal"], ["Birbaumer, Nils"]), 0.0)

    def test_bos_girdi_sifir_dondurur(self):
        self.assertEqual(compare_authors([], ["Vidal, Jean J."]), 0.0)
        self.assertEqual(compare_authors(["Vidal"], []), 0.0)

    def test_normalize_author_soyadini_korur(self):
        self.assertEqual(normalize_author("Vidal"), "vidal")
        self.assertEqual(normalize_author("Vidal, Jean J."), "vidal j")
        self.assertEqual(normalize_author("Jean Jacques Vidal"), "vidal j")


# --------------------------------------------------------------------- D1
class TestCrossrefIssuedFallback(unittest.TestCase):
    """D1: Crossref yıl okuması ``issued`` alanına geri düşmeli."""

    def test_issued_alanindan_yil_okunur(self):
        """1973 kaydında published-print yok, yalnızca 'issued' var.

        D1'in tersi bir tuzak: kaynak kaydında yıl *yoksa* nötr 0.5 dönmesi
        doğru davranıştır. Burada kaynak yılı 1973 verilir; 'issued'
        geri düşüşü olmazsa puan 0.5'te kalır.
        """
        yanit = _crossref_yaniti({
            "DOI": "10.1146/annurev.bb.02.060173.001105",
            "issued": {"date-parts": [[1973]]},
            "title": ["Toward direct brain-computer communication"],
            "container-title": [
                "Annual Review of Biophysics and Bioengineering"
            ],
            "author": [{"family": "Vidal", "given": "Jean Jacques"}],
        })
        with mock.patch("requests.get", return_value=yanit):
            sonuc = SourceVerifier().verify_crossref({
                "doi": "10.1146/annurev.bb.02.060173.001105",
                "title": "Toward direct brain-computer communication",
                "authors": ["Vidal, Jean Jacques"],
                "year": 1973,
                "journal": "Annual Review of Biophysics and Bioengineering",
            })
        self.assertNotIn("DOI yok", sonuc.errors)
        self.assertEqual(sonuc.match.year_score, 1.0)
        self.assertEqual(sonuc.match.journal_score, 1.0)
        self.assertEqual(sonuc.match.author_score, 1.0)
        self.assertGreaterEqual(sonuc.match.overall_score, 0.99)

    def test_kaynak_yili_yoksa_noktr_kalir(self):
        """D1'in ters yönü: yıl bilinmiyorsa nötr puan, uydurma eşleşme yok."""
        yanit = _crossref_yaniti({
            "DOI": "10.1146/annurev.bb.02.060173.001105",
            "issued": {"date-parts": [[1973]]},
            "title": ["Toward direct brain-computer communication"],
            "container-title": [
                "Annual Review of Biophysics and Bioengineering"
            ],
            "author": [{"family": "Vidal", "given": "Jean Jacques"}],
        })
        with mock.patch("requests.get", return_value=yanit):
            sonuc = SourceVerifier().verify_crossref(
                {"doi": "10.1146/annurev.bb.02.060173.001105"}
            )
        self.assertEqual(sonuc.match.year_score, 0.5)

    def test_published_print_ona_gelir(self):
        """'issued' geri düşmesi 'published-print' varsa onu ezmemeli."""
        yanit = _crossref_yaniti({
            "DOI": "10.1002/hbm.23730",
            "issued": {"date-parts": [[2018]]},
            "published-print": {"date-parts": [[2017]]},
            "title": ["Deep learning with convolutional neural networks"],
            "container-title": ["Human Brain Mapping"],
            "author": [{"family": "Schirrmeister", "given": "Robin T."}],
        })
        with mock.patch("requests.get", return_value=yanit):
            sonuc = SourceVerifier().verify_crossref(
                {"doi": "10.1002/hbm.23730", "year": 2017}
            )
        self.assertEqual(sonuc.match.year_score, 1.0)

    def test_issued_ve_printed_yoksa_noktr(self):
        """Hiçbir tarih alanı yoksa yıl nötr 0.5 kalmalı (uydurma yok)."""
        yanit = _crossref_yaniti({
            "DOI": "10.1000/xyz",
            "title": ["Bir kayit"],
            "container-title": ["Dergi"],
            "author": [{"family": "Yazar", "given": "Ad"}],
        })
        with mock.patch("requests.get", return_value=yanit):
            sonuc = SourceVerifier().verify_crossref({"doi": "10.1000/xyz"})
        self.assertEqual(sonuc.match.year_score, 0.5)


# --------------------------------------------------------- bütünleşik test
class TestVerifySourceSurnameOnly(unittest.TestCase):
    """Uçtan uca: kaynakça biçimindeki kayıt eşiği geçebilmeli."""

    def test_soyadli_kayit_esige_gecer(self):
        yanit = _crossref_yaniti({
            "DOI": "10.1146/annurev.bb.02.060173.001105",
            "issued": {"date-parts": [[1973]]},
            "title": ["Toward direct brain-computer communication"],
            "container-title": [
                "Annual Review of Biophysics and Bioengineering"
            ],
            "author": [{"family": "Vidal", "given": "Jean Jacques"}],
        })
        dogrulayici = SourceVerifier(min_match=0.60, min_sources=1)
        kayit = {
            "id": "SRC-0001",
            "doi": "10.1146/annurev.bb.02.060173.001105",
            "title": "Toward direct brain-computer communication",
            "authors": ["Vidal"],  # yalnızca soyadı
            "year": 1973,
            "journal": "Annual Review of Biophysics and Bioengineering",
        }
        with mock.patch("requests.get", return_value=yanit), mock.patch.object(
            SourceVerifier, "verify_openalex",
            return_value=_bos_kaynak("openalex"),
        ):
            sonuc = dogrulayici.verify_source(kayit)
        self.assertEqual(sonuc.status, "verified")
        self.assertIn("crossref", sonuc.verification_sources)
        self.assertEqual(sonuc.source_id, "SRC-0001")

    def test_yabanci_kayit_yanlis_eslesmez(self):
        """DOI doğru ama başlık başka bir kayda aitse doğrulanmamalı."""
        yanit = _crossref_yaniti({
            "DOI": "10.1038/nature04660",
            "issued": {"date-parts": [[2006]]},
            "title": ["Rapid discharge connects Antarctic subglacial lakes"],
            "container-title": ["Nature"],
            "author": [{"family": "Wingham", "given": "Hugh"}],
        })
        dogrulayici = SourceVerifier(min_match=0.60, min_sources=1)
        kayit = {
            "id": "SRC-0002",
            "doi": "10.1038/nature04660",
            "title": "Neuronal ensemble control of prosthetic devices",
            "authors": ["Hochberg", "Serruya", "Donoghue"],
            "year": 2006,
            "journal": "Nature",
        }
        with mock.patch("requests.get", return_value=yanit), mock.patch.object(
            SourceVerifier, "verify_openalex",
            return_value=_bos_kaynak("openalex"),
        ):
            sonuc = dogrulayici.verify_source(kayit)
        self.assertEqual(sonuc.status, "unverified")

    def test_doi_yoksa_pending(self):
        dogrulayici = SourceVerifier(min_match=0.60, min_sources=1)
        with mock.patch.object(
            SourceVerifier, "verify_openalex",
            return_value=_bos_kaynak("openalex"),
        ):
            sonuc = dogrulayici.verify_source({"id": "SRC-0003", "title": "X"})
        self.assertEqual(sonuc.status, "pending")


# ------------------------------------------ D5: OpenAlex host_venue kaldırılmış
class TestOpenalexDergiAlani(unittest.TestCase):
    """D5: OpenAlex ``host_venue`` alanını kaldırdı.

    Alan 2024 itibarıyla ``None`` dönüyor; dergi adı artık
    ``primary_location.source.display_name`` altında. ``verify_openalex``
    yalnızca eski alanı okuduğu için ikinci doğrulama kaynağında dergi
    puanı kalıcı olarak 0.0 oluyordu.
    """

    YANIT = {
        "doi": "https://doi.org/10.1002/hbm.23730",
        "display_name": (
            "Deep learning with convolutional neural networks for EEG "
            "decoding and visualization"
        ),
        "publication_year": 2017,
        "host_venue": None,  # gerçek API yanıtı
        "primary_location": {
            "source": {"display_name": "Human Brain Mapping"},
        },
        "authorships": [
            {"author": {"display_name": "Robin T. Schirrmeister"}},
            {"author": {"display_name": "Jonas T. Springenberg"}},
        ],
        "biblio": {
            "volume": "38", "issue": "11",
            "first_page": "5391", "last_page": "5420",
        },
    }

    def test_primary_location_dergi_adi_okunur(self):
        yanit = mock.Mock()
        yanit.raise_for_status.return_value = None
        yanit.json.return_value = self.YANIT
        with mock.patch("requests.get", return_value=yanit):
            sonuc = SourceVerifier().verify_openalex({
                "doi": "10.1002/hbm.23730",
                "journal": "Human Brain Mapping",
            })
        self.assertEqual(
            sonuc.match.journal_score, 1.0,
            "OpenAlex dergi adı primary_location altında ama okunmuyor",
        )

    def test_eski_host_venue_hala_calisir(self):
        """Geri uyumluluk: eski biçim de okunmalı."""
        yanit = mock.Mock()
        yanit.raise_for_status.return_value = None
        yanit.json.return_value = {
            "doi": "https://doi.org/10.1000/old",
            "display_name": "Bir kayit",
            "host_venue": {"display_name": "Eski Dergi"},
            "authorships": [],
            "biblio": {},
        }
        with mock.patch("requests.get", return_value=yanit):
            sonuc = SourceVerifier().verify_openalex(
                {"doi": "10.1000/old", "journal": "Eski Dergi"}
            )
        self.assertEqual(sonuc.match.journal_score, 1.0)

    def test_iki_konumlu_kayit_ilk_gecerli_olani_alir(self):
        """primary_location.source boşsa locations listesine düşülmeli."""
        yanit = mock.Mock()
        yanit.raise_for_status.return_value = None
        yanit.json.return_value = {
            "doi": "https://doi.org/10.1000/multi",
            "display_name": "Bir kayit",
            "host_venue": None,
            "primary_location": {"source": {"display_name": None}},
            "locations": [
                {"source": {"display_name": "Dergi Listesi"}},
            ],
            "authorships": [],
            "biblio": {},
        }
        with mock.patch("requests.get", return_value=yanit):
            sonuc = SourceVerifier().verify_openalex(
                {"doi": "10.1000/multi", "journal": "Dergi Listesi"}
            )
        self.assertEqual(sonuc.match.journal_score, 1.0)


# ---------------------------------------------------- D3 + D4: öncelik hatası
class TestAlanCozumlemeOnceligi(unittest.TestCase):
    """D3/D4: ``a or b if cond else c`` ifadesi ``(a or b) if cond else c``
    olarak ayrıştırılır. Bu yüzden kayıt ``year``/``journal`` anahtarlarını
    taşısa bile yıl ve dergi alanları düşürülüyordu.

    Etkisi: ``year_score`` her zaman 0.5, ``journal_score`` her zaman 0.0
    oluyordu; yani toplam ağırlığın 0.25'i (0.15 + 0.10) her doğrulamada
    sessizce yitiriliyordu.
    """

    def test_duz_yil_anahtari_hazir_degildir(self):
        """D3: kayıt 'year' taşıyorsa yıl alanı okunmalı."""
        kayit = {"title": "X", "authors": ["Vidal"], "year": 1973, "journal": "J"}
        es = compute_bibliographic_match(kayit, dict(kayit))
        self.assertEqual(
            es.year_score, 1.0,
            "db kaydı 'year' anahtarını taşıyor ama yıl nötr 0.5 geldi",
        )

    def test_publication_year_anahtari_okunur(self):
        """D3: OpenAlex 'publication_year' kullanır."""
        kayit = {"year": 1973}
        es = compute_bibliographic_match(kayit, {"publication_year": 1973})
        self.assertEqual(es.year_score, 1.0)

    def test_published_print_oku_meli(self):
        """D3: ham Crossref biçimi de okunmalı."""
        es = compute_bibliographic_match(
            {"year": 1973},
            {"published-print": {"date-parts": [[1973]]}},
        )
        self.assertEqual(es.year_score, 1.0)

    def test_duz_dergi_anahtari_hazir_degildir(self):
        """D4: kayıt 'journal' taşıyorsa dergi alanı okunmalı."""
        kayit = {"journal": "Annual Review of Biophysics and Bioengineering"}
        es = compute_bibliographic_match(kayit, dict(kayit))
        self.assertEqual(
            es.journal_score, 1.0,
            "db kaydı 'journal' anahtarını taşıyor ama dergi 0.0 geldi",
        )

    def test_container_title_okunur(self):
        """D4: Crossref 'container-title' listesini kullanır."""
        es = compute_bibliographic_match(
            {"journal": "Nature Reviews Neuroscience"},
            {"container_title": ["Nature Reviews Neuroscience"]},
        )
        self.assertEqual(es.journal_score, 1.0)

    def test_gercek_boş_deger_boş_kalmali(self):
        """Öncelik hatası düzeltilirken 'yok' durumu da 'yok' kalmalı."""
        es = compute_bibliographic_match(
            {"journal": "Nature"},
            {},  # hiçbir dergi alanı yok
        )
        self.assertEqual(es.journal_score, 0.0)
        es2 = compute_bibliographic_match({"year": 2000}, {})
        self.assertEqual(es2.year_score, 0.5)  # nötr, uydurma değil


# ------------------------------------------------ karsilastirma birimleri
class TestKarsilastirmaBirimleri(unittest.TestCase):
    def test_compare_years(self):
        self.assertEqual(compare_years(1973, 1973), 1.0)
        self.assertEqual(compare_years(1973, 1974), 0.8)
        self.assertEqual(compare_years(1973, 1975), 0.5)
        self.assertEqual(compare_years(1973, 1976), 0.0)
        self.assertEqual(compare_years(None, 1973), 0.5)

    def test_compute_match_tam_uyum(self):
        """DOI dahil tüm alanlar tutarlıysa tam puan gelmelidir."""
        kayit = {
            "doi": "10.1038/nrn.2015.7",
            "title": "Out of the lab: The real-world complexities of "
                     "brain-computer interface clinical research",
            "authors": ["Lujan, Macy A.", "Makin, James E."],
            "year": 2015,
            "journal": "Nature Reviews Neuroscience",
        }
        es = compute_bibliographic_match(kayit, dict(kayit))
        self.assertGreaterEqual(es.overall_score, 0.99)
        self.assertTrue(es.doi_match)

    def test_compute_match_sonucu_json_serilestirilebilir(self):
        """CLI hata ayıklama çıktısı ürettiği için sonuç JSON'a dönmeli."""
        es = compute_bibliographic_match(
            {"title": "A", "authors": ["X"], "year": 2000, "journal": "J"},
            {"title": "A", "authors": ["X"], "year": 2000, "journal": "J"},
        )
        json.dumps(es.__dict__, default=str)


if __name__ == "__main__":
    unittest.main()
