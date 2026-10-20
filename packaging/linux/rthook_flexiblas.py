"""Point FlexiBLAS at backends bundled next to the frozen app."""
import os
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    os.environ.setdefault("FLEXIBLAS_LIBRARY_PATH", str(base))
    os.environ.setdefault("FLEXIBLAS", "openblas-openmp")
