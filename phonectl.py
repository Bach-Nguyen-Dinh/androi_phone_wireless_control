"""Control an Android phone over Wi-Fi: open apps, tap their controls, and run per-app routines.

Usage (run with `uv run python phonectl.py <command> ...`):
  pair     <ip:pair_port> <code>   one-time pairing (Android 11+ Wireless debugging)
  connect  <ip:port>               connect to the phone
  devices                          list connected devices
  apps     [filter]                list installed package names
  dump     [out.xml]               save current screen's UI tree + screenshot, to find selectors
  routines                         list apps that have a built-in routine
  run      <app> [--count N] [--interval S]   run an app's routine; photos go to photos/<app>/
  shoot    <package> [selector options]      open any app, tap the control, pull the newest photo

Selector options for `shoot` (use one):
  --text "Shutter"  --desc "Take photo"  --id "com.app:id/shutter"  --xy 540,2000
"""

import argparse
from pathlib import Path

import adbutils

from apps import APPS
from device import adb, get_device, latest_photo, launch, pull_new_photo, tap


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


def cmd_routines(a):
    for name, app in APPS.items():
        print(f"{name:16} {app.TITLE} ({app.PACKAGE})")


def cmd_run(a):
    app = APPS[a.app]
    d = get_device(a.serial)
    app.run(d, Path(a.outdir) / app.NAME, count=a.count, interval=a.interval, pull=not a.no_pull)


def cmd_shoot(a):
    d = get_device(a.serial)
    before = latest_photo(d)
    launch(d, a.package, a.wait)
    tap(d, text=a.text, desc=a.desc, id=a.id, xy=a.xy)
    print("Tapped.")

    if a.no_pull:
        return
    saved = pull_new_photo(d, before, Path(a.outdir) / a.package)
    if saved:
        print(f"Saved {saved}")
    else:
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
    s = sub.add_parser("routines"); s.set_defaults(f=cmd_routines)

    s = sub.add_parser("run")
    s.add_argument("app", choices=APPS)
    s.add_argument("--count", type=int, default=1, help="number of photos to take")
    s.add_argument("--interval", type=float, default=0.0, help="seconds between photos")
    s.add_argument("--outdir", default="photos", help="photos are saved in <outdir>/<app>/")
    s.add_argument("--no-pull", action="store_true", help="don't copy photos to this machine")
    s.set_defaults(f=cmd_run)

    s = sub.add_parser("shoot")
    s.add_argument("package")
    g = s.add_mutually_exclusive_group()
    g.add_argument("--text"); g.add_argument("--desc"); g.add_argument("--id"); g.add_argument("--xy")
    s.add_argument("--wait", type=float, default=2.0, help="seconds to let the app load")
    s.add_argument("--outdir", default="photos", help="photos are saved in <outdir>/<package>/")
    s.add_argument("--no-pull", action="store_true", help="don't copy the photo to this machine")
    s.set_defaults(f=cmd_shoot)

    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
