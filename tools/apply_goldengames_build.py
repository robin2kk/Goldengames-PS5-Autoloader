#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: apply_goldengames_build.py <upstream-root>')

root = Path(sys.argv[1]).resolve()
param = root / 'assets' / 'param.json.template'
registry = root / 'tools' / 'gen_file_registry.py'
wkali_h = root / 'include' / 'wkali.h'
installer_c = root / 'src' / 'app_installer.c'
umtx_patch = root / 'patches' / 'umtx2-autoload.patch'

param.write_text('''{
    "titleId": "GGAU00001",
    "applicationCategoryType": 65536,
    "deeplinkUri": "http://127.0.0.1:18181/app/index.html",
    "localizedParameters": {
        "defaultLanguage": "en-US",
        "en-US": {
            "titleName": "Goldengames PS5 Autoloader v[[VERSION_PLACEHOLDER]]"
        }
    }
}\n''', encoding='utf-8')

# IMPORTANT: param.json and the native installer MUST use the same title ID.
wkali_text = wkali_h.read_text(encoding='utf-8')
old_title = '#define WKAL_TITLE_ID "WKAL00001"'
new_title = '#define WKAL_TITLE_ID "GGAU00001"'
if old_title not in wkali_text and new_title not in wkali_text:
    raise SystemExit('WKAL_TITLE_ID definition not found; upstream changed')
wkali_h.write_text(wkali_text.replace(old_title, new_title, 1), encoding='utf-8')

# Brand installer notifications too, so test builds are easy to distinguish.
installer_text = installer_c.read_text(encoding='utf-8')
installer_text = installer_text.replace('Updating WebKit Autoloader App...', 'Updating Goldengames PS5 Autoloader...')
installer_text = installer_text.replace('Installing WebKit Autoloader App...', 'Installing Goldengames PS5 Autoloader...')
installer_text = installer_text.replace('WebKit Autoloader App Ready!', 'Goldengames PS5 Autoloader Ready!')
installer_c.write_text(installer_text, encoding='utf-8')

text = registry.read_text(encoding='utf-8')
old = '''    lines.append(slopkit_iframe_url(app_dir))\n    lines.append(umtx2_iframe_url(app_dir))\n'''
new = '''    # Goldengames supports choosing the autoload payload from the dashboard.\n    # AppCache matches the iframe URL including its query string, so cache all\n    # supported autoload variants rather than only upstream payload.elf.\n    for payload_name in ("payload.elf", "etahen-2.5B.bin", "kstuff-1.10.elf"):\n        lines.append(slopkit_iframe_url(app_dir).replace("autoload=payload.elf", "autoload=" + payload_name))\n        lines.append(umtx2_iframe_url(app_dir).replace("autoload=payload.elf", "autoload=" + payload_name))\n'''
if old not in text:
    raise SystemExit('expected registry hook not found; upstream changed')
registry.write_text(text.replace(old, new, 1), encoding='utf-8')

# Critical UMTX2 fix for Goldengames AUTO JAILBREAK:
# upstream probes elfldr near the beginning of main() and stores the result in
# is_elfldr_running. On a fresh jailbreak that value is false, then the kernel
# chain starts elfldr later, but the upstream autoload block still tests the
# stale false value. Result: the kernel/kstuff stage succeeds, while etaHEN is
# never sent. Re-probe immediately before autoload so etaHEN is dispatched to
# the elfldr that the chain just started.
patch_text = umtx_patch.read_text(encoding='utf-8')
old_probe = '''+    var wkalAutoloadName = new URLSearchParams(location.search).get("autoload") || sessionStorage.getItem("wkal_autoload");\r\n+    if (wkalAutoloadName && is_elfldr_running) {\r\n'''
new_probe = '''+    var wkalAutoloadName = new URLSearchParams(location.search).get("autoload") || sessionStorage.getItem("wkal_autoload");\r\n+    // Goldengames: refresh elfldr state here. The initial probe happened before\r\n+    // the full kernel chain spawned elfldr, so that cached boolean is stale on\r\n+    // a fresh jailbreak and would incorrectly suppress etaHEN autoload.\r\n+    var wkalElfldrReady = await probe_sb_elfldr();\r\n+    await log("autoload: refreshed elfldr state: " + wkalElfldrReady, LogLevel.INFO);\r\n+    if (wkalAutoloadName && wkalElfldrReady) {\r\n'''
if old_probe not in patch_text:
    raise SystemExit('expected UMTX2 autoload probe hook not found; upstream changed')
patch_text = patch_text.replace(old_probe, new_probe, 1)
patch_text = patch_text.replace(
    '+    } else if (wkalAutoloadName && !is_elfldr_running) {\\r\\n',
    '+    } else if (wkalAutoloadName && !wkalElfldrReady) {\\r\\n',
    1
)
umtx_patch.write_text(patch_text, encoding='utf-8')

print('Goldengames build patches applied:')
print('  native WKAL_TITLE_ID: GGAU00001')
print('  param.json titleId: GGAU00001')
print('  titleName: Goldengames PS5 Autoloader')
print('  AppCache autoload variants: payload.elf, etaHEN 2.5B, Kstuff 1.10')
print('  UMTX2 autoload: refresh elfldr state before sending etaHEN')
