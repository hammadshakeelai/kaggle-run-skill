#!/usr/bin/env python3
"""kaggle_creds.py — Check credentials and output MCP config."""
import argparse, json, os, pathlib, subprocess, sys

def check():
    home = pathlib.Path.home()
    token_file = home / ".kaggle" / "access_token"
    legacy_file = home / ".kaggle" / "kaggle.json"
    env_token = os.environ.get("KAGGLE_API_TOKEN", "")
    env_user  = os.environ.get("KAGGLE_USERNAME", "")
    env_key   = os.environ.get("KAGGLE_KEY", "")
    ok_token  = token_file.exists() or bool(env_token)
    ok_legacy = legacy_file.exists() or bool(env_user and env_key)
    print("=== Kaggle Credentials ===")
    print(f"  ~/.kaggle/access_token : {'OK' if token_file.exists() else 'missing'}")
    print(f"  KAGGLE_API_TOKEN env   : {'OK' if env_token else 'missing'}")
    print(f"  ~/.kaggle/kaggle.json  : {'OK' if legacy_file.exists() else 'missing'}")
    print(f"  KAGGLE_USERNAME+KEY env: {'OK' if (env_user and env_key) else 'missing'}")
    if legacy_file.exists():
        try:
            d = json.loads(legacy_file.read_text())
            print(f"  Legacy user: {d.get('username','?')}  key: {'present' if 'key' in d else 'missing'}")
        except Exception:
            pass
    if not (ok_token or ok_legacy):
        print("\nSETUP: kaggle.com/settings → API → Generate New Token")
        print(f"  Save to {token_file}  OR  export KAGGLE_API_TOKEN=<token>")
        return False
    print("\nStatus: OK")
    return True

def verify():
    r = subprocess.run(["kaggle", "config", "view"], capture_output=True, text=True)
    print("Verify:", "OK" if r.returncode == 0 else "FAILED")
    print((r.stdout or r.stderr)[:300])
    return r.returncode == 0

def setup_mcp(token=None):
    if not token:
        t = pathlib.Path.home() / ".kaggle" / "access_token"
        token = t.read_text().strip() if t.exists() else os.environ.get("KAGGLE_API_TOKEN", "<your_api_token>")
    print("=== Kaggle MCP Server (66 tools) ===\n")
    print("Claude Code:")
    print(f'  claude mcp add kaggle --transport http https://www.kaggle.com/mcp \\\n    --header "Authorization: Bearer {token}"\n')
    print("Cursor / Gemini CLI / Claude Desktop:")
    print(json.dumps({"mcpServers": {"kaggle": {"url": "https://www.kaggle.com/mcp", "headers": {"Authorization": f"Bearer {token}"}}}}, indent=2))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--verify",    action="store_true")
    p.add_argument("--setup-mcp", action="store_true")
    p.add_argument("--token",     help="Token for MCP config output only")
    args = p.parse_args()
    if args.setup_mcp:
        setup_mcp(args.token); return
    ok = check()
    if args.verify and ok:
        verify()
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
