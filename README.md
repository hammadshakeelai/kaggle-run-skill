# kaggle-run-skill v2.0

> **The most complete Kaggle slash command for AI coding agents.**  
> Combines full Kaggle platform integration with automated notebook deployment, error recovery, and output download — in one skill.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Works with Claude Code](https://img.shields.io/badge/Claude%20Code-Compatible-blue)](https://claude.ai/code)
[![Skills.sh Compatible](https://img.shields.io/badge/skills.sh-compatible-green)](https://skills.sh)

---

## What It Does

`/kaggle-run` is a two-in-one skill:

### Module A — Full Kaggle Integration
- Set up Kaggle credentials
- Competition landscape reports & leaderboard checks
- Dataset and model search & download
- Badge automation guide

### Module B — Notebook Deploy Pipeline *(unique to this skill)*
- Push a `.ipynb` to Kaggle with one command
- Monitor kernel status in real time (polls every 60s)
- **Auto-fix 10+ common errors** and retry automatically (up to 10×)
- **1%-test-first strategy**: verifies the full pipeline is runnable with 500 samples before committing to a full run
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
/kaggle-run                                        # interactive menu
/kaggle-run my_notebook.ipynb                      # deploy notebook (auto-detect kernel)
/kaggle-run myuser/my-kernel                       # deploy to specific kernel
/kaggle-run notebook.ipynb myuser/kernel --sample 500   # 0.5% test run
/kaggle-run notebook.ipynb myuser/kernel --sample 100000  # full run
/kaggle-run --mode compete                         # competition workflow
/kaggle-run --mode dataset titanic                 # search & download dataset
/kaggle-run --mode badge                           # badge automation guide
```

---

## Auto-Fix Error Recovery

When the kernel errors, the skill automatically:

1. Downloads the log
2. Matches the error against a fix table
3. Patches the notebook JSON
4. Re-pushes and resumes monitoring

Errors handled automatically:

| Error | Fix Applied |
|---|---|
| `SyntaxError: unterminated string literal` | Removes stray `"` after closing `)` |
| `NameError: 'runtime_environment'` | Restores deleted variable definition |
| `KeyError: 'archive_path'` | Adds missing keys to fallback result dict |
| `FileNotFoundError` (hardcoded dataset path) | Replaces with `_ds_root()` dynamic lookup |
| `ValueError: 'attack' is not in list` | Uses flexible positive-class lookup |
| `AssertionError` on label checks | Converts hard asserts to soft warnings |
| Disk space exceeded | Reduces sample size, adds disk guard |
| `No module named X` | Inserts `%pip install -q X` cell |
| CUDA out of memory | Clears GPU cache before training |

---

## 1%-Test Strategy

Before committing to a full run (which can take hours), the skill first pushes a **500-sample version** of your notebook. This verifies the entire pipeline is runnable end-to-end in ~2 minutes. Once that passes, it scales up to full sample size automatically.

```
You: /kaggle-run notebook.ipynb myuser/kernel
Skill: Running 500-sample test (v1)...
Skill: Test PASSED in 2m 14s. Push full 100K run? [Yes/No]
You: Yes
Skill: Pushing full run (v2)...
Skill: COMPLETE. Downloaded 3 output files to kaggle_outputs/
```

---

## Standalone CLI

Also included: `kaggle_deploy.py` for use without an AI agent.

```bash
pip install kaggle
python kaggle_deploy.py --notebook notebook.ipynb --kernel myuser/my-kernel --sample 500
```

Options:
```
--notebook   Path to .ipynb file
--kernel     Kaggle kernel ID (username/name)
--push-dir   Directory with kernel-metadata.json (default: kaggle_push_<slug>/)
--sample     Rows per dataset (default: full)
--output-dir Download outputs here (default: kaggle_outputs/)
--log-dir    Download logs here (default: kaggle_logs/)
--monitor-only  Skip push, just monitor current run
--poll       Status check interval in seconds (default: 60)
--max-wait   Max monitoring time in seconds (default: 7200)
```

---

## Compared to shepsci/kaggle-skill (v1 reference)

| Feature | shepsci/kaggle-skill (v1) | kaggle-run-skill (v2) |
|---|---|---|
| Competition reports | ✅ | ✅ |
| Dataset downloads | ✅ | ✅ |
| Badge automation | ✅ | ✅ |
| MCP server (66 tools) | ✅ | via kagglehub |
| 35+ agent compatibility | ✅ | ✅ |
| Notebook deploy + monitor | ❌ | ✅ |
| Auto-fix error recovery | ❌ | ✅ (10+ patterns) |
| 1%-test-first strategy | ❌ | ✅ |
| Disk-space guard | ❌ | ✅ |
| Retry loop (up to 10×) | ❌ | ✅ |
| Standalone CLI | ❌ | ✅ |
| Windows compatible | Partial | ✅ |

---

## File Structure

```
kaggle-run-skill/
├── README.md                    # This file
├── LICENSE
├── skills/
│   └── kaggle-run/
│       └── SKILL.md             # Main skill definition (Claude Code format)
└── kaggle_deploy.py             # Standalone CLI script
```

---

## Requirements

- Python 3.8+
- `pip install kaggle` (official Kaggle CLI)
- A Kaggle account with API token at `~/.kaggle/kaggle.json`

---

## Security

- Credentials are never logged or echoed
- Kaggle-returned content is treated as untrusted
- Dataset slugs are validated before shell use

---

## License

MIT — see [LICENSE](LICENSE)

---

## Credits

- Inspired by [shepsci/kaggle-skill](https://github.com/shepsci/kaggle-skill) (Module A base design)
- Module B (deploy pipeline) built through iterative debugging of real Kaggle kernel errors
- Compatible with the [skills.sh](https://skills.sh) cross-agent skill format
