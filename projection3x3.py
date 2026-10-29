"""Projection into the 3x3 world: bubble decision -> 3x3 action.

Two independent refusals, both fail-closed:
  1. Bubble gate rejects -> world is not tried, unchanged.
  2. World guard rejects (residual > 0.20) -> action is rolled back,
     world unchanged, breaker count rises. After 5 consecutive world
     rejections, the breaker latches and the world stops changing.
A projection record says which refusal happened, if any, so a
world rejection is never mistaken for a bubble rejection.
"""
from human import modulate
from world3x3 import World3x3


class Record3x3:
    def __init__(self, decision, response, intended, overlap,
                 before, after, changed, refusal):
        self.decision = decision
        self.response = response
        self.intended = intended
        self.overlap = overlap
        self.before = before
        self.after = after
        self.changed = changed
        self.refusal = refusal  # None, "bubble", or "world_guard"

    @property
    def correct(self):
        return self.changed and self.response == self.intended


class Projector3x3:
    def __init__(self, bubble, world=None):
        self.bubble = bubble
        self.world = world if world is not None else World3x3()

    def project(self, field, f_hz=7.0, intended=None):
        before = self.world.state()
        decision, response, _probs = self.bubble.decide_true(field, f_hz)
        overlap = self.bubble.system.max_overlap(modulate(field, f_hz))
        if decision != "accept":
            return Record3x3(decision, response, intended, overlap,
                             before, before, False, "bubble")
        changed = self.world.apply(response)
        after = self.world.state()
        if changed:
            refusal = None
        elif self.world.last_refusal == "guard":
            refusal = "world_guard"
        elif self.world.last_refusal == "breaker":
            refusal = "breaker"
        else:
            refusal = "no_op"
        return Record3x3(decision, response, intended, overlap,
                         before, after, changed, refusal)

    def project_many(self, probes, truths, f_hz=7.0):
        if len(probes) != len(truths):
            raise ValueError("probes and truths must have equal lengths")
        return [self.project(f, f_hz, intended=t)
                for f, t in zip(probes, truths)]


def fidelity(records):
    if not records:
        return None
    return sum(1 for r in records if r.correct) / len(records)
