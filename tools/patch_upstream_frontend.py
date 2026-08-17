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
insert = needle + "  var dashboardEl = document.getElementById('dashboard');\n  var firmwareValueEl = document.getElementById('firmwareValue');\n  var exploitValueEl = document.getElementById('exploitValue');\n  var statusValueEl = document.getElementById('statusValue');\n  var runTitleEl = document.getElementById('runTitle');\n  var runSubtitleEl = document.getElementById('runSubtitle');\n  var selectedPayload = 'payload.elf';\n  var selectedLabel = 'Payload Manager';\n"
if needle not in text:
    raise SystemExit('upstream exploit element hook not found')
text = text.replace(needle, insert, 1)

# Make the two upstream URLs select the chosen payload dynamically while
# otherwise preserving their exact query strings.
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

# Rename upstream start() so Goldengames can choose the payload first.
text = text.replace('  function start() {\n', '  function runSelectedPayload() {\n', 1)
text = text.replace("    uiLog('WebKit Autoloader by PLK', 'success');", "    uiLog('Goldengames PS5 Autoloader', 'success');\n    uiLog('Selected payload: ' + selectedPayload, 'success');", 1)
text = text.replace("    EXPLOIT_URL = picked === 'umtx2' ? UMTX2_URL : SLOPKIT_URL;", "    EXPLOIT_URL = picked === 'umtx2' ? getUmtx2Url() : getSlopkitUrl();", 1)
text = text.replace("        sessionStorage.setItem('wkal_autoload', 'payload.elf');", "        sessionStorage.setItem('wkal_autoload', selectedPayload);", 1)

# Make the result visible in the Goldengames status box too.
text = text.replace(
    "    if (data.ok) {\n      uiLog('Payload loaded (' + data.bytes + ' bytes sent to elfldr).', 'success');",
    "    if (data.ok) {\n      if (statusValueEl) statusValueEl.textContent = 'LOADED';\n      uiLog(selectedLabel + ' loaded (' + data.bytes + ' bytes sent to elfldr).', 'success');",
    1
)
text = text.replace(
    "    } else {\n      uiLog('[ERROR] Autoload failed: ' + (data.why || 'unknown error'), 'error');",
    "    } else {\n      if (statusValueEl) statusValueEl.textContent = 'FAILED';\n      uiLog('[ERROR] ' + selectedLabel + ' autoload failed: ' + (data.why || 'unknown error'), 'error');",
    1
)

# Keep the dashboard available as a manual fallback, but auto-start etaHEN on
# every fresh app launch. This is patched into the real upstream app.js used by
# the installer build (overlay/frontend/app.js is only a reference copy).
start_tail = "  window.addEventListener('load', start);\n})();"
menu_tail = r'''  function choosePayload(payload, label) {
    if (chainStarted) return;
    selectedPayload = payload;
    selectedLabel = label;
    if (dashboardEl) dashboardEl.hidden = true;
    if (statusValueEl) statusValueEl.textContent = 'RUNNING';
    if (runTitleEl) runTitleEl.textContent = label;
    var fw = detectFirmware();
    if (runSubtitleEl) runSubtitleEl.textContent = fw ? ('Firmware ' + fw.str) : 'Firmware unknown';

    /* Remove stale autoload state before arming a new payload. runSelectedPayload
       will then write the exact selected payload for UMTX2. */
    try {
      sessionStorage.removeItem('wkal_autoload');
      sessionStorage.removeItem('on_load_autorun');
    } catch (e) { }

    runSelectedPayload();
  }

  function initGoldengamesMenu() {
    var fw = detectFirmware();
    var picked = pickExploit();
    if (firmwareValueEl) firmwareValueEl.textContent = fw ? fw.str : 'Unknown';
    if (exploitValueEl) exploitValueEl.textContent = picked === 'umtx2' ? 'UMTX2' : picked === 'slopkit' ? 'SlopKit' : 'Unsupported';
    if (statusValueEl) statusValueEl.textContent = picked ? 'AUTO START' : 'UNSUPPORTED';

    var autoBtn = document.getElementById('autoJailbreak');
    if (autoBtn) autoBtn.addEventListener('click', function () {
      choosePayload('etahen-2.5B.bin', 'AUTO JAILBREAK · etaHEN 2.5B');
    });

    var tiles = document.querySelectorAll('[data-payload]');
    for (var i = 0; i < tiles.length; i++) {
      tiles[i].addEventListener('click', function () {
        var key = this.getAttribute('data-payload');
        if (key === 'etahen') choosePayload('etahen-2.5B.bin', 'etaHEN 2.5B');
        else if (key === 'kstuff') choosePayload('kstuff-1.10.elf', 'Kstuff Lite 1.10');
        else choosePayload('payload.elf', 'Payload Manager');
      });
    }

    setTimeout(function () {
      splashEl.classList.add('hide');
      setTimeout(function () {
        splashEl.hidden = true;
        if (dashboardEl) dashboardEl.hidden = false;

        /* AUTO JAILBREAK means no button press: on supported firmware arm
           etaHEN immediately after the dashboard becomes visible. */
        if (picked && !chainStarted) {
          if (statusValueEl) statusValueEl.textContent = 'LOADING etaHEN';
          setTimeout(function () {
            choosePayload('etahen-2.5B.bin', 'AUTO JAILBREAK · etaHEN 2.5B');
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
print('Patched upstream app.js: Goldengames auto-starts etaHEN and preserves manual payload fallback.')
