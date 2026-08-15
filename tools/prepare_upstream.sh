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
cp "$ROOT/overlay/frontend/logo.svg" frontend/autoloader/logo.svg
cp "$ROOT/overlay/frontend/favicon.svg" frontend/autoloader/favicon.svg
python3 "$ROOT/tools/patch_upstream_frontend.py" "$UPSTREAM"

mkdir -p frontend/autoloader/payloads

echo "Goldengames overlay staged at: $UPSTREAM"
echo "Functional launcher base: upstream v0.3.0 app.js + Goldengames menu patch"
echo "Next: place the exact pinned payloads in frontend/autoloader/payloads and run the upstream build."