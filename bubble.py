"""Bubble containing the package's synthetic toy system.

The Observer is a measurement-generation harness with simulator access,
not an independent or blinded observer. The Calibrator consumes its
REPORTED synthetic samples and updates only the assumed shadow model.
Neither operation mutates the true gate or stored patterns; rescued probes
are never stored. That non-intervention is tested.

Gates for calibration (fail-closed):
  gate_calibrated: the internal gate was calibrated once, tau frozen
  review_signoff: a boolean toy gate (the demo's automatic toggle is not
    human review or authorization)
  money_gates: no send/spend action is authorised by this package
  (there is no send/spend here at all; the gate exists so a future
  actuator cannot be added silently)
Calibration is refused unless all gates pass and the required report types
have sufficiently narrow synthetic uncertainty summaries. The frozen true
gate is never overwritten. The assumed model must be assessed on a separate
synthetic held-out split; this remains internal software evaluation, not
external validation.
"""
import random

from human import modulate
from injection import CrystallizeInjection
from nervous import MembraneNervous, noisy, rand_field


class Bubble:
    """Full nervous system in a bubble, with assumed vs true separation."""

    def __init__(self, seed=42, cal_seed=11):
        self.seed = seed
        self.system = MembraneNervous(seed=seed)
        # Calibrate the internal gate once, exactly as v0.1.0 did.
        rng = random.Random(cal_seed)
        in_p = [noisy(self.system.patterns[k % 4], 0.15, rng)
                for k in range(100)]
        ood_p = [rand_field(128, rng) for _ in range(100)]
        tau, j = self.system.calibrate(in_p, ood_p)
        self.true_tau = tau
        self.true_j = j
        self.injection = CrystallizeInjection(self.system)
        # Assumed model: what the outside world believes, before
        # any calibration. Deliberately wrong on frequency centre
        # and tau, so calibration has something measurable to fix.
        self.assumed_tau = 0.50
        self.assumed_freq_hz = 5.0
        self.assumed_p0 = 0.50
        self.assumed_injection_recommendation = False
        # Simulator ground truth used by internal evaluation. The observer
        # harness is a synthetic measurement generator with simulator access,
        # not an independent or blinded physical observer.
        self._true_freq_hz = 7.0
        self._true_p0 = 0.75
        self.gates = {
            "gate_calibrated": True,
            "review_signoff": False,
            "money_gates_pass": True,
        }

    def set_review_signoff(self, value=True):
        self.gates["review_signoff"] = bool(value)

    def public_state(self):
        """What the outside world may see: assumed model only."""
        return {
            "assumed_tau": self.assumed_tau,
            "assumed_freq_hz": self.assumed_freq_hz,
            "assumed_p0": self.assumed_p0,
            "assumed_injection_recommendation": self.assumed_injection_recommendation,
            "responses": list(self.system.RESPONSE_NAMES),
            "n_neurons": self.system.geometry.n,
            "n_patterns": len(self.system.patterns),
            "tau_frozen": True,
        }

    def routing(self):
        """True routing times, for the bubble's own demo/tests only."""
        pain = self.system.seed_ids[0]
        return {
            "reflex": self.system.reflex_time(pain),
            "central": self.system.central_time(pain),
            "lesion_reflex": self.system.lesion_reflex_time(pain),
        }

    def decide_true(self, field, f_hz):
        """Internal decision, frozen gate, frequency-modulated."""
        return self.system.decide(modulate(field, f_hz))

    def decide_shadow(self, field, f_hz=None, tau=None, freq_hz=None):
        """Shadow decision under the assumed model.

        Shadow does not touch the true gate: it recomputes overlaps
        on a field modulated at the assumed frequency, and accepts
        iff max overlap >= assumed tau. Winner name is unchanged.
        """
        tau = self.assumed_tau if tau is None else tau
        # An explicit frequency is useful for sweeps; otherwise use the
        # assumed calibration, so Calibrator.apply affects this path.
        if freq_hz is None:
            freq_hz = self.assumed_freq_hz if f_hz is None else f_hz
        mod = modulate(field, freq_hz)
        winner, probs = self.system.project(mod)
        if winner is None:
            return "reject", None, probs
        if self.system.max_overlap(mod) < tau:
            return "reject", None, probs
        return "accept", self.system.RESPONSE_NAMES[winner], probs
