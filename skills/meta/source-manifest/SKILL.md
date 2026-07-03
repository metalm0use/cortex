---
schema_version: 1
tags:
  - "meta"
  - "manifest"
topics:
  - "source catalog"
status: seed
created: 2026-05-31
updated: 2026-06-27
sources: []
source_count: 0
aliases:
  - "source manifest"
skill_id: meta/source-manifest
summary: "Generated manifest of vault notes, scripts, root files, logs, and basic counts."
model_role: reference
depends_on:
  - "meta/contributing"
related:
  - "meta/index"
---

# Source Manifest

<!-- learned: 2026-06 | project: cortex-bootstrap | model: manifest-builder -->

Generated from repository files. Do not hand-edit counts or tables;
rerun `skills/meta/scripts/manifest_builder.py`.

## Counts

- Skill notes: 27
- Script files: 20
- Root files: 5
- Log markdown files: 3

## Domains

- `collaboration`: 2
- `devops`: 2
- `forensics`: 2
- `legal`: 4
- `meta`: 8
- `presentation`: 1
- `programming`: 1
- `prompting`: 2
- `security`: 1
- `sql`: 2
- `writing`: 2

## Statuses

- `active`: 1
- `seed`: 26

## Model Roles

- `execution`: 1
- `reference`: 10
- `thinking`: 16

## Review Statuses

- `human-noted`: 2
- `unreviewed`: 25

## Skill Notes

| Path | Skill ID | Status | Model Role | Review | Summary |
| --- | --- | --- | --- | --- | --- |
| `skills/collaboration/grill-me/SKILL.md` | `collaboration/grill-me` | seed | thinking | unreviewed / - | Interview the user one question at a time, starting low fidelity, to stress-test a plan until the design tree is resolved. |
| `skills/collaboration/handoff/SKILL.md` | `collaboration/handoff` | seed | thinking | unreviewed / - | Write a redacted project handoff so a fresh agent or developer can continue without duplicating existing artifacts. |
| `skills/devops/docker-patterns/SKILL.md` | `devops/docker-patterns` | seed | reference | human-noted / low | Apply Docker and Docker Compose patterns for local development, service wiring, volumes, and container hardening. |
| `skills/devops/redis-patterns/SKILL.md` | `devops/redis-patterns` | seed | reference | unreviewed / - | Apply Redis patterns for caching, rate limiting, locks, sessions, messaging, and production connection management. |
| `skills/forensics/ja4/SKILL.md` | `forensics/ja4` | seed | reference | unreviewed / - | Interpret JA4-family network fingerprints and avoid common implementation mistakes when working from packet captures or logs. |
| `skills/forensics/pcap/SKILL.md` | `forensics/pcap` | seed | reference | unreviewed / - | Preserve original packet captures and analyze derived copies for network-forensics artifacts, anomalies, and evidence. |
| `skills/legal/immigration-case-summary/SKILL.md` | `legal/immigration-case-summary` | seed | thinking | unreviewed / - | Draft attorney-facing immigration case summaries from client facts, procedural history, status, risk flags, and next steps. |
| `skills/legal/immigration-client-letter/SKILL.md` | `legal/immigration-client-letter` | seed | thinking | unreviewed / - | Draft plain-language immigration client letters and emails that explain case developments, next steps, and deadlines. |
| `skills/legal/immigration-rfe-response/SKILL.md` | `legal/immigration-rfe-response` | seed | thinking | unreviewed / - | Draft USCIS RFE, RFIE, and NOID response frameworks with issue maps, attorney briefs, exhibit lists, and evidence gaps. |
| `skills/legal/immigration-visa-brief/SKILL.md` | `legal/immigration-visa-brief` | seed | thinking | unreviewed / - | Draft immigration visa option and strategy briefs that compare candidate categories, risks, timelines, and next steps. |
| `skills/meta/conflicts/SKILL.md` | `meta/conflicts` | seed | thinking | unreviewed / - | Append-only log for unresolved contradictions found while updating vault skills. |
| `skills/meta/contributing/SKILL.md` | `meta/contributing` | active | thinking | human-noted / high | Protocol for deciding what belongs in the vault, how to update it, and how model roles are separated. |
| `skills/meta/deployment/SKILL.md` | `meta/deployment` | seed | execution | unreviewed / - | Deploy Cortex skills as managed native wrappers while preserving the vault as the source of truth. |
| `skills/meta/index/SKILL.md` | `meta/index` | seed | reference | unreviewed / - | Generated map of vault skills, domains, summaries, and relationships. |
| `skills/meta/orchestration/SKILL.md` | `meta/orchestration` | seed | thinking | unreviewed / - | Coordinate a boss agent that spawns specialized worker subagents and loops them until explicit completion criteria are met. |
| `skills/meta/roles/SKILL.md` | `meta/roles` | seed | thinking | unreviewed / - | Defines the strict split between thinking models that decide and execution models that format, lint, and commit. |
| `skills/meta/skill-authoring/SKILL.md` | `meta/skill-authoring` | seed | thinking | unreviewed / - | Draft Cortex skills after contribution triage, using concise triggers, concrete workflows, and deterministic resources. |
| `skills/meta/source-manifest/SKILL.md` | `meta/source-manifest` | seed | reference | unreviewed / - | Generated manifest of vault notes, scripts, root files, logs, and basic counts. |
| `skills/presentation/frontend-slides/SKILL.md` | `presentation/frontend-slides` | seed | thinking | unreviewed / - | Create polished offline-capable HTML slide decks from a brief, existing content, or PowerPoint source using vendored frontend slide templates. |
| `skills/programming/python-patterns/SKILL.md` | `programming/python-patterns` | seed | reference | unreviewed / - | Apply idiomatic Python patterns for readable code, type hints, error handling, package layout, tooling, and performance. |
| `skills/prompting/optimize/SKILL.md` | `prompting/optimize` | seed | thinking | unreviewed / - | Orchestrate a critic, rewriter, and evaluator to turn a draft prompt into a measurably stronger one against a fixed checklist and rubric. |
| `skills/prompting/patterns/SKILL.md` | `prompting/patterns` | seed | reference | unreviewed / - | Build and score effective prompts from a fixed component checklist, a pattern catalog, and an anchored quality rubric. |
| `skills/security/review/SKILL.md` | `security/review` | seed | thinking | unreviewed / - | Orchestrate a network-security review: a research worker analyzes the evidence and a report worker writes the findings, looped until complete. |
| `skills/sql/injection/SKILL.md` | `sql/injection` | seed | reference | unreviewed / - | Use parameterized SQL query patterns and avoid string-built query text for untrusted values. |
| `skills/sql/postgres-patterns/SKILL.md` | `sql/postgres-patterns` | seed | reference | unreviewed / - | Apply PostgreSQL patterns for schema design, indexes, query optimization, RLS, connection safety, and operational diagnostics. |
| `skills/writing/article-writing/SKILL.md` | `writing/article-writing` | seed | thinking | unreviewed / - | Draft and revise long-form articles, guides, essays, tutorials, and newsletters with structure, evidence, and voice discipline. |
| `skills/writing/humanizer/SKILL.md` | `writing/humanizer` | seed | thinking | unreviewed / - | Rewrite AI-shaped prose into clearer human-facing writing while preserving meaning, facts, and the author's intended voice. |

## Scripts

- `.githooks/pre-commit`
- `scripts/deploy-skills.ps1`
- `scripts/deploy-skills.sh`
- `scripts/install-skills.py`
- `skills/meta/scripts/capture_expertise.py`
- `skills/meta/scripts/commit_skill.py`
- `skills/meta/scripts/docs_smoke.py`
- `skills/meta/scripts/doctor.py`
- `skills/meta/scripts/index_builder.py`
- `skills/meta/scripts/install_hooks.py`
- `skills/meta/scripts/lint_skill.py`
- `skills/meta/scripts/log_entry.py`
- `skills/meta/scripts/manifest_builder.py`
- `skills/meta/scripts/skill_brief.py`
- `skills/meta/scripts/validate.py`
- `skills/presentation/frontend-slides/scripts/vendor_google_fonts.py`
- `skills/prompting/patterns/scripts/intent_router.py`
- `skills/prompting/patterns/scripts/prompt_lint.py`
- `src/cortex_cli/__init__.py`
- `src/cortex_cli/main.py`

## Root Files

- `README.md`
- `AGENTS.md`
- `.gitignore`
- `pyproject.toml`
- `uv.lock`

## Logs

- `logs/2026-05.md`
- `logs/2026-06.md`
- `logs/README.md`
