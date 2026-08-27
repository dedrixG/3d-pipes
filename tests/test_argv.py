import unittest
from unittest.mock import patch

from pipes import make_surface_format, normalize_screensaver_argv, parse_args


class ArgvTest(unittest.TestCase):
    def test_passthrough(self):
        self.assertEqual(normalize_screensaver_argv(["--settings"]), ["--settings"])

    def test_version(self):
        with self.assertRaises(SystemExit) as ctx:
            parse_args(["--version"])
        self.assertEqual(ctx.exception.code, 0)

    def test_windows_fullscreen(self):
        self.assertEqual(normalize_screensaver_argv(["/s"]), ["--fullscreen"])
        self.assertEqual(normalize_screensaver_argv(["/S"]), ["--fullscreen"])

    def test_windows_configure(self):
        self.assertEqual(normalize_screensaver_argv(["/c"]), ["--settings"])
        self.assertEqual(normalize_screensaver_argv(["/c:1234"]), ["--settings"])
        self.assertEqual(normalize_screensaver_argv(["/c", "12345"]), ["--settings"])
        self.assertEqual(normalize_screensaver_argv(["/C", "0x1a2b"]), ["--settings"])

    def test_windows_preview(self):
        self.assertEqual(normalize_screensaver_argv(["/p", "42"]), ["--preview", "42"])
        self.assertEqual(normalize_screensaver_argv(["/p:99"]), ["--preview", "99"])
        self.assertEqual(normalize_screensaver_argv(["/l", "7"]), ["--preview", "7"])

    def test_windows_password_hwnd_dropped(self):
        self.assertEqual(normalize_screensaver_argv(["/a", "99"]), [])

    def test_macos_psn_stripped(self):
        self.assertEqual(normalize_screensaver_argv(["-psn_0_12345"]), [])
        self.assertEqual(
            normalize_screensaver_argv(["-psn_0_12345", "--settings"]),
            ["--settings"],
        )
        args = parse_args(["-psn_0_98765"])
        self.assertFalse(args.window)
        self.assertFalse(args.settings)
        self.assertIsNone(args.preview)
        self.assertTrue(parse_args(["-psn_0_98765", "--settings"]).settings)

    def test_parse_scr_flags(self):
        self.assertTrue(parse_args(["/s"]).fullscreen)
        self.assertTrue(parse_args(["/c"]).settings)
        self.assertTrue(parse_args(["/c", "12345"]).settings)
        self.assertTrue(parse_args(["/s", "0"]).fullscreen)
        self.assertEqual(parse_args(["/p", "100"]).preview, "100")
        self.assertTrue(parse_args(["--window"]).window)
        self.assertFalse(parse_args(["--window"]).settings)


class SurfaceFormatTest(unittest.TestCase):
    def test_macos_requests_41(self):
        with patch("pipes.sys.platform", "darwin"):
            fmt = make_surface_format(False)
        self.assertEqual(fmt.majorVersion(), 4)
        self.assertEqual(fmt.minorVersion(), 1)

    def test_other_os_requests_33(self):
        with patch("pipes.sys.platform", "linux"):
            fmt = make_surface_format(False)
        self.assertEqual(fmt.majorVersion(), 3)
        self.assertEqual(fmt.minorVersion(), 3)


if __name__ == "__main__":
    unittest.main()
