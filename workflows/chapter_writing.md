# Bölüm Yazımı Çalışma Akışı

> **Bu akış bir komut dizisidir.** Ana zincir: `workflows/thesis_creation.md`
> Yalnızca `methodology` kapısı açıkken çalışır.

## Ön koşul: `methodology` kapısı açık olmalı

`thesis:write` ilk iş olarak `methodology` kapısını sorar. Kapı kapalıysa
yazım yapılmaz: sonradan yöntem değişince yazılmış tüm bölümler geçersiz
olur ve baştan yazılması gerekir.

## İki kip — ayrım bilinçlidir

```bash
thesis:write CH-001 --rq RQ-001                       # 1) brifing
thesis:write CH-001 --rq RQ-001 --file <BOLUM.json>  # 2) denetle + kaydet
```

| | `--file` yok | `--file` var |
|---|---|---|
| Ne yapar | brifing basar | bölümü denetler |
| Tez durumu | **değişmez** | bölümü kaydeder |
| Kim yazar | — | `agents/writer.md` ajanı |

**CLI Türkçe tez metni yazmaz.** Brifing verir, ajan metni yazar, CLI
doğrular. Bu Writing Gate'in varoluş sebebidir.

`--json` bayrağı brifingi makine-okunur biçimde basar:

```bash
thesis:write CH-001 --rq RQ-001 --json
```

## Adım 1 — Bölüm dosyasının şekli

`--file` verilen dosya `schemas/chapter.json` şemasına uyan **tek bir
JSON nesnesidir** (dizi değil):

```json
{
  "id": "CH-001",
  "number": 1,
  "title": "Giriş",
  "goal": "Araştırma sorusunu ve kapsamı tanımlamak",
  "paragraphs": [
    {
      "id": "P-001",
      "chapter": "CH-001",
      "section": "1.1",
      "type": "introduction",
      "text": "Paragraf metni.",
      "claims": ["CLM-001"],
      "evidence": ["EVD-001"],
      "sources": ["SRC-001"],
      "citations": ["CLM-001"],
      "research_questions": ["RQ-001"]
    }
  ]
}
```

Kurallar:

- `id` deseni `^CH-\d{3,}$`
- `paragraphs[].chapter` dosyadaki `id` ile **aynı** olmalı
- `research_questions` içindeki her kimlik `research_questions`
  registry'sinde var olmalı
- `sources` içindeki her kaynak `verified` olmalı — doğrulanmamış kaynak
  bölüme giremez (`tools/atw/write.py:haric_eden_kaynaklar`)
- `additionalProperties: false` — şemada olmayan alan hata verir

## Adım 2 — Denetim ve kayıt

Tek bir sorun bile varsa **hiçbir şey yazılmaz**; dosya yerinde bırakılır,
görünen her sorun listelenir ve düzeltip yeniden deneyebilirsiniz. Yarım
bölüm kaydedilmez.

Kayıt öncesi tez durumu şemaya karşı da doğrulanır. Doğrulama hatası
bölüm dosyasından değil, durumun **başka** registry'lerinden geliyor
olabilir; bu durumda bölüm kaydedilmez ve yolundaki alanı düzeltmeniz
gerekir.

## Adım 3 — Kalite kontrolü (CLI'nin denetlemediği kısım)

`thesis:write` şemayı ve bağları denetler, **üslubu denetlemez**. Elle
kontrol edilecekler:

- [ ] Akademik dil; süslü ifade yok
- [ ] Paragraf yapısı: her paragraf bir iddia + dayanağı taşır
- [ ] BULGU ve YORUM ayrı (`workflows/findings.md`)
- [ ] Metin içi atıf ↔ `citations` eşleşmesi
- [ ] `research_questions` bağlantısı doğru
- [ ] Atıf biçimi `references/citation_rules.md` ile uyumlu
- [ ] Terminoloji tez boyunca aynı

## Toplu yazım

```bash
thesis:write CH-001 --rq RQ-001 --file <C1.json>
thesis:write CH-002 --rq RQ-002 --file <C2.json>
thesis:write CH-003 --rq RQ-001 --file <C3.json>
```

Bölümler birbirinden bağımsızdır; sıra onay zincirinde belirlenir,
komutta değil.

## Şablonlar

- `templates/thesis_structure.md` — bölüm iskeleti
- `references/citation_rules.md` — atıf biçimi

## Sırada

```bash
thesis:audit --type all
thesis:approve final_thesis
thesis:export --format docx
```
