"""External observer: measures the bubble, never mutates it.

Every measurement is tagged REPORTED, never MEASURED, because the
observer sees a noisy report of the system, not the system itself.
Measuring must not change tau, patterns, gate decisions, or routing
times. The observer's own noise (sigma) is declared, and every
report carries a confidence half-width, so a calibrator can refuse
when the evidence is too thin or too noisy.

What the observer measures:
  routing: reflex, central, and lesion-reflex medians, with noise
  gate: overlap magnitudes for in-distribution and random probes
  frequency: accept rates at a list of frequencies, with noise
  injection: stock vs injected accepts and net scores, with truth
    used for scoring only, never for the decision (as in injection.py)
"""
import math
import random

from human import modulate
from nervous import noisy, rand_field


def half_width(values, z=1.96):
    if len(values) < 2:
        return math.inf
    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return z * math.sqrt(var / len(values))


class Report:
    def __init__(self, kind, value, half_width=math.inf, n=0, tag="REPORTED"):
        self.kind = kind
        self.value = value
        self.half_width = half_width
        self.n = n
        self.tag = tag

    def to_dict(self):
        return {"kind": self.kind, "value": self.value,
                "half_width": self.half_width, "n": self.n,
                "tag": self.tag}


class Observer:
    def __init__(self, bubble, sigma=0.05, seed=42):
        self.bubble = bubble
        self.sigma = sigma
        self.rng = random.Random(seed)
        self.reports = []

    def _noise(self):
        return self.rng.gauss(0, self.sigma)

    def measure_routing(self):
        true = self.bubble.routing()
        vals = {}
        for k, v in true.items():
            if math.isinf(v):
                vals[k] = math.inf
            else:
                vals[k] = v + self._noise()
        rep = Report("routing", vals, half_width=abs(self.sigma), n=1)
        self.reports.append(rep)
        return rep

    def measure_gate(self, n_in=40, n_ood=40, sigma_probe=0.15):
        sys = self.bubble.system
        rng = random.Random(99)
        in_vals = []
        for k in range(n_in):
            f = noisy(sys.patterns[k % 4], sigma_probe, rng)
            in_vals.append(sys.max_overlap(f) + self._noise())
        ood_vals = []
        for _ in range(n_ood):
            f = rand_field(128, rng)
            ood_vals.append(sys.max_overlap(f) + self._noise())
        rep = Report("gate", {"in": in_vals, "ood": ood_vals},
                     half_width=half_width(in_vals), n=n_in + n_ood)
        self.reports.append(rep)
        return rep

    def measure_frequency(self, frequencies=(0.25, 1.2, 7.0, 10.0),
                          n_per=40, sigma_probe=0.15):
        sys = self.bubble.system
        out = {}
        for f_hz in frequencies:
            rng = random.Random(99)
            ok = 0
            for k in range(n_per):
                probe = noisy(sys.patterns[k % 4], sigma_probe, rng)
                dec = self.bubble.decide_true(probe, f_hz)[0]
                if dec == "accept":
                    ok += 1
            out[f_hz] = ok / n_per
        rep = Report("frequency", out, half_width=0.10, n=len(frequencies) * n_per)
        self.reports.append(rep)
        return rep

    def measure_injection(self, n=40, sigma_probe=0.30, f_hz=7.0):
        sys = self.bubble.system
        inj = self.bubble.injection
        rng = random.Random(99)
        probes = [noisy(sys.patterns[k % 4], sigma_probe, rng)
                  for k in range(n)]
        stock = sum(1 for f in probes
                    if self.bubble.decide_true(f, f_hz)[0] == "accept")
        injected = 0
        nets = []
        for k, f in enumerate(probes):
            res = inj.attempt(f, f_hz, rng=random.Random(1000 + k), truth=1)
            if res.decision == "accept":
                injected += 1
            if res.net is not None:
                nets.append(res.net)
        rng2 = random.Random(99)
        rand_probes = [rand_field(128, rng2) for _ in range(n)]
        rand_injected = 0
        for k, f in enumerate(rand_probes):
            res = inj.attempt(f, f_hz, rng=random.Random(2000 + k), truth=0)
            if res.decision == "accept":
                rand_injected += 1
        val = {"stock": stock, "injected": injected, "n": n,
               "net_mean": (sum(nets) / len(nets)) if nets else None,
               "net_n": len(nets), "random_injected": rand_injected}
        rep = Report("injection", val, half_width=half_width(nets) if len(nets) > 1 else math.inf, n=n)
        self.reports.append(rep)
        return rep
