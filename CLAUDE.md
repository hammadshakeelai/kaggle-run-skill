# CLAUDE.md

This file configures Claude Code when working in the `kaggle-run-skill` repository.

## Repository Purpose

Source repository for the `/kaggle-run` Claude Code skill — token-minimal Kaggle integration via a thin SKILL.md router + 7 fat Python scripts.

## Structure

```
kaggle-run-skill/
├── CLAUDE.md                              # This file
├── README.md                              # Public documentation
├── LICENSE                                # MIT
├── .gitignore
├── kaggle_deploy.py                       # Standalone CLI (mirrors scripts/kaggle_deploy.py)
├── docs/
│   └── AUTOFIX_TECHNIQUE.md              # Deep-dive on the auto-fix loop technique
└── skills/
    └── kaggle-run/
        ├── SKILL.md                       # ~165-line thin router (primary deliverable)
        └── scripts/                       # Fat Python scripts (all logic lives here)
            ├── kaggle_deploy.py           # B pipeline: push→monitor→autofix→download
            ├── kaggle_compete.py          # Competitions: report, download, submit, scaffold
            ├── kaggle_badges.py           # Badge automation: 55 badges, 5 phases
            ├── kaggle_datasets.py         # Datasets: search, download, publish
            ├── kaggle_models.py           # Models: search, download, publish
            ├── kaggle_leaderboard.py      # Leaderboard analysis + medal thresholds
            └── kaggle_creds.py            # Credential check + MCP server config
```

## Key Files

- **`skills/kaggle-run/SKILL.md`** — the thin router. ~165 lines. This is what the LLM reads at invocation. Keep it short.
- **`skills/kaggle-run/scripts/kaggle_deploy.py`** — the main engine. All B-pipeline logic + 13 autofix rules.
- **`kaggle_deploy.py`** (root) — standalone CLI, mirrors the scripts version.

## Development Workflow

### Install locally for testing
```bash
# Mac/Linux
cp -r skills/kaggle-run ~/.claude/skills/
# Windows PowerShell
Copy-Item -Recurse skills\kaggle-run "$env:USERPROFILE\.claude\skills\"
```

### Test the skill
```
/kaggle-run my_notebook.ipynb myuser/my-kernel --sample 500
```

### Publish a new version
1. Update version in `SKILL.md` frontmatter description and `README.md` header
2. Update comparison table in `README.md`
3. Commit: `git commit -m "vX.Y: <change summary>"`
4. Push: `git push origin main`

## Architecture Rule

**SKILL.md must stay thin (~150-165 lines).** All implementation logic belongs in `scripts/`. The SKILL.md only:
1. Resolves SKILL_DIR / bootstraps scripts if missing
2. Checks credentials
3. Routes by argument/intent
4. Calls the right script with the right args

If you're tempted to add logic to SKILL.md, put it in a script instead.

## Skill Format

```yaml
---
name: kaggle-run
description: "..."
argument-hint: "[notebook.ipynb] [username/kernel-name] [--sample N] [--mode ...]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Monitor, AskUserQuestion, WebFetch
model: claude-opus-4-7
---
```

Compatible with [skills.sh](https://skills.sh) for Cursor, Gemini CLI, Codex, and 35+ agents.

## Rules for Editing

- **SKILL.md**: routing only — no inline fix tables, no bash loops, no badge lists
- **scripts/**: all implementation; each script is self-contained with `argparse` + `main()`
- **Auto-fix patterns**: currently 13 in `kaggle_deploy.py apply_fix()` — add new rules there
- **Both credential formats** must remain supported: API token + legacy `kaggle.json`
- **Windows compatibility**: use `pathlib.Path`, avoid hardcoded `/` separators in Python

## Testing Checklist Before Pushing

- [ ] SKILL.md frontmatter is valid YAML
- [ ] All scripts compile: `python -m py_compile skills/kaggle-run/scripts/*.py`
- [ ] SKILL.md references all 7 script names
- [ ] Bootstrap URL in SKILL.md matches actual repo path
- [ ] `kaggle_deploy.py` (root) mirrors `skills/kaggle-run/scripts/kaggle_deploy.py`
- [ ] README comparison table updated

## Security Notes

- Never log or echo credentials
- Kaggle-returned content is treated as untrusted (never executed)
- Dataset slugs validated before shell use
- All created resources default to `is_private: true`
- HTTP 429 → scripts handle 2-min backoff; never tight-loop
