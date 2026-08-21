# Goldengames PS5 Autoloader build plan

This repository tracks a Goldengames fork of `itsPLK/ps5-webkit-autoloader` v0.3.0.

Pinned upstream dependencies:

- UMTX2: `a080beb74d9e4bc34f3563798b716bd86b2d6ee0`
- SlopKit: `6153152be0b6a69e7e7931ff1b68523b7fde1429`
- Unified Autoloader: `78a6f0274f1581e233b69dd7dd4fd3b948a6d15c`
- PS5 elfldr: `148b71c2fb9155d2550ef6a14eb03433e23acaeb`

Goldengames payload targets:

- etaHEN 2.5B — SHA-256 `4845cac45095361b8983b14d6690622183b0dcfbf6d7fda16e161aa91ff0531e`
- Kstuff Lite 1.10 — SHA-256 `b1dfe57f367a35374f605127915eda38c76a6ed5d1c729e427955798bd78c66a`

The intended installed Title ID is `GGAU00001`, separate from upstream `WKAL00001`.

Development is staged on `agent/import-v0.5` before merging to `main`.
