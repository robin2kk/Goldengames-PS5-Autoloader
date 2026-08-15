#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, sys

ROOT = Path(__file__).resolve().parents[1]
PINS = json.loads((ROOT / 'dependency-pins.json').read_text())
FILES = ('etahen-2.5B.bin', 'kstuff-1.10.elf')

ok = True
for name in FILES:
    path = ROOT / 'payloads' / name
    expected = PINS[name + '.sha256']
    if not path.is_file():
        print(f'[MISSING] {path.relative_to(ROOT)}')
        ok = False
        continue
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if not data.startswith(b'\x7fELF'):
        print(f'[FAIL] {name}: not an ELF payload')
        ok = False
    elif actual != expected:
        print(f'[FAIL] {name}: sha256 {actual} != {expected}')
        ok = False
    else:
        print(f'[OK] {name}: {len(data):,} bytes sha256={actual}')

sys.exit(0 if ok else 1)
