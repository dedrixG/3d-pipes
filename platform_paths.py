"""OS-agnostic config/state locations for 3D Pipes."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ORG_NAME = "dedrixG"
APP_NAME = "3d-pipes"
APP_DISPLAY_NAME = "3D Pipes"
APP_VERSION = "0.4.0"
ORG_DOMAIN = "github.com/dedrixG"

LEGACY_LINUX_CONFIG = Path.home() / ".config" / "pipes-screensaver" / "config.json"


def predicted_config_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / ORG_NAME / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Preferences" / ORG_NAME / APP_NAME
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / ORG_NAME / APP_NAME


def predicted_state_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / ORG_NAME / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / ORG_NAME / APP_NAME
    xdg = os.environ.get("XDG_STATE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "state"
    return base / ORG_NAME / APP_NAME


def apply_app_identity() -> None:
    from PySide6.QtCore import QCoreApplication

    QCoreApplication.setOrganizationName(ORG_NAME)
    QCoreApplication.setOrganizationDomain(ORG_DOMAIN)
    QCoreApplication.setApplicationName(APP_NAME)


def _qt_writable(kind) -> Path | None:
    try:
        from PySide6.QtCore import QCoreApplication, QStandardPaths

        if QCoreApplication.instance() is None:
            return None
        loc = QStandardPaths.writableLocation(kind)
        return Path(loc) if loc else None
    except Exception:
        return None


def config_dir() -> Path:
    from PySide6.QtCore import QStandardPaths

    return _qt_writable(QStandardPaths.StandardLocation.AppConfigLocation) or predicted_config_dir()


def state_dir() -> Path:
    from PySide6.QtCore import QCoreApplication, QStandardPaths

    if hasattr(QStandardPaths.StandardLocation, "AppStateLocation"):
        found = _qt_writable(QStandardPaths.StandardLocation.AppStateLocation)
        if found is not None:
            return found
    generic = getattr(QStandardPaths.StandardLocation, "GenericStateLocation", None)
    if generic is not None and QCoreApplication.instance() is not None:
        base = QStandardPaths.writableLocation(generic)
        if base:
            org = QCoreApplication.organizationName() or ORG_NAME
            app = QCoreApplication.applicationName() or APP_NAME
            return Path(base) / org / app
    return predicted_state_dir()


def config_path() -> Path:
    return config_dir() / "config.json"


def migrate_legacy_config(dest: Path | None = None, legacy: Path | None = None) -> bool:
    """Copy the old Linux config once if the new file is not there yet."""
    dest = dest if dest is not None else config_path()
    legacy = legacy if legacy is not None else LEGACY_LINUX_CONFIG
    if dest.exists() or not legacy.is_file():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(legacy.read_bytes())
    return True


def peek_multisample(default: bool = True) -> bool:
    """Read MSAA before QApplication exists (needed for QSurfaceFormat)."""
    for path in (predicted_config_dir() / "config.json", LEGACY_LINUX_CONFIG):
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text())
            if isinstance(data, dict) and "multisample" in data:
                return bool(data["multisample"])
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            continue
    return default


def configure_opengl_env() -> None:
    """Set Qt GL backend. Skip on macOS so Cocoa can pick a 4.1 core context."""
    if sys.platform == "darwin":
        return
    os.environ.setdefault("QT_OPENGL", "desktop")
