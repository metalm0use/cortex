# Cortex

Cortex is a shared skill vault for AI agents.

Agents are useful, but they forget the shape of a team between sessions.
They rediscover the same decisions, miss the same caveats, and need the
same context pasted back in. Cortex gives that reusable knowledge a
simple home: markdown files in git.

When an agent learns something genuinely useful during a project, Cortex
turns it into a skill that future agents can read before they start. The
workflow is small on purpose. Keep your current agent tools, keep normal
git, and add a compact context layer that the team can inspect, edit,
validate, and version.

The tradeoff is a little extra token usage at the start of a session.
The gain is continuity. A fresh agent can inherit project habits,
hard-won fixes, handoff notes, and domain caveats without anyone
rebuilding the whole story from chat history.

There is no vector database, hidden memory service, or vendor-specific
format.

Use Cortex when you want:

- Reusable technical knowledge to compound across sessions.
- Project handoffs that another person or agent can actually continue.
- Agent skills that stay first-party and editable in your own repo.
- A local validation pipeline that works without hosted CI.

Cortex is intended to work on Windows and Linux. Codex and Claude are the
minimum supported native skill targets; other runtimes can be added as
adapters without changing the vault source format.

## Current Status

Cortex is locally production-ready for this maintainer environment:

- The portable validation contract passes.
- Global Codex and Claude native packages report `current`.
- Local runtime artifacts, Obsidian workspace state, and Smart
  Environment data are ignored.

Team rollout is the next step. Before asking teammates to depend on
Cortex, walk through [docs/FIRST_10_MINUTES.md](docs/FIRST_10_MINUTES.md)
with a fresh-clone mindset and check
[docs/TEAM_ROLLOUT.md](docs/TEAM_ROLLOUT.md) against the first real
project or teammate audience.

## Start Here

Pick the path that matches the job:

- New to Cortex: read [docs/FIRST_10_MINUTES.md](docs/FIRST_10_MINUTES.md).
- Rolling Cortex out to a team: read
  [docs/TEAM_ROLLOUT.md](docs/TEAM_ROLLOUT.md).
- Understanding commands and flags: read
  [docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md).
- Continuing development: read [docs/HANDOFF.md](docs/HANDOFF.md), then
  [docs/ROADMAP.md](docs/ROADMAP.md).
- Updating vault knowledge: start with
  [skills/meta/contributing/SKILL.md](skills/meta/contributing/SKILL.md).

> **The daily command.** After you commit a skill or deployment change,
> run `uv run cortex team finish` (or `uv run cortex finish` for your own
> selection). It is the one command that both validates the vault with
> `--fix-generated` and installs the changed skills into your native agent
> packages. It previews drift and asks before writing.

## Quick Start

From a fresh clone:

```bash
git clone git@github.com:[redacted-repo]/cortex.git
cd cortex
python --version
python skills/meta/scripts/validate.py
```

That is the smallest path. It uses only Python's standard library and
checks that the vault is healthy.

For the nicer terminal app, install `uv` and sync the optional
dependencies:

```bash
python -m pip install --user uv
uv sync
uv run cortex about
uv run cortex validate --fix-generated
```

If `uv` is installed but your shell cannot find it, restart the terminal
or add your Python Scripts directory to `PATH`. On this Windows setup the
important user paths are:

```text
%LOCALAPPDATA%\Python\bin
%APPDATA%\Python\Python314\Scripts
```

The committed [uv.lock](uv.lock) pins the optional CLI dependency set.
The core validation path does not need `uv`, Typer, or Rich.

For the shortest end-to-end path, follow
[docs/FIRST_10_MINUTES.md](docs/FIRST_10_MINUTES.md). It walks through
clone, validation, optional `uv`, skill install, `AGENTS.md`, expertise
capture, validation, commit, and wrapper sync.

## Guided Setup

The enhanced CLI has a first-run wizard for humans. It uses checkbox
multi-select for categories, skills, and target agents, then radio-style
selection for scope and install mode.

There are three command lanes:

- Use `uv run cortex first-run` when you are setting up your own machine
  and want the CLI to ask the questions.
- Use `uv run cortex team ...` when the team has agreed on the committed
  profile in `profiles/team-codex-claude.json`.
- Use explicit flags or the stdlib script when you are writing docs,
  debugging, automating, or asking an agent to do the work.

The lanes can be combined. A teammate can use `first-run` to learn the
choices, then use `team status` and `team finish` to align with the
shared profile. If no shared profile exists yet, save a local profile and
propose a committed profile under `profiles/` through normal review.

Preview a guided install:

```bash
uv run cortex first-run
```

The wizard can save your choices as a local profile, save a shared
profile file, preview the install, and then apply the same selection when
you approve it.

Profiles live under `.cortex/profiles/` and are ignored by git. They are
local preferences, not vault source. Every profile-backed command also
has equivalent flags, so agents and scripts can run without the
interactive wizard.

For team-repeatable deployment choices, use a committed JSON profile
instead of a local profile:

```bash
uv run cortex team profile
uv run cortex team status
uv run cortex team finish
```

Shared profiles should not contain machine-local project paths unless the
team intentionally wants that file to be environment-specific.

Most humans should use the short `team` commands. The longer
`--profile-file` form is there so the exact inputs are visible when a
script, agent, or troubleshooting note needs them.

<details>
<summary>Explicit profile commands</summary>

```bash
uv run cortex first-run --save-profile daily
uv run cortex first-run --no-dry-run --save-profile daily
uv run cortex profile save daily --categories collaboration --agents codex,claude --scope global
uv run cortex profile list
uv run cortex profile show daily
uv run cortex status --profile daily
uv run cortex sync --profile daily --yes
uv run cortex finish --profile daily --no-dry-run --yes
uv run cortex profile validate-file profiles/team-codex-claude.json
uv run cortex status --profile-file profiles/team-codex-claude.json
uv run cortex finish --profile-file profiles/team-codex-claude.json
uv run cortex finish --profile-file profiles/team-codex-claude.json --no-dry-run --yes
```

</details>

## Install Skills Into Agents

Cortex source files stay in this repo. Deployment creates managed native
packages for tools like Codex and Claude, with Cursor also supported as
a project-rule adapter.

For normal team setup, use the team lane:

```bash
uv run cortex team status
uv run cortex team finish
```

If `team finish` reports expected drift after a commit, approve the
write when it prompts.

For personal setup, use the wizard:

```bash
uv run cortex first-run
```

<details>
<summary>Explicit install and sync commands</summary>

```bash
uv run cortex install --categories collaboration --agents codex,claude --scope global --dry-run --yes
uv run cortex install --categories collaboration --agents codex,claude --scope global --yes
uv run cortex install --skills collaboration/handoff --agents codex,cursor --scope project --yes
uv run cortex status --skills collaboration/handoff --agents all --scope project
uv run cortex sync --categories collaboration --agents codex,claude --scope global --yes
uv run cortex finish --categories all --agents codex,claude --scope global
uv run cortex finish --categories all --agents codex,claude --scope global --no-dry-run --yes
```

</details>

<details>
<summary>No optional dependencies?</summary>

```bash
python skills/meta/scripts/validate.py --fix-generated
python scripts/install-skills.py --action status --profile-file profiles/team-codex-claude.json
python scripts/install-skills.py --action status --categories all --agents codex,claude --scope global
python scripts/install-skills.py --action sync --categories all --agents codex,claude --scope global --yes
python scripts/install-skills.py --action status --categories all --agents codex,claude --scope global
```

</details>

Generated packages include Cortex metadata and a `.cortex-managed`
marker. Cortex may update marked packages, but it skips unmarked native
skills so it does not overwrite your hand-written agent skills.
When a generated name changes, Cortex may remove older managed packages
for the same source skill during sync. It still skips unmanaged folders.

On Windows, Codex defaults to `%USERPROFILE%\.codex\skills` and Claude
defaults to `%USERPROFILE%\.claude\skills`. On Linux, Codex defaults to
`${CODEX_HOME:-$HOME/.codex}/skills` and Claude defaults to
`${CLAUDE_HOME:-$HOME/.claude}/skills`. You can override detected homes
with `CODEX_HOME`, `CLAUDE_HOME`, project scope, or an explicit target in
the deploy wrapper.

## Make An AI Use Cortex

The simplest project integration is an `AGENTS.md` file:

````markdown
Use Cortex for this work.

Before changing files, read:
- `skills/meta/index/SKILL.md`
- `skills/meta/contributing/SKILL.md`

Use relevant skills from the index and name them briefly when they guide
the work. If you learn something reusable, triage it through
`skills/meta/contributing/SKILL.md`: update or create a skill, add a log entry,
or leave it out if it is only session context.

Before committing Cortex changes, run:

```bash
python skills/meta/scripts/validate.py --fix-generated
```

After committing source skill or deployment-generator changes, if native
packages are installed, run `uv run cortex team finish`.
````

For another project, point those paths at the Cortex checkout. For
example:

````markdown
Use Cortex for this work.

Before changing files, read:
- `<cortex-root>\skills\meta\index\SKILL.md`
- `<cortex-root>\skills\meta\contributing\SKILL.md`

Use relevant skills from the index and name them briefly when they guide
the work. If you learn something reusable, triage it through
`<cortex-root>\skills\meta\contributing\SKILL.md`: update or create a skill,
add a log entry, or leave it out if it is only session context.

Before committing Cortex changes, run:

```bash
python <cortex-root>\skills\meta\scripts\validate.py --fix-generated
```

After committing source skill or deployment-generator changes, if native
packages are installed, run `uv run cortex team finish`.
````

When starting a session with an agent, paste something this concrete:

```text
Use Cortex for this work.

Before changing files, read:
- <cortex-root>\skills\meta\index\SKILL.md
- <cortex-root>\skills\meta\contributing\SKILL.md

Use relevant skills from the index and name them briefly when they guide
the work. If we learn something reusable, triage it through Cortex:
update or create a skill, add a log entry, or leave it out if it is only
session context.

Before committing Cortex changes, run:

python <cortex-root>\skills\meta\scripts\validate.py --fix-generated

After committing source skill or deployment-generator changes, if native
packages are installed, run `uv run cortex team finish`.
```

Useful prompts:

```text
Use Cortex and tell me which skills are relevant before you implement.
```

```text
Run the Cortex validation pipeline. If generated files are stale, fix
them, then rerun validation.
```

```text
We learned something reusable. Triage it through the Cortex contribution protocol
and either update a skill, create a new skill, or log why it is not
vault-worthy.
```

```text
I want to create a Cortex skill from my domain expertise.

Interview me just enough to understand the task, trigger situations,
examples, caveats, dangerous assumptions, and completion criteria. Then
triage the idea against the Cortex index. If it belongs in the vault,
draft or update the skill using meta/skill-authoring. Keep the common
path task-first, use required follow-on reading only for specific
branches, and run:

python <cortex-root>\skills\meta\scripts\validate.py --fix-generated
```

```text
I have domain expertise to add. Capture this against the relevant Cortex
skill as a human review note, then validate the vault.
```

```text
Create a project handoff using the Cortex handoff skill and commit it
with the rest of this work.
```

## Start A Skill From Expertise

A domain expert can intentionally start a skill without knowing the
Cortex markdown schema. The expert can talk to an agent with the prompt
above, or create a local brief first.

Guided terminal brief:

```bash
uv run cortex skill-brief
```

Scripted brief:

```bash
uv run cortex skill-brief --title "Encrypted traffic triage" --domain forensics --task "Teach agents how to triage encrypted packet captures without assuming payload visibility." --triggers "pcap, encrypted traffic, TLS investigation" --expertise "Prioritize DNS, SNI, certificate metadata, JA3/JA4, flow timing, and endpoint reputation before payload assumptions." --caveats "Payload inspection may be impossible or unlawful without keys and authorization." --outputs "A repeatable triage workflow and evidence checklist." --reviewer "packet analyst"
```

Stdlib equivalent:

```bash
python skills/meta/scripts/skill_brief.py --title "Encrypted traffic triage" --domain forensics --task "Teach agents how to triage encrypted packet captures without assuming payload visibility." --triggers "pcap, encrypted traffic, TLS investigation" --expertise "Prioritize DNS, SNI, certificate metadata, JA3/JA4, flow timing, and endpoint reputation before payload assumptions." --caveats "Payload inspection may be impossible or unlawful without keys and authorization." --outputs "A repeatable triage workflow and evidence checklist." --reviewer "packet analyst"
```

Briefs are written to `.cortex/skill-briefs/` by default and ignored by
git. They are local input for an agent. The agent still has to triage
the idea through `meta/contributing` and write the actual skill through
`meta/skill-authoring`.

## Add Human Expertise

Domain experts do not need to edit markdown by hand. They can explain
the correction, caveat, or field-tested pattern in conversation, and the
agent can capture it against the relevant skill.

Guided enhanced CLI:

```bash
uv run cortex expertise
```

Explicit enhanced CLI:

```bash
uv run cortex expertise forensics/pcap --claim "Encrypted traffic workflows should prioritize metadata and flow behavior before payload assumptions." --reviewer "packet analyst" --domain "packet forensics" --confidence high
```

Stdlib equivalent:

```bash
python skills/meta/scripts/capture_expertise.py forensics/pcap --claim "Encrypted traffic workflows should prioritize metadata and flow behavior before payload assumptions." --reviewer "packet analyst" --domain "packet forensics" --confidence high
python skills/meta/scripts/validate.py --fix-generated
```

Expertise capture updates optional review metadata and appends a
`Human Review Notes` section to the skill. Use it for human preference,
operational experience, domain expertise, disputes, and stale-skill
signals without making expert review mandatory for ordinary updates.

## Hooks And Validation

The validation command is the source of truth:

```bash
python skills/meta/scripts/validate.py
python skills/meta/scripts/validate.py --fix-generated
```

`--fix-generated` rebuilds the source manifest and skill graph, then
runs the full validation contract.

Install the optional git hook if you want local `git commit` to run the
pipeline automatically:

```bash
python skills/meta/scripts/install_hooks.py
```

The hook is a seatbelt, not the authority. Agents should still run
validation explicitly before committing.

Validation includes a docs smoke check for the README, onboarding,
rollout, roadmap, handoff links, and committed shared profile files:

```bash
python skills/meta/scripts/docs_smoke.py
```

Append lightweight project history with:

```bash
python skills/meta/scripts/log_entry.py --title "short title" --details "what changed and why"
```

## Everyday Commands

```bash
uv run cortex about
uv run cortex validate --fix-generated
uv run cortex first-run
uv run cortex skill-brief
uv run cortex team status
uv run cortex team finish
```

<details>
<summary>Portable and explicit equivalents</summary>

```bash
python skills/meta/scripts/validate.py
python skills/meta/scripts/validate.py --fix-generated
python scripts/install-skills.py --action status --profile-file profiles/team-codex-claude.json
python scripts/install-skills.py --action sync --categories all --agents codex,claude --scope global --yes
uv run cortex team finish --no-dry-run --yes
uv run cortex status --profile daily
uv run cortex status --profile-file profiles/team-codex-claude.json
uv run cortex install --categories collaboration --agents codex,claude --scope global --yes
uv run cortex repair --skills collaboration/handoff --agents cursor --scope project --yes
uv run cortex uninstall --skills collaboration/handoff --agents cursor --scope project --yes
```

</details>

## Shell Completion

The enhanced CLI exposes first-party completion help for Windows and
Linux shells:

```bash
uv run cortex completion powershell
uv run cortex completion bash
uv run cortex completion zsh
```

To let Typer install completion for the current shell:

```bash
uv run cortex completion powershell --install
uv run cortex completion bash --install
uv run cortex completion zsh --install
```

You can still use Typer's underlying options directly:

```bash
uv run cortex --show-completion powershell
uv run cortex --install-completion powershell
```

## How Cortex Decides What Belongs

Start with [skills/meta/contributing/SKILL.md](skills/meta/contributing/SKILL.md).
That protocol defines:

- What counts as vault-worthy knowledge.
- How to update existing skills instead of duplicating them.
- How to write model-agnostic, cold-agent-readable skills.
- How to handle conflicts without silent overwrites.
- How to deprecate knowledge without deleting history.

Skills may include a `model_role` hint:

- `thinking`: use a strong reasoning model to decide, resolve, or draft.
- `execution`: use a fast execution model to format, lint, index, or commit.
- `reference`: any competent agent can read and apply the skill.

These hints are advisory. Runtimes that cannot switch models should still
read them as guidance.

## Repository Map

Read these first:

- [skills/meta/index/SKILL.md](skills/meta/index/SKILL.md): generated skill graph.
- [skills/meta/contributing/SKILL.md](skills/meta/contributing/SKILL.md): update protocol.
- [skills/meta/roles/SKILL.md](skills/meta/roles/SKILL.md): model role split.
- [docs/ROADMAP.md](docs/ROADMAP.md): production-readiness plan.
- [docs/HANDOFF.md](docs/HANDOFF.md): current project state for a fresh agent.
- [docs/TEAM_ROLLOUT.md](docs/TEAM_ROLLOUT.md): team adoption and production checklist.
- [docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md): command inputs, outputs, flags, and fallbacks.

High-level structure:

```text
docs/
  FIRST_10_MINUTES.md
  TEAM_ROLLOUT.md
  CLI_REFERENCE.md
  ROADMAP.md
  HANDOFF.md
skills/
  collaboration/
    grill-me/
      SKILL.md
    handoff/
      SKILL.md
  meta/
    contributing/
      SKILL.md
    index/
      SKILL.md
    source-manifest/
      SKILL.md
    skill-authoring/
      SKILL.md
    roles/
      SKILL.md
    conflicts/
      SKILL.md
    deployment/
      SKILL.md
    scripts/
      lint_skill.py
      index_builder.py
      manifest_builder.py
      doctor.py
      validate.py
      commit_skill.py
      capture_expertise.py
      skill_brief.py
      log_entry.py
      install_hooks.py
      docs_smoke.py
  sql/
    injection/
      SKILL.md
  forensics/
    pcap/
      SKILL.md
    ja4/
      SKILL.md
  presentation/
    frontend-slides/
      SKILL.md
      vendor/
        frontend-slides/
        beautiful-html-templates/
  writing/
    humanizer/
      SKILL.md
scripts/
  install-skills.py
  deploy-skills.ps1
  deploy-skills.sh
profiles/
  team-codex-claude.json
src/
  cortex_cli/
    main.py
logs/
  README.md
```

## Deployment Details

Codex and Claude receive generated `SKILL.md` packages on Windows and
Linux. Cursor receives project rule files. Each generated artifact embeds
usable skill content and points back to Cortex for edits, validation,
commits, and reinstall.

Claude direct slash invocation uses the generated package directory name.
Cortex installs non-meta skills with task-shaped names when it can do so
safely. It prefers the first source alias as the native command name, so
`forensics/pcap` becomes `/pcap`, `writing/humanizer` becomes
`/humanizer`, `collaboration/handoff` becomes `/handoff`, and
`sql/injection` becomes `/sql`. If two skills would collide, Cortex falls
back to `domain-skill`, such as `/forensics-pcap`. Meta utility packages
stay prefixed as `/cortex-meta-*`.

Generated packages are task-first: the agent sees the actual skill
instructions before Cortex provenance, script paths, or feedback notes.
The Cortex footer is there to preserve the update loop without spending
the first screen of context on infrastructure.

Generated `SKILL.md` packages include aliases, topics, domain, leaf name,
and skill ID in their frontmatter, description, and a compact trigger
hints section. This gives Codex and Claude useful hooks for
natural-language requests even when the user does not invoke a slash
command directly.

Source skills follow the same rule. They should teach the task first and
link to Cortex process only when that process is the skill's subject.

Generated native packages and project-rule adapters also carry skill
companion resources such as `vendor/`, `assets/`, `references/`, and
`scripts/`. Directory-shaped runtimes receive those folders beside
`SKILL.md`; file-shaped runtimes receive a managed sibling resources
directory. This lets offline enterprise deployments use large assets
such as the `presentation/frontend-slides` template library without
reaching out to GitHub at runtime.

Those resource folders are not only for borrowed material. If the team
adds a first-party helper such as
`skills/forensics/pcap/scripts/extract_flows.py` using Scapy, a
`tshark_summary.sh` wrapper, or packet-analysis addenda under
`skills/forensics/pcap/references/`, those files are part of the pcap
skill and deploy with it. All source skills use the same folder shape:
`skills/<domain>/<name>/SKILL.md`. Skill-specific `scripts/`, `assets/`,
`references/`, and `vendor/` live beside that root file. The source
`SKILL.md` still uses Cortex frontmatter and validation, but the folder
looks like the native skill folders people already know. The skill
should still document any optional runtime dependency, such as Scapy or
`tshark`, because Cortex can carry the helper but cannot guarantee the
target machine has every tool installed.

The installer always includes the meta core bundle, even when you select
only one skill or category. That lets deployed agents find the index,
follow the contribution protocol, run helper scripts, and feed
improvements back into the vault.

Use the shell deploy-all wrappers when you want simple auto-detection:

```powershell
scripts/deploy-skills.ps1 -Agent auto
```

```bash
scripts/deploy-skills.sh --agent auto
```

`auto` detects known local agent homes such as Codex at
`${CODEX_HOME:-$HOME/.codex}/skills`. Use an explicit agent or target
when detection is not enough.
