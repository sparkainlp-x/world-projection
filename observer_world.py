"""World observer: measures the projection, never changes the world.

The observer sees the world state with declared noise (sigma) on
continuous fields, tagged REPORTED, and counts, from projection
records, how often the projected response matched the intended
response, how often a rejection left the world unchanged, and how
often a random field left the world unchanged. Measuring must not
move the world, change the gate, or add a pattern. That is tested.
"""
import random


class WorldObserver:
    def __init__(self, sigma=0.05, seed=42):
        self.sigma = sigma
        self.rng = random.Random(seed)

    def measure(self, world):
        return {
            "x": world.x + self.rng.gauss(0, self.sigma),
            "y": world.y + self.rng.gauss(0, self.sigma),
            "held": world.held,
            "stability": world.stability + self.rng.gauss(0, self.sigma),
            "temperature": world.temperature + self.rng.gauss(0, self.sigma),
            "step": world.step,
            "tag": "REPORTED",
        }

    @staticmethod
    def summarise(records):
        n = len(records)
        if n == 0:
            return {}
        accepted = [r for r in records if r.decision == "accept"]
        rejected = [r for r in records if r.decision == "reject"]
        return {
            "n": n,
            "accepted": len(accepted),
            "rejected": len(rejected),
            "correct": sum(1 for r in records if r.correct),
            "fidelity": sum(1 for r in records if r.correct) / n,
            "accuracy_on_accepted": (
                sum(1 for r in accepted if r.correct) / len(accepted)
                if accepted else None),
            "rejected_unchanged": sum(
                1 for r in rejected if not r.changed),
            "rejected_total": len(rejected),
        }
