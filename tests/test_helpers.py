"""Tests for add_dir, dir_eq, and prefer_straight helpers."""
from __future__ import annotations

import random
import unittest

from pipes import add_dir, dir_eq, prefer_straight


class AddDirTest(unittest.TestCase):
    def test_add_positive(self):
        self.assertEqual(add_dir((0, 0, 0), (1, 0, 0)), (1, 0, 0))

    def test_add_negative(self):
        self.assertEqual(add_dir((1, 1, 1), (-1, -1, -1)), (0, 0, 0))

    def test_add_mixed(self):
        self.assertEqual(add_dir((5, 5, 5), (1, -1, 0)), (6, 4, 5))


class DirEqTest(unittest.TestCase):
    def test_equal_dirs(self):
        self.assertTrue(dir_eq((1, 0, 0), (1, 0, 0)))

    def test_different_dirs(self):
        self.assertFalse(dir_eq((1, 0, 0), (0, 1, 0)))

    def test_opposite_dirs(self):
        self.assertFalse(dir_eq((1, 0, 0), (-1, 0, 0)))


class PreferStraightTest(unittest.TestCase):
    def test_picks_straight_when_available(self):
        """When the incoming direction is in options, it should be preferred."""
        options = [(1, 0, 0), (0, 1, 0)]
        incoming = (1, 0, 0)
        # Run multiple times to account for randomness bias, but straight should be picked often.
        # Since STRAIGHT_BIAS is high (0.78), we expect it most of the time.
        results = [prefer_straight(options, incoming) for _ in range(100)]
        self.assertTrue(results.count((1, 0, 0)) > 50)

    def test_returns_from_options_when_no_straight(self):
        """When the incoming direction is not in options, it should return one of the options."""
        options = [(0, 1, 0), (0, -1, 0)]
        incoming = (1, 0, 0)
        result = prefer_straight(options, incoming)
        self.assertIn(result, options)

    def test_single_option(self):
        """When only one option is available, it should be returned."""
        options = [(0, 1, 0)]
        incoming = (1, 0, 0)
        result = prefer_straight(options, incoming)
        self.assertEqual(result, (0, 1, 0))


if __name__ == "__main__":
    unittest.main()
