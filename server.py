#!/usr/bin/env python3
"""Back-compat launcher. 3D Pipes is a native OpenGL app now."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from pipes import main

if __name__ == "__main__":
    sys.exit(main())
