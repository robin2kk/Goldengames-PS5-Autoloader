#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${ROOT}/work"
UPSTREAM="${WORK}/ps5-webkit-autoloader"

rm -rf "$WORK"
mkdir -p "$WORK"

git clone --branch v0.3.0 --depth 1 https://github.com/itsPLK/ps5-webkit-autoloader.git "$UPSTREAM"
cd "$UPSTREAM"
git submodule update --init --recursive

# Verify the exact v0.3.0 dependency revisions before applying Goldengames.
expected_umtx2="a080beb74d9e4bc34f3563798b716bd86b2d6ee0"
expected_slopkit="6153152be0b6a69e7e7931ff1b68523b7fde1429"
expected_unified="78a6f0274f1581e233b69dd7dd4fd3b948a6d15c"
expected_elfldr="148b71c2fb9155d2550ef6a14eb03433e23acaeb"

check_pin() {
  local dir="$1" expected="$2"
  local actual
  actual="$(git -C "$dir" rev-parse HEAD)"
  [[ "$actual" == "$expected" ]] || { echo "Pin mismatch: $dir expected $expected got $actual" >&2; exit 1; }
}

check_pin third_party/umtx2 "$expected_umtx2"
check_pin third_party/slopkit "$expected_slopkit"
check_pin third_party/ps5-unified-autoloader "$expected_unified"
check_pin third_party/ps5-elfldr "$expected_elfldr"

# Goldengames autoloader dashboard.
cp "$ROOT/overlay/frontend/index.html" frontend/autoloader/index.html
cp "$ROOT/overlay/frontend/style.css" frontend/autoloader/style.css
cp "$ROOT/overlay/frontend/rc5.css" frontend/autoloader/rc5.css
cp "$ROOT/overlay/frontend/jb-icon.css" frontend/autoloader/jb-icon.css
cp "$ROOT/overlay/frontend/jb-icon.svg" frontend/autoloader/jb-icon.svg
cp "$ROOT/overlay/frontend/logo.svg" frontend/autoloader/logo.svg
cp "$ROOT/overlay/frontend/favicon.svg" frontend/autoloader/favicon.svg

# Goldengames native ELF installer browser screen.
cp "$ROOT/overlay/installer-page/index.html" frontend/installer-page/index.html
cp "$ROOT/overlay/frontend/jb-icon.svg" frontend/installer-page/jb-icon.svg
cp "$ROOT/overlay/assets/icon.svg" assets/icon.svg

python3 "$ROOT/tools/patch_upstream_frontend.py" "$UPSTREAM"
python3 "$ROOT/tools/rc7_session_fix.py" "$UPSTREAM"

# Upstream v0.3.0 downloads pinned dependency metadata through GitHub API.
python3 - "$UPSTREAM/tools/download_deps.sh" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
old = '''        req = urllib.request.Request(url, headers={
            "User-Agent": "ps5-webkit-autoloader-build",
            "Accept-Encoding": "gzip",
        })'''
new = '''        headers = {
            "User-Agent": "ps5-webkit-autoloader-build",
            "Accept-Encoding": "gzip",
        }
        token = os.environ.get("GITHUB_TOKEN", "").strip()
        if token and url.startswith("https://api.github.com/"):
            headers["Authorization"] = f"Bearer {token}"
            headers["X-GitHub-Api-Version"] = "2022-11-28"
        req = urllib.request.Request(url, headers=headers)'''
if old not in text:
    raise SystemExit("Could not patch upstream download_deps.sh for authenticated GitHub API access")
path.write_text(text.replace(old, new, 1))
print("Patched upstream download_deps.sh to use GITHUB_TOKEN for GitHub API metadata requests.")
PY

mkdir -p frontend/autoloader/payloads

echo "Goldengames overlay staged at: $UPSTREAM"
echo "Functional launcher base: upstream v0.3.0 app.js + Goldengames menu patch + RC7 session safety"
echo "Auto Jailbreak emblem: Goldengames JB yellow/blue SVG"
echo "Installer screen: Goldengames animated PS1-inspired UI"
echo "Homescreen icon: Goldengames overlay/assets/icon.svg"
echo "RC7: app reopen never automatically replays kernel exploit after successful etaHEN marker"
echo "RC7: manual sender verifies elfldr on 9021 and falls back to full chain if unavailable"
echo "Next: place the exact pinned payloads in frontend/autoloader/payloads and run the upstream build."
