---
schema_version: 1
tags:
  - "security"
  - "orchestration"
topics:
  - "security review"
  - "network forensics review"
status: seed
created: 2026-06-19
updated: 2026-06-19
sources: []
source_count: 0
aliases:
  - "security-review"
  - "security review"
  - "deep security review"
skill_id: security/review
summary: "Orchestrate a network-security review: a research worker analyzes the evidence and a report worker writes the findings, looped until complete."
model_role: thinking
depends_on:
  - meta/orchestration
related:
  - meta/orchestration
  - forensics/pcap
  - forensics/ja4
  - writing/article-writing
---

# Deep Security Review

<!-- learned: 2026-06 | project: cortex-milestone-7 | model: thinking-model -->

Use this skill when the user wants a network-security review of captured
evidence (packet captures, flow logs, TLS fingerprints) turned into a
written findings report. It is a deep skill: it coordinates two
specialized workers rather than doing the analysis and the writing in one
context.

This skill is the reference orchestrator. It demonstrates the
`meta/orchestration` loop with real workers defined in `agents/` beside
this file. Read `meta/orchestration` for the loop contract; this skill
only fills in the goal, the workers, and what "done" means.

## Core Rule

Coordinate; do not do the workers' jobs in this context. Spawn the
research worker to analyze the evidence, spawn the report worker to turn
confirmed findings into a report, evaluate each result against its
completion criteria, and re-dispatch unfinished work until done or a stop
bound is hit.

## Workers

Two workers live in `agents/` beside this skill:

- `researcher` (judgment-heavy, strong model): analyzes the evidence using
  `/pcap` and `/ja4` and returns confirmed findings with supporting
  detail. One scoped task: produce the findings list.
- `reporter` (assembly, fast model): turns the confirmed findings into a
  structured report using `/article-writing`. One scoped task: produce the
  report from the findings the boss passes in.

The two workers run on different model tiers on purpose: the researcher
needs reasoning depth, the reporter assembles already-confirmed findings
into prose. This is the routing diversity `meta/roles` describes.

## Workflow

1. Decompose the request into a research task and a reporting task. State
   each task's completion criteria up front.
2. Spawn `researcher` with the evidence paths and the question to answer.
   Completion criteria: a findings list where each finding names the
   evidence, the observation, and the assessed risk.
3. Evaluate the findings. Re-dispatch with corrective guidance if a
   finding lacks evidence or an assessment, or if a stated scope item was
   not covered.
4. Spawn `reporter` with the confirmed findings. Completion criteria: a
   report with a summary, per-finding sections, and recommended actions,
   written without inventing findings the researcher did not provide.
5. Evaluate the report against its criteria. Re-dispatch once with
   corrective guidance if it adds unsupported claims or drops findings.
6. Stop when both criteria are met or the round bound is hit. Aggregate
   the report and note any scope item the research could not resolve.

## Stop Conditions

- Done-signal: the findings list and the report both meet their criteria.
- Max rounds: cap re-dispatch at 3 per worker so a stuck worker cannot
  loop forever.
- Failure: if a finding cannot be resolved within its rounds, record the
  gap in the report rather than looping silently.

## Degradation

On a runtime without isolated subagents, run the two roles sequentially in
this context: first the research role using `/pcap` and `/ja4`, then the
reporting role using `/article-writing`. The loop contract and completion
criteria are unchanged; the work is simply less parallel.

## Completion Criteria

The review is complete when the findings list is evidence-backed and
assessed, the report covers every confirmed finding with recommended
actions and adds no unsupported claims, and any unresolved scope item is
named explicitly instead of dropped.
