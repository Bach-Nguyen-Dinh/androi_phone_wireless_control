"""Infrared Thermal Imager (com.dyt.wcc.neutral): app for a USB thermal camera."""

import sys
import time
from datetime import datetime

from device import ControlNotFound, latest_photo, launch, pull_new_photo, repeat, stop_on_eof, tap

NAME = "thermal_imager"
TITLE = "Infrared Thermal Imager"
PACKAGE = "com.dyt.wcc.neutral"
PHOTO_DIR = "/sdcard/DCIM/DYTCamera"

# Control resource IDs, from `phonectl.py dump` on the preview screen.
TAKE_PHOTO = f"{PACKAGE}:id/iv_preview_left_takePhoto"
RECORD = f"{PACKAGE}:id/bt_preview_left_record"
GALLERY = f"{PACKAGE}:id/iv_preview_left_gallery"
SETTINGS = f"{PACKAGE}:id/iv_preview_right_setting"
PALETTE = f"{PACKAGE}:id/iv_preview_left_palette"
FLIP = f"{PACKAGE}:id/cb_function_flip"


def take_photo(d, outdir, pull=True):
    d.screen_on()
    before = latest_photo(d, PHOTO_DIR)
    try:
        tap(d, id=TAKE_PHOTO, timeout=3)
    except ControlNotFound:  # app was closed or backgrounded: reopen it and retry once
        launch(d, PACKAGE)
        tap(d, id=TAKE_PHOTO)
    if pull:
        return pull_new_photo(d, before, outdir, PHOTO_DIR)


def _shooter(d, outdir, pull, total=None):
    """Return an action(i) that takes one photo and prints a timestamped result line."""
    def action(i):
        label = f"#{i + 1}" + (f"/{total}" if total else "")
        try:
            saved = take_photo(d, outdir, pull)
        except ControlNotFound as e:
            result = f"skipped: {e}"
        else:
            if not pull:
                result = "tapped"
            elif saved:
                result = f"saved {saved}"
            else:
                result = f"tapped, but no new file appeared in {PHOTO_DIR}"
        print(f"[{datetime.now():%H:%M:%S}] {label} {result}", flush=True)
    return action


def photo(d, outdir, count=1, interval=None, pull=True, **_):
    """Take --count photos (default 1), --interval apart."""
    launch(d, PACKAGE)
    shoot = _shooter(d, outdir, pull, total=count)
    for i in range(count):
        if i and interval:
            time.sleep(interval)
        shoot(i)


def timed(d, outdir, interval=None, duration=None, pull=True, **_):
    """Take a photo every --interval for --duration."""
    if not interval or not duration:
        sys.exit("timed needs --interval and --duration, e.g. --interval 10s --duration 5m")
    launch(d, PACKAGE)
    print(f"Taking a photo every {interval:g}s for {duration:g}s. Press Ctrl+C to stop early.")
    n = repeat(_shooter(d, outdir, pull), interval, duration=duration)
    print(f"Done: {n} photo{'' if n == 1 else 's'}.")


def continuous(d, outdir, interval=None, pull=True, **_):
    """Take a photo every --interval until you press Ctrl+D."""
    if not interval:
        sys.exit("continuous needs --interval, e.g. --interval 10s")
    launch(d, PACKAGE)
    print(f"Taking a photo every {interval:g}s. Press Ctrl+D to stop.")
    n = repeat(_shooter(d, outdir, pull), interval, stop=stop_on_eof())
    print(f"Stopped: {n} photo{'' if n == 1 else 's'}.")


ROUTINES = {"photo": photo, "timed": timed, "continuous": continuous}
