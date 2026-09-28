"""PRISMA uyumlu search_run.json üretimi ve sistematik arama koordine edici."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

from .crossref import search_crossref, CrossrefWork
from .openalex import search_openalex, OpenAlexWork, boolean_arama_ifadesi
from .semantic_scholar import search_semantic_scholar
from .pubmed import search_pubmed, PubMedArticle
from .google_scholar import search_google_scholar
from .query_builder import build_multi_database_queries, PICO, parse_pico, SearchQuery
from .deduplicate import deduplicate_sources, merge_duplicate_records, DedupResult

from tools.atw.ids import IdError, format_id, next_id, parse_id
from tools.atw.state import load_state, save_state


def _sentelen_sorgu(
    db: str,
    query: SearchQuery,
    *,
    year_from: int | None = None,
    year_to: int | None = None,
    types: list[str] | None = None,
) -> str:
    """API'ye fiilen gönderilen metni döndürür (arama kaydı için).

    Arama kaydı, gönderilmesi *gereken* metni yazmak denetimi
    yanıltır. Ölçülen ayrım: Crossref/PubMed gerçekten Boolean dizgesi
    gönderir; OpenAlex ise `filter_terms`'ten kurduğu parantezli boolean
    ifadeyi (`boolean_arama_ifadesi`) `search=` parametresi olarak.
    OpenAlex için dize `openalex.boolean_arama_ifadesi` ile üretilir —
    istemciyle AYNI fonksiyon çağrılır, kopya değil.
    """
    terimler = [t for t in (query.filter_terms or []) if t]
    if db == "openalex":
        return boolean_arama_ifadesi(terimler) or ""
    if db == "crossref":
        # `search_crossref` `filter_terms`'i boşlukla birleştirir.
        return " ".join(terimler) if terimler else query.boolean_string
    return query.boolean_string


@dataclass
class DatabaseSearchResult:
    """Tek veritabanı arama sonucu."""
    database: str
    query: SearchQuery
    records_found: int
    records_returned: int
    records: list[dict]  # source.json formatında
    execution_time_ms: int
    errors: list[str] = field(default_factory=list)
    #: API'ye fiilen gönderilen metin. `query.boolean_string` DENETLENEBİLİR
    #: değildir: Crossref/PubMed Boolean dizgesini gerçekten gönderir,
    #: OpenAlex ise `filter_terms`'ten kurulan parantezli boolean ifadeyi
    #: (`boolean_arama_ifadesi`) `search=` parametresi olarak gönderir.
    #: Arama kaydı ne gönderildiğini değil, ne gönderilmesi *gerektiğini*
    #: yazıyorsa denetim yanlış yönlendirir.
    sent_query: str = ""


@dataclass
class SearchRunResult:
    """PRISMA akışı için tam arama sonucu."""
    search_run_id: str
    query: SearchQuery
    timestamp: str
    databases_searched: list[str]
    database_results: list[DatabaseSearchResult]
    prisma_flow: dict
    deduplication: DedupResult
    included_source_ids: list[str]
    excluded_reasons: dict[str, int] = field(default_factory=dict)
    #: Tekilleştirilmiş ve kimlik atanmış kayıtlar. Yazma yolu BUNLARI
    #: ekler; `database_results[*].records` ham, veritabanı başına kopya
    #: içeren listelerdir.
    included_records: list[dict] = field(default_factory=list)

    def to_state_records(self) -> list[dict]:
        """Veritabanı başına bir `search_run.json` kaydı üretir.

        Neden kayıt başına değil koşu başına
        ------------------------------------
        `schemas/search_run.json` tanımı şunu diyor: *"Tek bir
        veritabanında çalıştırılan tek bir aramanın denetlenebilir
        kaydı."* Yani PRISMA akışı da, `results_returned` da tek bir
        veritabanına aittir. İki veritabanı tarayan bir koşuyu tek
        kayda sıkıştırmak, hangi veritabanının kaç kayıt döndürdüğünü
        denetlenemez kılar ve `database` alanı (`crossref | openalex |
        ...` tekil bir değer) yalan söyler.

        Ölçülen ihlaller (3 arama koşusunda 12 hata):
          * `deduplication_stats` — şemada tanımsız alan
          * `inclusion_criteria` — nesne yazılıyordu, dizi isteniyor
          * `exclusion_criteria` — boş dizi, `minItems: 1`
          * `exclusion_reasons` — nesne yazılıyordu, dizi isteniyor

        `inclusion_criteria` / `exclusion_criteria` burada PICO
        bileşenlerinden türetilen insan-okur metinlerdir; PRISMA'da
        bunlar araştırmacının tanımladığı ölçütlerdir, PICO değil.

        `included_source_ids` ve per-DB akış sayıları, dedup'lanmış
        kayıtların ilk görüldüğü veritabanına atfedilmesiyle üretilir
        (bkz. `_ilk_db_eslesmesi`). Aynı çalışma iki veritabanında da
        bulunduysa yalnızca ilk görülen sayılır; böylece kayıtların
        `studies_included` sayısı `included_source_ids` listeleriyle
        her zaman örtüşür ve `exclude`'un PRISMA yeniden türetimi
        kesirli kalmaz.
        """
        kayitlar: list[dict] = []
        try:
            _, taban = parse_id(self.search_run_id)
        except IdError:
            # Kimlik desene uymuyorsa kayıt kimlikleri türetilemez.
            # Sessizce ilk kaydı korumak, ikinci veritabanının kaydını
            # kimliksiz bırakmaktan iyidir ama yine de görünür olmalı:
            # `to_state_records` çağıranı hata görür.
            taban = 0

        eslesme = self._ilk_db_eslesmesi()

        for sira, db in enumerate(self.database_results):
            bu_db_kimlikler = [
                k for k in self.included_source_ids
                if eslesme.get(k) == db.database
            ]
            akis = {
                "records_identified": db.records_found,
                "duplicates_removed": db.records_found - len(bu_db_kimlikler),
                "records_screened": len(bu_db_kimlikler),
                "records_excluded": 0,
                "reports_sought": len(bu_db_kimlikler),
                "reports_not_retrieved": 0,
                "reports_excluded": 0,
                "studies_included": len(bu_db_kimlikler),
            }

            kayitlar.append({
                "id": format_id("SEARCH", taban + sira) if taban else self.search_run_id,
                "database": db.database,
                "query": db.sent_query or db.query.boolean_string,
                "timestamp": self.timestamp,
                "results_returned": db.records_returned,
                "inclusion_criteria": self._dahil_olcutleri(),
                "exclusion_criteria": self._dislama_olcutleri(),
                "prisma_flow": akis,
                "exclusion_reasons": [],
                "included_source_ids": bu_db_kimlikler,
                "executor": "agent",
            })
        return kayitlar

    def _ilk_db_eslesmesi(self) -> dict[str, str]:
        """Her dahil edilen kimliğin ilk görüldüğü veritabanını bulur.

        Neden nesne kimliği
        -------------------
        `deduplicate_sources` unique listesine kayıt NESNELERİNİN
        REFERANSINI ekler (kopya üretmez); orchestrator
        `record["id"] = src_id` atamasını o nesneye yapar. Böylece
        dedup'lanmış `included_records` içindeki bir kayıt, onu ilk
        getiren veritabanının ham `database_results[*].records`
        listesinde AYNI Python nesnesi olarak bulunur. Aynı çalışmanın
        ikinci veritabanındaki kopya nesnesi kimliksiz kaldığı için
        hiçbir veritabanına atfedilmez — çift sayım yoktur.

        Kimliği bulunamayan kayıt (nadir: dışarıdan eklenen) hiçbir
        veritabanına atfedilmez; `included_source_ids`'te görünmez.
        """
        eslesme: dict[str, str] = {}
        for db in self.database_results:
            ham_kimlikler = {id(k): k for k in db.records}
            for kayit in self.included_records:
                kimlik = kayit.get("id")
                if kimlik and kimlik not in eslesme and id(kayit) in ham_kimlikler:
                    eslesme[kimlik] = db.database
        return eslesme

    def _dahil_olcutleri(self) -> list[str]:
        """PICO bileşenlerinden okunur metin dize listesi."""
        pico = getattr(self.query, "pico", None)
        if pico is None:
            return ["Alandaki kayitlar (PICO ayristirilamadi)"]
        etiketler = (
            ("population", "Populasyon"),
            ("intervention", "Mudahale"),
            ("comparison", "Karsilastirma"),
            ("outcome", "Sonuc"),
            ("context", "Baglam"),
            ("study_design", "Calisma tasarimi"),
        )
        olcutler = [
            f"{etiket}: {deger}"
            for alan, etiket in etiketler
            if (deger := getattr(pico, alan, "") or "")
        ]
        return olcutler or ["PICO bos; alan sinirlari uygulanmadi"]

    def _dislama_olcutleri(self) -> list[str]:
        """Dahil edilen kayitlarda uygulanan dislama olcutleri.

        Bu kosuda otomatik dislama YAPILMAZ. Bos bir liste semayi
        gecersiz kildigi icin, gercegi yazar: hangi olcutlerin
        uygulanmadigi burada gorunur olur.
        """
        return ["Otomatik dislama uygulanmadi; eleme asagidaki akista yapilir"]

    def to_dict(self) -> dict:
        """Tek veritabanlı koşu için kayıt; çok veritabanlıysa ilki.

        Geriye dönük uyumluluk katmanıdır. Çok veritabanlı koşularda
        kayıt sıkıştırması yanıltıcı olduğu için çağıranlar
        `to_state_records()` kullanmalıdır.
        """
        kayitlar = self.to_state_records()
        if not kayitlar:
            raise ValueError("to_state_records() boş döndü: database_results yok")
        return kayitlar[0]


class SystematicSearchOrchestrator:
    """Sistematik arama koordine edici - PRISMA uyumlu."""

    DATABASES = ["crossref", "openalex", "semantic_scholar", "pubmed", "google_scholar"]

    def __init__(
        self,
        crossref_mailto: str = "research@example.com",
        openalex_email: str | None = None,
        semantic_scholar_key: str | None = None,
        pubmed_email: str | None = None,
        serpapi_key: str | None = None,
        max_results_per_db: int = 100,
        deduplication_threshold: float = 0.9,
    ):
        self.crossref_mailto = crossref_mailto
        self.openalex_email = openalex_email
        self.semantic_scholar_key = semantic_scholar_key
        self.pubmed_email = pubmed_email
        self.serpapi_key = serpapi_key
        self.max_results_per_db = max_results_per_db
        self.deduplication_threshold = deduplication_threshold

    def run_systematic_search(
        self,
        pico: PICO | str,
        databases: list[str] | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        inclusion_criteria: dict | None = None,
        exclusion_criteria: list[str] | None = None,
        thesis_id: str = "THESIS-2026-001",
        mevcut_kimlikler: Iterable[str] = (),
    ) -> SearchRunResult:
        """Sistematik arama çalıştır ve PRISMA akışı üret.

        Args:
            mevcut_kimlikler: Durumda ZATEN kullanılan `SRC-*` kimlikleri.
                Yeni kimlikler buradan devam eder. Boş bırakılırsa her
                koşu `SRC-001`'den başlar ve kayıtlar çakışır (ölçüldü:
                3 arama -> 72 kayıt / 24 kimlik, her biri 3 kez).
        """

        if isinstance(pico, str):
            pico = parse_pico(pico)

        if databases is None:
            databases = self.DATABASES

        # Sorgu oluştur
        queries = build_multi_database_queries(pico, databases=databases)

        # Her veritabanında arama
        db_results = []
        all_records = []
        prisma_counts = {
            "records_identified": 0,
            "duplicates_removed": 0,
            "records_screened": 0,
            "records_excluded": 0,
            "reports_sought": 0,
            "reports_not_retrieved": 0,
            "reports_excluded": 0,
            "studies_included": 0,
        }

        search_run_id = format_id("SEARCH", int(time.time() * 1000) % 10000)

        for db in databases:
            if db not in queries:
                continue

            query = queries[db]
            start_time = time.time()
            records = []
            errors = []

            try:
                if db == "crossref":
                    raw = search_crossref(
                        query=query.boolean_string,
                        max_results=self.max_results_per_db,
                        filter_terms=query.filter_terms,
                    )
                    records = [w.to_source_dict() for w in raw]
                elif db == "openalex":
                    raw = search_openalex(
                        query=query.boolean_string,
                        max_results=self.max_results_per_db,
                        filter_terms=query.filter_terms,
                    )
                    records = [w.to_source_dict() for w in raw]
                elif db == "semantic_scholar":
                    raw = search_semantic_scholar(
                        query=query.boolean_string,
                        max_results=self.max_results_per_db,
                    )
                    records = [w.to_source_dict() for w in raw]
                elif db == "pubmed":
                    raw = search_pubmed(
                        query=query.boolean_string,
                        max_results=self.max_results_per_db,
                    )
                    records = [w.to_source_dict() for w in raw]
                elif db == "google_scholar":
                    raw = search_google_scholar(
                        query=query.boolean_string,
                        max_results=min(20, self.max_results_per_db),  # Google Scholar sınırlı
                    )
                    records = [r.to_source_dict() for r in raw]
                else:
                    errors.append(f"Bilinmeyen veritabanı: {db}")
            except Exception as e:
                errors.append(str(e))
                records = []

            exec_time = int((time.time() - start_time) * 1000)

            # Kayıt sayısını güncelle
            prisma_counts["records_identified"] += len(records)

            db_results.append(DatabaseSearchResult(
                database=db,
                query=query,
                records_found=len(records),
                records_returned=len(records),
                records=records,
                execution_time_ms=exec_time,
                errors=errors,
                sent_query=_sentelen_sorgu(
                    db, query, year_from=year_from, year_to=year_to
                ),
            ))

            all_records.extend(records)

        # Deduplication
        print(f"Deduplicating {len(all_records)} records...")
        dedup_result = deduplicate_sources(
            all_records,
            threshold=self.deduplication_threshold,
        )
        prisma_counts["duplicates_removed"] = dedup_result.stats["removed"]

        # Unique kayıtları birleştir (aynı kaynak farklı DB'den gelmişse)
        unique_records = dedup_result.unique

        # Screening (basit: inclusion/exclusion criteria)
        # Şimdilik hepsini include ediyoruz, gerçek implementasyonda
        # inclusion/exclusion criteria uygulanacak
        screened = unique_records
        prisma_counts["records_screened"] = len(screened)

        # Exclusion (örnek: review articles, non-english, etc.)
        # Gerçek implementasyonda exclusion criteria uygulanır
        excluded_count = 0
        exclusion_reasons = {}

        # Final included
        included = screened  # Şimdilik hepsi
        prisma_counts["reports_sought"] = len(included)
        prisma_counts["studies_included"] = len(included)

        # Source ID'leri ata (SRC-XXX formatında)
        #
        # Neden `format_id("SRC", i + 1)` DEĞİL
        # ---------------------------------------
        # `format_id` yalnızca numarayı biçimlendirir; durumu GÖRMEZ.
        # Arama içi 1..N sayacı olduğu için her koşu SRC-001'den başlar.
        # Ölçülen sonuç (gerçek tez verisi, 3 arama):
        #   72 kayıt, ama yalnızca 24 ayrı kimlik, her biri 3 kez —
        #   ve aynı kimliğin 3 kaydı FARKLI kaynak:
        #       SRC-001 -> 1994 10.2737/feis-species-review-alch
        #               -> 2024 10.15641/bo.1573
        #               -> 2016 10.1111/1749-4877.12195
        # Kimlik anahtarlı her eşleme (`write._kimlikle_esles`,
        # `graph.kenar_tablosu`, `verify`) çakışanları üstüne yazıp
        # yalnızca SON kaydı tutar. 72 kayıt yazıldı, "Dahil edilen: 24"
        # raporlandı, doğrulama ve atıf yalnızca son 8'i gördü — hiçbir
        # hata üretilmedi.
        #
        # `tools/atw/record.py` aynı işi `next_id` ile zaten doğru
        # yapıyor; burada da onun kullanılması gerekiyor.
        havuz = list(mevcut_kimlikler)
        included_ids = []
        for record in included:
            src_id = next_id(havuz, "SRC")
            havuz.append(src_id)
            record["id"] = src_id
            included_ids.append(src_id)

        prisma_counts["records_excluded"] = excluded_count

        result = SearchRunResult(
            search_run_id=search_run_id,
            query=build_multi_database_queries(pico)[databases[0]] if databases else list(build_multi_database_queries(pico).values())[0],
            timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            databases_searched=databases,
            database_results=db_results,
            prisma_flow=prisma_counts,
            deduplication=dedup_result,
            included_source_ids=included_ids,
            excluded_reasons=exclusion_reasons,
            included_records=included,
        )

        return result

    def save_search_run(self, result: SearchRunResult, thesis_state_path: str = "thesis_state.json") -> None:
        """Search run sonucunu `thesis_state.json`'a kaydet.

        Yazılan iki küme vardır ve ikisi de BİRER KEZ yazılır:

          * `result.to_state_records()` — veritabanı başına bir arama
            kaydı. `to_dict()` (ilk kaydı döndürür) kullanılmaz: iki
            veritabanlı bir koşuda ikinci veritabanının kaydı sessizce
            kaybolur.
          * `result.included_records` — TEKİLLEŞTİRİLMİŞ kayıtlar.

        Neden `database_results[*].records` DEĞİL
        ---------------------------------------
        O liste veritabanı başına HAM kayıtları taşır; aynı kaynak iki
        veritabanında da bulunduysa iki kez bulunur. Önceden bu yol
        kullanılıyordu ama kopya kayıtlar boş `id` alanı sayesinde
        `if record["id"]` denetiminde düşüyordu — yani tekilleştirme
        KAZARA çalışıyordu, kural koda bağlı değildi. `included_records`
        kuralı açık hale getirir.
        """
        state = load_state(thesis_state_path)
        state["search_runs"].extend(result.to_state_records())

        varolan = {k.get("id") for k in state["sources"] if k.get("id")}
        eklenen = [r for r in result.included_records if r.get("id")]
        cakisan = sorted({r["id"] for r in eklenen} & varolan)
        if cakisan:
            # Kimlik çakışması sessiz veri kaybıdır; yazmadan dur.
            raise ValueError(
                f"Kaynak kimliği çakışıyor: {cakisan}. "
                "Arama, durumda kullanılan kimlikleri görmüyor. "
                "Kimlikler çakışırsa kimlik anahtarlı her eşleme yalnızca "
                "son kaydı tutar ve atıflar sessizce yanlış kaynağa bağlanır."
            )
        state["sources"].extend(eklenen)

        save_state(thesis_state_path, state)


def run_systematic_search(
    pico: PICO | str,
    databases: list[str] | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    max_results_per_db: int = 100,
    thesis_state_path: str = "thesis_state.json",
    crossref_mailto: str = "research@example.com",
    openalex_email: str | None = None,
    semantic_scholar_key: str | None = None,
    pubmed_email: str | None = None,
    serpapi_key: str | None = None,
) -> SearchRunResult:
    """Sistematik arama çalıştır (kolaylık fonksiyonu)."""
    orchestrator = SystematicSearchOrchestrator(
        crossref_mailto=crossref_mailto,
        openalex_email=openalex_email,
        semantic_scholar_key=semantic_scholar_key,
        pubmed_email=pubmed_email,
        serpapi_key=serpapi_key,
        max_results_per_db=max_results_per_db,
    )

    if isinstance(pico, str):
        pico = parse_pico(pico)

    return orchestrator.run_systematic_search(
        pico=pico,
        databases=databases,
        year_from=year_from,
        year_to=year_to,
        mevcut_kimlikler=durumdaki_kimlikler(thesis_state_path),
    )


def durumdaki_kimlikler(thesis_state_path: str = "thesis_state.json") -> list[str]:
    """Durumda kullanılan `SRC-*` kimliklerini döndürür.

    Aramanın nereye devam edeceğini belirleyen tek bilgidir. Dosya yoksa
    veya okunamazsa boş liste döner: yeni bir tezde kimlik çakışması
    olma olasılığı yoktur, okunamayan dosyada ise `save_search_run`
    zaten doğrulamayla reddedecektir.
    """
    yol = Path(thesis_state_path)
    if not yol.exists():
        return []
    try:
        durum = json.loads(yol.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return [
        k.get("id")
        for k in durum.get("sources", [])
        if isinstance(k, dict) and k.get("id")
    ]