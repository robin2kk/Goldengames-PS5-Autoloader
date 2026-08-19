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
rc4_routes = """        if (key === 'etahen') choosePayload('etahen-2.5B.bin', 'etaHEN 2.5B', false);\n        else if (key === 'etahen26') choosePayload('etahen-2.6B.bin', 'etaHEN 2.6B', false);\n        else if (key === 'kstuff') choosePayload('kstuff-1.10.elf', 'Kstuff Lite 1.10', false);\n        else if (key === 'pldmgr') choosePayload('pldmgr_v0.5.1.elf', 'Payload Manager 0.5.1', false);\n        else if (key === 'websrv') choosePayload('websrv-ps5.elf', 'WebSrv PS5', false);\n        else choosePayload('payload.elf', 'Payload Manager', false);"""
rc5_routes = """        if (key === 'etahen') choosePayload('etahen-2.5B.bin', 'etaHEN 2.5B', false);\n        else if (key === 'etahen26') choosePayload('etahen-2.6B.bin', 'etaHEN 2.6B', false);\n        else if (key === 'kstuff') choosePayload('kstuff-1.10.elf', 'Kstuff Lite 1.10', false);\n        else if (key === 'pldmgr') choosePayload('pldmgr_v0.5.1.elf', 'Payload Manager 0.5.1', false);\n        else if (key === 'websrv') choosePayload('websrv-ps5.elf', 'WebSrv PS5', false);\n        else if (key === 'shadowmount') choosePayload('shadowmountplus_v1.7alpha8.elf', 'ShadowMountPlus 1.7 alpha8', false);\n        else choosePayload('payload.elf', 'Payload Manager', false);"""
if rc4_routes in app_text:
    app_text = app_text.replace(rc4_routes, rc5_routes, 1)
elif old_routes in app_text:
    app_text = app_text.replace(old_routes, rc5_routes, 1)
elif "choosePayload('shadowmountplus_v1.7alpha8.elf'" not in app_text:
    raise SystemExit('Goldengames dashboard payload routing hook not found')

# RC5 session-resume logic. The v2 process epoch changes when the PS5 relaunches
# the cached web app, so it incorrectly starts AUTO JAILBREAK again. RC5 uses a
# short reopen ticket written when a known-jailbroken page closes. A cold launch
# without a fresh ticket goes straight to AUTO JAILBREAK as before.
start = app_text.find("  var JAILBREAK_LEASE_KEY = 'goldengames:jailbreak-lease-v2';\n")
end = app_text.find("  function showGoldengamesNotification", start)
if start != -1 and end != -1:
    session_block = """  var JAILBREAK_LEASE_KEY = 'goldengames:jailbreak-lease-v3';
  var JAILBREAK_REOPEN_KEY = 'goldengames:jailbreak-reopen-v1';
  var JAILBREAK_LEASE_MS = 12 * 60 * 60 * 1000;
  var JAILBREAK_REOPEN_MS = 90 * 1000;

  function getJailbreakLease() {
    try {
      var raw = localStorage.getItem(JAILBREAK_LEASE_KEY);
      var reopenRaw = localStorage.getItem(JAILBREAK_REOPEN_KEY);
      if (!raw || !reopenRaw) return false;
      var data = JSON.parse(raw);
      var stamp = parseInt(data.stamp, 10);
      var reopenStamp = parseInt(reopenRaw, 10);
      var age = Date.now() - stamp;
      var reopenAge = Date.now() - reopenStamp;
      if (!stamp || age < 0 || age > JAILBREAK_LEASE_MS || !reopenStamp || reopenStamp < stamp || reopenAge < 0 || reopenAge > JAILBREAK_REOPEN_MS) {
        if (age > JAILBREAK_LEASE_MS || age < 0) localStorage.removeItem(JAILBREAK_LEASE_KEY);
        localStorage.removeItem(JAILBREAK_REOPEN_KEY);
        return false;
      }
      return true;
    } catch (e) {
      try { localStorage.removeItem(JAILBREAK_REOPEN_KEY); } catch (ignore) { }
      return false;
    }
  }

  function hasJailbreakState() {
    return liveJailbreakState === true || getJailbreakLease();
  }

  function setJailbreakState(active) {
    liveJailbreakState = active === true;
    try {
      if (active) {
        localStorage.setItem(JAILBREAK_LEASE_KEY, JSON.stringify({ stamp: Date.now() }));
        localStorage.removeItem(JAILBREAK_REOPEN_KEY);
      } else {
        localStorage.removeItem(JAILBREAK_LEASE_KEY);
        localStorage.removeItem(JAILBREAK_REOPEN_KEY);
      }
    } catch (e) { }
  }

  function armJailbreakReopenTicket() {
    if (!liveJailbreakState) return;
    try { localStorage.setItem(JAILBREAK_REOPEN_KEY, String(Date.now())); } catch (e) { }
  }

  window.addEventListener('pagehide', armJailbreakReopenTicket);
  window.addEventListener('beforeunload', armJailbreakReopenTicket);

"""
    app_text = app_text[:start] + session_block + app_text[end:]
elif "goldengames:jailbreak-lease-v3" not in app_text:
    raise SystemExit('Goldengames RC5 session state hook not found')

# Once a fresh reopen ticket is accepted, keep the state live for that page so
# the next pagehide can arm another ticket and repeated close/reopen works.
needle = "    var jailbroken = hasJailbreakState();\n"
replacement = needle + "    if (jailbroken) liveJailbreakState = true;\n"
if replacement not in app_text:
    if needle not in app_text:
        raise SystemExit('Goldengames init jailbreak-state hook not found')
    app_text = app_text.replace(needle, replacement, 1)

app.write_text(app_text, encoding='utf-8')

# Make every selectable payload URL part of AppCache so manual payloads work offline.
reg_text = registry.read_text(encoding='utf-8')
old_variants = '("payload.elf", "etahen-2.5B.bin", "kstuff-1.10.elf")'
rc4_variants = '("payload.elf", "etahen-2.5B.bin", "etahen-2.6B.bin", "kstuff-1.10.elf", "pldmgr_v0.5.1.elf", "websrv-ps5.elf")'
rc5_variants = '("payload.elf", "etahen-2.5B.bin", "etahen-2.6B.bin", "kstuff-1.10.elf", "pldmgr_v0.5.1.elf", "websrv-ps5.elf", "shadowmountplus_v1.7alpha8.elf")'
if rc4_variants in reg_text:
    reg_text = reg_text.replace(rc4_variants, rc5_variants, 1)
elif old_variants in reg_text:
    reg_text = reg_text.replace(old_variants, rc5_variants, 1)
elif '"shadowmountplus_v1.7alpha8.elf"' not in reg_text:
    raise SystemExit('Goldengames AppCache payload variant hook not found')
registry.write_text(reg_text, encoding='utf-8')

print('Goldengames RC5 payloads/session mode enabled:')
print('  AUTO JAILBREAK: etaHEN 2.5B (unchanged)')
print('  Manual: etaHEN 2.6B, Kstuff Lite 1.10, Payload Manager 0.5.1, WebSrv PS5, ShadowMountPlus 1.7 alpha8')
print('  Reopen handling: short live-session ticket prevents immediate duplicate AUTO JAILBREAK')
