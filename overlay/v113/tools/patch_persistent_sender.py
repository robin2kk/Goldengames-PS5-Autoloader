#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_persistent_sender.py <upstream-root>")

root = Path(sys.argv[1]).resolve()
target = root / "tools" / "apply_umtx2_patch.sh"
text = target.read_text(encoding="utf-8")
marker = "# 4. Sanity check: the patched main.js must carry our integration markers, the\n"
if marker not in text:
    raise SystemExit("UMTX2 sanity-check marker not found")

bridge = r'''# Goldengames v1.1.3: keep the patched UMTX2 main loop available as a
# direct payload sender after the first successful etaHEN launch.
python3 - "$DEST/main.js" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text(encoding="utf-8")
anchor = ''' + "'''" + r'''    window.addEventListener(MAINLOOP_EXECUTE_PAYLOAD_REQUEST, async function (event) {
        /** @type {PayloadInfo} */
        let payload_info = event.detail;
        let toast = showToast(`${payload_info.displayTitle}: Waiting in queue...`, -1);
        queue.push({ payload_info, toast });
    });
''' + "'''" + r'''
replacement = anchor + ''' + "'''" + r'''

    // The parent dashboard can queue another payload without running PSFree
    // or the kernel exploit again. It follows the normal WKAL 9021 path and
    // reports the result through the existing autoload message contract.
    window.addEventListener("message", function (event) {
        var data = event.data || {};
        if (data.type !== "goldengames-direct-send") return;
        var name = String(data.payload || "");
        if (!name) return;
        window.dispatchEvent(new CustomEvent(MAINLOOP_EXECUTE_PAYLOAD_REQUEST, {
            detail: {
                displayTitle: String(data.label || name),
                fileName: name,
                wkalBase: "../payloads/",
                toPort: 9021,
                wkalAutoload: true
            }
        }));
    });
''' + "'''" + r'''
if "goldengames-direct-send" not in s:
    if anchor not in s:
        raise SystemExit("UMTX2 queue listener not found")
    s = s.replace(anchor, replacement, 1)
p.write_text(s, encoding="utf-8")
print("umtx2: Goldengames persistent sender bridge applied")
PY

'''

if "Goldengames persistent sender bridge applied" not in text:
    text = text.replace(marker, bridge + marker, 1)
target.write_text(text, encoding="utf-8")
print("Goldengames v1.1.3 UMTX2 sender patch installed")
