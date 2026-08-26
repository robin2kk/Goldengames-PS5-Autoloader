# Goldengames PS5 Auto Jailbreak

Goldengames PS5 Auto Jailbreak is an installable PS5 homebrew launcher that provides an automatic jailbreak flow, etaHEN 2.6B loading, and a built-in payload dashboard.

It is based on PS5 WebKit Autoloader v0.4.0 by itsPLK. Upstream credits and GPL-3.0 licensing are preserved.

## Version 1.1.0

This is the first stable Goldengames PS5 Auto Jailbreak release.

### Highlights

- Automatic two-stage jailbreak flow designed to avoid the PS5 WebKit out-of-memory warning.
- Automatically loads etaHEN 2.6B after the initial exploit stage.
- Reopening the app during the same console session goes directly to the payload dashboard instead of running the jailbreak again.
- Built-in payload menu with etaHEN, Payload Manager, Kstuff, Kstuff Lite, ShadowMount Plus, CheatRunner, nanoDNS, Linux Loader, FTP Server, and Web Server.
- Goldengames dashboard, launcher icon, and 3840 x 2160 homescreen background.
- Background metadata is installed in both the application and PS5 app metadata locations.
- Pinned and verified payload files for reproducible builds.

## Supported firmware

The automatic exploit route is selected from the detected PS5 firmware:

| Exploit route | Supported firmware |
| --- | --- |
| UMTX2 | 1.00–5.50 |
| Poops / SlopKit | 7.00–12.00 |
| P2JB | 12.02–12.70 |

Firmware 5.51–6.xx is not supported by this build. Firmware newer than 12.70 is not supported.

Support means the application contains a matching exploit route. Actual success rates can vary by firmware and console state.

## Installation requirements

> [!IMPORTANT]
> The installer ELF must be launched on a PS5 that is already jailbroken. You must already have a working ELF loader, such as elfldr or Payload Manager. The installer is not a PKG and cannot be opened directly from USB.

## How to install

1. Jailbreak the PS5 using a method that already works on your firmware.
2. Start elfldr or Payload Manager on the console.
3. Send `goldengames-ps5-auto-jailbreak-installer_v1.1.0.elf` to the PS5 through your normal ELF-sending method.
4. Wait for the installation-complete notification.
5. Return to the PS5 homescreen and locate **Goldengames PS5 Auto Jailbreak**.
6. Restart the PS5 once if the new launcher icon or 4K background does not appear immediately.
7. Open the app and select **Auto Jailbreak**.

After a successful jailbreak, etaHEN 2.6B is loaded automatically. If etaHEN returns to the PS5 homescreen, reopen Goldengames to enter the payload dashboard directly.

After a full PS5 restart, select **Auto Jailbreak** again to begin a new session.

## Included improvements

- Memory-safe first-stage payload flow.
- Persistent same-session dashboard reopening.
- Automatic cleanup of the exploit iframe after completion.
- 6.5-second separation between Payload Manager and etaHEN initialization.
- Individual payload launching without repeating the kernel exploit.
- Native PS5 homescreen artwork installed as RGB PNG and DXT5 DDS.

## Credits

Goldengames PS5 Auto Jailbreak builds on work by itsPLK and the upstream projects it integrates, including UMTX2, SlopKit, P2JB, PS5 Payload SDK, elfldr, Unified Autoloader / Payload Manager, etaHEN, Kstuff, Kstuff Lite, ShadowMount Plus, CheatRunner, nanoDNS, PS5 Linux Loader, ftpsrv, and websrv.

All upstream credits and licenses remain applicable.

## License

GPL-3.0
