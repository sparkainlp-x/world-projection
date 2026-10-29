"""Bubble holding the full membrane-nervous-system, unchanged inside.

The bubble is a boundary, not a new nervous system. Inside it lives
a MembraneNervous (vendored nervous.py, v0.2.0), its human frequency
layer (human.py), and its Crystallize injection (injection.py), all
unchanged. Outside it live only an Observer (observer.py) and a
Calibrator (calibrator.py), which see REPORTED measurements, never
the true internal state directly. Measuring does not mutate the
system: tau stays frozen, patterns stay 4, rescued probes are never
stored. That non-intervention is tested, not asserted.

Gates for calibration (fail-closed):
  gate_calibrated: the internal gate was calibrated once, tau frozen
  review_signoff: a human review has signed off on a calibration
  money_gates: no send/spend action is authorised by this package
  (there is no send/spend here at all; the gate exists so a future
  actuator cannot be added silently)
Calibration may be APPLIED to the assumed model only when all gates
pass AND at least 3 observer reports exist AND the confidence
half-width is < 0.20. Otherwise it is refused, with a failure
capsule. The frozen true gate is never overwritten by calibration;
calibration produces a shadow assumed model, evaluated side by side
with the frozen gate, so the scientific comparison is honest.
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
        # True parameters, for the package's own tests only. The
        # observer and calibrator never read these; they read reports.
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

    def decide_shadow(self, field, f_hz, tau=None, freq_hz=None):
        """Shadow decision under the assumed model.

        Shadow does not touch the true gate: it recomputes overlaps
        on a field modulated at the assumed frequency, and accepts
        iff max overlap >= assumed tau. Winner name is unchanged.
        """
        tau = self.assumed_tau if tau is None else tau
        # f_hz is the frequency to evaluate; freq_hz overrides it only
        # when explicitly given. The old default (assumed frequency)
        # made a frequency grid silently evaluate one frequency only.
        freq_hz = f_hz if freq_hz is None else freq_hz
        mod = modulate(field, freq_hz)
        winner, probs = self.system.project(mod)
        if winner is None:
            return "reject", None, probs
        if self.system.max_overlap(mod) < tau:
            return "reject", None, probs
        return "accept", self.system.RESPONSE_NAMES[winner], probs
