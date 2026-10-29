# Preregistration — world-projection v0.1.0

Before any demo run, the rules are fixed:

- Inside: bubble-nervous-system v0.1.0, vendored unchanged
  (nervous, human, injection, bubble, observer, calibrator).
  Gate calibrated once, tau frozen, patterns never added.
- World: start (0,0), held None, object "stone" at (2,0),
  stability 0.50, temperature 20.0, energy 100.0, step 0.
- Projection, the only definition used here: bubble decision
  (accept + response, or reject) at a given frequency, then on
  accept the world applies exactly that response once, on reject
  the world is unchanged. Actions: withdraw x -= 10, stability
  -= 0.05; grasp picks iff object within 5 and held is None;
  balance stability += 0.20 (cap 1.0); cool-alert temperature
  -= 5.0. Each changed action costs 1.0 energy, step += 1.
- Fidelity = correct / all, where correct = accepted AND
  response == intended. Rejects count in the denominator.
  Accuracy-on-accepted is reported separately, never as fidelity.
- Demo grid: sigmas 0.15, 0.30, 0.50 at 7.0 Hz, plus 0.15 at
  0.25 Hz, n=40 per cell, seed 99, plus 40 random fields per cell
  which must leave the world unchanged probe by probe.
- Claim bar, fixed before running: clean on-frequency fidelity
  >= 0.80, noisy fidelity < clean fidelity, off-frequency
  projection rejects, random fields leave the world unchanged
  in at least 35/40 cases per cell. If any bar fails, the result
  is reported as a failure, not tuned away.
- Headline: WITHHELD for any physical claim. What is proved here
  is implementation + measurement inside this toy, not that
  physical holographic projection is real.
