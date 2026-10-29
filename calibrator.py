"""External calibrator: updates ASSUMED parameters only, or refuses.

Rules, fail-closed, in order:
 1. If any gate is missing (gate not calibrated, no review signoff,
    money gate failed), refuse. No partial calibration.
 2. If fewer than 3 reports exist, refuse: too little evidence.
 3. If any report half-width >= 0.20, refuse: too noisy.
 4. Otherwise, estimate from reports only, never from true params:
    - tau: midpoint of the taus maximising Youden's J on the
      reported in/ood overlap distributions (same method as the
      internal gate, applied to reported data).
    - frequency: the frequency with the highest reported accept rate.
    - injection: ON only if the reported net mean is positive AND
      its lower confidence bound is positive AND injected accepts
      exceed stock accepts; otherwise OFF, with the negative kept
      in the record, not tuned away.
Applying a calibration updates the bubble's ASSUMED model only.
The frozen true gate is never overwritten. After applying, the
caller must evaluate the shadow model on held-out probes (see
sweep.py / optimizer.py) before claiming any improvement.
"""
import math

from bubble import Bubble


class FailureCapsule:
    def __init__(self, reason, detail=None):
        self.reason = reason
        self.detail = detail or {}

    def to_dict(self):
        return {"refused": True, "reason": self.reason, "detail": self.detail}


def youden_tau(in_vals, ood_vals, grid=101):
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


class Calibrator:
    def __init__(self, bubble):
        self.bubble = bubble

    def _gate_check(self, reports):
        if not self.bubble.gates.get("gate_calibrated"):
            return FailureCapsule("gate_not_calibrated")
        if not self.bubble.gates.get("review_signoff"):
            return FailureCapsule("review_signoff_missing")
        if not self.bubble.gates.get("money_gates_pass"):
            return FailureCapsule("money_gates_failed")
        if len(reports) < 3:
            return FailureCapsule("too_few_reports", {"n": len(reports)})
        for r in reports:
            if r.half_width is not None and r.half_width >= 0.20:
                return FailureCapsule("half_width_too_wide",
                                      {"kind": r.kind, "half_width": r.half_width})
        return None

    def calibrate(self, reports):
        """Return (applied_dict, capsule_or_None)."""
        fail = self._gate_check(reports)
        if fail is not None:
            return None, fail
        out = {}
        gate_rep = next((r for r in reports if r.kind == "gate"), None)
        if gate_rep is not None:
            tau, j = youden_tau(gate_rep.value["in"], gate_rep.value["ood"])
            out["tau"] = tau
            out["tau_j"] = j
        freq_rep = next((r for r in reports if r.kind == "frequency"), None)
        if freq_rep is not None:
            best_f = max(freq_rep.value, key=lambda f: freq_rep.value[f])
            out["freq_hz"] = best_f
            out["freq_accept"] = freq_rep.value[best_f]
        inj_rep = next((r for r in reports if r.kind == "injection"), None)
        if inj_rep is not None:
            v = inj_rep.value
            net = v["net_mean"]
            lower = None if net is None else net - inj_rep.half_width
            on = (net is not None and lower is not None and lower > 0
                  and v["injected"] > v["stock"])
            out["injection_on"] = on
            out["injection_net_mean"] = net
            out["injection_net_lower"] = lower
            out["injection_stock"] = v["stock"]
            out["injection_injected"] = v["injected"]
        return out, None

    def apply(self, calibration):
        """Apply to assumed model only. Never touches the true gate."""
        if calibration is None:
            return False
        if "tau" in calibration:
            self.bubble.assumed_tau = calibration["tau"]
        if "freq_hz" in calibration:
            self.bubble.assumed_freq_hz = calibration["freq_hz"]
        if "injection_on" in calibration:
            self.bubble.assumed_p0 = 0.75 if calibration["injection_on"] else 0.50
        return True
