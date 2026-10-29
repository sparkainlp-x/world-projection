"""World state: what a projection acts on, inside the bubble universe.

The world is a small, fully defined toy state, not a physical world:
  position: (x, y) in arbitrary distance units, start (0, 0)
  held: None or an object name, start None
  object_at: an object the world can grasp, at (2, 0) by default
  stability: 0..1, start 0.50
  temperature: arbitrary units, start 20.0
  energy: arbitrary units, start 100.0, each action costs 1.0
  step: count of applied actions

Actions, one per nervous response, fixed in PREREG:
  withdraw:   x -= 10, stability -= 0.05 (floor 0)
  grasp:      if object_at is within 5 of position, held = object,
              else no change to held; stability unchanged
  balance:    stability = min(1.0, stability + 0.20)
  cool-alert: temperature -= 5.0
Any other response name raises ValueError: the projection may only
apply the four responses the nervous system can produce. A rejected
probe applies NOTHING: the world is unchanged, step does not advance.
That fail-closed rule is the whole safety property of the projection.
"""
import math


class World:
    def __init__(self, object_at=(2.0, 0.0), object_name="stone"):
        self.x = 0.0
        self.y = 0.0
        self.held = None
        self.object_at = tuple(object_at)
        self.object_name = object_name
        self.stability = 0.50
        self.temperature = 20.0
        self.energy = 100.0
        self.step = 0

    def state(self):
        return {"x": self.x, "y": self.y, "held": self.held,
                "object_at": self.object_at, "stability": self.stability,
                "temperature": self.temperature, "energy": self.energy,
                "step": self.step}

    def apply(self, response):
        """Apply one response. Returns True if the world changed."""
        if response == "withdraw":
            self.x -= 10.0
            self.stability = max(0.0, self.stability - 0.05)
            changed = True
        elif response == "grasp":
            dist = math.hypot(self.x - self.object_at[0],
                              self.y - self.object_at[1])
            if dist <= 5.0 and self.held is None:
                self.held = self.object_name
                changed = True
            else:
                changed = False
        elif response == "balance":
            self.stability = min(1.0, self.stability + 0.20)
            changed = True
        elif response == "cool-alert":
            self.temperature -= 5.0
            changed = True
        else:
            raise ValueError(f"unknown response: {response!r}")
        if changed:
            self.energy -= 1.0
            self.step += 1
        return changed

    def __repr__(self):
        return (f"World(x={self.x}, y={self.y}, held={self.held!r}, "
                f"stability={self.stability:.2f}, temp={self.temperature}, "
                f"energy={self.energy}, step={self.step})")
