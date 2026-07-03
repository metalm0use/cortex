# Cortex CLI Reference

This document is the command contract for the enhanced `uv run cortex`
CLI and the standard-library fallback scripts.

The enhanced CLI owns the happy human path. It should ask questions,
show status, preview writes, and prompt before changing native packages.
The flags documented here are still first-class, but they are mainly the
alignment layer for scripts, agents, docs, debugging, and the
standard-library fallback.

The stdlib scripts are the portable contract for fresh clones and
environments without optional dependencies. When both exist, they must
operate on the same Cortex source files and native package metadata.

## Common Inputs

Humans should usually start with `uv run cortex first-run` for personal
setup or `uv run cortex team ...` for the committed team profile. These
lanes are compatible: use `first-run` to learn or draft local choices,
then use `team status` and `team finish` to align with the reviewed team
profile. Use the long flag forms only when the exact inputs need to be
visible, repeatable, non-interactive, or debuggable.

Skill selection:

- `--skills`: comma-separated skill IDs such as `collaboration/handoff`,
  or `all`.
- `--categories`: comma-separated domains such as `collaboration`, or
  `all`.
- No selection on status-like commands means all skills.
- The meta core bundle is always included by deployment commands.

Native targets:

- `--agents`: comma-separated `codex`, `claude`, `cursor`, or `all`.
- `--codex`, `--claude`, `--cursor`: convenience filters on status and
  cleanup commands.
- `--scope`: `global` or `project`.
- `--mode`: `wrapper`, `symlink`, or `copy`; default is `wrapper`.
- `--project`: project root for project-scoped installs.

Profiles:

- `--profile`: local ignored profile from `.cortex/profiles/`.
- `--profile-file`: explicit JSON profile, usually committed under
  `profiles/`.
- Explicit flags override profile values.
- Shared profiles should avoid machine-local paths unless that is
  intentional.

Write controls:

- `--dry-run`: preview writes.
- `--no-dry-run`: allow writes for commands that default to preview.
- `--yes`: skip confirmation for scripted or write paths.
- `--show-missing`: include absent selected packages in enhanced status
  output. Status hides missing packages by default to keep normal checks
  focused on installed or actionable managed targets.
- `--raw`: print stdlib installer output instead of a Rich table.

## Status States

- `current`: installed metadata matches current source and generator.
- `stale`: managed package exists but source hash, skill ID, or generator
  version no longer matches.
- `missing`: selected package is absent.
- `unmanaged`: target exists without Cortex metadata.
- `unsupported`: selected agent and scope have no known target.

Only `current` means no action is needed. `stale` and `missing` are safe
to fix with `sync` or `finish` when the targets are Cortex-managed.
`unmanaged` must not be overwritten without owner agreement.

## Enhanced Commands

| Command | Purpose | Mutates |
| --- | --- | --- |
| `uv run cortex about` | Show Cortex identity and local paths. | Nothing. |
| `uv run cortex validate --fix-generated` | Run the portable validation contract. | Generated catalogs when `--fix-generated` is used. |
| `uv run cortex first-run` | Guided human setup for skill, agent, scope, mode, optional profile saving, preview, and optional apply-now. | Profiles when requested; native packages only after approval or with `--no-dry-run`. |
| `uv run cortex team profile` | Show `profiles/team-codex-claude.json`. | Nothing. |
| `uv run cortex team status` | Inspect native packages selected by the team profile. | Nothing. |
| `uv run cortex team finish` | Validate, inspect, preview drift sync, optionally apply it, and inspect again using the team profile. | Generated catalogs; native packages only after approval or with `--no-dry-run --yes`. |
| `uv run cortex team sync` | Sync managed native packages selected by the team profile. | Native packages only after approval or with `--no-dry-run --yes`. |
| `uv run cortex status` | Inspect selected native packages. | Nothing. |
| `uv run cortex install` | Install selected native packages. | Native packages unless `--dry-run` is used. |
| `uv run cortex sync` | Regenerate selected managed native packages. | Native packages unless `--dry-run` is used. |
| `uv run cortex repair` | Repair selected managed native packages. | Native packages unless `--dry-run` is used. |
| `uv run cortex uninstall` | Remove selected Cortex-managed native packages. | Native packages unless `--dry-run` is used. |
| `uv run cortex cleanup` | Preview and optionally remove Cortex-managed native packages, defaulting to all Cortex skills for Codex and Claude. | Native packages only after approval or with `--no-dry-run --yes`. |
| `uv run cortex profile ...` | Manage local and shared deployment profiles. | Profiles for `save` and `delete`. |
| `uv run cortex completion <shell>` | Show completion setup for PowerShell, bash, zsh, or fish. | Nothing. |
| `uv run cortex expertise` | Capture a human expertise claim against a skill. | Source skill markdown; generated catalogs when validating. |
| `uv run cortex skill-brief` | Create a local domain-expert brief. | Local brief files unless `--print-only` is used. |

## Team Commands

Use these first for normal team deployment work:

```bash
uv run cortex team profile
uv run cortex team status
uv run cortex team finish
```

`team finish` defaults to dry-run. It validates Cortex, inspects native
status, reports drift, previews sync, and asks whether to apply it.

Non-interactive write form:

```bash
uv run cortex team finish --no-dry-run --yes
```

Long-form equivalent:

```bash
uv run cortex finish --profile-file profiles/team-codex-claude.json
uv run cortex finish --profile-file profiles/team-codex-claude.json --no-dry-run --yes
```

Stdlib equivalent:

```bash
python skills/meta/scripts/validate.py --fix-generated
python scripts/install-skills.py --action status --profile-file profiles/team-codex-claude.json
python scripts/install-skills.py --action sync --profile-file profiles/team-codex-claude.json --yes
python scripts/install-skills.py --action status --profile-file profiles/team-codex-claude.json
```

Agent-focused status examples:

```bash
uv run cortex status --codex
uv run cortex status --claude --show-missing
uv run cortex team status --codex
python scripts/install-skills.py --action status --categories all --agents codex --scope global --hide-missing
```

Cleanup preview and apply:

```bash
uv run cortex cleanup
uv run cortex cleanup --codex
uv run cortex cleanup --no-dry-run --yes
python scripts/install-skills.py --action cleanup --categories all --agents codex,claude --scope global --dry-run
python scripts/install-skills.py --action cleanup --categories all --agents codex,claude --scope global --yes
```

## Profile File Schema

Shared profile files are JSON objects with these optional string fields:

```json
{
  "skills": "collaboration/handoff,sql/injection",
  "categories": "all",
  "agents": "codex,claude",
  "scope": "global",
  "mode": "wrapper",
  "project": "C:/path/to/project"
}
```

At least one of `skills` or `categories` must be present. `agents` may
contain `codex`, `claude`, `cursor`, or `all`. `scope` must be `global`
or `project`. `mode` must be `wrapper`, `symlink`, or `copy`.

Validate a shared profile with:

```bash
uv run cortex profile validate-file profiles/team-codex-claude.json
python scripts/install-skills.py --action status --profile-file profiles/team-codex-claude.json
```

## Stdlib Installer Contract

The stdlib installer is:

```bash
python scripts/install-skills.py
```

Important flags:

- `--action`: `install`, `status`, `sync`, `repair`, `uninstall`, or
  `cleanup`. `cleanup` is a safer named alias for removing selected
  Cortex-managed native packages.
- `--profile-file`: shared JSON profile defaults.
- `--skills`, `--categories`, `--agents`, `--scope`, `--mode`,
  `--project`: same meaning as the enhanced CLI.
- `--dry-run`: preview writes.
- `--hide-missing`: omit absent packages from status output.
- `--yes`: skip confirmation.

The installer prints selected skills, agents, scope, mode, action, and
one line per target. These raw status lines are what the enhanced CLI
parses into Rich tables.

## Other Command Notes

`uv run cortex first-run` requires a TTY because it uses interactive
selection. In the guided path it can save a local profile, save a shared
profile file, preview the selected install, and then ask whether to apply
the same selection. Every first-run choice can also be provided through
explicit flags, local profiles, or shared profile files.

`uv run cortex cleanup` defaults to dry-run and only removes packages
with Cortex metadata. It is the preferred human-facing way to remove
Cortex-owned native skills without touching unmanaged local skills.

`uv run cortex completion <shell>` supports `powershell`, `bash`, `zsh`,
and `fish`. With `--install`, it prints Typer install commands. Without
`--install`, it prints shell-specific setup guidance.

`uv run cortex expertise` is guided when run without a skill or claim in
a TTY. It asks for the target skill, durable claim, optional details,
reviewer, domain, review status, confidence, and contribution kind. The
explicit form accepts the same values through flags. The stdlib fallback
is `skills/meta/scripts/capture_expertise.py`.

`uv run cortex skill-brief` can run interactively or from flags. It
writes local briefs under `.cortex/skill-briefs/` by default. The stdlib
fallback is `skills/meta/scripts/skill_brief.py`.

## Validation Expectations

Before commit:

```bash
python skills/meta/scripts/validate.py --fix-generated
git diff --check
```

After committing source skill or deployment-generator changes:

```bash
uv run cortex team finish
uv run cortex team finish --no-dry-run --yes
```

Use the dry run first. Write only when the reported drift is expected.
