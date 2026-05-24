#!/usr/bin/env python3
"""
kaggle_compete.py — Competition workflow: report, download, submit, scaffold, hackathon.

Usage:
    python kaggle_compete.py --list
    python kaggle_compete.py --comp titanic
    python kaggle_compete.py --comp titanic --download
    python kaggle_compete.py --comp titanic --submit preds.csv [--message "v1"]
    python kaggle_compete.py --comp titanic --scaffold
    python kaggle_compete.py --comp titanic --auto-submit
    python kaggle_compete.py --hackathon <slug>
"""
import argparse, json, subprocess, sys, zipfile, glob as _glob
from pathlib import Path

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def list_competitions(search=None):
    cmd = ["kaggle", "competitions", "list", "--sort-by", "latestDeadline"]
    if search:
        cmd += ["-s", search]
    r = run(cmd)
    print((r.stdout or r.stderr)[:3000])


def competition_report(comp):
    print(f"\n=== Competition: {comp} ===\n")
    # Files
    r = run(["kaggle", "competitions", "files", comp])
    print("--- Data Files ---")
    print((r.stdout or r.stderr)[:800])
    # Leaderboard top 10
    r2 = run(["kaggle", "competitions", "leaderboard", comp, "--show"])
    lines = (r2.stdout or "").strip().split("\n")
    print("\n--- Top 10 ---")
    for ln in lines[:11]:
        print(ln)
    # Recent submissions
    r3 = run(["kaggle", "competitions", "submissions", comp])
    if r3.stdout:
        print("\n--- Your Submissions ---")
        for ln in r3.stdout.strip().split("\n")[:6]:
            print(ln)


def download_data(comp, path="./data"):
    Path(path).mkdir(parents=True, exist_ok=True)
    print(f"[download] {comp} → {path}/")
    r = run(["kaggle", "competitions", "download", "-c", comp, "-p", path])
    print((r.stdout or r.stderr)[:400])
    for zf in _glob.glob(f"{path}/*.zip"):
        print(f"[unzip] {zf}")
        with zipfile.ZipFile(zf) as z:
            z.extractall(path)
    files = list(Path(path).iterdir())
    print(f"  {len(files)} file(s) in {path}/")


def submit(comp, file_path, message="Auto-submission via kaggle-run"):
    print(f"[submit] {file_path} → {comp}")
    r = run(["kaggle", "competitions", "submit", "-c", comp, "-f", file_path, "-m", message])
    print((r.stdout or r.stderr)[:400])
    r2 = run(["kaggle", "competitions", "submissions", comp])
    if r2.stdout:
        print("\n--- Recent Submissions ---")
        for ln in r2.stdout.strip().split("\n")[:6]:
            print(ln)


def scaffold_baseline(comp, data_dir="./data", output_dir="."):
    csvs = _glob.glob(f"{data_dir}/*.csv")
    train = next((f for f in csvs if "train" in Path(f).name.lower()), csvs[0] if csvs else "train.csv")
    test  = next((f for f in csvs if "test"  in Path(f).name.lower()), "test.csv")
    sample = next((f for f in csvs if "sample" in Path(f).name.lower()), "sample_submission.csv")

    nb = {
        "cells": [
            {"cell_type": "code", "source": [
                f"# Baseline notebook — {comp}\n",
                "import pandas as pd, numpy as np\n",
                f"train  = pd.read_csv('/kaggle/input/{comp}/{Path(train).name}')\n",
                f"test   = pd.read_csv('/kaggle/input/{comp}/{Path(test).name}')\n",
                f"sample = pd.read_csv('/kaggle/input/{comp}/{Path(sample).name}')\n",
                "print('train:', train.shape, '  test:', test.shape)\ntrain.head()"
            ], "outputs": [], "execution_count": None, "metadata": {}},
            {"cell_type": "code", "source": [
                "# TODO: Build your model here\n",
                "# predictions = model.predict(test_features)\n",
                "# sub = pd.DataFrame({'id': test['id'], 'target': predictions})\n",
                "# sub.to_csv('submission.csv', index=False)\n",
                "print('Edit this cell to build your model, then submit submission.csv')"
            ], "outputs": [], "execution_count": None, "metadata": {}}
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.10.0"}
        },
        "nbformat": 4, "nbformat_minor": 5
    }
    nb_path = Path(output_dir) / f"{comp}_baseline.ipynb"
    nb_path.write_text(json.dumps(nb, indent=1))
    print(f"[scaffold] Created {nb_path}")
    return str(nb_path)


def hackathon_report(slug):
    print(f"\n=== Hackathon: {slug} ===\n")
    print("Requires Kaggle MCP server — run: python kaggle_creds.py --setup-mcp\n")
    print("MCP tool sequence:")
    for i, (tool, arg) in enumerate([
        ("get_hackathon_overview",     f'competition="{slug}"'),
        ("list_hackathon_tracks",      f'competition="{slug}"'),
        ("list_hackathon_write_ups",   f'competition="{slug}"'),
        ("get_writeup",                'writeup_id="<id from step 3>"'),
        ("get_resolved_writeup_links", 'writeup_id="<id>"  [hosts/judges only]'),
    ], 1):
        print(f"  {i}. {tool}({arg})")


def main():
    p = argparse.ArgumentParser(description="Kaggle competition workflow")
    p.add_argument("--list",         action="store_true", help="List active competitions")
    p.add_argument("--comp",         help="Competition slug")
    p.add_argument("--search",       help="Search competitions by keyword")
    p.add_argument("--download",     action="store_true")
    p.add_argument("--data-dir",     default="./data")
    p.add_argument("--submit",       metavar="FILE")
    p.add_argument("--message",      default="Auto-submission via kaggle-run")
    p.add_argument("--scaffold",     action="store_true", help="Create baseline notebook")
    p.add_argument("--auto-submit",  action="store_true", help="Download + scaffold (then edit + submit)")
    p.add_argument("--hackathon",    help="Hackathon slug")
    args = p.parse_args()

    if args.list:
        list_competitions(args.search); return
    if args.hackathon:
        hackathon_report(args.hackathon); return
    if not args.comp:
        p.print_help(); sys.exit(1)

    if not any([args.download, args.submit, args.scaffold, args.auto_submit]):
        competition_report(args.comp); return

    if args.download or args.auto_submit:
        download_data(args.comp, args.data_dir)
    if args.scaffold or args.auto_submit:
        nb = scaffold_baseline(args.comp, args.data_dir)
        if args.auto_submit:
            print(f"\nNext steps:")
            print(f"  1. Edit {nb} — add your model")
            print(f"  2. Deploy: python kaggle_deploy.py --nb {nb} --kernel <user>/{args.comp}-solution")
            print(f"  3. Submit: python kaggle_compete.py --comp {args.comp} --submit submission.csv")
    if args.submit:
        submit(args.comp, args.submit, args.message)


if __name__ == "__main__":
    main()
