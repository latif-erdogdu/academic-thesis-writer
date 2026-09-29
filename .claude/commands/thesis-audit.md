---
description: "Tam tez denetimi (5 aşama: yapısal, atıf, metodoloji, tutarlılık, yazım)"
argument-hint: "[--type citation|methodology|consistency|integrity|all]"
---

Tez denetimi. `python -m tools.atw.cli audit` alt komutunu `$ARGUMENTS` ile
çalıştır. `--type` verilmezse tüm aşamalar çalışır. Denetçi ajanların
(sözleşmede tanımlı) bulguları raporlanır; uydurma kaynak, kanıtsız iddia,
retraksiyon ve kopuk atıf denetimlerini içerir.

Çalıştır: `python -m tools.atw.cli audit $ARGUMENTS`

Denetim bulgularını (önem sırasıyla) kullanıcıya raporla.