# Goldengames PS5 Auto Jailbreak v1.1.0

Goldengames PS5 Auto Jailbreak v1.1.0 is the first stable release of the Goldengames launcher.

## What is new

- Added a two-stage Auto Jailbreak flow that prevents the WebKit out-of-memory warning observed when etaHEN was started during the exploit's peak memory usage.
- Added automatic etaHEN 2.6B loading after Payload Manager initializes.
- Added persistent same-session state: reopening Goldengames after a successful jailbreak now opens the payload dashboard directly.
- Added ShadowMount Plus to the built-in payload menu.
- Added a custom Goldengames launcher icon and 3840 x 2160 PS5 homescreen background.
- Added PNG and DDS artwork installation in both the app and `/user/appmeta` metadata paths.
- Added pinned payload verification during official builds.

## Supported PS5 firmware

- 1.00–5.50 through UMTX2
- 7.00–12.00 through Poops / SlopKit
- 12.02–12.70 through P2JB

Firmware 5.51–6.xx and firmware newer than 12.70 are not supported by this release.

## Installation

The installer ELF requires a PS5 that is already jailbroken with a working ELF loader.

1. Jailbreak the PS5 using your existing method.
2. Start elfldr or Payload Manager.
3. Send `goldengames-ps5-auto-jailbreak-installer_v1.1.0.elf` to the console.
4. Wait for the installation notification.
5. Open **Goldengames PS5 Auto Jailbreak** from the PS5 homescreen.
6. Restart the console once if the updated icon or background remains cached.

The ELF is an installer payload, not a PKG. It cannot be installed by copying it to USB and opening it directly.

## SHA-256

`ed22ab6f093cb39911261883f9ec21151682ace03ad41bcccd9c16be19b6bad2`
