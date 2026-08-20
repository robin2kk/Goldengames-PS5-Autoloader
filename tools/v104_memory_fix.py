#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v104_memory_fix.py <upstream-root>')

root = Path(sys.argv[1]).resolve()
app = root / 'frontend' / 'autoloader' / 'app.js'
umtx_apply = root / 'tools' / 'apply_umtx2_patch.sh'

s = app.read_text(encoding='utf-8')

# Keep the successful UMTX2 runtime alive after Auto Jailbreak. Re-running
# PSFree/UMTX2 for every manual payload was the main source of repeated UaF
# retries and PS5 "not enough free system memory" dialogs.
anchor = "  var autoJailbreakRetryCount = 0;\n"
insert = anchor + "  var persistentSenderReady = false;\n  var persistentSendTimer = null;\n"
if anchor not in s:
    raise SystemExit('v1.0.4 persistent sender variable anchor not found')
s = s.replace(anchor, insert, 1)

# A successful etaHEN Auto Jailbreak leaves the live UMTX2 iframe/main loop
# resident so later payloads can be queued directly to elfldr:9021.
success_anchor = """      if (selectedPayload === 'etahen-2.5B.bin') {\n        autoJailbreakRetryCount = 0;\n        setJailbreakState(true);"""
success_new = """      if (selectedPayload === 'etahen-2.5B.bin') {\n        autoJailbreakRetryCount = 0;\n        persistentSenderReady = (exploitMode === 'umtx2');\n        setJailbreakState(true);"""
if success_anchor not in s:
    raise SystemExit('v1.0.4 etaHEN success anchor not found')
s = s.replace(success_anchor, success_new, 1)

# Do not destroy the UMTX2 iframe after a successful jailbreak. Preserve its
# primitives/main loop for direct sender use; only blank it for non-persistent
# paths.
return_old = """  function returnToGoldengamesMenu() {\n    try { exploitEl.src = 'about:blank'; } catch (e) { }\n    loaderEl.hidden = true;"""
return_new = """  function returnToGoldengamesMenu() {\n    if (!persistentSenderReady) {\n      try { exploitEl.src = 'about:blank'; } catch (e) { }\n    }\n    loaderEl.hidden = true;"""
if return_old not in s:
    raise SystemExit('v1.0.4 return-to-menu anchor not found')
s = s.replace(return_old, return_new, 1)

# Preserve chainStarted while the persistent iframe is alive.
s = s.replace("""    chainStarted = false;\n    finished = false;""",
              """    chainStarted = persistentSenderReady;\n    finished = false;""", 1)

# Direct-send helper: uses the already-running UMTX2 main loop. No PSFree,
# no WebKit exploit retry loop, no kernel exploit.
fn_anchor = "  function choosePayload(payload, label, forceFullJailbreak) {\n"
helper = r'''  function sendViaPersistentUmtx(payload, label) {
    finished = false;
    loaderEl.hidden = false;
    if (dashboardEl) dashboardEl.hidden = true;
    if (statusValueEl) statusValueEl.textContent = 'SENDING';
    if (runTitleEl) runTitleEl.textContent = label;
    if (runSubtitleEl) runSubtitleEl.textContent = 'Firmware ' + ((detectFirmware() || {}).str || 'Unknown') + ' · Direct 9021 sender';
    uiLog('Persistent sender: reusing live UMTX2 runtime; PSFree/kernel exploit skipped.', 'success');
    uiLog('Selected payload: ' + payload, 'success');
    updateProgress(15, 'Sending directly to elfldr 9021...');

    if (persistentSendTimer) clearTimeout(persistentSendTimer);
    persistentSendTimer = setTimeout(function () {
      if (finished) return;
      persistentSenderReady = false;
      chainStarted = false;
      if (statusValueEl) statusValueEl.textContent = 'SESSION LOST';
      uiLog('[ERROR] Persistent sender did not respond. Reopen Auto Jailbreak instead of retrying WebKit repeatedly.', 'error');
      showGoldengamesNotification('SESSION LOST', 'Live sender stopped responding · Auto Jailbreak is available');
      if (backButtonEl) backButtonEl.disabled = false;
    }, 10000);

    try {
      exploitEl.contentWindow.postMessage({
        type: 'goldengames-direct-send',
        payload: payload,
        label: label
      }, '*');
    } catch (e) {
      persistentSenderReady = false;
      chainStarted = false;
      if (persistentSendTimer) clearTimeout(persistentSendTimer);
      persistentSendTimer = null;
      onAutoloadResult({ ok: false, why: 'persistent sender unavailable' });
    }
  }

'''
if fn_anchor not in s:
    raise SystemExit('v1.0.4 choosePayload anchor not found')
s = s.replace(fn_anchor, helper + fn_anchor, 1)

# Use persistent direct-send for manual payloads when the initial jailbreak
# runtime is still alive.
call_anchor = """    runSelectedPayload();\n  }\n\n  function initGoldengamesMenu() {"""
call_new = """    if (selectedManual && persistentSenderReady && exploitMode === 'umtx2') {\n      sendViaPersistentUmtx(selectedPayload, selectedLabel);\n      return;\n    }\n\n    runSelectedPayload();\n  }\n\n  function initGoldengamesMenu() {"""
if call_anchor not in s:
    raise SystemExit('v1.0.4 payload dispatch anchor not found')
s = s.replace(call_anchor, call_new, 1)

# Any explicit full Auto Jailbreak must tear down the old persistent runtime.
auto_anchor = """    if (autoBtn) autoBtn.addEventListener('click', function () {\n      setJailbreakState(false);"""
auto_new = """    if (autoBtn) autoBtn.addEventListener('click', function () {\n      persistentSenderReady = false;\n      try { exploitEl.src = 'about:blank'; } catch (e) { }\n      chainStarted = false;\n      setJailbreakState(false);"""
if auto_anchor not in s:
    raise SystemExit('v1.0.4 Auto Jailbreak button anchor not found')
s = s.replace(auto_anchor, auto_new, 1)

# Clear the direct-send timeout whenever an autoload/direct-send result arrives.
result_anchor = """  function onAutoloadResult(data) {\n    if (finished) return;\n    finished = true;"""
result_new = """  function onAutoloadResult(data) {\n    if (finished) return;\n    finished = true;\n    if (persistentSendTimer) {\n      clearTimeout(persistentSendTimer);\n      persistentSendTimer = null;\n    }"""
if result_anchor not in s:
    raise SystemExit('v1.0.4 result timer anchor not found')
s = s.replace(result_anchor, result_new, 1)

app.write_text(s, encoding='utf-8')

# Extend the patched UMTX2 main loop with a parent-message bridge. It simply
# queues a normal payload request through the already-running main loop.
sh = umtx_apply.read_text(encoding='utf-8')
marker = '# 4. Sanity check: the patched main.js must carry our integration markers, the\n'
if marker not in sh:
    raise SystemExit('v1.0.4 UMTX insertion marker not found')

block = r'''# Goldengames v1.0.4 persistent direct sender bridge.
python3 - "$DEST/main.js" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')
anchor = ''' + "'''" + r'''    window.addEventListener(MAINLOOP_EXECUTE_PAYLOAD_REQUEST, async function (event) {
        /** @type {PayloadInfo} */
        let payload_info = event.detail;
        let toast = showToast(`${payload_info.displayTitle}: Waiting in queue...`, -1);
        queue.push({ payload_info, toast });
    });
''' + "'''" + r'''
replacement = anchor + ''' + "'''" + r'''
    // Goldengames v1.0.4: keep this runtime alive after etaHEN and accept
    // later manual payloads from the parent dashboard without rerunning PSFree.
    window.addEventListener("message", function (event) {
        var data = event.data || {};
        if (data.type !== "goldengames-direct-send") return;
        var name = String(data.payload || "");
        if (!name) return;
        var title = String(data.label || name);
        try { window.parent.postMessage({ type: "goldengames-diag", stage: "persistent-dispatch", payload: name, port: 9021 }, "*"); } catch (e) { }
        window.dispatchEvent(new CustomEvent(MAINLOOP_EXECUTE_PAYLOAD_REQUEST, {
            detail: {
                displayTitle: title,
                fileName: name,
                wkalBase: "../payloads/",
                toPort: 9021,
                wkalAutoload: true
            }
        }));
    });
''' + "'''" + r'''
if anchor not in s:
    raise SystemExit('v1.0.4 UMTX queue-listener anchor not found')
s = s.replace(anchor, replacement, 1)
p.write_text(s, encoding='utf-8')
print('umtx2: Goldengames v1.0.4 persistent direct sender bridge applied.')
PY

'''
if 'Goldengames v1.0.4 persistent direct sender bridge applied' not in sh:
    sh = sh.replace(marker, block + marker, 1)
umtx_apply.write_text(sh, encoding='utf-8')

print('Goldengames v1.0.4 memory/stability fix applied:')
print('  successful UMTX2 runtime stays alive after etaHEN')
print('  manual payloads use direct persistent sender to elfldr:9021')
print('  manual payloads no longer rerun PSFree/UMTX2 while sender is alive')
print('  dead persistent sender times out instead of entering repeated WebKit retries')
