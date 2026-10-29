"""3x3 membrane world: the world inside world-projection, as a lattice.

This is NOT the membrane-arena-3x3 density-matrix engine. That engine
is NumPy, 32-dimensional density matrices, on GitHub at
sparkainlp-x/membrane-arena-3x3, and it is not vendored here.
This world is a stdlib analogue with the same shape and the same
fail-closed idea, so it can run inside world-projection without NumPy:
  - 3x3 cells, agent starts at the centre (1,1)
  - each cell has a purity (seeded 0.06-0.12, like the arena's random
    starting states near 0.06), a temperature (20.0), and a stability
  - an object "stone" sits at (1,0), west of the centre, so a withdraw carries the agent onto it
  - a guard: after an action, max |purity - initial purity| across
    cells must stay <= 0.20, mirroring the arena's residual guard
  - a breaker: after 5 consecutive guard rejections, the breaker
    latches and every later action does nothing, mirroring the arena
    (default run: 8 steps, 3 accepted, 5 rejected, breaker open)

Actions, fixed in PREREG, one per nervous response:
  withdraw:   agent moves west if possible; centre-cell purity -0.05
  grasp:      if the agent cell holds the stone, held = stone
  balance:    centre-cell purity +0.08, stability +0.20 (cap 1.0)
  cool-alert: temperature of all cells -5.0, purity of all cells -0.03
A guard rejection rolls the action back completely, so the world is
unchanged, and counts toward the breaker. A bubble rejection also
leaves the world unchanged, before the world is even tried.
"""
import copy
import random


class World3x3:
    GUARD = 0.20
    BREAKER_LIMIT = 5

    def __init__(self, seed=42):
        rng = random.Random(seed)
        self.purity = [[0.06 + 0.06 * rng.random() for _ in range(3)]
                       for _ in range(3)]
        self.initial_purity = copy.deepcopy(self.purity)
        self.temperature = [[20.0] * 3 for _ in range(3)]
        self.agent = (1, 1)
        self.held = None
        self.stone_at = (1, 0)
        self.stability = 0.50
        self.step = 0
        self.accepted = 0
        self.rejected = 0
        self.consecutive_rejects = 0
        self.breaker_open = False
        self.last_refusal = None  # None, "guard", "no_op", or "breaker"

    def max_residual(self):
        return max(abs(self.purity[r][c] - self.initial_purity[r][c])
                   for r in range(3) for c in range(3))

    def state(self):
        return {"agent": self.agent, "held": self.held,
                "stone_at": self.stone_at, "stability": self.stability,
                "temperature": self.temperature[1][1],
                "max_residual": self.max_residual(),
                "step": self.step, "accepted": self.accepted,
                "rejected": self.rejected,
                "consecutive_rejects": self.consecutive_rejects,
                "breaker_open": self.breaker_open,
                "purity": copy.deepcopy(self.purity)}

    def apply(self, response):
        """Apply one response, with guard + breaker. Returns changed?

        A grasp that picks nothing is a no-op, NOT a guard rejection
        and NOT an acceptance: it changes nothing, advances nothing,
        and does not count toward the breaker. Counting it as
        accepted would inflate fidelity, which is exactly what the
        first version of this file did by mistake, and was fixed.
        """
        self.last_refusal = None
        if self.breaker_open:
            self.last_refusal = "breaker"
            return False
        saved = (copy.deepcopy(self.purity),
                 copy.deepcopy(self.temperature), self.agent, self.held,
                 self.stability)
        r, c = self.agent
        changed_action = True
        if response == "withdraw":
            if c > 0:
                self.agent = (r, c - 1)
            self.purity[r][c] = max(0.0, self.purity[r][c] - 0.05)
        elif response == "grasp":
            if self.agent == self.stone_at and self.held is None:
                self.held = "stone"
            else:
                changed_action = False
        elif response == "balance":
            self.purity[r][c] = min(1.0, self.purity[r][c] + 0.08)
            self.stability = min(1.0, self.stability + 0.20)
        elif response == "cool-alert":
            for i in range(3):
                for j in range(3):
                    self.temperature[i][j] -= 5.0
                    self.purity[i][j] = max(0.0, self.purity[i][j] - 0.03)
        else:
            raise ValueError(f"unknown response: {response!r}")
        if not changed_action:
            self.last_refusal = "no_op"
            return False
        if self.max_residual() > self.GUARD:
            # Roll back completely: guard rejection, world unchanged.
            (self.purity, self.temperature, self.agent, self.held,
             self.stability) = saved
            self.last_refusal = "guard"
            self.rejected += 1
            self.consecutive_rejects += 1
            if self.consecutive_rejects >= self.BREAKER_LIMIT:
                self.breaker_open = True
            return False
        self.accepted += 1
        self.consecutive_rejects = 0
        self.step += 1
        return True
