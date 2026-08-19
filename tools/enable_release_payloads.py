#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: enable_release_payloads.py <upstream-root>')

root = Path(sys.argv[1]).resolve()
app = root / 'frontend' / 'autoloader' / 'app.js'
registry = root / 'tools' / 'gen_file_registry.py'

# Add manual dashboard routes while keeping etaHEN 2.5B as AUTO JAILBREAK.
# IMPORTANT: do NOT replace the base RC3 reboot-safe jailbreak-session logic.
# RC5's pagehide/beforeunload reopen-ticket layer caused sluggish reopen behavior
# on console, so RC6 keeps the known-good v2 process-epoch logic from the base patch.
app_text = app.read_text(encoding='utf-8')
old_routes = """        if (key === 'etahen') choosePayload('etahen-2.5B.bin', 'etaHEN 2.5B', false);\n        else if (key === 'kstuff') choosePayload('kstuff-1.10.elf', 'Kstuff Lite 1.10', false);\n        else choosePayload('payload.elf', 'Payload Manager', false);"""
rc4_routes = """        if (key === 'etahen') choosePayload('etahen-2.5B.bin', 'etaHEN 2.5B', false);\n        else if (key === 'etahen26') choosePayload('etahen-2.6B.bin', 'etaHEN 2.6B', false);\n        else if (key === 'kstuff') choosePayload('kstuff-1.10.elf', 'Kstuff Lite 1.10', false);\n        else if (key === 'pldmgr') choosePayload('pldmgr_v0.5.1.elf', 'Payload Manager 0.5.1', false);\n        else if (key === 'websrv') choosePayload('websrv-ps5.elf', 'WebSrv PS5', false);\n        else choosePayload('payload.elf', 'Payload Manager', false);"""
rc6_routes = """        if (key === 'etahen') choosePayload('etahen-2.5B.bin', 'etaHEN 2.5B', false);\n        else if (key === 'etahen26') choosePayload('etahen-2.6B.bin', 'etaHEN 2.6B', false);\n        else if (key === 'kstuff') choosePayload('kstuff-1.10.elf', 'Kstuff Lite 1.10', false);\n        else if (key === 'pldmgr') choosePayload('pldmgr_v0.5.1.elf', 'Payload Manager 0.5.1', false);\n        else if (key === 'websrv') choosePayload('websrv-ps5.elf', 'WebSrv PS5', false);\n        else if (key === 'shadowmount') choosePayload('shadowmountplus_v1.7alpha8.elf', 'ShadowMountPlus 1.7 alpha8', false);\n        else choosePayload('payload.elf', 'Payload Manager', false);"""
if rc4_routes in app_text:
    app_text = app_text.replace(rc4_routes, rc6_routes, 1)
elif old_routes in app_text:
    app_text = app_text.replace(old_routes, rc6_routes, 1)
elif "choosePayload('shadowmountplus_v1.7alpha8.elf'" not in app_text:
    raise SystemExit('Goldengames dashboard payload routing hook not found')

# Guard against accidentally re-introducing the RC5 reopen-ticket hooks.
if 'goldengames:jailbreak-reopen-v1' in app_text or "addEventListener('pagehide'" in app_text or "addEventListener('beforeunload'" in app_text:
    raise SystemExit('RC5 reopen-ticket hooks must not be present in RC6')
if "JAILBREAK_LEASE_KEY = 'goldengames:jailbreak-lease-v2'" not in app_text:
    raise SystemExit('RC3 reboot-safe v2 lease logic is missing')

app.write_text(app_text, encoding='utf-8')

# Make every selectable payload URL part of AppCache so manual payloads work offline.
reg_text = registry.read_text(encoding='utf-8')
old_variants = '("payload.elf", "etahen-2.5B.bin", "kstuff-1.10.elf")'
rc4_variants = '("payload.elf", "etahen-2.5B.bin", "etahen-2.6B.bin", "kstuff-1.10.elf", "pldmgr_v0.5.1.elf", "websrv-ps5.elf")'
rc6_variants = '("payload.elf", "etahen-2.5B.bin", "etahen-2.6B.bin", "kstuff-1.10.elf", "pldmgr_v0.5.1.elf", "websrv-ps5.elf", "shadowmountplus_v1.7alpha8.elf")'
if rc4_variants in reg_text:
    reg_text = reg_text.replace(rc4_variants, rc6_variants, 1)
elif old_variants in reg_text:
    reg_text = reg_text.replace(old_variants, rc6_variants, 1)
elif '"shadowmountplus_v1.7alpha8.elf"' not in reg_text:
    raise SystemExit('Goldengames AppCache payload variant hook not found')
registry.write_text(reg_text, encoding='utf-8')

print('Goldengames RC6 payloads enabled:')
print('  AUTO JAILBREAK: etaHEN 2.5B (unchanged)')
print('  Manual: etaHEN 2.6B, Kstuff Lite 1.10, Payload Manager 0.5.1, WebSrv PS5, ShadowMountPlus 1.7 alpha8')
print('  Session handling: restored RC3 reboot-safe v2 process-epoch logic; RC5 reopen hooks removed')
