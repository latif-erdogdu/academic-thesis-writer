---
description: PRISMA onay kapısı aç/kapat — hazırlığı olmayan kapı açılmaz; bu olmadan yazım ve ihracat ilerlemez
argument-hint: "<KAPI> [--revoke] | --list"
---

PRISMA onay kapısı. `python -m tools.atw.cli approve` alt komutunu
`$ARGUMENTS` ile çalıştır. Kapıyı açan başka komut yoktur; hazırlığı
olmayan kapı açılmaz. `--revoke` ile kapı kapatılır, `--list` ile kapı
durumları gösterilir.

Çalıştır: `python -m tools.atw.cli approve $ARGUMENTS`

Kapı durumunu kullanıcıya raporla.