# Literature Review Workflow

## Overview
This workflow guides the systematic review and synthesis of existing research on your thesis topic.

## Phase 1: Topic Definition
### Define Scope
- **Research area**: Clearly articulate the field/domain
- **Key concepts**: Identify core terminology
- **Boundaries**: Specify inclusion/exclusion criteria

### Search Strategy
1. Academic databases (Google Scholar, Scopus, Web of Science)
2. Conference proceedings
3. Grey literature as appropriate
4. Key authors and seminal works in field

## Phase 2: Source Collection
### Minimum Requirements
- **Seminal papers**: Foundational works (prioritize these)
- **Recent publications**: Last 5 years where possible
- **Methodological diversity**: Multiple approaches if applicable
- **Geographic/temporal scope**: Clear boundaries if relevant

### Collection Template
```markdown
## Source Entry
### Citation: [Full citation]
### Relevance score: High/Medium/Low
### Key contribution: [1-2 sentences]
### Methodology type: [Quantitative/Qualitative/Mixed]
### Date: YYYY
### Status: ✓ Verified / ⚠ Needs review / ✗ Discard
```

## Phase 3: Synthesis Matrix
Generate the literature matrix using `templates/literature_matrix.md`:

### Structure
```markdown
# Literature Review Matrix
## Topic Area
| Author (Year) | Key Finding | Methodology | Limitations | Relevance Score |
|---------------|-------------|--------------|-------------|-----------------|
|               |             |              |             |                 |

## Themes Identified
1. Theme 1: [Summary]
2. Theme 2: [Summary]
3. Theme 3: [Summary]

## Gaps Identified
- Gap 1: [What's missing in current research]
- Gap 2: [What needs further investigation]
- Gap 3: [Opportunities for contribution]
```

## Phase 4: Writing the Review Chapter
### Section 1: Introduction to Literature Review
- Purpose of review
- Scope and organization
- Selection criteria

### Section 2: Thematic Organization
- Group sources by themes rather than chronologically
- Within each theme: synthesize, don't just list
- Identify patterns, contradictions, gaps

### Section 3: Critical Analysis
- Compare methodological approaches
- Evaluate strength of evidence
- Note limitations in existing work
- Position your research within the landscape

### Section 4: Gap Identification
- Clearly articulate research gaps
- Connect gaps to research questions
- Justify how this thesis addresses them

## Phase 5: Integration with Thesis State
Update `schemas/thesis_state.json` with:
- Literature review completion status
- Key themes identified
- Gaps documented
- Sources verified count

## Quality Checklist
- [ ] All sources properly cited
- [ ] No gaps in literature coverage
- [ ] Themes are clearly articulated
- [ ] Critical analysis (not just summary) present
- [ ] Gaps clearly connected to research questions
- [ ] Literature matrix completed and accurate
- [ ] All sources verified per `references/source_verification.md`

## Next Steps
After completing literature review:
1. Update thesis state file
2. Define methodology based on literature findings
3. Proceed to `workflows/methodology.md`
