# 3D Pipes

Classic Windows **3D Pipes**, as a native OpenGL screensaver.

One window per monitor. Move the mouse or press a key to exit.

![3D Pipes icon](share/icon.svg)

**v0.4.0** ships a Linux AppImage, Windows `.exe` / `.scr`, and macOS
`.app` zips from [Releases](https://github.com/dedrixG/3d-pipes/releases).
Sequential pipe start is the default (256-segment / 5-color caps); scenes
reset when pipes finish.

## Quick start

### Linux (AppImage)

Download `3D_Pipes-x86_64.AppImage` from
[Releases](https://github.com/dedrixG/3d-pipes/releases), then:

```bash
chmod +x 3D_Pipes-x86_64.AppImage
./3D_Pipes-x86_64.AppImage              # fullscreen, every monitor
./3D_Pipes-x86_64.AppImage --settings   # windowed preview + settings
```

`chmod +x` is normal on Linux: browsers and `curl` save a regular file, not a
program. You mark it executable once after downloading.

Needs a working GPU / OpenGL 3.3 driver.

### Windows

Download `3DPipes.exe` from
[Releases](https://github.com/dedrixG/3d-pipes/releases). Double-click for
fullscreen, or run `3DPipes.exe --settings`.

To install as a screensaver, use `3DPipes.scr` (same folder on the Release)
and right-click → **Install**. Windows then calls:

| Flag | Meaning |
| --- | --- |
| `/s` (or no flag) | Fullscreen |
| `/c` or `/c <HWND>` | Settings |
| `/p <HWND>` | Tiny preview in Display Settings |

The build is unsigned. SmartScreen may show “Windows protected your PC” —
**More info → Run anyway**. That is expected for a hobby release.

### macOS

Download `3D_Pipes-macos-arm64.zip` (Apple Silicon) or
`3D_Pipes-macos-x86_64.zip` (Intel) from
[Releases](https://github.com/dedrixG/3d-pipes/releases). Unzip, then
right-click `3D Pipes.app` → **Open** (the app is unsigned; Gatekeeper
blocks a first-time double-click).

```bash
open "3D Pipes.app"                        # fullscreen, every display
open "3D Pipes.app" --args --settings      # windowed preview + settings
```

This is a normal app, not a System Settings screensaver. Needs macOS 12+
and a GPU that can do OpenGL 4.1 core (every Mac that runs 12 can).

## From source

```bash
git clone https://github.com/dedrixG/3d-pipes.git
cd 3d-pipes
```

### Linux

```bash
sudo dnf install python3-pyside6 python3-numpy
chmod +x start.sh
./start.sh              # fullscreen, every monitor
./start.sh --settings   # windowed preview + settings
./start.sh --dump-screens
```

`./start.sh` also installs **3D Pipes** and **3D Pipes Settings** launchers on
the desktop and in the application menu.

### Debian / Ubuntu

```bash
sudo apt install python3-pip python3-venv \
  libgl1 libglib2.0-0 libxkbcommon-x11-0 libxcb-cursor0 \
  libxcb-icccm4 libxcb-keysyms1 libxcb-shape0
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./start.sh --settings
```

### Windows (build the exe yourself)

GitHub Actions already publishes `3DPipes.exe`. Building locally needs
Windows 10/11 (this repo does not cross-compile the `.exe` from Linux):

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
scripts\build-windows.bat
```

That writes `dist\3DPipes.exe` and `dist\3DPipes.scr`.

### macOS (build the app yourself)

Needs a Mac (this repo does not cross-compile the `.app` from Linux):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./scripts/build-macos.sh
```

That writes `dist/3D Pipes.app` and `dist/3D_Pipes-macos-<arch>.zip`.

### Linux AppImage (build yourself)

```bash
./scripts/build-appimage.sh
```

## Controls

| | Fullscreen | Windowed / settings |
| --- | --- | --- |
| Exit | Esc always; after 5s also mouse move, click, or any key | Esc |
| Restart | — | Space |
| Settings | — | S toggles the panel |

Settings are saved in the platform config directory:

- Linux: `~/.config/dedrixG/3d-pipes/config.json`
- Windows: `%LOCALAPPDATA%\dedrixG\3d-pipes\config.json`
- macOS: `~/Library/Preferences/dedrixG/3d-pipes/config.json`

An older `~/.config/pipes-screensaver/config.json` is copied there once.

## Settings

| Setting | What it does |
| --- | --- |
| Number of pipes | How many pipes in a scene (1–8) |
| Pipe start | Sequential (default) grows one pipe until it stops, then starts the next (max 256 segments, max 5 colors). Simultaneous grows every pipe at once. |
| Thickness | Pipe radius |
| Speed | How fast new segments grow |
| Reset interval | Parked in 0.4.0 — scenes restart after pipes fill the cube |
| Pause before reset | Delay after pipes finish before starting over |
| Joints | Elbow, ball, mixed, or cycling |
| Camera spin | Slow orbit |
| Smooth edges | MSAA — applies the next time you launch |

## Requirements

- Linux (Wayland or X11), Windows 10/11, or macOS 12+
- Python 3.10+ (from source only)
- [PySide6](https://pypi.org/project/PySide6/) and NumPy (from source only)
- OpenGL 3.3+

## Changelog

[CHANGELOG.md](CHANGELOG.md)

Maintainers shipping a tag: [docs/publishing.md](docs/publishing.md).

## License

[MIT](LICENSE)
