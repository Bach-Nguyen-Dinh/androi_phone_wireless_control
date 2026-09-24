# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A general tool for controlling an Android phone over Wi-Fi ADB: it opens apps, taps their controls via uiautomator2, and runs per-app routines. More apps will be added over time, so keep app-specific code in `apps/` and the rest app-agnostic. The first routine, `thermal_imager`, drives a USB thermal camera app: it takes photos and pulls them from the phone into `photos/thermal_imager/`.

## Layout

```
phonectl.py            CLI entry point (argparse subcommands)
device.py              app-agnostic phone helpers
apps/__init__.py       APPS registry of app profiles
apps/thermal_imager.py Infrared Thermal Imager profile + routine
photos/<app>/          pulled photos (gitignored)
```

## Environment

Use `uv` with the project `.venv`; do not install packages system-wide. Dependencies are declared in `pyproject.toml` and locked in `uv.lock`. `requirements.txt` is generated, so regenerate it after changing dependencies:

```bash
uv sync                                                        # create/update .venv
uv add <pkg>                                                   # add a dependency
uv export --no-hashes --format requirements-txt -o requirements.txt
```

There are no tests, linter, or build step.

## Running

```bash
uv run python phonectl.py pair <ip:pair_port> <code>   # one-time, Android 11+ Wireless debugging
uv run python phonectl.py connect <ip:port>
uv run python phonectl.py devices
uv run python phonectl.py apps [filter]                 # find the app's package name
uv run python phonectl.py dump [out.xml]                # UI tree + screenshot, to find selectors
uv run python phonectl.py routines                      # list apps with a built-in routine
uv run python phonectl.py run thermal_imager [--count N] [--interval S] [--outdir photos] [--no-pull]
uv run python phonectl.py shoot <package> --text|--desc|--id|--xy <value> [--wait 2] [--outdir photos] [--no-pull]
```

`--serial` (a global option, placed before the subcommand) is required when more than one device is connected. Running any command needs a real phone connected over ADB.

## How it works

- `phonectl.py` is the CLI only. Shared phone helpers (`get_device`, `launch`, `tap`, `latest_photo`, `pull_new_photo`, `adb`) live in `device.py`.
- `apps/` holds one module per app. Each defines `NAME` (also the photo subfolder), `TITLE`, `PACKAGE`, `PHOTO_DIR`, the control resource IDs, and `run(d, outdir, count, interval, pull)`. `apps/__init__.py` registers them in `APPS`, which drives `run`'s choices and `routines`.
- `apps/thermal_imager.py` covers the Infrared Thermal Imager app (`com.dyt.wcc.neutral`), which saves to `/sdcard/DCIM/DYTCamera`. Its UI elements report `clickable="false"` but still respond to taps by resource ID.
- Subcommands are argparse subparsers that each `set_defaults(f=cmd_<name>)`; `main()` calls `a.f(a)`. Add a new command by writing `cmd_<name>(a)` and registering a subparser the same way.
- `pair` shells out to the adb binary bundled with `adbutils` (`adbutils.adb_path()`); `connect`/`devices` use `adbutils` directly; everything else goes through a `uiautomator2` device from `get_device()`.
- `shoot` (generic, saves to `photos/<package>/`) and the routines detect the new photo by comparing the newest file in the photo folder (via `ls -t`; `/sdcard/DCIM/*` unless the app sets `PHOTO_DIR`) before and after the tap, polling for ~10 s. Apps that save elsewhere need `--no-pull`.
- To add an app: copy `apps/thermal_imager.py` to `apps/<name>.py`, set its constants from a `dump` of the app's screen, and add the module to `APPS`. Reuse `device.py` helpers rather than calling uiautomator2 directly for common actions.
- Generated output (`photos/`, `ui_dump.*`) is gitignored.
