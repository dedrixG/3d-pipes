#!/usr/bin/env python3
"""Print the latest numbered CHANGELOG section (skips [Unreleased])."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
out: list[str] = []
started = False
for line in text.splitlines():
    if line.startswith("## ["):
        if "Unreleased" in line:
            continue
        if started:
            break
        started = True
    if started:
        out.append(line)
body = "\n".join(out).strip()
if not body:
    raise SystemExit("No version section found in CHANGELOG.md")
print(body)
print()
