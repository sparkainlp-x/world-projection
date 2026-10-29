# Design and evaluation notes

## What the toy does

The recognition layer stores four seeded, enveloped complex fields. For a probe `x` and stored pattern `p`, the code computes the complex inner product `m = Σ conjugate(pᵢ) xᵢ`; the selected response is `argmax |m|`. The gate accepts iff `max |m| ≥ tau`. The reported class scores are `|m|² / Σ|m|²`; they are not trained or calibrated probabilities.

The 3×3 world is a separate hand-authored state machine. `end-to-end success` is `count(changed action AND response matches intended label) / all probes`. It deliberately counts every bubble rejection, world refusal, and no-op in the denominator. `response accuracy on accepted` is a separate classifier-only metric. Neither number should be compared directly to v0.1.0’s different projection metric.

The frequency curve, world deltas, purity guard, and breaker count are design choices. The frequency curve is a Gaussian multiplier centered at 7 Hz. It is not estimated from people or biological signals.

## Routes are graph distances, not physiology

The stored neuron graph is undirected. Route summaries now constrain cross-stage movement to the specified monotone sequences: sensory → spinal → motor, or sensory → spinal → central → motor. The lesion removes every spinal–motor link, including any contributed by k-nearest-neighbour construction. Distances are toy coordinate units, never milliseconds. These corrections affect route summaries and lesion behavior, not the undirected graph used to make stored wave patterns.

## Evaluation and uncertainty

The optimizer selects a threshold/frequency pair using only train data. A separate calibration split checks predeclared acceptance and false-accept bounds; failure stops the run before held-out evaluation. The held-out split is evaluated once after selection is locked. Wilson intervals are shown for per-probe decision rates only. End-to-end success is one stateful trajectory, so it has no binomial interval; the sweep’s mean/range summarize only three seeded trajectories and are descriptive.

The observer is a synthetic measurement generator that has simulator access. Its reports and bootstrap interval characterize generated toy samples, not external measurement error or a population. The review runner evaluates the calibrated assumed model on a different synthetic held-out set. Its automatic toggle of the `review_signoff` flag is a test harness action, not human review. The optimizer’s “frozen” comparator uses the known simulator threshold and is an oracle/reference baseline.

Injection uses paired in-pattern and random-field probes, including stock-accepted probes in scoring. Its score is a Brier loss plus configured sample cost. The calibrator can return an on/off recommendation only when the score’s lower 95% summary is positive, new accepts are observed, and the random-field false-accept Wilson upper bound is ≤0.05. This recommendation is recorded in assumed state but is not wired into the projection/world action path.

## Change and lineage record

The source baseline is [`sparkainlp-x/world-projection` at `a4ecc9c3826d821b76612437d6406e1ad089e3d0`](https://github.com/sparkainlp-x/world-projection/commit/a4ecc9c3826d821b76612437d6406e1ad089e3d0), the v0.1.0 import. The current upstream `main` snapshot inspected for this candidate is `9277d871bd36d3d57cd4eec6d4d278eb2447c299`; its later change adds the game link to the README, which is retained here. See [`PROVENANCE.md`](PROVENANCE.md) for component-level details and unresolved source-name references.

The prior `world.py`, `projection.py`, and `observer_world.py` interface is replaced by `world3x3.py` and `projection3x3.py`; this is a deliberate API change, not a drop-in update. New evaluation files are `sweep3x3.py`, `optimizer3x3.py`, `full_science.py`, and `passport3x3.py`. Some inherited modules have small behavior-preserving guards or explicitly documented route/measurement corrections; the full differences are visible in the local candidate diff. The top-level AGPL-3.0-only license text is byte-for-byte preserved from the upstream repository.

No participant data, recordings, network telemetry, credentials, or private keys are included. Citation metadata contains the public author name, affiliation, and ORCID already associated with the project.
