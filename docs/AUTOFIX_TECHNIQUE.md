# Autonomous Kaggle Notebook Execution — Technique & Future Work

This document captures the end-to-end technique developed for running complex Jupyter notebooks on Kaggle fully autonomously — including push, monitoring, error detection, surgical notebook patching, and re-push — with zero human intervention per iteration.

---

## The Core Technique: Autonomous Fix Loop

### Problem Statement

Running a large multi-stage research notebook on Kaggle is painful because:

- Kaggle runs asynchronously — you push, wait 5–90 min, then discover one error
- Each error reveals a new error downstream — it's whack-a-mole without the full run
- OOM kills produce no Python traceback — just `DeadKernelError: Kernel died`
- Fix-and-retry cycles eat Kaggle GPU quota (30h/week)
- Notebooks contain thousands of lines — finding the right line to patch is slow

The technique solves all of these with a single background script: **push → poll → download log → parse stderr → surgical JSON patch → push → repeat**.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Local machine (background Python script)                    │
│                                                              │
│  poll_until_done()  ──► get_status() via kaggle CLI          │
│       │                                                      │
│  status=error                                                │
│       │                                                      │
│  download_log(v)  ──► kaggle kernels output                  │
│       │                                                      │
│  extract_error()  ──► parse NDJSON log → find stderr lines   │
│       │                                                      │
│  apply_fix()      ──► match error → patch notebook JSON      │
│       │                                                      │
│  save_nb() + push_nb()  ──► kaggle kernels push              │
│       │                                                      │
│  poll_until_done() for new version  ──► loop                 │
│                                                              │
│  status=complete                                             │
│       │                                                      │
│  patch PHASE1_SAMPLE to 100k → push full run                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Two-Phase Execution Strategy

### Phase 1: Tiny Test Run (50–1000 samples)

The key insight: a notebook that runs to completion with stubs is infinitely more useful than one that OOMs at cell 60 out of 130.

**Mechanism:**

```python
# In the notebook's "suite gate" cell:
_RUN_SAMPLE = (LIVE_REPLAY_CONFIG.get('sample_per_dataset') or PHASE1_SAMPLE_PER_DATASET) \
    if 'LIVE_REPLAY_CONFIG' in dir() else PHASE1_SAMPLE_PER_DATASET

if IS_KAGGLE and _RUN_SAMPLE <= 1000:
    # Stub path: define all expected DataFrames as synthetic data
    # Skips all heavy ML (RL, DQL, ensemble search, OT alignment)
    canonical_raw_replay_df = pd.DataFrame(stub_rows)
    live_lodo_df = pd.DataFrame(...)
    # ... all downstream variables stubbed
    print("[Suite] stubs initialised (test run)")
else:
    # Full path: run all replay functions with real data
    canonical_raw_replay_df = run_canonical_paper_replay_from_raw(
        sample_per_dataset=_RUN_SAMPLE, ...
    )
```

This pattern means:
- All 130 cells execute successfully at 50 samples (~6 min)
- Every variable is defined — no `NameError` on plotting/reporting cells
- No real data loaded — no OOM
- All the fix iterations happen fast (6 min/cycle vs 90 min/cycle)

### Phase 2: RAM-Safe Full Run (5,000–100,000 samples)

Only pushed after Phase 1 completes cleanly. Apply dataset size caps before the full run:

```python
# In load_raw_paper_frames():
# Cap BoT-IoT to 20 representative files (was 999 → caused OOM on 14GB dataset)
bot_paths = select_representative_files(sorted(bot_root.glob("**/*.csv")), max_files=20)
# Cap N-BaIoT to 40 files
nb_paths = sorted(nb_root.glob("**/*.csv"))[:40]
```

---

## The Log Parsing Pattern

Kaggle kernel logs are newline-delimited JSON (NDJSON), each line like:
```json
{"stream_name": "stderr", "data": "Traceback (most recent call last):\n"}
```

Extracting the error:
```python
def extract_error(log_text):
    lines = []
    for raw in log_text.strip().split("\n"):
        raw = raw.lstrip(",").strip()
        try:
            obj = json.loads(raw)
            if obj.get("stream_name") == "stderr":
                lines.append(obj["data"])
        except Exception:
            pass
    stderr = "".join(lines)
    m = re.search(
        r"(KeyError|NameError|ValueError|TypeError|AttributeError|ImportError"
        r"|IndexError|AssertionError|FileNotFoundError|RuntimeError):\s*(.+)",
        stderr,
    )
    return (m.group(0).strip() if m else stderr[-500:]), stderr
```

**Critical:** The log filename is derived from the kernel slug — `"username/kernel-name"` → `"kernel-name.log"`. Always derive it programmatically rather than hardcoding.

---

## Error Patterns & Fixes Discovered

### 1. OOM: `DeadKernelError: Kernel died` with no Python traceback

**Root cause:** Linux OOM killer terminates the kernel process. No Python exception is raised.

**Detection:**
```python
if "DeadKernelError" in full_stderr or "Kernel died" in full_stderr:
    # OOM — look at stdout to find the last print before death
```

**Stdout tells you where it died:**
```
[Suite] FULL RUN - executing all replay functions ...
[Suite] Starting canonical binary paper replay ...
← Kernel died here (during load_raw_paper_frames)
```

**Fix strategy:**
- If died during data loading → cap file glob (`max_files=20`)
- If died during ML training → add `PHASE1_SAMPLE_PER_DATASET <= 1000` guard around that cell

---

### 2. `_RUN_SAMPLE = None` → Full run triggered at 50 samples

**Root cause:** `LIVE_REPLAY_CONFIG` dict has `sample_per_dataset: null`. Python's `.get(key, default)` only uses the default when the key is **absent** — if the key is present with value `None`, it returns `None`.

```python
# BUG:
_RUN_SAMPLE = LIVE_REPLAY_CONFIG.get('sample_per_dataset', PHASE1_SAMPLE_PER_DATASET)
# → returns None if key exists with None value
# → None <= 1000 raises TypeError or evaluates False → full run path

# FIX:
_RUN_SAMPLE = (LIVE_REPLAY_CONFIG.get('sample_per_dataset') or PHASE1_SAMPLE_PER_DATASET)
# → None or 50 → 50 → stub path triggered correctly
```

**Rule:** Always use `or fallback` for config values that can be explicitly `None`.

---

### 3. `KeyError: 'benign'` / `KeyError: 'malicious'` in classification report

**Root cause:** With 50 samples, stratified sampling may produce a slice with only one class. `classification_report(..., output_dict=True)` then omits the missing class entirely.

**Fix:**
```python
# BUG:
return {label: float(report[label]["f1-score"]) for label in ["malicious", "benign"]}

# FIX:
return {label: float((report.get(label) or {}).get("f1-score", 0.0))
        for label in ["malicious", "benign"]}
```

---

### 4. `ValueError: At least one label specified must be in y_true`

**Root cause:** Datasets label attacks as `"malicious"` but code expects `"attack"`. The positive-class string mismatch means both y_true and y_pred use different strings.

**Fix — normalise at the entry point:**
```python
# Normalise before scoring:
y_true = np.where(np.isin(y_true, ["malicious", "attack"]), "attack", "benign")
y_pred = np.where(attack_scores >= threshold, "attack", "benign")

# Also make confusion_matrix labels dynamic:
confusion_matrix(
    y_true, y_pred,
    labels=[l for l in ["benign", "attack"] if l in set(y_true) | set(y_pred)]
).tolist()
```

---

### 5. `NameError: name 'live_feature_coverage_df' is not defined`

**Root cause:** Suite gate stub cell didn't define every variable downstream cells reference. Each new variable discovered this way requires adding it to the stub.

**Auto-fix pattern:**
```python
# Inject stub before the suite gate's final print:
stub = f"    {varname} = {{}}  # auto-stub\n    "
# Insert before: print("[Suite] All suite DataFrames ... initialised")
```

**Note:** Use `{}` (empty dict), not `pd.DataFrame()` — `pd` may not be in scope at injection point.

---

### 6. `IndentationError` from auto-stub injection

**Root cause:** Auto-injected stub string had wrong indentation relative to surrounding code. The inserted line started at the wrong column.

**Prevention:** Always match the indentation of the marker line being replaced:
```python
# The marker is indented 4 spaces → stub must also be indented 4 spaces
stub = f"    {varname} = {{}}  # auto-stub\n    "
```

---

### 7. `BoT-IoT glob causes OOM even before loading any data`

**Root cause:** `sorted(bot_root.glob("**/*.csv"))` on a 14GB dataset directory with thousands of CSVs creates a massive in-memory list. The glob itself OOMs before a single row is read.

**Fix:**
```python
# Stream only the first 20 representative files
all_paths = sorted(bot_root.glob("**/*.csv"))  # still loads path list
bot_paths = select_representative_files(all_paths, max_files=20)
```

For truly massive directories (millions of files), use `itertools.islice` on the glob generator instead of `sorted()`.

---

### 8. `col_m` catch-all fires on KeyErrors already handled

**Root cause:** The generic `KeyError: 'col_name'` rule fires on every `KeyError`, including ones where the earlier specific rules (`per_class_f1`, `attack_idx`) already detected and attempted a fix. If the specific fix found no target, it fell through to the generic rule which then patched the wrong cell.

**Fix:** Add `return False` after specific rules fail to patch their target:
```python
if re.search(r"KeyError: '(benign|malicious|attack)'", error_line):
    idx, src = find_cell(nb, "def per_class_f1")
    if idx >= 0:
        # ... attempt fix ...
        if patch_cell(...): return True
    return False  # ← don't fall through to generic KeyError handler
```

---

### 9. `missing_cols` overwrite bug

**Root cause:** Two independent regex patterns both write to `missing_cols`, but the second overwrites the first instead of extending it.

```python
# BUG:
if col_m:    missing_cols = [col_m.group(1)]
if col_m2:   missing_cols = re.findall(...)  # silently discards col_m

# FIX:
if col_m:    missing_cols = [col_m.group(1)]
if col_m2:   missing_cols.extend(re.findall(...))
```

---

### 10. Full-run patch hits markdown cells

**Root cause:** Scanning all cells for `PHASE1_SAMPLE_PER_DATASET` and patching the first match can hit a markdown documentation cell containing the string in a code example.

**Fix:**
```python
for i, cell in enumerate(nb["cells"]):
    if cell.get("cell_type") != "code":  # ← guard added
        continue
    src = "".join(cell.get("source", []))
    if "PHASE1_SAMPLE_PER_DATASET" in src:
        # patch
```

---

## The `patch_cell` Abstraction

Every fix branch needs the same 3-line ending. Extract it:

```python
def patch_cell(nb, idx, src, new_src, label):
    if new_src != src:
        nb["cells"][idx]["source"] = [new_src]
        print(f"  Fix: {label}", flush=True)
        return True
    return False
```

Similarly, many fix rules need a two-step cell lookup ("try pattern A, fall back to pattern B"):

```python
def find_cell_any(nb, patterns):
    for p in patterns:
        idx, src = find_cell(nb, p)
        if idx >= 0:
            return idx, src
    return -1, ""
```

---

## Complete Fix Rule Architecture

The final `apply_fix` function structure — ordered by specificity (most specific first, catch-alls last):

```
1. KeyError: 'benign'/'malicious'/'attack'  → per_class_f1 .get() fix  [return False if not matched]
2. "At least one label"                     → label normalisation
3. "Only one class in y_true"               → roc_auc single-class guard
4. (ValueError|KeyError).*attack            → flexible attack_idx       [return False if not matched]
5. KeyError: 'col_name' / Columns not found → stub column injection      [extend, not overwrite]
6. NameError: 'varname'                     → stub variable injection
7. No module named 'X'                      → pip install cell
8. GaussianMixture / sum(pvals)             → GMM covariance fix
```

---

## Configuration Constants Pattern

Replace magic strings with module-level constants — they appear in multiple fix rules and must stay in sync:

```python
SUITE_GATE = "Suite execution gate"   # cell-finder pattern
SUITE_GATE_FALLBACK = "_stub_rows"    # fallback if gate was renamed
LOG_FILENAME = KERNEL.split("/")[1] + ".log"  # derived, never diverges
```

---

## VERSION as Plain Global

```python
# AVOID — list-as-mutable-global anti-pattern:
VERSION = [33]
def push_nb():
    VERSION[0] += 1

# PREFER — explicit global:
VERSION = 33
def push_nb():
    global VERSION
    VERSION += 1
```

---

## Future Work

### Short Term

1. **OOM detection from stdout** — parse the last stdout line before `DeadKernelError` to identify which function caused the OOM, then automatically add an OOM guard to that specific cell.

2. **`itertools.islice` glob** — replace `sorted(dir.glob("**/*.csv"))` with a generator-based approach to avoid in-memory path lists on massive directories.

3. **Incremental fix loop with cell-level re-run** — instead of re-running the entire notebook on each fix, use Kaggle's cell-level execution API (if/when available) to only re-run from the failing cell onward.

4. **Per-rule confidence scores** — track how many times each fix rule fires and succeeds vs. makes things worse. Rules that fail more than they succeed should be deprioritised or disabled automatically.

5. **Diff-based push** — only push cells that actually changed (Kaggle still runs the full notebook, but the push payload is smaller and less likely to be throttled).

### Medium Term

6. **LLM-generated fix rules** — when no rule matches, send the stderr + surrounding cell source to an LLM and ask it to generate a fix. Apply the suggested fix as a new auto-fix rule candidate. Persist accepted rules back to the fix library.

7. **Multi-version parallel testing** — push N variants simultaneously (different sample sizes, different fix hypotheses) and take the first one that completes. Requires coordinating across Kaggle's per-user concurrent kernel limit (typically 2).

8. **Semantic cell fingerprinting** — instead of string-matching cell content to find the right cell to patch, compute a semantic embedding of each cell's purpose. More robust to minor rewrites and cell reordering.

9. **Notebook dependency graph** — build a DAG of which cells depend on which variables. When a fix touches cell X, automatically identify all downstream cells that may be affected and validate them before pushing.

10. **Resource-adaptive sample sizing** — query Kaggle hardware before running. If T4 (16GB VRAM), use one sample budget; if A100 (40GB), use a larger budget. Automatically find the largest sample size that fits in memory for the given hardware.

### Long Term

11. **Cross-kernel learning** — share the fix rule library across different notebooks/projects. A fix that worked for `KeyError: 'benign'` in one notebook should be available as a candidate for any other notebook hitting the same error.

12. **Automatic suite gate generation** — given a notebook with no stub/test mode, automatically insert a suite gate cell that stubs all heavy computations. Requires static analysis of the notebook to identify which cells are "heavy" (contain model training, large data loads, etc.).

13. **Regression testing** — after a successful full run, store a "golden" output checksum. On subsequent runs, compare outputs and alert if key metrics deviate beyond a threshold.

14. **Fix rule DSL** — replace the imperative fix functions with a declarative DSL:
    ```yaml
    - name: per_class_f1_missing_key
      triggers:
        - pattern: "KeyError: '(benign|malicious|attack)'"
      target_cell: "def per_class_f1"
      patch:
        find: 'float(report[label]["f1-score"])'
        replace: 'float((report.get(label) or {}).get("f1-score", 0.0))'
      on_no_target: return_false  # don't fall through
    ```

15. **Kaggle MCP integration** — use Kaggle's official MCP server (66 tools) instead of CLI subprocess calls for status, output, and push. Removes the shell=True subprocess pattern and enables proper error handling via structured API responses.

---

## References

- [Kaggle Kernels API docs](https://www.kaggle.com/docs/api#kernels)  
- [Papermill execution model](https://papermill.readthedocs.io/en/latest/)  
- [nbclient / nbconvert](https://nbclient.readthedocs.io/)  
- `kaggle_autofix_loop.py` — the reference implementation in this project
