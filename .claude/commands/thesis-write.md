---
description: Bölüm yazımı — doğrulanmış girdi brifingi üretir; ajanın yazdığı bölüm dosyasını denetleyip kaydeder
argument-hint: "<CHAPTER-ID> --rq <RQ-ID> [--file <BÖLÜM.json>]"
---

Bölüm yazımı. `python -m tools.atw.cli write` alt komutunu `$ARGUMENTS` ile
çalıştır. `--file` verilmezse brifing basılır ve tez durumu değişmez — metni
yazan ajan (writer) üretir; CLI Türkçe metin yazmaz. Kayıt öncesi
Evidence Gate → Writing Gate denetimleri işler.

Çalıştır: `python -m tools.atw.cli write $ARGUMENTS`

Brifingi veya kayıt sonucunu kullanıcıya özetle.