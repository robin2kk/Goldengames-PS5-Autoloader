#!/usr/bin/env python3
"""Add PS5 homescreen key-art files to the upstream launcher installer."""

from pathlib import Path


path = Path("src/app_installer.c")
text = path.read_text()


def replace_once(old: str, new: str) -> None:
    global text
    if text.count(old) != 1:
        raise SystemExit(f"background patch anchor count != 1: {old!r}")
    text = text.replace(old, new, 1)


replace_once(
    'INCASSET(icon0_png, "assets/icon0.png");',
    'INCASSET(icon0_png, "assets/icon0.png");\n'
    'INCASSET(pic0_png, "assets/pic0.png");',
)
replace_once(
    "  char icon_path[256];",
    "  char icon_path[256];\n"
    "  char pic0_path[256];\n"
    "  char pic1_path[256];",
)
replace_once(
    '  snprintf(icon_path, sizeof(icon_path), "/user/app/%s/sce_sys/icon0.png",\n'
    "           title_id);",
    '  snprintf(icon_path, sizeof(icon_path), "/user/app/%s/sce_sys/icon0.png",\n'
    "           title_id);\n"
    '  snprintf(pic0_path, sizeof(pic0_path), "/user/app/%s/sce_sys/pic0.png",\n'
    "           title_id);\n"
    '  snprintf(pic1_path, sizeof(pic1_path), "/user/app/%s/sce_sys/pic1.png",\n'
    "           title_id);",
)
replace_once(
    "    if (needs_update(icon_path, icon0_png, icon0_png_size))\n"
    "      update_needed = 1;",
    "    if (needs_update(icon_path, icon0_png, icon0_png_size))\n"
    "      update_needed = 1;\n"
    "    if (needs_update(pic0_path, pic0_png, pic0_png_size))\n"
    "      update_needed = 1;\n"
    "    if (needs_update(pic1_path, pic0_png, pic0_png_size))\n"
    "      update_needed = 1;",
)
replace_once(
    "  if (install_file(icon_path, icon0_png, icon0_png_size)) {\n"
    '    wkali_log("[WKALI] Failed to install icon0.png\\n");\n'
    "    sceAppInstUtilTerminate();\n"
    "    return -1;\n"
    "  }",
    "  if (install_file(icon_path, icon0_png, icon0_png_size)) {\n"
    '    wkali_log("[WKALI] Failed to install icon0.png\\n");\n'
    "    sceAppInstUtilTerminate();\n"
    "    return -1;\n"
    "  }\n"
    "  if (install_file(pic0_path, pic0_png, pic0_png_size) ||\n"
    "      install_file(pic1_path, pic0_png, pic0_png_size)) {\n"
    '    wkali_log("[WKALI] Failed to install homescreen background\\n");\n'
    "    sceAppInstUtilTerminate();\n"
    "    return -1;\n"
    "  }",
)

path.write_text(text)
print("Applied homescreen background installer patch")
