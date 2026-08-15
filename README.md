# Goldengames PS5 Autoloader

Goldengames PS5 Autoloader — Auto Jailbreak, etaHEN, Kstuff & Payload Launcher.

Based on PS5 WebKit Autoloader by itsPLK. This fork preserves upstream credits and GPL-3.0 licensing.

> [!WARNING]
> **Do not use the older Goldengames v0.5 test installer.** It used inconsistent application identity values during development. The current test line is **v0.5.1 Test** and uses `GGAU00001` consistently in both the native installer and PS5 app metadata.

## Current status

**v0.5.1 Test** is a development build. It is not a public/stable release yet.

- Base: PS5 WebKit Autoloader v0.3.0
- UMTX2: firmware 1.00–5.50
- SlopKit: firmware 9.00–12.00
- Embedded payload choices: etaHEN 2.5B, Kstuff Lite 1.10, Payload Manager
- Goldengames application Title ID: `GGAU00001`

## Installing the test build on an already-jailbroken PS5

The `.elf` file is **not a PKG and is not installed by opening it directly**. It is an installer payload.

1. Jailbreak the PS5 using your normal working method.
2. Make sure `elfldr` or Payload Manager is already running.
3. Send or launch `goldengames-ps5-autoloader-installer_v0.5.1-test.elf` through elfldr / Payload Manager.
4. The installer should cache the local WebKit frontend and create the **Goldengames PS5 Autoloader** homescreen app.
5. Reboot the console once.
6. Launch Goldengames PS5 Autoloader from the PS5 homescreen.

If the installer does not show an installation notification or does not create the homescreen app, stop and collect the payload/installer log before retrying.

## First functional test order

For test builds, verify features separately before using Auto Jailbreak:

1. Open the Goldengames dashboard.
2. Test Payload Manager.
3. Test etaHEN 2.5B.
4. Test Kstuff Lite 1.10.
5. Test **AUTO JAILBREAK** last.

## Credits

Goldengames PS5 Autoloader is based on the work of itsPLK and the upstream projects it integrates, including UMTX2, SlopKit, PS5 Payload SDK, elfldr, Unified Autoloader / Payload Manager, etaHEN, and Kstuff Lite. Upstream project credits and licensing are preserved.

## License

GPL-3.0
