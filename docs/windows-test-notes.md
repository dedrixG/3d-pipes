# Windows smoke test notes

Shipped in **0.2.0**. How this Linux machine publishes that tag: [publishing.md](publishing.md).

Machine: Windows 10/11, Python 3.13, PySide6 6.11.2, one display
`\\.\DISPLAY1` 1920×1080 physical, 125% DPI (Qt geometry 1536×864). OpenGL 3.3 core.

Ran from `OneDrive\Projects\pipes-screensaver` against source (not a frozen `.exe`).

## What worked

- Unit tests (`tests/test_argv.py`, `tests/test_cover_screens.py`)
- `--dump-screens`
- Windowed OpenGL (`tests/smoke_gl.py`): pipes render, framebuffer 1200×675 at 125% DPI
- `--settings`: preview + panel, controls load defaults
- Config path: `%LOCALAPPDATA%\dedrixG\3d-pipes\config.json`
- Fullscreen GL framebuffer is 1920×1080 when the window is covering

## Retest after fixes

- `/c 12345` parses as settings (no argparse error)
- `--window` keeps the settings panel hidden
- Fullscreen desktop grab now shows pipes covering the whole display including over the taskbar (`docs/windows-fullscreen-desktop-after.png`)
- `/p` embed into a host HWND returned True and sized to the parent client (500×375 at 125% DPI). Host `grab()` is empty gray — expected, the child is a native Win32 child, not a Qt child.

## Bugs found (fixed)

1. **`/c <HWND>` crash** — Display Settings passes `/c 12345` as two tokens. The HWND was left for argparse → `unrecognized arguments: 12345`, so Configure did nothing. Same class of bug for `/a <HWND>` and `/s <HWND>`.
2. **Fullscreen was invisible** — Wayland's `createWinId()`-before-`show()` path produced a Qt fullscreen window whose FBO rendered (grabFramebuffer had pipes) but the native window never covered the desktop. Desktop grab showed other apps + the taskbar. Stay-on-top had been disabled on Win32.
3. **`/p` preview** — `SetParent` without 64-bit `argtypes`, no `WS_CHILD`, no resize to the parent client rect, no quit when the preview HWND died.
4. **`--window` always opened the settings panel** (same as `--settings`).
5. **`faulthandler.enable()`** throws `RuntimeError: sys.stderr is None` in a windowed frozen process.

## Still true / not a crash

- Requested MSAA 4, driver reported `samples=0` (same class of issue already noted on some Linux setups). “Smooth edges” still saved in config.
- Single monitor only — hotplug / two-head cover plan was not exercised on hardware.
- Frozen `3DPipes.exe` / `.scr` not built on this pass (PyInstaller). Source path is what was tested.
- Unsigned SmartScreen warning still expected for a hobby `.exe`.

## How to re-run

```bat
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe tests\smoke_gl.py docs\windows-gl-smoke.png
.venv\Scripts\python.exe pipes.py --dump-screens
.venv\Scripts\python.exe pipes.py --settings
.venv\Scripts\python.exe pipes.py /c 12345
```
