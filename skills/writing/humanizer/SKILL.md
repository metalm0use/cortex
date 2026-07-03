---
schema_version: 1
tags:
  - "writing"
  - "editing"
  - "voice"
topics:
  - "human-facing prose"
  - "AI writing cleanup"
  - "voice calibration"
status: seed
created: 2026-06-04
updated: 2026-06-27
sources:
  - "https://github.com/blader/humanizer"
  - "https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing"
  - "user discussion 2026-06-04"
source_count: 3
aliases:
  - "humanizer"
  - "humanize writing"
  - "AI prose cleanup"
skill_id: writing/humanizer
summary: "Rewrite AI-shaped prose into clearer human-facing writing while preserving meaning, facts, and the author's intended voice."
model_role: thinking
depends_on:
  - meta/contributing
related:
  - collaboration/handoff
  - meta/skill-authoring
---

# Humanizer

<!-- learned: 2026-06 | project: cortex-bootstrap | model: thinking-model -->

Use this skill when editing human-facing prose that should feel clear,
natural, and authored by a person: READMEs, onboarding guides, project
updates, essays, handoffs for mixed human and agent audiences, emails,
and public documentation.

Do not use this skill to hide authorship, bypass disclosure rules, fake a
human writer, or launder unsourced claims. Use it to improve clarity,
specificity, rhythm, and reader comfort.

## Core Rule

Rewrite AI-shaped prose into clearer, more specific, author-appropriate
writing while preserving the original meaning, factual claims, required
structure, and level of certainty.

Agent-facing docs and human-facing docs need different treatment:

- Agent-facing docs, such as roadmaps, protocols, and handoffs, should
  stay compact, explicit, and easy to scan without filling the context
  window.
- Human-facing docs, such as READMEs and onboarding material, should keep
  that clarity while adding enough warmth and voice that readers feel
  comfortable adopting the workflow.

## Workflow

1. Identify the audience: human-facing, agent-facing, or mixed.
2. Ask for or inspect a writing sample when the user wants voice matching.
3. Scan for clusters of AI-shaped prose, not isolated tells.
4. Rewrite the text while preserving coverage. Do not drop facts merely
   because the phrasing is bad.
5. Audit the rewrite by asking what still sounds machine-shaped.
6. Revise once more, then return the final text and a brief change note
   when useful.

For long documents, work section by section. Do not paste a giant pattern
catalog into the response unless the user asks for a diagnosis.

## What To Fix

Look for clusters of these patterns:

- Inflated importance: "pivotal", "vital", "serves as a testament",
  "marks a shift", or claims that ordinary facts reflect broad trends.
- Promotional language: "vibrant", "rich", "breathtaking", "must-visit",
  "groundbreaking", "showcasing", or "nestled".
- Superficial present-participle analysis: sentences padded with
  "highlighting", "underscoring", "reflecting", "ensuring", or
  "contributing to".
- Vague sourcing: "experts say", "observers note", "industry reports",
  or paragraphs about missing information that turn into speculation.
- Formulaic structure: rule-of-three lists, generic "challenges and
  future outlook" sections, false "from X to Y" ranges, and upbeat
  conclusions with no concrete information.
- Chatbot residue: "Certainly", "Great question", "I hope this helps",
  "let me know", knowledge-cutoff disclaimers, and sycophantic praise.
- Overbuilt language: "delve", "intricate", "tapestry", "landscape",
  "underscore", "foster", "align with", "at its core", and "the real
  question is".
- Formatting tells: decorative bold labels, emoji bullets, title-case
  headings in ordinary docs, vertical lists where prose would be clearer,
  and curly quotes when the surrounding file uses straight quotes.
- Em and en dashes: heavy use is a strong tell. In final human-facing prose,
  prefer periods, commas, colons, or parentheses. A single deliberate dash is
  not proof of AI, so do not strip one that is doing real work.
- Copula avoidance: "serves as", "boasts", "features", "stands as" where a
  plain "is" or "has" reads better.
- Negative parallelism and tailing negations: "not just X but Y", "it's not
  about X, it's about Y", "no fluff, just results".
- Filler and hedging: "in order to", "due to the fact that", "it's worth noting
  that", "it's important to note", and stacked qualifiers like "could
  potentially".
- Signposting and self-announcement: "let's dive in", "in this section", "here's
  what you need to know", placed before the actual content.
- Persuasive-authority tropes and aphorism formulas: "the real question is",
  "what really matters", "X is the Y of Z", "X becomes a trap".
- Manufactured drama: runs of two- and three-word fragments for effect
  ("Simple. Fast. Done."), and conversational hooks used as openers
  ("Honestly?", "Look,", "Here's the thing").
- Diff-anchored writing: describing what changed ("now updated to", "no longer
  requires") instead of the thing as it currently is. A reader without the old
  version has no diff to anchor to.
- Fragmented headers: a heading immediately restated by a one-line sentence
  before any real content arrives.
- Hyphenation drift: hyphenate compound modifiers only before the noun
  ("high-quality report" vs. "the report is high quality").
- Rhythm problems: every sentence has similar length, every paragraph
  resolves too neatly, or the text has no point of view where a human
  author would naturally have one.

## Voice Calibration

When the user provides a sample, match it before applying generic taste:

- Sentence length and paragraph rhythm.
- Vocabulary level and favorite plain words.
- How the writer starts sections.
- Punctuation habits.
- Directness, uncertainty, humor, and aside frequency.
- How much personality the genre allows.

When no sample exists, use the document type as the voice boundary.
Technical reference text should stay plain. User-facing onboarding can be
warmer. Opinion writing can have more pulse.

## Preserve Human Signals

Do not flatten prose just because it is polished. Preserve:

- Specific details that would be hard to fabricate.
- Mixed feelings or unresolved tension.
- Defensible first-person choices.
- Natural repetition when the repeated term is clearer than synonym
  cycling.
- Short sentences, asides, and imperfect but intentional rhythm.
- Dated or era-bound references that would be costly to fabricate.

When a phrase is a false positive, leave it alone. None of these *alone* prove
AI-shaped writing:

- Perfect grammar, formal vocabulary, or a polished but bland passage.
- A single em dash, one formal transition, or one short punchy sentence.
- A letter-style opening, a common transition, or an unsourced claim.
- Correct, conventional formatting.

Treat tells as evidence only when they cluster.

## Agent-Facing Versus Human-Facing

For agent-facing docs, optimize for:

- Explicit state, dates, commands, and file paths.
- Short sections with stable headings.
- No atmospheric prose.
- No buried decisions.
- Enough context for a cold agent to act without re-reading the whole
  repository.

For human-facing docs, optimize for:

- A clear reason to care.
- Low-friction adoption language.
- Warm but direct prose.
- Concrete examples that make the workflow feel approachable.
- Honest tradeoffs, such as extra token usage for better continuity.

For mixed docs such as handoffs and roadmaps, let the agent-facing needs
win on structure and precision, then add human comfort only where it does
not slow scanning.

## Examples

AI-shaped:

```text
Cortex serves as a pivotal foundation for transforming modern agentic
workflows, showcasing a vibrant approach to durable knowledge capture.
```

Human-facing:

```text
Cortex gives agents a shared place to remember what the team has already
learned. It adds a small amount of context at the start of a session, and
it saves future sessions from rediscovering the same decisions.
```

Agent-facing:

```text
Cortex stores reusable agent knowledge as markdown skills in git. Before
work starts, read the generated index and the contribution protocol.
After reusable learning occurs, update or add a skill and run validation.
```

## Completion Criteria

The edit is done when:

- The rewrite preserves the original meaning and factual boundaries.
- The audience and document type are clear from the prose.
- AI-shaped pattern clusters have been removed or justified.
- Agent-facing sections are shorter and easier to scan.
- Human-facing sections feel direct, specific, and comfortable to read.
- No new facts, fake sources, or fake personal voice were invented.
