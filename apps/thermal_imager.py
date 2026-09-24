"""Infrared Thermal Imager (com.dyt.wcc.neutral): app for a USB thermal camera."""

import time

from device import latest_photo, launch, pull_new_photo, tap

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
    before = latest_photo(d, PHOTO_DIR)
    tap(d, id=TAKE_PHOTO)
    if pull:
        return pull_new_photo(d, before, outdir, PHOTO_DIR)


def run(d, outdir, count=1, interval=0.0, pull=True):
    """Open the app, then take `count` photos `interval` seconds apart."""
    launch(d, PACKAGE)
    for i in range(count):
        if i:
            time.sleep(interval)
        saved = take_photo(d, outdir, pull)
        if not pull:
            print(f"[{i + 1}/{count}] Tapped.")
        elif saved:
            print(f"[{i + 1}/{count}] Saved {saved}")
        else:
            print(f"[{i + 1}/{count}] Tapped, but no new file appeared in {PHOTO_DIR}.")
