# Publishing 3D Pipes from Fedora

This is the maintainer guide for putting a tagged release on the public
GitHub repo [`dedrixG/3d-pipes`](https://github.com/dedrixG/3d-pipes).
End users should use the [README](../README.md), not this file.

## What 0.3.0 is (what was done)

0.1.0 was Linux-only. 0.2.0 added Windows `.exe` / `.scr` and the AppImage.

0.3.0 is the same Python + PySide6 app plus a macOS `.app` built on GitHub’s
Mac runners (this Fedora box cannot smoke it). Checklist:
[macos-notes.md](macos-notes.md).

| Work | Where |
| --- | --- |
| Portable config/logs (`QStandardPaths`, org `dedrixG`, app `3d-pipes`) | `platform_paths.py` |
| Linux AppImage | `scripts/build-appimage.sh`, `packaging/linux/` |
| Windows `/s` `/c` `/p` screensaver flags, `.exe` / `.scr` spec | `pipes.py`, `packaging/windows/`, `scripts/build-windows.bat` |
| Per-monitor cover plan (gaps, negative origins, hotplug) | `cover_screens.py` |
| Windows bugs found on real Win11 hardware | see below |
| macOS `.app` (PyInstaller bundle, arm64 + Intel zips) | `packaging/macos/`, `scripts/build-macos.sh` |
| Tests + tag-triggered GitHub Release with binaries | `.github/workflows/` |

**Windows smoke (source, not a frozen exe):** one 1920×1080 display at 125%
DPI, Python 3.13, PySide6 6.11, OpenGL 3.3. Fullscreen was invisible until
stay-on-top + no early `createWinId()`. `/c <HWND>` crashed argparse. `/p`
preview HWND handling was incomplete. Details:
[windows-test-notes.md](windows-test-notes.md).

**macOS:** no hardware here. CI builds `3D Pipes.app`; a human with a Mac
should run the checklist in [macos-notes.md](macos-notes.md) before calling
it smoked.

Fedora does **not** cross-compile the Windows exe or the macOS app. Pushing
tag `v0.3.0` runs GitHub Actions on `ubuntu-latest`, `windows-latest`,
`macos-latest` (arm64), and `macos-15-intel`, then attaches:

- `3D_Pipes-x86_64.AppImage`
- `3DPipes.exe`, `3DPipes.scr`, `3DPipes-windows.zip`
- `3D_Pipes-macos-arm64.zip`, `3D_Pipes-macos-x86_64.zip`

to the GitHub Release. That is the public download-and-run path.

To build the `.app` **without** tagging (artifact only): Actions → Release →
**Run workflow**. Publish still only happens on `v*` tags.

## What not to commit

`dist/`, `build/`, `.venv/`, `__pycache__/`, `*.AppImage`, and `docs/*.png`
are gitignored on purpose. Those are local/CI outputs (the Linux tree under
`dist/` is full of Fedora `.so` files and must not go public).

Do not add `web/` — the native app does not use it.

## Fedora: ship it

OneDrive/NTFS will have dropped the executable bit and may have CRLF from the
Windows edits. Do this **on Fedora**, in the repo root.

### 1. Line endings and +x

```bash
git add --renormalize .
chmod +x start.sh server.py \
  scripts/build-appimage.sh scripts/build-macos.sh scripts/make-icns.py \
  scripts/release-check.sh scripts/changelog-excerpt.py
```

`.gitattributes` forces LF for everything except `*.bat` (CRLF).

### 2. Sanity check

```bash
# Fedora system packages, if you do not already have them:
sudo dnf install python3-pyside6 python3-numpy

chmod +x scripts/release-check.sh
./scripts/release-check.sh
```

Expect unit tests OK, `3D Pipes 0.3.0`, and a cover plan for your monitors.

Optional local AppImage (not required; CI builds it):

```bash
python3 -m pip install --user 'pyinstaller>=6'
./scripts/build-appimage.sh
# smoke: ./dist/3D_Pipes-x86_64.AppImage --settings
```

### 3. Stage only source

```bash
git add \
  .gitattributes .gitignore \
  .github/workflows/release.yml .github/workflows/test.yml \
  CHANGELOG.md LICENSE README.md \
  cover_screens.py pipes.py platform_paths.py requirements.txt server.py start.sh \
  packaging scripts share tests \
  docs/cross-platform-plan.md docs/publishing.md docs/windows-test-notes.md \
  docs/macos-notes.md

git status   # dist/, .venv/, docs/*.png must stay untracked
```

If `start.sh` / `scripts/*.sh` show as non-executable, run the `chmod +x` again
and `git add` those files.

### 4. Commit and push `main`

```bash
git commit -m "$(cat <<'EOF'
Release 0.3.0: macOS app bundle

Ship 3D Pipes.app (arm64 + Intel zips) from a v0.3.0 tag via GitHub Actions.
Same Python/Qt core as Linux and Windows. No Mac hardware smoke on this box.
EOF
)"

git push origin main
```

Confirm [Actions → Test](https://github.com/dedrixG/3d-pipes/actions) is green
on that push.

### 5. Tag (this publishes the downloads)

```bash
git tag -a v0.3.0 -m "3D Pipes 0.3.0"
git push origin v0.3.0
```

Watch [Actions → Release](https://github.com/dedrixG/3d-pipes/actions). When it
finishes, the Release page should list the AppImage, the Windows files, and
both macOS zips.

Repo **must be public** (Settings → Change repository visibility) if you want
strangers to download without signing in.

### 6. If Actions is red

- Linux AppImage: open the `linux` job log. FUSE-less runners already extract
  `appimagetool`; missing Qt libs are installed in the workflow.
- Windows exe: open the `windows` job log. The spec is
  `packaging/windows/3d-pipes.spec`.
- macOS app: open the `macos` job log (arm64 and Intel). The spec is
  `packaging/macos/3d-pipes.spec`. `macos-15-intel` is the Intel runner.
- You can also run **Release → Run workflow** (`workflow_dispatch`) to rebuild
  artifacts without creating a Release. Only `v*` tags publish.

Do not upload the Fedora `dist/` tree as a Windows build. It is ELF, not PE.

## Public install (what you tell people)

Already in the README:

- Linux: download AppImage, `chmod +x`, run.
- Windows: download `3DPipes.exe` (SmartScreen: More info → Run anyway).
  Optional: `3DPipes.scr` → right-click → Install.
- macOS: unzip the arm64 or Intel zip, right-click `3D Pipes.app` → Open.

## Version bump later

1. Set `APP_VERSION` in `platform_paths.py`.
2. Add a `## [x.y.z] — YYYY-MM-DD` section at the top of `CHANGELOG.md`
   (keep `## [Unreleased]` above it).
3. Commit, push `main`, tag `vX.Y.Z`, push the tag.
