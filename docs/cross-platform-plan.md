# Cross-platform action plan

Keep one Python + PySide6 + OpenGL codebase. Do **not** rewrite per OS. Package that same app for Windows, macOS, and more Linux distros.

Today the renderer already is portable. What is not: paths, launchers, installers, and “real screensaver” hooks.

## Current blockers

| Area | Linux (now) | What others need |
| --- | --- | --- |
| Config | `~/.config/pipes-screensaver/` | `QStandardPaths.AppConfigLocation` |
| Crash log | `~/.local/state/pipes-screensaver/` | `QStandardPaths.AppLocalDataLocation` |
| Launch | `start.sh` + `.desktop` + `gio` | Windows `.exe` / Start Menu; macOS `.app` |
| Fullscreen | one frameless window per `QScreen` | Same Qt API; test Win32 and Cocoa |
| OpenGL | Mesa 3.3 core, `QT_OPENGL=desktop` | Windows: desktop GL; macOS: 4.1 core (Apple cap) |
| Screensaver | run as an app | Windows `.scr` (`/s` `/c` `/p`); macOS `.saver` later |

## Principles

1. One `pipes.py`. Platform differences live in a thin `platform_paths.py` / launcher layer.
2. Ship a **standalone app** first. Register as an OS screensaver second.
3. GitHub Actions builds the artifacts. No one should need Python installed to run a release.
4. macOS OpenGL is deprecated but still works through Qt for this (no compute, no Metal rewrite).

## Phases

### 0 — Portable core (half day)

Do this before any OS packaging. Small, unblocks everything.

- [x] Replace hardcoded `~/.config` and `~/.local/state` with `QStandardPaths`
- [x] Set `QApplication` org/name (`dedrixG` / `3d-pipes`) so those paths are stable
- [x] Move `QT_OPENGL=desktop` behind `sys.platform` (skip or use `software` fallback on macOS if the context fails)
- [x] `--window` / `--settings` / `--fullscreen` unchanged
- [x] Add `--preview` (HWND / window id) stub for future Windows `/p`
- [x] Manual check: this Linux machine still runs; config file migrates once from the old path if present

**Done when:** same source runs with no Linux-only paths, still works on this machine.

### 1 — Broader Linux support (1–2 days)

- [x] `pip install -r requirements.txt` documented for Ubuntu/Debian (`python3-pip`, maybe `libxcb-*` notes)
- [x] **AppImage** via PyInstaller + appimagetool (`./scripts/build-appimage.sh`). One file, any modern distro.
- [ ] Optional later: Flatpak (Flathub) and a `.deb` / COPR. Not required for v1.
- [x] Keep `.desktop` install for people who clone the repo
- [x] Test: AppImage + from-source on this Linux machine (Wayland). Other distros not smoke-tested here.

**Done when:** `./scripts/build-appimage.sh` produces a runnable `.AppImage`. Publishing it on a GitHub Release is Phase 4.

### 2 — Windows (2–3 days)

PySide6 is the Windows port. The work is packaging and screensaver flags.

- [x] PyInstaller onefile spec → `3DPipes.exe` (`packaging/windows/3d-pipes.spec`, `scripts/build-windows.bat`)
- [x] Icon from `share/icon.svg` (export `.ico`)
- [x] Honor classic screensaver args:
  - no args or `/s` → fullscreen (current default)
  - `/c` → settings window
  - `/p <HWND>` → embed into the preview HWND on Windows; small window otherwise
- [x] Optional: copy/rename to `3DPipes.scr` and document “right-click → Install”
- [ ] Multi-monitor on a real Windows box (or a VM with two displays)
- [x] Fullscreen stay-on-top on Win32 (without it the cover sat behind other windows / the taskbar)
- [x] Code signing is **not** v1 (SmartScreen warning is acceptable for a hobby release)
- [x] Source smoke on real Win11 hardware: `--dump-screens`, `--settings`, OpenGL grab, `/c HWND` argv, fullscreen cover

**Done when:** `scripts\build-windows.bat` on a Windows machine produces `dist\3DPipes.exe`. Source smoke on Win11 is done; frozen `.exe` still needs a local PyInstaller run.

### 3 — macOS (2–3 days)

- [x] PyInstaller onedir + `BUNDLE` → `3D Pipes.app` (`packaging/macos/3d-pipes.spec`, `scripts/build-macos.sh`)
- [x] Icon `.icns` from `share/icon.svg` (`scripts/make-icns.py`)
- [x] Cover each `QScreen` by geometry + stay-on-top (Cocoa `showFullScreen()` would put each window in its own Space)
- [ ] Hardware: built-in + external display (no Mac on this box; checklist in `docs/macos-notes.md`)
- [x] OpenGL 4.1 core requested on Darwin; shaders stay `#version 330 core`; fail dialog if they don’t compile
- [x] Settings + fullscreen as a normal app first
- [x] Notarization / hardened runtime is **not** v1 (Gatekeeper “right-click Open” is OK)
- [ ] Native `.saver` (ScreenSaverEngine) is a **follow-up**. It is a different bundle type and not required to enjoy the app.

**Done when:** a zip containing `3D Pipes.app` is built on GitHub’s Mac runners (arm64 + Intel). Opening it on real hardware is still a smoke checklist, not a claim.

### 4 — CI and release (1 day, once 1–3 work locally)

- [x] GitHub Actions:
  - `ubuntu-latest` → AppImage
  - `windows-latest` → exe zip
  - `macos-latest` → `3D_Pipes-macos-arm64.zip`
  - `macos-15-intel` → `3D_Pipes-macos-x86_64.zip`
- [x] Tag `v0.2.0` (Linux + Windows)
- [ ] Tag `v0.3.0` (adds macOS zips) once Actions has built the `.app`
- [x] Release notes from `CHANGELOG.md` (`scripts/changelog-excerpt.py`)
- [x] README install section per OS

**Done when:** pushing tag `v0.3.0` publishes Linux + Windows + macOS artifacts.

## Suggested order

```
0 portable paths  →  1 AppImage  →  2 Windows exe  →  3 macOS app  →  4 CI tags
```

Windows before macOS: more people still expect a `.exe`/`.scr`, and OpenGL is less of a fight. AppImage first so Linux users on other distros are not left behind while Windows is in progress.

## Out of scope for this pass

- Metal / Direct3D rewrite
- Separate C++/C#/Swift codebases
- xscreensaver module, KDE KWin effect, GNOME extension
- macOS `.saver` in System Settings
- Paid signing certificates

Those can stack on later without changing the core sim.

## Risk notes

- **macOS OpenGL:** Qt still creates a 4.1 core context. Shaders are `#version 330 core` — compatible. If a future macOS build of Qt drops GL, then we reassess (not now).
- **Windows preview HWND:** fiddly; shipping `/s` and `/c` is enough for people to use it.
- **PyInstaller size:** 40–80 MB because of Qt. Fine for this kind of app. Don’t chase a 2 MB binary.
- **Wayland vs Win32 vs Cocoa fullscreen:** keep the current “one widget per `QScreen`” model; it is the Qt-portable approach.

## Effort snapshot

| Phase | Calendar | Depends on |
| --- | --- | --- |
| 0 Portable core | ~0.5 day | nothing |
| 1 Linux AppImage | 1–2 days | 0 |
| 2 Windows | 2–3 days | 0 |
| 3 macOS | 2–3 days | 0 |
| 4 CI | ~1 day | 1–3 working locally |

Phases 1–3 can overlap after 0 if you want, but serial is simpler for a first public release.
