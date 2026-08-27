"""Layouts we cannot plug in: 15 heads, negative origins, mixed DPI, gaps."""
from __future__ import annotations

import unittest

from cover_screens import cover_plan, format_cover_plan, iter_cover_screens


class Geo:
    def __init__(self, x, y, w, h):
        self._x, self._y, self._w, self._h = x, y, w, h

    def x(self):
        return self._x

    def y(self):
        return self._y

    def width(self):
        return self._w

    def height(self):
        return self._h


class FakeScreen:
    def __init__(self, name, x, y, w, h, dpr=1.0):
        self._name = name
        self._geo = Geo(x, y, w, h)
        self._dpr = dpr

    def name(self):
        return self._name

    def geometry(self):
        return self._geo

    def devicePixelRatio(self):
        return self._dpr


class BrokenScreen:
    def geometry(self):
        raise RuntimeError("gone")


class CoverScreensTest(unittest.TestCase):
    def test_empty_and_none(self):
        self.assertEqual(iter_cover_screens([]), [])
        self.assertEqual(iter_cover_screens(None), [])
        self.assertEqual(iter_cover_screens([None]), [])

    def test_skips_zero_and_negative_size(self):
        screens = [
            FakeScreen("ok", 0, 0, 1920, 1080),
            FakeScreen("zero", 100, 100, 0, 1080),
            FakeScreen("neg", 0, 0, 1920, -1),
        ]
        names = [s.name() for s in iter_cover_screens(screens)]
        self.assertEqual(names, ["ok"])

    def test_skips_duplicates_and_broken(self):
        a = FakeScreen("a", 0, 0, 800, 600)
        b = FakeScreen("b", 0, 0, 800, 600)
        screens = [a, BrokenScreen(), b]
        kept = iter_cover_screens(screens)
        self.assertEqual(len(kept), 1)
        self.assertIs(kept[0], a)

    def test_negative_origin_kept(self):
        screens = [
            FakeScreen("left", -1920, 0, 1920, 1080),
            FakeScreen("primary", 0, 0, 1920, 1080),
        ]
        plan = cover_plan(screens)
        self.assertEqual([p["x"] for p in plan], [-1920, 0])

    def test_mixed_aspect_and_dpi(self):
        screens = [
            FakeScreen("uw", 0, 0, 5120, 1440, dpr=1.0),
            FakeScreen("phone", 5120, -200, 1080, 2400, dpr=2.75),
            FakeScreen("square", -1200, 400, 1200, 1200, dpr=1.25),
            FakeScreen("8k", 5120, 2400, 7680, 4320, dpr=1.5),
        ]
        plan = cover_plan(screens)
        self.assertEqual(len(plan), 4)
        self.assertTrue(plan[1]["portrait"])
        self.assertFalse(plan[0]["portrait"])
        self.assertEqual(plan[1]["dpr"], 2.75)

    def test_fifteen_mixed_heads(self):
        screens = []
        for i in range(15):
            if i % 3 == 0:
                screens.append(FakeScreen(f"P{i}", i * 400 - 2000, -i * 50, 1440, 2560, dpr=1.0))
            elif i % 3 == 1:
                screens.append(FakeScreen(f"L{i}", i * 1100, 200, 3840, 1600, dpr=1.25 + (i % 2)))
            else:
                screens.append(FakeScreen(f"4K{i}", -i * 300, i * 800, 3840, 2160, dpr=2.0))
        plan = cover_plan(screens)
        self.assertEqual(len(plan), 15)
        text = format_cover_plan(screens)
        self.assertIn("15 screen(s) to cover", text)
        xs = [p["x"] for p in plan]
        self.assertTrue(min(xs) < 0)
        self.assertTrue(any(p["portrait"] for p in plan))
        self.assertTrue(any(not p["portrait"] for p in plan))

    def test_gap_in_virtual_desktop(self):
        screens = [
            FakeScreen("A", 0, 0, 800, 600),
            FakeScreen("B", 5000, 4000, 640, 480),
        ]
        plan = cover_plan(screens)
        self.assertEqual(len(plan), 2)
        self.assertEqual(plan[1]["x"], 5000)


if __name__ == "__main__":
    unittest.main()
