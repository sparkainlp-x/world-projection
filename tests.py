"""Tests for world-projection-3x3 v0.2.0 review candidate.

Run: python3 -m unittest tests -v
"""
import math
import random
import unittest

from bubble import Bubble
from calibrator import Calibrator, youden_tau
from human import sensitivity
from injection import CrystallizeInjection
from nervous import MembraneNervous, normalize, noisy, overlap, rand_field
from observer import Observer
from projection3x3 import Projector3x3, fidelity
from world3x3 import World3x3


def make_proj(seed=42):
    return Projector3x3(Bubble(seed=seed), World3x3(seed=seed))


class TestWorld3x3(unittest.TestCase):
    def test_grid_shape_and_start(self):
        world = World3x3(seed=42)
        self.assertEqual(world.agent, (1, 1))
        self.assertEqual(world.stone_at, (1, 0))
        self.assertIsNone(world.held)
        self.assertFalse(world.breaker_open)

    def test_withdraw_moves_west(self):
        proj = make_proj()
        sys = proj.bubble.system
        record = proj.project(sys.patterns[0], f_hz=7.0, intended="withdraw")
        self.assertTrue(record.changed)
        self.assertEqual(proj.world.agent, (1, 0))

    def test_grasp_picks_when_agent_is_on_stone(self):
        proj = make_proj()
        sys = proj.bubble.system
        proj.world.agent = (1, 0)
        record = proj.project(sys.patterns[1], f_hz=7.0, intended="grasp")
        self.assertTrue(record.changed)
        self.assertEqual(proj.world.held, "stone")

    def test_balance_twice_passes_third_guard_rejects(self):
        world = World3x3(seed=42)
        self.assertTrue(world.apply("balance"))
        self.assertTrue(world.apply("balance"))
        self.assertFalse(world.apply("balance"))
        self.assertEqual(world.accepted, 2)
        self.assertEqual(world.rejected, 1)

    def test_breaker_latches_after_five_consecutive_guard_rejections(self):
        world = World3x3(seed=42)
        world.apply("balance")
        world.apply("balance")
        for _ in range(5):
            self.assertFalse(world.apply("balance"))
        self.assertTrue(world.breaker_open)
        self.assertEqual(world.rejected, 5)
        self.assertFalse(world.apply("withdraw"))
        self.assertEqual(world.last_refusal, "breaker")

    def test_bubble_reject_leaves_world_unchanged(self):
        proj = make_proj()
        rng = random.Random(99)
        for _ in range(40):
            before = proj.world.state()
            record = proj.project(rand_field(128, rng), f_hz=7.0)
            if record.refusal == "bubble":
                self.assertEqual(proj.world.state(), before)
                self.assertFalse(record.changed)

    def test_grasp_no_op_is_not_accepted(self):
        proj = make_proj()
        sys = proj.bubble.system
        record = proj.project(sys.patterns[1], f_hz=7.0, intended="grasp")
        self.assertFalse(record.changed)
        self.assertEqual(record.refusal, "no_op")
        self.assertIsNone(proj.world.held)

    def test_known_clean_demo_outcome_is_exact(self):
        proj = make_proj()
        sys = proj.bubble.system
        rng = random.Random(99)
        probes = [noisy(sys.patterns[k % 4], 0.15, rng) for k in range(40)]
        truths = [sys.RESPONSE_NAMES[k % 4] for k in range(40)]
        records = proj.project_many(probes, truths, f_hz=7.0)
        self.assertEqual(sum(r.decision == "accept" for r in records), 40)
        self.assertEqual(sum(r.changed for r in records), 31)
        self.assertEqual(sum(r.correct for r in records), 31)
        self.assertAlmostEqual(fidelity(records), 0.775, places=12)

    def test_project_many_rejects_misaligned_truths(self):
        proj = make_proj()
        with self.assertRaises(ValueError):
            proj.project_many([proj.bubble.system.patterns[0]], [])

    def test_seeded_route_metrics_are_stage_constrained(self):
        for seed in (0, 1, 7, 42, 123):
            bubble = Bubble(seed=seed)
            source = bubble.system.seed_ids[0]
            reflex = bubble.system.reflex_time(source)
            central = bubble.system.central_time(source)
            lesion = bubble.system.lesion_reflex_time(source)
            self.assertTrue(math.isfinite(reflex))
            self.assertTrue(math.isfinite(central))
            self.assertGreaterEqual(central, reflex)
            self.assertTrue(math.isinf(lesion))


class TestNumericalValidation(unittest.TestCase):
    def test_nonfinite_values_rejected(self):
        with self.assertRaises(ValueError):
            normalize([complex(float("nan"), 0.0)])
        with self.assertRaises(ValueError):
            sensitivity(float("nan"))
        with self.assertRaises(ValueError):
            sensitivity(float("inf"))
        with self.assertRaises(ValueError):
            noisy([1 + 0j], -0.1, random.Random(1))

    def test_dimension_and_empty_calibration_rejected(self):
        with self.assertRaises(ValueError):
            overlap([1 + 0j], [1 + 0j, 0j])
        system = MembraneNervous(seed=42)
        with self.assertRaises(ValueError):
            system.calibrate([], [system.patterns[0]])
        with self.assertRaises(ValueError):
            system.calibrate([system.patterns[0]], [system.patterns[1]], grid=0)
        with self.assertRaises(ValueError):
            youden_tau([], [0.1])

    def test_injection_requires_positive_sample_count(self):
        system = MembraneNervous(seed=42)
        system.calibrate([system.patterns[0]], [rand_field(128, random.Random(2))])
        with self.assertRaises(ValueError):
            CrystallizeInjection(system, n_samples=0)

    def test_stock_accepted_injection_probe_is_scored(self):
        bubble = Bubble(seed=42)
        result = bubble.injection.attempt(
            bubble.system.patterns[0], 7.0, truth=1)
        self.assertEqual(result.attempts, 0)
        self.assertIsNotNone(result.brier)
        self.assertIsNotNone(result.net)


class TestSyntheticEvaluation(unittest.TestCase):
    def test_sweep_is_reproducible_and_summary_is_seed_range(self):
        from sweep3x3 import run_cell, full_sweep
        first = run_cell(42, 0.15, 7.0, n=40)
        second = run_cell(42, 0.15, 7.0, n=40)
        self.assertEqual(first, second)
        self.assertIn("breaker_refusals", first)
        sweep = full_sweep(seeds=(42, 7), sigmas=(0.15,),
                           frequencies=(7.0,), n=40)
        summary = sweep["summary"]["clean_0.15_7Hz"]
        self.assertLessEqual(summary["trajectory_success_range"][0],
                             summary["trajectory_success_mean"])
        self.assertLessEqual(summary["trajectory_success_mean"],
                             summary["trajectory_success_range"][1])
        self.assertIn("no inferential confidence interval", 
                      sweep["summary_uncertainty_note"])

    def test_optimizer_uses_three_distinct_splits_and_locks_test(self):
        from optimizer3x3 import make_split, optimise
        bubble = Bubble(seed=42)
        train = make_split(bubble.system, 40, 0.15, 201)
        calibration = make_split(bubble.system, 40, 0.15, 202)
        test = make_split(bubble.system, 40, 0.15, 203)
        self.assertNotEqual(train["probes"], calibration["probes"])
        self.assertNotEqual(calibration["probes"], test["probes"])
        result = optimise(bubble, n_train=40, n_calibration=40, n_test=40)
        self.assertEqual(result["split_seeds"],
                         {"train": 201, "calibration": 202, "test": 203})
        self.assertEqual(result["world_seeds"],
                         {"train": 42, "calibration": 43, "test": 44})
        if result["refused"]:
            self.assertFalse(result.get("test_evaluated", False))
        else:
            self.assertTrue(result["calibration"]["constraints_pass"])
            self.assertTrue(result["test"]["candidate_locked_before_evaluation"])
            self.assertIn("false_accept_rate_wilson", result["test"])
            self.assertNotIn("fidelity_wilson", result["test"])

    def test_calibrator_requires_useful_report_kinds_and_keeps_true_tau(self):
        bubble = Bubble(seed=42)
        observer = Observer(bubble, sigma=0.05, seed=42)
        observer.measure_routing(n_rep=20)
        observer.measure_gate(n_in=100, n_ood=100)
        observer.measure_frequency(n_per=100)
        observer.measure_injection(n=100)
        bubble.set_review_signoff(True)
        calibrator = Calibrator(bubble)
        before_true_tau = bubble.system.tau
        incomplete, failure = calibrator.calibrate(observer.reports[:2])
        self.assertIsNone(incomplete)
        self.assertEqual(failure.reason, "required_report_missing")
        result, failure = calibrator.calibrate(observer.reports)
        self.assertIsNone(failure, failure.to_dict() if failure else None)
        self.assertIn("tau_bootstrap_interval", result)
        self.assertIn("injection_recommendation_only", result)
        self.assertEqual(bubble.system.tau, before_true_tau)
        self.assertEqual(result["freq_hz"], 7.0)
        self.assertTrue(calibrator.apply(result))
        self.assertEqual(bubble.assumed_tau, result["tau"])
        self.assertEqual(bubble.assumed_freq_hz, result["freq_hz"])
        self.assertEqual(bubble.system.tau, before_true_tau)

    def test_shadow_defaults_use_applied_assumed_parameters(self):
        bubble = Bubble(seed=42)
        probe = bubble.system.patterns[0]
        bubble.assumed_tau = 0.10
        bubble.assumed_freq_hz = 7.0
        initial = bubble.decide_shadow(probe)
        bubble.assumed_tau = 0.50
        bubble.assumed_freq_hz = 0.25
        changed = bubble.decide_shadow(probe)
        self.assertNotEqual(initial[0], changed[0])

    def test_passport_seal_and_synthetic_headline_rule(self):
        from passport3x3 import headline_allowed, seal
        import pathlib
        files = [str(p) for p in pathlib.Path(".").glob("*.py")]
        self.assertNotEqual(seal({"success": 0.775}, files),
                            seal({"success": 0.776}, files))
        self.assertFalse(headline_allowed("synthetic", 1.0))


if __name__ == "__main__":
    unittest.main()
