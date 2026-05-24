#!/usr/bin/env python3
"""
kaggle_models.py — Search, download, and publish Kaggle models.

Usage:
    python kaggle_models.py --search "gemma"
    python kaggle_models.py --download google/gemma/transformers/2b [--path ./models]
    python kaggle_models.py --download google/gemma/transformers/2b --kagglehub
    python kaggle_models.py --info google/gemma
    python kaggle_models.py --publish ./my-model [--title "My Model"]
    python kaggle_models.py --accelerators
"""
import argparse, json, subprocess, sys
from pathlib import Path

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

ACCELERATORS = {
    "CPU":   "4 cores, 16GB RAM — unlimited",
    "P100":  "GPU 16GB VRAM — 30h/week",
    "T4×2":  "GPU 2×16GB VRAM — 30h/week",
    "A100":  "GPU 40GB VRAM — special request",
    "TPUv3": "TPU v3-8 — 20h/week",
    "H100":  "GPU H100 — limited availability",
    "L4":    "GPU L4 — limited availability",
}

DATA_PATHS = {
    "competition data":     "/kaggle/input/",
    "attached dataset":     "/kaggle/input/<dataset-slug>/",
    "attached model":       "/kaggle/input/<model-slug>/<framework>/<variation>/<version>/",
    "working directory":    "/kaggle/working/",
    "output dir":           "/kaggle/working/",
}


def search(query, n=15):
    r = run(["kaggle", "models", "list"])
    lines = (r.stdout or "").strip().split("\n")
    q = query.lower()
    matches = [l for l in lines if q in l.lower()]
    for ln in (matches or lines)[:n]:
        print(ln)


def get_info(handle):
    r = run(["kaggle", "models", "instances", "get", handle])
    print(r.stdout if r.stdout else r.stderr[:500])


def download_cli(handle, path="./models"):
    Path(path).mkdir(parents=True, exist_ok=True)
    print(f"[download] {handle} → {path}/")
    r = run(["kaggle", "models", "instances", "versions", "download", handle, "-p", path])
    print((r.stdout or r.stderr)[:400])


def download_kagglehub(handle):
    try:
        import kagglehub
        path = kagglehub.model_download(handle)
        print(f"[kagglehub] → {path}")
        return path
    except ImportError:
        print("ERROR: pip install kagglehub"); sys.exit(1)


def publish_kagglehub(handle, path, license_name="Apache 2.0"):
    try:
        import kagglehub
        result = kagglehub.model_upload(handle, path, license_name=license_name)
        print(f"[kagglehub] model_upload → {result}")
    except ImportError:
        print("ERROR: pip install kagglehub"); sys.exit(1)


def publish(path, title=None):
    path = Path(path)
    meta = path / "model-metadata.json"
    if not meta.exists():
        r = run(["kaggle", "models", "init", "-p", str(path)])
        if r.returncode != 0:
            print(f"init failed: {r.stderr[:300]}"); sys.exit(1)
    if meta.exists() and title:
        d = json.loads(meta.read_text())
        d["title"] = title
        meta.write_text(json.dumps(d, indent=2))
    r = run(["kaggle", "models", "create", "-p", str(path)])
    print((r.stdout or r.stderr)[:300])


def show_accelerators():
    print("=== Kaggle Accelerators ===")
    for k, v in ACCELERATORS.items():
        print(f"  {k:<8} {v}")
    print("\n=== Kaggle Data Paths ===")
    for k, v in DATA_PATHS.items():
        print(f"  {k:<22} {v}")


def main():
    p = argparse.ArgumentParser(description="Kaggle model operations")
    p.add_argument("--search",       metavar="QUERY")
    p.add_argument("--download",     metavar="HANDLE")
    p.add_argument("--info",         metavar="HANDLE")
    p.add_argument("--publish",      metavar="DIR")
    p.add_argument("--path",         default="./models")
    p.add_argument("--title")
    p.add_argument("--handle",       help="Model handle for kagglehub publish (owner/model/framework/variation)")
    p.add_argument("--license",      default="Apache 2.0")
    p.add_argument("--kagglehub",    action="store_true")
    p.add_argument("--accelerators", action="store_true")
    args = p.parse_args()

    if   args.accelerators: show_accelerators()
    elif args.search:        search(args.search)
    elif args.download:
        if args.kagglehub:   download_kagglehub(args.download)
        else:                download_cli(args.download, args.path)
    elif args.info:          get_info(args.info)
    elif args.publish:
        if args.kagglehub and args.handle: publish_kagglehub(args.handle, args.publish, args.license)
        else:                              publish(args.publish, args.title)
    else:                    p.print_help()


if __name__ == "__main__":
    main()
