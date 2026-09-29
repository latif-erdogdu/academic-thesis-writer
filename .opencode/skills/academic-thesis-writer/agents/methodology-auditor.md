# Yöntem Denetçisi Ajanı

## Görev
Araştırma sorusu ile yöntem arasındaki uyumu denetle.

## Girdi

| Alan | Kaynak |
|------|--------|
| Araştırma soruları | `thesis_state.research_questions` — `type` (`main` / `sub`) ve `method` alanları |
| Yöntem tanımı | `thesis_state.methodology` |
| Veri kümeleri | `thesis_state.datasets` (`dataset.json` → `provenance`) |
| Analizler | `thesis_state.analyses` (`analysis.json` → `method`) |
| İstatistikler | `thesis_state.statistics` (`statistic.json` → `n`, `effect_size`) |
| Bulgular | `thesis_state.findings_registry` |

## Zincir Kontrolü
Araştırma Sorusu
  ↓
Araştırma Tasarımı
  ↓
Evren
  ↓
Örneklem
  ↓
Veri Toplama
  ↓
Değişkenler
  ↓
Analiz
  ↓
Bulgular
  ↓
Sonuç

## Örnek Hata
RQ2 → nitel
Yöntem → nicel
=> Otomatik hata üret

## Çıktı
Yöntem Denetim Raporu