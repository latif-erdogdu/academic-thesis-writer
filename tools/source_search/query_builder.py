"""Sorgu oluşturucu: RQ → Boolean query (PICO/PECO framework)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# MeSH terimleri ve eş anlamlılar için basit bir ontology
MESH_SYNONYMS = {
    "depression": ["depressive disorder", "major depression", "melancholia"],
    "anxiety": ["anxiety disorders", "generalized anxiety disorder", "panic disorder"],
    "cognitive behavioral therapy": ["CBT", "cognitive therapy", "behavior therapy"],
    "mindfulness": ["mindfulness-based therapy", "MBSR", "MBCT", "meditation"],
    "exercise": ["physical activity", "training", "workout", "aerobic exercise"],
    "online": ["internet-based", "web-based", "digital", "e-health", "telehealth"],
    "adolescent": ["teenager", "youth", "young adult", "juvenile"],
    "elderly": ["older adult", "aged", "geriatric", "senior"],
    "randomized controlled trial": ["RCT", "randomized trial", "controlled clinical trial"],
    "systematic review": ["meta-analysis", "systematic literature review"],
    "crossref": ["Crossref", "CrossRef"],
    "openalex": ["OpenAlex"],
    "semantic scholar": ["Semantic Scholar"],
    "pubmed": ["PubMed", "MEDLINE"],
}

# Boolean operatörleri
BOOLEAN_OPS = ["AND", "OR", "NOT"]


@dataclass
class PICO:
    """PICO/PECO çerçevesi bileşenleri."""
    population: str = ""          # P: Population / Problem
    intervention: str = ""        # I: Intervention / Exposure
    comparison: str = ""          # C: Comparison / Control
    outcome: str = ""             # O: Outcome
    context: str = ""             # C: Context / Setting (PECO için)
    study_design: str = ""        # S: Study Design (PICOS için)

    def to_dict(self) -> dict:
        return {
            "population": self.population,
            "intervention": self.intervention,
            "comparison": self.comparison,
            "outcome": self.outcome,
            "context": self.context,
            "study_design": self.study_design,
        }

    def non_empty(self) -> dict:
        return {k: v for k, v in self.to_dict().items() if v}


@dataclass
class SearchQuery:
    """Oluşturulan arama sorgusu."""
    boolean_string: str
    pico: PICO
    databases: list[str]
    filters: dict = field(default_factory=dict)
    synonyms_used: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return self.boolean_string


def parse_pico(text: str) -> PICO:
    """Serbest metinden PICO bileşenlerini çıkar (basit heuristik)."""
    pico = PICO()

    # Basit anahtar kelime eşleştirme
    patterns = {
        "population": [
            r"(?:patients?|participants?|subjects?|individuals?|people|adults?|adolescents?|children|elderly|older adults?)",
        ],
        "intervention": [
            r"(?:treatment|therapy|intervention|program|training|exercise|meditation|mindfulness|cbt|cognitive behavioral therapy|drug|medication|therapy)",
        ],
        "comparison": [
            r"(?:versus|vs\.?|compared to|control|placebo|waitlist|treatment as usual|usual care|no treatment)",
        ],
        "outcome": [
            r"(?:outcome|effect|efficacy|effectiveness|improvement|reduction|change|score|symptoms?|quality of life|well-being)",
        ],
        "context": [
            r"(?:setting|clinic|hospital|community|online|internet|primary care|primary health care)",
        ],
        "study_design": [
            r"(?:randomized|RCT|controlled trial|systematic review|meta-analysis|cohort|case-control|cross-sectional)",
        ],
    }

    text_lower = text.lower()
    for component, patterns_list in patterns.items():
        matches = []
        for pattern in patterns_list:
            for match in re.finditer(pattern, text_lower):
                # Eşleşen ifadenin çevresindeki kelimeleri al
                start, end = match.span()
                context_start = max(0, start - 30)
                context_end = min(len(text_lower), end + 30)
                snippet = text_lower[context_start:context_end].strip()
                matches.append(snippet)

        if matches:
            # En uzun snippet'i al
            best = max(matches, key=len)
            setattr(pico, component, best)

    return pico


def expand_synonyms(term: str, max_synonyms: int = 3) -> list[str]:
    """Terim için eş anlamlıları genişlet (MeSH/ontology tabanlı)."""
    term_lower = term.lower()
    synonyms = [term]

    # Doğrudan eşleşme
    for key, syns in MESH_SYNONYMS.items():
        if key in term_lower:
            synonyms.extend(syns[:max_synonyms])
            break

    # Kısmi eşleşme
    if len(synonyms) == 1:
        for key, syns in MESH_SYNONYMS.items():
            if key in term_lower or term_lower in key:
                synonyms.extend(syns[:max_synonyms])
                break

    # Benzersiz ve sınırla
    seen = set()
    unique = []
    for s in synonyms:
        if s.lower() not in seen:
            seen.add(s.lower())
            unique.append(s)
    return unique[:max_synonyms + 1]


def build_boolean_query(
    pico: PICO | str,
    use_synonyms: bool = True,
    field_mapping: dict | None = None,
    database: str = "crossref",
) -> SearchQuery:
    """PICO'dan Boolean query string oluştur.

    Args:
        pico: PICO nesnesi veya serbest metin
        use_synonyms: Eş anlamlı genişletme kullanılsın mı
        field_mapping: Veritabanı alan eşleşmesi (örn: {"title": "title", "author": "author"})
        database: Hedef veritabanı (crossref, openalex, pubmed, semantic_scholar)
    """
    if isinstance(pico, str):
        pico = parse_pico(pico)

    # Veritabanı özel alan mapping'i
    default_fields = {
        "crossref": ["title", "abstract", "author"],
        "openalex": ["title", "abstract", "authorships.author.display_name"],
        "pubmed": ["title", "abstract", "author"],
        "semantic_scholar": ["title", "abstract", "authors.name"],
        "semantic_scholar": ["title", "abstract", "authors"],
    }
    fields = field_mapping or default_fields.get(database, ["title", "abstract"])

    # Her PICO bileşeni için terimler topla
    pico_dict = pico.non_empty()
    all_terms = {}
    all_synonyms = []

    for component, text in pico_dict.items():
        # Basit tokenizasyon
        tokens = re.findall(r'\b\w+\b', text.lower())
        # Stopwords çıkar
        stopwords = {"the", "and", "or", "of", "in", "for", "to", "with", "a", "an", "is", "on", "by", "as", "at"}
        tokens = [t for t in tokens if t not in stopwords and len(t) > 2]

        # Bileşen bazlı gruplama
        component_terms = []
        for token in tokens:
            if use_synonyms:
                syns = expand_synonyms(token)
                all_synonyms.extend(syns[1:])  # Orijinal hariç
                component_terms.extend(syns)
            else:
                component_terms.append(token)

        if component_terms:
            all_terms[component] = component_terms

    # Boolean query string oluştur
    # Her bileşen OR ile birleşir, bileşenler AND ile
    query_parts = []
    for component, terms in all_terms.items():
        if not terms:
            continue
        # Her terimi alanlara uygula
        field_queries = []
        for term in terms:
            field_qs = [f"{field}:{term}" for field in fields]
            field_queries.append(f"({' OR '.join(field_qs)})")
        if field_queries:
            query_parts.append(f"({' OR '.join(field_queries)})")

    boolean_string = " AND ".join(query_parts) if query_parts else ""

    # Veritabanı özel filtreler
    filters = {}
    if database == "pubmed":
        filters["datetype"] = "pdat"
    elif database == "crossref":
        filters["sort"] = "relevance"
    elif database == "openalex":
        filters["sort"] = "relevance_score:desc"

    return SearchQuery(
        boolean_string=boolean_string,
        pico=pico,
        databases=[database],
        filters=filters,
        synonyms_used=list(set(all_synonyms)),
    )


def build_multi_database_queries(
    pico: PICO | str,
    databases: list[str] = ["crossref", "openalex", "pubmed", "semantic_scholar"],
    **kwargs
) -> dict[str, SearchQuery]:
    """Birden fazla veritabanı için sorgu oluştur."""
    queries = {}
    for db in databases:
        queries[db] = build_boolean_query(pico, database=db, **kwargs)
    return queries


# Crossref/OpenAlex/Semantic Scholar için özel sorgu oluşturucular
def build_crossref_query(pico: PICO, **kwargs) -> SearchQuery:
    return build_boolean_query(pico, database="crossref", **kwargs)


def build_openalex_query(pico: PICO, **kwargs) -> SearchQuery:
    return build_boolean_query(pico, database="openalex", **kwargs)


def build_pubmed_query(pico: PICO, **kwargs) -> SearchQuery:
    # PubMed için MeSH terimleri ve [MeSH Terms] etiketi
    query = build_boolean_query(pico, database="pubmed", **kwargs)
    # PubMed özel: [MeSH Terms], [Title/Abstract] etiketleri
    return query


def build_semantic_scholar_query(pico: PICO, **kwargs) -> SearchQuery:
    return build_boolean_query(pico, database="semantic_scholar", **kwargs)