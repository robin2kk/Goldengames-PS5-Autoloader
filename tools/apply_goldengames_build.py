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
umtx_apply = root / 'tools' / 'apply_umtx2_patch.sh'

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

wkali_text = wkali_h.read_text(encoding='utf-8')
old_title = '#define WKAL_TITLE_ID "WKAL00001"'
new_title = '#define WKAL_TITLE_ID "GGAU00001"'
if old_title not in wkali_text and new_title not in wkali_text:
    raise SystemExit('WKAL_TITLE_ID definition not found; upstream changed')
wkali_h.write_text(wkali_text.replace(old_title, new_title, 1), encoding='utf-8')

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

# Keep upstream patches/umtx2-autoload.patch byte-for-byte intact so git apply
# remains valid.  Instead, add a Goldengames post-patch edit to the upstream
# preparation script.  That edit runs only AFTER WKAL's patch has applied to
# frontend/autoloader/umtx2/main.js.
apply_text = umtx_apply.read_text(encoding='utf-8')
marker = '# 4. Sanity check: the patched main.js must carry our integration markers, the\n'
if marker not in apply_text:
    raise SystemExit('UMTX2 post-patch insertion point not found; upstream changed')
post_patch = r'''# Goldengames: the first elfldr probe in UMTX2 happens before the full kernel
# chain starts elfldr.  Refresh it immediately before WKAL autoload so a fresh
# AUTO JAILBREAK can send etaHEN 2.5B to port 9021.
python3 - "$DEST/main.js" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')
old = ''' + "'''" + r'''    var wkalAutoloadName = new URLSearchParams(location.search).get("autoload") || sessionStorage.getItem("wkal_autoload");
    if (wkalAutoloadName && is_elfldr_running) {
''' + "'''" + r'''
new = ''' + "'''" + r'''    var wkalAutoloadName = new URLSearchParams(location.search).get("autoload") || sessionStorage.getItem("wkal_autoload");
    // Goldengames: refresh elfldr after the kernel chain before etaHEN autoload.
    var wkalElfldrReady = await probe_sb_elfldr();
    await log("autoload: refreshed elfldr state: " + wkalElfldrReady, LogLevel.INFO);
    if (wkalAutoloadName && wkalElfldrReady) {
''' + "'''" + r'''
if old not in s:
    raise SystemExit('Goldengames UMTX2 autoload hook not found after upstream patch')
s = s.replace(old, new, 1)
old_fail = '    } else if (wkalAutoloadName && !is_elfldr_running) {'
new_fail = '    } else if (wkalAutoloadName && !wkalElfldrReady) {'
if old_fail not in s:
    raise SystemExit('Goldengames UMTX2 failure hook not found after upstream patch')
s = s.replace(old_fail, new_fail, 1)
p.write_text(s, encoding='utf-8')
print('umtx2: Goldengames refreshed-elfldr etaHEN autoload fix applied.')
PY

'''
if 'Goldengames refreshed-elfldr etaHEN autoload fix applied' not in apply_text:
    apply_text = apply_text.replace(marker, post_patch + marker, 1)
umtx_apply.write_text(apply_text, encoding='utf-8')

print('Goldengames build patches applied:')
print('  native WKAL_TITLE_ID: GGAU00001')
print('  param.json titleId: GGAU00001')
print('  titleName: Goldengames PS5 Autoloader')
print('  AppCache autoload variants: payload.elf, etaHEN 2.5B, Kstuff 1.10')
print('  UMTX2 autoload: post-patch elfldr refresh before sending etaHEN')
