# DESIGN — world-projection v0.1.0

## Layers, kept distinct

- Nervous system (vendored): 128 neurons, 4 responses, frozen gate.
- Bubble universe (vendored): the boundary, observer, calibrator.
- World (new): a small state with four fixed actions.
- Projection (new): the one-step mapping from decision to action,
  fail-closed on reject.

## Why fidelity counts rejects

If fidelity counted only accepted projections, a gate that
accepted one probe correctly and rejected 39 would score 1.000.
That would be a headline, not a measurement. Here fidelity =
correct / all, accuracy-on-accepted is separate, and both are
reported. A projection that refuses is honest, and it lowers
fidelity, as it should.

## Why this is not a proof about physical reality

A proof about a physical phenomenon needs a physical system, a
physical measurement, a control, and independent replication.
This package has a synthetic state, a synthetic probe, and a
synthetic observer, all defined by its own code. It can prove
internal consistency — that the defined mapping does what it
says, reproducibly, under noise, frequency, and lesion — and
it does that, with tests. It cannot, by construction, prove
anything about light, diamond, a brain, or a world outside the
code. Claiming otherwise would break the portfolio principle:
software that refuses to overclaim, and publishes its own
failure modes.

## Files

- nervous.py, human.py, injection.py, bubble.py, observer.py,
  calibrator.py, LICENSE: vendored, unchanged
- world.py, projection.py, observer_world.py: new world, mapping,
  world observer
- demo.py, tests.py, PREREG.md, README.md, DESIGN.md: run, verify,
  preregister, explain, design
- Private work: excluded entirely, never imported.
