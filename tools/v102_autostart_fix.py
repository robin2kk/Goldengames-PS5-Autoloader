#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v102_autostart_fix.py <upstream-root>')

root = Path(sys.argv[1]).resolve()
app = root / 'frontend' / 'autoloader' / 'app.js'
umtx_apply = root / 'tools' / 'apply_umtx2_patch.sh'

s = app.read_text(encoding='utf-8')

# v1.0.2: a cached etaHEN marker is only a hint. On UMTX2 firmwares, verify
# the live elfldr socket before suppressing Auto Jailbreak. The probe runs in
# wk-only mode, so it never launches the kernel exploit.
anchor = "  var selectedManual = false;\n"
insert = anchor + "  var startupSessionProbe = false;\n  var startupSessionProbeTimer = null;\n"
if anchor not in s:
    raise SystemExit('v1.0.2 app variable anchor not found')
s = s.replace(anchor, insert, 1)

fn_anchor = "  function initGoldengamesMenu() {\n"
functions = r'''  function startFreshAutoJailbreak(reason) {
    startupSessionProbe = false;
    if (startupSessionProbeTimer) {
      clearTimeout(startupSessionProbeTimer);
      startupSessionProbeTimer = null;
    }
    try {
      sessionStorage.removeItem('goldengames_probe_only');
      sessionStorage.removeItem('goldengames_sender_only');
    } catch (e) { }
    try { exploitEl.src = 'about:blank'; } catch (e) { }
    setJailbreakState(false);
    if (statusValueEl) statusValueEl.textContent = 'AUTO START';
    if (reason) showGoldengamesNotification('AUTO JAILBREAK', reason);
    setTimeout(function () {
      if (!chainStarted) choosePayload('etahen-2.5B.bin', 'AUTO JAILBREAK · etaHEN 2.5B', true);
    }, 350);
  }

  function verifyCachedUmtxSession() {
    startupSessionProbe = true;
    if (statusValueEl) statusValueEl.textContent = 'VERIFYING';
    showGoldengamesNotification('VERIFYING SESSION', 'Checking live elfldr 9021 before skipping Auto Jailbreak');
    try {
      sessionStorage.setItem('goldengames_probe_only', '1');
      sessionStorage.setItem('on_load_autorun', 'wkonly');
      sessionStorage.removeItem('goldengames_sender_only');
      /* This exact URL is already present in the offline AppCache registry. */
      exploitEl.src = 'umtx2/index.html?autoload=etahen-2.5B.bin&v=1';
    } catch (e) {
      startFreshAutoJailbreak('Session probe could not start · running full jailbreak');
      return;
    }

    startupSessionProbeTimer = setTimeout(function () {
      if (!startupSessionProbe) return;
      startFreshAutoJailbreak('No live-session response · running full jailbreak');
    }, 18000);
  }

  function handleStartupSessionProbe(event) {
    var data = event.data || {};
    if (data.type !== 'goldengames-session-probe' || !startupSessionProbe) return;

    startupSessionProbe = false;
    if (startupSessionProbeTimer) {
      clearTimeout(startupSessionProbeTimer);
      startupSessionProbeTimer = null;
    }
    try {
      sessionStorage.removeItem('goldengames_probe_only');
      sessionStorage.removeItem('on_load_autorun');
      exploitEl.src = 'about:blank';
    } catch (e) { }

    if (data.active === true) {
      liveJailbreakState = true;
      if (statusValueEl) statusValueEl.textContent = 'SESSION READY';
      showGoldengamesNotification('SESSION READY', 'elfldr 9021 is live · Auto Jailbreak skipped');
      return;
    }

    startFreshAutoJailbreak('Previous session ended · starting etaHEN 2.5B');
  }

'''
if fn_anchor not in s:
    raise SystemExit('v1.0.2 init anchor not found')
s = s.replace(fn_anchor, functions + fn_anchor, 1)

# Register the probe result listener at menu initialization.
listener_anchor = "  function initGoldengamesMenu() {\n    var fw = detectFirmware();\n"
listener_new = "  function initGoldengamesMenu() {\n    window.addEventListener('message', handleStartupSessionProbe);\n    var fw = detectFirmware();\n"
if listener_anchor not in s:
    raise SystemExit('v1.0.2 init listener anchor not found')
s = s.replace(listener_anchor, listener_new, 1)

# RC7 suppressed Auto Jailbreak purely from localStorage. v1.0.2 verifies the
# live port first on UMTX2 firmware. Non-UMTX2 behavior remains unchanged.
old = """        if (jailbroken) {\n          showGoldengamesNotification('SESSION READY', 'Auto Jailbreak skipped · payload sender will verify elfldr 9021');\n          return;\n        }\n\n        if (picked && !chainStarted) {"""
new = """        if (jailbroken) {\n          if (picked === 'umtx2') {\n            verifyCachedUmtxSession();\n            return;\n          }\n          showGoldengamesNotification('SESSION READY', 'Cached session marker present · Auto Jailbreak skipped');\n          return;\n        }\n\n        if (picked && !chainStarted) {"""
if old not in s:
    raise SystemExit('v1.0.2 RC7 startup suppression block not found')
s = s.replace(old, new, 1)

app.write_text(s, encoding='utf-8')

# Add a probe-only exit to the UMTX2 runtime after its native 9021 probe and
# before any kernel-exploit decision. This reuses the already proven socket
# probe but never sends a payload or runs UMTX2 when goldengames_probe_only=1.
sh = umtx_apply.read_text(encoding='utf-8')
marker = '# 4. Sanity check: the patched main.js must carry our integration markers, the\n'
if marker not in sh:
    raise SystemExit('v1.0.2 UMTX insertion marker not found')

block = r'''# Goldengames v1.0.2 startup live-session probe.
python3 - "$DEST/main.js" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')
anchor = ''' + "'''" + r'''    let is_elfldr_running = await probe_sb_elfldr();
    await log("is elfldr running: " + is_elfldr_running, LogLevel.INFO);
''' + "'''" + r'''
replacement = ''' + "'''" + r'''    let is_elfldr_running = await probe_sb_elfldr();
    await log("is elfldr running: " + is_elfldr_running, LogLevel.INFO);

    var goldengamesProbeOnly = false;
    try { goldengamesProbeOnly = sessionStorage.getItem("goldengames_probe_only") === "1"; } catch (e) { }
    if (goldengamesProbeOnly) {
        await log("Goldengames v1.0.2: startup probe only; kernel exploit will not run.", LogLevel.INFO);
        try { sessionStorage.removeItem("goldengames_probe_only"); } catch (e) { }
        try { window.parent.postMessage({ type: "goldengames-session-probe", active: is_elfldr_running === true, port: 9021 }, "*"); } catch (e) { }
        return;
    }
''' + "'''" + r'''
if anchor not in s:
    raise SystemExit('v1.0.2 UMTX probe anchor not found')
s = s.replace(anchor, replacement, 1)
p.write_text(s, encoding='utf-8')
print('umtx2: Goldengames v1.0.2 startup 9021 probe-only mode applied.')
PY

'''
if 'Goldengames v1.0.2 startup 9021 probe-only mode applied' not in sh:
    sh = sh.replace(marker, block + marker, 1)
umtx_apply.write_text(sh, encoding='utf-8')

print('Goldengames v1.0.2 Auto-Start fix applied:')
print('  cached RC7 marker no longer blindly suppresses Auto Jailbreak on UMTX2')
print('  startup performs wk-only elfldr:9021 probe')
print('  live 9021 -> SESSION READY, no repeated jailbreak')
print('  closed 9021 -> stale marker cleared, etaHEN 2.5B Auto Jailbreak starts')
