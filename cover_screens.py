"""Pick which QScreen-like objects should get a fullscreen cover window.

Works with real QScreen instances or simple fakes that implement geometry()
and optionally name(). Independent of Qt so layouts can be unit-tested.
"""
from __future__ import annotations


def _geo_tuple(geo) -> tuple[int, int, int, int] | None:
    try:
        w = int(geo.width())
        h = int(geo.height())
        if w < 1 or h < 1:
            return None
        return (int(geo.x()), int(geo.y()), w, h)
    except Exception:
        return None


def iter_cover_screens(screens) -> list:
    """Drop null/empty/duplicate screens; keep unusual origins and aspect ratios."""
    out = []
    seen: set[tuple[int, int, int, int]] = set()
    if not screens:
        return out
    for screen in screens:
        if screen is None:
            continue
        try:
            geo = screen.geometry()
        except Exception:
            continue
        key = _geo_tuple(geo)
        if key is None or key in seen:
            continue
        seen.add(key)
        out.append(screen)
    return out


def cover_plan(screens) -> list[dict]:
    plan = []
    for screen in iter_cover_screens(screens):
        geo = screen.geometry()
        x, y, w, h = int(geo.x()), int(geo.y()), int(geo.width()), int(geo.height())
        name = ""
        try:
            name = str(screen.name())
        except Exception:
            name = ""
        dpr = 1.0
        try:
            dpr = float(screen.devicePixelRatio())
        except Exception:
            pass
        plan.append(
            {
                "name": name or f"{x},{y}",
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "dpr": dpr,
                "portrait": h > w,
            }
        )
    return plan


def format_cover_plan(screens) -> str:
    rows = cover_plan(screens)
    if not rows:
        return "3D Pipes  no coverable screens"
    lines = [f"3D Pipes  {len(rows)} screen(s) to cover:"]
    for i, r in enumerate(rows, 1):
        orient = "portrait" if r["portrait"] else "landscape"
        lines.append(
            f"  {i:2d}. {r['name']}  {r['x']},{r['y']}  "
            f"{r['width']}x{r['height']}  dpr={r['dpr']:g}  {orient}"
        )
    return "\n".join(lines)
