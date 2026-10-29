"""Projection: nervous system -> bubble universe -> world.

Definition, fixed in PREREG, and the only definition this package
uses for "projection":
  1. A probe field is presented to the bubble's nervous system.
  2. The bubble decides, with its frozen gate, at a given frequency:
     accept with a response name, or reject.
  3. On accept, the world applies exactly that response, once.
  4. On reject, the world is unchanged, and the projection record
     says so. A rejected projection is not a failed projection;
     it is the gate working.

"Projection is real" in this package means only this: the mapping
above is implemented, reproducible, and measurable inside this
toy, with a fidelity number computed from it. It does NOT mean
that a physical hologram, a light field, or a real nervous system
projects into a real world. Those are different claims, with
different evidence, and this toy supplies none of it.

A ProjectionRecord carries: decision, response, intended response
(truth, for scoring only, never for deciding), overlap, probs,
world state before and after, and whether the world changed.
"""
from human import modulate
from world import World


class ProjectionRecord:
    def __init__(self, decision, response, intended, overlap, probs,
                 before, after, changed):
        self.decision = decision
        self.response = response
        self.intended = intended
        self.overlap = overlap
        self.probs = probs
        self.before = before
        self.after = after
        self.changed = changed

    @property
    def correct(self):
        return self.decision == "accept" and self.response == self.intended

    def to_dict(self):
        return {"decision": self.decision, "response": self.response,
                "intended": self.intended, "overlap": self.overlap,
                "probs": self.probs, "before": self.before,
                "after": self.after, "changed": self.changed,
                "correct": self.correct}


class Projector:
    """Projects bubble decisions into a world, fail-closed."""

    def __init__(self, bubble, world=None):
        self.bubble = bubble
        self.world = world if world is not None else World()

    def project(self, field, f_hz=7.0, intended=None):
        before = self.world.state()
        decision, response, probs = self.bubble.decide_true(field, f_hz)
        # Overlap recomputed on the modulated field, for the record
        # only; the decision above already happened and is not
        # changed by this recomputation.
        overlap = self.bubble.system.max_overlap(modulate(field, f_hz))
        changed = False
        if decision == "accept":
            changed = self.world.apply(response)
        after = self.world.state()
        return ProjectionRecord(decision, response, intended, overlap,
                                probs, before, after, changed)

    def project_many(self, probes, truths, f_hz=7.0):
        return [self.project(f, f_hz, intended=t)
                for f, t in zip(probes, truths)]


def fidelity(records):
    """Projection fidelity: correct projections / all projections.

    Correct = accepted AND response == intended. Rejected probes
    count in the denominator: a projection that refuses is not a
    correct projection, and hiding refusals would inflate fidelity.
    Accuracy-on-accepted is reported alongside, separately.
    """
    if not records:
        return None
    correct = sum(1 for r in records if r.correct)
    return correct / len(records)


def accuracy_on_accepted(records):
    acc = [r for r in records if r.decision == "accept"]
    if not acc:
        return None
    return sum(1 for r in acc if r.correct) / len(acc)
