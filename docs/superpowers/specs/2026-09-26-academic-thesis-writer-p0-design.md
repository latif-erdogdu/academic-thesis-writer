# Academic Thesis Writer — P0 Implementation Design Spec

**Date:** 2026-09-26  
**Version:** 1.0  
**Status:** Approved for Implementation  
**Author:** Brainstorming Session Output

---

## 1. Genel Mimarî ve P0 Kapsamı

### Hedef
SKILL.md'de tanımlanan mimari ile repo arasındaki drift'i kapatmak. **Mevcut iskeleti çalışır hale getirmek** — dosyaların büyük kısmı zaten mevcut; eksik olan gerçek uygulama (kod) ve veri modeli derinliği.

| Bileşen | Mevcut Durum (doğrulandı) | P0 Hedefi |
|---------|---------------------------|-----------|
| `agents/` | 8 dosya var, SKILL.md 8'ini referanslıyor | 10 dosya → `contradiction-analyzer.md` + `integrity-auditor.md` **yeni** |
| `workflows/` | 8 dosya var, hepsi SKILL.md'de referanslı | Değişiklik yok (8/8 tam) |
| `schemas/` | 7 dosya var, `thesis_state.json` yalın (registry alanları yok) | 18 dosya → 11 şema **yeni**, `thesis_state.json` genişletilir |
| `references/` | 5 dosya var | 7 dosya → `systematic_review_protocol.md` + `methodology_rules.md` **yeni** |
| `templates/` | 5 dosya var | Değişiklik yok (5/5 tam) |
| `tools/` | 4 klasör, **yalnızca README.md** — kod yok | 4 aracın gerçek Python/CLI uygulaması |
| `tests/` | 4 klasör, **yalnızca .md senaryo metni** — çalıştırılamaz | pytest altyapısı + `fixtures/` + 6 test paketi |
| Evidence Engine | Tanımlı, uygulanmamış | `pdf_extract` (pymupdf/pdfplumber + passage localization), `evidence_extract` (claim linking), `evidence_verify` |
| Source Verification | Tanımlı, uygulanmamış | Crossref + OpenAlex gerçek HTTP client (httpx, async), SQLite cache, rate limiting, exponential backoff, DOI + metadata doğrulama, retraction/correction kontrolü; Semantic Scholar stub |
| Institutional Guidelines | Yok | `style_profile.json` şema + validator + formatter (APA 7 / MLA 9 / Chicago / IEEE / Harvard + üniversite override) |
| Human Approval Gates | Yok | Skill içi onay akışı, state'de `human_approvals` takibi; P1'de harici hook |
| Test Altyapısı | Yok (yalnızca senaryo metni) | `tests/fixtures/` + pytest tabanlı source/evidence/citation/methodology/consistency/integrity testleri |

### P0'da Yazılacak Yeni Dosyalar — Özet

| Kategori | Yeni dosya sayısı | Dosyalar |
|----------|------------------|----------|
| Agent | 2 | `agents/contradiction-analyzer.md`, `agents/integrity-auditor.md` |
| Şema | 11 | `citation`, `research_gap`, `finding`, `discussion`, `conclusion`, `search_run`, `dataset`, `analysis`, `statistic`, `table`, `figure` |
| Şema (güncelleme) | 1 | `schemas/thesis_state.json` genişletilir (registry + `human_approvals` + `schema_version`) |
| Referans | 2 | `references/systematic_review_protocol.md`, `references/methodology_rules.md` |
| Araç kodu | ~20 Python | `tools/source_search/`, `tools/source_verify/`, `tools/pdf_extract/`, `tools/citation_check/` |
| Test | 1 config + 6 paket + 10 fixture | `pytest.ini`, `tests/fixtures/`, 6 test klasörü |

### P0'da Değişiklik Yapılmayacak Dosyalar
`SKILL.md` (referanslar zaten doğru), 8 mevcut agent dosyasının içeriği, 8 workflow, 5 template, `.opencode/skill/` kopyası.

### P0 Dışı (P1/P2'ye Bırakılanlar)
- Semantic Scholar gerçek entegrasyonu
- Meta-analysis desteği
- Bibliometric analysis
- Reproducibility/run registry
- Advanced contradiction engine (ML-based)
- Temporal literature tracking
- Review-type protocols (scoping, integrative, bibliometric)
- Dataset/analysis provenance (full chain)
- External workflow orchestration (GitHub Issues/Linear)

---

## 2. Dizin Yapısı (Target)

```
academic-thesis-writer/
├── SKILL.md
├── README.md
├── AGENTS.md                          # graft MCP + repo talimatı (.gitignore'da)
├── opencode.json                      # graft MCP yapılandırması (.gitignore'da)
├── pytest.ini                         # [YENİ] pytest yapılandırması
├── requirements.txt                   # [YENİ] Python bağımlılıkları
├── .opencode/
│   └── skill/
│       └── academic-thesis-writer/
│           ├── SKILL.md               # kök SKILL.md'nin senkron kopyası
│           └── agents/                # 10 agent kopyası
│
├── agents/                          # 10 agent — 8 mevcut + 2 yeni
│   ├── researcher.md                 # mevcut
│   ├── source-verifier.md            # mevcut
│   ├── evidence-extractor.md         # mevcut
│   ├── gap-analyzer.md               # mevcut
│   ├── writer.md                     # mevcut
│   ├── citation-auditor.md           # mevcut
│   ├── methodology-auditor.md        # mevcut
│   ├── consistency-auditor.md        # mevcut
│   ├── contradiction-analyzer.md     # [YENİ] P0
│   └── integrity-auditor.md          # [YENİ] P0
│
├── workflows/                       # 8 workflow — TAM (değişiklik yok)
│   ├── thesis_creation.md
│   ├── literature_review.md
│   ├── systematic_review.md
│   ├── methodology.md
│   ├── chapter_writing.md
│   ├── findings.md
│   ├── discussion.md
│   └── thesis_audit.md
│
├── references/                      # 7 referans — 5 mevcut + 2 yeni
│   ├── citation_rules.md             # mevcut
│   ├── source_verification.md        # mevcut
│   ├── evidence_rules.md             # mevcut
│   ├── research_gap.md               # mevcut
│   ├── academic_integrity.md         # mevcut
│   ├── systematic_review_protocol.md # [YENİ] P0
│   └── methodology_rules.md          # [YENİ] P0
│
├── schemas/                         # 18 şema — 7 mevcut + 11 yeni
│   ├── thesis_state.json             # [GÜNCELLEME] registry alanları eklenir
│   ├── source.json                   # mevcut — [GÜNCELLEME] retraction_status
│   ├── evidence.json                 # mevcut — [GÜNCELLEME] evidence_type
│   ├── claim.json                    # mevcut
│   ├── paragraph.json                # mevcut
│   ├── research_question.json        # mevcut
│   ├── audit.json                    # mevcut
│   ├── citation.json                 # [YENİ] P0
│   ├── research_gap.json             # [YENİ] P0
│   ├── finding.json                  # [YENİ] P0
│   ├── discussion.json               # [YENİ] P0
│   ├── conclusion.json               # [YENİ] P0
│   ├── search_run.json               # [YENİ] P0 (PRISMA provenance)
│   ├── dataset.json                  # [YENİ] P0
│   ├── analysis.json                 # [YENİ] P0
│   ├── statistic.json                # [YENİ] P0
│   ├── table.json                    # [YENİ] P0
│   └── figure.json                   # [YENİ] P0
│
├── templates/                       # 5 template — TAM (değişiklik yok)
│   ├── thesis_structure.md
│   ├── literature_matrix.md
│   ├── evidence_matrix.md
│   ├── gap_analysis.md
│   └── quality_report.md
│
├── tools/                           # 4 araç — 4 README var, kod 0
│   ├── source_search/                # [YENİ] gerçek kod
│   │   ├── __init__.py
│   │   ├── cli.py
│   │   ├── providers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # Provider arayüzü (3 provider için)
│   │   │   ├── crossref.py           # gerçek HTTP client
│   │   │   ├── openalex.py           # gerçek HTTP client
│   │   │   └── semantic_scholar.py   # stub (P1'de gerçek)
│   │   ├── cache.py                  # SQLite cache (gerçek)
│   │   ├── rate_limiter.py           # token bucket (gerçek)
│   │   └── retry.py                  # exponential backoff (gerçek)
│   ├── source_verify/                # [YENİ] gerçek kod
│   │   ├── __init__.py
│   │   ├── cli.py
│   │   ├── verifier.py               # DOI + metadata doğrulama
│   │   └── retraction_checker.py     # retraction/correction kontrolü
│   ├── pdf_extract/                  # [YENİ] gerçek kod
│   │   ├── __init__.py
│   │   ├── cli.py
│   │   ├── extractor.py              # pymupdf/pdfplumber
│   │   ├── ocr.py                    # tesseract
│   │   ├── passage_localizer.py      # regex + heuristic
│   │   └── evidence_builder.py       # evidence + claim linking
│   ├── citation_check/               # [YENİ] gerçek kod
│   │   ├── __init__.py
│   │   ├── cli.py
│   │   ├── formatter.py              # style_profile.json güdümlü
│   │   ├── validator.py
│   │   └── style_profile.json
│   └── atw/                          # [YENİ] ortak çekirdek
│       ├── __init__.py
│       ├── state.py                  # thesis_state yükle/kaydet/geçerlilik
│       ├── ids.py                    # SRC-/EVD-/CLM-... kimlik üretimi
│       ├── approval.py               # human approval gate akışı
│       └── models.py                 # pydantic modelleri (şemaların karşılığı)
│
├── tests/                           # 4 senaryo .md var, çalıştırılabilir test 0
│   ├── fixtures/                     # [YENİ]
│   │   ├── valid_source.json
│   │   ├── fabricated_source.json
│   │   ├── retracted_paper.json
│   │   ├── corrected_paper.json
│   │   ├── unsupported_claim.json
│   │   ├── contradictory_claim.json
│   │   ├── inconsistent_method.json
│   │   ├── sample_pdf.pdf            # 5 sayfa, bölüm başlıkları + tablo
│   │   └── style_profiles/
│   │       ├── apa7.json
│   │       ├── mla9.json
│   │       └── university-x-department-y-apa7.json
│   ├── conftest.py                   # [YENİ] ortak fixture yükleyici
│   ├── source_tests/                 # mevcut .md + [YENİ] pytest
│   ├── evidence_tests/               # [YENİ]
│   ├── citation_tests/               # mevcut .md + [YENİ] pytest
│   ├── methodology_tests/            # mevcut .md + [YENİ] pytest
│   ├── consistency_tests/            # mevcut .md + [YENİ] pytest
│   └── integrity_tests/              # [YENİ]
│
└── docs/
    └── superpowers/
        ├── specs/
        │   └── 2026-09-26-academic-thesis-writer-p0-design.md
        └── plans/                    # [YENİ] writing-plans çıktısı
```

---

## 3. Thesis State — Genişletilmiş Yapı

```json
{
  "schema_version": "2.0",
  "thesis_id": "THESIS-2026-001",
  "title": "",
  "field": "",
  "discipline": "",
  "degree": "",
  "language": "tr",
  "research_problem": "",
  "purpose": "",
  "research_questions": [],
  "hypotheses": [],
  "conceptual_framework": [],
  "methodology": { ... },
  "chapters": [],
  
  "evidence_registry": [],        // EVD-XXX listesi
  "claims_registry": [],          // CLM-XXX listesi  
  "findings_registry": [],        // FND-XXX listesi
  "discussion_registry": [],      // DSC-XXX listesi
  "conclusion_registry": [],      // CON-XXX listesi
  "gap_registry": [],             // GAP-XXX listesi
  "audit_registry": [],           // AUD-XXX listesi
  "search_runs": [],              // SEARCH-XXX listesi
  
  "sources": [],                  // SRC-XXX (verified)
  "citations": [],                // CIT-XXX
  "definitions": [],
  "variables": [],
  "open_questions": [],
  "quality_issues": [],
  
  "human_approvals": {
    "research_question": false,
    "search_strategy": false,
    "source_set": false,
    "research_gap": false,
    "methodology": false,
    "findings": false,
    "final_thesis": false
  },
  
  "style_profile": "apa7",
  "created_at": "",
  "updated_at": "",
  "version": 1
}
```

### Entity ID Standardı
- `SRC-XXX` — Source
- `EVD-XXX` — Evidence  
- `CLM-XXX` — Claim
- `CIT-XXX` — Citation
- `P-XXX` — Paragraph
- `RQ-XXX` — Research Question
- `HYP-XXX` — Hypothesis
- `FND-XXX` — Finding
- `DSC-XXX` — Discussion
- `CON-XXX` — Conclusion
- `GAP-XXX` — Research Gap
- `AUD-XXX` — Audit
- `SEARCH-XXX` — Search Run
- `DS-XXX` — Dataset
- `ANL-XXX` — Analysis
- `STAT-XXX` — Statistic
- `TBL-XXX` — Table
- `FIG-XXX` — Figure

---

## 4. Evidence Engine — Veri Akışı

```
PDF / Full Text
      │
      ▼
pdf_extract.extractor.extract_pages()  →  List[PageText(page_num, text, sections)]
      │
      ▼
pdf_extract.passage_localizer.locate()  →  List[Passage(page, section, text, char_start, char_end)]
      │
      ▼
evidence_extract.evidence_builder.build()  →  Evidence(
      id: EVD-XXX,
      source_id: SRC-XXX,
      location: {page, section, paragraph},
      text: "...",
      evidence_type: "finding|method|theory|data|statistical",
      supports_claim: CLM-XXX,
      strength: "direct|indirect",
      verified: true,
      extracted_at: "..."
   )
      │
      ▼
claim.claim_linker.link_evidence()  →  Claim.evidence_ids.append(EVD-XXX)
      │
      ▼
thesis_state.evidence_registry.append(EVD-XXX)
```

### Passage Localization Heuristics (P0)
- Section header detection (regex: `^\d+(\.\d+)*\s+[A-Z]`)
- Reference to page/section in text (e.g., "Table 3 shows...", "In Section 2.1...")
- Keyword proximity (claim keywords within ±3 sentences)

---

## 5. Source Verification — Veri Akışı

```
Source Candidate (DOI/Title/Author/Year)
      │
      ▼
source_search.providers.Crossref.lookup()  →  Metadata
      │
      ▼
source_search.providers.OpenAlex.lookup()  →  Metadata
      │
      ▼
source_verify.verifier.match_metadata()  →  VerificationResult(
      status: "verified|unverified|pending|retracted|corrected",
      bibliographic_match: 0.95,
      doi_match: true,
      author_match: true,
      title_match: true,
      year_match: true,
      journal_match: true,
      retraction_status: "not_retracted",
      correction_status: "none",
      supersedes: null,
      verified_at: "...",
      verification_sources: ["crossref", "openalex"]
   )
      │
      ▼
thesis_state.sources.append(Source(verification=...))
```

### Cache Schema (SQLite)
```sql
CREATE TABLE source_cache (
  key TEXT PRIMARY KEY,
  provider TEXT,
  response_json TEXT,
  fetched_at TIMESTAMP,
  expires_at TIMESTAMP
);
CREATE TABLE rate_limits (
  provider TEXT PRIMARY KEY,
  tokens REAL,
  last_refill TIMESTAMP
);
```

---

## 6. Institutional Guidelines — Style Profile

```json
{
  "schema_version": "1.0",
  "profile_id": "university-x-department-y-apa7",
  "name": "Üniversite X — Bölüm Y — APA 7",
  "base_style": "apa7",
  "citation": {
    "in_text": "author_year",
    "reference_list": "apa7",
    "page_format": "p. X / pp. X-Y",
    "et_al_threshold": 3,
    "date_format": "YYYY"
  },
  "formatting": {
    "font": "Times New Roman",
    "font_size": 12,
    "line_spacing": 1.5,
    "margins": { "top": 2.54, "bottom": 2.54, "left": 2.54, "right": 2.54 },
    "page_numbers": "bottom_center",
    "heading_style": {
      "chapter": { "level": 1, "format": "BÖLÜM X", "bold": true, "size": 14 },
      "section": { "level": 2, "format": "X.Y", "bold": true, "size": 12 },
      "subsection": { "level": 3, "format": "X.Y.Z", "italic": true, "size": 12 }
    },
    "table_style": { "caption_position": "top", "numbering": "chapter" },
    "figure_style": { "caption_position": "bottom", "numbering": "chapter" },
    "abstract": { "max_words": 300, "structured": false, "keywords": true },
    "toc": { "max_depth": 3 }
  },
  "university_overrides": {
    "chapter_order": ["abstract", "acknowledgments", "toc", "list_of_tables", "list_of_figures", "chapters", "references", "appendices"],
    "required_sections": ["abstract", "keywords", "acknowledgments"],
    "language": "tr"
  }
}
```

### Writer Agent Kullanımı
1. `thesis_state.style_profile` → load profile
2. Paragraph yazarken → `formatter.format_paragraph()`
3. Citation eklerken → `formatter.format_citation(source, style)`
4. Bölüm bitiminde → `validator.check_format(chapter_text, profile)`
5. Final → `formatter.generate_bibliography(sources, profile)`

---

## 7. Human Approval Gates — State Machine

```python
APPROVAL_GATES = [
  "research_question",
  "search_strategy", 
  "source_set",
  "research_gap",
  "methodology",
  "findings",
  "final_thesis"
]

async def request_approval(gate_name: str, context: dict):
    if thesis_state.human_approvals[gate_name]:
        return True
    print(f"⏸️  ON BEKLİYOR: {gate_name}")
    print(f"Bağlam: {context}")
    response = await question(f"{gate_name} onaylanıyor mu? (evet/hayır/detay)")
    if response.lower() == "evet":
        thesis_state.human_approvals[gate_name] = True
        save_state()
        return True
    elif response.lower() == "detay":
        return await request_approval(gate_name, context)
    return False
```

### Gate Konumları (Workflow dosyalarına bağlanır)
- `workflows/thesis_creation.md` → `research_question` gate
- `workflows/systematic_review.md` → `search_strategy`, `source_set` gate'leri
- `workflows/literature_review.md` → `research_gap` gate
- `workflows/methodology.md` → `methodology` gate
- `workflows/findings.md` → `findings` gate
- `workflows/thesis_audit.md` → `final_thesis` gate

> Not: `templates/gap_analysis.md` bir şablondur, gate tanımı içermez. `research_gap` gate'i ilgili workflow'a bağlanır.

### Uygulama Konumu
Gate mantığı `tools/atw/approval.py` içinde yaşar. Agent'lar (insan onayı soran taraf) `workflows/*.md` talimatlarıdır; `approval.py` onay durumunu `thesis_state.human_approvals` içinde okur/yazar ve `question` aracını çağırır.

---

## 8. Test Stratejisi — Fixtures

```
tests/fixtures/
├── valid_source.json
├── fabricated_source.json
├── retracted_paper.json
├── corrected_paper.json
├── unsupported_claim.json
├── contradictory_claim.json
├── inconsistent_method.json
├── sample_pdf.pdf
└── style_profiles/
    ├── apa7.json
    ├── mla9.json
    └── university-x-department-y-apa7.json
```

### Test Kategorileri
| Test Dosyası | Ne Test Ediyor |
|-------------|----------------|
| `source_tests/test_verification.py` | DOI lookup, metadata match, retraction detection, cache hit/miss |
| `evidence_tests/test_extraction.py` | PDF → passage → evidence → claim linking, strength classification |
| `citation_tests/test_format.py` | APA/MLA/Chicago/IEEE/Harvard format, style_profile override |
| `methodology_tests/test_alignment.py` | RQ↔Method, Hypothesis↔Variables, Analysis↔Finding |
| `consistency_tests/test_crossref.py` | Terminology, numbers, sample, dates, chapter cross-refs |
| `integrity_tests/test_fabrication.py` | Fabricated source detection, unsupported claim detection |

---

## 9. Implementation Sequence (P0)

Sıralama ilkesi: **önce veri modeli, sonra kod, en son test.** Çünkü araçlar şemaları okur; şema değişmeden yazılan araç kodu yeniden yazılır.

| Faz | İçerik | Bağımlılık | Teslim Edilebilir Kanıt |
|-----|--------|------------|------------------------|
| 0 | Ortak çekirdek: `requirements.txt`, `pytest.ini`, `tools/atw/` (ids, models, state, approval çekirdeği) | — | `pytest` çalışır (0 test, hatasız), `atw.ids.next_id("SRC")` → `SRC-001` |
| 1 | Şemalar: 11 yeni şema + `thesis_state.json` genişletme + `source.json`/`evidence.json` güncelleme | Faz 0 | Her şema `jsonschema` ile doğrulanır; `thesis_state` şeması registry alanlarını zorunlu kılar |
| 2 | Test altyapısı: `tests/fixtures/` (10 fixture) + `conftest.py` + şema doğrulama testleri | Faz 1 | `pytest tests/` yeşil; `valid_source.json` geçer, `fabricated_source.json` şemayı geçer ama integrity testinde reddedilir |
| 3 | Source Search: provider arayüzü + Crossref + OpenAlex + SQLite cache + rate limiter + retry | Faz 0 | CLI: `python -m tools.source_search --doi 10.xxxx/yyy` gerçek metadata döner; ikinci çağrı cache'ten; 429'da retry eder |
| 4 | Source Verify: metadata eşleştirme + retraction/correction kontrolü | Faz 3 | `python -m tools.source_verify` DOI + başlık + yazar + yıl + dergi + DOI + retraction durumunu raporlar |
| 5 | Evidence Engine: `pdf_extract` (extractor + ocr + passage_localizer + evidence_builder) | Faz 0 | `sample_pdf.pdf` → sayfa/bölüm/alıntı → `EVD-XXX`; claim linking `CLM.evidence_ids`'e yazar |
| 6 | Citation Check: `style_profile.json` + formatter (5 stil) + validator + üniversite override | Faz 0 | APA/MLA/Chicago/IEEE/Harvard çıktısı; aynı kaynak farklı profilde farklı biçimlenir |
| 7 | Human Approval Gates: `atw/approval.py` 7 gate durum makinesi | Faz 0 | Gate reddi akışı durdurur; onay `thesis_state.human_approvals`'e yazılır ve kalıcıdır |
| 8 | 2 yeni ajan: `contradiction-analyzer.md`, `integrity-auditor.md` + SKILL.md yönlendirme tablosu | Faz 1,4,5 | SKILL.md 10 ajanı da adlandırır; iki ajan dosyası mevcut |
| 9 | 2 yeni referans: `systematic_review_protocol.md`, `methodology_rules.md` | Faz 1 | SKILL.md 7 referansı da adlandırır |
| 10 | Bütünleşik test: uçtan uca akış (arama → doğrulama → PDF → kanıt → iddia → atıf → denetim) | Faz 2-9 | `pytest tests/integration/` yeşil; tek komutla tam zincir çalışır |
| 11 | README + SKILL.md son güncelleme; `.opencode/skill/` kopyası senkronizasyonu | Faz 10 | Push edilen commit'te `.opencode/skill/` kök ile birebir aynı |

### Kritik Uyarılar

- **Faz sırası ihlal edilmemeli.** Faz 3 (source_search) Faz 1 (şemalar) tamamlanmadan yazılırsa, provider'lar geçici dict şemasına göre kodlanır ve Faz 1'de elden geçer.
- **Faz 10 ağ erişimi gerektirir.** Crossref/OpenAlex canlı çağrı yapar. Testler `--live` bayrağı olmadan fixture tabanlı çalışmalı; canlı testler ayrı marker ile işaretlenip CI'da varsayılan kapalı olmalı.
- **`tools/atw/` çekirdeği yeni.** Dört araç da state okuma/yazma, kimlik üretimi ve şema doğrulama ihtiyacı duyuyor. Bu ortak katman Faz 0'da kurulmazsa her araç kendi kopyasını yazar.

---

**Spec Self-Review:** ✅

1. *Placeholder taraması* — "TBD"/"TODO" yok; tüm ID formatları, enum değerleri ve dosya yolları tanımlı.
2. *İç tutarlılık* — Durum tablosu (mevcut → hedef), dizin ağacı (`[YENİ]`/`[GÜNCELLEME]` işaretleri) ve faz sırası birbirini tutuyor. Ağaçtaki 18 şema ile "11 yeni + 2 güncelleme + 5 mevcut" eşleşiyor. Ağaçtaki 10 ajan ile "8 mevcut + 2 yeni" eşleşiyor.
3. *Kapsam denetimi* — P0 tek bir plan için uygun; 12 faz sıralı bağımlılık zinciriyle ayrılabilir durumda. Semantic Scholar, meta-analiz, bibliometrik analiz P1/P2'ye itildi.
4. *Belirsizlik denetimi* — "2 bağımsız kaynak" kuralı Faz 4'te somut olarak "crossref + openalex" provider adlarına bağlandı. `quality_score` tek puan yerine ayrık alanlara (`retraction_status`, `correction_status`, `strength`) bağlandı. Uydurma kaynak riski `integrity-auditor` ajanı ve `tests/fixtures/fabricated_source.json` ile karşılanıyor.

**Düzeltme kaydı (2026-09-26):** İlk yazımda durum tablosu `agents/`, `workflows/`, `templates/`, `references/` klasörlerinin "mevcut" olduğunu doğru yansıtmıyordu. Repo doğrulaması yapıldı: 8 agent, 8 workflow, 5 template, 5 referans ve 7 şema zaten mevcut. Tablo "Mevcut Durum → P0 Hedefi" formatına çevrildi; dizin ağacına `[YENİ]` / `[GÜNCELLEME]` işaretleri eklendi; `workflows/methodology.md` ağaca geri alındı; şema sayısı 17 → 18 düzeltildi; ortak çekirdek `tools/atw/` eklendi.

**Kullanıcı Onayı:** ✅ Tasarım bölümleri onaylandı. Kapsam kararı: 10 ajanın tamamı P0'da. Spec düzeltmesi talep edildi ve uygulandı.

**Sonraki Adım:** `writing-plans` → ayrıntılı implementation planı.