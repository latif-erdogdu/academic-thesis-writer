"""OpenAlex API istemcisi.

API: https://api.openalex.org/
Rate limit: 10 req/s (anonymous), 100 req/s (with API key/email)
Docs: https://docs.openalex.org/
"""
from __future__ import annotations

import time
import logging
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import quote_plus

import requests

from .kayit import sema_uyumlu

logger = logging.getLogger(__name__)


@dataclass
class OpenAlexWork:
    """OpenAlex'ten gelen bir çalışma (work) kaydı."""
    id: str  # https://openalex.org/W1234567890
    doi: Optional[str]
    title: str
    authors: list[dict]
    year: Optional[int]
    journal: Optional[str]
    venue: Optional[str]
    volume: Optional[str]
    issue: Optional[str]
    pages: Optional[str]
    cited_by_count: int
    is_open_access: bool
    open_access_url: Optional[str]
    abstract: Optional[str]
    keywords: list[dict]
    concepts: list[dict]
    institutions: list[dict]
    countries: list[str]
    type: str
    type_crossref: Optional[str]
    indexed_in: list[str]
    created_date: str
    updated_date: str
    referenced_works: list[str]
    related_works: list[str]
    grants: list[dict]
    datasets: list[dict]
    versions: list[dict]

    @classmethod
    def from_api(cls, item: dict) -> "OpenAlexWork":
        """OpenAlex API yanıtından OpenAlexWork oluştur."""
        # Yazarları normalize et
        authors = []
        for auth in item.get("authorships", []):
            author = auth.get("author", {})
            institutions = [inst.get("display_name", "") for inst in auth.get("institutions", [])]
            authors.append({
                "id": author.get("id", ""),
                "orcid": author.get("orcid", "").replace("https://orcid.org/", "") if author.get("orcid") else "",
                "display_name": author.get("display_name", ""),
                "institutions": institutions,
                "raw_affiliation_string": auth.get("raw_affiliation_string", ""),
            })

        # Kavramlar (concepts)
        concepts = []
        for c in item.get("concepts", []):
            concepts.append({
                "id": c.get("id", ""),
                "display_name": c.get("display_name", ""),
                "level": c.get("level", 0),
                "score": c.get("score", 0.0),
            })

        # Kurumlar
        institutions = []
        for auth in item.get("authorships", []):
            for inst in auth.get("institutions", []):
                institutions.append({
                    "id": inst.get("id", ""),
                    "display_name": inst.get("display_name", ""),
                    "type": inst.get("type", ""),
                    "country_code": inst.get("country_code", ""),
                })

        # Ülkeler
        countries = list(set(
            inst.get("country_code", "")
            for auth in item.get("authorships", [])
            for inst in auth.get("institutions", [])
            if inst.get("country_code")
        ))

        # Open Access bilgisi
        oa = item.get("open_access", {}) or {}
        oa_url = oa.get("oa_url")

        return cls(
            id=item.get("id", ""),
            doi=item.get("doi"),
            title=item.get("display_name", "") or item.get("title", ""),
            authors=authors,
            year=item.get("publication_year"),
            journal=item.get("host_venue", {}).get("display_name") if item.get("host_venue") else None,
            venue=item.get("host_venue", {}).get("display_name") if item.get("host_venue") else None,
            volume=item.get("biblio", {}).get("volume"),
            issue=item.get("biblio", {}).get("issue"),
            pages=item.get("biblio", {}).get("first_page") + "-" + item.get("biblio", {}).get("last_page")
                if item.get("biblio", {}).get("first_page") and item.get("biblio", {}).get("last_page")
                else item.get("biblio", {}).get("first_page"),
            cited_by_count=item.get("cited_by_count", 0),
            is_open_access=item.get("open_access", {}).get("is_oa", False),
            open_access_url=oa_url,
            abstract=item.get("abstract"),
            keywords=item.get("keywords", []) or [],
            concepts=concepts,
            institutions=institutions,
            countries=countries,
            type=item.get("type", ""),
            type_crossref=item.get("type_crossref"),
            indexed_in=item.get("indexed_in", []) or [],
            created_date=item.get("created_date", ""),
            updated_date=item.get("updated_date", ""),
            referenced_works=item.get("referenced_works", []) or [],
            related_works=item.get("related_works", []) or [],
            grants=item.get("grants", []) or [],
            datasets=item.get("datasets", []) or [],
            versions=item.get("versions", []) or [],
        )

    def to_source_dict(self) -> dict:
        """source.json şemasına uygun dict'e dönüştür."""
        author_strings = []
        for a in self.authors:
            name = a.get("display_name", "")
            if a.get("orcid"):
                name += f" (ORCID: {a['orcid']})"
            author_strings.append(name)

        # Dergi/venue
        journal = self.journal or self.venue

        # Sayfa aralığı
        page_list = None
        if self.pages:
            try:
                parts = self.pages.split("-")
                start = int(parts[0])
                end = int(parts[1]) if len(parts) > 1 else start
                page_list = list(range(start, end + 1))
            except (ValueError, IndexError):
                pass

        return sema_uyumlu({
            "id": "",
            "title": self.title,
            "authors": author_strings,
            "year": self.year,
            "journal": journal,
            "publisher": self.host_venue_publisher() if hasattr(self, 'host_venue_publisher') else None,
            "doi": self.doi,
            "url": f"https://openalex.org{self.id.split('/')[-1]}" if self.id else None,
            "source_type": self._map_type(),
            "publication_status": "published",
            "retraction_status": "not_retracted",
            "correction_status": "none",
            "supersedes_source_id": None,
            "verified": False,
            "verification": {
                "status": "pending",
                "bibliographic_match": 0.0,
                "doi_match": bool(self.doi),
                "author_match": None,
                "title_match": None,
                "year_match": None,
                "journal_match": None,
                "verified_at": "",
                "verification_sources": ["openalex"],
            },
            "verification_notes": f"OpenAlex metadata: {self.id}",
            "supports_claims": [],
            "evidence_ids": [],
            "page_numbers": page_list,
            "volume": self.volume,
            "issue": self.issue,
            "pages": self.pages,
            "edition": "",
            "isbn": "",
            "location_verified": True,
            "access_date": "",
            "language": "en",
            "peer_reviewed": self.type in ("journal-article", "peer-review"),
        })

    def _map_type(self) -> str:
        mapping = {
            "journal-article": "article",
            "book-chapter": "book_chapter",
            "book": "book",
            "proceedings-article": "conference",
            "proceedings": "conference",
            "report": "report",
            "dataset": "dataset",
            "preprint": "preprint",
            "peer-review": "article",
            "other": "other",
        }
        return mapping.get(self.type, "other")

    def host_venue_publisher(self) -> Optional[str]:
        """Host venue publisher (eksik alan, API'den gelirse eklenir)."""
        return None


class OpenAlexClient:
    """OpenAlex API istemcisi."""

    BASE_URL = "https://api.openalex.org"
    DEFAULT_HEADERS = {
        "User-Agent": "AcademicThesisWriter/1.0",
        "Accept": "application/json",
    }

    def __init__(
        self,
        email: str | None = None,
        api_key: str | None = None,
        rate_limit: float = 10.0,  # req/s (anonymous)
        timeout: int = 30,
        retry_deneme: int = 3,
        retry_gecikme_sn: float = 30.0,
    ):
        self.email = email
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.retry_deneme = max(1, retry_deneme)
        self.retry_gecikme_sn = retry_gecikme_sn
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        self._last_request = 0.0

        if email:
            self.session.params = {"mailto": email}
        if api_key:
            self.session.headers["Authorization"] = f"Bearer {api_key}"

    def _throttle(self):
        elapsed = time.time() - self._last_request
        min_interval = 1.0 / self.rate_limit
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

    def _get(self, path: str, params: dict | None = None) -> dict:
        """OpenAlex'e GET; 429'a karşı sınırlı geri çekilme + yeniden deneme.

        Neden yeniden deneme
        --------------------
        Anonim havuzda OpenAlex periyodik 429 döndürür (ölçüldü
        2026-09-28: SEARCH-1724/4775 openalex kayıt=0 — tek atışta
        kalıcı boşluk yazılıyordu). 429 geçicidir; geri çekilme ile
        yeniden deneme, kayıtın "meşru boş sonuç" gibi görünmesini
        engeller. Diğer hata kodları (4xx/5xx) kalıcıdır — yeniden
        denenmez, `raise_for_status` yükseltir.
        """
        self._throttle()
        url = f"{self.BASE_URL}{path}"
        for deneme in range(1, self.retry_deneme + 1):
            logger.debug(f"GET {url} params={params}")
            response = self.session.get(url, params=params, timeout=self.timeout)
            self._last_request = time.time()
            if response.status_code == 429 and deneme < self.retry_deneme:
                gecikme = self.retry_gecikme_sn * deneme
                logger.warning(
                    f"OpenAlex 429 (deneme {deneme}/{self.retry_deneme}); "
                    f"{gecikme:.0f}s sonra yeniden deneniyor"
                )
                time.sleep(gecikme)
                continue
            response.raise_for_status()
            return response.json()

    def works(
        self,
        filter: dict | str | None = None,
        search: str | None = None,
        per_page: int = 25,
        page: int = 1,
        sort: str = "relevance_score:desc",
        select: list[str] | None = None,
        sample: int | None = None,
        seed: int | None = None,
    ) -> dict:
        """Works endpoint'ini sorgula.

        Args:
            filter: Filtreler (örn: {"type": "journal-article", "from_publication_date": "2020-01-01"})
            search: Full-text arama
            per_page: Sayfa başına sonuç (max 200)
            page: Sayfa numarası
            sort: Sıralama (relevance_score:desc, cited_by_count:desc, publication_date:desc)
            select: Alan seçimi
            sample: Rastgele örnekleme
            seed: Rastgele tohum
        """
        params = {
            "per-page": min(per_page, 200),
            "page": page,
            "sort": sort,
        }
        if filter:
            # OpenAlex filter formatı: key:value,key:value. Aynı anahtar
            # birden çok kez geçebilir (`title_and_abstract.search` VE
            # zinciri), bu yüzden SÖZLÜK değil DİZE kabul edilir.
            if isinstance(filter, str):
                params["filter"] = filter
            else:
                params["filter"] = ",".join(f"{k}:{v}" for k, v in filter.items())
        if search:
            params["search"] = search
        if select:
            params["select"] = ",".join(select)
        if sample:
            params["sample"] = sample
        if seed:
            params["seed"] = seed

        data = self._get("/works", params)
        return data

    def work_by_id(self, work_id: str) -> OpenAlexWork:
        """ID ile tek work getir."""
        # ID formatı: W1234567890 veya https://openalex.org/W1234567890
        clean_id = work_id.split("/")[-1] if "/" in work_id else work_id
        data = self._get(f"/works/{clean_id}")
        return OpenAlexWork.from_api(data)

    def works_by_dois(self, dois: list[str]) -> list[OpenAlexWork]:
        """DOI listesi ile work'ları getir (filter=doi:...)."""
        # OpenAlex filter=doi:doi1|doi2|... (OR mantığı)
        # Çok fazla DOI varsa chunk'la
        chunks = [dois[i:i+50] for i in range(0, len(dois), 50)]
        works = []
        for chunk in chunks:
            filter_dict = {"doi": "|".join(chunk)}
            data = self.works(filter=filter_dict, per_page=len(chunk))
            for item in data.get("results", []):
                works.append(OpenAlexWork.from_api(item))
        return works

    def authors(self, filter: dict | None = None, per_page: int = 25) -> dict:
        data = self._get("/authors", {"per-page": per_page, **(filter or {})})
        return data

    def institutions(self, filter: dict | None = None, per_page: int = 25) -> dict:
        data = self._get("/institutions", {"per-page": per_page, **(filter or {})})
        return data

    def concepts(self, filter: dict | None = None, per_page: int = 25) -> dict:
        data = self._get("/concepts", {"per-page": per_page, **(filter or {})})
        return data

    def sources(self, filter: dict | None = None, per_page: int = 25) -> dict:
        data = self._get("/sources", {"per-page": per_page, **(filter or {})})
        return data


AYRILMIS_SOZCUKLER = {"AND", "OR", "NOT"}


def boolean_arama_ifadesi(filter_terms: list[str]) -> str:
    """OpenAlex `search` parametresi için parantezli boolean ifade kurar.

    Her PICO bileşeni (ör. ``yerleştirme saldırım translocat release``)
    tokenlara bölünür ve ``(t1 OR t2 …)`` olarak kapatılır; bileşenler
    `` AND `` ile zincirlenir:

        (yerleştirme OR saldırım OR translocat OR release) AND (…)

    Neden: `title_and_abstract.search` süzgeci çok kelimeli değeri
    bitişik TAMLAMA olarak arar (ölçüldü, 2026-09-28): üretken PICO
    bileşenleri (Türkçe+İngilizce karışık, 3-7 kelime) hiçbir özette
    bitişik geçmediği için anahtar tekrarlı VE zinciri
    ``meta.count=0`` döndürüyordu. OpenAlex `search` parametresi
    ``(a OR b) AND (c OR d)`` yazımını destekler (resmi doküman); boşluk
    ayıracı AND'dir, işleçler BÜYÜK harf olmalıdır — `AYRILMIS_SOZCUKLER`
    içindeki bir sözcük ifadeyi bozmasın diye tırnaklanır.

    Args:
        filter_terms: `SearchQuery.filter_terms` — bileşen başına BİR
            temiz ifade (etiket/Boolean sözdizimi içermez).

    Returns:
        `` AND `` ile bağlı ``(…)`` grupları; girdi boşsa boş dize.
    """
    gruplar: list[str] = []
    for ifade in filter_terms or []:
        tokenlar = [
            f'"{t.upper()}"' if t.upper() in AYRILMIS_SOZCUKLER else t
            for t in ifade.split()
        ]
        if tokenlar:
            gruplar.append(f"({' OR '.join(tokenlar)})")
    return " AND ".join(gruplar)


def filtre_dizgesi(
    *,
    year_from: int | None = None,
    year_to: int | None = None,
    types: list[str] | None = None,
) -> str | None:
    """`filter=` parametresine gönderilecek ham dizeyi üretir (yıl/tip).

    NOT: Tam metin eşleşmesi bu fonksiyonun kapsamı DIŞINDADIR. Önceden
    `filter_terms` burada `title_and_abstract.search` anahtarına çevriliyor
    ve bileşen başına tekrarlanıyordu; ölçüldü (2026-09-28): çok kelimeli
    değer OpenAlex'te bitişik tamlama arandığı için üretken PICO'da
    ``meta.count=0``. Tam metin araması `boolean_arama_ifadesi`'nin
    ürettiği `search=` parametresine taşındı. Bu fonksiyon yalnız
    `from_publication_date`/`until_publication_date`/`type` süzgeçlerini
    üretir; bunlar `search=` ile VE olarak birleşir (farklı anahtarlar).

    Arama kaydının denetlenebilir olması için `search_openalex` ile
    `search_run._sentelen_sorgu` AYNI fonksiyonları çağırır. Sorgu
    dizesi kopyalanırsa denetim kaydı gerçeği yansıtmaz.
    """
    parcalar: list[str] = []
    if year_from:
        parcalar.append(f"from_publication_date:{year_from}-01-01")
    if year_to:
        parcalar.append(f"until_publication_date:{year_to}-12-31")
    if types:
        parcalar.append(f"type:{'|'.join(types)}")
    return ",".join(parcalar) or None


def search_openalex(
    query: str,
    max_results: int = 100,
    year_from: int | None = None,
    year_to: int | None = None,
    types: list[str] | None = None,
    email: str | None = None,
    filter_terms: list[str] | None = None,
) -> list[OpenAlexWork]:
    """OpenAlex'te arama yap ve OpenAlexWork listesi döndür.

    Neden `filter_terms` var
    -----------------------
    Ham `query` (kütüphane-genel Boolean dizgesi) doğrudan `search=`'e
    verilemez: `title:`/`abstract:` alan önekleri OpenAlex'te yok sayılır
    ve terimler torbalanır. Ölçülen sonuç (eski, 2026-09-28): 47 sonuç,
    neredeyse tamamı gürültü ("Nutritional modulation ... in poultry",
    "Chemical mutagenesis: a survey of the 1975-1976 literature").

    `filter_terms` verilirse `boolean_arama_ifadesi` her bileşeni
    ``(t1 OR t2 …)`` grubuna kapatıp `` AND `` ile zincirler ve bu
    ifade `search=` parametresine gider. Neden süzgeç değil: önceki
    uygulama `title_and_abstract.search` anahtarını bileşen başına
    tekrarlıyordu; OpenAlex çok kelimeli değeri bitişik TAMLAMA olarak
    aradığı için üretken PICO bileşenleri (Türkçe+İngilizce, 3-7 kelime)
    ölçülen 0 sonuç döndürüyordu (SEARCH-2982/9078/5201: openalex
    kayıt=0). Kısa tamlamalı deneme PICO'su ("alectoris chukar",
    "survival mortality") 22 ilgili kayıt verse de mekanizmanın kendisi
    kırılgandı; `(a OR b) AND (c OR d)` resmi `search` sözdizimi,
    bileşen içinde OR'u (eş anlamlılar) ve bileşenler arası AND'i tam
    olarak ifade eder.

    Args:
        query: Boolean dizgesi (yalnızca `filter_terms` verilmezse kullanılır).
        max_results: En çok kaç kayıt.
        year_from: Başlangıç yılı.
        year_to: Bitiş yılı.
        types: OpenAlex kayıt tipleri.
        email: Politika e-postası için.
        filter_terms: VE ile zincirlenecek temiz ifadeler (bileşen başına BİR).
    """
    client = OpenAlexClient(email=email)

    # Tam metin eşleşmesi `search=` parametresinde parantezli boolean
    # ifadeyle gider: filter_terms → `(t1 OR t2) AND (u1 OR u2)`.
    # `title_and_abstract.search` süzgeç anahtarı çok kelimeli değeri
    # bitişik TAMLAMA aradığı için kullanılmaz (ölçüldü 2026-09-28:
    # üretken PICO'da meta.count=0). Yıl/tip süzgeçleri `filter=`'de
    # kalır; `search_run._sentelen_sorgu` aynı fonksiyonları çağırdığı
    # için denetim kaydı gönderilen metinle aynı kalır.
    aranacak: str | None = query
    if filter_terms:
        aranacak = boolean_arama_ifadesi(filter_terms) or None

    filter_str = filtre_dizgesi(
        year_from=year_from,
        year_to=year_to,
        types=types,
    )

    all_works = []
    per_page = 200
    page = 1

    while len(all_works) < max_results:
        data = client.works(
            filter=filter_str,
            search=aranacak,
            per_page=per_page,
            page=page,
            sort="relevance_score:desc",
        )
        results = data.get("results", [])
        if not results:
            break

        for item in results:
            all_works.append(OpenAlexWork.from_api(item))
            if len(all_works) >= max_results:
                break

        page += 1
        if len(results) < per_page:
            break

    return all_works[:max_results]