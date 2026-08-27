# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

repo = Path(SPECPATH).resolve().parents[1]
sys.path.insert(0, str(repo))
from platform_paths import APP_DISPLAY_NAME, APP_VERSION  # noqa: E402

icon = repo / "share" / "icon.icns"

a = Analysis(
    [str(repo / "pipes.py")],
    pathex=[str(repo)],
    binaries=[],
    datas=[(str(repo / "share" / "icon.svg"), "share")],
    hiddenimports=[
        "cover_screens",
        "platform_paths",
        "PySide6.QtOpenGL",
        "PySide6.QtOpenGLWidgets",
        "PySide6.QtSvg",
        "shiboken6",
        "numpy",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineQuick",
        "PySide6.Qt3DCore",
        "PySide6.QtBluetooth",
        "PySide6.QtNfc",
        "PySide6.QtPdf",
        "PySide6.QtDesigner",
        "PySide6.QtTest",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="3d-pipes",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="3d-pipes",
)

app = BUNDLE(
    coll,
    name=f"{APP_DISPLAY_NAME}.app",
    icon=str(icon) if icon.is_file() else None,
    bundle_identifier="com.dedrixG.threedpipes",
    info_plist={
        "CFBundleName": APP_DISPLAY_NAME,
        "CFBundleDisplayName": APP_DISPLAY_NAME,
        "CFBundleGetInfoString": f"{APP_DISPLAY_NAME} {APP_VERSION}",
        "CFBundleShortVersionString": APP_VERSION,
        "CFBundleVersion": APP_VERSION,
        "CFBundleIdentifier": "com.dedrixG.threedpipes",
        "NSHumanReadableCopyright": "Copyright © 2026 dedrixG",
        "NSHighResolutionCapable": True,
        "NSSupportsAutomaticGraphicsSwitching": True,
        "LSMinimumSystemVersion": "12.0",
        "LSApplicationCategoryType": "public.app-category.entertainment",
        "NSPrincipalClass": "NSApplication",
    },
)
