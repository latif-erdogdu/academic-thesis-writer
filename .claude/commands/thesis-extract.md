---
description: Doğrulanmış PDF'lerden kanıt çıkar (claim-evidence linking)
argument-hint: "<SRC-ID> --claim <CLM-ID>"
---

Kanıt çıkarma. `python -m tools.atw.cli extract` alt komutunu `$ARGUMENTS` ile
çalıştır. Yalnızca DOĞRULANMIŞ kaynakların PDF'lerinden kanıt çıkarılır;
kanıt-iddia eşlemesi claim-evidence linking kuralına uyar.

Çalıştır: `python -m tools.atw.cli extract $ARGUMENTS`

Çıkarılan kanıtları (sayfa/bölüm, alıntı) kullanıcıya özetle.