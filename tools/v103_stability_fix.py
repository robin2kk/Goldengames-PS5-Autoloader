#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v103_stability_fix.py <upstream-root>')

root = Path(sys.argv[1]).resolve()
app = root / 'frontend' / 'autoloader' / 'app.js'
param = root / 'assets' / 'param.json.template'

s = app.read_text(encoding='utf-8')

# One automatic recovery attempt for a fresh etaHEN Auto Jailbreak failure.
anchor = "  var startupSessionProbeTimer = null;\n"
insert = anchor + "  var autoJailbreakRetryCount = 0;\n"
if anchor not in s:
    raise SystemExit('v1.0.3 retry variable anchor not found')
s = s.replace(anchor, insert, 1)

# Reset the retry counter after a successful Auto Jailbreak.
success_anchor = """      if (selectedPayload === 'etahen-2.5B.bin') {\n        setJailbreakState(true);"""
success_new = """      if (selectedPayload === 'etahen-2.5B.bin') {\n        autoJailbreakRetryCount = 0;\n        setJailbreakState(true);"""
if success_anchor not in s:
    raise SystemExit('v1.0.3 success anchor not found')
s = s.replace(success_anchor, success_new, 1)

# If the first fresh Auto Jailbreak reports a failure, cleanly re-arm exactly
# once after a short cooldown. Manual payload failures are never auto-retried.
fail_anchor = """    } else {\n      if (statusValueEl) statusValueEl.textContent = 'FAILED';\n      if (selectedPayload === 'etahen-2.5B.bin') setJailbreakState(false);\n      showGoldengamesNotification('PAYLOAD FAILED', selectedLabel + ': ' + (data.why || 'unknown error'));\n      uiLog('[ERROR] ' + selectedLabel + ' autoload failed: ' + (data.why || 'unknown error'), 'error');"""
fail_new = """    } else {\n      if (statusValueEl) statusValueEl.textContent = 'FAILED';\n      if (selectedPayload === 'etahen-2.5B.bin') setJailbreakState(false);\n\n      if (selectedPayload === 'etahen-2.5B.bin' && !selectedManual && autoJailbreakRetryCount < 1) {\n        autoJailbreakRetryCount += 1;\n        uiLog('[AUTO] First jailbreak attempt failed. Retrying once after cooldown...', 'warning');\n        showGoldengamesNotification('AUTO RETRY', 'First attempt failed · retrying etaHEN 2.5B automatically');\n        if (statusValueEl) statusValueEl.textContent = 'RETRYING';\n        setTimeout(function () {\n          try { exploitEl.src = 'about:blank'; } catch (e) { }\n          try {\n            sessionStorage.removeItem('goldengames_sender_only');\n            sessionStorage.removeItem('goldengames_probe_only');\n            sessionStorage.removeItem('wkal_autoload');\n            sessionStorage.removeItem('on_load_autorun');\n          } catch (e) { }\n          clearSlopkitState();\n          finished = false;\n          chainStarted = false;\n          selectedManual = false;\n          choosePayload('etahen-2.5B.bin', 'AUTO JAILBREAK · etaHEN 2.5B', true);\n        }, 4500);\n        return;\n      }\n\n      showGoldengamesNotification('PAYLOAD FAILED', selectedLabel + ': ' + (data.why || 'unknown error'));\n      uiLog('[ERROR] ' + selectedLabel + ' autoload failed: ' + (data.why || 'unknown error'), 'error');"""
if fail_anchor not in s:
    raise SystemExit('v1.0.3 failure anchor not found')
s = s.replace(fail_anchor, fail_new, 1)

# Give the PS5 browser a little more time to settle before the first automatic
# exploit start. This does not change manual button behavior.
startup_anchor = """          setTimeout(function () {\n            choosePayload('etahen-2.5B.bin', 'AUTO JAILBREAK · etaHEN 2.5B', true);\n          }, 650);"""
startup_new = """          setTimeout(function () {\n            choosePayload('etahen-2.5B.bin', 'AUTO JAILBREAK · etaHEN 2.5B', true);\n          }, 1200);"""
if startup_anchor not in s:
    raise SystemExit('v1.0.3 initial auto-start delay anchor not found')
s = s.replace(startup_anchor, startup_new, 1)

# The stale-session fallback also gets a slightly longer settle delay.
s = s.replace("""    setTimeout(function () {\n      if (!chainStarted) choosePayload('etahen-2.5B.bin', 'AUTO JAILBREAK · etaHEN 2.5B', true);\n    }, 350);""",
              """    setTimeout(function () {\n      if (!chainStarted) choosePayload('etahen-2.5B.bin', 'AUTO JAILBREAK · etaHEN 2.5B', true);\n    }, 900);""", 1)

app.write_text(s, encoding='utf-8')

# Keep the PS5 home-screen/app title short. The build's internal VERSION can
# remain versioned for cache paths, but it is no longer appended to titleName.
p = param.read_text(encoding='utf-8')
old_title = '"titleName": "Goldengames PS5 Autoloader v[[VERSION_PLACEHOLDER]]"'
new_title = '"titleName": "Goldengames PS5 Autoloader"'
if old_title not in p and new_title not in p:
    raise SystemExit('v1.0.3 titleName anchor not found')
p = p.replace(old_title, new_title, 1)
param.write_text(p, encoding='utf-8')

print('Goldengames v1.0.3 stability fix applied:')
print('  first fresh etaHEN Auto Jailbreak failure retries once after 4.5 s')
print('  first automatic start delayed to 1.2 s for browser settling')
print('  stale-session fallback delayed to 0.9 s')
print('  PS5 app title shortened to: Goldengames PS5 Autoloader')
