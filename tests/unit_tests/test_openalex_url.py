"""OpenAlex fallback URL slash kusuru.

Kok neden: openalex.py L188'de f"https://openalex.org{self.id.split('/')[-1]}"
slash eksik; self.id zaten 'https://openalex.org/W...' formatinda oldugu icin
sonuc 'https://openalex.orgW...' olur (slash yok). Bu URL calismaz.
"""
import sys

sys.path.insert(0, r"D:\academic-thesis-writer")
from tools.source_search.openalex import OpenAlexWork


def _ornek_work() -> OpenAlexWork:
    return OpenAlexWork(
        id="https://openalex.org/W1952419700",
        doi="10.1000/ornek",
        title="Ornek Calisma",
        authors=[{"id": "", "orcid": "", "display_name": "Yazar, A.",
                  "institutions": [], "raw_affiliation_string": ""}],
        year=2021,
        journal="Ornek Dergi",
        venue=None, volume=None, issue=None, pages=None,
        cited_by_count=0, is_open_access=False, open_access_url=None,
        abstract=None, keywords=[], concepts=[], institutions=[],
        countries=[], type="article", type_crossref=None, indexed_in=[],
        created_date="2021-01-01", updated_date="2021-01-01",
        referenced_works=[], related_works=[], grants=[], datasets=[],
        versions=[],
    )


def test_openalex_fallback_url_slash_icerir():
    """OpenAlex fallback URL'si slash icermeli.

    Regresyon: f"https://openalex.org{self.id.split('/')[-1]}" slash eksik;
    'https://openalex.orgW...' uretiyor ve calismiyor.
    """
    work = _ornek_work()
    kayit = work.to_source_dict()
    url = kayit.get("url")
    assert url is not None
    assert "openalex.org/W" in url, f"URL slash icermiyor: {url}"
    assert "openalex.orgW" not in url, f"URL slash eksik: {url}"