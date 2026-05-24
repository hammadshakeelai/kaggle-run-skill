#!/usr/bin/env python3
"""
kaggle_leaderboard.py — Pull and analyze Kaggle competition leaderboards.

Usage:
    python kaggle_leaderboard.py --comp titanic
    python kaggle_leaderboard.py --comp titanic --top 50 --analyze
    python kaggle_leaderboard.py --comp titanic --thresholds
    python kaggle_leaderboard.py --comp titanic --export lb.csv
"""
import argparse, csv, statistics, subprocess, sys
from pathlib import Path

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def pull(comp, n=20):
    r = run(["kaggle", "competitions", "leaderboard", comp, "--show"])
    if r.returncode != 0:
        print(f"ERROR: {r.stderr[:300]}"); sys.exit(1)
    lines = r.stdout.strip().split("\n")
    # Print top n
    for ln in lines[:n+1]:
        print(ln)
    return lines


def parse_scores(lines):
    scores = []
    for ln in lines[1:]:  # skip header
        parts = ln.split()
        if len(parts) < 3:
            continue
        try:
            rank  = int(parts[0])
            score = float(parts[-1])
            team  = " ".join(parts[1:-1])
            scores.append({"rank": rank, "team": team, "score": score})
        except ValueError:
            pass
    return scores


def analyze(scores, comp):
    if not scores:
        print("No parseable scores."); return
    vals = [s["score"] for s in scores]
    print(f"\n=== Analysis: {comp} ===")
    print(f"  Entries    : {len(scores)}")
    print(f"  Top score  : {vals[0]:.5f}  ({scores[0]['team']})")
    if len(vals) >= 10:
        print(f"  Top-10 cut : {vals[9]:.5f}")
        print(f"  Spread 1→10: {abs(vals[0]-vals[9]):.6f}")
    if len(vals) >= 5:
        print(f"  Median     : {statistics.median(vals):.5f}")
        print(f"  Stdev      : {statistics.stdev(vals):.5f}")
    # Medal zones (Kaggle formula: top N teams, min 3)
    n = len(scores)
    gold   = max(3, round(n * 0.001))
    silver = max(3, round(n * 0.005))
    bronze = max(3, round(n * 0.01))
    print(f"\n  Gold   zone: top {gold} teams  (≥ {vals[min(gold-1,n-1)]:.5f})")
    print(f"  Silver zone: top {silver} teams  (≥ {vals[min(silver-1,n-1)]:.5f})")
    print(f"  Bronze zone: top {bronze} teams  (≥ {vals[min(bronze-1,n-1)]:.5f})")


def thresholds(scores, comp):
    if not scores:
        print("No scores."); return
    n = len(scores)
    print(f"\n=== Competitive Thresholds: {comp} ({n} teams) ===")
    for pct, label in [(0.10,"Top 10%"), (0.25,"Top 25%"), (0.50,"Median")]:
        idx = max(0, min(int(n * pct), n-1))
        print(f"  {label:<10}: {scores[idx]['score']:.5f}  (rank {scores[idx]['rank']})")


def export_csv(scores, path):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["rank","team","score"])
        w.writeheader(); w.writerows(scores)
    print(f"[export] {len(scores)} entries → {path}")


def main():
    p = argparse.ArgumentParser(description="Kaggle leaderboard analysis")
    p.add_argument("--comp",       required=True)
    p.add_argument("--top",        type=int, default=20)
    p.add_argument("--analyze",    action="store_true")
    p.add_argument("--thresholds", action="store_true")
    p.add_argument("--export",     metavar="FILE")
    args = p.parse_args()

    lines  = pull(args.comp, args.top)
    scores = parse_scores(lines)

    if args.analyze:    analyze(scores, args.comp)
    if args.thresholds: thresholds(scores, args.comp)
    if args.export:     export_csv(scores, args.export)


if __name__ == "__main__":
    main()
