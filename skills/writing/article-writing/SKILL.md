---
schema_version: 1
tags:
  - "writing"
  - "articles"
  - "longform"
  - "voice"
  - "editing"
topics:
  - "article drafting"
  - "blog posts"
  - "long-form content"
  - "newsletter writing"
status: seed
created: 2026-06-07
updated: 2026-06-07
sources:
  - "https://github.com/affaan-m/ECC/blob/main/skills/article-writing/SKILL.md"
source_count: 1
aliases:
  - "article writing"
  - "blog post"
  - "longform writing"
  - "newsletter"
skill_id: writing/article-writing
summary: "Draft and revise long-form articles, guides, essays, tutorials, and newsletters with structure, evidence, and voice discipline."
model_role: thinking
depends_on:
  - meta/contributing
related:
  - writing/humanizer
  - collaboration/grill-me
  - meta/skill-authoring
---

# Article Writing

<!-- learned: 2026-06 | project: cortex-skill-import | model: thinking-model -->

Use this skill when drafting or substantially revising long-form human
writing: articles, blog posts, essays, guides, tutorials, launch posts,
newsletter issues, or polished prose built from notes, transcripts,
research, or examples.

Use `writing/humanizer` instead when the task is mainly to clean up
existing prose while preserving its meaning and structure. Use this skill
when the task needs a thesis, outline, section flow, evidence selection,
or a full draft.

## Core Rule

Lead with the concrete thing: example, artifact, output, observation,
number, code, screenshot, quote, or conflict. Explain after the reader
has something real to hold onto.

## Workflow

1. Identify the audience, purpose, intended medium, and desired reader
   action. If those are missing and cannot be inferred, ask briefly.
2. Gather the source material: notes, transcript, product details,
   research, screenshots, code, customer evidence, or voice samples.
3. Separate known facts from claims, opinions, and open questions. Do not
   invent customers, metrics, quotes, anecdotes, or research.
4. Build a hard outline with one job per section. Each section should
   introduce proof, conflict, example, explanation, or a decision.
5. Draft with the strongest concrete material early. Avoid throat
   clearing before the actual point.
6. Revise for structure first, then voice, then line-level polish.
7. Run the quality gate before delivery.

## Structure Patterns

For technical guides:

- Open with what the reader will be able to do or understand.
- Put code, commands, screenshots, outputs, or concrete examples in the
  major sections.
- Explain tradeoffs where a reader might otherwise cargo-cult the
  pattern.
- End with actionable next steps, not a vague recap.

For essays or opinion pieces:

- Start with a tension, contradiction, observation, or specific scene.
- Keep one argument thread per section.
- Make every strong opinion answer to evidence or lived reasoning.
- Let uncertainty stay visible where the facts are incomplete.

For launch posts:

- Put the product, feature, artifact, or change in the first screen.
- Show what is new through examples, screenshots, workflow changes, or
  before/after behavior.
- Name the audience and problem plainly.
- Keep roadmap promises distinct from shipped facts.

For newsletters:

- Make the first screen useful. Do not lead with diary filler.
- Use section labels only when they improve scanning.
- Keep links and recommendations tied to why the reader should care.
- Close with a useful pointer, not engagement bait.

## Voice Handling

If the user provides voice examples, extract a compact voice profile
before drafting:

- Sentence and paragraph rhythm.
- Favorite plain words and avoided words.
- How the writer opens and closes sections.
- Level of humor, directness, warmth, and skepticism.
- How the writer uses first person, uncertainty, and opinion.

If no voice reference exists, default to a concrete operator voice:
useful, unsentimental, specific, and comfortable saying what is not yet
known.

Do not fake personal experience, vulnerability, founder mythology, or
customer proof. When a draft needs those ingredients, leave a clear
placeholder or ask for the missing source.

## Banned Patterns

Delete or rewrite these patterns unless the source voice intentionally
uses them:

- Generic openings about a rapidly changing landscape.
- "Game-changer", "cutting-edge", "revolutionary", or similar empty
  importance words.
- "Here is why this matters" as a standalone bridge.
- Fake vulnerability arcs added for emotional shape.
- Biography padding that does not advance the argument.
- A closing question included only to drive engagement.
- Generic AI transitions that delay the point.
- Self-congratulatory descriptions of the piece or author.

## Drafting Checks

Ask these while revising:

- What concrete thing opens the piece?
- Does each section add a new job, or does it restate the previous one?
- Which claims need a source, example, or caveat?
- Which paragraph exists only because the outline expected a paragraph?
- Where is the reader being asked to trust adjectives instead of proof?
- Does the ending give the reader a usable next move?

## Relationship To Humanizer

This skill and `writing/humanizer` overlap at line editing, but they have
different jobs. Article writing owns topic framing, outline, evidence,
argument flow, and full-draft generation. Humanizer owns prose cleanup,
AI-shaped pattern removal, and voice-preserving rewrites of existing
text.

When doing both, use this skill first to create or restructure the piece,
then use `writing/humanizer` as the final pass.

## Completion Criteria

The piece is ready when the audience and purpose are clear, the opening
uses concrete material, every section has a distinct job, factual claims
are backed by supplied sources or marked as assumptions, the voice
matches the provided examples or agreed default, generic AI transitions
are gone, and the ending gives the reader a real takeaway or next action.
