#!/usr/bin/env python3
"""Build share/icon.icns from share/icon.svg (ImageMagick)."""
from __future__ import annotations

import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "share" / "icon.svg"
OUT = ROOT / "share" / "icon.icns"

# PNG-in-ICNS types used by modern macOS. Sizes are pixel dimensions.
ICONS: list[tuple[bytes, int]] = [
    (b"icp4", 16),
    (b"icp5", 32),
    (b"icp6", 64),
    (b"ic07", 128),
    (b"ic08", 256),
    (b"ic09", 512),
    (b"ic10", 1024),
    (b"ic11", 32),
    (b"ic12", 64),
    (b"ic13", 256),
    (b"ic14", 512),
]


def _magick() -> str:
    for name in ("magick", "convert"):
        try:
            subprocess.run([name, "-version"], check=True, capture_output=True)
            return name
        except (OSError, subprocess.CalledProcessError):
            continue
    raise SystemExit("ImageMagick (magick/convert) is required to rasterize icon.svg")


def rasterize(svg: Path, dest: Path, size: int) -> None:
    cmd = _magick()
    subprocess.run(
        [
            cmd,
            "-background",
            "none",
            str(svg),
            "-resize",
            f"{size}x{size}",
            str(dest),
        ],
        check=True,
    )


def pack_icns(pngs: list[tuple[bytes, bytes]]) -> bytes:
    chunks = b""
    for ostype, data in pngs:
        chunks += ostype + struct.pack(">I", 8 + len(data)) + data
    return b"icns" + struct.pack(">I", 8 + len(chunks)) + chunks


def main() -> int:
    if not SVG.is_file():
        raise SystemExit(f"missing {SVG}")
    pngs: list[tuple[bytes, bytes]] = []
    with tempfile.TemporaryDirectory(prefix="3d-pipes-icns-") as tmp:
        tmp_path = Path(tmp)
        cache: dict[int, bytes] = {}
        for ostype, size in ICONS:
            if size not in cache:
                png_path = tmp_path / f"icon-{size}.png"
                rasterize(SVG, png_path, size)
                cache[size] = png_path.read_bytes()
            pngs.append((ostype, cache[size]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(pack_icns(pngs))
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
