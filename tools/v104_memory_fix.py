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
# PSFree/UMTX2 for every manual payload was causing repeated UaF retries and
# contributing to the PS5 "not enough free system memory" condition.
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

# Do not destroy the live UMTX2 iframe when returning to the dashboard.
return_old = """  function returnToGoldengamesMenu() {\n    try { exploitEl.src = 'about:blank'; } catch (e) { }\n    loaderEl.hidden = true;"""
return_new = """  function returnToGoldengamesMenu() {\n    if (!persistentSenderReady) {\n      try { exploitEl.src = 'about:blank'; } catch (e) { }\n    }\n    loaderEl.hidden = true;"""
if return_old not in s:
    raise SystemExit('v1.0.4 return-to-menu anchor not found')
s = s.replace(return_old, return_new, 1)

# Upstream also unloads the UMTX2 iframe immediately after a successful
# autoload. Guard that unload so the proven runtime can remain available.
unload_old = """      if (exploitMode === 'umtx2') {\n        try { exploitEl.src = 'about:blank'; } catch (e) { }\n      }"""
unload_new = """      if (exploitMode === 'umtx2' && !persistentSenderReady) {\n        try { exploitEl.src = 'about:blank'; } catch (e) { }\n      }"""
if unload_old not in s:
    raise SystemExit('v1.0.4 upstream UMTX2 unload anchor not found')
s = s.replace(unload_old, unload_new, 1)

# Direct-send helper: uses the already-running UMTX2 main loop. No second
# PSFree pass and no second kernel exploit while the persistent runtime lives.
fn_anchor = "  function choosePayload(payload, label, forceFullJailbreak) {\n"
helper = r'''  function sendViaPersistentUmtx(payload, label) {
    finished = false;
    chainStarted = true;
    loaderEl.hidden = false;
    if (dashboardEl) dashboardEl.hidden = true;
    if (statusValueEl) statusValueEl.textContent = 'SENDING';
    if (runTitleEl) runTitleEl.textContent = label;
    var fw = detectFirmware();
    if (runSubtitleEl) runSubtitleEl.textContent = (fw ? ('Firmware ' + fw.str) : 'Firmware unknown') + ' · Direct 9021 sender';
    uiLog('Persistent sender: reusing live UMTX2 runtime; PSFree/kernel exploit skipped.', 'success');
    uiLog('Selected payload: ' + payload, 'success');
    updateProgress(15, 'Sending directly to elfldr 9021...');

    if (persistentSendTimer) clearTimeout(persistentSendTimer);
    persistentSendTimer = setTimeout(function () {
      if (finished) return;
      persistentSenderReady = false;
      chainStarted = false;
      if (statusValueEl) statusValueEl.textContent = 'SESSION LOST';
      uiLog('[ERROR] Persistent sender did not respond. Auto Jailbreak can rebuild the session.', 'error');
      showGoldengamesNotification('SESSION LOST', 'Live sender stopped responding · run Auto Jailbreak again');
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

# Inject direct-send selection inside choosePayload without depending on which
# helper functions v1.0.2 inserted after it.
choose_pos = s.find(fn_anchor)
run_pos = s.find("    runSelectedPayload();\n", choose_pos)
if choose_pos < 0 or run_pos < 0:
    raise SystemExit('v1.0.4 payload dispatch anchor not found')
direct_block = """    if (selectedManual && persistentSenderReady && exploitMode === 'umtx2') {\n      sendViaPersistentUmtx(selectedPayload, selectedLabel);\n      return;\n    }\n\n"""
s = s[:run_pos] + direct_block + s[run_pos:]

# Any explicit full Auto Jailbreak tears down the old persistent runtime.
auto_anchor = """    if (autoBtn) autoBtn.addEventListener('click', function () {\n      setJailbreakState(false);"""
auto_new = """    if (autoBtn) autoBtn.addEventListener('click', function () {\n      persistentSenderReady = false;\n      try { exploitEl.src = 'about:blank'; } catch (e) { }\n      chainStarted = false;\n      setJailbreakState(false);"""
if auto_anchor not in s:
    raise SystemExit('v1.0.4 Auto Jailbreak button anchor not found')
s = s.replace(auto_anchor, auto_new, 1)

# Clear direct-send timeout whenever an autoload/direct-send result arrives.
result_anchor = """  function onAutoloadResult(data) {\n    if (finished) return;\n    finished = true;"""
result_new = """  function onAutoloadResult(data) {\n    if (finished) return;\n    finished = true;\n    if (persistentSendTimer) {\n      clearTimeout(persistentSendTimer);\n      persistentSendTimer = null;\n    }"""
if result_anchor not in s:
    raise SystemExit('v1.0.4 result timer anchor not found')
s = s.replace(result_anchor, result_new, 1)

app.write_text(s, encoding='utf-8')

# Extend the patched UMTX2 main loop with a parent-message bridge. It queues a
# normal WKAL payload request through the runtime that is already alive.
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
    // Goldengames v1.0.4: accept later manual payloads from the parent
    // dashboard without re-running PSFree or the kernel exploit.
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
print('  manual payloads reuse the live runtime and send to elfldr:9021')
print('  manual payloads no longer start another PSFree/UMTX2 pass while sender is alive')
print('  dead persistent sender times out instead of entering repeated WebKit retries')
