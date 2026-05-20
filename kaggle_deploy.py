#!/usr/bin/env python3
"""
kaggle_deploy.py — push a notebook to Kaggle, monitor, and download outputs.

Usage:
    python kaggle_deploy.py --notebook path/to/nb.ipynb --kernel username/kernel-name
    python kaggle_deploy.py --notebook path/to/nb.ipynb --kernel username/kernel-name --push-dir kaggle_push/
    python kaggle_deploy.py --kernel username/kernel-name --monitor-only
"""
import argparse, json, os, shutil, subprocess, sys, time
from pathlib import Path


def run(args, **kwargs):
    return subprocess.run(args, capture_output=True, text=True, **kwargs)


def get_status(kernel_id):
    r = run(["kaggle", "kernels", "status", kernel_id])
    out = (r.stdout + r.stderr)
    for s in ["COMPLETE", "ERROR", "RUNNING", "QUEUED", "CANCEL"]:
        if s in out:
            return s
    return "UNKNOWN"


def get_log_tail(kernel_id, log_dir, n=50):
    run(["kaggle", "kernels", "output", kernel_id, "-p", str(log_dir)])
    logs = list(Path(log_dir).glob("*.log"))
    if not logs:
        return ""
    log = json.loads(logs[0].read_text(encoding="utf-8", errors="replace"))
    lines = [e.get("data", "") for e in log if e.get("stream_name") == "stderr"]
    return "".join(lines[-n:])


def push(push_dir):
    r = run(["kaggle", "kernels", "push"], cwd=str(push_dir))
    print(r.stdout.strip())
    if r.returncode != 0:
        print("PUSH ERROR:", r.stderr[:500])
        sys.exit(1)


def download_outputs(kernel_id, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    r = run(["kaggle", "kernels", "output", kernel_id, "-p", str(out_dir)])
    print(r.stdout.strip())
    files = list(out_dir.rglob("*"))
    print(f"Downloaded {len(files)} file(s) to {out_dir}/")


def monitor(kernel_id, poll=60, max_wait=7200):
    print(f"[MONITOR] Watching {kernel_id} (poll={poll}s, max={max_wait}s)")
    prev = ""
    elapsed = 0
    while elapsed < max_wait:
        status = get_status(kernel_id)
        if status != prev:
            print(f"[{elapsed:5d}s] STATUS: {status}")
            prev = status
        if status == "COMPLETE":
            return "COMPLETE"
        if status in ("ERROR", "CANCEL"):
            return status
        time.sleep(poll)
        elapsed += poll
    return "TIMEOUT"


def copy_notebook(src, push_dir):
    push_dir = Path(push_dir)
    push_dir.mkdir(parents=True, exist_ok=True)
    dst = push_dir / "notebook.ipynb"
    nb = json.loads(Path(src).read_text(encoding="utf-8", errors="replace"))
    # Clear outputs before pushing
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "code":
            cell["outputs"] = []
            cell["execution_count"] = None
    dst.write_text(json.dumps(nb, indent=1, ensure_ascii=True), encoding="ascii")
    print(f"Copied {src} -> {dst}")


def main():
    parser = argparse.ArgumentParser(description="Deploy notebook to Kaggle and monitor.")
    parser.add_argument("--notebook", "-n", help="Path to .ipynb notebook")
    parser.add_argument("--kernel", "-k", required=True, help="Kaggle kernel ID (user/name)")
    parser.add_argument("--push-dir", "-d", help="Push directory (default: kaggle_push_<slug>/)")
    parser.add_argument("--output-dir", "-o", default="kaggle_outputs", help="Output download dir")
    parser.add_argument("--log-dir", "-l", default="kaggle_logs", help="Log download dir")
    parser.add_argument("--monitor-only", action="store_true", help="Skip push, just monitor")
    parser.add_argument("--poll", type=int, default=60, help="Poll interval in seconds")
    parser.add_argument("--max-wait", type=int, default=7200, help="Max wait in seconds")
    args = parser.parse_args()

    kernel_slug = args.kernel.split("/")[-1]
    push_dir = Path(args.push_dir or f"kaggle_push_{kernel_slug}")

    if not args.monitor_only:
        if not args.notebook:
            # Try to find a notebook
            nbs = list(Path(".").glob("*.ipynb"))
            if not nbs:
                print("ERROR: No .ipynb found. Use --notebook to specify one.")
                sys.exit(1)
            args.notebook = str(nbs[0])
            print(f"Using notebook: {args.notebook}")

        if not Path(args.notebook).exists():
            print(f"ERROR: Notebook not found: {args.notebook}")
            sys.exit(1)

        if not (push_dir / "kernel-metadata.json").exists():
            print(f"ERROR: {push_dir}/kernel-metadata.json not found.")
            print(f"Create it with: {{\"id\": \"{args.kernel}\", \"language\": \"python\", \"kernel_type\": \"notebook\"}}")
            sys.exit(1)

        copy_notebook(args.notebook, push_dir)
        push(push_dir)
        print("Waiting 30s for Kaggle to register new version...")
        time.sleep(30)

    status = monitor(args.kernel, poll=args.poll, max_wait=args.max_wait)

    if status == "COMPLETE":
        print("\nSUCCESS: Kernel completed!")
        download_outputs(args.kernel, args.output_dir)
    elif status == "ERROR":
        print("\nERROR: Kernel failed. Fetching logs...")
        tail = get_log_tail(args.kernel, args.log_dir)
        print(tail[-2000:])
        print(f"\nFull logs in {args.log_dir}/")
        sys.exit(1)
    elif status == "TIMEOUT":
        print(f"\nTIMEOUT: Kernel still running after {args.max_wait}s. Check Kaggle manually.")
        sys.exit(2)
    else:
        print(f"\nUnexpected status: {status}")
        sys.exit(3)


if __name__ == "__main__":
    main()
