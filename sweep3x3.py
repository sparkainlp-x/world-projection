"""Seeded synthetic evaluation of the 3x3 projection toy.

Each cell is one stateful world trajectory. Probe labels are balanced and
shuffled, while the same probe draws are reused across frequency conditions
within a seed/sigma pair (paired comparison). The per-seed range is descriptive;
three trajectories are not enough for a population confidence interval.
"""
import random

from bubble import Bubble
from nervous import noisy, rand_field
from projection3x3 import Projector3x3
from world3x3 import World3x3


def wilson(k, n, z=1.96):
    """Wilson score interval for per-probe Bernoulli decision rates only."""
    if n <= 0 or not 0 <= k <= n:
        raise ValueError("Wilson interval requires 0 <= k <= n and n > 0")
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return (p, max(0.0, centre - half), min(1.0, centre + half))


def run_cell(seed, sigma, f_hz, n=40):
    if not isinstance(n, int) or n <= 0:
        raise ValueError("n must be a positive integer")
    proj = Projector3x3(Bubble(seed=seed), World3x3(seed=seed))
    sys = proj.bubble.system
    # Same independently seeded probe/label sequence across frequency cells
    # for a given geometry seed and sigma, enabling paired comparisons.
    rng = random.Random(10_000 + seed)
    labels = [i % len(sys.RESPONSE_NAMES) for i in range(n)]
    rng.shuffle(labels)
    probes = [noisy(sys.patterns[label], sigma, rng) for label in labels]
    truths = [sys.RESPONSE_NAMES[label] for label in labels]
    recs = proj.project_many(probes, truths, f_hz=f_hz)
    accepted = [r for r in recs if r.decision == "accept"]
    response_correct = sum(1 for r in accepted if r.response == r.intended)
    end_to_end_success = sum(1 for r in recs if r.correct)
    w = proj.world.state()
    return {
        "seed": seed, "sigma": sigma, "f_hz": f_hz, "n": n,
        "end_to_end_success_count": end_to_end_success,
        "end_to_end_success_rate": end_to_end_success / n,
        # Compatibility key, explicitly defined as task success / all probes.
        "fidelity": end_to_end_success / n,
        "bubble_accepts": len(accepted),
        "bubble_accept_rate": len(accepted) / n,
        "bubble_accept_rate_wilson": wilson(len(accepted), n),
        "response_correct_on_accepts": response_correct,
        "response_accuracy_on_accepted": (
            response_correct / len(accepted) if accepted else None),
        "bubble_rejects": sum(1 for r in recs if r.refusal == "bubble"),
        "world_guard_rejects": sum(1 for r in recs if r.refusal == "world_guard"),
        "breaker_refusals": sum(1 for r in recs if r.refusal == "breaker"),
        "grasp_no_ops": sum(1 for r in recs if r.refusal == "no_op"),
        "changed_actions": sum(1 for r in recs if r.changed),
        "breaker_open": w["breaker_open"],
        "held": w["held"],
        "max_residual": w["max_residual"],
    }


def full_sweep(seeds=(42, 7, 123), sigmas=(0.0, 0.15, 0.30, 0.50),
               frequencies=(0.25, 1.2, 7.0, 10.0), n=40):
    cells = []
    for seed in seeds:
        for sigma in sigmas:
            for f_hz in frequencies:
                cells.append(run_cell(seed, sigma, f_hz, n=n))
    summary = {}
    for label, sigma, f_hz in [
        ("clean_0.15_7Hz", 0.15, 7.0),
        ("noisy_0.30_7Hz", 0.30, 7.0),
        ("off_0.15_0.25Hz", 0.15, 0.25),
        ("very_noisy_0.50_7Hz", 0.50, 7.0),
    ]:
        selected = [c for c in cells
                    if c["sigma"] == sigma and c["f_hz"] == f_hz]
        if not selected:
            continue
        rates = [c["end_to_end_success_rate"] for c in selected]
        summary[label] = {
            "n_seeded_trajectories": len(selected),
            "trajectory_success_mean": sum(rates) / len(rates),
            "trajectory_success_range": (min(rates), max(rates)),
            "breaker_rate_across_trajectories": (
                sum(1 for c in selected if c["breaker_open"]) / len(selected)),
            "world_guard_rejects_mean_per_trajectory": (
                sum(c["world_guard_rejects"] for c in selected) / len(selected)),
            "breaker_refusals_mean_per_trajectory": (
                sum(c["breaker_refusals"] for c in selected) / len(selected)),
            "grasp_no_ops_mean_per_trajectory": (
                sum(c["grasp_no_ops"] for c in selected) / len(selected)),
        }
    return {
        "seeds": list(seeds), "sigmas": list(sigmas),
        "frequencies": list(frequencies), "n_per_trajectory": n,
        "summary_uncertainty_note": (
            "Mean and range summarize the listed seeded trajectories only; "
            "no inferential confidence interval is claimed."),
        "cells": cells, "summary": summary,
    }
