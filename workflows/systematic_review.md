# Sistematik İnceleme Çalışma Akışı

> **Bu akış bir komut dizisidir.** Bu dosya PRISMA akışını yedi kapıya ve
> gerçek komutlara eşler. Ana zincir: `workflows/thesis_creation.md`

## PRISMA adımı → kapı → komut

| PRISMA adımı | Kapı | Komut |
|---|---|---|
| Araştırma sorusu | `research_question` | `thesis:new` → `thesis:record research_questions` → `thesis:approve research_question` |
| Arama stratejisi | `search_strategy` | `thesis:search` → `thesis:approve search_strategy` |
| Veritabanı seçimi + arama sorgusu | `search_strategy` | `thesis:search --databases … --pico …` |
| Dahil/hariç tutma kriterleri | `search_strategy` | `--pico` metninde ifade edilir |
| Tarama (başlık/özet) | `source_set` | `thesis:verify --all` |
| Tam metin incelemesi | `source_set` | `thesis:verify --all` |
| Kalite değerlendirme | `source_set` | `thesis:verify` (eşleşme ≥ 0.60) |
| Veri çıkarımı | `source_set` | `thesis:extract SRC-001 --claim CLM-001 --pdf <dosya.pdf>` |
| Sentez | `research_gap` | `thesis:record gap_registry` → `thesis:approve research_gap` |
| Değerlendirme | `methodology` | `thesis:record variables/datasets/analyses/statistics` → `thesis:approve methodology` |
| Yayın / raporlama | `final_thesis` | `thesis:audit` → `thesis:approve final_thesis` → `thesis:export` |

Tekrar giderme (`PRISMA` 3. adımı) `thesis:search`'in her çalıştırılmasıyla
olur; her çalıştırma `search_runs`'a ayrı bir kayıt bırakır. Bu, tekrar
gidermenin izlenebilir olmasını sağlar.

## Veritabanları

`--databases` varsayılanı: `crossref,openalex,pubmed`

**Google Scholar ve Semantic Scholar CLI'da yoktur.** Akışta sayılan
veritabanı listesinin geri kalanını kapsamaz; arama bu üçüyle sınırlıdır.

## Kayıt

CLI'ya yazılan registry'ler:

- `search_runs` — her arama (sorgu, veritabanı, sonuç sayısı)
- `sources` — `thesis:verify` sonucu, `verification.status` ile
- `evidence_registry` — `thesis:extract` sonucu
- `gap_registry` — `research_gap` kapısının girdisi

## Çıktı

PRISMA akışının dört çıktısı, tez durumunda şu karşılıklara oturur:

| PRISMA çıktısı | Tez karşılığı |
|---|---|
| Literatür matrisi | `templates/literature_matrix.md` (bölüm taslağına girer) |
| Kanıt matrisi | `evidence_registry` + `templates/evidence_matrix.md` |
| Boşluk analizi | `gap_registry` (şema: `schemas/research_gap.json`) |
| Kalite değerlendirme raporu | `audit_registry` (`thesis:audit` kayıtları) |

## Kaynak

- `references/systematic_review_protocol.md` — ayrıntılı protokol
- `references/research_gap.md` — boşluk tanımı kuralları
- `references/source_verification.md` — doğrulama ölçütleri
