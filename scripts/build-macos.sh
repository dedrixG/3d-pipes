#!/usr/bin/env bash
# Build 3D Pipes.app on macOS (Apple Silicon or Intel). Not a cross-compile.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "scripts/build-macos.sh must run on macOS (or GitHub's macos runner)." >&2
  echo "This Linux machine cannot produce a .app. Use Actions → Release → Run workflow." >&2
  exit 1
fi

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

ARCH="$(uname -m)"
case "$ARCH" in
  arm64|aarch64) ARCH_TAG="arm64" ;;
  x86_64) ARCH_TAG="x86_64" ;;
  *) echo "Unsupported macOS arch: $ARCH" >&2; exit 1 ;;
esac

DIST="$ROOT/dist"
SPEC="$ROOT/packaging/macos/3d-pipes.spec"
APP="$DIST/3D Pipes.app"
ZIP="$DIST/3D_Pipes-macos-${ARCH_TAG}.zip"

mkdir -p "$DIST"

if [[ ! -f "$ROOT/share/icon.icns" ]]; then
  echo "==> generating share/icon.icns"
  if [[ -d "$ROOT/share/icon.iconset" ]]; then
    iconutil -c icns "$ROOT/share/icon.iconset" -o "$ROOT/share/icon.icns"
  else
    "$PYTHON" "$ROOT/scripts/make-icns.py"
  fi
fi

if ! "$PYTHON" -c "import PyInstaller" >/dev/null 2>&1; then
  echo "Installing PyInstaller..." >&2
  "$PYTHON" -m pip install 'pyinstaller>=6'
fi

echo "==> PyInstaller ($PYTHON) $ARCH_TAG"
rm -rf "$ROOT/build/pyinstaller-macos" "$DIST/3d-pipes" "$APP" "$ZIP"
"$PYTHON" -m PyInstaller \
  --noconfirm \
  --distpath "$DIST" \
  --workpath "$ROOT/build/pyinstaller-macos" \
  "$SPEC"

if [[ ! -d "$APP" ]]; then
  echo "PyInstaller did not write $APP" >&2
  ls -la "$DIST" >&2
  exit 1
fi

echo "==> zip"
ditto -c -k --keepParent "$APP" "$ZIP"
echo "Built $APP"
echo "Built $ZIP"
ls -lh "$APP" "$ZIP"
codesign -dv --verbose=2 "$APP" 2>&1 | head -20 || true
