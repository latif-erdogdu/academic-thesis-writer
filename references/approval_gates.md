# Onay Kapıları Sözleşmesi

Bu dosya `tools/atw/approval.py` içindeki kapı modelinin **kanonik
spesifikasyonudur**. Kod ile bu doküman çelişirse **kod yanlıştır** veya
doküman güncellenmelidir; `tests/contract_tests/test_kapi_sozlesmesi.py`
ikisini de denetler.

## 1. Neden bu sözleşme var

`state.APPROVAL_GATES` yedi kapının adını söylüyordu ama hiçbir yerde
zorlanmıyordu. `human_approvals` yalnızca `true/false` tutuyordu; "hangi
sürüm, hangi kanıtla, kim tarafından, ne zaman onaylandı" sorularının
yanıtı yoktu. Sonuç: onaylanan içerik sonradan değişse bile onay geçerli
görünüyordu.

Bu sözleşme dört şeyi ayırır:

| Kavram | Soru | Nerede tutulur |
|---|---|---|
| **Onay** | İnsan kararı verdi mi? | `human_approvals.<kapı>.approved` |
| **Hazırlık** | Kararı uygulayacak veri var mı? | `GATE_HAZIRLIK[kapı]` → kayıt düzeyinde şema doğrulaması |
| **Denetim** | Otomatik denetim geçti mi? | `audit_registry` |
| **Tazelik** | Onay verildikten sonra içerik değişti mi? | `content_hash` karşılaştırması |

**Denetim geçmesi onay değildir.** Denetim `thesis:audit` ile, onay
`thesis:approve` ile verilir; ikisi ayrı koşuldur. Denetim temiz geçse
bile kapı insan kararı olmadan açılmaz.

İki kural birbirinden ayrıdır ve karıştırılmamalıdır:

| Kural | Hangi kapılar | Kayıt yoksa |
|---|---|---|
| Denetim **zorunlu** | yalnız `final_thesis` (`ZORUNLU_DENETIM_KAPILARI`) | kapı açılmaz |
| Denetimde **`critical` bulgu** kapıyı kapatır | tüm kapılar | ara kapılarda denetim henüz çalışmamış olabilir; bu **geçerli** bir yoldur |

Ara kapılarda denetimi atlamak kasıtlıdır: `source_set` kapısı, kaynak
kümesi incelenirken henüz `evidence` denetimi çalışmamış olabilir. Denetim
kaydı zorunlu kılınsaydı akış kilitlenirdi. Buna karşılık `final_thesis`
teslim kapısıdır: "denetimi çalıştırmadan onay verdim" denemez.

## 2. Onay kaydı

`human_approvals.<kapı>` şunlardan **biridir**:

```jsonc
true                                     // eski biçim: onaylı, metadata yok
false                                    // eski biçim: onaysız
{ "approved": true,  "content_hash": "sha256:1a2b…" }   // yeni biçim
{ "approved": false, "rejection_reason": "…" }           // ret
```

Tam şema: [`schemas/approval.json`](../schemas/approval.json).

| Alan | Tip | Anlam |
|---|---|---|
| `approved` | bool | İnsan kararı olumlu mu |
| `approved_by` | string \| null | Kararı veren kişi (insan adı, ajan adı değil). `approved: true` iken **zorunludur**; `approved: false` iken `null` kalabilir — geri almada kimlik onayla birlikte silinir. |
| `approved_at` | RFC3339 \| null | Karar anı |
| `content_hash` | `sha256:` + 16 hex | Onay anında kapsanan içeriğin özeti |
| `comment` | string \| null | Serbest not (≤ 2000) |
| `rejection_reason` | string \| null | Ret gerekçesi (≤ 2000) |
| `audit_refs` | `AUD-XXX[]` | Kararın dayandığı denetimler |
| `revision` | int ≥ 1 | Aynı kapının N. onayı |

## 3. Bağımlılık grafiği

Bağımlılık **sıraya** değil, **açık listeye** bağlıdır. Akış sırası tesadüfi
olarak değişse de kapı açılma koşulu değişmez.

```
research_question ──▶ search_strategy ──▶ source_set ──▶ research_gap
                                                                    │
                                            methodology ◀────────────┘
                                                 │
                                            findings
                                                 │
                                          final_thesis
```

`GATE_BAGIMLILIK` sözlüğü bu grafiği taşır. Bir kapı yalnızca kendisine
**doğrudan** bağımlı kapıların *geçerli* (onaylı **ve** taze) onayına
dayanır; dolaylı bağımlılık zincirleme zaten çözülür.

## 4. Her kapının kontratı

`on_kosul` → **precondition**: onay verilebilmesi için verinin hazır olması.
`son_kosul` → **postcondition**: kapının açık olmasının garanti ettiği şey.

### 4.1 `research_question`
- **Bağımlı:** —
- **Denetim:** —
- **On koşul:** `research_questions` en az bir soru içerir; her soru `research_question` şemasına uygundur (`id`, `text`, `type`, `status` doludur) ve `text` alanı boş değildir.
- **Son koşul:** Araştırma soruları tanımlıdır ve hiçbiri `pending` değildir.

### 4.2 `search_strategy`
- **Bağımlı:** `research_question`
- **Denetim:** —
- **On koşul:** `search_runs` en az bir kayıt içerir; her kayıt `search_run` şemasına uygundur (PRISMA akışı aritmetiği şema tarafından zorunlu kılınır).
- **Son koşul:** Taramalar denetlenebilir biçimde kayıt altındadır.

### 4.3 `source_set`
- **Bağımlı:** `search_strategy`
- **Denetim:** —
- **On koşul:** `sources` en az bir kaynak içerir; her kaynak `source` şemasına uygundur ve `doi` ya da `url` alanlarından en az biri doludur.
- **Son koşul:** Kaynak kümesi tanımlıdır ve her kaynak geri çekilmiş (`retracted`) değildir.

### 4.4 `research_gap`
- **Bağımlı:** `source_set`
- **Denetim:** —
- **On koşul:** `gap_registry` en az bir boşluk içerir; her boşluk `research_gap` şemasına uygundur, `statement` alanı boş değildir ve `supporting_source_ids` en az bir **doğrulanmış** kaynağa çözülür.
- **Son koşul:** Literatürdeki boşluk kanıtlanmıştır; boşluk beyanı uydurma kaynakla desteklenemez.

### 4.5 `methodology`
- **Bağımlı:** `research_gap`
- **Denetim:** `methodology` — zorunlu değil; çalıştıysa `critical` bulgu kapatır
- **Hazırlık denetimi:** **yok** (bkz. §4.8, dairesellik kuralı)
- **On koşul:** Her `research_questions` kaydı `status` alanına sahiptir; `pending` soru varsa gerekçe (`unanswerable_reason`) zorunludur.
- **Son koşul:** Yöntem, her araştırma sorusunun yanıtlanıp yanıtlanamayacağını gerekçesiyle birlikte belirtir. Yanıtlanamayan soru sessizce atlanmaz.

Bu kapı iki alanı **bilinçli olarak** dışarıda bırakır. İkisi de
`thesis:write` kilitlenmesine yol açtı.

- `research_questions` kapsam dışıdır. Sorunun `status` alanı çalışma
  ilerledikçe `pending` → `answered` olur; bu bir yöntem değişikliği
  değil, işin doğal sonucudur. Kapsama alınsaydı `cmd_write` — ki bu
  kapıya bağımlıdır — kendi onayını bayatlatır ve yazım döngüsü
  kilitlenirdi. Kilit: `test_methodology_kapisi_bos_bolumle_yazilabilir`.
- `chapters` hazırlık denetimi dışıdır, çünkü `chapters`'i dolduran tek
  yol `cmd_write`'tır ve o da bu kapının arkasındadır. Denetim, kapının
  *arkasındaki* komutun ürettiği veriye bakarsa dairesel bağımlılık kurar
  ve o komut hiç çalışamaz. Kilit:
  `test_methodology_kapisi_bos_bolumle_yazilabilir`.

Bu yüzden `methodology` yedi kapının **tek** hazırlık denetimi olmayan
kapısıdır (`hazirlik_engelleri` boş liste döner). Buna karşılık kapsamı
geniştir: yöntem, hipotez, kavramsal çerçeve, veri seti, değişken,
analiz, istatistik ve `audit_registry` — yani yöntemin kararını etkileyen
her şey.

### 4.6 `findings`
- **Bağımlı:** `methodology`
- **Denetim:** `evidence`, `consistency` — zorunlu değil; çalıştıysa `critical` bulgu kapatır
- **On koşul:** `findings_registry` en az bir bulgu içerir; her bulgu `finding` şemasına uygundur ve `evidence_ids` listesi boş değildir.
- **Son koşul:** Her bulgu en az bir kanıt kaydına bağlıdır; kanıtsız bulgu onaylanabilir değildir.

`audit_registry` kapsama **dahildir**. Bu kapının dayandığı `evidence` ve
`consistency` denetimlerinin bulguları içerik özetine girer; onaydan sonra
`critical` bulgu üretildiğinde bu kapının onayı bayatlar. Bu, "denetim
onay değildir" ilkesinin onay tarafındaki karşılığıdır: denetimi geçmiş bir
şey, sonradan bozulan bir şeyle birlikte geçerli kalamaz.

### 4.7 `final_thesis`
- **Bağımlı:** `findings`
- **Denetim:** `citation`, `methodology`, `consistency`, `integrity`, `evidence` (tümü) — **zorunlu**: beşinden biri hiç çalıştırılmamışsa kapı açılmaz
- **On koşul:** `chapters` en az bir bölüm içerir; her bölümde metni olan en az bir paragraf vardır (`_bolumler_hazir`); bütünlük taraması boş döner (`_bulgulari_tara`: kopuk referans, kanıtsız iddia, geri çekilmiş kaynak yoktur).
- **Son koşul:** Tez aktarılabilir: hiçbir metinde gösterilen kaynak `sources` içinde yoktur, hiçbiri geri çekilmiş değildir, kaynakça yalnızca gerçekten atıf yapılan kaynakları içerir.

Bu, `ZORUNLU_DENETIM_KAPILARI` içindeki **tek** kapıdır. Metin varlığı
denetimi (`_bolumler_hazir`) buraya özgüdür: yalnız bölüm başlıklarından
oluşan bir "tez" onaylanabilirse kapı hiçbir şeyi doğrulamıyor demektir.

### 4.8 Hazırlık denetiminin ortak mekanizması

Bu bir kapı değildir; yedi kapının hepsinde geçerli olan hazırlık
denetiminin nasıl çalıştığını anlatır.

**Yalnız "dolu mu" bakmak zayıf bir denetimidir.** `[{}]` doludur ama hiçbir
şey taşımaz. `{"id": "RQ-001", "text": "..."}` doludur ama `type` alanı
yoktur. Böyle bir kayıtla kapı açılması, kapının hiçbir şeyi doğrulamadığı
anlamına gelir.

Bu yüzden `GATE_HAZIRLIK` her kaydı **kendi varlık şemasına karşı**
denetler:

| Registry | Denetim |
|---|---|
| `research_questions` | her kayıt `research_question.json` |
| `search_runs` | her kayıt `search_run.json` |
| `sources` | her kayıt `source.json` |
| `gap_registry` | her kayıt `research_gap.json` |
| `findings_registry` | her kayıt `finding.json` |
| `final_thesis` | `_bulgulari_tara` + `_bolumler_hazir` (kayıt şeması değil) |
| `methodology` | **yok** — bkz. §4.5 |

Dört kural:

1. **Şema, kaydın yazıldığı yolun aynı kuralıdır.** `thesis:record` bir
   kaydı yazmadan önce bu şemayı kullanır, `thesis:approve` de aynı şemayı
   kullanır. İki farklı kural olsaydı *yazılabilen ama onaylanamayan*
   kayıtlar oluşurdu.
2. **Varlık tipi `graph.registry_haritasi()`'ndan gelir**, kodda tekrar
   yazılmaz. `record.varlik_tipi` **kullanılmaz**: o fonksiyon yalnız
   `thesis:record` ile *yazılabilen* registry'lere cevap verir ve
   `search_runs` gibi sahiplenilmiş registry'lerde bilerek hata verir.
   Hazırlık denetimi yazma izni değil, var olan verinin *geçerliliğini*
   sorar.
3. **Tüm hatalar raporlanır, ilki değil.** `iter_errors` tüm hataları
   döndürür; `validate` yalnız ilkini. İlk hata gösterilseydi, tek
   komutla düzeltilemeyen bir kayıt için kullanıcı her seferinde yeni bir
   hata öğrenirdi.
4. **En çok 5 sorun gösterilir** (`_HAZIRLIK_RAPOR_SINIRI`). Kesme
   sebebi: kullanıcıya 300 satırlık şema hatası göstermek teşhis değil,
   gizlemedir. Kalan sayı açıkça yazılır.

Denetlenemeyen bir registry sessizce geçilmez — `"{alan} denetlenemiyor"`
açık bir engel olarak döner. Denetlenmemiş bir kapıyı denetlenmiş gibi
göstermek, denetlememiş olmaktan kötüdür.

## 5. Tazelik (immutable onay)

Onay anında kapsanan içeriğin SHA-256 özeti kısaltılmış hâlde saklanır.
İçerik sonradan değişirse:

```
kapi_acik_mi(...)  -> False      # onay bayatladı
onay_stale_mi(...) -> True
```

`cmd_write` ve `cmd_export` `kapi_acik_mi` üzerinden çalıştığı için bayat
onay bu komutları **otomatik olarak durdurur**; ayrı bir kontrol gerekmez.

Denetim de tazeliğe dahildir: onaydan sonra aynı `audit_type` için **yeni**
bir denetim farklı sonuç verirse onay bayatlar. Böylece "denetim geçti diye
onay" sonradan geçersizleşir.

## 6. Ret ve revizyon

`thesis:approve <kapı> --reject --reason "..." --by "<ad>"` kapıyı kapatır ve
`rejection_reason` yazar. Kapının önkoşulu sağlanana kadar tekrar açılamaz.
Her ret, kapının hangi alanlarının düzeltilmesi gerektiğini de taşır
(`gerekçe` serbest metindir; boş bırakılamaz).

**Ret de onay gibi bir karardır ve kararı vereni taşır.** Gerekçe "kimi
dinlemedik" sorusunu yanıtlar; anonim ret bu zinciri koparır. Bu yüzden
`--by` ret için de zorunludur: ret eden de bir insandır.

### 6.1 Geri alma neden kimlik istemez

`thesis:approve <kapı> --revoke` bir **kapatma** işlemidir: onayı geri
alır, bağımlı kapıları da düşürür ve kayda `approved_by: null` yazar
(kimlik onayla birlikte silinir).

Bu yüzden geri alma, onay ve retten **bilinçli olarak muaftır.** Gerekçe
yön bilgidir: geri alma güvenliği artırır — "daha az izin ver" yönünde
etki eder — dolayısıyla kimlik zorlaması burada yalnızca geri almayı
zorlaştırır, güvenlik kazandırmaz.

Muafiyetin etkileri:

- `onay_geri_al()` `onaylayan` parametresi **taşımaz.**
- `schemas/approval.json` `approved_by` tipini genel olarak
  `string | null` bırakır; yalnız `approved: true` dalı boşluğu reddeder.
  Aksi halde geri alma kaydı geçersiz olurdu.

Kuralın özeti: **kapıyı açan her karar kimlik taşır, kapıyı kapatan
kararlar kimlik taşımak zorunda değildir.**

## 7. Olay günlüğü

Durumda `approval_events` dizisi tutulur. Her onay, ret, geri alma ve
tazelik kaybı bir olay yazar:

```json
{"event_id":"EVT-0003","gate":"final_thesis","action":"approve",
 "actor":"Danışman Adı","at":"2026-09-30T09:14:22Z",
 "content_hash":"sha256:9f2c…","reason":null,"comment":"taslak incelendi",
 "audit_refs":["AUD-007"]}
```

`action` ∈ `approve` · `reject` · `revoke` · `stale` · `block`.
Olaylar **eklenir**, silinmez veya güncellenmez; `human_approvals` anlık
durumu tutar, `approval_events` geçmişi.

## 8. Eşzamanlılık

`thesis_state.json` tek yazıcı dosyasıdır. `save_state` geçici dosya +
atomik `os.replace` ile yazar (yarım dosya bırakmaz). Aynı anda iki süreç
yazarsa son yazan kazanır ve `approval_events` içinde aynı `event_id` veya
kaybolan olay görülür. Bu **kabul edilmiş** bir sınırdır: kapı modeli
eşzamanlı yazmayı değil, tek yazıcı disiplini varsayar. Üretimde aynı tez
üzerinde eşzamanlı iki ajan çalıştırılmamalıdır.

## 9. Sınırlamalar

- `approved_by` **insan** adıdır. Ajan kendi onayını yazamaz; `approve`
  komutu insan tarafından çalıştırılır. Araç, `approved_by` alanına
  güvenerek yetki kararı vermez.
- `revision` artar ama geçmiş kayıt silinmez.
- Bu sürümde `appendices` (ekler) alanı yoktur; `final_thesis` kapısı
  ekleri kapsamaz ve dışa aktarım çıktısında bu durum açıkça yazılır.
