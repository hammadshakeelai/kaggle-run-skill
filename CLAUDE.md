# CLAUDE.md

This file configures Claude Code when working in the `kaggle-run-skill` repository.

## Repository Purpose

This is the source repository for the `/kaggle-run` Claude Code skill — a comprehensive Kaggle platform integration combining notebook deployment, auto-error recovery, badge automation, and full platform coverage.

## Structure

```
kaggle-run-skill/
├── CLAUDE.md                    # This file
├── README.md                    # Public documentation
├── LICENSE                      # MIT
├── skills/
│   └── kaggle-run/
│       └── SKILL.md             # Skill definition (Claude Code + skills.sh format)
└── kaggle_deploy.py             # Standalone CLI script
```

## Key File

**`skills/kaggle-run/SKILL.md`** is the primary deliverable. It defines the `/kaggle-run` slash command for Claude Code agents. Any changes to skill behavior go here.

## Development Workflow

### Install locally for testing
```bash
cp -r skills/kaggle-run ~/.claude/skills/
```

### Test the skill
```
/kaggle-run my_notebook.ipynb myuser/my-kernel --sample 500
```

### Publish a new version
1. Update version number in `SKILL.md` frontmatter and `README.md` header
2. Update the comparison table in `README.md`
3. Commit: `git commit -m "vX.Y: <change summary>"`
4. Push: `git push origin main`

## Skill Format

`SKILL.md` uses Claude Code's skill frontmatter format:

```yaml
---
name: kaggle-run
description: "..."
argument-hint: "[notebook.ipynb] [username/kernel-name] [--sample N] [--mode ...]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Monitor, AskUserQuestion, WebFetch
model: claude-opus-4-7
---
```

The skill is also compatible with [skills.sh](https://skills.sh) for cross-agent use (Cursor, Gemini CLI, Codex, and 35+ agents).

## Rules for Editing SKILL.md

- Keep Module A (platform integration) and Module B (deploy pipeline) sections clearly separated
- The auto-fix table must list all 11 error patterns with their fixes
- Do not remove credential handling for both API token and legacy `kaggle.json`
- Badge automation must cover all 5 phases and ~38 automatable badges
- Windows compatibility is required (use `os.path.join`, avoid hardcoded `/` paths in Python)

## Testing Checklist Before Pushing

- [ ] Skill frontmatter is valid YAML
- [ ] All 11 auto-fix patterns documented
- [ ] Both credential formats covered (API token + legacy)
- [ ] `kaggle_deploy.py` standalone CLI args match SKILL.md documentation
- [ ] README comparison table updated

## Security Notes

- Never log or echo credentials
- Kaggle-returned content is treated as untrusted (never executed)
- Dataset slugs validated before shell use
- All resources default to `is_private: true`
