# World Projection v0.1.0

A nervous system, in a bubble universe, projecting into a world.

## The projection, defined

1. A probe is presented to the bubble's nervous system.
2. The bubble decides, frozen gate, at a frequency: accept with
   withdraw, grasp, balance, or cool-alert, or reject.
3. On accept, the world applies exactly that response, once.
4. On reject, the world is unchanged. That is fail-closed, not
   a failure.

World start: position (0,0), held None, object "stone" at (2,0),
stability 0.50, temperature 20.0, energy 100.0.

## Run

```
python demo.py
python3 -m unittest tests -v
```

## What this proves, and what it does not

Proved, inside this toy, by the tests and demo: the projection
mapping is implemented, reproducible, and measurable, with a
fidelity number that counts rejects in the denominator, and
with random and off-frequency probes leaving the world unchanged.

NOT proved, and NOT claimed: that physical holographic projection
is real, that light projects a nervous system into a physical
world, that this is optical holography, neuroscience, a medical
device, or a measurement of any real person. "Holographic" here
means membrane holographic memory: outer-product storage and
one-shot projection recall, as in the vendored nervous system.
That is a different thing from optical wavefront holography and
from LED fan display, and this package never merges them.

## Credits

Project author: Jean-François Brisson (Spark).
Related work: Mun Seok Lee's Digital to Wave paradigm (Zenodo
records 21947036 and 21947108) is cited as inspiration for the
wave and membrane work; this source citation does not indicate
package coauthorship. Brisson built the package's new code with
AI assistance. Vendored components retain their upstream
attributions and license terms, as documented in DESIGN.md.
