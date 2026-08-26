#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
cd "$ROOT"

install_launcher() {
  local apps="$HOME/.local/share/applications"
  local desk="$HOME/Desktop"
  mkdir -p "$apps" "$HOME/.local/share/icons/hicolor/scalable/apps"
  cp -f "$ROOT/share/icon.svg" "$HOME/.local/share/icons/hicolor/scalable/apps/pipes-screensaver.svg"
  sed "s|@ROOT@|$ROOT|g" "$ROOT/share/pipes-screensaver.desktop" > "$apps/pipes-screensaver.desktop"
  chmod +x "$apps/pipes-screensaver.desktop"
  sed "s|@ROOT@|$ROOT|g" "$ROOT/share/pipes-screensaver-settings.desktop" > "$apps/pipes-screensaver-settings.desktop"
  chmod +x "$apps/pipes-screensaver-settings.desktop"
  if [[ -d "$desk" ]]; then
    sed "s|@ROOT@|$ROOT|g" "$ROOT/share/pipes-screensaver.desktop" > "$desk/3D Pipes.desktop"
    chmod +x "$desk/3D Pipes.desktop"
    gio set "$desk/3D Pipes.desktop" metadata::trusted true 2>/dev/null || true
    sed "s|@ROOT@|$ROOT|g" "$ROOT/share/pipes-screensaver-settings.desktop" > "$desk/3D Pipes Settings.desktop"
    chmod +x "$desk/3D Pipes Settings.desktop"
    gio set "$desk/3D Pipes Settings.desktop" metadata::trusted true 2>/dev/null || true
  fi
}

install_launcher || true
exec python3 "$ROOT/pipes.py" "$@"
