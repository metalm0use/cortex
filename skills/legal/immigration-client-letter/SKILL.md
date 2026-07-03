---
schema_version: 1
tags:
  - "legal"
  - "immigration"
  - "writing"
  - "client-communication"
topics:
  - "client letters"
  - "immigration status updates"
  - "USCIS notices"
  - "plain-language legal writing"
status: seed
created: 2026-06-15
updated: 2026-06-15
sources:
  - "https://github.com/Gonzih/skills-immigration/blob/main/skills/client-letter/SKILL.md"
  - "https://www.uscis.gov/forms/all-forms"
  - "https://travel.state.gov/content/travel/en/us-visas.html"
  - "https://i94.cbp.dhs.gov/"
source_count: 4
aliases:
  - "immigration client letter"
  - "client letter"
  - "client update"
  - "status letter"
  - "case update"
skill_id: legal/immigration-client-letter
summary: "Draft plain-language immigration client letters and emails that explain case developments, next steps, and deadlines."
model_role: thinking
depends_on:
  - meta/contributing
related:
  - legal/immigration-case-summary
  - legal/immigration-rfe-response
  - legal/immigration-visa-brief
  - writing/humanizer
---

# Immigration Client Letter

<!-- learned: 2026-06 | project: cortex-skill-import | model: thinking-model -->

Use this skill when asked to write a client update letter, status letter,
case update email, or plain-language communication about an immigration
case development such as a Request for Evidence (RFE), interview notice,
approval, denial, transfer notice, biometrics appointment, consular step,
or administrative processing update.

## Core Rule

Write for the client, not the agency. Explain what happened, what it
means, what the client must do, what the office will do, and what not to
do. Attempt official-resource lookups before stating current forms,
document requirements, travel-record facts, appointment requirements, or
time-sensitive government instructions.

## Workflow

1. Collect the client name, preferred salutation, case type, case
   development, deadline, client actions needed, attorney or firm
   signature, and whether the output should be a formal letter, email, or
   both.
2. Translate the development into plain English. Avoid unexplained form
   numbers, citations, acronyms, and passive phrasing.
3. Attempt official lookups when the communication depends on current
   public information:
   - USCIS form instructions and filing requirements at
     `https://www.uscis.gov/forms/all-forms`.
   - State Department visa and embassy information at
     `https://travel.state.gov/content/travel/en/us-visas.html`.
   - CBP I-94 travel history at `https://i94.cbp.dhs.gov/` only when the
     client can access or provide the record; do not imply the agent can
     retrieve private travel data without client participation.
4. Include a clear "What Happens Next" section with client tasks,
   office tasks, dates, and expected timing.
5. Include a "Please Do Not" section when there are meaningful risk
   behaviors, such as travel, contacting USCIS directly, changing
   employment, missing appointments, or ignoring agency mail.
6. Close with a reassuring but accurate statement and a direct contact
   path.

## Output Shape

For most requests, provide:

1. Formal Letter Version with letterhead placeholder, date, salutation,
   subject line, body, deadline section, next steps, and signature block.
2. Email Version with a subject line, warmer tone, concise action list,
   and signature.

If the user only asks for one medium, produce that medium and do not add
an unwanted second version.

## Lookup Caveats

When an official lookup affects the letter, mention it briefly in an
attorney note rather than burdening the client with research mechanics:

```text
Attorney note: USCIS form instructions checked 2026-06-15. Confirm before
sending because agency instructions and fees can change.
```

If lookup is unavailable, write the client-facing letter with a bracketed
attorney placeholder such as `[ATTORNEY TO CONFIRM CURRENT DEADLINE]`.

## Legal Caveat

This skill drafts communications for attorney review. The attorney of
record must verify legal advice, deadlines, eligibility statements,
current agency instructions, and tone before sending anything to a
client.

## Completion Criteria

The communication is ready when it is client-readable, names the case
development, gives concrete next steps and deadlines, attempts official
lookups for current requirements, marks any unverified legal facts for
attorney confirmation, and avoids promising outcomes.
