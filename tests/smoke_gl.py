"""Headed OpenGL smoke: start a window, wait for GL, grab a frame, exit."""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from pipes import PipesSim, PipesWidget, configure_surface, load_config
from platform_paths import apply_app_identity, configure_opengl_env, peek_multisample


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "windows-gl-smoke.png"
    out.parent.mkdir(parents=True, exist_ok=True)

    configure_opengl_env()
    configure_surface(peek_multisample())
    app = QApplication([sys.argv[0]])
    apply_app_identity()
    sim = PipesSim(load_config(), parent=app)
    view = PipesWidget(sim, windowed=True)
    view.resize(960, 540)
    view.show()
    view.raise_()
    view.activateWindow()

    result = {"code": 2}

    def check() -> None:
        try:
            if not view._ready or view.gl is None:
                print("SMOKE FAIL: OpenGL did not become ready", flush=True)
                result["code"] = 1
                app.quit()
                return
            img = view.grabFramebuffer()
            if img.isNull() or img.width() < 2:
                print("SMOKE FAIL: empty framebuffer", flush=True)
                result["code"] = 1
                app.quit()
                return
            img.save(str(out))
            print(f"SMOKE OK: {out} {img.width()}x{img.height()} items={len(sim.items)}", flush=True)
            result["code"] = 0
        except Exception:
            traceback.print_exc()
            result["code"] = 1
        app.quit()

    QTimer.singleShot(2500, check)
    QTimer.singleShot(8000, app.quit)
    app.exec()
    return result["code"]


if __name__ == "__main__":
    sys.exit(main())
