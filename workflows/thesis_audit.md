# Tez Denetim Çalışma Akışı

> **Bu akış bir komut dizisidir.** Ana zincir: `workflows/thesis_creation.md`
> Bu dosya 7. kapının (`final_thesis`) denetim kısmını kapsar.

## Komut

```bash
thesis:audit --type all
```

Kayıtlar `audit_registry`'ye yazılır. **En az bir `critical` bulgu varsa
komut 1 döner** — böylece denetim doğrudan CI kapısı olabilir.

## Gerçekte uygulanan dört denetim

| `--type` | Uygulanıyor mu? | Ne yapar |
|---|---|---|
| `citation` | evet | Eksik/fazla atıf, kaynakça eşleşmesi |
| `methodology` | evet | Tasarım, analiz, geçerlilik tutarlılığı |
| `integrity` | evet | Bütünlük denetimleri (aşağıdaki 5 sayaç) |
| `evidence` | evet | Kanıt zinciri: bulgu → kanıt → kaynak |
| `consistency` | **hayır** | ⚠️ `agents/consistency-auditor.md` ajanının işidir |

`--type consistency` verildiğinde CLI **uyarı basar ve atlar**; sahte bir
denetim kaydı yazmaz. Denetimi olmayan alanı denetlenmiş göstermek, hiç
denetlenmemekten kötüdür.

Bu, beş denetim türünden dördüdür. `--type all` dördünü çalıştırır.

## Bütünlük denetimi — beş sayaç

`integrity` (ve `final_thesis` kapısı) `integrity_checks` alanında beş
sayac döner:

| Sayaç | Anlamı |
|---|---|
| `fabricated_sources` | Doğrulanamayan kaynakla desteklenen iddia |
| `unsupported_claims` | Kanıtı olmayan iddia |
| `retracted_sources_in_use` | Geri çekilmiş kaynağa dayanan iddia |
| `orphaned_citations` | Var olmayan kimliğe işaret eden atıf |
| `unverifiable_claims` | Doğrulama durumu `unverified`/`pending` kalan iddia |

`"unverified"` bir sonuç değil, henüz çalışma durumudur
(`tools/atw/audit.py:_TERMINAL_DOGRULAMA`).

## Elle yapılan denetimler

`thesis:audit` **üslubu, terminolojiyi ve edebi bütünlüğü denetlemez.**
Aşağıdakiler ajana kalır:

### Terminoloji
- [ ] Aynı kavram tez boyunca tek adla mı kullanılıyor?
- [ ] Terim tanımı ilk kullanıldığı yerde verilmiş mi?

### Sayı tutarlılığı
- [ ] Aynı veri farklı bölümlerde aynı rakamı veriyor mu?
- [ ] Yuvarlama, metinden hesaplanabilir mi?

### Örneklem tutarlılığı
- [ ] Örneklem büyüklüğü her yerde aynı mı?
- [ ] Dahil/hariç bırakılan birimler metot ile bulgular arasında tutarlı mı?

### Yöntem ↔ bulgular uyumu
- [ ] Bulguların dayandığı analiz gerçekten yapılmış mı?
- [ ] Yöntem bölümünde anlatılan ile yapılan aynı mı?

### Tutarlılık denetimi (ajan)

```bash
# CLI'da yok; ajanın görevi
```

- Aynı veri farklı bölümlerde farklı mı?
- Yöntem ile bulgular uyumlu mu?

`agents/consistency-auditor.md` bu işi yapar. Raporunu
`audit_registry`'ye yazması için ajan ayrıca `thesis:audit --type consistency`
çağırmaz — bu komut uyarı basıp atlar.

## Kritik sorun listesi

Denetim tamamlandıktan sonra önceliklendirilmiş tabloyu
`templates/quality_report.md` şablonuyla doldurun.

| Sorun | Önem | Bölüm | Düzeltildi mi? |
|---|---|---|---|
| … | critical / major / minor | CH-00X | ✓ / ✗ |

## Döngü

```bash
thesis:audit --type all
#   → 🔴 bulgu var mı? düzelt, sonra yine denetle
thesis:approve final_thesis
```

`final_thesis` en katı kapıdır: `approval.py` içinde bütünlük denetimi
burada da devreye girer, yani `thesis:audit`'i ayrıca çalıştırmadan
da kopuk referans, kanıtsız iddia ve retraksiyon denetimleri yapılır.

Kapı açıldıktan sonra:

```bash
thesis:export --format docx
```

## Ajanlar

Denetimlerin altı aşaması CLI dışındadır; her birinin ajanı vardır:
`agents/citation-auditor.md`, `agents/methodology-auditor.md`,
`agents/consistency-auditor.md`, `agents/integrity-auditor.md`,
`agents/gap-analyzer.md`, `agents/source-verifier.md`
