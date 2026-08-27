# Changelog

All notable changes to 3D Pipes are listed here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned

- macOS `3D Pipes.app` and a macOS GitHub Actions build
- Optional later: Flatpak / `.deb`

## [0.2.0] — 2026-08-26

Cross-platform source, Linux AppImage, and Windows `.exe` / `.scr`. Tag `v0.2.0` and GitHub Actions attach the downloads. How to ship it from Fedora: [docs/publishing.md](docs/publishing.md). What was tested on Windows: [docs/windows-test-notes.md](docs/windows-test-notes.md).

### Added

- Portable config and log paths via `QStandardPaths` (`dedrixG` / `3d-pipes`)
- One-time migration from `~/.config/pipes-screensaver/config.json`
- Linux AppImage build (`./scripts/build-appimage.sh`)
- Debian/Ubuntu pip + system library install notes
- `--dump-screens` prints the per-monitor cover plan
- `--version`
- Fullscreen skips empty/duplicate screens, keeps negative origins and mixed aspect ratios, and follows hotplug
- Windows screensaver flags `/s` `/c` `/p`, PyInstaller spec, and `3DPipes.scr`
- GitHub Actions: tests on push; tag `v*` publishes AppImage + Windows exe/scr
- Maintainer publish guide (`docs/publishing.md`)

### Fixed

- Windows Control Panel `/c <HWND>` (and `/a <HWND>` / `/s <HWND>`) no longer dies as an unrecognized argparse token
- Fullscreen on Windows is actually visible: skip Wayland's early `createWinId()`, stay on top, and pin `HWND_TOPMOST` so the cover is not behind other windows and the taskbar
- `/p` preview parents into the Display Settings HWND with 64-bit-safe ctypes, resizes to the parent, and quits when that parent is destroyed
- `--window` keeps the settings panel hidden (`--settings` still opens it)
- `faulthandler.enable()` no longer crashes a windowed Windows process when `sys.stderr` is None
- OpenGL backend is left to Qt on macOS instead of forcing `QT_OPENGL=desktop`

### Known issues

- macOS app is not in this release
- MSAA may report 0 samples on some GPUs (Linux Mesa and the Windows box used for smoke); “Smooth edges” still saves and applies on the next launch when the driver allows it
- Windows builds are unsigned — SmartScreen “More info → Run anyway” is expected
- Multi-monitor cover was unit-tested; only one real Windows display was smoked

## [0.1.0] — 2026-08-26

First public Linux release. Native OpenGL, no browser.

### Added

- Fullscreen 3D Pipes on every monitor (one window per screen)
- Windowed preview with a settings panel (`--settings` / `--window`)
- Saved settings: pipe count, thickness, speed, reset interval, pause before reset, joint style, camera spin, MSAA
- Joint styles: elbow, ball, mixed, cycle
- World-space key light from the left so highlights travel as the camera orbits
- Desktop launchers for 3D Pipes and 3D Pipes Settings
- Config file at `~/.config/pipes-screensaver/config.json`

### Fixed

- OpenGL startup crash (`QOpenGLFunctions_3_3_Core` null on init)
- Instant quit on desktop double-click (grace period ignored mouse press)
- False “crash” from tiny mouse / touchpad motion (now 5s arm, ~50px move)
- Hollow pipes and visible segment discs
- Shredded U-bends from overlapping cylinder, elbow, cap, and plug meshes
- Elbow lighting looking inverted vs the connected straight pipe
- Dark collars at elbow joins (normals taken from the model matrix in-shader)

### Known issues

- Linux-only launchers and config paths
- MSAA may report 0 samples on some Wayland + Mesa setups; the “Smooth edges” option still applies on next launch when the driver allows it
- Not yet a system screensaver (KDE/GNOME/Windows/macOS hook)

[Unreleased]: https://github.com/dedrixG/3d-pipes/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/dedrixG/3d-pipes/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/dedrixG/3d-pipes/releases/tag/v0.1.0

