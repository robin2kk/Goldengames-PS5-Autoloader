#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v104_etahen26_autojb_test.py <upstream-root>')

root = Path(sys.argv[1]).resolve()
app = root / 'frontend' / 'autoloader' / 'app.js'
s = app.read_text(encoding='utf-8')

# Test-only change: switch only the Auto Jailbreak payload from etaHEN 2.5B
# to etaHEN 2.6B. Do not alter UMTX2, persistent 9021 sender, retry timings,
# manual payloads, or dashboard behavior.
old = "choosePayload('etahen-2.5B.bin', 'etaHEN 2.5B', true)"
new = "choosePayload('etahen-2.6B.bin', 'etaHEN 2.6B', true)"
if old not in s:
    raise SystemExit('etaHEN 2.5B Auto Jailbreak selector not found')
s = s.replace(old, new)

# v1.0.4 marks the persistent sender ready after successful Auto Jailbreak.
# Make that success check follow 2.6B in this isolated test build.
s = s.replace("selectedPayload === 'etahen-2.5B.bin'", "selectedPayload === 'etahen-2.6B.bin'")

app.write_text(s, encoding='utf-8')
print('Test build: Auto Jailbreak switched to etaHEN 2.6B only.')
