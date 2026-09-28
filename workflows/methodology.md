# Metodoloji Çalışma Akışı

> **Bu akış bir komut dizisidir.** Ana zincir: `workflows/thesis_creation.md`
> Bu dosya 5. kapının (`methodology`) kayıtlarını ve 7. kapının arkasındaki
> bölüm yazımını kapsar.

## Kapının kendisi hazırlık denetiminden geçmez

`methodology` kapısı, `tools/atw/approval.py:GATE_HAZIRLIK` içinde **boş
denetim** taşır. Bu bir eksik değil, tasarım: bölümleri dolduran
`thesis:write` bu kapının arkasındadır; denetim `chapters`'a baksa ilk
bölüm hiç yazılamazdı (dairesel bağımlılık).

Bu yüzden metodoloji kayıtları **isteğe bağlı şema düzeyinde** durur ama
tez inandırıcılığı için zorunludur. `thesis:audit --type methodology` boş
metodolojiyi bulur.

## Kayıtlar

Dört registry, dört komut. Hepsi `thesis:record` ile yazılır:

```bash
thesis:record variables   --file <DEGISKENLER.json>
thesis:record datasets    --file <VERI_KUMELERI.json>
thesis:record analyses    --file <ANALIZLER.json>
thesis:record statistics  --file <ISTATISTIKLER.json>
thesis:approve methodology
```

Şemalar: `schemas/variable.json`, `schemas/dataset.json`,
`schemas/analysis.json`, `schemas/statistic.json`

`thesis:record` yalnızca şu registry'leri kabul eder:
`variables`, `datasets`, `analyses`, `statistics` (ve diğer ajan
registry'leri). `chapters`, `sources`, `search_runs`, `evidence_registry`,
`paragraphs`, `audit_registry` **CLI'nin sahibidir** — `thesis:record` bunları
reddeder, çünkü yazılabilirliklerinin kanıtı yoksa içerik uydurulabilirdi.

## Aşama 1 — Tasarım seçimi

Bu kararlar **CLI'ya yazılmaz**; `analyses` registry'sine gider.

| Yaklaşım | Ne zaman |
|---|---|
| Deneysel (kontrol grubu, randomizasyon) | Müdahale etkisi ölçülecekse |
| Anket | Geniş örneklemde betimsel/genelleştirilebilir |
| Nitel — fenomenoloji | Deneyimin derinlemesine anlamı |
| Nitel — etnografi | Kültürel bağlam |
| Nitel — durum çalışması | Tek olgu(ların) ayrıntılı incelenmesi |
| Karma — eşzamanlı paralel | Her iki veri toplanır, ayrı analiz edilir |
| Karma — açıklayıcı sıralı | Nicel bulguyu nitel açıklar |
| Karma — keşifsel sıralı | Nitel bulgu nicel genellemeye yön verir |

## Aşama 2 — Veri toplama planı

CLI'ya yazılan kısım `datasets` registry'sidir. Serbest metin kalanlar
`templates/thesis_structure.md` ile bölüm taslağına gider.

- Evren ve erişilebilirlik
- Örnekleme yöntemi (olasılıksal / olasılıksal değil — gerekçesiyle)
- Örneklem büyüklüğü: nicelde **güç analizi**, nitelde **doyma noktası**
- Veri toplama dönemi ve gerekçesi

## Aşama 3 — Ölçüm araçları

- Kavramsal operasyonelleştirme: her kavram nasıl ölçülüyor, neden bu ölçüm
- Güvenirlik (α) ve geçerlilik kanıtı (içerik / yapısal / kriter)
- Nitelte: görüşme rehberi, pilot test, kayıt izinleri

`references/methodology_rules.md` ayrıntılı kuralları verir.

## Aşama 4 — Analiz planı

`analyses` ve `statistics` registry'leri buraya yazılır.

1. Yazılım ve sürümü
2. Varsayım kontrolleri (normalite, homoskedastisite)
3. Çıkarımsal testler
4. Etki büyüklüğü — yalnızca p değeri değil
5. Duyarlılık analizleri

Nitelte: kodlama süreci, üye kontrolü, akran danışmanlığı, denetim izi.

## Aşama 5 — Etik

Etik kurul onayı, aydınlatılmış onay, veri gizliliği, çıkar çatışması.
Bu belgeler CLI'ya **yazılmaz**; `references/academic_integrity.md` ve tez
metnindeki metodoloji bölümüne gider.

## Aşama 6 — Geçerlilik ve güvenirlik

Nicel: iç geçerlilik, dış geçerlilik, ölçüm güvenirlik belgelenmesi.
Nitel: üçgenleme, üye kontrolü, kalıntı betimleme, refleksivite.

## Kapıdan sonra — bölüm yazımı

```bash
thesis:write CH-001 --rq RQ-001
```

`--file` verilmezse brifing basılır ve **tez durumu değişmez**. Brifing,
`variables`/`datasets`/`analyses`/`statistics` kayıtlarını ve yalnızca
doğrulanmış kaynakları içerir. Metni `agents/writer.md` ajanı yazar.
Ayrıntı: `workflows/chapter_writing.md`

## Kalite kontrol listesi

- [ ] Tasarım gerekçelendirilmiş ve araştırma sorusuna uygun
- [ ] Örnekleme yöntemi ve büyüklüğü gerekçeli
- [ ] Her değişken tanımlı ve ölçülebilir
- [ ] Analiz planı varsayımlarıyla birlikte yazılı
- [ ] Etki büyüklüğü hesaplanıyor
- [ ] Etik onay durumu belirtilmiş
- [ ] `thesis:audit --type methodology` temiz
- [ ] Atıf biçimi `references/citation_rules.md` ile uyumlu
