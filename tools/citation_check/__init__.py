"""tools.citation_check — atif butunluk denetimi modulu.

Metin↔kaynakça bütünlüğünü denetler: kaynak varlığı, retraksiyon,
metinde atıflanmayan kaynak, iddia desteği, APA 7 biçim ve sayfa
numarası tutarlılığı. Çıktı, schemas/audit.json'a uyan bir denetim kaydıdır.
"""
from __future__ import annotations

from .checker import audit_citations
from .style import validate_apa7

__all__ = ["audit_citations", "validate_apa7"]
