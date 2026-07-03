---
schema_version: 1
tags:
  - "legal"
  - "immigration"
  - "writing"
  - "evidence"
topics:
  - "RFE responses"
  - "RFIE responses"
  - "USCIS requests for evidence"
  - "immigration briefs"
  - "exhibit lists"
status: seed
created: 2026-06-15
updated: 2026-06-15
sources:
  - "https://github.com/Gonzih/skills-immigration/blob/main/skills/rfie-response/SKILL.md"
  - "https://www.uscis.gov/policy-manual"
  - "https://www.uscis.gov/laws-and-policy/other-resources/administrative-appeals/aao-decisions"
source_count: 3
aliases:
  - "immigration rfe response"
  - "RFE response"
  - "RFIE response"
  - "request for evidence"
  - "RFE brief"
  - "NOID response"
skill_id: legal/immigration-rfe-response
summary: "Draft USCIS RFE, RFIE, and NOID response frameworks with issue maps, attorney briefs, exhibit lists, and evidence gaps."
model_role: thinking
depends_on:
  - meta/contributing
related:
  - legal/immigration-case-summary
  - legal/immigration-client-letter
  - legal/immigration-visa-brief
  - writing/article-writing
---

# Immigration RFE Response

<!-- learned: 2026-06 | project: cortex-skill-import | model: thinking-model -->

Use this skill when asked to respond to a USCIS Request for Evidence
(RFE), Request for Further Evidence (RFIE), Notice of Intent to Deny
(NOID), or similar immigration evidence request. The output should help
an attorney organize issues, arguments, evidence, and filing tasks.

## Core Rule

Treat the agency notice as the controlling input. Address every issue it
raises, map each argument to evidence, attempt official-source lookup for
legal standards or agency guidance, and mark all citations, deadlines,
and legal conclusions for attorney verification.

## Workflow

1. Parse the notice. Identify receipt number, petitioner or applicant,
   benefit type, notice date, response deadline, filing address or upload
   channel, and every issue raised.
2. Create an issue map. For each issue, capture the agency concern,
   category, applicable standard, proposed response, evidence on hand,
   and evidence still needed.
3. Attempt official legal-source lookups before stating current agency
   standards or relying on authority:
   - USCIS Policy Manual at `https://www.uscis.gov/policy-manual`.
   - AAO decisions at
     `https://www.uscis.gov/laws-and-policy/other-resources/administrative-appeals/aao-decisions`.
   - Current USCIS form or filing instructions when the response package
     depends on them.
4. Draft the response brief in the notice's order. Use respectful,
   precise language: state the concern, legal standard, facts, evidence,
   and requested outcome.
5. Build an exhibit list that matches the brief. Include exhibit labels,
   descriptions, what each item proves, status, and page count when
   known.
6. Identify expert-letter needs when the issue involves specialty
   occupation, extraordinary ability, exceptional ability, national
   interest, business necessity, technical complexity, or other facts
   needing independent support.
7. End with a filing checklist. Mark missing items as `[TO OBTAIN]`,
   legal authority as `[ATTORNEY TO VERIFY]`, and strategic choices as
   `[ATTORNEY TO DECIDE]`.

## Output Shape

Use these sections unless the user asks for a narrower artifact:

1. Issue Map table.
2. Response Strategy summary.
3. Draft Attorney Brief or cover letter.
4. Exhibit List.
5. Expert Letter Guidance, if needed.
6. Filing Checklist with missing items and verification points.

## Lookup Caveats

Do not invent citations, precedent holdings, filing addresses, or
deadline calculations. If an official lookup is unavailable, write a
placeholder instead:

```text
[ATTORNEY TO VERIFY] Current USCIS Policy Manual section and any binding
or persuasive authority for this issue.
```

When quoting the agency notice, quote only the relevant excerpts the user
provided. If the full RFE is not available, state that the issue map is
partial.

## Legal Caveat

This skill is a drafting and organization aid for licensed immigration
attorneys and supervised staff. The attorney of record must verify all
facts, exhibits, citations, deadlines, legal standards, and filing
instructions before submission.

## Completion Criteria

The response framework is ready when every known RFE/RFIE/NOID issue is
mapped, each argument points to evidence, official-source lookups were
attempted for legal standards or instructions, missing evidence is
explicit, citations and deadlines are flagged for attorney verification,
and the exhibit list aligns with the draft brief.
