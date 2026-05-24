# kaggle-run-skill v4.0

> **The ultimate Kaggle slash command for AI coding agents.**  
> Token-minimal: ~150-line router skill + 7 fat Python scripts that handle all the work.  
> Deploy notebooks, auto-fix 13 error patterns, compete, earn badges, analyze leaderboards.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Works with Claude Code](https://img.shields.io/badge/Claude%20Code-Compatible-blue)](https://claude.ai/code)
[![Skills.sh Compatible](https://img.shields.io/badge/skills.sh-compatible-green)](https://skills.sh)

---

## Architecture: Thin Skill + Fat Scripts

```
skills/kaggle-run/
├── SKILL.md          ← ~150-line router (what LLM reads at invocation)
└── scripts/
    ├── kaggle_deploy.py      ← B pipeline: push→monitor→autofix→download
    ├── kaggle_compete.py     ← competitions: report, download, submit, scaffold
    ├── kaggle_badges.py      ← 55 badges across 5 phases
    ├── kaggle_datasets.py    ← datasets: search, download, publish
    ├── kaggle_models.py      ← models: search, download, publish
    ├── kaggle_leaderboard.py ← leaderboard pull + statistical analysis
    └── kaggle_creds.py       ← credential check + MCP server config
```

**v3 → v4 token reduction:** SKILL.md went from 700 lines → 150 lines. The LLM reads 150 lines, calls one script, gets structured output. All fix logic, badge automation, and platform knowledge live in Python — zero LLM retry waste.

---

## What It Does

### Module A — Full Kaggle Platform
- **Credentials** — API token (new) + legacy `kaggle.json`, both supported
- **Competitions** — report, leaderboard analysis, data download, submission workflow, auto-submit pipeline
- **Datasets** — search, download (CLI + kagglehub), publish, version
- **Models** — search, download (CLI + kagglehub), publish
- **Badge automation** — 55 badges across 5 phases (~38 fully automatable)
- **Hackathon writeups** — rules, rubrics, MCP tool chain
- **MCP server** — 66 Kaggle tools for AI agents
- **Leaderboard analysis** — medal zone thresholds, score distribution, CSV export

### Module B — Notebook Deploy Pipeline
- Push any `.ipynb` to Kaggle with one command
- Monitor kernel status (polls every 60s, 2-hour cap)
- **Auto-fix 13 error patterns** and retry (up to 10×)
- **1%-test-first**: verify pipeline runs at 500 samples before full run
- Parallel multi-size sweep: push 3 kernels simultaneously
- OOM + disk-space guards built in

---

## Installation

### Claude Code (recommended)
```bash
claude install-skill https://github.com/hammadshakeelai/kaggle-run-skill
```

### Git clone (Mac / Linux)
```bash
git clone https://github.com/hammadshakeelai/kaggle-run-skill.git
cp -r kaggle-run-skill/skills/kaggle-run ~/.claude/skills/
```

### Git clone (Windows PowerShell)
```powershell
git clone https://github.com/hammadshakeelai/kaggle-run-skill.git
Copy-Item -Recurse kaggle-run-skill\skills\kaggle-run "$env:USERPROFILE\.claude\skills\"
```

### skills.sh — Cursor, Gemini CLI, Codex, Windsurf, 35+ agents
```bash
npx skills add hammadshakeelai/kaggle-run-skill
```
> Scripts auto-download from GitHub on first `/kaggle-run` invocation (one-time, ~5s).

### curl one-liner (Mac / Linux)
```bash
mkdir -p ~/.claude/skills/kaggle-run/scripts
BASE="https://raw.githubusercontent.com/hammadshakeelai/kaggle-run-skill/main/skills/kaggle-run"
curl -fsSL "$BASE/SKILL.md" -o ~/.claude/skills/kaggle-run/SKILL.md
for s in kaggle_deploy kaggle_compete kaggle_badges kaggle_datasets kaggle_models kaggle_leaderboard kaggle_creds; do
    curl -fsSL "$BASE/scripts/${s}.py" -o ~/.claude/skills/kaggle-run/scripts/${s}.py
done
```

---

## Usage

```
/kaggle-run                                             # interactive menu
/kaggle-run notebook.ipynb                              # deploy (auto-detect kernel)
/kaggle-run notebook.ipynb user/kernel --sample 500     # 500-sample test run
/kaggle-run notebook.ipynb user/kernel --full-run 100000  # test then full
/kaggle-run --mode compete                              # competition report
/kaggle-run --mode compete titanic --download           # download competition data
/kaggle-run --mode compete titanic --submit preds.csv   # submit predictions
/kaggle-run --mode dataset titanic                      # search & download dataset
/kaggle-run --mode model google/gemma                   # download model
/kaggle-run --mode publish                              # publish dataset/model
/kaggle-run --mode badge                                # badge automation
/kaggle-run --mode badge --phase 1                      # Phase 1 only (~16 badges)
/kaggle-run --mode leaderboard titanic --analyze        # leaderboard + stats
/kaggle-run --mode hackathon kaggle-measuring-agi       # hackathon writeup chain
/kaggle-run --mode mcp                                  # configure MCP server
/kaggle-run --mode submit titanic                       # auto-submit pipeline
```

---

## Standalone CLI (no AI agent)

```bash
pip install kaggle
# Deploy
python kaggle_deploy.py --nb notebook.ipynb --kernel user/name --sample 500
# Full pipeline (test then full)
python kaggle_deploy.py --nb notebook.ipynb --kernel user/name --sample 500 --full-run 100000
# Monitor only
python kaggle_deploy.py --kernel user/name --monitor-only
# Parallel sweep
python kaggle_deploy.py --nb notebook.ipynb --kernel user/name --parallel 25000,50000,100000
# Competition
python skills/kaggle-run/scripts/kaggle_compete.py --comp titanic --download
# Badges
python skills/kaggle-run/scripts/kaggle_badges.py --phase 1
# Leaderboard
python skills/kaggle-run/scripts/kaggle_leaderboard.py --comp titanic --analyze --thresholds
```

---

## Auto-Fix Error Recovery (13 patterns)

| Rule | Error | Fix |
|---|---|---|
| R1 | `KeyError: 'benign'/'malicious'/'attack'` | `per_class_f1` → `.get()` fallback |
| R2 | `ValueError: At least one label not in y_true` | Normalise y_true + dynamic label list |
| R3 | `ValueError: Only one class present` | `roc_auc_score` single-class guard |
| R4 | `ValueError/'attack' is not in list` | Flexible `attack_idx` via `next()` |
| R5 | `KeyError: '<col>'` (column) | Inject missing column stub |
| R6 | `NameError: name '<var>'` | Stub variable + restore `runtime_environment` |
| R7 | `No module named 'X'` | Prepend `%pip install -q X` |
| R8 | `SyntaxError: unterminated string literal` | Remove stray `"` after `)` |
| R9 | `DeadKernelError` / OOM / `MemoryError` | Cap glob to 20 files + disk guard |
| R10 | `CUDA out of memory` | `torch.cuda.empty_cache()` + halve batch |
| R11 | `KeyError: 'archive_path'` | Add missing keys to fallback dict |
| R12 | `FileNotFoundError` in `_ds_root` | Add `/kaggle/input/datasets/` search root |
| R13 | `AssertionError` on label checks | Convert hard asserts to soft `[WARN]` |

---

## Badge Automation (55 Badges, 5 Phases)

| Phase | Badges | Method | Time |
|---|---|---|---|
| 1 — Instant API | ~16 | Fully automated | ~10 min |
| 2 — Competition | ~7 | CLI commands | ~15 min |
| 3 — Pipeline | ~3 | API + CLI | ~30 min |
| 4 — Browser | ~8 | Manual (guided) | ~10 min |
| 5 — Streaks | ~4 | Time-based | Days |

Phase 1 fires automatically: `python_coder`, `r_coder`, `api_notebook_creator`, `dataset_creator`, `api_dataset_creator`, `model_creator`, `api_model_creator`, and 9 more — all in one `--phase 1` run.

---

## Leaderboard Analysis

```bash
python skills/kaggle-run/scripts/kaggle_leaderboard.py \
    --comp titanic --top 50 --analyze --thresholds --export lb.csv
```

Output: top scores, medal zone cutoffs (gold/silver/bronze), top-10% / top-25% / median thresholds.

---

## v3 → v4 Changes

| Feature | v3.0 | v4.0 |
|---|---|---|
| SKILL.md size | 700 lines | **~150 lines** |
| Logic location | Inline in SKILL.md | **Fat Python scripts** |
| Token burn at invocation | High (full 700 lines) | **Minimal (150 lines)** |
| Auto-fix patterns | 11 | **13** |
| Leaderboard analysis | ❌ | **✅** |
| Auto-submit pipeline | ❌ | **✅** |
| Competition scaffold | ❌ | **✅** |
| Parallel sweep | B-11 script (separate) | **Built-in `--parallel` flag** |
| scripts/ directory | ❌ | **✅ 7 scripts** |
| Bootstrap (skills.sh users) | ❌ | **✅ auto-download** |

---

## Compared to shepsci/kaggle-skill v2.3

| Feature | shepsci v2.3 | kaggle-run v4.0 |
|---|---|---|
| Competition reports | ✅ | ✅ |
| Dataset + model downloads | ✅ | ✅ |
| Publishing | ✅ | ✅ |
| Badge automation (55 badges) | ✅ | ✅ |
| Hackathon writeups | ✅ | ✅ |
| MCP server (66 tools) | ✅ | ✅ |
| Notebook deploy + monitor | ❌ | ✅ |
| Auto-fix error recovery | ❌ | ✅ (13 patterns) |
| 1%-test-first strategy | ❌ | ✅ |
| Parallel multi-size sweep | ❌ | ✅ |
| Leaderboard analysis | ❌ | ✅ |
| Auto-submit pipeline | ❌ | ✅ |
| Competition scaffold | ❌ | ✅ |
| Standalone scripts | ❌ | ✅ |
| Token-minimal SKILL.md | ❌ | ✅ (~150 lines) |
| Windows compatible | Partial | ✅ |

---

## Credential Support

| Method | Notes |
|---|---|
| `KAGGLE_API_TOKEN` env | Recommended — works with CLI ≥ 1.8, kagglehub ≥ 0.4.1, MCP |
| `~/.kaggle/access_token` | File-based equivalent |
| `~/.kaggle/kaggle.json` | Legacy; still works |
| `KAGGLE_USERNAME` + `KAGGLE_KEY` | Legacy env pair |

---

## MCP Server (66 Tools)

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

## Requirements

- Python 3.10+
- `pip install kaggle` — official Kaggle CLI
- A Kaggle account with API token (kaggle.com/settings)

**Optional:**
- `pip install kagglehub` — Python download API
- `pip install kagglehub[pandas-datasets]` — direct DataFrame loading

---

## Security

- Credentials never logged or echoed
- Kaggle-returned content treated as untrusted
- Slugs validated before shell use
- All created resources default to `is_private: true`
- HTTP 429 → 2-min backoff (not tight retry loop)

---

## License

MIT — see [LICENSE](LICENSE)

## Credits

- Module A base: [shepsci/kaggle-skill v2.3](https://github.com/shepsci/kaggle-skill) (MIT)
- Module B: Deploy pipeline via iterative real-Kaggle-error debugging
- Architecture: Thin-router + fat-scripts pattern for token efficiency
