"""`parse_pico` — Türkçe metni ve açık etiketli PICO'yu anlayabilmeli.

Neden bu test
-------------
Bu modül (`tools/source_search/`) test dosyası olmadan geliştirilmişti.
`parse_pico` yalnızca İngilizce anahtar kelimelere bakıyor ve iki somut
arıza üretiyor.

1. **Türkçe metin boş PICO'ya dönüşüyor.** Türkçe bir tez başlığı

       "Doğaya Yerleştirilen Kınalı Kekliklerin (Alectoris chukar) Hayatta
        Kalma ve Üreme Başarısını Etkileyen Faktörlerin Belirlenmesi"

   `parse_pico`'dan geçince `non_empty()` boş döner. `cmd_search` bunu
   görüp aramayı reddeder. Yani CLI'nin kendi tez dili onun kendi
   arama katmanını çalıştıramıyor.

2. **CLI'nin önerdiği çıkış yolu ÇALIŞMIYOR — üstelik sessizce bozuk.**
   `cmd_search` boş PICO hatasında şunu öneriyor:

       --pico "pop: …, intervention: …, outcome: …"

   Ama `parse_pico` bu etiketleri hiç bilmiyor. Metin içindeki kelime
   `outcome` için regex çalışır, **etiketin kendisini** eşleşme sayar ve
   çevresindeki 30 karakteri kırpar. Ölçülen sonuç:

       parse_pico("pop: Alectoris chukar translocated, outcome: survival
                   and reproductive success")
       -> outcome = 'lectoris chukar translocated, outcome: survival
                     and reproductive su'

   İki hata bir arada: baştan `Al` düşmüş, sondan `ccess` düşmüş, yani
   kullanıcı yazdığı terimi DEĞİLDİĞİ bir terimle arama yapıyor ve
   akış "arama tamamlandı" diye yeşil çıkıyor. Sessiz ve yanlış.

   Yani `--pico` şu an iki yönlü bir tuzak: etiketli kullanım bozuk
   sorgu üretiyor, etiketsiz kullanım hiç üretmiyor.

3. **`--pico` dalı boşluğu denetlemiyor.** `cmd_search._aramaya_pico`
   `--pico` verilmişse `parse_pico` çıktısını `non_empty()` kontrolü
   olmadan döndürür. `--rq` dalı denetliyor. Aynı arıza, iki dalda
   farklı davranış.

Bu dosya dördüncü maddeyi de pinler: açık etiketli bileşenler
heuristiğe YENİLİR, yazara açıktır; serbest metin ise geriye
düşülen yoldur.

Ağ YOK: `parse_pico` saf metin işlemesidir, hiçbir test ağ çağrısı yapmaz.
"""
from __future__ import annotations

import pytest

from tools.source_search import parse_pico


#: Tezin gerçek başlığı — bu dosyanın var olma sebebi.
GERCEK_BASLIK = (
    "Doğaya Yerleştirilen Kınalı Kekliklerin (Alectoris chukar) Hayatta "
    "Kalma ve Üreme Başarısını Etkileyen Faktörlerin Belirlenmesi"
)

#: Bir kanıtlayıcı olmayan tıbbi cümle: İngilizce davranışın bozulmadığını
#: göstermek için. `parse_pico` bunu bugün de dolduruyor.
INGILIZCE_CUMLE = (
    "In elderly patients with major depression, does cognitive behavioral "
    "therapy compared to placebo improve quality of life outcomes?"
)


class TestAcikEtiketler:
    """`pop: X, outcome: Y` yazımı gerçekten X ve Y'yi vermeli."""

    def test_etiketli_pico_bilesenleri_doldurur(self):
        pico = parse_pico(
            "pop: Alectoris chukar translocated, "
            "intervention: translocation, "
            "outcome: survival and reproductive success"
        )
        assert pico.population == "Alectoris chukar translocated"
        assert pico.intervention == "translocation"
        assert pico.outcome == "survival and reproductive success"

    def test_etiketli_deger_kirpilmaz(self):
        """Değer BAŞTAN ve SONDAN kaybolmamalı.

        Kırpma, kullanıcının yazdığı terimi değil başka bir terimi
        aratır; sonuç sessizce yanlış olur.
        """
        pico = parse_pico("pop: Alectoris chukar, outcome: reproductive success")
        assert pico.population.startswith("Alectoris")
        assert pico.outcome.endswith("success")
        assert "…" not in pico.outcome and "..." not in pico.outcome

    def test_etiket_kelimesi_degerin_icine_karismaz(self):
        """`outcome:` etiketi, outcome DEĞERİ içinde görünmemeli.

        Kırılmış davranışın tam olarak bu satırı. Değer, etiket
        kelimesini içeriyorsa hâlâ kendi terimini vermeli.
        """
        pico = parse_pico("pop: keklik, outcome: hayatta kalma ve üreme başarısı")
        assert pico.outcome == "hayatta kalma ve üreme başarısı"
        assert "outcome" not in pico.outcome.lower()

    @pytest.mark.parametrize(
        "etiket,alan",
        [
            ("pop", "population"),
            ("population", "population"),
            ("p", "population"),
            ("int", "intervention"),
            ("intervention", "intervention"),
            ("exposure", "intervention"),
            ("comp", "comparison"),
            ("comparison", "comparison"),
            ("out", "outcome"),
            ("outcome", "outcome"),
            ("ctx", "context"),
            ("context", "context"),
            ("design", "study_design"),
            ("study_design", "study_design"),
            ("sd", "study_design"),
        ],
    )
    def test_etiket_takma_adlari(self, etiket, alan):
        pico = parse_pico(f"{etiket}: keklik popülasyonu")
        assert pico.to_dict()[alan] == "keklik popülasyonu"

    def test_son_etiketsiz_som_satir_da_alinir(self):
        """Virgülle biten metinde son bileşen de yakalanmalı."""
        pico = parse_pico("pop: keklik, outcome: üreme başarısı")
        assert pico.outcome == "üreme başarısı"

    def test_etiket_etiketi_doldurulmamis_bileseni_bos_birakir(self):
        pico = parse_pico("pop: keklik")
        assert pico.population == "keklik"
        assert pico.outcome == ""


class TestTurkceAnahtarKelimeler:
    """Serbest Türkçe metin boş PICO'ya düşmemeli."""

    def test_gercek_tez_basligi_bos_pico_uretmez(self):
        pico = parse_pico(GERCEK_BASLIK)
        assert pico.non_empty(), (
            "Türkçe tez başlığı boş PICO'ya dönüştü: CLI'nin kendi tez "
            "dili onun kendi arama katmanını çalıştıramıyor."
        )

    def test_yerlestirme_maruziyeti_tespit_edilir(self):
        pico = parse_pico(GERCEK_BASLIK)
        assert "yerleştir" in pico.intervention

    def test_hayatta_kalma_sonuc_olarak_taninir(self):
        pico = parse_pico(GERCEK_BASLIK)
        assert "hayatta kal" in pico.outcome

    def test_ureme_basarisı_sonuc_olarak_taninir(self):
        pico = parse_pico("üreme başarısı kınalı kekliklerde nasıl ölçülür?")
        assert "üreme" in pico.outcome

    def test_karsilastirma_terimi_taninir(self):
        pico = parse_pico("yerli popülasyon ile karşılaştırıldığında hayatta kalma")
        assert "karşılaştır" in pico.comparison

    def test_alan_terimi_bicak_dizisi_yakalar(self):
        pico = parse_pico("saha çalışması biçiminde izlenen popülasyon")
        assert "saha" in pico.study_design.lower()

    def test_populasyon_terimi_taninir(self):
        pico = parse_pico("doğal popülasyondaki bireyler")
        assert "popülasyon" in pico.population

    def test_bosluk_doldurulmamis_bilesen_hic_uremez(self):
        """Eşleşme yoksa alan boş kalmalı — uydurma terin üretilmez."""
        pico = parse_pico("alelik analizi")
        assert pico.to_dict() == dict.fromkeys(pico.to_dict(), "")


class TestIngilizceGeriyeUyum:
    """Mevcut İngilizce davranış bozulmamalı."""

    def test_ingilizce_cumle_hala_dolu_pico_verir(self):
        pico = parse_pico(INGILIZCE_CUMLE)
        assert pico.non_empty()
        assert "elderly" in pico.population
        assert "outcome" in pico.outcome
        assert "clinic" not in pico.context  # yoksa olmalı, ama kırılmamalı

    def test_etiketli_ve_etiketsiz_ayni_dili_verir(self):
        """Serbest metin de aynı PICO'yu vermeli; etiketler kısayol."""
        serbest = parse_pico(
            "elderly patients outcome quality of life cognitive therapy"
        )
        etiketli = parse_pico("pop: elderly patients, outcome: quality of life")
        assert etiketli.population == "elderly patients"
        assert "elderly" in serbest.population
        assert "quality of life" in etiketli.outcome
        assert "quality of life" in serbest.outcome


class TestEtiketOnceligi:
    """Yazarın yazdığı, heuristiğin tahmini yener."""

    def test_etiketli_deger_heuristigi_ezmez(self):
        """`outcome: keklik` yazıldıysa değer `keklik` olmalı.

        Serbest metinde `outcome` kelimesi regex'e takılıp çevresini
    kırpar. Açık etiket yazara niyetini bildirdiği için kazanır.
        """
        pico = parse_pico("outcome: Alectoris chukar translocations")
        assert pico.outcome == "Alectoris chukar translocations"

    def test_etiket_yoksa_heuristik_devreye_girer(self):
        pico = parse_pico(INGILIZCE_CUMLE)
        assert pico.population  # etiket yok, heuristik çalıştı


class TestGirdiSinirlari:
    """Bozuk girdi çökme yapmamalı, uydurma üretmemeli."""

    @pytest.mark.parametrize("bos", ["", "   ", "\n", "\t  \n "])
    def test_bos_girdi_bos_pico(self, bos):
        assert parse_pico(bos).to_dict() == dict.fromkeys(
            parse_pico(bos).to_dict(), ""
        )

    def test_yalniz_etiket_girdisi_cokmez(self):
        """`pop:` sonrası boşsa bile hata vermemeli."""
        pico = parse_pico("pop:")
        assert pico.population == ""

    def test_bilinmeyen_etiket_yok_sayilir(self):
        """`foo: bar` çökmeye yol açmamalı, PICO boş kalmalı."""
        pico = parse_pico("foo: bar baz")
        assert pico.population == ""
        assert pico.outcome == ""

    def test_noktalama_etiketleri_bozmaz(self):
        pico = parse_pico("pop: keklik; outcome: üreme başarısı.")
        assert pico.population == "keklik"
        assert "üreme" in pico.outcome
        assert pico.outcome.endswith(".")


class TestCLIBoslukDenetimi:
    """`--pico` dalı da boşluğu denetlemeli (RQ dalı zaten denetliyor)."""

    def test_etiketsiz_dogru_sozdeki_pico_reddedilir(self):
        from argparse import Namespace

        from tools.atw.cli import main as cli

        args = Namespace(pico="alelik analizi", rq=None, json=False)
        pico, hata = cli._aramaya_pico(args, {"research_questions": []})
        assert hata is not None, (
            "`--pico` boş PICO'ya düşüyor ve `cmd_search` sessizce "
            "genel/bozuk bir arama çalıştıracak."
        )
        assert pico is None

    def test_etiketli_pico_kabul_edilir(self):
        from argparse import Namespace

        from tools.atw.cli import main as cli

        args = Namespace(pico="pop: Alectoris chukar, outcome: survival", rq=None)
        pico, hata = cli._aramaya_pico(args, {"research_questions": []})
        assert hata is None
        assert pico is not None and pico.non_empty()
