"""Synthetic optimizer with explicit train / calibration / held-out splits.

Selection happens only on TRAIN. The frozen candidate must then pass
predeclared operating constraints on a separate CALIBRATION split. A
candidate that fails calibration is refused without touching TEST. TEST is
evaluated once after the candidate is locked. All inputs and outcomes are
synthetic; this is a reproducibility exercise, not external validation.

The search objective is end-to-end world success: a correct response that
actually changes the toy world divided by all probes. The separately reported
accepted-response accuracy excludes world state and is a classifier metric.
The frozen-gate comparison uses the simulator's known tau and is therefore an
oracle/frozen reference, not a deployable baseline.
"""
import math
import random

from bubble import Bubble
from nervous import noisy, rand_field
from world3x3 import World3x3


DEFAULT_SPLIT_SEEDS = {"train": 201, "calibration": 202, "test": 203}
DEFAULT_WORLD_SEEDS = {"train": 42, "calibration": 43, "test": 44}
FREQUENCIES = (0.25, 1.2, 7.0, 10.0)
MAX_FALSE_ACCEPT_UPPER = 0.05
MIN_ACCEPT_LOWER = 0.50


def wilson(k, n, z=1.96):
    """Wilson score interval for a Bernoulli rate; returns (p, lo, hi)."""
    if n <= 0 or not 0 <= k <= n:
        raise ValueError("Wilson interval requires 0 <= k <= n and n > 0")
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (p, max(0.0, centre - half), min(1.0, centre + half))


def make_split(system, n, sigma, seed):
    """Generate a balanced, independently shuffled synthetic split."""
    if not isinstance(n, int) or n <= 0:
        raise ValueError("split size must be a positive integer")
    if not math.isfinite(sigma) or sigma < 0:
        raise ValueError("sigma must be finite and >= 0")
    rng = random.Random(seed)
    labels = [i % len(system.RESPONSE_NAMES) for i in range(n)]
    rng.shuffle(labels)
    probes = [noisy(system.patterns[label], sigma, rng) for label in labels]
    random_fields = [rand_field(system.n, rng) for _ in range(n)]
    return {
        "seed": seed,
        "probes": probes,
        "labels": labels,
        "random_fields": random_fields,
    }


def shadow_fidelity(bubble, tau, f_hz, probes, truths, rand_fields,
                    world_seed=42):
    """Evaluate a fixed shadow model on one stateful trajectory.

    `accept_rate` and false-accept rate concern independent per-probe
    decisions. The end-to-end rate is a whole-trajectory outcome: world
    state makes successive outcomes dependent, so no per-probe binomial
    interval is attached to that metric.
    """
    if len(probes) != len(truths):
        raise ValueError("probes and truths must have equal lengths")
    if not probes:
        raise ValueError("at least one probe is required")
    if not rand_fields:
        raise ValueError("at least one random field is required")
    world = World3x3(seed=world_seed)
    correct_responses = 0
    successes = 0
    changed_actions = 0
    accepted = 0
    bubble_rejects = 0
    guard_rejects = 0
    breaker_refusals = 0
    no_ops = 0
    for field, truth in zip(probes, truths):
        decision, response, _ = bubble.decide_shadow(
            field, f_hz=f_hz, tau=tau, freq_hz=f_hz)
        if decision != "accept":
            bubble_rejects += 1
            continue
        accepted += 1
        response_correct = response == bubble.system.RESPONSE_NAMES[truth]
        correct_responses += int(response_correct)
        changed = world.apply(response)
        if changed:
            changed_actions += 1
        elif world.last_refusal == "guard":
            guard_rejects += 1
        elif world.last_refusal == "breaker":
            breaker_refusals += 1
        elif world.last_refusal == "no_op":
            no_ops += 1
        if changed and response_correct:
            successes += 1

    false_accepts = sum(
        1 for field in rand_fields
        if bubble.decide_shadow(field, f_hz=f_hz, tau=tau,
                                freq_hz=f_hz)[0] == "accept"
    )
    n = len(probes)
    n_random = len(rand_fields)
    end_to_end = successes / n
    return {
        "tau": tau,
        "f_hz": f_hz,
        "n": n,
        "correct_response_count": correct_responses,
        "end_to_end_success_count": successes,
        "end_to_end_success_rate": end_to_end,
        # Compatibility key; defined identically to the explicit name above.
        "fidelity": end_to_end,
        "changed_action_rate": changed_actions / n,
        "bubble_accepts": accepted,
        "accept_rate": accepted / n,
        "accept_rate_wilson": wilson(accepted, n),
        "response_accuracy_on_accepted": (
            correct_responses / accepted if accepted else None),
        "bubble_rejects": bubble_rejects,
        "world_guard_rejects": guard_rejects,
        "breaker_refusals": breaker_refusals,
        "no_ops": no_ops,
        "random_fields_n": n_random,
        "false_accepts": false_accepts,
        "false_accept_rate": false_accepts / n_random,
        "false_accept_rate_wilson": wilson(false_accepts, n_random),
        "final_world": world.state(),
    }


def _constraints_pass(metrics):
    return (
        metrics["false_accept_rate_wilson"][2] <= MAX_FALSE_ACCEPT_UPPER
        and metrics["accept_rate_wilson"][1] >= MIN_ACCEPT_LOWER
    )


def optimise(bubble, sigma=0.15, n_train=100, n_calibration=100,
             n_test=100, split_seeds=None, world_seeds=None):
    """Select on TRAIN, qualify once on CALIBRATION, evaluate once on TEST."""
    if not math.isfinite(sigma) or sigma < 0:
        raise ValueError("sigma must be finite and >= 0")
    seeds = dict(DEFAULT_SPLIT_SEEDS if split_seeds is None else split_seeds)
    if set(seeds) != {"train", "calibration", "test"}:
        raise ValueError("split_seeds must define train, calibration, and test")
    if len(set(seeds.values())) != 3:
        raise ValueError("train, calibration, and test seeds must be distinct")
    worlds = dict(DEFAULT_WORLD_SEEDS if world_seeds is None else world_seeds)
    if set(worlds) != {"train", "calibration", "test"}:
        raise ValueError("world_seeds must define train, calibration, and test")
    if len(set(worlds.values())) != 3:
        raise ValueError("train, calibration, and test world seeds must be distinct")
    train = make_split(bubble.system, n_train, sigma, seeds["train"])
    calibration = make_split(bubble.system, n_calibration, sigma,
                             seeds["calibration"])
    test = make_split(bubble.system, n_test, sigma, seeds["test"])

    best = None
    for tau_i in range(101):
        tau = tau_i / 100.0
        for f_hz in FREQUENCIES:
            ev = shadow_fidelity(
                bubble, tau, f_hz, train["probes"], train["labels"],
                train["random_fields"], world_seed=worlds["train"])
            # Use train estimates only for selection; the independent
            # calibration split below is the operating-point qualification.
            if ev["false_accept_rate"] > MAX_FALSE_ACCEPT_UPPER:
                continue
            if ev["accept_rate"] < MIN_ACCEPT_LOWER:
                continue
            if best is None or ev["end_to_end_success_rate"] > best["end_to_end_success_rate"]:
                best = ev
    if best is None:
        return {
            "refused": True,
            "reason": "no_train_grid_point_meets_constraints",
            "split_seeds": seeds,
            "world_seeds": worlds,
            "split_sizes": {"train": n_train,
                            "calibration": n_calibration, "test": n_test},
            "selection_constraints": {
                "train_false_accept_rate_max": MAX_FALSE_ACCEPT_UPPER,
                "train_accept_rate_min": MIN_ACCEPT_LOWER,
            },
        }

    cal_ev = shadow_fidelity(
        bubble, best["tau"], best["f_hz"], calibration["probes"],
        calibration["labels"], calibration["random_fields"],
        world_seed=worlds["calibration"])
    cal_pass = _constraints_pass(cal_ev)
    calibration_record = {
        "locked_candidate": {"tau": best["tau"], "f_hz": best["f_hz"]},
        "metrics": cal_ev,
        "constraints_pass": cal_pass,
        "constraints": {
            "false_accept_rate_wilson_upper_max": MAX_FALSE_ACCEPT_UPPER,
            "accept_rate_wilson_lower_min": MIN_ACCEPT_LOWER,
        },
        "used_for_selection": False,
    }
    if not cal_pass:
        return {
            "refused": True,
            "reason": "locked_train_candidate_failed_calibration_constraints",
            "split_seeds": seeds,
            "world_seeds": worlds,
            "split_sizes": {"train": n_train,
                            "calibration": n_calibration, "test": n_test},
            "train_best": best,
            "calibration": calibration_record,
            "test_evaluated": False,
        }

    # Candidate is locked before the held-out set is evaluated.
    test_ev = shadow_fidelity(
        bubble, best["tau"], best["f_hz"], test["probes"], test["labels"],
        test["random_fields"], world_seed=worlds["test"])
    frozen = shadow_fidelity(
        bubble, bubble.true_tau, 7.0, test["probes"], test["labels"],
        test["random_fields"], world_seed=worlds["test"])
    return {
        "refused": False,
        "split_seeds": seeds,
        "world_seeds": worlds,
        "split_sizes": {"train": n_train,
                        "calibration": n_calibration, "test": n_test},
        "selection_constraints": {
            "train_false_accept_rate_max": MAX_FALSE_ACCEPT_UPPER,
            "train_accept_rate_min": MIN_ACCEPT_LOWER,
        },
        "calibration": calibration_record,
        "train_best": best,
        "test": {**test_ev, "candidate_locked_before_evaluation": True},
        "frozen_oracle_reference_test": frozen,
        "improvement_test": (test_ev["end_to_end_success_rate"]
                             - frozen["end_to_end_success_rate"]),
        "test_uncertainty_note": (
            "Wilson intervals apply only to per-probe accept/FAR rates; "
            "end-to-end success is one stateful trajectory and has no "
            "binomial confidence interval."),
    }
