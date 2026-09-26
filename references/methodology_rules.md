# Yöntem Denetim Kuralları

## Temel Kural

**Tek bir denetim ölçeği tüm yöntemlere uygulanamaz.**

Nicel bir çalışmada p değeri denetlenir; nitel bir çalışmada p değeri
anlamsızdır. Nitel bir çalışmada tema doygunluğu denetlenir; nicel bir
çalışmada tema doygunluğu anlamsızdır. Tek şablon, doğru bulguyu
**yanlışlıkla reddetmeye** yol açar — ki bu, denetimi işlevsiz kılar.

Bu dosya üç ayrı denetim ölçeği tanımlar. `methodology-auditor.md`
önce yöntem türünü belirler, sonra yalnızca o ölçeği uygular.

---

## Ölçek A — Nicel Yöntemler

### Zincir

```
RQ → Hipotez → Degiskenler → Operasyonellestirme → Olcum araci
   → Olasilik ornekleme → Orneklem buyuklugu → Istatistiksel varsayim
   → Istatistiksel test → Etki buyuklugu → Guven araliği → Bulgu
```

### Denetim Ölçeği

| # | Denetim | Nerede okunur | Başarısızlık hali |
|---|---------|---------------|------------------|
| 1 | RQ test edilebilir mi? | `research_question.json` → `type`, `status` | `main` tipinde ama ölçülebilir değil |
| 2 | Hipotez RQ'ya bağlı mı? | `research_question.json` → `hypothesis_ids` | Hipotez var, RQ yok |
| 3 | Her değişken operasyonelleştirilmiş mi? | `thesis_state.variables` | "Başarı" değişkeni nasıl ölçüldüğü yok |
| 4 | Ölçüm aracı belirtilmiş mi? | `dataset.json` → `provenance.collection_instrument` | Anket adı/ölçek bilgisi yok |
| 5 | Güvenilirlik ve geçerlik raporlanmış mı? | `dataset.json` → `provenance` | Güvenilirlik katsayısı hiç verilmemiş |
| 6 | Olasılık örneklemesi mi? | `dataset.json` → `provenance.collection_instrument` | "Rastgele seçildi" gerekçesiz |
| 7 | Örneklem büyüklüğü hesaplanmış mı? | `analysis.json` → `parameters` | Gerekçesiz n |
| 8 | Varsayımlar denetlenmiş mi? | `analysis.json` → `method`, `parameters` | Normallik/homojenlik varsayımı hiç sorgulanmamış |
| 9 | Test parametrelere uygun mu? | `analysis.json` → `method` | İkili sonuç için t-testi |
| 10 | Etki büyüklüğü raporlanmış mı? | `statistic.json` → `effect_size` | Yalnızca p değeri var |
| 11 | Güven aralığı raporlanmış mı? | `statistic.json` → `ci_lower`, `ci_upper` | Nokta tahmin verilmiş, belirsizlik verilmemiş |
| 12 | n tutarlı mı? | `statistic.json` → `n` ile `dataset.json` → `row_count_cleaned` | Yöntem n=240, sonuç n=214, açıklama yok |

### 12 numaralı kural kritiktir

Örneklem sayısı kaynak veri kümesinden temizlenmiş satır sayısıyla
**eşleşmiyorsa**, her sayıyı kullanan istatistik değişmiş demektir.
Farkın gerekçesi `dataset.json` → `provenance.operations` içinde
bulunmalıdır ("19 eksik değer atıldı"). Gerekçe yoksa bulgu
**major** seviyedir.

---

## Ölçek B — Nitel Yöntemler

### Zincir

```
RQ → Arastirma tasarimi → Olasalik orneklemesi → Veri toplama
   → Kodlama → Tema gelistirme → Guvenilirlik → Yorumlama
```

### Denetim Ölçeği

| # | Denetim | Nerede okunur | Başarısızlık hali |
|---|---------|---------------|------------------|
| 1 | Tasarım RQ ile uyumlu mu? | `analysis.json` → `method` | Deneyim araştırmasına nicel tasarım |
| 2 | Katılımcı sayısı gerekçeli mi? | `dataset.json` → `provenance` | "5 kişi görüşüldü" gerekçesiz |
| 3 | Veri toplama yöntemi belirtilmiş mi? | `dataset.json` → `provenance.collection_instrument` | Görüşme mi gözlem mi belirsiz |
| 4 | Kodlama süreci açıklanmış mı? | `analysis.json` → `parameters` | "Kodlandı" denip geçilmiş |
| 5 | Tema geliştirme yöntemi belirtilmiş mi? | `analysis.json` → `method` | Temanın nasıl oluştuğu belirsiz |
| 6 | Kodlayıcılar arası tutarlılık var mı? | `analysis.json` → `parameters` | Tek kodlayıcı, kontrol yok |
| 7 | Güvenilirlik ölçütü belirtilmiş mi? | `dataset.json` → `provenance.operations` | Hiçbir güvenilirlik ölçütü yok |
| 8 | Karşı görüşler raporlanmış mı? | `discussion.json` → `alternative_explanations` | Yalnızca destekleyen alıntılar |
| 9 | Araştırmacı yanlılığı ele alınmış mı? | `discussion.json` → `limitations_acknowledged` | Kendi konumu hiç sorgulanmamış |
| 10 | Alıntılar kaynağına bağlı mı? | `evidence.json` → `text`, `location` | Alıntı var, sayfa yok |

### En az iki güvenilirlik ölçütü

Nitel çalışmada güvenilirlik **tek** ölçütle desteklenmez. En az iki
biri birlikte kullanılmalıdır: kayıt/denetim zinciri, kodlayıcılar
arası tutarlılık, ayrılmış kodlama, negatif durum analizi, üye
denetimi, kalın açıklama.

`dataset.json` → `provenance.operations` içinde hangi ölçütlerin
kullanıldığı yazılıdır.

---

## Ölçek C — Karma Yöntemler

Karma tasarımlarda **her iki ölçek de uygulanır** ve hangi aşamanın
hangi ölçeğe tabi olduğu açıkça yazılır.

| Aşama | Ölçek |
|-------|-------|
| Nicel veri toplama ve analiz | Ölçek A |
| Nitel veri toplama ve analiz | Ölçek B |
| Entegrasyon aşaması | Aşağıdaki kurallar |

### Entegrasyon Denetimi

| # | Denetim | Başarısızlık hali |
|---|---------|------------------|
| 1 | Entegrasyon noktası belirtilmiş mi? | Ortak veri havuzu mu, öncelikli mi belirsiz |
| 2 | Her iki kümenin çelişen bulguları ele alınmış mı? | Çelişki sessizce bırakılmış |
| 3 | Çelişki çözüm yöntemi var mı? | Çelişki "ikisi de doğru" diye bırakılmış |
| 4 | Aşamalar sırası raporlanmış mı? | Önce hangisinin yapıldığı belirsiz |

---

## Yöntem Seçimi Denetimi

`methodology-auditor.md` ilk adımda yöntem türünü belirler:

| Belirti | Seçim |
|---------|-------|
| `dataset.json` → `provenance.collection_instrument` bir ölçek/anket adı | **Ölçek A** |
| `collection_instrument` görüşme/gözlem kaydı | **Ölçek B** |
| Her iki tür de var | **Ölçek C** |
| `collection_instrument` boş | **Durdur** — yöntem türü belirlenemiyor |

Yöntem türü belirlenemiyorsa denetim yapılamaz. Bu durumda bulgu
`major` seviyedir ve `methodology` insan onayı verilene kadar akış durur.

---

## İnsan Onayı

`workflows/methodology.md` akışında `human_approvals.methodology`
kapısı bu kuralların tamamı uygulandıktan **sonra** açılır.
Ölçeklerden biri eksik uygulanmışsa kapı açılmaz.

## Bağlı Olduğu Şemalar

- `schemas/analysis.json` — yöntem, yazılım, parametreler
- `schemas/dataset.json` — örneklem, ölçüm aracı, güvenilirlik
- `schemas/statistic.json` — test, etki büyüklüğü, güven aralığı, n
- `schemas/research_question.json` — soru → yöntem bağı
- `schemas/finding.json` — bulgu → kanıt bağı
