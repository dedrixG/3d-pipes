import os
import unittest
from pathlib import Path
from unittest.mock import patch

import platform_paths


class PlatformPathsTest(unittest.TestCase):
    def test_darwin_predicted_dirs(self):
        home = Path.home()
        with patch.object(platform_paths.sys, "platform", "darwin"):
            cfg = platform_paths.predicted_config_dir()
            state = platform_paths.predicted_state_dir()
        self.assertEqual(cfg, home / "Library" / "Preferences" / "dedrixG" / "3d-pipes")
        self.assertEqual(
            state,
            home / "Library" / "Application Support" / "dedrixG" / "3d-pipes",
        )

    def test_win32_predicted_dirs(self):
        with patch.object(platform_paths.sys, "platform", "win32"):
            with patch.dict(os.environ, {"LOCALAPPDATA": "/tmp/LocalAppData"}):
                cfg = platform_paths.predicted_config_dir()
                state = platform_paths.predicted_state_dir()
        self.assertEqual(cfg, Path("/tmp/LocalAppData") / "dedrixG" / "3d-pipes")
        self.assertEqual(state, Path("/tmp/LocalAppData") / "dedrixG" / "3d-pipes")

    def test_version(self):
        self.assertEqual(platform_paths.APP_VERSION, "0.3.0")


if __name__ == "__main__":
    unittest.main()
