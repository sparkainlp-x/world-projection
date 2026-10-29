"""Calibrate only the bubble's ASSUMED synthetic model.

Calibration uses observer reports as a calibration split. It does not use the
later optimizer's held-out evaluation split. Threshold stability is assessed
with a deterministic bootstrap; frequency is selected by Youden's J over
in-distribution and random-field calibration probes. Injection remains an
informational recommendation and is not wired into the projection action path.
"""
import math
import random

from bubble import Bubble


MAX_REPORT_HALF_WIDTH = 0.20
MAX_TAU_BOOTSTRAP_HALF_WIDTH = 0.20
MAX_RANDOM_INJECTION_FAR_UPPER = 0.05


def _validate_scores(values, name):
    if not values:
        raise ValueError(f"{name} must be non-empty")
    if not all(math.isfinite(v) for v in values):
        raise ValueError(f"{name} must contain only finite values")


def youden_tau(in_vals, ood_vals, grid=101):
    if not isinstance(grid, int) or grid < 1:
        raise ValueError("grid must be a positive integer")
    _validate_scores(in_vals, "in_vals")
    _validate_scores(ood_vals, "ood_vals")
    best_j, best_taus = -2.0, []
    for step in range(grid + 1):
        tau = step / grid
        tpr = sum(1 for v in in_vals if v >= tau) / len(in_vals)
        fpr = sum(1 for v in ood_vals if v >= tau) / len(ood_vals)
        j = tpr - fpr
        if j > best_j + 1e-12:
            best_j, best_taus = j, [tau]
        elif abs(j - best_j) <= 1e-12:
            best_taus.append(tau)
    return (best_taus[0] + best_taus[-1]) / 2.0, best_j


def _quantile(values, q):
    values = sorted(values)
    if not values:
        raise ValueError("quantile requires at least one value")
    pos = (len(values) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return values[lo]
    return values[lo] + (values[hi] - values[lo]) * (pos - lo)


def bootstrap_tau_interval(in_vals, ood_vals, grid=101, repeats=500, seed=909):
    """Deterministic percentile bootstrap interval for the selected tau."""
    if repeats < 100:
        raise ValueError("use at least 100 bootstrap replicates")
    _validate_scores(in_vals, "in_vals")
    _validate_scores(ood_vals, "ood_vals")
    rng = random.Random(seed)
    taus = []
    for _ in range(repeats):
        in_sample = [in_vals[rng.randrange(len(in_vals))]
                     for _ in range(len(in_vals))]
        ood_sample = [ood_vals[rng.randrange(len(ood_vals))]
                      for _ in range(len(ood_vals))]
        tau, _ = youden_tau(in_sample, ood_sample, grid=grid)
        taus.append(tau)
    lower, upper = _quantile(taus, 0.025), _quantile(taus, 0.975)
    return {"lower": lower, "upper": upper,
            "half_width": (upper - lower) / 2.0,
            "repeats": repeats, "seed": seed,
            "method": "percentile bootstrap"}


class FailureCapsule:
    def __init__(self, reason, detail=None):
        self.reason = reason
        self.detail = detail or {}

    def to_dict(self):
        return {"refused": True, "reason": self.reason, "detail": self.detail}


class Calibrator:
    REQUIRED_KINDS = ("gate", "frequency", "injection")

    def __init__(self, bubble):
        self.bubble = bubble

    def _gate_check(self, reports):
        if not self.bubble.gates.get("gate_calibrated"):
            return FailureCapsule("gate_not_calibrated")
        if not self.bubble.gates.get("review_signoff"):
            return FailureCapsule("review_signoff_missing")
        if not self.bubble.gates.get("money_gates_pass"):
            return FailureCapsule("money_gates_failed")
        by_kind = {}
        for report in reports:
            if report.kind in self.REQUIRED_KINDS:
                if report.kind in by_kind:
                    return FailureCapsule("duplicate_report_kind",
                                          {"kind": report.kind})
                by_kind[report.kind] = report
        missing = [kind for kind in self.REQUIRED_KINDS if kind not in by_kind]
        if missing:
            return FailureCapsule("required_report_missing", {"kinds": missing})
        for kind, report in by_kind.items():
            if (report.half_width is None or not math.isfinite(report.half_width)
                    or report.half_width >= MAX_REPORT_HALF_WIDTH):
                return FailureCapsule("report_half_width_too_wide",
                                      {"kind": kind,
                                       "half_width": report.half_width})
        gate = by_kind["gate"].value
        if (not isinstance(gate, dict) or len(gate.get("in", [])) < 2
                or len(gate.get("ood", [])) < 2):
            return FailureCapsule("insufficient_gate_samples")
        try:
            _validate_scores(gate["in"], "gate in values")
            _validate_scores(gate["ood"], "gate ood values")
        except (KeyError, TypeError, ValueError) as error:
            return FailureCapsule("invalid_gate_report", {"error": str(error)})
        freq = by_kind["frequency"].value
        if (not isinstance(freq, dict) or not freq.get("frequencies")
                or not freq.get("in") or not freq.get("ood")):
            return FailureCapsule("invalid_frequency_report")
        if set(freq["frequencies"]) != set(freq["in"]) or set(freq["frequencies"]) != set(freq["ood"]):
            return FailureCapsule("frequency_report_keys_mismatch")
        for group in (freq["in"], freq["ood"]):
            if any(not math.isfinite(float(rate)) or not 0 <= rate <= 1
                   for rate in group.values()):
                return FailureCapsule("invalid_frequency_rate")
        inj = by_kind["injection"].value
        required_inj = ("net_mean", "net_half_width", "random_injected_wilson",
                        "paired_new_accepts")
        if not isinstance(inj, dict) or any(key not in inj for key in required_inj):
            return FailureCapsule("invalid_injection_report")
        if (not math.isfinite(inj["net_mean"])
                or not math.isfinite(inj["net_half_width"])
                or inj["net_half_width"] < 0):
            return FailureCapsule("invalid_injection_score")
        interval = inj["random_injected_wilson"]
        if (not isinstance(interval, (tuple, list)) or len(interval) != 3
                or not all(math.isfinite(x) for x in interval)):
            return FailureCapsule("invalid_injection_far_interval")
        return None

    def calibrate(self, reports):
        """Return a proposed calibration and refusal capsule, if any."""
        fail = self._gate_check(reports)
        if fail is not None:
            return None, fail
        by_kind = {r.kind: r for r in reports}
        gate = by_kind["gate"].value
        tau, j = youden_tau(gate["in"], gate["ood"])
        tau_ci = bootstrap_tau_interval(gate["in"], gate["ood"])
        if tau_ci["half_width"] >= MAX_TAU_BOOTSTRAP_HALF_WIDTH:
            return None, FailureCapsule("tau_selection_unstable", tau_ci)

        freq = by_kind["frequency"].value
        best_f = max(freq["frequencies"],
                     key=lambda f: (freq["youden_j"][f], -float(f)))
        inj = by_kind["injection"].value
        net_lower = inj["net_mean"] - inj["net_half_width"]
        far_upper = inj["random_injected_wilson"][2]
        injection_on = (
            net_lower > 0
            and far_upper <= MAX_RANDOM_INJECTION_FAR_UPPER
            and inj["paired_new_accepts"] > 0
        )
        out = {
            "tau": tau,
            "tau_j": j,
            "tau_bootstrap_interval": tau_ci,
            "freq_hz": best_f,
            "freq_j": freq["youden_j"][best_f],
            "freq_in_accept": freq["in"][best_f],
            "freq_random_false_accept": freq["ood"][best_f],
            "injection_on": injection_on,
            "injection_recommendation_only": True,
            "injection_net_mean": inj["net_mean"],
            "injection_net_lower": net_lower,
            "injection_random_far_upper": far_upper,
            "injection_stock_accepts": inj["stock"],
            "injection_injected_accepts": inj["injected"],
            "injection_random_accepts": inj["random_injected"],
        }
        return out, None

    def apply(self, calibration):
        """Apply tau/frequency to the assumed model; record injection advice."""
        if calibration is None:
            return False
        tau = calibration.get("tau")
        freq = calibration.get("freq_hz")
        if tau is not None and (not math.isfinite(tau) or not 0 <= tau <= 1):
            raise ValueError("assumed tau must be finite and in [0, 1]")
        if freq is not None and (not math.isfinite(freq) or freq < 0):
            raise ValueError("assumed frequency must be finite and >= 0")
        if "tau" in calibration:
            self.bubble.assumed_tau = tau
        if "freq_hz" in calibration:
            self.bubble.assumed_freq_hz = freq
        if "injection_on" in calibration:
            self.bubble.assumed_injection_recommendation = bool(
                calibration["injection_on"])
            self.bubble.assumed_p0 = 0.75 if calibration["injection_on"] else 0.50
        return True
