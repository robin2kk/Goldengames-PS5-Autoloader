#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: rc7_session_fix.py <upstream-root>')

app = Path(sys.argv[1]).resolve() / 'frontend' / 'autoloader' / 'app.js'
s = app.read_text(encoding='utf-8')

old = '''      var savedEpoch = parseInt(data.processEpoch, 10);\n      var age = Date.now() - stamp;\n      var nowEpoch = currentProcessEpoch();\n      if (!stamp || age < 0 || age > JAILBREAK_LEASE_MS || !savedEpoch || !nowEpoch || Math.abs(nowEpoch - savedEpoch) > PROCESS_EPOCH_TOLERANCE_MS) {\n        localStorage.removeItem(JAILBREAK_LEASE_KEY);\n        return false;\n      }\n      return true;'''
new = '''      var age = Date.now() - stamp;\n      /* RC7 safety rule: a successful etaHEN marker survives WebProcess/app\n         recreation. WebProcess epoch is NOT console uptime and caused RC5/RC6\n         to rerun the kernel exploit when Goldengames was reopened. The actual\n         sender path still probes elfldr:9021 and falls back to the full chain\n         if the loader is unavailable. */\n      if (!stamp || age < 0 || age > JAILBREAK_LEASE_MS) {\n        localStorage.removeItem(JAILBREAK_LEASE_KEY);\n        return false;\n      }\n      return true;'''
if old not in s:
    raise SystemExit('RC7 lease hook not found')
s = s.replace(old, new, 1)

# Do not claim that a cached marker alone proves kernel state. It means that
# automatic replay is suppressed; the native UMTX2 sender verifies 9021 before send.
s = s.replace("statusValueEl.textContent = hasJailbreakState() ? 'JAILBROKEN' : 'READY';",
              "statusValueEl.textContent = hasJailbreakState() ? 'SESSION READY' : 'READY';")
s = s.replace("(jailbroken ? 'JAILBROKEN' : 'AUTO START')",
              "(jailbroken ? 'SESSION READY' : 'AUTO START')")
s = s.replace("showGoldengamesNotification('JAILBREAK ACTIVE', 'Existing live session detected · Auto Jailbreak skipped');",
              "showGoldengamesNotification('SESSION READY', 'Auto Jailbreak skipped · payload sender will verify elfldr 9021');")

app.write_text(s, encoding='utf-8')
print('RC7 session safety applied: reopen suppresses Auto Jailbreak; sender verifies elfldr 9021.')
