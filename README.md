# World Projection 3×3 — v0.2.0 review candidate

A standard-library Python toy that maps synthetic complex-valued pattern probes through a frozen overlap gate into state-changing actions in a 3×3 lattice. It is a software experiment only—not evidence about physics, optical holography, neuroscience, a person, or real-world safety.

The existing game remains available: [Play World Projection](https://muse.ai/s/world-projection-game-mr6hxzxw8ayxx2/NsBG4ExZGzJ-dKn4k2TKOu02lwkRnWEH1DPp-e5RDP8).

## What it computes

The model stores four code-generated, normalized wave patterns. A probe is assigned to the pattern with the largest absolute overlap; a frozen threshold rejects probes below `tau`. The reported squared-overlap proportions are toy scores, not calibrated probabilities. A separately imposed Gaussian frequency multiplier is centered at 7 Hz with width 1.5 Hz; those parameters are design choices, not fitted measurements.

Accepted labels invoke one hand-written world action: `withdraw`, `grasp`, `balance`, or `cool-alert`. The world has a purity residual guard and a breaker. These rules are arbitrary simulator rules, not physical safety limits.

Two rates are kept distinct:

- **Response accuracy on accepted probes**: correct response labels divided by bubble-accepted probes; this ignores whether the stateful world action succeeds.
- **End-to-end success** (the compatibility key `fidelity`): a correct response that actually changes the world divided by *all* probes. Bubble rejects, guard/breaker refusals, and no-ops count as failures.

The original 3×3 world behavior is retained: a grasp does nothing unless the agent is on the stone; repeated balance actions eventually exceed the guard; a rejected action rolls back.

## Reproducible run

Requires Python 3 and only the standard library:

```bash
python3 demo.py
python3 -m unittest tests -v
python3 full_science.py                 # writes science-results.json
python3 full_science.py /tmp/run.json   # optional output path
```

`science-results.json` is a deterministic run record for the current code and Python version. It includes the protocol, full report and cell data, per-file source hashes, and a SHA-256 seal. A seal detects changed inputs; it does not validate claims or certify independent review. The file is ignored by Git because it is regenerated.

The full runner has separate synthetic evaluations:

- The internal frozen gate is built from 100 in-pattern and 100 random probes using calibration seed 11. Its resulting `tau` is seed- and implementation-specific, not a universal constant.
- The observer/calibrator exercise uses independent deterministic streams. The observer is a simulator-backed report generator, not an independent or blinded measurement. Calibration selects `tau` by Youden’s J, selects frequency by Youden’s J against random-field controls, and reports a deterministic bootstrap interval for `tau`. The demo sets a boolean review flag automatically solely to exercise the toy gate; this is not a real human review or authorization.
- The calibrated assumed model is compared before/after on a separate 200-probe synthetic set (seed 404), which is not used to select the calibration. Injection is reported only as a recommendation; it is not connected to the world-action path.
- The optimizer uses distinct train, calibration, and held-out probe streams (seeds 201, 202, 203) and world initializations (seeds 42, 43, 44; 100 probes per split by default). It searches 101 thresholds and four fixed frequencies on train, checks the locked candidate on calibration, and evaluates held-out only if those checks pass. Calibration requires the 95% Wilson upper bound for random-field false acceptance to be at most 0.05 and the Wilson lower bound for in-pattern acceptance to be at least 0.50. Its frozen-threshold comparison uses simulator ground truth and is an oracle/reference, not a deployable competitor.
- The sweep summarizes 40-probe stateful trajectories across seeds 42, 7, and 123. It reports per-seed results and descriptive means/ranges. It does not claim a confidence interval for trajectory success: successive probes share a changing world state, and three trajectories are too few for population inference.

All data are synthetic and generated from the package’s own rules. The held-out sets are held out only within this toy distribution—not external data, independent subjects, or replication. Small differences between settings are not evidence of generalization.

## Provenance, license, and credits

This candidate is derived from the public [`sparkainlp-x/world-projection`](https://github.com/sparkainlp-x/world-projection) repository. The exact upstream snapshot and retained/replaced components are recorded in [`PROVENANCE.md`](PROVENANCE.md). The repository’s existing AGPL-3.0-only license is preserved; the provenance note also flags source-name references that still need owner confirmation before a public release.

Project author: Jean-François Brisson (Spark). The Digital to Wave paradigm by Mun Seok Lee (Zenodo records [21947036](https://zenodo.org/records/21947036) and [21947108](https://zenodo.org/records/21947108)) is cited as inspiration only, not as package coauthorship. The package author reports AI assistance in writing new code. See [`DESIGN.md`](DESIGN.md) for the design changes and limitations.
