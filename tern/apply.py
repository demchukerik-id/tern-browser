"""Apply Tern's branding to a Chromium source tree.

Each edit names the exact text it expects, so a Chromium release that moved the
code fails here, loudly, instead of producing a half-branded browser.

Usage: python -I apply.py <chromium src dir>
"""
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAME = 'Tern'

BRANDING = f"""COMPANY_FULLNAME={NAME}
COMPANY_SHORTNAME={NAME}
PRODUCT_FULLNAME={NAME}
PRODUCT_SHORTNAME={NAME}
PRODUCT_INSTALLER_FULLNAME={NAME} Installer
PRODUCT_INSTALLER_SHORTNAME={NAME} Installer
COPYRIGHT=Copyright @LASTCHANGE_YEAR@ The {NAME} Authors and The Chromium Authors. All rights reserved.
MAC_BUNDLE_ID=dev.tern.Tern
MAC_CREATOR_CODE=Tern
MAC_TEAM_ID=
"""

# (file, expected text, replacement). Own identity on Windows, so Tern never
# shares registry keys, file associations or the default profile folder with
# an installed Chromium.
EDITS = [
    ('chrome/install_static/chromium_install_modes.h', [
        ('kProductPathName[] = L"Chromium"', f'kProductPathName[] = L"{NAME}"'),
        ('.base_app_name = L"Chromium"', f'.base_app_name = L"{NAME}"'),
        ('.base_app_id = L"Chromium"', f'.base_app_id = L"{NAME}"'),
        ('.browser_prog_id_prefix = L"ChromiumHTM"', '.browser_prog_id_prefix = L"TernHTM"'),
        ('L"Chromium HTML Document"', f'L"{NAME} HTML Document"'),
        ('.direct_launch_url_scheme = "chromium"', '.direct_launch_url_scheme = "tern"'),
        ('.pdf_prog_id_prefix = L"ChromiumPDF"', '.pdf_prog_id_prefix = L"TernPDF"'),
        ('L"Chromium PDF Document"', f'L"{NAME} PDF Document"'),
        # Active Setup GUID {7D2B3E1D-...} -> Tern's own.
        ('L"{7D2B3E1D-D096-4594-9D8F-A6667F12E0AC}"', 'L"{4E8B6A52-3C1F-4D7A-9B25-6F0E2D9C7A31}"'),
        # Toast activator CLSID {635EFA6F-08D6-4EC9-BD14-8A0FDE975159} -> Tern's own.
        ('.toast_activator_clsid = {0x635EFA6F,\n                                  0x08D6,\n                                  0x4EC9,\n'
         '                                  {0xBD, 0x14, 0x8A, 0x0F, 0xDE, 0x97, 0x51,\n                                   0x59}}',
         '.toast_activator_clsid = {0x2B7C9E14,\n                                  0x6A3D,\n                                  0x4F58,\n'
         '                                  {0x8E, 0x21, 0x5C, 0x9A, 0x07, 0xB3, 0xD4,\n                                   0x6F}}'),
    ]),
    # Top bar: the editor's navy (#1b202a) as the default theme colour (V1).
    # Only the default changes, so a user can still pick another colour.
    ('chrome/browser/themes/theme_service.cc', [
        ('registry->RegisterIntegerPref(prefs::kUserColor, SK_ColorTRANSPARENT);',
         'registry->RegisterIntegerPref(prefs::kUserColor,\n'
         '                               SkColorSetRGB(0x1b, 0x20, 0x2a));  // Tern'),
    ]),
    # No "Google API keys are missing" bar at every start: Tern ships without
    # Google keys on purpose (web sign-in to Google sites does not need them).
    ('chrome/browser/ui/startup/infobar_utils.cc', [
        ('if (!google_apis::HasAPIKeyConfigured()) {',
         'if (!google_apis::HasAPIKeyConfigured() &&\n'
         '      base::CommandLine::ForCurrentProcess()->HasSwitch(\n'
         '          "tern-show-api-keys-infobar")) {'),
    ]),
]

# Generated icons (make_icons.py) -> paths in the Chromium tree.
ICONS = {
    'product_logo_16.png': ['chrome/app/theme/chromium/product_logo_16.png',
                            'chrome/app/theme/default_100_percent/chromium/product_logo_16.png'],
    'product_logo_24.png': ['chrome/app/theme/chromium/product_logo_24.png'],
    'product_logo_32.png': ['chrome/app/theme/default_100_percent/chromium/product_logo_32.png',
                            'chrome/app/theme/default_200_percent/chromium/product_logo_16.png'],
    'product_logo_48.png': ['chrome/app/theme/chromium/product_logo_48.png'],
    'product_logo_64.png': ['chrome/app/theme/chromium/product_logo_64.png',
                            'chrome/app/theme/default_200_percent/chromium/product_logo_32.png'],
    'product_logo_128.png': ['chrome/app/theme/chromium/product_logo_128.png'],
    'product_logo_256.png': ['chrome/app/theme/chromium/product_logo_256.png'],
    'tern.ico': ['chrome/app/theme/chromium/win/chromium.ico',
                 'chrome/app/theme/chromium/win/app_list.ico'],
}


def edit(src, rel, pairs):
    f = src / rel
    text = f.read_text(encoding='utf-8')
    for old, new in pairs:
        if new in text and old not in text:
            continue  # already applied (a resumed build runs this again)
        if text.count(old) != 1:
            sys.exit(f'apply: expected text not found once in {rel}: {old[:60]!r}')
        text = text.replace(old, new)
    f.write_text(text, encoding='utf-8')


def main(src):
    src = Path(src)
    marker = src / '.tern_applied'
    if marker.exists():
        print('apply: already applied')
        return
    (src / 'chrome/app/theme/chromium/BRANDING').write_text(BRANDING, encoding='utf-8')
    for rel, pairs in EDITS:
        edit(src, rel, pairs)
    icons = HERE / 'icons'
    for name, targets in ICONS.items():
        for rel in targets:
            if not (src / rel).exists():
                sys.exit(f'apply: icon target missing: {rel}')
            shutil.copyfile(icons / name, src / rel)
    subprocess.run([sys.executable, '-I', str(HERE / 'brand_strings.py'), str(src), NAME], check=True)
    marker.write_text(NAME)
    print('apply: Tern branding applied')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
