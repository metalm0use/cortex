---
schema_version: 1
tags:
  - "legal"
  - "immigration"
  - "writing"
  - "casework"
topics:
  - "immigration case summaries"
  - "case history"
  - "USCIS case status"
  - "client intake"
status: seed
created: 2026-06-15
updated: 2026-06-15
sources:
  - "https://github.com/Gonzih/skills-immigration/blob/main/skills/case-summary/SKILL.md"
  - "https://egov.uscis.gov/"
  - "https://travel.state.gov/content/travel/en/us-visas/immigrate/nvc-timeframes.html"
source_count: 3
aliases:
  - "immigration case summary"
  - "case summary"
  - "case memo"
  - "matter summary"
  - "immigration history"
skill_id: legal/immigration-case-summary
summary: "Draft attorney-facing immigration case summaries from client facts, procedural history, status, risk flags, and next steps."
model_role: thinking
depends_on:
  - meta/contributing
related:
  - legal/immigration-client-letter
  - legal/immigration-rfe-response
  - legal/immigration-visa-brief
  - writing/humanizer
---

# Immigration Case Summary

<!-- learned: 2026-06 | project: cortex-skill-import | model: thinking-model -->

Use this skill when asked to summarize an immigration matter, prepare a
case overview, write a case memo, organize immigration history, or turn
intake notes, correspondence, or agency notices into an attorney-facing
case summary.

## Core Rule

Separate facts, verified public-status information, legal risks, and
attorney judgment. Attempt official-resource lookups for current status
or timeline claims when identifiers and access permit, then mark the
lookup result, source, and date. If a lookup cannot be completed, state
that plainly and do not fill the gap from memory.

## Workflow

1. Identify the client, case type, relief sought, current status, key
   dates, petitioner or employer, dependents, prior filings, denials,
   appeals, and any immigration court history.
2. Build a chronological procedural history: entries, status changes,
   filings, receipt notices, biometrics, interviews, Requests for
   Evidence (RFEs), Notices of Intent to Deny (NOIDs), decisions, appeals,
   hearings, and pending deadlines.
3. Attempt official lookups when useful and possible:
   - USCIS case status at `https://egov.uscis.gov/` when a receipt number
     is provided.
   - National Visa Center public timeframes at
     `https://travel.state.gov/content/travel/en/us-visas/immigrate/nvc-timeframes.html`
     when consular processing timing matters.
   - The State Department Visa Bulletin when priority-date availability
     affects the current status.
4. Summarize current status: pending filings, authorized stay or work
   authorization, travel permission, priority date posture, and known
   next agency action.
5. Flag legal issues for attorney review, including unlawful presence,
   status gaps, misrepresentation, criminal history, prior removal
   orders, inadmissibility or deportability grounds, and asylum or
   country-condition issues.
6. Produce specific next steps with deadlines. Mark legal strategy
   choices as `[ATTORNEY TO DECIDE]`.

## Output Shape

Use this structure unless the user asks for a different format:

1. Case Header: client, A-Number if known, case type, responsible
   attorney, date prepared.
2. Executive Summary: three to five sentences.
3. Client Profile: citizenship, status, petitioner, dependents, and
   immigration goals.
4. Procedural History: chronological timeline.
5. Current Status: pending items, authorizations, and verified lookups.
6. Legal Issues And Risk Flags: use `[CRITICAL]`, `[MONITOR]`, and
   `[NOTE]`.
7. Recommended Next Steps: prioritized action list.

## Lookup Caveats

Only use official sources for current case status, government queue
times, visa availability, and agency instructions. Do not rely on blogs,
third-party trackers, or stale examples for live legal facts.

When a lookup is attempted, include a compact note such as:

```text
Lookup: USCIS Case Status, receipt IOE..., checked 2026-06-15.
Result: [summarize exactly]. Caveat: attorney must verify before use.
```

If no receipt number, priority date, country of chargeability, or other
lookup input is available, list the missing input under next steps.

## Legal Caveat

This skill is a drafting aid for licensed immigration attorneys and
their supervised staff. The output is not legal advice, does not create
an attorney-client relationship, and must be reviewed by the attorney of
record for factual accuracy, legal correctness, and strategy.

## Completion Criteria

The case summary is ready when the timeline is coherent, facts are
distinguished from assumptions, official lookups were attempted where
current status or timing mattered, lookup failures are disclosed, risks
are severity-tagged, deadlines are visible, and legal judgment calls are
left for attorney review.
