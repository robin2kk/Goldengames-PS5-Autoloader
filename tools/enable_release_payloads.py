#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: enable_release_payloads.py <upstream-root>')

root = Path(sys.argv[1]).resolve()
app = root / 'frontend' / 'autoloader' / 'app.js'
registry = root / 'tools' / 'gen_file_registry.py'

# Add manual dashboard routes while keeping etaHEN 2.5B as AUTO JAILBREAK.
app_text = app.read_text(encoding='utf-8')
old_routes = """        if (key === 'etahen') choosePayload('etahen-2.5B.bin', 'etaHEN 2.5B', false);\n        else if (key === 'kstuff') choosePayload('kstuff-1.10.elf', 'Kstuff Lite 1.10', false);\n        else choosePayload('payload.elf', 'Payload Manager', false);"""
new_routes = """        if (key === 'etahen') choosePayload('etahen-2.5B.bin', 'etaHEN 2.5B', false);\n        else if (key === 'etahen26') choosePayload('etahen-2.6B.bin', 'etaHEN 2.6B', false);\n        else if (key === 'kstuff') choosePayload('kstuff-1.10.elf', 'Kstuff Lite 1.10', false);\n        else if (key === 'pldmgr') choosePayload('pldmgr_v0.5.1.elf', 'Payload Manager 0.5.1', false);\n        else if (key === 'websrv') choosePayload('websrv-ps5.elf', 'WebSrv PS5', false);\n        else choosePayload('payload.elf', 'Payload Manager', false);"""
if old_routes not in app_text:
    if "choosePayload('etahen-2.6B.bin'" not in app_text:
        raise SystemExit('Goldengames dashboard payload routing hook not found')
else:
    app_text = app_text.replace(old_routes, new_routes, 1)
app.write_text(app_text, encoding='utf-8')

# Make every selectable payload URL part of AppCache so manual payloads work offline.
reg_text = registry.read_text(encoding='utf-8')
old_variants = '("payload.elf", "etahen-2.5B.bin", "kstuff-1.10.elf")'
new_variants = '("payload.elf", "etahen-2.5B.bin", "etahen-2.6B.bin", "kstuff-1.10.elf", "pldmgr_v0.5.1.elf", "websrv-ps5.elf")'
if old_variants not in reg_text:
    if '"etahen-2.6B.bin"' not in reg_text or '"pldmgr_v0.5.1.elf"' not in reg_text or '"websrv-ps5.elf"' not in reg_text:
        raise SystemExit('Goldengames AppCache payload variant hook not found')
else:
    reg_text = reg_text.replace(old_variants, new_variants, 1)
registry.write_text(reg_text, encoding='utf-8')

print('Goldengames release payloads enabled:')
print('  AUTO JAILBREAK: etaHEN 2.5B (unchanged)')
print('  Manual: etaHEN 2.6B, Kstuff Lite 1.10, Payload Manager 0.5.1, WebSrv PS5')
