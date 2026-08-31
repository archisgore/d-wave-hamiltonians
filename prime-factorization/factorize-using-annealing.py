"""Factor an integer by annealing a multiplication circuit.

Plan (yours to implement):
  1. Build gate BQMs from primitives - see ../hello-world/and-gate.py for the
     AND gate; add or_gate / xor_gate the same way.
  2. Compose a half-adder and full-adder from those gates by sharing variable
     names as wires.
  3. Wire the adders into an n-bit multiplier: a * b = P, with the product
     bits P fixed to the integer you want to factor.
  4. Sample the combined BQM; the a and b bits of the ground state are the
     factors.

Nothing is implemented here yet - build it up gate by gate.
"""

from __future__ import annotations


def main() -> int:
    raise NotImplementedError("Build the multiplier circuit from gates, then sample it.")


if __name__ == "__main__":
    raise SystemExit(main())
