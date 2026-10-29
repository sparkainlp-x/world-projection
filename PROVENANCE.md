# Provenance and rights notes

## Direct repository lineage

This review candidate is derived from the public repository [`sparkainlp-x/world-projection`](https://github.com/sparkainlp-x/world-projection). Its v0.1.0 source baseline is commit [`a4ecc9c3826d821b76612437d6406e1ad089e3d0`](https://github.com/sparkainlp-x/world-projection/commit/a4ecc9c3826d821b76612437d6406e1ad089e3d0). The current upstream `main` snapshot inspected here is `9277d871bd36d3d57cd4eec6d4d278eb2447c299`; that later commit adds the Muse game link to the README. The link is retained in this candidate.

The upstream’s `LICENSE` file is preserved byte-for-byte as AGPL-3.0-only. The initial archive’s `nervous.py`, `human.py`, `injection.py`, `bubble.py`, `observer.py`, and `calibrator.py` matched the corresponding upstream source files before this review’s narrowly documented changes. In this review candidate, those files now contain the following changes: input and frequency validation; stage-constrained route summaries and complete reflex-edge removal; repeated synthetic measurement summaries; paired injection scoring; report-type and calibration checks; default assumed-shadow parameters; and explicit simulated-observer wording. `projection3x3.py` also rejects mismatched probe/truth arrays. New v0.2.0 components are `world3x3.py`, `projection3x3.py`, `sweep3x3.py`, `optimizer3x3.py`, `full_science.py`, and `passport3x3.py`; `demo.py`, `tests.py`, and the documentation are revised.

The prior `world.py`, `projection.py`, and `observer_world.py` are removed in the archive and replaced by the 3×3 implementation. This is a deliberate API change. The repository’s full local diff, not this summary, is the authoritative change set.

## Source names cited in inherited module headers

The source headers identify these projects as algorithmic lineage or inspiration. The direct source project is `world-projection`; the names below are preserved as component-level attribution rather than claims of coauthorship.

| Module | Cited source names | Public source/license status checked for this review |
|---|---|---|
| `nervous.py` | `membrane-capacity`, `refusing-membrane`, `membrane-vs-hopfield`, `membrane-heart`, `membrane-brain`, `holo-heart-neurons` | Public repositories were found for [`membrane-capacity`](https://github.com/sparkainlp-x/membrane-capacity), [`refusing-membrane`](https://github.com/sparkainlp-x/refusing-membrane), [`membrane-heart`](https://github.com/sparkainlp-x/membrane-heart), and [`membrane-brain`](https://github.com/sparkainlp-x/membrane-brain); GitHub reports AGPL-3.0 for those repositories. Exact public repositories for `membrane-vs-hopfield` and `holo-heart-neurons` were not identified in the source account’s public repository list.
| `human.py` | `bentov-kuramoto/chain.py` | The exact repository name was not identified in the source account’s public repository list. The module says its frequency table is illustrative and not measured.
| `injection.py` | `membrane-arena-3x3`; `microtubule-crystallize/calibration.py` | [`membrane-arena-3x3`](https://github.com/sparkainlp-x/membrane-arena-3x3) is public and GitHub reports AGPL-3.0. The exact `microtubule-crystallize` repository name was not identified. The separate public `crystallize` repository inspected during this review is a web game and does not establish the identity/license of `microtubule-crystallize`.
| `README.md` | Digital to Wave paradigm, Mun Seok Lee | The two Zenodo records are cited as inspiration, not package coauthorship: [21947036](https://zenodo.org/records/21947036) and [21947108](https://zenodo.org/records/21947108).

The related source projects’ license declarations are not substitutes for a component-level provenance audit. Before a public v0.2.0 release, the project owner should confirm whether the unresolved names are private, renamed, or references to specific public source revisions, and verify that the relevant notices and licenses are compatible. No unrelated source files from those named projects are included as separate vendored trees in this archive.

## Privacy and third-party material

The archive and reviewed source tree contain no participant records, human recordings, telemetry, credentials, private keys, or binary media. The Python code uses local deterministic random generators and does not send data over a network. The only personal data are the project author’s name, affiliation, and public ORCID in citation metadata; the owner should confirm these remain intended for publication.
