---
description: Ajanın ürettiği JSON kaydını şema + kopuk referans denetiminden geçirip registry'ye yaz (araştırma sorusu, hipotez, iddia, atıf, boşluk, bulgu, ölçüm koleksiyonları)
argument-hint: <REGISTRY> --file <KAYIT.json>
---

Kayıt komutu. `python -m tools.atw.cli record` alt komutunu `$ARGUMENTS` ile
çalıştır. Kayıt ya hep yazılır ya hiç; id verilmezse otomatik atanır.

Not: `sources/`, `search_runs/`, `evidence_registry/`, `chapters/`,
`paragraphs/`, `audit_registry` bu komutla yazılamaz — onların sahibi ayrı
komutlardır.

Çalıştır: `python -m tools.atw.cli record $ARGUMENTS`

Komut çıktısını özetle.