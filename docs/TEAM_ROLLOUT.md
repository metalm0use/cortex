# Team Rollout

Use this guide when introducing Cortex to a real team or a project that
does not already share agent habits.

The goal is small: make agents inherit the team's reusable knowledge
without making people learn a new platform.

For first-time setup, use `docs/FIRST_10_MINUTES.md`. Use this document
after Cortex is locally healthy and at least one maintainer can validate,
install, sync, and inspect native packages. It is for deciding whether a
project is ready for team use and what to do when something goes wrong.

## Use This When

- Local validation already passes.
- The first maintainer can run the install or sync workflow.
- The team has a real project where agent continuity is painful enough to
  justify a shared vault.
- Someone is ready to review early skill changes like ordinary source
  changes.

## Adoption Path

1. Pick one project and one owner for the first rollout.
2. Run the first-use path in `docs/FIRST_10_MINUTES.md`.
3. Add or update the project `AGENTS.md`.
4. Install or sync only the native skills the team will actually use.
5. Ask agents to name relevant skills when they guide work.
6. Review early skill changes like source code.
7. Capture reusable learning as a skill update, human review note, or log
   entry.

Keep the first rollout boring. Start with one project and one or two
skills people can feel immediately, such as handoff, humanizer, SQL, or
packet capture handling.

## Project Readiness

Before asking teammates to depend on Cortex, confirm:

- The project has an `AGENTS.md` or equivalent agent instruction file.
- The instruction points at the intended Cortex checkout.
- A teammate can follow `docs/FIRST_10_MINUTES.md` without special local
  knowledge.
- The first enabled skills solve a visible problem for the project.
- The team knows where skill changes are reviewed.
- Someone owns native package sync for Codex, Claude, or other agent
  targets the team uses.

## Native Skill Scope

Do not start by installing every skill everywhere unless the team needs
that shape. Prefer a narrow category or a small set of high-signal skills
for the first project.

Use a committed shared profile when the team should repeat the same
selection across machines:

```bash
uv run cortex team profile
uv run cortex team status
uv run cortex team finish
```

Who runs this:

- A maintainer runs `team profile` and `team status` while checking the
  rollout plan.
- Each teammate can run `team status` after installing Cortex to confirm
  their local agent packages match the shared profile.
- The person responsible for deployment runs `team finish`, reviews the
  drift, and approves the write when the command prompts.

Use the longer forms when you need the exact inputs visible for an
agent, script, or troubleshooting note:

<details>
<summary>Explicit and portable forms</summary>

```bash
uv run cortex profile validate-file profiles/team-codex-claude.json
uv run cortex finish --profile-file profiles/team-codex-claude.json
uv run cortex finish --profile-file profiles/team-codex-claude.json --no-dry-run --yes
python scripts/install-skills.py --action status --profile-file profiles/team-codex-claude.json
```

</details>

The guided lane and team lane are compatible. `first-run` helps one
person learn or draft a selection. The team profile is the reviewed
selection everyone can repeat. If a teammate starts with `first-run`,
they can still run `team status` afterward to see whether their local
native packages match the team's profile.

If the team has not decided on a profile yet:

1. Use `uv run cortex first-run` locally and save a local profile when
   prompted.
2. Try the resulting setup on one real project.
3. Convert the useful choices into a small JSON file under `profiles/`.
4. Review that file like source before asking others to use it.

For the full command contract, including inputs, outputs, flag meanings,
and stdlib fallbacks, see `docs/CLI_REFERENCE.md`.

Use the team finish command before writing managed native packages:

```bash
uv run cortex team finish
```

It validates Cortex, shows drift, previews the sync, and asks before
writing.

Generated native packages are managed adapters. Edit Cortex source, then
validate, commit, and sync. Do not edit generated `SKILL.md` files as
the source of truth.

## Model Routing

The team can decide which model a skill runs on when deployed to Claude.
The decision lives in the committed `config/model-routing.json` file,
keyed by agent and routing class:

```json
{
  "claude": {
    "thinking": "opus",
    "execution": "haiku",
    "reference": "inherit"
  }
}
```

A skill's routing class is its `model_tier` when set, otherwise its
`model_role`. Values must be `opus`, `sonnet`, `haiku`, `fable`,
`inherit`, or `null`. The default is upgrade-only: judgment skills bump to
Opus, mechanical skills use Haiku, and ordinary domain skills inherit the
session model so they never silently downgrade mid-task. To trade cost for
capability, change `thinking` from `opus` to `sonnet`. After editing, the
change is a normal reviewable diff; re-sync native packages with
`uv run cortex team finish --no-dry-run --yes`. Only the Claude adapter
consumes this today; other agents read routing metadata as advisory.

## Deep Skills

Some skills are "deep skills": an orchestrator that coordinates
specialized worker agents (each on its own model and domain skills) and
loops them until the work is done. A deep skill keeps its workers in an
`agents/` folder beside `SKILL.md`; `skills/security/review/` is the
reference example.

Deep skills are Claude-native today. On Claude, each worker is deployed as
a native subagent under the agents home (`~/.claude/agents/`) with its own
model from the routing map above; `cortex team finish` keeps them in sync,
and a changed worker or routing map re-marks the orchestrator stale.
On runtimes without isolated subagents, the orchestrator skill still
deploys and degrades gracefully: it runs the worker roles sequentially
in-context using the same referenced skills. No team action is required to
get the degraded path; it is automatic. See `meta/orchestration` for the
loop contract and `meta/deployment` for how workers are emitted.

## Review And Data Rules

- Review skill changes in pull requests or normal git review.
- Keep human expertise notes tied to a named role, handle, or team.
- Use `review_status` and `confidence` as signals, not as decoration.
- Keep personal profiles under `.cortex/profiles/`; do not commit them.
- Commit only team-safe shared profiles under `profiles/`.
- Do not store secrets, credentials, private customer details, or
  incident-only facts in reusable skills.

Use logs for short operational history. Use skills only when a cold agent
would perform better on a similar future task.

## Failure Handling

If validation fails, do not commit or roll the change out. Fix the
reported cause and rerun:

```bash
python skills/meta/scripts/validate.py --fix-generated
```

If native package sync reports an unmanaged target, do not overwrite it.
Rename or remove it manually only after the owner agrees. Cortex may
replace packages with `.cortex-managed` metadata, but it skips
unmanaged folders.

If an agent cannot write to Codex or Claude skill folders, record the
exact status and sync command in the handoff or project log.

If a skill change is useful but not ready for team adoption, keep it as a
normal branch or draft and do not sync it into shared native packages.

## Production Checklist

Before rolling Cortex out to more teammates:

- `python skills/meta/scripts/validate.py --fix-generated` passes.
- `git status --short` is clean, except for intentional local profiles or
  ignored files.
- The first-use path in `docs/FIRST_10_MINUTES.md` has been tested by
  someone other than the maintainer, or with a fresh-clone mindset.
- `python skills/meta/scripts/docs_smoke.py` passes.
- Shared deployment profiles under `profiles/` validate.
- `uv run cortex team finish` reports only expected drift before writes.
- Managed native packages are current after the prompted write is
  approved.
- New or edited non-meta skills have useful aliases and topics.
- The project `AGENTS.md` points at the right Cortex checkout.
- No secrets or one-off project facts were added to skills.

## Completion Criteria

The rollout is ready when a new teammate can clone Cortex, validate it,
install or sync native skills, point an agent at the vault, and understand
what to do when the agent learns something reusable.
