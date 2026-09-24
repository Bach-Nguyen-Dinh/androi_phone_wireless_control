# thermal-testing

Take pictures on an Android phone from a computer over Wi-Fi. `phone_cam.py` opens a camera app on the phone (for example, a thermal camera app), taps its shutter button, and copies the new photo back to the computer.

## Requirements

- **Computer:** Linux, macOS or Windows, with [uv](https://docs.astral.sh/uv/getting-started/installation/) installed. You don't need to install `adb`, because the `adbutils` package brings its own copy.
- **Phone:** Android 11 or later, on the same Wi-Fi network as the computer.

## Install

```bash
git clone <repo-url> thermal_testing
cd thermal_testing
uv sync
```

`uv sync` creates `.venv/` with the exact versions pinned in `uv.lock`. If you don't have uv, you can use plain pip instead:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

If you install with pip, run the commands below with `.venv/bin/python phone_cam.py ...` instead of `uv run python phone_cam.py ...`.

## Set up the phone (once)

1. Open **Settings → About phone** and tap **Build number** 7 times. This turns on **Developer options**.
2. Go to **Settings → Developer options → Wireless debugging** and turn it on.
3. Tap **Pair device with pairing code**. The phone shows an IP address with a port and a 6-digit code. Pair the computer with them:

   ```bash
   uv run python phone_cam.py pair 192.168.1.50:37123 123456
   ```

You only need to pair once per computer.

## Connect

The main **Wireless debugging** screen shows an IP address and port. This port is different from the pairing port. Connect with:

```bash
uv run python phone_cam.py connect 192.168.1.50:41234
uv run python phone_cam.py devices      # check the phone is listed
```

The port can change when the phone restarts or Wi-Fi reconnects. If that happens, run `connect` again with the new port.

The first time a command controls the phone, `uiautomator2` installs a small helper app on it. Accept the prompt if one appears.

## Take a picture

### 1. Find the app's package name

```bash
uv run python phone_cam.py apps camera
```

### 2. Find the shutter button

Open the app on the phone, then run:

```bash
uv run python phone_cam.py dump
```

This saves `ui_dump.xml`, which describes the screen's layout, and `ui_dump.png`, a screenshot. In `ui_dump.xml`, find the shutter button and note one of these values:

- `text="..."`
- `content-desc="..."`
- `resource-id="..."`

### 3. Shoot

```bash
uv run python phone_cam.py shoot com.example.cam --desc "Shutter"
```

Use whichever selector matches what you found:

| Option | Matches | Example |
|---|---|---|
| `--text` | the button's visible text | `--text "Capture"` |
| `--desc` | its `content-desc` | `--desc "Take photo"` |
| `--id` | its `resource-id` | `--id "com.example.cam:id/shutter"` |
| `--xy` | a screen position in pixels | `--xy 540,2000` |

`shoot` wakes the screen, starts the app, taps the button, and copies the newest photo from `/sdcard/DCIM` into `./photos/`.

Other options:

- `--wait 2`: seconds to wait for the app to load before tapping. Increase it for slow apps.
- `--outdir photos`: the folder to save photos in.
- `--no-pull`: take the picture but don't copy it to the computer.

If more than one device is connected, put `--serial <ip:port>` before the command:

```bash
uv run python phone_cam.py --serial 192.168.1.50:41234 shoot com.example.cam --xy 540,2000
```

## Troubleshooting

- **"No device connected".** Run `connect` again. Check that Wireless debugging is still on and that you're using the current port.
- **"Control not found on screen".** The selector doesn't match anything. Run `dump` while the app is open and check the value. Some apps draw their own interface (common with thermal camera apps), so the button isn't in the dump at all. In that case, use `--xy`: read the coordinates from `ui_dump.png`, or turn on **Developer options → Pointer location** and tap the button.
- **"No new file under /sdcard/DCIM".** The app saves photos somewhere else. Use `--no-pull` and copy the photos yourself.
- **Nothing happens on the phone.** Unlock the phone, or turn off the lock screen while testing.

## Updating dependencies

```bash
uv add <package>
uv export --no-hashes --format requirements-txt -o requirements.txt
```

Commit `pyproject.toml`, `uv.lock` and `requirements.txt` together.
