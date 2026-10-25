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

## 0.4.0 laptop install — 2026-09-10

Same OneDrive tree, a second Win11 box (this one). **No source changes.**
This was the 0.4.0 build (sequential spawn, parked reset interval),
not GitHub `v0.3.0`. That build is now the published `v0.4.0` tag
(`74bb637`).

Machine: Windows 11 Pro Insider, build 26100, Python 3.13.14 (Store) venv,
PySide6 6.11.2, PyInstaller 6.22.2. One display `\\.\DISPLAY1` 1920×1080
**dpr=1** (100% DPI — previous smoke was 125%). OpenGL 3.3 core, `samples=0`.

### Source smoke

- 36 unit tests OK, including untracked `tests/test_config.py`
- `--version` → `3D Pipes 0.4.0`
- `--dump-screens` → one 1920×1080 landscape cover
- `tests/smoke_gl.py` → `SMOKE OK` 960×540, pipes visible
  (`docs/windows-gl-smoke.png`)

### Frozen smoke (this was the gap)

`scripts\build-windows.bat` equivalent against `.venv`:

```
dist\3DPipes.exe   (~60 MB onefile)
dist\3DPipes.scr   (copy of the exe)
```

- Frozen `--dump-screens` exit 0 in ~1.8s
- Frozen `--settings`: preview + panel, Sequential default, Reset interval
  hidden as parked (`docs/windows-settings-frozen.png`)
- Frozen `/s`: cover is visible over the whole desktop including the
  taskbar (`docs/windows-fullscreen-frozen.png`). Stay-on-top still good.
- No `faulthandler` crash in the windowed freeze. State log landed at
  `%LOCALAPPDATA%\State\dedrixG\3d-pipes\faulthandler.log` (Qt
  `AppStateLocation` on this Win11). Empty file, no traceback.

### Install on this laptop

Copied to `%LOCALAPPDATA%\Programs\3DPipes\` (not System32 — no admin).

```
HKCU\Control Panel\Desktop\SCRNSAVE.EXE =
  C:\Users\ridge\AppData\Local\Programs\3DPipes\3DPipes.scr
ScreenSaveActive=1
ScreenSaveTimeOut=300   (left alone; was Ribbons.scr)
```

Start Menu: **3D Pipes** and **3D Pipes Settings**.

The Screen Saver dropdown in desk.cpl only lists `System32\*.scr`. Idle
will still run this path. To also show in the dropdown, on the laptop:
right-click `3DPipes.scr` → **Install** (UAC copies into System32).

### Fedora adjustments

These were the laptop's instructions. They are closed for `v0.4.0`.

1. **Committed and tagged from Fedora.** `v0.4.0` is `74bb637` on `main`,
   and the GitHub Release is published. The Windows checkout was not the
   place to commit it.
2. **Do not `git add` the 0-line script diffs** (`start.sh`, `server.py`,
   `scripts/*.sh`, `scripts/*.py`). This box has `core.autocrlf=true` and
   `core.filemode=true`; OneDrive/NTFS dropped `+x` and may have touched
   CRLF. Same as [publishing.md](publishing.md) § “Line endings and +x”.
   On Fedora: `git checkout --` those files if they look dirty, then
   `chmod +x` as already documented.
3. **Do not commit** `dist/3DPipes.exe`, `dist/3DPipes.scr`, `.venv`, or
   `docs/*.png` (already gitignored). The Fedora `dist/` tree is still
   ELF / AppImage — do not upload it as a Windows build.
4. README Windows config path (`%LOCALAPPDATA%\dedrixG\3d-pipes`) is the
   *predicted* dir. This freeze wrote state under
   `%LOCALAPPDATA%\State\dedrixG\3d-pipes`. Left as a note, not a bug.
   Store-Python *source* runs also virtualize AppData under
   `Packages\PythonSoftwareFoundation.Python.3.13_*\LocalCache\` — the
   frozen `.exe` does not.
5. Frozen `.exe` / `.scr` is smoked on real Win11 hardware. That box is
   ticked in [cross-platform-plan.md](cross-platform-plan.md) phase 2.
6. Still unsigned. Still one monitor on this laptop. MSAA was `samples=0`.
   `/p` HWND embed was not re-tested on this pass.
7. **Display scale** is accepted for `v0.4.0`. The pipes look a bit small
   on this laptop. Camera and thickness stay the Fedora-authored values.

## Display scale

Accepted for `v0.4.0`. The cube stays authored on the Fedora box
(`GRID=16`, `CELL=1.0`, `DEFAULTS["thickness"]=0.33`, camera 56° FOV and
`dist * 1.08` in `PipesWidget._paint_gl`). Perspective fills the **same
fraction of the window** at any pixel size, so 1080p vs 1440p at the
same aspect looks identical. This laptop is a **smaller physical
panel**, so that fraction looks small. This release does not scale
camera or thickness from `QScreen`.

### This laptop (the user to match)

`--dump-screens` plus `QScreen` on 2026-09-10:

| | |
| --- | --- |
| Name | `\\.\DISPLAY1` (Chimei Innolux) |
| Geometry | `0,0 1920x1080` (dpr=1, 100% DPI) |
| Physical | 344 × 193 mm (~15.5" diagonal) |
| DPI | logical 96, physical ~142 |
| Refresh | 60 Hz |

Fullscreen cover is 1920×1080. Pipes sat as a small cluster in the
middle (`docs/windows-fullscreen-frozen.png`). That is the `v0.4.0` look.
