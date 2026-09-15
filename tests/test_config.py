import random
import unittest

from PySide6.QtWidgets import QApplication

from pipes import (
    DEFAULTS,
    SEQUENTIAL_MAX_COLORS,
    SEQUENTIAL_MAX_SEGMENTS,
    PipesSim,
    reset_decision,
    sanitize_config,
)


def _qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


class SanitizeConfigTest(unittest.TestCase):
    def test_defaults_include_sequential(self):
        cfg = sanitize_config({})
        self.assertEqual(cfg["spawn_mode"], "sequential")
        self.assertEqual(cfg["spawn_mode"], DEFAULTS["spawn_mode"])

    def test_simultaneous_kept(self):
        cfg = sanitize_config({"spawn_mode": "simultaneous"})
        self.assertEqual(cfg["spawn_mode"], "simultaneous")

    def test_unknown_spawn_mode_falls_back(self):
        cfg = sanitize_config({"spawn_mode": "all-at-once"})
        self.assertEqual(cfg["spawn_mode"], "sequential")


class ResetDecisionTest(unittest.TestCase):
    def test_when_finished_schedules_then_restarts(self):
        restart, reset_at = reset_decision(
            now=10.0,
            started_at=0.0,
            reset_at=0.0,
            reset_seconds=0.0,
            reset_delay=0.9,
            living=False,
        )
        self.assertFalse(restart)
        self.assertAlmostEqual(reset_at, 10.9)
        restart, reset_at = reset_decision(
            now=10.9,
            started_at=0.0,
            reset_at=10.9,
            reset_seconds=0.0,
            reset_delay=0.9,
            living=False,
        )
        self.assertTrue(restart)

    def test_when_finished_does_not_reset_while_living(self):
        restart, reset_at = reset_decision(
            now=30.0,
            started_at=0.0,
            reset_at=0.0,
            reset_seconds=0.0,
            reset_delay=0.9,
            living=True,
        )
        self.assertFalse(restart)
        self.assertEqual(reset_at, 0.0)

    def test_timer_waits_even_if_pipes_already_finished(self):
        restart, reset_at = reset_decision(
            now=30.0,
            started_at=0.0,
            reset_at=0.0,
            reset_seconds=120.0,
            reset_delay=0.9,
            living=False,
        )
        self.assertFalse(restart)
        self.assertEqual(reset_at, 0.0)

    def test_timer_fires_at_interval(self):
        restart, _reset_at = reset_decision(
            now=120.0,
            started_at=0.0,
            reset_at=0.0,
            reset_seconds=120.0,
            reset_delay=0.9,
            living=True,
        )
        self.assertTrue(restart)


def _color_key(color):
    return (round(color.x(), 5), round(color.y(), 5), round(color.z(), 5))


def _grow_until_done(sim: PipesSim, max_steps: int = 20000) -> None:
    dt = 1.0 / sim.speed
    steps = 0
    while sim._scene_active() and steps < max_steps:
        for p in sim.pipes:
            p.update(dt)
        sim._maybe_spawn_next()
        steps += 1


class SpawnModeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = _qapp()

    def test_sequential_starts_one_pipe(self):
        sim = PipesSim({"pipe_count": 4, "spawn_mode": "sequential"})
        sim.restart()
        self.assertEqual(len(sim.pipes), 1)
        self.assertEqual(sim.pipes_remaining, 3)

    def test_simultaneous_starts_all_pipes(self):
        sim = PipesSim({"pipe_count": 4, "spawn_mode": "simultaneous"})
        sim.restart()
        self.assertEqual(len(sim.pipes), 4)
        self.assertEqual(sim.pipes_remaining, 0)

    def test_sequential_starts_next_after_current_finishes(self):
        sim = PipesSim({"pipe_count": 3, "spawn_mode": "sequential"})
        sim.restart()
        current = sim.pipes[0]
        current.alive = False
        current.growing = None
        sim._maybe_spawn_next()
        self.assertEqual(len(sim.pipes), 2)
        self.assertEqual(sim.pipes_remaining, 1)
        self.assertTrue(sim.pipes[-1].alive)

    def test_sequential_does_not_start_next_while_busy(self):
        sim = PipesSim({"pipe_count": 3, "spawn_mode": "sequential"})
        sim.restart()
        sim._maybe_spawn_next()
        self.assertEqual(len(sim.pipes), 1)
        self.assertEqual(sim.pipes_remaining, 2)

    def test_scene_stays_active_until_all_sequential_pipes_finish(self):
        sim = PipesSim({"pipe_count": 5, "spawn_mode": "sequential", "speed": 20.0})
        sim.restart()
        self.assertTrue(sim._scene_active())
        dt = 1.0 / sim.speed
        steps = 0
        while sim._scene_active() and steps < 20000:
            for p in sim.pipes:
                p.update(dt)
            sim._maybe_spawn_next()
            steps += 1
        self.assertFalse(sim._scene_active())
        self.assertEqual(sim.pipes_remaining, 0)
        self.assertEqual(len(sim.pipes), 5)
        restart, reset_at = reset_decision(
            now=100.0,
            started_at=0.0,
            reset_at=0.0,
            reset_seconds=0.0,
            reset_delay=sim.cfg["reset_delay"],
            living=sim._scene_active(),
        )
        self.assertFalse(restart)
        self.assertAlmostEqual(reset_at, 100.0 + sim.cfg["reset_delay"])

    def test_sequential_pipe_stops_at_256_segments(self):
        hit_cap = False
        for seed in range(8):
            random.seed(seed)
            sim = PipesSim({"pipe_count": 1, "spawn_mode": "sequential", "speed": 20.0})
            sim.restart()
            _grow_until_done(sim)
            self.assertEqual(len(sim.pipes), 1)
            self.assertLessEqual(sim.pipes[0].segments, SEQUENTIAL_MAX_SEGMENTS)
            if sim.pipes[0].segments == SEQUENTIAL_MAX_SEGMENTS:
                hit_cap = True
        self.assertTrue(hit_cap)

    def test_sequential_uses_at_most_five_colors(self):
        sim = PipesSim({"pipe_count": 8, "spawn_mode": "sequential", "speed": 20.0})
        sim.restart()
        _grow_until_done(sim)
        colors = {_color_key(p.color) for p in sim.pipes}
        self.assertLessEqual(len(colors), SEQUENTIAL_MAX_COLORS)
        self.assertEqual(len(sim.scene_palette), SEQUENTIAL_MAX_COLORS)
        for p in sim.pipes:
            self.assertLessEqual(p.segments, SEQUENTIAL_MAX_SEGMENTS)

    def test_sequential_five_pipes_get_distinct_colors(self):
        sim = PipesSim({"pipe_count": 5, "spawn_mode": "sequential"})
        sim.restart()
        for _ in range(4):
            sim.pipes[-1].alive = False
            sim.pipes[-1].growing = None
            sim._maybe_spawn_next()
        self.assertEqual(len(sim.pipes), 5)
        colors = [_color_key(p.color) for p in sim.pipes]
        self.assertEqual(len(set(colors)), 5)

    def test_simultaneous_has_no_segment_cap(self):
        sim = PipesSim({"pipe_count": 4, "spawn_mode": "simultaneous"})
        sim.restart()
        self.assertIsNone(sim.max_pipe_segments())
        self.assertEqual(len(sim.scene_palette), 10)


if __name__ == "__main__":
    unittest.main()
