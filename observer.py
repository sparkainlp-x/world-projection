"""Synthetic observer harness for the bubble toy.

This is not an independent physical observer: it generates repeated noisy
reports from the package's own simulator. Its uncertainty summaries describe
only those synthetic draws. The calibrator receives report values, not hidden
parameters, but no real-world measurement or population inference is made.
"""
import math
import random

from nervous import noisy, rand_field


Z_95 = 1.96


def half_width(values, z=Z_95):
    """Normal-approximation 95% half-width for an independent sample mean."""
    if len(values) < 2:
        return math.inf
    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return z * math.sqrt(var / len(values))


def wilson(k, n, z=Z_95):
    """Wilson score interval for a Bernoulli rate; returns (p, lo, hi)."""
    if n <= 0 or not 0 <= k <= n:
        raise ValueError("Wilson interval requires 0 <= k <= n and n > 0")
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (p, max(0.0, centre - half), min(1.0, centre + half))


class Report:
    def __init__(self, kind, value, half_width=math.inf, n=0,
                 tag="REPORTED", intervals=None, details=None):
        self.kind = kind
        self.value = value
        self.half_width = half_width
        self.n = n
        self.tag = tag
        self.intervals = intervals or {}
        self.details = details or {}

    def to_dict(self):
        return {"kind": self.kind, "value": self.value,
                "half_width": self.half_width, "n": self.n,
                "tag": self.tag, "intervals": self.intervals,
                "details": self.details}


class Observer:
    """Generate deterministic synthetic reports from a Bubble instance."""

    def __init__(self, bubble, sigma=0.05, seed=42):
        if not math.isfinite(sigma) or sigma < 0:
            raise ValueError("sigma must be finite and >= 0")
        self.bubble = bubble
        self.sigma = sigma
        self.seed = seed
        self.reports = []

    def _rng(self, offset):
        return random.Random(self.seed + offset)

    def measure_routing(self, n_rep=40):
        if not isinstance(n_rep, int) or n_rep < 2:
            raise ValueError("n_rep must be an integer >= 2")
        truth = self.bubble.routing()
        rng = self._rng(101)
        values = {}
        intervals = {}
        widths = []
        for name, route in truth.items():
            if math.isinf(route):
                values[name] = math.inf
                intervals[name] = [math.inf, math.inf]
                continue
            samples = [route + rng.gauss(0, self.sigma) for _ in range(n_rep)]
            mean = sum(samples) / n_rep
            width = half_width(samples)
            values[name] = mean
            intervals[name] = [mean - width, mean + width]
            widths.append(width)
        rep = Report("routing", values,
                     half_width=max(widths) if widths else math.inf,
                     n=n_rep, intervals=intervals,
                     details={"replicates_per_finite_route": n_rep,
                              "seed": self.seed + 101,
                              "uncertainty": "synthetic repeated-noise means"})
        self.reports.append(rep)
        return rep

    def measure_gate(self, n_in=40, n_ood=40, sigma_probe=0.15):
        if not isinstance(n_in, int) or n_in < 2 or not isinstance(n_ood, int) or n_ood < 2:
            raise ValueError("n_in and n_ood must both be integers >= 2")
        if not math.isfinite(sigma_probe) or sigma_probe < 0:
            raise ValueError("sigma_probe must be finite and >= 0")
        sys = self.bubble.system
        rng = self._rng(201)
        in_vals = []
        for k in range(n_in):
            field = noisy(sys.patterns[k % 4], sigma_probe, rng)
            in_vals.append(min(1.0, max(0.0, sys.max_overlap(field)
                                        + rng.gauss(0, self.sigma))))
        ood_vals = []
        for _ in range(n_ood):
            field = rand_field(sys.n, rng)
            ood_vals.append(min(1.0, max(0.0, sys.max_overlap(field)
                                         + rng.gauss(0, self.sigma))))
        intervals = {
            "in_mean": [sum(in_vals) / n_in - half_width(in_vals),
                        sum(in_vals) / n_in + half_width(in_vals)],
            "ood_mean": [sum(ood_vals) / n_ood - half_width(ood_vals),
                         sum(ood_vals) / n_ood + half_width(ood_vals)],
        }
        rep = Report(
            "gate", {"in": in_vals, "ood": ood_vals},
            half_width=max(half_width(in_vals), half_width(ood_vals)),
            n=n_in + n_ood, intervals=intervals,
            details={"n_in": n_in, "n_ood": n_ood,
                     "sigma_probe": sigma_probe, "report_noise_sigma": self.sigma,
                     "seed": self.seed + 201,
                     "overlap_values_clipped_to": [0.0, 1.0]})
        self.reports.append(rep)
        return rep

    def measure_frequency(self, frequencies=(0.25, 1.2, 7.0, 10.0),
                          n_per=40, sigma_probe=0.15):
        frequencies = tuple(frequencies)
        if not frequencies or len(set(frequencies)) != len(frequencies):
            raise ValueError("frequencies must be non-empty and unique")
        if any(not math.isfinite(f) or f < 0 for f in frequencies):
            raise ValueError("frequencies must be finite and >= 0")
        if not isinstance(n_per, int) or n_per < 2:
            raise ValueError("n_per must be an integer >= 2")
        if not math.isfinite(sigma_probe) or sigma_probe < 0:
            raise ValueError("sigma_probe must be finite and >= 0")
        sys = self.bubble.system
        rng = self._rng(301)
        labels = [k % 4 for k in range(n_per)]
        rng.shuffle(labels)
        probes = [noisy(sys.patterns[label], sigma_probe, rng)
                  for label in labels]
        ood_rng = self._rng(302)
        random_fields = [rand_field(sys.n, ood_rng) for _ in range(n_per)]
        out = {"frequencies": list(frequencies), "in": {}, "ood": {},
               "youden_j": {}}
        intervals = {}
        for f_hz in frequencies:
            in_ok = sum(1 for probe in probes
                        if self.bubble.decide_true(probe, f_hz)[0] == "accept")
            ood_ok = sum(1 for field in random_fields
                         if self.bubble.decide_true(field, f_hz)[0] == "accept")
            in_rate, ood_rate = in_ok / n_per, ood_ok / n_per
            out["in"][f_hz] = in_rate
            out["ood"][f_hz] = ood_rate
            out["youden_j"][f_hz] = in_rate - ood_rate
            _p, in_lo, in_hi = wilson(in_ok, n_per)
            _p, ood_lo, ood_hi = wilson(ood_ok, n_per)
            intervals[str(f_hz)] = {
                "in": [in_lo, in_hi], "ood": [ood_lo, ood_hi]}
        max_width = max((hi - lo) / 2
                        for pair in intervals.values()
                        for lo, hi in pair.values())
        rep = Report("frequency", out, half_width=max_width,
                     n=2 * len(frequencies) * n_per, intervals=intervals,
                     details={"n_per_frequency": n_per,
                              "sigma_probe": sigma_probe,
                              "in_seed": self.seed + 301,
                              "ood_seed": self.seed + 302,
                              "same_probes_paired_across_frequencies": True,
                              "interval": "pointwise 95% Wilson; not simultaneous",
                              "selection_metric": "Youden's J = in acceptance - random-field acceptance"})
        self.reports.append(rep)
        return rep

    def measure_injection(self, n=40, sigma_probe=0.30, f_hz=7.0):
        if not isinstance(n, int) or n < 2:
            raise ValueError("n must be an integer >= 2")
        if not math.isfinite(sigma_probe) or sigma_probe < 0:
            raise ValueError("sigma_probe must be finite and >= 0")
        if not math.isfinite(f_hz) or f_hz < 0:
            raise ValueError("f_hz must be finite and >= 0")
        sys = self.bubble.system
        inj = self.bubble.injection
        in_rng = self._rng(401)
        labels = [k % 4 for k in range(n)]
        in_rng.shuffle(labels)
        probes = [noisy(sys.patterns[label], sigma_probe, in_rng)
                  for label in labels]
        stock_in = 0
        injected_in = 0
        in_nets = []
        for k, field in enumerate(probes):
            stock_in += int(self.bubble.decide_true(field, f_hz)[0] == "accept")
            result = inj.attempt(field, f_hz, rng=random.Random(self.seed + 1001 + k),
                                 truth=1)
            injected_in += int(result.decision == "accept")
            in_nets.append(result.net)

        ood_rng = self._rng(402)
        random_probes = [rand_field(sys.n, ood_rng) for _ in range(n)]
        stock_ood = 0
        injected_ood = 0
        ood_nets = []
        for k, field in enumerate(random_probes):
            stock_ood += int(self.bubble.decide_true(field, f_hz)[0] == "accept")
            result = inj.attempt(field, f_hz, rng=random.Random(self.seed + 2001 + k),
                                 truth=0)
            injected_ood += int(result.decision == "accept")
            ood_nets.append(result.net)

        all_nets = in_nets + ood_nets
        net_mean = sum(all_nets) / len(all_nets)
        net_width = half_width(all_nets)
        far = wilson(injected_ood, n)
        value = {
            "stock": stock_in, "injected": injected_in, "n": n,
            "paired_new_accepts": injected_in - stock_in,
            "injection_net_mean": sum(in_nets) / n,
            "injection_net_in_half_width": half_width(in_nets),
            "ood_net_mean": sum(ood_nets) / n,
            "ood_net_half_width": half_width(ood_nets),
            "net_mean": net_mean, "net_n": len(all_nets),
            "net_half_width": net_width,
            "random_stock": stock_ood, "random_injected": injected_ood,
            "random_n": n, "random_false_accept_rate": injected_ood / n,
            "random_injected_wilson": far,
            "net_scores": all_nets,
        }
        rep = Report("injection", value, half_width=net_width,
                     n=2 * n,
                     intervals={"random_false_accept_rate": [far[1], far[2]],
                                "net_mean": [net_mean - net_width,
                                             net_mean + net_width]},
                     details={"n_in": n, "n_ood": n,
                              "sigma_probe": sigma_probe, "f_hz": f_hz,
                              "in_seed": self.seed + 401,
                              "ood_seed": self.seed + 402,
                              "paired_stock_vs_injection": True,
                              "net_score": "Brier loss plus configured per-attempt cost"})
        self.reports.append(rep)
        return rep
