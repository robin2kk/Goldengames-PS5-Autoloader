#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: apply_goldengames_build.py <upstream-root>')

root = Path(sys.argv[1]).resolve()
param = root / 'assets' / 'param.json.template'
registry = root / 'tools' / 'gen_file_registry.py'
wkali_h = root / 'include' / 'wkali.h'
installer_c = root / 'src' / 'app_installer.c'
umtx_apply = root / 'tools' / 'apply_umtx2_patch.sh'

param.write_text('''{
    "titleId": "GGAU00001",
    "applicationCategoryType": 65536,
    "deeplinkUri": "http://127.0.0.1:18181/app/index.html",
    "localizedParameters": {
        "defaultLanguage": "en-US",
        "en-US": {
            "titleName": "Goldengames PS5 Autoloader v[[VERSION_PLACEHOLDER]]"
        }
    }
}\n''', encoding='utf-8')

wkali_text = wkali_h.read_text(encoding='utf-8')
old_title = '#define WKAL_TITLE_ID "WKAL00001"'
new_title = '#define WKAL_TITLE_ID "GGAU00001"'
if old_title not in wkali_text and new_title not in wkali_text:
    raise SystemExit('WKAL_TITLE_ID definition not found; upstream changed')
wkali_h.write_text(wkali_text.replace(old_title, new_title, 1), encoding='utf-8')

installer_text = installer_c.read_text(encoding='utf-8')
installer_text = installer_text.replace('Updating WebKit Autoloader App...', 'Updating Goldengames PS5 Autoloader...')
installer_text = installer_text.replace('Installing WebKit Autoloader App...', 'Installing Goldengames PS5 Autoloader...')
installer_text = installer_text.replace('WebKit Autoloader App Ready!', 'Goldengames PS5 Autoloader Ready!')
installer_c.write_text(installer_text, encoding='utf-8')

text = registry.read_text(encoding='utf-8')
old = '''    lines.append(slopkit_iframe_url(app_dir))\n    lines.append(umtx2_iframe_url(app_dir))\n'''
new = '''    # Goldengames supports choosing the autoload payload from the dashboard.\n    for payload_name in ("payload.elf", "etahen-2.5B.bin", "kstuff-1.10.elf"):\n        lines.append(slopkit_iframe_url(app_dir).replace("autoload=payload.elf", "autoload=" + payload_name))\n        lines.append(umtx2_iframe_url(app_dir).replace("autoload=payload.elf", "autoload=" + payload_name))\n'''
if old not in text:
    raise SystemExit('expected registry hook not found; upstream changed')
registry.write_text(text.replace(old, new, 1), encoding='utf-8')

# Keep upstream patches/umtx2-autoload.patch intact. The PS5 diagnostic run
# showed the loader actually listening on 127.0.0.1:9021 immediately before
# etaHEN autoload. Route to that observed loader and instrument fetch/send.
apply_text = umtx_apply.read_text(encoding='utf-8')
marker = '# 4. Sanity check: the patched main.js must carry our integration markers, the\n'
if marker not in apply_text:
    raise SystemExit('UMTX2 post-patch insertion point not found; upstream changed')
post_patch = r'''# Goldengames diagnostic etaHEN autoload routing.
python3 - "$DEST/main.js" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')
old = ''' + "'''" + r'''    var wkalAutoloadName = new URLSearchParams(location.search).get("autoload") || sessionStorage.getItem("wkal_autoload");
    if (wkalAutoloadName && is_elfldr_running) {
        await log("autoload: waiting 4 s for elfldr to bind 9021...", LogLevel.LOG);
        setTimeout(function () {
            window.dispatchEvent(new CustomEvent(MAINLOOP_EXECUTE_PAYLOAD_REQUEST, {
                detail: {
                    displayTitle: "Autoload",
                    fileName: wkalAutoloadName,
                    wkalBase: "../payloads/",
                    toPort: 9021,
                    wkalAutoload: true
                }
            }));
        }, 4000);
    } else if (wkalAutoloadName && !is_elfldr_running) {
        await log("autoload failed: elfldr did not load", LogLevel.ERROR);
        try { window.parent.postMessage({ type: "wkal", kind: "autoload", ok: false, why: "elfldr did not load" }, "*"); } catch (e) { }
    }
''' + "'''" + r'''
new = ''' + "'''" + r'''    var wkalAutoloadName = new URLSearchParams(location.search).get("autoload") || sessionStorage.getItem("wkal_autoload");
    var wkalAutoloadPort = 9021;
    var wkalAutoloadReady = await probe_sb_elfldr();

    await log("Goldengames diag: elfldr probe 9021 = " + wkalAutoloadReady, LogLevel.INFO);
    if (wkalAutoloadName && wkalAutoloadReady) {
        await log("Goldengames diag: routing " + wkalAutoloadName + " to elfldr port 9021", LogLevel.INFO);
        try { window.parent.postMessage({ type: "goldengames-diag", stage: "elfldr-ready", payload: wkalAutoloadName, port: 9021 }, "*"); } catch (e) { }
        setTimeout(function () {
            try { window.parent.postMessage({ type: "goldengames-diag", stage: "autoload-dispatch", payload: wkalAutoloadName, port: 9021 }, "*"); } catch (e) { }
            window.dispatchEvent(new CustomEvent(MAINLOOP_EXECUTE_PAYLOAD_REQUEST, {
                detail: {
                    displayTitle: "etaHEN 2.5B",
                    fileName: wkalAutoloadName,
                    wkalBase: "../payloads/",
                    toPort: 9021,
                    wkalAutoload: true
                }
            }));
        }, 1500);
    } else if (wkalAutoloadName) {
        await log("Goldengames diag: elfldr 9021 not ready; etaHEN not sent", LogLevel.ERROR);
        try { window.parent.postMessage({ type: "wkal", kind: "autoload", ok: false, why: "elfldr 9021 not ready" }, "*"); } catch (e) { }
    }
''' + "'''" + r'''
if old not in s:
    raise SystemExit('Goldengames UMTX2 autoload block not found after upstream patch')
s = s.replace(old, new, 1)

fetch_old = ''' + "'''" + r'''        const response = await fetch(base + filename);
        if (!response.ok) {
            throw new Error(`Failed to fetch the binary file. Status: ${response.status}`);
        }
        const data = await response.arrayBuffer();
''' + "'''" + r'''
fetch_new = ''' + "'''" + r'''        const response = await fetch(base + filename);
        await log("Goldengames diag: fetch " + base + filename + " -> HTTP " + response.status, LogLevel.INFO);
        if (!response.ok) {
            throw new Error(`Failed to fetch the binary file. Status: ${response.status}`);
        }
        const data = await response.arrayBuffer();
        await log("Goldengames diag: payload bytes loaded = " + data.byteLength, LogLevel.INFO);
        try { window.parent.postMessage({ type: "goldengames-diag", stage: "payload-fetched", file: filename, bytes: data.byteLength }, "*"); } catch (e) { }
''' + "'''" + r'''
if fetch_old not in s:
    raise SystemExit('Goldengames payload fetch diagnostic hook not found')
s = s.replace(fetch_old, fetch_new, 1)

send_old = '                        await send_buffer_to_port(elf_store, total_sz, payload_info.toPort);\n'
send_new = ''' + "'''" + r'''                        await log("Goldengames diag: sending " + total_sz + " bytes to port " + payload_info.toPort, LogLevel.INFO);
                        try { window.parent.postMessage({ type: "goldengames-diag", stage: "send-start", bytes: total_sz, port: payload_info.toPort }, "*"); } catch (e) { }
                        await send_buffer_to_port(elf_store, total_sz, payload_info.toPort);
                        await log("Goldengames diag: send completed to port " + payload_info.toPort, LogLevel.INFO);
                        try { window.parent.postMessage({ type: "goldengames-diag", stage: "send-complete", bytes: total_sz, port: payload_info.toPort }, "*"); } catch (e) { }
''' + "'''" + r'''
if send_old not in s:
    raise SystemExit('Goldengames payload send diagnostic hook not found')
s = s.replace(send_old, send_new, 1)

p.write_text(s, encoding='utf-8')
print('umtx2: Goldengames etaHEN 9021 diagnostics applied.')
PY

'''
if 'Goldengames etaHEN 9021 diagnostics applied' not in apply_text:
    apply_text = apply_text.replace(marker, post_patch + marker, 1)
umtx_apply.write_text(apply_text, encoding='utf-8')

print('Goldengames build patches applied:')
print('  native WKAL_TITLE_ID: GGAU00001')
print('  param.json titleId: GGAU00001')
print('  titleName: Goldengames PS5 Autoloader')
print('  AppCache autoload variants: payload.elf, etaHEN 2.5B, Kstuff 1.10')
print('  UMTX2 etaHEN diagnostic route: verified elfldr on port 9021')
