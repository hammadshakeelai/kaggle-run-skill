#!/usr/bin/env python3
"""
kaggle_datasets.py — Search, download, and publish Kaggle datasets.

Usage:
    python kaggle_datasets.py --search "titanic"
    python kaggle_datasets.py --download owner/slug [--path ./data]
    python kaggle_datasets.py --download owner/slug --kagglehub [--file data.csv]
    python kaggle_datasets.py --files owner/slug
    python kaggle_datasets.py --publish ./my-dir [--title "My Dataset"] [--license CC0-1.0]
    python kaggle_datasets.py --version ./my-dir --message "v2 notes"
"""
import argparse, json, subprocess, sys, zipfile, glob as _glob
from pathlib import Path

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

LICENSES = ["CC0-1.0","CC-BY-SA-3.0","CC-BY-SA-4.0","CC-BY-NC-SA-4.0",
            "GPL-2.0","GPL-3.0","ODbL-1.0","Apache-2.0","CC-BY-4.0"]


def search(query, n=15):
    r = run(["kaggle", "datasets", "list", "-s", query])
    lines = (r.stdout or r.stderr).strip().split("\n")
    for ln in lines[:n+1]:
        print(ln)


def list_files(slug):
    r = run(["kaggle", "datasets", "files", slug])
    print(r.stdout if r.stdout else r.stderr[:500])


def download_cli(slug, path="./data"):
    Path(path).mkdir(parents=True, exist_ok=True)
    print(f"[download] {slug} → {path}/")
    # Try --unzip first
    r = run(["kaggle", "datasets", "download", "-d", slug, "-p", path, "--unzip"])
    if r.returncode == 0:
        print(r.stdout[:300]); return
    # Fallback: download then manual unzip
    r2 = run(["kaggle", "datasets", "download", "-d", slug, "-p", path])
    if r2.returncode != 0:
        print(f"ERROR: {r2.stderr[:500]}"); sys.exit(1)
    for zf in _glob.glob(f"{path}/*.zip"):
        print(f"[unzip] {zf}")
        with zipfile.ZipFile(zf) as z:
            z.extractall(path)
    files = list(Path(path).rglob("*"))
    print(f"  {len(files)} file(s) in {path}/")


def download_kagglehub(slug, filename=None):
    try:
        import kagglehub
        if filename:
            from kagglehub import KaggleDatasetAdapter
            df = kagglehub.dataset_load(KaggleDatasetAdapter.PANDAS, slug, filename)
            print(f"[kagglehub] DataFrame {df.shape}")
            print(df.head())
            return df
        else:
            path = kagglehub.dataset_download(slug)
            print(f"[kagglehub] → {path}")
            return path
    except ImportError:
        print("ERROR: pip install kagglehub"); sys.exit(1)


def publish_kagglehub(slug, path, license_name="CC0-1.0"):
    try:
        import kagglehub
        result = kagglehub.dataset_upload(slug, path, license_name=license_name)
        print(f"[kagglehub] dataset_upload → {result}")
    except ImportError:
        print("ERROR: pip install kagglehub"); sys.exit(1)


def publish(path, title=None, version_notes=None, license_name="CC0-1.0"):
    path = Path(path)
    meta = path / "dataset-metadata.json"
    if not meta.exists():
        r = run(["kaggle", "datasets", "init", "-p", str(path)])
        if r.returncode != 0:
            print(f"init failed: {r.stderr[:300]}"); sys.exit(1)
    if meta.exists() and title:
        d = json.loads(meta.read_text())
        d["title"] = title
        if "licenses" not in d:
            d["licenses"] = [{"name": license_name}]
        meta.write_text(json.dumps(d, indent=2))
    # Try create, then version
    r = run(["kaggle", "datasets", "create", "-p", str(path), "--dir-mode", "zip"])
    if r.returncode == 0:
        print(f"[publish] created: {(r.stdout or r.stderr)[:300]}")
    elif version_notes:
        r2 = run(["kaggle", "datasets", "version", "-p", str(path), "-m", version_notes])
        print(f"[version] {(r2.stdout or r2.stderr)[:300]}")
    else:
        print(f"[publish] {(r.stderr)[:300]}")


def main():
    p = argparse.ArgumentParser(description="Kaggle dataset operations")
    p.add_argument("--search",   metavar="QUERY")
    p.add_argument("--download", metavar="SLUG")
    p.add_argument("--files",    metavar="SLUG")
    p.add_argument("--publish",  metavar="DIR")
    p.add_argument("--version",  metavar="DIR")
    p.add_argument("--path",     default="./data")
    p.add_argument("--title")
    p.add_argument("--message",  default="New version")
    p.add_argument("--license",  default="CC0-1.0", choices=LICENSES)
    p.add_argument("--kagglehub", action="store_true")
    p.add_argument("--file",     help="Specific file for kagglehub load")
    p.add_argument("--slug",     help="Slug for kagglehub publish (owner/name)")
    args = p.parse_args()

    if   args.search:   search(args.search)
    elif args.download:
        if args.kagglehub: download_kagglehub(args.download, args.file)
        else:              download_cli(args.download, args.path)
    elif args.files:    list_files(args.files)
    elif args.publish:
        if args.kagglehub and args.slug: publish_kagglehub(args.slug, args.publish, args.license)
        else:                            publish(args.publish, args.title, None, args.license)
    elif args.version:  publish(args.version, args.title, args.message, args.license)
    else:               p.print_help()


if __name__ == "__main__":
    main()
