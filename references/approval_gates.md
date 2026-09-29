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
| **Hazırlık** | Kararı uygulayacak veri var mı? | `GATE_KOSULLARI[kapı].on_kosul` |
| **Denetim** | Otomatik denetim geçti mi? | `audit_registry` |
| **Tazelik** | Onay verildikten sonra içerik değişti mi? | `content_hash` karşılaştırması |

**Denetim geçmesi onay değildir.** `thesis:audit` `critical` bulgu
bulmadığında kapı açılmaz; kapı ancak insan `thesis:approve` çalıştırdığında
ve içerik o günkü hâliyle eşleştiğinde açılır. İkisi ayrı koşuldur ve
ikisi de sağlanmalıdır.

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
| `approved_by` | string \| null | Kararı veren kişi (zorunlu; ajan adı değil) |
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
- **Denetim:** `methodology`
- **On koşul:** Tüm `research_questions` için `status` alanı `answered` veya `partially_answered`; `pending` soru varsa gerekçe (`unanswerable_reason`) zorunludur.
- **Son koşul:** Yöntem, her araştırma sorusunun yanıtlanıp yanıtlanamayacağını gerekçesiyle birlikte belirtir. Yanıtlanamayan soru sessizce atlanmaz.

### 4.6 `findings`
- **Bağımlı:** `methodology`
- **Denetim:** `evidence`, `consistency`
- **On koşul:** `findings_registry` en az bir bulgu içerir; her bulgunun `evidence_ids` listesi boş değildir.
- **Son koşul:** Her bulgu en az bir kanıt kaydına bağlıdır; kanıtsız bulgu onaylanabilir değildir.

### 4.7 `final_thesis`
- **Bağımlı:** `findings`
- **Denetim:** `citation`, `methodology`, `consistency`, `integrity`, `evidence` (tümü)
- **On koşul:** `chapters` en az bir bölüm içerir; her bölümde metni olan en az bir paragraf vardır; bütünlük taraması boş döner (kopuk referans, kanıtsız iddia, retraksiyon yok).
- **Son koşul:** Tez aktarılabilir: hiçbir metinde gösterilen kaynak `sources` içinde yoktur, hiçbiri geri çekilmiş değildir, kaynakça yalnızca gerçekten atıf yapılan kaynakları içerir.

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

`thesis:approve <kapı> --reject --reason "..."` kapıyı kapatır ve
`rejection_reason` yazar. Kapının önkoşulu sağlanana kadar tekrar açılamaz.
Her ret, kapının hangi alanlarının düzeltilmesi gerektiğini de taşır
(`gerekçe` serbest metindir; boş bırakılamaz).

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
