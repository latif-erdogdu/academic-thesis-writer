# Academic Thesis Writer — P0 Implementation Design Spec

**Date:** 2026-09-26  
**Version:** 1.0  
**Status:** Approved for Implementation  
**Author:** Brainstorming Session Output

---

## 1. Genel Mimarî ve P0 Kapsamı

### Hedef
SKILL.md'de tanımlanan V2 mimarisi ile repo arasındaki "drift"i kapatmak. P0'da şunlar **tam çalışır** olacak:

| Bileşen | P0 Durumu |
|---------|-----------|
| 8 Agent dosyaları | ✅ Fiziksel dosya + SKILL referansı |
| 8 Workflow dosyaları | ✅ Fiziksel dosya + SKILL referansı |
| 17 Schema (JSON) | ✅ thesis_state V2 + evidence, claim, citation, paragraph, research_question, research_gap, finding, discussion, conclusion, audit, search_run, dataset, analysis, statistic, table, figure |
| 7 Referans dosyası | ✅ citation_rules, source_verification, evidence_rules, research_gap, academic_integrity, systematic_review_protocol, methodology_rules |
| 5 Template dosyası | ✅ thesis_structure, literature_matrix, evidence_matrix, gap_analysis, quality_report |
| Evidence Engine | ✅ pdf_extract (pymupdf/pdfplumber + passage localization), evidence_extract (claim linking), evidence_verify |
| Source Verification | ✅ Crossref + OpenAlex real HTTP client (httpx, async), SQLite cache, rate limiting, exponential backoff, DOI + metadata verification, retraction/correction check; Semantic Scholar stub |
| Institutional Guidelines | ✅ style_profile.json schema + validator + formatter (APA 7/MLA 9/Chicago/IEEE/Harvard + university override) |
| Human Approval Gates | ✅ Skill-içi basit onay (question tool), state'de `human_approvals` tracking, P1'de external hook |
| Test Altyapısı | ✅ tests/fixtures/ + pytest tabanlı source/evidence/citation/methodology/consistency/integrity testleri |

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
├── AGENTS.md
├── opencode.json
├── README.md
├── .opencode/
│   └── skill/
│       └── academic-thesis-writer/
│           ├── SKILL.md
│           └── agents/ (8 agent)
│
├── agents/                          # 8 agent (SKILL referansı)
│   ├── researcher.md
│   ├── source-verifier.md
│   ├── evidence-extractor.md
│   ├── gap-analyzer.md
│   ├── contradiction-analyzer.md
│   ├── writer.md
│   ├── citation-auditor.md
│   ├── methodology-auditor.md
│   ├── consistency-auditor.md
│   └── integrity-auditor.md
│
├── workflows/                       # 8 workflow
│   ├── thesis_creation.md
│   ├── literature_review.md
│   ├── systematic_review.md
│   ├── chapter_writing.md
│   ├── findings.md
│   ├── discussion.md
│   └── thesis_audit.md
│
├── references/                      # 7 referans
│   ├── citation_rules.md
│   ├── source_verification.md
│   ├── evidence_rules.md
│   ├── research_gap.md
│   ├── academic_integrity.md
│   ├── systematic_review_protocol.md
│   └── methodology_rules.md
│
├── schemas/                         # 17 schema (JSON)
│   ├── thesis_state.json
│   ├── source.json
│   ├── evidence.json
│   ├── claim.json
│   ├── citation.json
│   ├── paragraph.json
│   ├── research_question.json
│   ├── research_gap.json
│   ├── finding.json
│   ├── discussion.json
│   ├── conclusion.json
│   ├── audit.json
│   ├── search_run.json
│   ├── dataset.json
│   ├── analysis.json
│   ├── statistic.json
│   ├── table.json
│   └── figure.json
│
├── templates/                       # 5 template
│   ├── thesis_structure.md
│   ├── literature_matrix.md
│   ├── evidence_matrix.md
│   ├── gap_analysis.md
│   └── quality_report.md
│
├── tools/                           # 4 tool (CLI + Python)
│   ├── source_search/
│   │   ├── __init__.py
│   │   ├── cli.py
│   │   ├── providers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── crossref.py
│   │   │   ├── openalex.py
│   │   │   └── semantic_scholar.py (stub)
│   │   ├── cache.py (SQLite)
│   │   ├── rate_limiter.py (token bucket)
│   │   └── retry.py (exponential backoff)
│   ├── source_verify/
│   │   ├── __init__.py
│   │   ├── cli.py
│   │   ├── verifier.py
│   │   └── retraction_checker.py
│   ├── pdf_extract/
│   │   ├── __init__.py
│   │   ├── cli.py
│   │   ├── extractor.py (pymupdf/pdfplumber)
│   │   ├── ocr.py (tesseract)
│   │   ├── passage_localizer.py (regex + heuristic)
│   │   └── evidence_builder.py
│   └── citation_check/
│       ├── __init__.py
│       ├── cli.py
│       ├── formatter.py (style_profile.json driven)
│       ├── validator.py
│       └── style_profile.json
│
├── tests/                           # Pytest + fixtures
│   ├── fixtures/
│   │   ├── valid_source.json
│   │   ├── fabricated_source.json
│   │   ├── unsupported_claim.json
│   │   ├── contradictory_claim.json
│   │   ├── inconsistent_method.json
│   │   ├── retracted_paper.json
│   │   ├── sample_pdf.pdf
│   │   └── style_profiles/
│   ├── source_tests/
│   ├── evidence_tests/
│   ├── citation_tests/
│   ├── methodology_tests/
│   ├── consistency_tests/
│   └── integrity_tests/
│
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-09-26-academic-thesis-writer-p0-design.md
```

---

## 3. Thesis State V2 — Kritik Alanlar

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

### Gate Konumları
- `thesis_creation.md` → research_question gate
- `systematic_review.md` → search_strategy, source_set gates  
- `gap_analysis.md` → research_gap gate
- `methodology.md` → methodology gate
- `findings.md` → findings gate
- `thesis_audit.md` → final_thesis gate

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

| Phase | Tasks | Deliverable |
|-------|-------|-------------|
| 1 | Repo drift fix: agent/workflow/reference/template/schema dosyalarını oluştur | Tüm SKILL referansları fiziksel dosya olarak mevcut |
| 2 | Schema'lar: thesis_state V2 + 16 yeni schema | JSON schema dosyaları + validation |
| 3 | Tools: source_search (Crossref/OpenAlex real + cache/rate-limit) + source_verify + pdf_extract + citation_check | Çalışan CLI tool'ları |
| 4 | Evidence Engine: pdf_extract + evidence_extract + claim linking | PDF → Evidence → Claim zinciri |
| 5 | Institutional Guidelines: style_profile schema + formatter + validator | APA/MLA/Chicago/IEEE/Harvard + university override |
| 6 | Human Approval Gates: question-tool tabanlı onay akışı | 7 gate state machine |
| 7 | Test altyapısı: fixtures + pytest testleri | Self-testing repo |
| 8 | Integration test: uçtan uca bir tez akışı | Demo çalıştırılabilir |

---

**Spec Self-Review:** ✅ Placeholder yok, iç tutarlılık var, kapsam P0 ile sınırlı, ambiguite yok.

**User Review:** ✅ Approved (brainstorming session output).

**Next Step:** `writing-plans` skill invoke → detailed implementation plan.