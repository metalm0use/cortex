---
schema_version: 1
tags:
  - "meta"
  - "deployment"
topics:
  - "agent adapters"
  - "skill installation"
status: seed
created: 2026-05-31
updated: 2026-06-19
sources:
  - "user product rule 2026-06-05: first-party guided deployment paths for humans"
  - "frontend-slides offline vendoring 2026-06-05"
  - "offline validation feedback 2026-06-12: dry-run prompts, focused status, managed cleanup"
  - "milestone 7 2026-06-19: agents/ worker subagent emission for deep skills"
source_count: 4
aliases:
  - "skill deployment"
skill_id: meta/deployment
summary: "Deploy Cortex skills as managed native wrappers while preserving the vault as the source of truth."
model_role: execution
depends_on:
  - meta/contributing
  - meta/index
related:
  - meta/roles
  - meta/orchestration
  - meta/source-manifest
---

# Skill Deployment

<!-- learned: 2026-06 | project: cortex-bootstrap | model: thinking-model -->

Deploy Cortex skills into agent-native skill structures as generated
packages, not as relocated source files. The generated package gives the
target runtime first-party discovery through its native interface while
preserving the Cortex markdown file as the editable source of truth.

Deployment must remain portable across Windows and Linux. Codex and
Claude are the minimum supported native skill targets; other runtimes may
be supported as adapters, but they must not weaken Codex/Claude support
or require an operating-system-specific source format.

For runtimes that use `SKILL.md`, generate a native package directory
with a `SKILL.md` file. The package should include enough embedded skill
content to be immediately usable, plus a Cortex feedback section that
points back to the source skill, update protocol, log helper, and commit
pipeline. This avoids a thin pointer that is discoverable but not useful
when loaded cold.

Generated native packages must be task-first. Non-meta skills should use
task-shaped native names such as `pcap`, `humanizer`, `handoff`, or
`sql` when those names are unambiguous. Prefer the first source alias as
the native short name; fall back to the skill ID leaf when no alias is
present. If two skills want the same short name, use the scoped
`domain-skill` form. Keep meta packages prefixed as `cortex-meta-*` so
utility skills do not pollute the user's direct slash command space.

The frontmatter description and first body section should tell the agent
what the skill actually does, such as analyzing packet captures or
running a handoff. Include source aliases, topics, domain, leaf name, and
skill ID as first-class trigger hints in generated frontmatter, generated
descriptions, and a compact `Trigger Hints` section before the body.
Cortex provenance, script paths, and feedback instructions belong in a
compact footer. Do not make agents read a long Cortex preamble before
the operational skill instructions.

The footer should preserve the update loop with the fewest useful
commands: source path, vault root, index, contribution protocol,
validation command, log command, and commit helper. Do not include full
protocol prose in every generated package; link back to the meta skills
instead.

The Claude adapter also emits a `model:` line in generated wrapper
frontmatter when a skill's routing class maps to a model. The class is
the skill's `model_tier` when set, otherwise its `model_role`. The
class-to-model map is a team decision in the committed
`config/model-routing.json` file, with a built-in default when the file
is absent; it lives in the adapter, not in skill frontmatter. See
`meta/roles` for the map, valid values, and rationale. Claude Code honors
`model:` as a per-invocation override. Routing classes that inherit the
session model emit no line, and non-Claude targets omit it entirely.
Changing the map or a skill's routing class changes wrapper output, which
marks installed packages stale until the next sync.

Do not move Cortex skill files into runtime folders. Moving makes the
runtime folder the source of truth and breaks the vault's cross-agent
compounding behavior.

## Core Bundle

Every deployment must include the core meta bundle even when the user
selects only one category or one individual skill. The core bundle is all
`skills/meta/*/SKILL.md` skills plus the meta helper scripts under
`skills/meta/scripts/`.

The core bundle ensures every deployed runtime can:

- Find the skill graph through `skills/meta/index/SKILL.md`.
- Follow the update protocol in `skills/meta/contributing/SKILL.md`.
- Respect role hints from `skills/meta/roles/SKILL.md`.
- Run lint, manifest, index, doctor, log, and commit helpers.
- Feed improvements back into the Cortex repository.

## Category Selection

Installation should support selecting whole skill categories, such as
`collaboration`, `sql`, or `forensics`, as well as selecting individual
skills. Category selection is an install convenience only. It does not
change skill identity; skill IDs remain `domain/name`.

Use `all` when the user wants every skill. Use a category name when the
user wants a coherent capability family.

## Native Interfaces

Use the target runtime's native shape:

- `SKILL.md` package directories for runtimes that discover skills by
  `SKILL.md`, including Codex and Claude.
- Project rule files for runtimes that discover project instructions
  through rule folders.
- `AGENTS.md` as the fallback for any runtime that can read project
  instructions but has no native skill folder.

The native package is an adapter. It may contain embedded source content,
but edits still belong in Cortex.

For skills with companion resource directories, generated native
packages for `SKILL.md` runtimes need to carry those resources with
`SKILL.md`. Resource directories include `assets/`,
`references/`, `scripts/`, and `vendor/` under the skill's companion
directory. This is required for offline enterprise environments where a
deployed skill cannot fetch templates, scripts, screenshots, or example
assets from the internet.

For Cortex source skills, the source file is the skill folder's
`SKILL.md`, and the companion directory is the skill folder itself, such
as `skills/presentation/frontend-slides/` or `skills/forensics/pcap/`.

Treat skill-local `scripts/` and `references/` as first-party source
when the team writes them as part of the skill, even if they are added
after the initial skill commit. A helper such as
`skills/forensics/pcap/scripts/extract_flows.py` or
`skills/forensics/pcap/scripts/tshark_summary.sh` should deploy with the
pcap skill. The package can carry the script; it does not guarantee that
optional dependencies such as Scapy or external executables such as
`tshark` are installed on the target machine. The skill must document
those dependency assumptions and failure modes.

Directory-shaped runtimes receive the resource directories directly next
to `SKILL.md`. File-shaped runtimes such as project rule adapters receive
a managed sibling resource directory, for example
`<rule>.mdc.resources/`, with the same resource directory names inside.
Both shapes are generated artifacts; edit the Cortex source skill and
companion resources, then redeploy.

## Worker Subagents For Deep Skills

A deep skill that orchestrates multiple agents keeps its worker
definitions in an `agents/` folder beside `SKILL.md`. Unlike `assets/`,
`references/`, `scripts/`, and `vendor/`, `agents/` is not a copied
resource directory: each worker `*.md` is linted separately and compiled
into a native subagent for runtimes that support isolated subagents.

The Claude adapter is the first such target. For each worker it generates
one native subagent file in the Claude agents home (`~/.claude/agents/`
for global scope, `<project>/.cortex/claude/agents/` for project scope),
named `<orchestrator-install-name>__<worker>.md` so workers from different
orchestrators never collide. The generated subagent carries:

- a `model:` line from the worker's routing class (`model_tier`, else
  `model_role`) via the same `config/model-routing.json` map skills use;
- a `skills:` list mapped to deployed native names, plus a `## Skills`
  body pointer naming each referenced skill's invokable handle and source
  id. Skill bodies are never inlined; the worker reaches for the deployed
  skills.

Generated workers count toward package drift. A changed worker source, a
changed routing map, or an on-disk edit marks the orchestrator stale, and
`sync` regenerates the workers; `uninstall` removes them so no orphans
remain in the agents home. A pre-existing file that Cortex did not
generate is never overwritten. Non-Claude adapters deploy the orchestrator
skill only and degrade to running the worker roles sequentially. See
`meta/orchestration` for the loop contract and `meta/skill-authoring` for
authoring a deep skill plus its workers.

## Install Modes

Prefer `wrapper` mode. It writes a managed native package in the target
runtime folder and marks it with `.cortex-managed`.

Use `symlink` mode only when the local environment supports directory
symlinks reliably. The symlink should point to a generated native package
inside the Cortex repository, not directly to the rich Cortex markdown
file.

Use `copy` mode only as a compatibility fallback when symlinks are not
available and wrapper writes are acceptable.

Do not support a default `move` mode. Moving source files out of Cortex
breaks provenance, generated catalogs, and self-referential updates.

The vault remains the source of truth:

- Edit `skills/**/SKILL.md` in the Cortex repository.
- Run `skills/meta/scripts/lint_skill.py` against changed skills.
- Rebuild `skills/meta/index/SKILL.md` when skill metadata changes.
- Commit from the Cortex repository.
- Reinstall generated native packages after source changes.

Managed packages include a `.cortex-managed` marker. Deployment scripts
may overwrite packages with this marker, but must skip existing skill
folders without it. This prevents accidental replacement of native skills
that do not belong to Cortex.

When the generated native name for a skill changes, sync may remove older
Cortex-managed package directories for the same `source_skill_id` and
agent before writing the new target. This cleanup must only touch
artifacts with Cortex metadata and a `.cortex-managed` marker; unmanaged
folders are never migration targets.

## Install Status And Metadata

<!-- learned: 2026-06 | project: cortex-roadmap | model: execution-model -->

Generated native packages must carry machine-readable metadata so a user
can inspect install state without guessing. Package metadata records the
source skill ID, source path, source hash, generated timestamp, Cortex
commit, target agent, scope, install mode, install name, preferred
Python executable, target path, resource roots, and a per-file resource
manifest for companion assets.

Use `scripts/install-skills.py --action status` to inspect installed
state. Status output should classify selected skills as:

- `current`: installed metadata matches the current source skill hash and
  generator version.
- `stale`: installed metadata exists, but the source hash, skill ID, or
  generator version no longer matches, or required companion resources
  are missing from the installed package.
- `missing`: no generated package or rule exists at the target path.
- `unmanaged`: a target artifact exists without Cortex metadata.
- `unsupported`: the selected agent and scope combination has no known
  native target.

Use `--action sync` or `--action repair` to regenerate managed native
packages from the current Cortex source. Use `--action uninstall` only
for Cortex-managed artifacts; unmanaged native skills must be skipped.
All mutating actions must keep refusing to overwrite or remove unmarked
native packages.

## Deployment Impact Lifecycle

<!-- learned: 2026-06 | project: cortex-bootstrap | model: thinking-model -->

Treat deployed native packages as generated artifacts that can drift.
After changing a source skill, metadata field, package footer, wrapper
format, or installer behavior, check whether installed packages are
stale and update managed targets in the same session when possible.

Use this loop:

```bash
uv run cortex status --categories all --agents codex,claude --scope global
uv run cortex sync --categories all --agents codex,claude --scope global --yes
uv run cortex status --categories all --agents codex,claude --scope global
```

Use narrower `--skills`, `--categories`, `--agents`, or `--scope` values
when only a subset is relevant.

If the generated package shape, naming rule, or trigger metadata changes,
bump `GENERATOR_VERSION` in `scripts/install-skills.py`.
That intentionally marks older managed packages as `stale` so `sync` can
refresh them. If the session cannot write to the native target folders,
record the exact sync command in the handoff or log.

If companion resource copying or resource hashing changes, also bump
`GENERATOR_VERSION`. A package that has the current `SKILL.md` but is
missing required `vendor/`, `assets/`, `references/`, or `scripts/`
content is stale for offline use.

## Fresh Install Script Access

<!-- learned: 2026-06 | project: cortex-roadmap | model: execution-model -->

A freshly deployed native package must be able to tell the agent how to
run Cortex's Python helpers. Do not assume the command `python` exists on
every machine. Generated packages should include:

- The vault root path.
- The preferred Python executable captured when deployment ran.
- The exact command for `skills/meta/scripts/validate.py`.
- The exact command for `validate.py --fix-generated`.
- A fallback instruction to try `python3`, `python`, or `py` with the
  same script path when the preferred interpreter is unavailable.
- Pointers to validation, log entry, and skill commit helper scripts.

`AGENTS.md` remains a thin pointer into the vault. It does not need to
duplicate script commands because `skills/meta/contributing/SKILL.md` owns the
portable validation lifecycle. Native packages can include more explicit
runtime commands because they are generated for a concrete local
environment.

## Installer UX And Dependencies

<!-- learned: 2026-06 | project: cortex-roadmap | model: thinking-model -->

The installer should grow optional third-party dependencies when they make
deployment meaningfully easier for humans. Good candidates include Typer
for clearer command structure and Rich or prompt-tooling for selection
and status displays. These dependencies are acceptable only for optional
deployment ergonomics, not for the core validation contract.

If optional dependencies are introduced:

- Declare them in `pyproject.toml`.
- Prefer `uv sync` as the enhanced install path.
- Expose the enhanced package as a `cortex` console command.
- Prefer subcommands such as `install`, `status`, `sync`, `repair`, and
  `uninstall` over an action flag in the enhanced CLI.
- Keep scripted noninteractive installer flags available for agents and
  automation.
- Keep `skills/meta/scripts/validate.py` and core health scripts
  standard-library only.
- Document the fallback path for users who do not install optional
  dependencies.
- Delegate enhanced commands to the stdlib backend unless there is a
  concrete reason to duplicate behavior.
- Keep saved profiles as local preferences, not vault source. Profiles
  may live under an ignored path such as `.cortex/profiles/`, and every
  profile-backed action must still be expressible through flags.
- Support explicit shared profile files for team-repeatable deployment
  choices. A shared profile should be a small JSON file committed under a
  normal repo path such as `profiles/`, passed with `--profile-file`, and
  reviewed like source. Keep machine-local paths out of shared profiles
  unless the team intentionally wants an environment-specific file.
- Default guided install flows to dry-run so first-run setup previews
  writes before touching native agent folders.
- After a guided dry-run preview, the enhanced CLI must return to the
  human flow and explicitly ask whether to apply the same selection. Do
  not route preview execution through helper code that exits the command
  before the apply prompt can run.
- Status commands should be quiet by default: hide missing packages
  unless the user asks for them, and expose simple target filters such as
  Codex-only or Claude-only checks. Missing-package noise makes normal
  offline validation harder to read when the user only cares about one
  installed runtime.
- Provide a cleanup helper that removes only Cortex-managed native
  packages. Cleanup must default to dry-run, prompt before deleting, and
  refuse unmanaged local skills.
- First-party the happy human path. Humans should normally use guided
  personal setup such as `uv run cortex first-run` or team profile
  commands such as `uv run cortex team status` and
  `uv run cortex team finish`. The enhanced CLI should hide long flag
  combinations behind prompts, profiles, status tables, and preview
  confirmations.
- Keep explicit flags and stdlib commands as the transparent contract for
  scripts, agents, debugging, and environments without optional
  dependencies. Human-facing docs may show those forms behind Markdown
  `<details>` blocks or in `docs/CLI_REFERENCE.md`, but the visible
  onboarding path should not require a reader to compose flag-heavy
  commands.

Do not add dependencies just for polish. Add them when they reduce
operator error, make multi-agent/category selection clearer, or make
status/sync/repair output easier to act on.

Fallback contract:

- Core health scripts are Tier 0 and must remain stdlib-only.
- The existing stdlib installer path is Tier 1 and must remain runnable
  for fresh clones, agents, and automation.
- The enhanced `uv`/Typer/Rich-style app is Tier 2 and may improve human
  ergonomics, but it must call or preserve the same underlying install,
  status, sync, repair, and uninstall behavior.
- Every interactive command must also be fully inputable through flags or
  an input file. Do not create wizard-only workflows.

Current enhanced path:

```bash
uv sync
uv run cortex --help
uv run cortex about
uv run cortex validate --fix-generated
uv run cortex first-run
uv run cortex team status
uv run cortex team finish
uv run cortex completion powershell
uv run cortex completion bash
uv run cortex completion zsh
```

Explicit equivalent examples belong in CLI reference docs, scripted
automation, or troubleshooting notes:

```bash
uv run cortex status --profile-file profiles/team-codex-claude.json
python scripts/install-skills.py --action status --profile-file profiles/team-codex-claude.json
```

The enhanced CLI is a wrapper over the portable scripts. `cortex about`
may include a vanity ASCII banner because it is opt-in and not part of
machine-readable validation or deployment output. `cortex status` may
render a Rich table for humans and should keep a raw-output option for
automation or troubleshooting. If `uv`, Typer, or Rich are unavailable,
use `python skills/meta/scripts/validate.py` and
`python scripts/install-skills.py` directly. Run enhanced commands from
the repository root, or set `CORTEX_ROOT` to the vault root when invoking
the package from another directory.

Shell completion is optional operator ergonomics, not part of the core
validation contract. The enhanced CLI should expose first-party
completion help for PowerShell, bash, and zsh so contributors can enable
completion without copying maintainer-specific shell profile blocks.

## Feedback Path

Every generated native package should tell the runtime how to feed back:

- Improve the Cortex source file, not the generated package.
- Run the Cortex lint, manifest, index, and doctor pipeline.
- Use `skills/meta/scripts/log_entry.py` for lightweight observations
  that do not yet justify a skill edit.
- Use `skills/meta/scripts/commit_skill.py` when committing a skill
  update.
- Reinstall generated native packages after the source commit.

If the runtime can read the package but cannot edit the Cortex repository,
it should produce a concrete proposed change for a user or another agent
with repository write access.

Use the interactive installer when choosing categories, skills, agents,
scope, or install mode:

```bash
python scripts/install-skills.py
```

Scripted examples:

```bash
python scripts/install-skills.py --categories collaboration --agents codex,claude --scope global --yes
python scripts/install-skills.py --skills collaboration/handoff --agents cursor --scope project --yes
python scripts/install-skills.py --categories all --agents all --scope project --dry-run --yes
python scripts/install-skills.py --action status --skills collaboration/handoff --agents all --scope project
python scripts/install-skills.py --action sync --categories collaboration --agents codex,claude --scope global --yes
python scripts/install-skills.py --action uninstall --skills collaboration/handoff --agents cursor --scope project --yes
```

Use the platform deploy script when a simple deploy-all wrapper workflow
is enough:

```bash
scripts/deploy-skills.sh --agent auto
```

```powershell
scripts/deploy-skills.ps1 -Agent auto
```

`auto` detects known local agent homes. Use an explicit agent or target
directory when auto-detection cannot infer the runtime:

```bash
scripts/deploy-skills.sh --agent codex
scripts/deploy-skills.sh --agent claude
scripts/deploy-skills.sh --target /path/to/native/skills
```

```powershell
scripts/deploy-skills.ps1 -Agent codex
scripts/deploy-skills.ps1 -Agent claude
scripts/deploy-skills.ps1 -Target C:\path\to\native\skills
```

If a runtime cannot use native skill folders, keep `AGENTS.md` as the
fallback integration point. The two-line pointer is enough for any
agent that can read project instructions.
