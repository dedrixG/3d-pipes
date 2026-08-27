import unittest

from pipes import normalize_screensaver_argv, parse_args


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

    def test_parse_scr_flags(self):
        self.assertTrue(parse_args(["/s"]).fullscreen)
        self.assertTrue(parse_args(["/c"]).settings)
        self.assertTrue(parse_args(["/c", "12345"]).settings)
        self.assertTrue(parse_args(["/s", "0"]).fullscreen)
        self.assertEqual(parse_args(["/p", "100"]).preview, "100")
        self.assertTrue(parse_args(["--window"]).window)
        self.assertFalse(parse_args(["--window"]).settings)


if __name__ == "__main__":
    unittest.main()
