"""Kaynak deduplication: DOI, başlık+yazar+yıl benzerliği ile tekrarları kaldır."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from rapidfuzz import fuzz, process

# DOI regex
DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)

# Yıl regex
YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")


@dataclass
class DedupResult:
    """Deduplication sonucu."""
    unique: list[dict]           # Benzersiz kayıtlar
    duplicates: list[tuple]      # (orijinal_idx, kopya_idx, benzerlik, neden)
    stats: dict                  # İstatistikler


def normalize_doi(doi: str) -> str:
    """DOI'yi normalize et (küçük harf, prefix/suffix temizle)."""
    if not doi:
        return ""
    # "https://doi.org/10.xxx" -> "10.xxx"
    doi = doi.lower().strip()
    for prefix in ["https://doi.org/", "http://doi.org/", "doi:", "doi "]:
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
            break
    return doi.strip()


def normalize_title(title: str) -> str:
    """Başlığı normalize et (küçük harf, noktalama temizle)."""
    if not title:
        return ""
    # Küçük harf
    title = title.lower()
    # Noktalama ve özel karakterleri temizle
    title = re.sub(r"[^\w\s]", " ", title)
    # Çoklu boşlukları tek yap
    title = re.sub(r"\s+", " ", title)
    return title.strip()


def normalize_author(author: str) -> str:
    """Yazar adını normalize et (soyad, başharf)."""
    if not author:
        return ""
    author = author.lower().strip()
    # "Smith, John" -> "smith j"
    # "John Smith" -> "smith j"
    parts = [p.strip() for p in re.split(r"[,\s]+", author) if p.strip()]
    if not parts:
        return ""
    if "," in author:
        # "Soyad, Ad" formatı
        surname = parts[0].replace(",", "")
        given = parts[1] if len(parts) > 1 else ""
    else:
        # "Ad Soyad" formatı
        surname = parts[-1]
        given = parts[0] if len(parts) > 1 else ""
    initial = given[0] if given else ""
    return f"{surname} {initial}".strip()


def extract_year(text: str) -> int | None:
    """Metinden yıl çıkar."""
    if not text:
        return None
    match = YEAR_PATTERN.search(str(text))
    if match:
        year = int(match.group())
        if 1900 <= year <= 2100:
            return year
    return None


def compute_signature(record: dict) -> tuple:
    """Kayıt için imza oluştur (DOI, normalized_title+author+year)."""
    # DOI varsa DOI imzası
    doi = normalize_doi(record.get("doi", "") or record.get("DOI", ""))
    if doi:
        return ("doi", doi)

    # DOI yoksa: başlık + yazar + yıl
    title = normalize_title(record.get("title", "") or record.get("Title", ""))
    authors = record.get("authors", []) or record.get("Authors", [])
    author_sigs = [normalize_author(a) for a in authors] if isinstance(authors, list) else [normalize_author(str(authors))]
    author_sig = "|".join(sorted(author_sigs[:3]))  # İlk 3 yazar
    year = extract_year(record.get("year") or record.get("Year") or record.get("publication_year"))

    return ("title_author_year", title, author_sig, year)


def are_duplicates(record1: dict, record2: dict, threshold: float = 0.9) -> tuple[bool, float, str]:
    """İki kaydın kopyası olup olmadığını kontrol et.

    Returns: (is_duplicate, similarity_score, reason)
    """
    # 1. DOI kontrolü (en güçlü)
    doi1 = normalize_doi(record1.get("doi", "") or record1.get("DOI", ""))
    doi2 = normalize_doi(record2.get("doi", "") or record2.get("DOI", ""))
    if doi1 and doi2:
        if doi1 == doi2:
            return True, 1.0, "DOI match"

    # 2. Başlık + Yazar + Yıl benzerliği
    title1 = normalize_title(record1.get("title", "") or record1.get("Title", ""))
    title2 = normalize_title(record2.get("title", "") or record2.get("Title", ""))

    if title1 and title2:
        title_sim = fuzz.ratio(title1, title2) / 100.0
        if title_sim >= threshold:
            # Yazar kontrolü
            authors1 = [normalize_author(a) for a in (record1.get("authors", []) or record1.get("Authors", []) or [])]
            authors2 = [normalize_author(a) for a in (record2.get("authors", []) or record2.get("Authors", []) or [])]

            author_sim = 0.0
            if authors1 and authors2:
                # En az bir yazar eşleşiyor mu
                set1 = set(authors1[:3])
                set2 = set(authors2[:3])
                if set1 & set2:
                    author_sim = 1.0
                else:
                    # Fuzzy yazar karşılaştırması
                    author_sim = max(
                        fuzz.ratio(a1, a2) / 100.0
                        for a1 in authors1[:3]
                        for a2 in authors2[:3]
                    ) if authors1 and authors2 else 0.0

            # Yıl kontrolü
            year1 = extract_year(record1.get("year") or record1.get("Year") or record1.get("publication_year"))
            year2 = extract_year(record2.get("year") or record2.get("Year") or record2.get("publication_year"))
            year_match = 1.0 if year1 and year2 and year1 == year2 else (0.5 if year1 or year2 else 0.0)

            # Ağırlıklı skor
            composite = (title_sim * 0.5) + (author_sim * 0.3) + (year_match * 0.2)
            if composite >= threshold:
                reason = f"title:{title_sim:.2f} author:{author_sim:.2f} year:{year_match:.2f}"
                return True, composite, reason

    # 3. Sadece başlık çok benzerse (yazar/yıl yoksa)
    if title1 and title2:
        title_sim = fuzz.ratio(title1, title2) / 100.0
        if title_sim >= 0.95:  # Çok yüksek eşik
            return True, title_sim, f"title only: {title_sim:.2f}"

    return False, 0.0, "no match"


def deduplicate_sources(
    sources: list[dict],
    threshold: float = 0.9,
    keep_first: bool = True,
) -> DedupResult:
    """Kaynak listesinden tekrarları kaldır.

    Args:
        sources: Kaynak kayıt listesi (dict)
        threshold: Benzerlik eşiği (0-1)
        keep_first: True ise ilk görülen korunur, False ise en kapsamlı (alan sayısı) korunur

    Returns:
        DedupResult: unique, duplicates, stats
    """
    if not sources:
        return DedupResult(
            unique=[],
            duplicates=[],
            stats={"input": 0, "unique": 0, "removed": 0, "by_doi": 0, "by_title_author_year": 0, "by_title_only": 0},
        )

    unique = []
    duplicates = []
    seen_signatures = {}  # signature -> index in unique

    stats = {
        "input": len(sources),
        "unique": 0,
        "removed": 0,
        "by_doi": 0,
        "by_title_author_year": 0,
        "by_title_only": 0,
    }

    for idx, record in enumerate(sources):
        # İmza kontrolü
        sig = compute_signature(record)

        is_dup = False
        dup_reason = ""

        if sig in seen_signatures:
            # Aynı imza zaten var
            orig_idx = seen_signatures[sig]
            orig_record = unique[orig_idx]
            is_dup, sim, reason = are_duplicates(orig_record, record, threshold=0.95)
            if is_dup:
                dup_reason = f"signature:{sig[0]} sim:{sim:.3f} {reason}"
            else:
                # İmza çakışması ama gerçekten farklı (nadir)
                pass

        if not is_dup:
            # Fuzzy karşılaştırma mevcut unique'larla
            for u_idx, u_record in enumerate(unique):
                is_dup, sim, reason = are_duplicates(u_record, record, threshold=threshold)
                if is_dup:
                    dup_reason = f"fuzzy:{reason} sim:{sim:.3f}"
                    break

        if is_dup:
            stats["removed"] += 1
            if "doi" in dup_reason:
                stats["by_doi"] += 1
            elif "title_author_year" in dup_reason:
                stats["by_title_author_year"] += 1
            elif "title only" in dup_reason:
                stats["by_title_only"] += 1

            duplicates.append((seen_signatures.get(sig, -1), idx, 0.0, dup_reason))
        else:
            # Yeni benzersiz kayıt
            unique.append(record)
            seen_signatures[sig] = len(unique) - 1

    stats["unique"] = len(unique)
    return DedupResult(unique=unique, duplicates=duplicates, stats=stats)


def deduplicate_by_doi_only(sources: list[dict]) -> DedupResult:
    """Sadece DOI bazlı deduplication (hızlı, kesin)."""
    seen_dois = {}
    unique = []
    duplicates = []

    for idx, record in enumerate(sources):
        doi = normalize_doi(record.get("doi", "") or record.get("DOI", ""))
        if doi and doi in seen_dois:
            duplicates.append((seen_dois[doi], idx, 1.0, "DOI match"))
        else:
            if doi:
                seen_dois[doi] = len(unique)
            unique.append(record)

    return DedupResult(
        unique=unique,
        duplicates=duplicates,
        stats={
            "input": len(sources),
            "unique": len(unique),
            "removed": len(duplicates),
            "by_doi": len(duplicates),
            "by_title_author_year": 0,
            "by_title_only": 0,
        }
    )


def merge_duplicate_records(records: list[dict]) -> dict:
    """Aynı kaydın farklı veritabanından gelen versiyonlarını birleştir.

    En kapsamlı alanı alır (None olmayan en uzun değer).
    """
    if not records:
        return {}

    if len(records) == 1:
        return records[0].copy()

    merged = {}
    all_keys = set()
    for r in records:
        all_keys.update(r.keys())

    for key in all_keys:
        values = [r.get(key) for r in records if r.get(key) is not None]
        if not values:
            merged[key] = None
            continue

        # En uzun/karakter sayısı en fazla olanı al
        best = max(values, key=lambda v: len(str(v)) if v else 0)
        merged[key] = best

    return merged


def find_potential_duplicates(
    sources: list[dict],
    threshold: float = 0.85,
    max_pairs: int = 100,
) -> list[tuple[int, int, float, str]]:
    """Olası kopyaları bul (manuel inceleme için).

    Returns: [(idx1, idx2, similarity, reason), ...]
    """
    pairs = []
    n = len(sources)

    for i in range(n):
        for j in range(i + 1, n):
            if len(pairs) >= max_pairs:
                break
            is_dup, sim, reason = are_duplicates(sources[i], sources[j], threshold)
            if is_dup:
                pairs.append((i, j, sim, reason))
        if len(pairs) >= max_pairs:
            break

    # Benzerlik skoruna göre sırala (yüksekten düşüğe)
    pairs.sort(key=lambda x: x[2], reverse=True)
    return pairs