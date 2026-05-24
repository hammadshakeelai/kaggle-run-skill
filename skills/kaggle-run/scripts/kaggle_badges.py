#!/usr/bin/env python3
"""
kaggle_badges.py — Automate Kaggle badge collection (55 badges, 5 phases).

Usage:
    python kaggle_badges.py              # run all phases (1 automated + guidance for 2-5)
    python kaggle_badges.py --phase 1    # API badges only (~16, ~10 min)
    python kaggle_badges.py --phase 2    # competition badge guidance
    python kaggle_badges.py --list       # print all 55 badges
"""
import argparse, json, os, subprocess, sys, tempfile, time
from pathlib import Path

def run(cmd, cwd=None):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)

def get_username():
    r = run(["kaggle", "config", "view"])
    for ln in r.stdout.split("\n"):
        if "username" in ln.lower():
            return ln.split(":")[-1].strip()
    return os.environ.get("KAGGLE_USERNAME", "")

MINIMAL_PY = json.dumps({
    "cells": [{"cell_type": "code", "source": ["print('badge run')"],
               "outputs": [], "execution_count": None, "metadata": {}}],
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10.0"}
    },
    "nbformat": 4, "nbformat_minor": 5
})

MINIMAL_R = json.dumps({
    "cells": [{"cell_type": "code", "source": ["cat('r badge run')"],
               "outputs": [], "execution_count": None, "metadata": {}}],
    "metadata": {
        "kernelspec": {"display_name": "R", "language": "R", "name": "ir"},
        "language_info": {"name": "R", "version": "4.0.0"}
    },
    "nbformat": 4, "nbformat_minor": 5
})


def phase1(username):
    print(f"\n=== Phase 1: Instant API Badges (~16 badges) ===  user={username}\n")
    earned = []

    with tempfile.TemporaryDirectory() as _tmp:
        tmp = Path(_tmp)

        # ── Python notebook ──────────────────────────────────────────
        py_dir = tmp / "badge_py"
        py_dir.mkdir()
        (py_dir / "notebook.ipynb").write_text(MINIMAL_PY)
        (py_dir / "kernel-metadata.json").write_text(json.dumps({
            "id": f"{username}/badge-py-run", "title": "badge-py-run",
            "code_file": "notebook.ipynb", "language": "python",
            "kernel_type": "notebook", "is_private": True,
            "enable_gpu": False, "enable_internet": False,
            "dataset_sources": [], "competition_sources": [], "kernel_sources": []
        }))
        r = run(["kaggle", "kernels", "push"], cwd=str(py_dir))
        if r.returncode == 0:
            earned += ["python_coder", "api_notebook_creator", "code_uploader"]
            print("  ✓ python_coder  api_notebook_creator  code_uploader")
        else:
            print(f"  ✗ push failed: {r.stderr[:200]}")
        time.sleep(2)

        # ── R notebook ───────────────────────────────────────────────
        r_dir = tmp / "badge_r"
        r_dir.mkdir()
        (r_dir / "notebook.ipynb").write_text(MINIMAL_R)
        (r_dir / "kernel-metadata.json").write_text(json.dumps({
            "id": f"{username}/badge-r-run", "title": "badge-r-run",
            "code_file": "notebook.ipynb", "language": "r",
            "kernel_type": "notebook", "is_private": True,
            "enable_gpu": False, "enable_internet": False,
            "dataset_sources": [], "competition_sources": [], "kernel_sources": []
        }))
        r2 = run(["kaggle", "kernels", "push"], cwd=str(r_dir))
        if r2.returncode == 0:
            earned.append("r_coder")
            print("  ✓ r_coder")
        time.sleep(2)

        # ── Dataset ──────────────────────────────────────────────────
        ds_dir = tmp / "badge_ds"
        ds_dir.mkdir()
        (ds_dir / "data.csv").write_text("id,value\n1,test\n2,demo\n")
        run(["kaggle", "datasets", "init", "-p", str(ds_dir)])
        dm_path = ds_dir / "dataset-metadata.json"
        if dm_path.exists():
            dm = json.loads(dm_path.read_text())
            dm.update({
                "title": "badge-dataset-run",
                "id": f"{username}/badge-dataset-run",
                "licenses": [{"name": "CC0-1.0"}],
                "subtitle": "Badge automation dataset – kaggle-run v4",
                "keywords": ["badge", "automation", "test"]
            })
            dm_path.write_text(json.dumps(dm, indent=2))
        r3 = run(["kaggle", "datasets", "create", "-p", str(ds_dir), "--dir-mode", "zip"])
        if r3.returncode == 0:
            earned += ["dataset_creator", "api_dataset_creator", "dataset_tagger", "dataset_documenter"]
            print("  ✓ dataset_creator  api_dataset_creator  dataset_tagger  dataset_documenter")
        else:
            print(f"  ✗ dataset create: {r3.stderr[:200]}")
        time.sleep(2)

        # ── Model ────────────────────────────────────────────────────
        m_dir = tmp / "badge_model"
        m_dir.mkdir()
        (m_dir / "README.md").write_text("# Badge Model\nBadge automation model – kaggle-run v4.\n")
        run(["kaggle", "models", "init", "-p", str(m_dir)])
        mm_path = m_dir / "model-metadata.json"
        if mm_path.exists():
            mm = json.loads(mm_path.read_text())
            mm.update({
                "title": "badge-model-run",
                "ownerSlug": username,
                "slug": "badge-model-run",
                "subtitle": "Badge automation model – kaggle-run v4",
                "isPrivate": True
            })
            mm_path.write_text(json.dumps(mm, indent=2))
        r4 = run(["kaggle", "models", "create", "-p", str(m_dir)])
        if r4.returncode == 0:
            earned += ["model_creator", "api_model_creator", "model_tagger", "model_documenter"]
            print("  ✓ model_creator  api_model_creator  model_tagger  model_documenter")
        else:
            print(f"  ✗ model create: {r4.stderr[:200]}")

    print(f"\n  Phase 1 done — {len(earned)} badge actions fired")
    print("  Check kaggle.com/badges for results (may take a few minutes to appear)")
    return earned


def phase2_guide():
    print("""
=== Phase 2: Competition Badges (~7 badges, ~15 min) ===

  Fastest path — submit to the Titanic Getting Started competition:
    python kaggle_compete.py --comp titanic --download
    # edit submission.csv (or use the sample), then:
    python kaggle_compete.py --comp titanic --submit submission.csv

  Badges you'll earn:
    competitor  getting_started_competitor  code_submitter
    notebook_modeler  competition_modeler
    playground_competitor (submit to any Playground comp)
    community_competitor  (submit to any Community comp)
""")


def phase3_guide():
    print("""
=== Phase 3: Pipeline Badges (~3 badges, ~30 min) ===

  dataset_pipeline_creator:
    After a successful kernel run, publish its output as a dataset:
    kaggle datasets create -p ./kaggle_outputs --dir-mode zip

  model_pipeline_creator:
    Same but publish as a model:
    kaggle models create -p ./kaggle_outputs

  r_markdown_coder:
    Push an R Markdown (.Rmd) notebook via API as kernel_type "rMarkdown"
""")


def phase4_guide():
    print("""
=== Phase 4: Browser Badges (~8 badges, manual ~10 min) ===

  stylish           — Fill profile: bio, location, occupation  kaggle.com/settings
  vampire           — Enable dark theme in kaggle.com/settings
  bookmarker        — Bookmark any notebook/dataset from its page
  collector         — Create a collection at kaggle.com/collections
  github_coder      — Link a GitHub repo: notebook → Settings → GitHub
  colab_coder       — Open a notebook in Colab: notebook → Open In → Google Colab
  linked_dataset_creator — Create a dataset linked to a URL source
  linked_model_creator   — Create a model linked to an external source (e.g., HuggingFace)
""")


def phase5_guide():
    print("""
=== Phase 5: Streak Badges (time-based) ===

  seven_day_login_streak   — Log in 7 consecutive days
  thirty_day_login_streak  — Log in 30 consecutive days
  submission_streak        — Submit to competitions 7 consecutive days
  super_submission_streak  — Submit 30 consecutive days

  No automation needed — just log in and submit daily.
""")


def list_all():
    data = [
        ("Phase 1 — Instant API (~16, API, ~10min)", [
            "python_coder","r_coder","api_notebook_creator","utility_scripter",
            "code_uploader","code_forker","code_tagger",
            "dataset_creator","api_dataset_creator","dataset_tagger","dataset_documenter",
            "model_creator","api_model_creator","model_variation_creator","model_tagger","model_documenter"
        ]),
        ("Phase 2 — Competition (~7, CLI+browser, ~15min)", [
            "competitor","getting_started_competitor","playground_competitor",
            "community_competitor","code_submitter","notebook_modeler","competition_modeler"
        ]),
        ("Phase 3 — Pipeline (~3, API, ~30min)", [
            "dataset_pipeline_creator","model_pipeline_creator","r_markdown_coder"
        ]),
        ("Phase 4 — Browser (~8, manual, ~10min)", [
            "stylish","vampire","bookmarker","collector",
            "github_coder","colab_coder","linked_dataset_creator","linked_model_creator"
        ]),
        ("Phase 5 — Streaks (~4, time-based)", [
            "seven_day_login_streak","thirty_day_login_streak",
            "submission_streak","super_submission_streak"
        ]),
    ]
    total = 0
    for phase, badges in data:
        print(f"\n{phase}:")
        for b in badges:
            print(f"  - {b}")
        total += len(badges)
    print(f"\nTotal: {total} badges (~38 automatable)")


def main():
    p = argparse.ArgumentParser(description="Kaggle badge automation")
    p.add_argument("--phase", choices=["1","2","3","4","5","all"], default="all")
    p.add_argument("--list", action="store_true")
    args = p.parse_args()

    if args.list:
        list_all(); return

    username = get_username()
    if not username:
        print("ERROR: Kaggle credentials required. Run: python kaggle_creds.py")
        sys.exit(1)

    phase = args.phase
    if phase in ("1", "all"):
        phase1(username)
    if phase in ("2", "all"):
        phase2_guide()
    if phase in ("3", "all"):
        phase3_guide()
    if phase in ("4", "all"):
        phase4_guide()
    if phase in ("5", "all"):
        phase5_guide()

    if phase == "all":
        print("=== Summary ===")
        print("  Phase 1: EXECUTED — check kaggle.com/badges")
        print("  Phases 2-5: follow the guidance printed above")


if __name__ == "__main__":
    main()
