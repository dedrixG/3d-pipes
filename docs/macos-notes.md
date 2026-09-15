# macOS notes (no hardware smoke on this box)

3D Pipes for macOS is a normal `.app`, not a System Settings `.saver`.
GitHub Actions builds it; this Fedora machine cannot run the result.

## What CI produces

On tag `v*` (or **Actions → Release → Run workflow**):

| File | Machine |
| --- | --- |
| `3D_Pipes-macos-arm64.zip` | Apple Silicon (`macos-latest`) |
| `3D_Pipes-macos-x86_64.zip` | Intel (`macos-15-intel`) |

Inside each zip: `3D Pipes.app`. Unsigned. PyInstaller ad-hoc signs so the
bundle can launch locally; Gatekeeper still blocks a first-time download
until you right-click → **Open**.

## Install (for whoever has the Mac)

1. Unzip the matching archive (Apple menu → About This Mac: chip vs Intel).
2. Optional: drag `3D Pipes.app` to `/Applications`.
3. Right-click the app → **Open** → Open. Later double-clicks are fine.
4. Default launch is fullscreen on every display.
5. Settings:

```bash
open -a "3D Pipes" --args --settings
# or
"/Applications/3D Pipes.app/Contents/MacOS/3d-pipes" --settings
```

Config: `~/Library/Preferences/dedrixG/3d-pipes/config.json`  
Logs: `~/Library/Application Support/dedrixG/3d-pipes/`

Notarization / Developer ID is not this release. Native `.saver` is later.

## Smoke checklist (when a Mac is available)

Same spirit as [windows-test-notes.md](windows-test-notes.md). Do not call
it done until these pass:

- [ ] `--version` prints `3D Pipes 0.4.0`
- [ ] `--dump-screens` lists built-in (and external, if attached)
- [ ] `--settings` window + sliders save, relaunch picks them up
- [ ] Double-click covers every display (laptop + HDMI if possible)
- [ ] Esc quits immediately, including during the 5s mouse grace
- [ ] After 5s, a real mouse move quits; a tiny jitter does not
- [ ] Pipes look solid; elbow lighting matches the shafts
- [ ] Gatekeeper: right-click Open works; a second launch does not warn
- [ ] Retina: not blurry / not 1/4 of the screen
- [ ] OpenGL log line is 4.1 core (or 3.3+), not a shader dialog

Known risk we coded around but did not see: `showFullScreen()` on Cocoa
creates a Space per window, which would leave a second monitor uncovered.
Cover windows size to `QScreen.geometry()` and stay on top instead.

## Build on a Mac

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./scripts/build-macos.sh
```

Writes `dist/3D Pipes.app` and `dist/3D_Pipes-macos-<arch>.zip`.
Do not run that script on Linux; it will refuse.
