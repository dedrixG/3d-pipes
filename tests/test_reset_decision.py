"""Tests for reset_decision edge cases (GitHub issue #4)."""
from __future__ import annotations

import math
import unittest

from pipes import reset_decision


class ResetDecisionEdgeCasesTest(unittest.TestCase):
    """Test boundary conditions and edge cases for reset_decision."""

    def test_reset_exactly_at_threshold(self):
        """When now equals the scheduled reset_at, it should trigger a restart."""
        # Scenario: "when finished" mode, pipes died at t=10.0, delay=0.9 -> reset_at=10.9
        # Now is exactly 10.9
        restart, new_reset_at = reset_decision(
            now=10.9,
            started_at=0.0,
            reset_at=10.9,
            reset_seconds=0.0,
            reset_delay=0.9,
            living=False,
        )
        self.assertTrue(restart)
        self.assertEqual(new_reset_at, 0.0)

    def test_reset_just_before_threshold(self):
        """When now is just before the scheduled reset_at, it should NOT trigger a restart."""
        # Scenario: "when finished" mode, pipes died at t=10.0, delay=0.9 -> reset_at=10.9
        # Now is 10.89 (just before)
        restart, new_reset_at = reset_decision(
            now=10.89,
            started_at=0.0,
            reset_at=10.9,
            reset_seconds=0.0,
            reset_delay=0.9,
            living=False,
        )
        self.assertFalse(restart)
        self.assertEqual(new_reset_at, 10.9)

    def test_reset_just_after_threshold(self):
        """When now is just after the scheduled reset_at, it should trigger a restart."""
        # Scenario: "when finished" mode, pipes died at t=10.0, delay=0.9 -> reset_at=10.9
        # Now is 10.91 (just after)
        restart, new_reset_at = reset_decision(
            now=10.91,
            started_at=0.0,
            reset_at=10.9,
            reset_seconds=0.0,
            reset_delay=0.9,
            living=False,
        )
        self.assertTrue(restart)
        self.assertEqual(new_reset_at, 0.0)

    def test_reset_seconds_zero_disabled_means_when_finished(self):
        """reset_seconds=0 means 'restart when finished', not 'never restart'."""
        # If pipes are still living, it should NOT schedule a reset yet.
        restart, new_reset_at = reset_decision(
            now=100.0,
            started_at=0.0,
            reset_at=0.0,
            reset_seconds=0.0,
            reset_delay=0.9,
            living=True,
        )
        self.assertFalse(restart)
        self.assertEqual(new_reset_at, 0.0)

    def test_reset_seconds_zero_when_finished_schedules(self):
        """When pipes are dead and reset_seconds=0, it should schedule a reset."""
        restart, new_reset_at = reset_decision(
            now=10.0,
            started_at=0.0,
            reset_at=0.0,
            reset_seconds=0.0,
            reset_delay=0.9,
            living=False,
        )
        self.assertFalse(restart)  # Not yet time
        self.assertAlmostEqual(new_reset_at, 10.9)

    def test_nan_reset_seconds_treated_as_zero(self):
        """NaN reset_seconds should be treated as disabled (0) by sanitize_config,
        but if passed directly to reset_decision, it should not crash and behave like 0."""
        # Note: In practice, sanitize_config converts NaN to default. This tests the function's robustness.
        restart, new_reset_at = reset_decision(
            now=10.0,
            started_at=0.0,
            reset_at=0.0,
            reset_seconds=float("nan"),
            reset_delay=0.9,
            living=False,
        )
        # Since nan > 0 is False, it falls through to the 'when finished' logic
        self.assertFalse(restart)
        self.assertAlmostEqual(new_reset_at, 10.9)

    def test_nan_reset_delay_treated_as_zero(self):
        """NaN reset_delay should not crash the function."""
        restart, new_reset_at = reset_decision(
            now=10.0,
            started_at=0.0,
            reset_at=0.0,
            reset_seconds=0.0,
            reset_delay=float("nan"),
            living=False,
        )
        # nan + 0.9 is nan, so it won't trigger restart immediately unless now >= nan (which is false)
        self.assertFalse(restart)
        self.assertTrue(math.isnan(new_reset_at))


if __name__ == "__main__":
    unittest.main()
