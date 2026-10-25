"""Changelog and README claims the release notes and install steps rely on."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DocsTests(unittest.TestCase):
    def test_single_changelog(self) -> None:
        names = sorted(path.name for path in ROOT.glob("CHANGELOG*.md"))
        self.assertEqual(names, ["CHANGELOG.md"])

    def test_release_excerpt_has_finished_line(self) -> None:
        excerpt = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "changelog-excerpt.py")],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("## [0.4.0]", excerpt.stdout)
        self.assertIn("finished screensaver", excerpt.stdout)

    def test_dnf_only_under_fedora_heading(self) -> None:
        lines = (ROOT / "README.md").read_text(encoding="utf-8").splitlines()
        inside = False
        level = 0
        seen = 0
        for line in lines:
            if line.startswith("#"):
                marks = len(line) - len(line.lstrip("#"))
                title = line[marks:].strip()
                if inside and marks <= level:
                    inside = False
                if "Fedora" in title:
                    inside = True
                    level = marks
            if "dnf install" in line:
                self.assertTrue(inside, line)
                seen += 1
        self.assertGreater(seen, 0)


if __name__ == "__main__":
    unittest.main()
