"""Bibliyografik karşılaştırma fonksiyonları.

Kaynak kayıtları (source.json) ile veritabanı kayıtları (Crossref, OpenAlex, vb.)
arasında bibliyografik eşleşme skorunu hesaplar.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional

from rapidfuzz import fuzz, process

# Yıl regex
YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")

# DOI regex
DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)

# Stopwords for title comparison
TITLE_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "in", "for", "to", "with", "on", "by",
    "as", "at", "from", "into", "during", "including", "until", "against",
    "among", "throughout", "despite", "towards", "upon", "within", "without",
    "via", "per", "pro", "anti", "sub", "super", "inter", "intra", "trans",
    "over", "under", "after", "before", "between", "beyond", "but", "nor",
    "yet", "so", "than", "that", "this", "these", "those", "their", "there",
    "then", "than", "now", "how", "all", "any", "both", "each", "few", "more",
    "most", "other", "some", "such", "only", "own", "same", "so", "too", "very",
    "can", "will", "just", "don", "should", "would", "could", "may", "might",
    "must", "shall", "need", "dare", "ought", "used", "use", "using", "used"
}


@dataclass
class BibliographicMatch:
    """Bibliyografik eşleşme sonucu."""
    overall_score: float              # 0.0 - 1.0
    title_score: float                # 0.0 - 1.0
    author_score: float               # 0.0 - 1.0
    year_score: float                 # 0.0 - 1.0
    journal_score: float              # 0.0 - 1.0
    doi_match: bool                   # True/False
    details: dict                     # Detaylı skorlar ve notlar


def normalize_title(title: str) -> str:
    """Başlığı normalize et (küçük harf, noktalama temizle, stopwords çıkar)."""
    if not title:
        return ""
    title = title.lower()
    # Noktalama temizle
    title = re.sub(r"[^\w\s]", " ", title)
    # Çoklu boşlukları tek yap
    title = re.sub(r"\s+", " ", title)
    # Stopwords çıkar (opsiyonel - tam eşleşme için koru)
    words = [w for w in title.split() if w not in TITLE_STOPWORDS or len(w) > 3]
    return " ".join(words).strip()


def normalize_author(author: str) -> str:
    """Yazar adını normalize et (soyad + başharf)."""
    if not author:
        return ""
    author = author.lower().strip()
    # "Smith, John" -> "smith j"
    # "John Smith" -> "smith j"
    # "Smith J" -> "smith j"
    # "J. Smith" -> "smith j"
    parts = [p.strip() for p in re.split(r"[,\s]+", author) if p.strip()]
    if not parts:
        return ""
    if "," in author:
        surname = parts[0].replace(",", "")
        given = parts[1] if len(parts) > 1 else ""
    else:
        surname = parts[-1]
        given = parts[0] if len(parts) > 1 else ""
    initial = given[0] if given else ""
    return f"{surname} {initial}".strip()


def normalize_journal(journal: str) -> str:
    """Dergi adını normalize et."""
    if not journal:
        return ""
    journal = journal.lower()
    # Yaygın kısaltmaları genişlet
    abbreviations = {
        "j.": "journal",
        "proc.": "proceedings",
        "conf.": "conference",
        "int.": "international",
        "natl.": "national",
        "acad.": "academy",
        "soc.": "society",
        "assoc.": "association",
        "inst.": "institute",
        "univ.": "university",
        "dept.": "department",
        "rev.": "review",
        "lett.": "letters",
        "comm.": "communications",
        "trans.": "transactions",
    }
    for abbr, full in abbreviations.items():
        journal = journal.replace(abbr, full)
    # Noktalama temizle
    journal = re.sub(r"[^\w\s]", " ", journal)
    journal = re.sub(r"\s+", " ", journal)
    return journal.strip()


def extract_year(text: Any) -> Optional[int]:
    """Metinden yıl çıkar."""
    if not text:
        return None
    if isinstance(text, int):
        if 1900 <= text <= 2100:
            return text
        return None
    match = YEAR_PATTERN.search(str(text))
    if match:
        year = int(match.group())
        if 1900 <= year <= 2100:
            return year
    return None


def normalize_doi(doi: str) -> str:
    """DOI'yi normalize et."""
    if not doi:
        return ""
    doi = doi.lower().strip()
    for prefix in ["https://doi.org/", "http://doi.org/", "doi:", "doi "]:
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
            break
    return doi.strip()


def compare_titles(title1: str, title2: str) -> float:
    """İki başlığı karşılaştır (0.0 - 1.0)."""
    if not title1 or not title2:
        return 0.0
    # Normalize et
    t1 = normalize_title(title1)
    t2 = normalize_title(title2)
    if not t1 or not t2:
        return 0.0
    # Tam eşleşme
    if t1 == t2:
        return 1.0
    # Token-based Jaccard
    tokens1 = set(t1.split())
    tokens2 = set(t2.split())
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    jaccard = len(intersection) / len(union)
    # Fuzzy ratio da hesapla
    fuzzy = fuzz.ratio(t1, t2) / 100.0
    # Ağırlıklı ortalama
    return 0.7 * jaccard + 0.3 * fuzzy


def _soyadi_kokenli_eslesme(a: str, b: str) -> bool:
    """İki normalize yazar arasında soyadı kökenli eşleşme var mı?

    Kaynakça biçimi çoğu zaman yalnızca soyadı verir ("Vidal"), veritabanı
    ise "Soyad, Ad" biçimini ("Vidal, Jean J." -> "vidal j"). Bu iki biçim
    birebir eşit olmadığı için normalizasyon sonrası tam küme kesişimi
    boş kalır. Soyadı aynı olan yazarları eşleşmiş sayarız.
    """
    if not a or not b:
        return False
    if a == b:
        return True
    return a.split(" ")[0] == b.split(" ")[0]


def compare_authors(authors1: list[str], authors2: list[str]) -> float:
    """İki yazar listesi karşılaştır (0.0 - 1.0)."""
    if not authors1 or not authors2:
        return 0.0
    # Normalize et
    norm1 = [normalize_author(a) for a in authors1 if a]
    norm2 = [normalize_author(a) for a in authors2 if a]
    if not norm1 or not norm2:
        return 0.0
    # İlk 3 yazarı karşılaştır (genelde en önemli olanlar)
    set1 = set(norm1[:3])
    set2 = set(norm2[:3])
    if not set1 or not set2:
        return 0.0
    # Tam küme kesişimi
    union = set1 | set2
    kesisim = len(set1 & set2) / len(union) if union else 0.0
    # Soyadı kökenli esnek eşleşme (kaynakça biçimi için)
    esnek = sum(
        1 for a in set1 if any(_soyadi_kokenli_eslesme(a, b) for b in set2)
    )
    jaccard = max(kesisim, esnek / max(len(set1), len(set2)))
    # İlk yazar eşleşmesi bonus
    ilk_match = 1.0 if any(
        _soyadi_kokenli_eslesme(norm1[0], b) for b in norm2[:3]
    ) else 0.0
    return 0.7 * jaccard + 0.3 * ilk_match


def compare_years(year1: Any, year2: Any) -> float:
    """İki yıl karşılaştır (0.0 - 1.0)."""
    y1 = extract_year(year1)
    y2 = extract_year(year2)
    if y1 is None or y2 is None:
        return 0.5  # Bilinmeyen yıl - nötr
    if y1 == y2:
        return 1.0
    diff = abs(y1 - y2)
    if diff <= 1:
        return 0.8  # 1 yıl fark tolere edilebilir (early view vs print)
    if diff <= 2:
        return 0.5
    return 0.0


def compare_journals(journal1: str, journal2: str) -> float:
    """İki dergi adını karşılaştır (0.0 - 1.0)."""
    if not journal1 or not journal2:
        return 0.0
    j1 = normalize_journal(journal1)
    j2 = normalize_journal(journal2)
    if not j1 or not j2:
        return 0.0
    if j1 == j2:
        return 1.0
    # Fuzzy matching
    return fuzz.ratio(j1, j2) / 100.0


def _crossref_date_year(alan: Any) -> Optional[int]:
    """Crossref tarih alanından (``{"date-parts": [[1973]]}``) yılı çıkar.

    Alan eksik veya bozuksa ``None`` döner; zincirde bir sonraki alana
    geçilir. Böylece okuyucu "okunamadı" ile "okundu ve tutmadı" durumlarını
    ayırt edebilir.
    """
    if not isinstance(alan, dict):
        return None
    parcalar = alan.get("date-parts") or []
    if not parcalar or not parcalar[0]:
        return None
    yil = parcalar[0][0]
    return yil if isinstance(yil, int) and 1900 <= yil <= 2100 else None


def compute_bibliographic_match(
    source_record: dict,
    db_record: dict,
    weights: dict | None = None,
) -> BibliographicMatch:
    """Kaynak kaydı ile veritabanı kaydı arasında bibliyografik eşleşme hesapla.

    Args:
        source_record: source.json formatında kaynak kaydı
        db_record: Veritabanı (Crossref, OpenAlex, vb.) formatında kayıt
        weights: Alan ağırlıkları (varsayılan: title=0.35, author=0.30, year=0.15, journal=0.10, doi=0.10)

    Returns:
        BibliographicMatch: Detaylı eşleşme sonucu
    """
    default_weights = {
        "title": 0.35,
        "author": 0.30,
        "year": 0.15,
        "journal": 0.10,
        "doi": 0.10,
    }
    w = weights or default_weights

    # DOI eşleşmesi
    source_doi = normalize_doi(source_record.get("doi", "") or "")
    db_doi = normalize_doi(
        db_record.get("doi", "") or
        db_record.get("DOI", "") or
        db_record.get("doi", "") or ""
    )
    doi_match = bool(source_doi and db_doi and source_doi == db_doi)
    doi_score = 1.0 if doi_match else 0.0

    # Başlık
    source_title = source_record.get("title", "") or ""
    db_title = (
        db_record.get("title", "") or
        db_record.get("display_name", "") or
        db_record.get("title", "") or ""
    )
    title_score = compare_titles(source_title, db_title)

    # Yazarlar
    source_authors = source_record.get("authors", []) or []
    db_authors_raw = db_record.get("authors", []) or db_record.get("authorships", []) or []
    if isinstance(db_authors_raw[0], dict) if db_authors_raw else False:
        # OpenAlex formatı: authorships -> author.display_name
        db_authors = [a.get("author", {}).get("display_name", "") for a in db_authors_raw if a.get("author")]
    else:
        db_authors = [str(a) for a in db_authors_raw]
    author_score = compare_authors(source_authors, db_authors)

    # Yıl
    # DİKKAT: Python'da koşul ifadesi `or`dan düşük önceliklidir.
    # `a or b if cond else c` ifadesi `(a or b) if cond else c` olarak
    # ayrıştırılır. Bu yüzden her zincir ayrı parantezlenmiştir; aksi
    # hâlde "year" anahtarı taşıyan bir kayıtta bile yıl alanı düşer.
    source_year = source_record.get("year")
    db_year = (
        db_record.get("year")
        or db_record.get("publication_year")
        or _crossref_date_year(db_record.get("published-print"))
        or _crossref_date_year(db_record.get("published-online"))
        or _crossref_date_year(db_record.get("issued"))
    )
    year_score = compare_years(source_year, db_year)

    # Dergi — aynı öncelik sorunu burada da geçerliydi.
    source_journal = source_record.get("journal", "") or ""
    db_journal = (
        db_record.get("journal", "")
        or (
            db_record.get("container_title", [""])[0]
            if db_record.get("container_title") else ""
        )
        or (
            db_record.get("container-title", [""])[0]
            if db_record.get("container-title") else ""
        )
        or (
            db_record.get("host_venue", {}).get("display_name", "")
            if db_record.get("host_venue") else ""
        )
        or (
            db_record.get("primary_location", {}).get("source", {}).get("display_name", "")
            if db_record.get("primary_location") else ""
        )
    )
    journal_score = compare_journals(source_journal, db_journal)

    # Ağırlıklı toplam
    overall = (
        w.get("title", 0.35) * title_score +
        w.get("author", 0.30) * author_score +
        w.get("year", 0.15) * year_score +
        w.get("journal", 0.10) * journal_score +
        w.get("doi", 0.10) * doi_score
    )

    return BibliographicMatch(
        overall_score=round(overall, 3),
        title_score=round(title_score, 3),
        author_score=round(author_score, 3),
        year_score=round(year_score, 3),
        journal_score=round(journal_score, 3),
        doi_match=doi_match,
        details={
            "weights": w,
            "title": {"source": source_title[:80], "db": db_title[:80] if isinstance(db_title, str) else str(db_title)[:80]},
            "author": {"source_count": len(source_authors), "db_count": len(db_authors) if isinstance(db_authors, list) else 0},
            "year": {"source": source_year, "db": year2 if (year2 := extract_year(db_year)) else None},
            "journal": {"source": source_journal, "db": db_journal},
            "doi": {"source": source_doi, "db": db_doi},
        }
    )