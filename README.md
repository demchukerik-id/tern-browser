# Tern

Tern is a Chromium-based browser for Windows x64, built from Chromium's **stable** releases with its own name, icon and top-bar colour. It is the browser Agent Editor docks into its browser page.

Tern is not affiliated with Google. "Chrome" and "Chromium" are trademarks of Google LLC.

## What is changed from Chromium

All changes are in `tern/` and applied to an unmodified Chromium checkout by `tern/apply.py`:

| Change | Where |
| --- | --- |
| Product and company name, file properties | `chrome/app/theme/chromium/BRANDING` |
| Name in the UI, in every language (translations kept) | `tern/brand_strings.py` (ids recomputed with grit) |
| Own Windows identity: profile folder name, ProgIDs, URL scheme, Active Setup and toast GUIDs | `chrome/install_static/chromium_install_modes.h` |
| Default theme colour `#1b202a` (users can still change it) | `chrome/browser/themes/theme_service.cc` |
| No "Google API keys are missing" bar | `chrome/browser/ui/startup/infobar_utils.cc` |
| Icons (`tern/make_icons.py` draws them) | `chrome/app/theme/...` |

Build settings are in `tern/args.gn`: official optimised build, no proprietary codecs (no H.264/AAC), FFmpeg as a separate DLL, no Widevine, no Google API keys. Signing in to Google websites works without keys; Chrome Sync, Translate and Safe Browsing do not.

## How it is built

GitHub's free Windows runners allow 6 hours per job, and a Chromium build takes about 40 hours. `build.yml` therefore runs up to 12 stages in a chain. Each stage unpacks the previous stage's work tree, builds for about 4 h 50 m, then packs the tree (about 15 GB) as an artifact for the next stage. `tern/build.py` skips every step whose output already exists, so each stage carries on where the last one stopped.

- `check-stable.yml` runs once a day and starts `build.yml` when Chromium stable for Windows has a version without a Tern release.
- A finished build is published as a GitHub release `v<chromium version>` with `tern-<version>-win-x64.zip` and its SHA-256.
- Start a build by hand: Actions → build → Run workflow (optionally with a version).

The chained-stage design follows [ungoogled-chromium-windows](https://github.com/ungoogled-software/ungoogled-chromium-windows) (BSD-3-Clause).

## Install

Unzip a release anywhere and run `tern-win\chrome.exe`. The release is not code-signed yet, so Windows SmartScreen may warn on first start.

## Licences

Tern's own scripts: BSD-3-Clause (`LICENSE`). The browser is built from Chromium; its licence and the licences of all third-party code ship in the package as `LICENSE` and `credits.html` (also at `chrome://credits`).
