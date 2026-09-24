# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A general tool for controlling an Android phone over Wi-Fi ADB: it opens apps, taps their controls via uiautomator2, and runs per-app routines. More apps will be added over time, so keep app-specific code in `apps/` and the rest app-agnostic. The first routine, `thermal_imager`, drives a USB thermal camera app: it takes photos and pulls them from the phone into `photos/thermal_imager/`.

## Layout

```
phonectl.py            CLI entry point (argparse subcommands)
device.py              app-agnostic phone helpers
apps/__init__.py       APPS registry of app profiles
apps/thermal_imager.py Infrared Thermal Imager profile + routines
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
uv run python phonectl.py routines                      # list apps and their routines
uv run python phonectl.py run thermal_imager [photo] [--count N] [--interval 10s]
uv run python phonectl.py run thermal_imager timed --interval 10s --duration 5m
uv run python phonectl.py run thermal_imager continuous --interval 30s   # stops on Ctrl+D (stdin EOF)
# common run options: [--outdir photos] [--no-pull]; times accept 90, 30s, 5m, 1h30m
uv run python phonectl.py shoot <package> --text|--desc|--id|--xy <value> [--wait 2] [--outdir photos] [--no-pull]
```

`--serial` (a global option, placed before the subcommand) is required when more than one device is connected. Running any command needs a real phone connected over ADB.

## How it works

- `phonectl.py` is the CLI only (plus the `seconds` argparse type for time values). Shared phone helpers (`get_device`, `launch`, `tap`, `latest_photo`, `pull_new_photo`, `adb`) live in `device.py`.
- `device.tap` raises `ControlNotFound` (and `ValueError` for no selector) instead of exiting, so routines can skip a missed shot; `main()` turns these into a clean exit.
- `device.repeat(action, interval, duration=None, stop=None)` is the shared scheduler: it calls `action(i)` on fixed slots from the start time (no drift), skips slots an overrunning action missed, stops at `duration` (exclusive), when the `stop` Event is set, or on Ctrl+C. `device.stop_on_eof()` returns an Event set by a daemon thread when stdin hits EOF (Ctrl+D).
- `apps/` holds one module per app. Each defines `NAME` (also the photo subfolder), `TITLE`, `PACKAGE`, `PHOTO_DIR`, the control resource IDs, and `ROUTINES`, a dict of name -> `fn(d, outdir, count=, interval=, duration=, pull=, **_)` whose first entry is the default and whose docstring first line is shown by `routines`. `apps/__init__.py` registers modules in `APPS`, which drives `run`'s choices and `routines`. Routines validate their own required options.
- `apps/thermal_imager.py` covers the Infrared Thermal Imager app (`com.dyt.wcc.neutral`), which saves to `/sdcard/DCIM/DYTCamera`. Its UI elements report `clickable="false"` but still respond to taps by resource ID. Routines: `photo` (default), `timed`, `continuous`. `take_photo` wakes the screen and, if the shutter isn't found within 3 s, relaunches the app and retries once (cheaper than checking `app_current()`, which costs ~1.5 s). A shot takes ~4 s including the pull, so intervals under ~5 s skip slots.
- Subcommands are argparse subparsers that each `set_defaults(f=cmd_<name>)`; `main()` calls `a.f(a)`. Add a new command by writing `cmd_<name>(a)` and registering a subparser the same way.
- `pair` shells out to the adb binary bundled with `adbutils` (`adbutils.adb_path()`); `connect`/`devices` use `adbutils` directly; everything else goes through a `uiautomator2` device from `get_device()`.
- `shoot` (generic, saves to `photos/<package>/`) and the routines detect the new photo by comparing the newest file in the photo folder (via `ls -t`; `/sdcard/DCIM/*` unless the app sets `PHOTO_DIR`) before and after the tap, polling for ~10 s. Apps that save elsewhere need `--no-pull`.
- To add an app: copy `apps/thermal_imager.py` to `apps/<name>.py`, set its constants from a `dump` of the app's screen, adjust `ROUTINES`, and add the module to `APPS`. Reuse `device.py` helpers rather than calling uiautomator2 directly for common actions.
- Generated output (`photos/`, `ui_dump.*`) is gitignored.
