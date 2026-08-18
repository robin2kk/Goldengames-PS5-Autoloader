#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_upstream_frontend.py <upstream-root>')

root = Path(sys.argv[1]).resolve()
app = root / 'frontend' / 'autoloader' / 'app.js'
text = app.read_text(encoding='utf-8')

# Add Goldengames dashboard references immediately after the upstream iframe ref.
needle = "  var exploitEl = document.getElementById('exploit');\n"
insert = needle + """  var dashboardEl = document.getElementById('dashboard');
  var firmwareValueEl = document.getElementById('firmwareValue');
  var exploitValueEl = document.getElementById('exploitValue');
  var statusValueEl = document.getElementById('statusValue');
  var runTitleEl = document.getElementById('runTitle');
  var runSubtitleEl = document.getElementById('runSubtitle');
  var backButtonEl = document.getElementById('backButton');
  var notificationEl = document.getElementById('notification');
  var notificationTitleEl = document.getElementById('notificationTitle');
  var notificationTextEl = document.getElementById('notificationText');
  var selectedPayload = 'payload.elf';
  var selectedLabel = 'Payload Manager';
  var selectedManual = false;
  var liveJailbreakState = false;

  /* Never persist the jailbreak flag across document/app launches. The PS5
     browser can restore WebStorage after reboot, which made RC1 incorrectly
     skip Auto Jailbreak. A successful etaHEN delivery marks only this live
     dashboard instance; returning to the menu keeps manual sender mode, while
     opening the app again starts a fresh Auto Jailbreak as expected. */
  function hasJailbreakState() {
    return liveJailbreakState === true;
  }

  function setJailbreakState(active) {
    liveJailbreakState = active === true;
  }

  function showGoldengamesNotification(title, message) {
    if (!notificationEl) return;
    if (notificationTitleEl) notificationTitleEl.textContent = title;
    if (notificationTextEl) notificationTextEl.textContent = message;
    notificationEl.hidden = false;
    setTimeout(function () { notificationEl.hidden = true; }, 5500);
  }

  function returnToGoldengamesMenu() {
    try { exploitEl.src = 'about:blank'; } catch (e) { }
    loaderEl.hidden = true;
    if (dashboardEl) dashboardEl.hidden = false;
    if (backButtonEl) backButtonEl.disabled = true;
    chainStarted = false;
    finished = false;
    selectedManual = false;
    try {
      sessionStorage.removeItem('goldengames_sender_only');
      sessionStorage.removeItem('wkal_autoload');
      sessionStorage.removeItem('on_load_autorun');
    } catch (e) { }
    if (statusValueEl) statusValueEl.textContent = hasJailbreakState() ? 'JAILBROKEN' : 'READY';
  }
"""
if needle not in text:
    raise SystemExit('upstream exploit element hook not found')
text = text.replace(needle, insert, 1)

old_umtx = "  var UMTX2_URL =\n    'umtx2/index.html?autoload=payload.elf&v=1';"
new_umtx = "  function getUmtx2Url() {\n    return 'umtx2/index.html?autoload=' + encodeURIComponent(selectedPayload) + '&v=1';\n  }"
if old_umtx not in text:
    raise SystemExit('upstream UMTX2 URL hook not found')
text = text.replace(old_umtx, new_umtx, 1)

old_slop = "  var SLOPKIT_URL =\n    'slopkit/slopkit/poops.html?go=1&auto=1&production=1&trigger=netcontrol&attempts=8&only=ps0_preflight,ps1_prepare,ps3_stage0,ps4_validate,ps5_stage1,ps6_stage2,ps8_stage3,ps9_stage4,ps10_stage5&log=debug&payload=1&autoload=payload.elf&v=final';"
new_slop = "  function getSlopkitUrl() {\n    return 'slopkit/slopkit/poops.html?go=1&auto=1&production=1&trigger=netcontrol&attempts=8&only=ps0_preflight,ps1_prepare,ps3_stage0,ps4_validate,ps5_stage1,ps6_stage2,ps8_stage3,ps9_stage4,ps10_stage5&log=debug&payload=1&autoload=' + encodeURIComponent(selectedPayload) + '&v=final';\n  }"
if old_slop not in text:
    raise SystemExit('upstream SlopKit URL hook not found')
text = text.replace(old_slop, new_slop, 1)

text = text.replace('  function start() {\n', '  function runSelectedPayload() {\n', 1)
text = text.replace("    uiLog('WebKit Autoloader by PLK', 'success');", "    uiLog('Goldengames PS5 Autoloader', 'success');\n    uiLog('Selected payload: ' + selectedPayload, 'success');\n    if (selectedManual) uiLog('Manual sender mode: existing jailbreak detected; kernel exploit will be skipped.', 'success');", 1)
text = text.replace("    EXPLOIT_URL = picked === 'umtx2' ? UMTX2_URL : SLOPKIT_URL;", "    EXPLOIT_URL = picked === 'umtx2' ? getUmtx2Url() : getSlopkitUrl();", 1)
text = text.replace("        sessionStorage.setItem('wkal_autoload', 'payload.elf');", "        sessionStorage.setItem('wkal_autoload', selectedPayload);", 1)

text = text.replace(
    "    if (data.ok) {\n      uiLog('Payload loaded (' + data.bytes + ' bytes sent to elfldr).', 'success');",
    "    if (data.ok) {\n      if (selectedPayload === 'etahen-2.5B.bin') {\n        setJailbreakState(true);\n        if (statusValueEl) statusValueEl.textContent = 'JAILBROKEN';\n        showGoldengamesNotification('etaHEN 2.5B LAUNCHED', 'Jailbreak ready · Manual Payload Mode enabled');\n      } else {\n        if (statusValueEl) statusValueEl.textContent = 'PAYLOAD SENT';\n        showGoldengamesNotification(selectedLabel + ' SENT', 'Payload delivered to elfldr successfully');\n      }\n      uiLog(selectedLabel + ' loaded (' + data.bytes + ' bytes sent to elfldr).', 'success');",
    1
)
text = text.replace(
    "      updateProgress(100, 'Autoload finished.');",
    "      updateProgress(100, selectedPayload === 'etahen-2.5B.bin' ? 'etaHEN 2.5B launched successfully.' : 'Payload sent successfully.');\n      if (backButtonEl) backButtonEl.disabled = false;\n      setTimeout(returnToGoldengamesMenu, 2600);",
    1
)
text = text.replace(
    "    } else {\n      uiLog('[ERROR] Autoload failed: ' + (data.why || 'unknown error'), 'error');",
    "    } else {\n      if (statusValueEl) statusValueEl.textContent = 'FAILED';\n      if (selectedPayload === 'etahen-2.5B.bin') setJailbreakState(false);\n      showGoldengamesNotification('PAYLOAD FAILED', selectedLabel + ': ' + (data.why || 'unknown error'));\n      uiLog('[ERROR] ' + selectedLabel + ' autoload failed: ' + (data.why || 'unknown error'), 'error');",
    1
)

start_tail = "  window.addEventListener('load', start);\n})();"
menu_tail = r'''  function choosePayload(payload, label, forceFullJailbreak) {
    if (chainStarted) return;
    selectedPayload = payload;
    selectedLabel = label;
    selectedManual = hasJailbreakState() && !forceFullJailbreak;
    if (dashboardEl) dashboardEl.hidden = true;
    if (statusValueEl) statusValueEl.textContent = selectedManual ? 'MANUAL SEND' : 'RUNNING';
    if (runTitleEl) runTitleEl.textContent = label;
    var fw = detectFirmware();
    if (runSubtitleEl) runSubtitleEl.textContent = fw ? ('Firmware ' + fw.str + (selectedManual ? ' · Sender-only' : '')) : 'Firmware unknown';

    try {
      sessionStorage.removeItem('wkal_autoload');
      sessionStorage.removeItem('on_load_autorun');
      if (selectedManual) sessionStorage.setItem('goldengames_sender_only', '1');
      else sessionStorage.removeItem('goldengames_sender_only');
    } catch (e) { }

    runSelectedPayload();
  }

  function initGoldengamesMenu() {
    var fw = detectFirmware();
    var picked = pickExploit();
    var jailbroken = hasJailbreakState();
    if (firmwareValueEl) firmwareValueEl.textContent = fw ? fw.str : 'Unknown';
    if (exploitValueEl) exploitValueEl.textContent = picked === 'umtx2' ? 'UMTX2' : picked === 'slopkit' ? 'SlopKit' : 'Unsupported';
    if (statusValueEl) statusValueEl.textContent = picked ? (jailbroken ? 'JAILBROKEN' : 'AUTO START') : 'UNSUPPORTED';

    if (backButtonEl) backButtonEl.addEventListener('click', function () {
      if (!backButtonEl.disabled) returnToGoldengamesMenu();
    });

    var autoBtn = document.getElementById('autoJailbreak');
    if (autoBtn) autoBtn.addEventListener('click', function () {
      setJailbreakState(false);
      choosePayload('etahen-2.5B.bin', 'AUTO JAILBREAK · etaHEN 2.5B', true);
    });

    var tiles = document.querySelectorAll('[data-payload]');
    for (var i = 0; i < tiles.length; i++) {
      tiles[i].addEventListener('click', function () {
        var key = this.getAttribute('data-payload');
        if (key === 'etahen') choosePayload('etahen-2.5B.bin', 'etaHEN 2.5B', false);
        else if (key === 'kstuff') choosePayload('kstuff-1.10.elf', 'Kstuff Lite 1.10', false);
        else choosePayload('payload.elf', 'Payload Manager', false);
      });
    }

    setTimeout(function () {
      splashEl.classList.add('hide');
      setTimeout(function () {
        splashEl.hidden = true;
        if (dashboardEl) dashboardEl.hidden = false;

        /* Fresh document = fresh Auto Jailbreak. liveJailbreakState can only
           become true after etaHEN succeeds in this same page instance. */
        if (picked && !chainStarted && !hasJailbreakState()) {
          if (statusValueEl) statusValueEl.textContent = 'LOADING etaHEN';
          setTimeout(function () {
            choosePayload('etahen-2.5B.bin', 'AUTO JAILBREAK · etaHEN 2.5B', true);
          }, 650);
        }
      }, 350);
    }, 700);
  }

  window.addEventListener('load', initGoldengamesMenu);
})();'''
if start_tail not in text:
    raise SystemExit('upstream load hook not found')
text = text.replace(start_tail, menu_tail, 1)

app.write_text(text, encoding='utf-8')
print('Patched upstream app.js: fresh-launch auto jailbreak + live-page manual sender mode enabled.')
