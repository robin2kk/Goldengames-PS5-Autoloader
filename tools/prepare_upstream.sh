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

# Keep upstream v0.3.0 app.js as the functional base. Only replace the visual
# shell, then patch upstream's tested start() flow to wait for a menu choice.
cp "$ROOT/overlay/frontend/index.html" frontend/autoloader/index.html
cp "$ROOT/overlay/frontend/style.css" frontend/autoloader/style.css
cp "$ROOT/overlay/frontend/jb-icon.css" frontend/autoloader/jb-icon.css
cp "$ROOT/overlay/frontend/jb-icon.svg" frontend/autoloader/jb-icon.svg
cp "$ROOT/overlay/frontend/logo.svg" frontend/autoloader/logo.svg
cp "$ROOT/overlay/frontend/favicon.svg" frontend/autoloader/favicon.svg

# Replace the upstream PS5 homescreen icon with the Goldengames icon. The
# upstream Makefile converts assets/icon.svg to the final icon0.png embedded
# by the installer, so this keeps the build reproducible from source.
cp "$ROOT/overlay/assets/icon.svg" assets/icon.svg

python3 "$ROOT/tools/patch_upstream_frontend.py" "$UPSTREAM"

# Upstream v0.3.0 downloads pinned elfldr/unified-autoloader release metadata
# through the GitHub API. Anonymous API calls can hit the shared runner rate
# limit, so teach the pinned downloader to use GITHUB_TOKEN when Actions passes
# it into the Docker build container. The token is never printed or persisted.
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
echo "Functional launcher base: upstream v0.3.0 app.js + Goldengames menu patch"
echo "Auto Jailbreak emblem: Goldengames JB yellow/blue SVG"
echo "Homescreen icon: Goldengames overlay/assets/icon.svg"
echo "GitHub release metadata: authenticated in Actions when GITHUB_TOKEN is available"
echo "Next: place the exact pinned payloads in frontend/autoloader/payloads and run the upstream build."
