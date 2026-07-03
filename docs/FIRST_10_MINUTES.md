# First 10 Minutes With Cortex

This path is for a new user, a teammate, or a fresh agent that needs
Cortex to be useful before the whole vault makes sense.

The goal is not mastery. The goal is to clone the repo, prove it is
healthy, deploy one useful skill, point an agent at the vault, and learn
the update loop.

## Why A Team Would Adopt This

Cortex adds a small habit to work teams already do: point the agent at a
shared repo before it starts, then capture durable lessons when the work
teaches something reusable.

That costs a little extra token usage because the agent reads a compact
index, contribution protocol, and any relevant skills. The payoff is
that future sessions stop rediscovering the same decisions, failure
modes, prompts, handoffs, and domain caveats from scratch.

The adoption surface is deliberately small:

- Keep using normal git.
- Keep using normal markdown.
- Keep using your current agent tools.
- Add two project instructions through `AGENTS.md` or the equivalent.
- Run validation before committing Cortex changes.
- Run one local finish command after committing when native packages are
  installed.

The point is not to replace team judgment or project documentation. The
point is to give agents a durable, reviewable memory that lives where the
team already works: in files, in git, under review.

## Minute 0: Get The Vault

```bash
git clone git@github.com:[redacted-repo]/cortex.git
cd cortex
```

On Windows, PowerShell is fine. On Linux, a normal shell is fine. Run
commands from the repository root unless a command says otherwise.

## Minute 1: Prove It Works

Start with the portable check. This proves the clone is healthy before
you install anything optional.

```bash
python --version
python skills/meta/scripts/validate.py
```

This is the portable health check. It uses Python's standard library. It
does not need `uv`, hosted CI, embeddings, or an agent integration.

If the check says the generated catalogs are stale, repair them:

```bash
python skills/meta/scripts/validate.py --fix-generated
```

## Minute 2: Optional Nice Terminal App

Most people should use the enhanced CLI. It asks better questions, shows
better status, supports completion, and keeps the scary flags out of the
common path. It still wraps the same portable scripts.

```bash
python -m pip install --user uv
uv sync
uv run cortex about
uv run cortex validate --fix-generated
```

If your shell cannot find `uv` after install, restart the terminal or add
your Python Scripts directory to `PATH`.

If you cannot install `uv`, keep using the standard-library commands in
this guide. The full fallback surface is in `docs/CLI_REFERENCE.md`.

## Minute 3: Preview A Skill Install

Run the guided setup. It asks what you want, previews the install, and
then asks whether to apply the same selection. You can also save the
selection as a local or shared profile from inside the wizard.

```bash
uv run cortex first-run
```

If your team already has a committed profile, check that path too:

```bash
uv run cortex team status
uv run cortex team finish
```

The guided lane and team lane are compatible. Use `first-run` to learn
the choices or draft a local setup. Use `team status` and `team finish`
to compare your machine with the team's reviewed profile.

## Minute 4: Install Or Save A Profile

For a personal setup, keep using `uv run cortex first-run`. Let it save
a local profile if you want to reuse the same choices later. Let it
install when the preview makes sense.

If you are following the team's agreed setup, use the team profile
instead:

```bash
uv run cortex team profile
uv run cortex team status
uv run cortex team finish
```

If the team profile is missing or looks wrong, treat that as a normal
team setup gap. Use the guided lane locally, then propose a shared
profile in `profiles/` through normal review.

Local profiles live under `.cortex/profiles/` and are ignored by git.
Team profiles live under `profiles/` and should be reviewed like source.
The long flag forms are in `docs/CLI_REFERENCE.md`.

<details>
<summary>Scripted form for agents and repeatable docs</summary>

```bash
uv run cortex first-run --save-profile daily
uv run cortex first-run --no-dry-run --save-profile daily
```

Use explicit flags when there is no interactive terminal, when you are
writing automation, or when an agent needs exact inputs.

</details>

## Minute 5: Point An Agent At Cortex

In this repo, `AGENTS.md` is intentionally tiny:

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

In another project, use the same instructions with paths to your
Cortex checkout:

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

For a new session, paste:

```text
Use Cortex for this work. Before changing files, read:
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

## Minute 6: Add A Small Piece Of Context

Use logs for lightweight project history:

```bash
python skills/meta/scripts/log_entry.py --title "try Cortex onboarding" --details "Validated the vault, previewed skill deployment, and pointed an agent at Cortex."
```

There is no enhanced wrapper for log entries yet; this is intentionally a
small standard-library helper.

Use expertise capture when a human contributes durable knowledge about a
skill:

```bash
uv run cortex expertise
```

It will ask which skill the knowledge belongs to and capture the claim,
reviewer, domain, confidence, and caveats. Use the explicit command form
from `docs/CLI_REFERENCE.md` when scripting or asking an agent to do it.

If you want to start a new skill from domain knowledge, create a local
brief:

```bash
uv run cortex skill-brief
```

The brief is local input. An agent still needs to triage it through
`skills/meta/contributing/SKILL.md` before changing vault source.

## Minute 7: Validate Before You Commit

Use the enhanced command if you installed `uv`:

```bash
uv run cortex validate --fix-generated
```

<details>
<summary>Portable fallback</summary>

```bash
python skills/meta/scripts/validate.py --fix-generated
```

</details>

This rebuilds generated catalogs and runs the full local validation
contract.

## Minute 8: Commit The Change

Use normal git for documentation or multi-file work:

```bash
git status --short
git diff --check
git add README.md docs/FIRST_10_MINUTES.md logs/2026-06.md
git commit -m "docs: add first 10 minutes onboarding"
```

For a single skill update, prefer the structured helper:

Standard-library path:

```bash
python skills/meta/scripts/commit_skill.py skills/sql/injection/SKILL.md "skill(sql/injection): add safe query example"
```

There is no enhanced commit wrapper yet. Normal git is still the right
path for docs, scripts, and multi-file changes.

## Minute 9: Finish And Sync Managed Agent Packages

After committing a skill or deployment-generator change, check installed
native packages and refresh managed stale ones:

```bash
uv run cortex team finish
```

It validates Cortex, shows native package drift, previews the sync, and
then asks whether to apply it.

<details>
<summary>Non-interactive write form</summary>

```bash
uv run cortex team finish --no-dry-run --yes
```

</details>

<details>
<summary>Portable fallback</summary>

```bash
python scripts/install-skills.py --action status --profile-file profiles/team-codex-claude.json
python scripts/install-skills.py --action sync --profile-file profiles/team-codex-claude.json --yes
python scripts/install-skills.py --action status --profile-file profiles/team-codex-claude.json
```

</details>

## Minute 10: Know Where To Go Next

Read these when you need more than the first path:

- `README.md`: day-to-day commands and repository map.
- `docs/ROADMAP.md`: production-readiness milestones.
- `docs/HANDOFF.md`: current project state for a fresh session.
- `docs/CLI_REFERENCE.md`: command inputs, outputs, flags, and fallbacks.
- `skills/meta/contributing/SKILL.md`: what belongs in Cortex and how updates
  are made.
- `skills/meta/skill-authoring/SKILL.md`: how to write or revise a skill.
- `skills/meta/deployment/SKILL.md`: how native agent adapters work.

## Daily Commands

Use these when Cortex is already set up.

**The one to remember:** after you commit a skill or deployment change,
run `uv run cortex team finish`. It is the single command that both
validates the vault with `--fix-generated` and installs the changed
skills into your native agent packages. It previews drift and asks before
writing. Everything below is the same loop, broken into smaller steps.

Start or resume work:

```bash
git pull
uv run cortex validate --fix-generated
```

Check deployed native packages:

```bash
uv run cortex team status
```

Before committing Cortex changes:

```bash
uv run cortex validate --fix-generated
git diff --check
git status --short
```

After committing skill or deployment changes, dry-run first and then
write managed packages if the drift is expected:

```bash
uv run cortex team finish
```

The command asks before writing.

<details>
<summary>No uv available?</summary>

```bash
python skills/meta/scripts/validate.py --fix-generated
python scripts/install-skills.py --action status --profile-file profiles/team-codex-claude.json
```

</details>

Set up completion when using the enhanced CLI regularly:

```bash
uv run cortex completion powershell
uv run cortex completion bash
uv run cortex completion zsh
```
