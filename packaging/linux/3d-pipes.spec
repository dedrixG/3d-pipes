# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

repo = Path(SPECPATH).resolve().parents[1]

datas = [(str(repo / "share" / "icon.svg"), "share")]
binaries = []
flexi_dir = Path("/usr/lib64/flexiblas")
for name in (
    "libflexiblas_openblas-openmp.so",
    "libflexiblas_netlib.so",
    "libflexiblas_fallback_lapack.so",
):
    lib = flexi_dir / name
    if lib.is_file():
        binaries.append((str(lib), "."))
hiddenimports = [
    "cover_screens",
    "platform_paths",
    "PySide6.QtOpenGL",
    "PySide6.QtOpenGLWidgets",
    "PySide6.QtSvg",
    "shiboken6",
    "numpy",
]

a = Analysis(
    [str(repo / "pipes.py")],
    pathex=[str(repo)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(repo / "packaging" / "linux" / "rthook_flexiblas.py")],
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
