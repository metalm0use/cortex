---
schema_version: 1
tags:
  - "legal"
  - "immigration"
  - "writing"
  - "strategy"
topics:
  - "visa strategy"
  - "visa category analysis"
  - "immigration pathways"
  - "Visa Bulletin"
  - "USCIS processing times"
status: seed
created: 2026-06-15
updated: 2026-06-15
sources:
  - "https://github.com/Gonzih/skills-immigration/blob/main/skills/visa-brief/SKILL.md"
  - "https://www.uscis.gov/policy-manual"
  - "https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin.html"
  - "https://egov.uscis.gov/processing-times/"
source_count: 4
aliases:
  - "immigration visa brief"
  - "visa brief"
  - "visa options"
  - "visa strategy"
  - "immigration options memo"
  - "immigration pathway"
skill_id: legal/immigration-visa-brief
summary: "Draft immigration visa option and strategy briefs that compare candidate categories, risks, timelines, and next steps."
model_role: thinking
depends_on:
  - meta/contributing
related:
  - legal/immigration-case-summary
  - legal/immigration-client-letter
  - legal/immigration-rfe-response
  - writing/article-writing
---

# Immigration Visa Brief

<!-- learned: 2026-06 | project: cortex-skill-import | model: thinking-model -->

Use this skill when asked to analyze visa options, compare immigration
pathways, draft a visa strategy memo, evaluate a client against visa
categories, or prepare an attorney-facing immigration options brief.

## Core Rule

Analyze eligibility from supplied facts, not optimism. Attempt official
lookups for current eligibility guidance, Visa Bulletin availability,
and processing-time estimates before making timing or availability
claims. Mark all strategy recommendations for attorney review.

## Workflow

1. Collect the client snapshot: nationality, country of birth or
   chargeability, current status, education, work history, achievements,
   family ties, employer sponsorship, goals, urgency, travel needs, and
   prior immigration issues.
2. Identify plausible categories across temporary work visas, immigrant
   employment categories, family categories, and humanitarian or other
   relief only when the facts support considering them.
3. Attempt official lookups when current public data affects the memo:
   - USCIS Policy Manual at `https://www.uscis.gov/policy-manual` for
     agency guidance and eligibility framing.
   - State Department Visa Bulletin at
     `https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin.html`
     for priority-date availability.
   - USCIS processing times at `https://egov.uscis.gov/processing-times/`
     for current agency timing estimates.
4. For each candidate category, assess eligibility as `Strong`,
   `Possible`, or `Unlikely`, with strengths, weaknesses, sponsorship
   needs, timing, wait-time constraints, and evidence gaps.
5. Recommend a primary path, secondary or parallel path, short-term
   status plan, and long-term permanent-residence plan when applicable.
6. Flag risks that require attorney analysis: unlawful presence, status
   gaps, prior denials, criminal history, inadmissibility, removal
   orders, country-specific backlog, cap constraints, and travel risks.

## Output Shape

Use these sections unless the user asks for a narrower memo:

1. Client Snapshot table.
2. Candidate Categories table.
3. Recommended Strategy with primary and backup paths.
4. Timing And Availability Notes with lookup dates and caveats.
5. Next Steps.
6. Risks And Caveats.

## Lookup Caveats

Do not use stale examples for current Visa Bulletin cutoffs, processing
times, agency fees, or USCIS policy positions. If lookup is unavailable,
write a visible caveat:

```text
[ATTORNEY TO VERIFY] Current Visa Bulletin and USCIS processing-time
data before advising the client.
```

Do not estimate filing fees unless the user supplied them or an official
current source was checked. When exact category fit depends on legal
interpretation, say what facts support the category and what facts are
missing instead of presenting certainty.

## Legal Caveat

This skill is a drafting aid for licensed immigration attorneys and
their supervised staff. Visa eligibility is fact-specific and changes
over time. The attorney of record must verify all legal standards,
current government data, risk analysis, and recommended strategy before
advising a client.

## Completion Criteria

The visa brief is ready when client facts are explicit, plausible
categories are compared, official lookups were attempted for current
policy, availability, and timing claims, lookup failures are disclosed,
risks and evidence gaps are visible, and final strategy is framed for
attorney decision-making.
