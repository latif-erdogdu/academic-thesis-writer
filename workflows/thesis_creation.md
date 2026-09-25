# Thesis Creation Workflow

## Overview
This workflow orchestrates the end-to-end creation of a comprehensive academic thesis, integrating literature review, methodology, and writing phases.

## Prerequisites
Before running this workflow:
- ✓ Complete literature review (`workflows/literature_review.md`)
- ✓ Finalize research methodology (`workflows/methodology.md`)
- ✓ Define chapter structure

## Execution Order
1. Literature Review Analysis → `literature_matrix.md` output
2. Methodology Planning → `methodology_state.json` updates
3. Thesis Structure Generation → Using `templates/thesis_structure.md`
4. Chapter-by-Chapter Writing → Via `workflows/chapter_writing.md`
5. Integration and Synthesis → Combine all chapters with introduction/conclusion
6. Quality Review → Run `workflows/thesis_audit.md`

## State Management
State is tracked in:
- `schemas/thesis_state.json` - Overall progress and metadata
- `references/source_verification.md` - Source quality tracking

## Workflow Steps

### Step 1: Literature Synthesis
```markdown
## Chapter 1: Introduction
- Research background
- Problem statement
- Research questions/objectives
- Significance of study
- Thesis structure overview

See: templates/thesis_structure.md for outline
```

### Step 2: Methodology Integration
- Review methodology chapter output
- Ensure consistency with research design
- Verify alignment with research questions

### Step 3: Results & Discussion Generation
- Integrate literature insights with findings
- Ensure proper citation of all claims
- Cross-reference verified sources

### Step 4: Conclusion Synthesis
- Summarize key contributions
- Address each research question
- Discuss implications and limitations
- Suggest future research directions

## Output Structure
```
Thesis/
├── 01_Introduction.md
├── 02_Literature_Review.md
├── 03_Methodology.md
├── 04_Results.md
├── 05_Discussion.md
├── 06_Conclusion.md
├── References.bib
└── Quality_Report.md
```

## Citation Integration
- All claims must be attributed (see `references/citation_rules.md`)
- Verify all sources through source verification checklist
- Maintain consistent citation style throughout

## Quality Gates
Before moving between chapters:
1. Review previous chapter for completeness
2. Check citation accuracy
3. Verify state file is updated (`schemas/thesis_state.json`)
4. Ensure smooth transitions between sections

## Next Step
After thesis creation completes, run the audit workflow:
```bash
# Run thesis audit
workflows/thesis_audit.md
```
