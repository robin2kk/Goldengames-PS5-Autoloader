# Integrated payloads

The Goldengames build expects these exact files:

- `etahen-2.5B.bin` — SHA-256 `4845cac45095361b8983b14d6690622183b0dcfbf6d7fda16e161aa91ff0531e`
- `kstuff-1.10.elf` — SHA-256 `b1dfe57f367a35374f605127915eda38c76a6ed5d1c729e427955798bd78c66a`

Do not silently substitute another build/version. The build workflow must verify these hashes before embedding either payload.
