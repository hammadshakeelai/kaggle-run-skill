# kaggle-run-skill v3.0

> **The most complete Kaggle slash command for AI coding agents.**  
> Built on [shepsci/kaggle-skill v2.3](https://github.com/shepsci/kaggle-skill) with full platform integration, automated notebook deployment, 11-pattern error recovery, 55-badge automation, and hackathon writeup retrieval — all in one skill.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Works with Claude Code](https://img.shields.io/badge/Claude%20Code-Compatible-blue)](https://claude.ai/code)
[![Skills.sh Compatible](https://img.shields.io/badge/skills.sh-compatible-green)](https://skills.sh)
[![Based on shepsci/kaggle-skill](https://img.shields.io/badge/based%20on-shepsci%2Fkaggle--skill-orange)](https://github.com/shepsci/kaggle-skill)

---

## What It Does

`/kaggle-run` combines two modules:

### Module A — Full Kaggle Platform Integration *(built on shepsci/kaggle-skill v2.3)*
- **Credential setup** — API token (new format) + legacy `kaggle.json`, both supported
- **Competition reports** — landscape, leaderboard, data files, submission workflow
- **Dataset & model downloads** — CLI + kagglehub Python API
- **Publishing** — upload datasets, models, notebooks with proper metadata
- **Competition submissions** — `kaggle competitions submit` full workflow
- **Badge automation** — 55 badges across 5 phases (~38 automatable)
- **Hackathon writeup retrieval** — rules, rubrics, MCP tool chain
- **MCP server setup** — 66 Kaggle tools for AI agents (Claude Code, Cursor, Gemini CLI)
- **Platform knowledge** — hardware quotas, GPU/TPU specs, progression tiers

### Module B — Notebook Deploy Pipeline *(unique to this skill)*
- Push any `.ipynb` to Kaggle with one command
- Monitor kernel status in real time (polls every 60s)
- **Auto-fix 11 common errors** and retry automatically (up to 10×)
- **1%-test-first strategy**: verifies full pipeline is runnable with 500 samples before committing to a full run
- OOM guard: skips heavy optional runners on test runs
- Download outputs on completion

---

## Quick Start

### Install (Claude Code)
```bash
claude install-skill https://github.com/hammadshakeelai/kaggle-run-skill
```

### Install (skills.sh — works with Cursor, Gemini CLI, Codex, and 35+ agents)
```bash
npx skills add hammadshakeelai/kaggle-run-skill
```

### Manual Install
```bash
# Global (all projects)
cp -r skills/kaggle-run ~/.claude/skills/

# Project-only
cp -r skills/kaggle-run .claude/skills/
```

---

## Usage

```
/kaggle-run                                        # interactive menu (10 options)
/kaggle-run my_notebook.ipynb                      # deploy notebook (auto-detect kernel)
/kaggle-run myuser/my-kernel                       # deploy to specific kernel
/kaggle-run notebook.ipynb myuser/kernel --sample 500    # 0.5% test run
/kaggle-run notebook.ipynb myuser/kernel --sample 100000 # full run
/kaggle-run --mode compete                         # competition report + submission
/kaggle-run --mode dataset titanic                 # search & download dataset
/kaggle-run --mode model google/gemma              # download model via kagglehub
/kaggle-run --mode publish                         # publish dataset/model/notebook
/kaggle-run --mode badge                           # badge automation (55 badges)
/kaggle-run --mode hackathon kaggle-measuring-agi  # retrieve hackathon writeups
/kaggle-run --mode mcp                             # configure MCP server
```

---

## Badge Automation (55 Badges, 5 Phases)

The badge collector covers all automatable Kaggle badges:

| Phase | Name | Badges | Time |
|---|---|---|---|
| 1 | Instant API | ~16 | 5-10 min |
| 2 | Competition | ~7 | 10-15 min |
| 3 | Pipeline | ~3 | 15-30 min |
| 4 | Browser | ~8 | 5-10 min |
| 5 | Streaks | ~4 | Setup only |

Phase 1 gets you `python_coder`, `api_notebook_creator`, `dataset_creator`, `api_dataset_creator`, `model_creator`, `api_model_creator`, and 10+ more — all in one session.

---

## Auto-Fix Error Recovery

When the kernel errors, the skill automatically:

1. Downloads the log
2. Matches the error against the fix table
3. Patches the notebook JSON
4. Re-pushes and resumes monitoring

Errors handled automatically:

| Error | Fix Applied |
|---|---|
| `SyntaxError: unterminated string literal` | Removes stray `"` after closing `)` |
| `NameError: 'runtime_environment'` | Restores deleted variable definition |
| `KeyError: 'archive_path'` | Adds missing keys to fallback result dict |
| `FileNotFoundError` (hardcoded dataset path) | Replaces with `_ds_root()` dynamic lookup |
| `FileNotFoundError` in `_ds_root` | Adds `/kaggle/input/datasets/` as search root |
| `ValueError: 'attack' is not in list` | Uses flexible positive-class lookup |
| `AssertionError` on label checks | Converts hard asserts to soft warnings |
| `NameError: 'canonical_raw_replay_df'` | Inserts missing execution cell |
| Disk space / OOM / `Killed` | Reduces sample size, adds disk guard |
| `No module named X` | Inserts `%pip install -q X` cell |
| CUDA out of memory | Clears GPU cache before training |

---

## 1%-Test Strategy

Before a full run (which can take hours), the skill pushes a **500-sample version** to verify the entire pipeline end-to-end in ~2 minutes.

```
You:   /kaggle-run notebook.ipynb myuser/kernel
Skill: Running 500-sample test (v1)...
Skill: Test PASSED in 2m 14s. Push full 100K run? [Yes/No]
You:   Yes
Skill: Pushing full run (v2)...
Skill: COMPLETE. Downloaded 3 output files to kaggle_outputs/
```

---

## Credential Support

Both Kaggle credential formats are supported:

| Method | How to Get |
|---|---|
| `KAGGLE_API_TOKEN` env var | kaggle.com/settings → "Generate New Token" |
| `~/.kaggle/access_token` | Same token saved to file |
| `~/.kaggle/kaggle.json` | Legacy: "Create Legacy API Key" |
| `KAGGLE_USERNAME` + `KAGGLE_KEY` | Legacy key pair env vars |

---

## MCP Server (66 Tools)

Configure Kaggle's official MCP server for AI agent integration:

```bash
# Claude Code
claude mcp add kaggle --transport http https://www.kaggle.com/mcp \
  --header "Authorization: Bearer <your_api_token>"
```

```json
// Cursor / Gemini CLI / Claude Desktop
{
  "mcpServers": {
    "kaggle": {
      "url": "https://www.kaggle.com/mcp",
      "headers": { "Authorization": "Bearer <your_api_token>" }
    }
  }
}
```

---

## Standalone CLI

Use `kaggle_deploy.py` without an AI agent:

```bash
pip install kaggle
python kaggle_deploy.py --notebook notebook.ipynb --kernel myuser/my-kernel --sample 500
```

Options:
```
--notebook     Path to .ipynb file
--kernel       Kaggle kernel ID (username/name)
--push-dir     Directory with kernel-metadata.json (default: kaggle_push_<slug>/)
--sample       Rows per dataset (default: full)
--output-dir   Download outputs here (default: kaggle_outputs/)
--log-dir      Download logs here (default: kaggle_logs/)
--monitor-only Skip push, just monitor current run
--poll         Status check interval in seconds (default: 60)
--max-wait     Max monitoring time in seconds (default: 7200)
```

---

## Compared to shepsci/kaggle-skill

| Feature | shepsci/kaggle-skill v2.3 | kaggle-run-skill v3.0 |
|---|---|---|
| Competition reports | ✅ | ✅ |
| Dataset downloads (CLI) | ✅ | ✅ |
| Dataset downloads (kagglehub) | ✅ | ✅ |
| Model downloads (CLI + kagglehub) | ✅ | ✅ |
| Publishing (datasets/models/notebooks) | ✅ | ✅ |
| Competition submissions | ✅ | ✅ |
| Badge automation (55 badges / 5 phases) | ✅ | ✅ |
| Hackathon writeup retrieval | ✅ | ✅ |
| MCP server (66 tools) | ✅ | ✅ |
| 35+ agent compatibility | ✅ | ✅ |
| API token + legacy credentials | ✅ | ✅ |
| Platform knowledge (GPU/TPU/quotas) | ✅ | ✅ |
| Notebook deploy + monitor | ❌ | ✅ |
| Auto-fix error recovery (11 patterns) | ❌ | ✅ |
| 1%-test-first strategy | ❌ | ✅ |
| OOM guard on test runs | ❌ | ✅ |
| Disk-space guard | ❌ | ✅ |
| Retry loop (up to 10×) | ❌ | ✅ |
| Standalone CLI (`kaggle_deploy.py`) | ❌ | ✅ |
| Windows compatible | Partial | ✅ |

---

## File Structure

```
kaggle-run-skill/
├── README.md                    # This file
├── LICENSE                      # MIT
├── skills/
│   └── kaggle-run/
│       └── SKILL.md             # Main skill definition (Claude Code + skills.sh format)
└── kaggle_deploy.py             # Standalone CLI script
```

---

## Requirements

- Python 3.10+
- `pip install kaggle` (official Kaggle CLI)
- A Kaggle account with an API token (kaggle.com/settings)

**Optional:**
- `pip install kagglehub` — for Python download API
- `pip install kagglehub[pandas-datasets]` — for direct DataFrame loading

---

## Security

- Credentials are never logged or echoed
- Kaggle-returned content is treated as untrusted (never executed)
- Dataset slugs are validated before shell use
- All created resources default to private (`is_private: true`)
- Rate limits respected: HTTP 429 → wait and retry, not loop

---

## License

MIT — see [LICENSE](LICENSE)

---

## Credits

- **Module A**: Built on [shepsci/kaggle-skill v2.3](https://github.com/shepsci/kaggle-skill) (MIT) — comprehensive Kaggle platform integration
- **Module B**: Deploy pipeline built through iterative debugging of real Kaggle kernel errors
- **Platform knowledge**: Sourced from [kaggle.com/docs](https://www.kaggle.com/docs)
- Compatible with the [skills.sh](https://skills.sh) cross-agent skill format
