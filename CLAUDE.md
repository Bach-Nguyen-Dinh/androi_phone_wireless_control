# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A single-script tool, `phone_cam.py`, that drives an Android phone over Wi-Fi ADB: it opens a camera app (e.g. a thermal camera app), taps its shutter control via uiautomator2, and pulls the newest photo from `/sdcard/DCIM` back to this machine.

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
uv run python phone_cam.py pair <ip:pair_port> <code>   # one-time, Android 11+ Wireless debugging
uv run python phone_cam.py connect <ip:port>
uv run python phone_cam.py devices
uv run python phone_cam.py apps [filter]                 # find the app's package name
uv run python phone_cam.py dump [out.xml]                # UI tree + screenshot, to find selectors
uv run python phone_cam.py shoot <package> --text|--desc|--id|--xy <value> [--wait 2] [--outdir photos] [--no-pull]
```

`--serial` (a global option, placed before the subcommand) is required when more than one device is connected. Running any command needs a real phone connected over ADB.

## How it works

- Subcommands are argparse subparsers that each `set_defaults(f=cmd_<name>)`; `main()` calls `a.f(a)`. Add a new command by writing `cmd_<name>(a)` and registering a subparser the same way.
- `pair` shells out to the adb binary bundled with `adbutils` (`adbutils.adb_path()`); `connect`/`devices` use `adbutils` directly; everything else goes through a `uiautomator2` device from `get_device()`.
- `shoot` detects the new photo by comparing the newest file under `/sdcard/DCIM/*/*` (via `ls -t`) before and after the tap, polling for ~10 s. Apps that save elsewhere need `--no-pull`.
- Generated output (`photos/`, `ui_dump.*`) is gitignored.
