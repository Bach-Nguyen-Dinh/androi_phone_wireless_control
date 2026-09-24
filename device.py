"""Phone helpers shared by the CLI and the app routines."""

import subprocess
import sys
import time
from pathlib import Path

import adbutils
import uiautomator2 as u2

ADB = adbutils.adb_path()


def adb(*args):
    return subprocess.run([ADB, *args], text=True, capture_output=True)


def get_device(serial=None):
    devices = adbutils.adb.device_list()
    if not devices:
        sys.exit("No device connected. Run `connect <ip:port>` first.")
    if serial is None and len(devices) > 1:
        sys.exit("Multiple devices connected; pass --serial. " + ", ".join(d.serial for d in devices))
    return u2.connect(serial or devices[0].serial)


def launch(d, package, wait=2.0):
    d.screen_on()
    d.app_start(package, wait=True)
    time.sleep(wait)


def tap(d, text=None, desc=None, id=None, xy=None, timeout=10):
    if xy:
        x, y = (int(v) for v in xy.split(",")) if isinstance(xy, str) else xy
        d.click(x, y)
        return
    if text:
        el = d(text=text)
    elif desc:
        el = d(description=desc)
    elif id:
        el = d(resourceId=id)
    else:
        sys.exit("Give one of --text, --desc, --id or --xy")
    if not el.wait(timeout=timeout):
        sys.exit("Control not found on screen. Run `dump` to inspect the UI.")
    el.click()


def latest_photo(d, photo_dir="/sdcard/DCIM/*"):
    out = d.shell(f"ls -t {photo_dir}/* 2>/dev/null | head -1").output.strip()
    return out or None


def pull_new_photo(d, before, outdir, photo_dir="/sdcard/DCIM/*", timeout=10):
    """Wait for a file newer than `before` to appear in `photo_dir` and copy it to `outdir`."""
    for _ in range(int(timeout / 0.5)):
        time.sleep(0.5)
        newest = latest_photo(d, photo_dir)
        if newest and newest != before:
            time.sleep(1)  # let the app finish writing it
            dest = Path(outdir) / Path(newest).name
            dest.parent.mkdir(parents=True, exist_ok=True)
            d.pull(newest, str(dest))
            return dest
    return None
