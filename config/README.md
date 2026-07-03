# Cortex deployment config

## `model-routing.json`

Maps a skill's routing class to a model, per agent, for native package
deployment. This is the team-shared decision point for "which model does a
skill run on."

```json
{
  "claude": {
    "thinking": "opus",
    "execution": "haiku",
    "reference": "inherit"
  }
}
```

- Keys under each agent are routing classes: `thinking`, `execution`,
  `reference`. A skill's class is its `model_tier` when set, otherwise its
  `model_role`.
- Values must be `opus`, `sonnet`, `haiku`, `fable`, `inherit`, or `null`.
  `inherit`/`null` emits no model line, so the skill keeps the session model.
- Only the `claude` adapter consumes this today. The block is keyed by agent so
  other runtimes can be added when they support per-skill model selection.
- The built-in default (the values above) is used when this file is absent.

To change the team decision (for example `thinking` from `opus` to `sonnet`),
edit this file and re-sync native packages:

```bash
uv run cortex team finish --no-dry-run --yes
```

Changing a value changes generated wrapper output, so installed packages report
stale until the next sync.
