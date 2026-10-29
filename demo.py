"""Demo for world-projection v0.1.0.
Run: python demo.py
Projection = bubble nervous decision -> world action, fail-closed
on reject. All numbers below are inside this toy only.
"""
import random

from bubble import Bubble
from nervous import noisy, rand_field
from observer_world import WorldObserver
from projection import Projector, accuracy_on_accepted, fidelity
from world import World


def run(bubble, sigma, f_hz, n=40, seed=99):
    sys = bubble.system
    rng = random.Random(seed)
    probes = [noisy(sys.patterns[k % 4], sigma, rng) for k in range(n)]
    truths = [sys.RESPONSE_NAMES[k % 4] for k in range(n)]
    proj = Projector(bubble, World())
    recs = proj.project_many(probes, truths, f_hz=f_hz)
    # Random fields must leave the world unchanged, probe by probe.
    rng2 = random.Random(seed + 7)
    rand_unchanged = 0
    for _ in range(n):
        before = proj.world.state()
        rec = proj.project(rand_field(128, rng2), f_hz=f_hz, intended=None)
        if not rec.changed:
            rand_unchanged += 1
    return recs, rand_unchanged, n


def main():
    print("world-projection v0.1.0 — nervous system -> bubble universe -> world")
    b = Bubble(seed=42)
    print(f"bubble: frozen tau = {b.true_tau:.3f}, J = {b.true_j:.3f}, 128 neurons, 4 responses")
    for sigma, f_hz, label in [
            (0.15, 7.0, "clean-ish, on-frequency"),
            (0.30, 7.0, "noisy, on-frequency"),
            (0.15, 0.25, "clean, off-frequency"),
            (0.50, 7.0, "very noisy, on-frequency")]:
        recs, rand_unchanged, rand_n = run(Bubble(seed=42), sigma, f_hz)
        s = WorldObserver.summarise(recs)
        print(f"{label} (sigma={sigma}, f={f_hz} Hz): fidelity = {s['fidelity']:.3f}, "
              f"accuracy-on-accepted = {s['accuracy_on_accepted']}, "
              f"accepted {s['accepted']}/{s['n']}, rejected-unchanged {s['rejected_unchanged']}/{s['rejected_total']}, "
              f"random-unchanged {rand_unchanged}/{rand_n}")
    # One trace per response, each from a fresh world, so the
    # projection is visible, not just a rate. A shared world would
    # make the second trace fail: withdraw moves x to -10, then the
    # object at (2,0) is 12 away, outside the grasp range of 5.
    for idx, intended in [(0, "withdraw"), (1, "grasp"), (2, "balance"), (3, "cool-alert")]:
        proj = Projector(Bubble(seed=42), World())
        sys = proj.bubble.system
        rec = proj.project(sys.patterns[idx], f_hz=7.0, intended=intended)
        print(f"trace clean {intended} -> {rec.response}, before={rec.before}, after={rec.after}")
    print("claim, stated exactly: projection is implemented and measurable "
          "inside this toy, with the fidelities above. It is NOT a proof "
          "that physical holographic projection is real, NOT optical "
          "holography, NOT neuroscience, NOT a medical device.")


if __name__ == "__main__":
    main()
