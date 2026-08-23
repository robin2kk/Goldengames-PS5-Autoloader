#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v105_etahen26_upstream031.py <upstream-root>')

root = Path(sys.argv[1]).resolve()
app = root / 'frontend' / 'autoloader' / 'app.js'
index = root / 'frontend' / 'autoloader' / 'index.html'

text = app.read_text(encoding='utf-8')

# v1.0.5 keeps etaHEN 2.5B available as a manual payload, but changes every
# Auto Jailbreak success/failure marker and automatic launch path to the exact
# pinned etaHEN 2.6B binary.
replacements = {
    "if (selectedPayload === 'etahen-2.5B.bin') {": "if (selectedPayload === 'etahen-2.6B.bin') {",
    "selectedPayload === 'etahen-2.5B.bin' ? 'etaHEN 2.5B launched successfully.'": "selectedPayload === 'etahen-2.6B.bin' ? 'etaHEN 2.6B launched successfully.'",
    "if (selectedPayload === 'etahen-2.5B.bin') setJailbreakState(false);": "if (selectedPayload === 'etahen-2.6B.bin') setJailbreakState(false);",
    "showGoldengamesNotification('etaHEN 2.5B LAUNCHED', 'Jailbreak ready · Manual Payload Mode enabled');": "showGoldengamesNotification('etaHEN 2.6B LAUNCHED', 'Jailbreak ready · Manual Payload Mode enabled');",
    "choosePayload('etahen-2.5B.bin', 'AUTO JAILBREAK · etaHEN 2.5B', true);": "choosePayload('etahen-2.6B.bin', 'AUTO JAILBREAK · etaHEN 2.6B', true);",
}

for old, new in replacements.items():
    if old not in text:
        raise SystemExit(f'v1.0.5 Auto Jailbreak hook not found: {old}')
    text = text.replace(old, new)

# The replacement above intentionally does not touch the manual etaHEN 2.5B
# tile; both 2.5B and 2.6B remain selectable manually.
if "choosePayload('etahen-2.5B.bin', 'etaHEN 2.5B', false)" not in text:
    raise SystemExit('Manual etaHEN 2.5B route was unexpectedly removed')
if "choosePayload('etahen-2.6B.bin', 'etaHEN 2.6B', false)" not in text:
    raise SystemExit('Manual etaHEN 2.6B route is missing')

# Require both automatic entry points (button + timed auto-start) to use 2.6B.
auto_route = "choosePayload('etahen-2.6B.bin', 'AUTO JAILBREAK · etaHEN 2.6B', true);"
if text.count(auto_route) < 2:
    raise SystemExit('Expected both v1.0.5 Auto Jailbreak entry points to route to etaHEN 2.6B')
if "AUTO JAILBREAK · etaHEN 2.5B" in text:
    raise SystemExit('Stale etaHEN 2.5B Auto Jailbreak route remains')

app.write_text(text, encoding='utf-8')

# Update visible dashboard copy when the Goldengames overlay contains the old
# stable-path wording. This is cosmetic and does not change the manual 2.5B tile.
if index.is_file():
    html = index.read_text(encoding='utf-8')
    html = html.replace('Auto Jailbreak · etaHEN 2.5B', 'Auto Jailbreak · etaHEN 2.6B')
    html = html.replace('AUTO JAILBREAK · etaHEN 2.5B', 'AUTO JAILBREAK · etaHEN 2.6B')
    html = html.replace('Auto Jailbreak uses etaHEN 2.5B', 'Auto Jailbreak uses etaHEN 2.6B')
    index.write_text(html, encoding='utf-8')

print('Goldengames v1.0.5 Auto Jailbreak routing applied:')
print('  Base: itsPLK PS5 WebKit Autoloader v0.3.1')
print('  AUTO JAILBREAK: etaHEN 2.6B')
print('  Manual etaHEN 2.5B: retained')
print('  Manual etaHEN 2.6B: retained')
