---
description: Kaynakları Crossref + OpenAlex ile DOI/bibliyografik doğrular (en az 2 bağımsız kaynak, skor ≥ 0.60) ve sonucu source.verification alanına yazar
argument-hint: "[<SRC-ID> …] | --all"
---

Kaynak doğrulama. `python -m tools.atw.cli verify` alt komutunu `$ARGUMENTS`
ile çalıştır. Retraksiyon ve korizyon da denetlenir; geri çekilmiş kaynak
doğrulanmış işaretlenmez ve geri çekilmişliği bir daha silinmez.

Çalıştır: `python -m tools.atw.cli verify $ARGUMENTS`

Doğrulama sonuçlarını (skor, kaynak sayısı, retraksiyon uyarıları) özetle.