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
packages are installed, run `uv run cortex finish --no-dry-run --yes`,
or use the stdlib installer status/sync/status fallback.
