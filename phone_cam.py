"""Control an Android phone over Wi-Fi: open an app and tap its shutter button.

Usage (run with `uv run python phone_cam.py <command> ...`):
  pair    <ip:pair_port> <code>   one-time pairing (Android 11+ Wireless debugging)
  connect <ip:port>               connect to the phone
  devices                         list connected devices
  apps    [filter]                list installed package names
  dump    [out.xml]               save current screen's UI tree + screenshot, to find selectors
  shoot   <package> [selector options]   open app, tap the control, pull the newest photo

Selector options for `shoot` (use one):
  --text "Shutter"  --desc "Take photo"  --id "com.app:id/shutter"  --xy 540,2000
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

import adbutils
import uiautomator2 as u2

ADB = adbutils.adb_path()


def adb(*args):
    return subprocess.run([ADB, *args], text=True, capture_output=True)


def get_device(serial):
    devices = adbutils.adb.device_list()
    if not devices:
        sys.exit("No device connected. Run `connect <ip:port>` first.")
    if serial is None and len(devices) > 1:
        sys.exit("Multiple devices connected; pass --serial. " + ", ".join(d.serial for d in devices))
    return u2.connect(serial or devices[0].serial)


def cmd_pair(a):
    r = adb("pair", a.addr, a.code)
    print(r.stdout or r.stderr)


def cmd_connect(a):
    print(adbutils.adb.connect(a.addr, timeout=10))


def cmd_devices(a):
    for d in adbutils.adb.device_list():
        print(d.serial, d.prop.model)


def cmd_apps(a):
    d = get_device(a.serial)
    for pkg in sorted(d.app_list()):
        if not a.filter or a.filter.lower() in pkg.lower():
            print(pkg)


def cmd_dump(a):
    d = get_device(a.serial)
    out = Path(a.out)
    out.write_text(d.dump_hierarchy(), encoding="utf-8")
    d.screenshot(str(out.with_suffix(".png")))
    print(f"Saved {out} and {out.with_suffix('.png')}")
    print("Look for text=, content-desc= or resource-id= on the button you want to tap.")


def latest_photo(d):
    out = d.shell("ls -t /sdcard/DCIM/*/* 2>/dev/null | head -1").output.strip()
    return out or None


def cmd_shoot(a):
    d = get_device(a.serial)
    before = latest_photo(d)

    d.screen_on()
    d.app_start(a.package, wait=True)
    time.sleep(a.wait)

    if a.xy:
        x, y = (int(v) for v in a.xy.split(","))
        d.click(x, y)
    else:
        if a.text:
            el = d(text=a.text)
        elif a.desc:
            el = d(description=a.desc)
        elif a.id:
            el = d(resourceId=a.id)
        else:
            sys.exit("Give one of --text, --desc, --id or --xy")
        if not el.wait(timeout=10):
            sys.exit("Control not found on screen. Run `dump` to inspect the UI.")
        el.click()
    print("Tapped.")

    if a.no_pull:
        return
    for _ in range(20):  # wait up to ~10 s for the new file to appear
        time.sleep(0.5)
        newest = latest_photo(d)
        if newest and newest != before:
            time.sleep(1)  # let the app finish writing it
            dest = Path(a.outdir) / Path(newest).name
            dest.parent.mkdir(parents=True, exist_ok=True)
            d.pull(newest, str(dest))
            print(f"Saved {dest}")
            return
    print("No new file under /sdcard/DCIM; the app may save elsewhere (use --no-pull).")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--serial", help="device serial / ip:port when several are connected")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("pair"); s.add_argument("addr"); s.add_argument("code"); s.set_defaults(f=cmd_pair)
    s = sub.add_parser("connect"); s.add_argument("addr"); s.set_defaults(f=cmd_connect)
    s = sub.add_parser("devices"); s.set_defaults(f=cmd_devices)
    s = sub.add_parser("apps"); s.add_argument("filter", nargs="?"); s.set_defaults(f=cmd_apps)
    s = sub.add_parser("dump"); s.add_argument("out", nargs="?", default="ui_dump.xml"); s.set_defaults(f=cmd_dump)

    s = sub.add_parser("shoot")
    s.add_argument("package")
    g = s.add_mutually_exclusive_group()
    g.add_argument("--text"); g.add_argument("--desc"); g.add_argument("--id"); g.add_argument("--xy")
    s.add_argument("--wait", type=float, default=2.0, help="seconds to let the app load")
    s.add_argument("--outdir", default="photos")
    s.add_argument("--no-pull", action="store_true", help="don't copy the photo to this machine")
    s.set_defaults(f=cmd_shoot)

    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
