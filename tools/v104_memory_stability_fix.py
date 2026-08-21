#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v104_memory_stability_fix.py <upstream-root>')

root = Path(sys.argv[1]).resolve()
app = root / 'frontend' / 'autoloader' / 'app.js'
umtx_apply = root / 'tools' / 'apply_umtx2_patch.sh'

s = app.read_text(encoding='utf-8')

# v1.0.4: make the single automatic retry less aggressive. Tear down the
# exploit iframe immediately and allow WebKit/GC state more time to settle.
s = s.replace("""        setTimeout(function () {\n          try { exploitEl.src = 'about:blank'; } catch (e) { }""",
              """        try { exploitEl.src = 'about:blank'; } catch (e) { }\n        setTimeout(function () {""", 1)
s = s.replace("""        }, 4500);""", """        }, 8000);""", 1)
s = s.replace("First attempt failed · retrying etaHEN 2.5B automatically",
              "First attempt failed · cooling down before one automatic retry", 1)

# Manual payloads in an already-jailbroken session must request sender-only.
# The UMTX2 runtime below will probe 9021 and return before any kernel path.
manual_anchor = """    selectedPayload = payload;\n    selectedLabel = label;\n    selectedManual = !isAuto;"""
manual_new = """    selectedPayload = payload;\n    selectedLabel = label;\n    selectedManual = !isAuto;\n    try {\n      if (selectedManual && liveJailbreakState) sessionStorage.setItem('goldengames_sender_only', '1');\n      else sessionStorage.removeItem('goldengames_sender_only');\n    } catch (e) { }"""
if manual_anchor not in s:
    raise SystemExit('v1.0.4 choosePayload anchor not found')
s = s.replace(manual_anchor, manual_new, 1)

app.write_text(s, encoding='utf-8')

# Tighten sender-only inside UMTX2: if 9021 is live, skip the kernel exploit
# immediately. Payload dispatch later in main.js still fetches and sends to 9021.
sh = umtx_apply.read_text(encoding='utf-8')
marker = '# 4. Sanity check: the patched main.js must carry our integration markers, the\n'
if marker not in sh:
    raise SystemExit('v1.0.4 UMTX insertion marker not found')
block = r'''# Goldengames v1.0.4 memory/stability sender path.
python3 - "$DEST/main.js" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')
old = ''' + "'''" + r'''    if (goldengamesSenderOnly && is_elfldr_running) {
        wkOnly = true;
        await log("Goldengames: jailbreak already active; sender-only mode enabled.", LogLevel.SUCCESS);
''' + "'''" + r'''
new = ''' + "'''" + r'''    if (goldengamesSenderOnly && is_elfldr_running) {
        wkOnly = true;
        await log("Goldengames v1.0.4: live elfldr 9021 detected; kernel exploit bypassed.", LogLevel.SUCCESS);
''' + "'''" + r'''
if old not in s:
    raise SystemExit('v1.0.4 sender-only hook not found')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
print('umtx2: Goldengames v1.0.4 direct sender/memory path applied.')
PY

'''
if 'Goldengames v1.0.4 direct sender/memory path applied' not in sh:
    sh = sh.replace(marker, block + marker, 1)
umtx_apply.write_text(sh, encoding='utf-8')

print('Goldengames v1.0.4 memory/stability fix applied:')
print('  one retry only, cooldown increased to 8 seconds')
print('  exploit iframe torn down before cooldown')
print('  manual payloads request sender-only when live jailbreak is known')
print('  live elfldr 9021 keeps kernel exploit bypassed for manual sends')
