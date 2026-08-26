#!/usr/bin/env python3
"""Install PS5 homescreen key art in both app and metadata locations."""

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
    'INCASSET(pic0_png, "assets/pic0.png");\n'
    'INCASSET(pic0_dds, "assets/pic0.dds");',
)
replace_once(
    "  char icon_path[256];",
    "  char icon_path[256];\n"
    "  char app_pic0_png_path[256];\n"
    "  char app_pic0_dds_path[256];\n"
    "  char appmeta_dir[256];\n"
    "  char appmeta_pic0_png_path[256];\n"
    "  char appmeta_pic0_dds_path[256];",
)
replace_once(
    '  snprintf(icon_path, sizeof(icon_path), "/user/app/%s/sce_sys/icon0.png",\n'
    "           title_id);",
    '  snprintf(icon_path, sizeof(icon_path), "/user/app/%s/sce_sys/icon0.png",\n'
    "           title_id);\n"
    '  snprintf(app_pic0_png_path, sizeof(app_pic0_png_path),\n'
    '           "/user/app/%s/sce_sys/pic0.png", title_id);\n'
    '  snprintf(app_pic0_dds_path, sizeof(app_pic0_dds_path),\n'
    '           "/user/app/%s/sce_sys/pic0.dds", title_id);\n'
    '  snprintf(appmeta_dir, sizeof(appmeta_dir), "/user/appmeta/%s", title_id);\n'
    '  snprintf(appmeta_pic0_png_path, sizeof(appmeta_pic0_png_path),\n'
    '           "/user/appmeta/%s/pic0.png", title_id);\n'
    '  snprintf(appmeta_pic0_dds_path, sizeof(appmeta_pic0_dds_path),\n'
    '           "/user/appmeta/%s/pic0.dds", title_id);',
)
replace_once(
    "    if (needs_update(icon_path, icon0_png, icon0_png_size))\n"
    "      update_needed = 1;",
    "    if (needs_update(icon_path, icon0_png, icon0_png_size))\n"
    "      update_needed = 1;\n"
    "    if (needs_update(app_pic0_png_path, pic0_png, pic0_png_size))\n"
    "      update_needed = 1;\n"
    "    if (needs_update(app_pic0_dds_path, pic0_dds, pic0_dds_size))\n"
    "      update_needed = 1;\n"
    "    if (needs_update(appmeta_pic0_png_path, pic0_png, pic0_png_size))\n"
    "      update_needed = 1;\n"
    "    if (needs_update(appmeta_pic0_dds_path, pic0_dds, pic0_dds_size))\n"
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
    "  if (install_file(app_pic0_png_path, pic0_png, pic0_png_size) ||\n"
    "      install_file(app_pic0_dds_path, pic0_dds, pic0_dds_size)) {\n"
    '    wkali_log("[WKALI] Failed to install app homescreen background\\n");\n'
    "    sceAppInstUtilTerminate();\n"
    "    return -1;\n"
    "  }",
)

replace_once(
    '  wkali_log("[WKALI] Launcher app installed successfully.\\n");',
    "  /* App registration can recreate appmeta, so install its key art last. */\n"
    "  if (mkdir_p(appmeta_dir, 0755) != 0 ||\n"
    "      install_file(appmeta_pic0_png_path, pic0_png, pic0_png_size) ||\n"
    "      install_file(appmeta_pic0_dds_path, pic0_dds, pic0_dds_size)) {\n"
    '    wkali_log("[WKALI] Failed to install app metadata background\\n");\n'
    "    sceAppInstUtilTerminate();\n"
    "    return -1;\n"
    "  }\n\n"
    '  wkali_log("[WKALI] Launcher app installed successfully.\\n");',
)

path.write_text(text)
print("Applied PS5 appmeta homescreen background patch")
