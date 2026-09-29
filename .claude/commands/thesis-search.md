---
description: Araştırma sorusu için sistematik kaynak arama başlat
argument-hint: "<RQ-ID> [--databases crossref,openalex,pubmed]"
---

Sistematik kaynak araması başlat. `python -m tools.atw.cli search` alt komutunu
`$ARGUMENTS` ile çalıştır. Veritabanı listesi verilmezse varsayılanlarla (ör.
crossref, openalex, pubmed) çalışır.

Çalıştır: `python -m tools.atw.cli search $ARGUMENTS`

Arama özetini (bulunan kaynak sayısı, adaylar) kullanıcıya raporla.