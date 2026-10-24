"""Tests for screensaver argument normalization helpers."""
from __future__ import annotations

import unittest

from pipes import _looks_like_hwnd, _scr_token, normalize_screensaver_argv


class ScrTokenTest(unittest.TestCase):
    def test_plain_flag(self):
        self.assertEqual(_scr_token("/s"), ("/s", None))
        self.assertEqual(_scr_token("-c"), ("-c", None))

    def test_attached_hwnd(self):
        self.assertEqual(_scr_token("/c:1234"), ("/c", "1234"))
        self.assertEqual(_scr_token("/p:0x1a2b"), ("/p", "0x1a2b"))

    def test_empty_body(self):
        self.assertEqual(_scr_token("/"), ("/", None))
        self.assertEqual(_scr_token("-"), ("-", None))

    def test_no_flag_char(self):
        self.assertEqual(_scr_token("s"), ("s", None))
        self.assertEqual(_scr_token(""), ("", None))


class LooksLikeHwndTest(unittest.TestCase):
    def test_valid_hwnds(self):
        self.assertTrue(_looks_like_hwnd("1234"))
        self.assertTrue(_looks_like_hwnd("0x1a2b"))
        self.assertTrue(_looks_like_hwnd("0"))

    def test_invalid_hwnds(self):
        self.assertFalse(_looks_like_hwnd("/c"))
        self.assertFalse(_looks_like_hwnd("-p"))
        self.assertFalse(_looks_like_hwnd("abc"))
        self.assertFalse(_looks_like_hwnd(""))


class NormalizeScreensaverArgvTest(unittest.TestCase):
    def test_s_flag(self):
        self.assertEqual(normalize_screensaver_argv(["/s"]), ["--fullscreen"])

    def test_c_with_attached_hwnd(self):
        self.assertEqual(normalize_screensaver_argv(["/c:123"]), ["--settings"])

    def test_p_with_separate_hwnd(self):
        self.assertEqual(normalize_screensaver_argv(["/p", "456"]), ["--preview", "456"])

    def test_macos_psn_stripped(self):
        self.assertEqual(normalize_screensaver_argv(["-psn_0_12345"]), [])

    def test_garbage_tokens_passthrough(self):
        self.assertEqual(normalize_screensaver_argv(["--unknown", "garbage"]), ["--unknown", "garbage"])

    def test_mixed_flags_and_garbage(self):
        result = normalize_screensaver_argv(["/s", "--verbose", "/c:99", "-psn_0_12345"])
        self.assertEqual(result, ["--fullscreen", "--verbose", "--settings"])


if __name__ == "__main__":
    unittest.main()
