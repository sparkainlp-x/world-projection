"""Tests for world-projection v0.1.0.
Run: python3 -m unittest tests -v"""
import random
import unittest

from bubble import Bubble
from nervous import noisy, rand_field
from observer_world import WorldObserver
from projection import Projector, accuracy_on_accepted, fidelity
from world import World


def make_proj(seed=42):
    return Projector(Bubble(seed=seed), World())


class TestWorldProjection(unittest.TestCase):
    def test_withdraw_moves_world(self):
        proj = make_proj()
        sys = proj.bubble.system
        rec = proj.project(sys.patterns[0], f_hz=7.0, intended="withdraw")
        self.assertEqual(rec.response, "withdraw")
        self.assertEqual(rec.after["x"], -10.0)
        self.assertEqual(rec.after["step"], 1)

    def test_grasp_picks_near_object(self):
        proj = make_proj()
        sys = proj.bubble.system
        # Touch pattern is index 1, response grasp; object at (2,0),
        # world at (0,0), distance 2 <= 5, so grasp succeeds.
        rec = proj.project(sys.patterns[1], f_hz=7.0, intended="grasp")
        self.assertEqual(rec.response, "grasp")
        self.assertEqual(rec.after["held"], "stone")

    def test_balance_and_cool(self):
        proj = make_proj()
        sys = proj.bubble.system
        rec = proj.project(sys.patterns[2], f_hz=7.0, intended="balance")
        self.assertEqual(rec.after["stability"], 0.70)
        rec = proj.project(sys.patterns[3], f_hz=7.0, intended="cool-alert")
        self.assertEqual(rec.after["temperature"], 15.0)

    def test_reject_leaves_world_unchanged(self):
        proj = make_proj()
        rng = random.Random(99)
        unchanged = 0
        for _ in range(40):
            before = proj.world.state()
            rec = proj.project(rand_field(128, rng), f_hz=7.0, intended=None)
            if rec.decision == "reject":
                self.assertEqual(proj.world.state(), before)
                unchanged += 1
        self.assertGreaterEqual(unchanged, 35)

    def test_off_frequency_rejects(self):
        proj = make_proj()
        sys = proj.bubble.system
        rec = proj.project(sys.patterns[0], f_hz=0.25, intended="withdraw")
        self.assertEqual(rec.decision, "reject")
        self.assertEqual(rec.after["step"], 0)

    def test_observer_does_not_mutate_world(self):
        proj = make_proj()
        before = proj.world.state()
        obs = WorldObserver(sigma=0.05)
        obs.measure(proj.world)
        self.assertEqual(proj.world.state(), before)

    def test_fidelity_clean_high_noisy_lower(self):
        def fid(sigma):
            proj = make_proj()
            sys = proj.bubble.system
            rng = random.Random(99)
            probes = [noisy(sys.patterns[k % 4], sigma, rng) for k in range(40)]
            truths = [sys.RESPONSE_NAMES[k % 4] for k in range(40)]
            recs = proj.project_many(probes, truths, f_hz=7.0)
            return fidelity(recs)
        self.assertGreaterEqual(fid(0.15), 0.80)
        self.assertLess(fid(0.50), fid(0.15))

    def test_fidelity_counts_rejects_in_denominator(self):
        proj = make_proj()
        sys = proj.bubble.system
        rng = random.Random(99)
        probes = [noisy(sys.patterns[k % 4], 0.30, rng) for k in range(40)]
        truths = [sys.RESPONSE_NAMES[k % 4] for k in range(40)]
        recs = proj.project_many(probes, truths, f_hz=7.0)
        acc = accuracy_on_accepted(recs)
        f = fidelity(recs)
        self.assertLessEqual(f, acc if acc is not None else 1.0)

    def test_reproducible(self):
        def run_once():
            proj = make_proj()
            sys = proj.bubble.system
            rng = random.Random(99)
            probes = [noisy(sys.patterns[k % 4], 0.15, rng) for k in range(40)]
            truths = [sys.RESPONSE_NAMES[k % 4] for k in range(40)]
            return fidelity(proj.project_many(probes, truths, f_hz=7.0))
        self.assertEqual(run_once(), run_once())

    def test_unknown_response_rejected_by_world(self):
        w = World()
        with self.assertRaises(ValueError):
            w.apply("teleport")


if __name__ == "__main__":
    unittest.main()
