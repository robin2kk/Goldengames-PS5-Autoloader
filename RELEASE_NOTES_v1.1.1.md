# Goldengames PS5 Jailbreak v1.1.1

Version 1.1.1 updates the interface, execution controls, payload library, and SlopKit launch URLs based on feedback from v1.1.0 users.

## What is new

- Rebuilt the dashboard in English with Payloads on the left, Jailbreak controls in the center, and live Console Status on the right.
- Made Manual Mode the default. The user starts the jailbreak and decides which payload to launch afterward.
- Added an optional Auto Mode switch. Auto Mode launches the user-selected payload after the jailbreak stage completes.
- Kept the dashboard open while operations run. The hidden exploit frame no longer replaces the main page.
- Added animated action buttons and an animated PlayStation-color activity bar.
- Added detailed English states for firmware detection, exploit progress, selected payload, operating mode, and failures.

## Compatibility fixes

- Fixed the SlopKit `Production request refused: noncanonical-production-request` error caused by a noncanonical route-version value.
- Synchronized the online runtime URL and every offline AppCache payload URL with SlopKit's required `v=final` production route.
- Retained explicit Poops routing for firmware 7.61 and 10.20.
- Retained explicit P2JB routing for firmware 12.70, including PS5 Pro user-agent detection through the standard PS5 firmware string.
- Preserved the memory-safe two-stage payload flow and the 6.5-second cooldown before launching the selected Auto Mode payload.

## New and updated payloads

- OnionHEN 0.0.11
- PIZZA-HEN v0.1
- ShadowMountPlus 1.7 alpha 11

All bundled payloads are SHA-256 verified during the official build.

## Supported firmware

| Exploit route | Supported firmware |
| --- | --- |
| UMTX2 | 1.00–5.50 |
| Poops / SlopKit | 7.00–12.00 |
| P2JB | 12.02–12.70 |

Firmware 5.51–6.xx and firmware newer than 12.70 are not supported. A listed route means the matching exploit and offsets are included; success rates can still vary by console, firmware, and session state.

## Installation

The installer ELF requires a PS5 that is already jailbroken with a working ELF loader.

1. Jailbreak the PS5 using a method that already works on its firmware.
2. Start elfldr or Payload Manager.
3. Send `goldengames-ps5-jailbreak-installer_v1.1.1.elf` to the console.
4. Wait for the installation-complete notification.
5. Open **Goldengames PS5 Jailbreak** from the PS5 homescreen.
6. Restart the console once if the updated icon or 4K background remains cached.

The installer is an ELF payload, not a PKG, and cannot be installed by opening it directly from USB.

## Testing status

Version 1.1.1 has been successfully tested on real PS5 hardware running firmware 5.10, including the jailbreak flow, etaHEN 2.5B and 2.6B selection, individual payload launching, persistent dashboard behavior, and the animated segmented progress bar.

The listed exploit routes and offsets for other supported firmware ranges are included, but firmware 7.61, 10.20, and PS5 Pro 12.70 have not yet been confirmed on real hardware for this release. Success rates can vary by console, firmware, and session state.
