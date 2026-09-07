"""OR gate as a reusable annealing building block.

Two constructions of the same gate (out = a OR b):
  1. from primitives  - the penalty QUBO/BQM built by hand
  2. from dimod        - dimod.generators.or_gate does the algebra for you

Both return a BinaryQuadraticModel with *your* chosen variable names, so you
can wire them into bigger circuits by reusing a variable name as the shared
"wire" between gates. The composition demo at the bottom shows that pattern -
it's the same trick you'll use to build adders and a full multiplier.

Run:  source ../ocean/bin/activate && python or-gate.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import dimod

if TYPE_CHECKING:
    from dimod import BinaryQuadraticModel
    from dimod.typing import Variable


# --- 1. AND gate from primitives -------------------------------------------
#
# A QUBO is a dict {(var_i, var_j): coefficient} for the energy
#     E(x) = sum_i  Q[i,i]*x_i          (diagonal = linear "bias" terms)
#          + sum_i<j Q[i,j]*x_i*x_j     (off-diagonal = quadratic "couplings")
# because each x is binary, x_i^2 == x_i, so (i,i) entries ARE the linear part.
#
# The OR penalty, derivable by hand, is
#     E = a + b + out + a*b - 2*a*out - 2*b*out
# which is 0 exactly on the valid rows {000, 011, 101, 111} and > 0 otherwise:
#   (a,a)=(b,b)=(out,out)=1  -> each variable-on costs +1 on its own...
#   (a,out)=(b,out)=-2       -> ...refunded 2 when an input agrees with out...
#   (a,b)=1                  -> ...and both-inputs-on (out forced to 1) nets right.
def or_gate_from_primitives(a: Variable, b: Variable, out: Variable) -> BinaryQuadraticModel:
    linear = {a: 1.0, b: 1.0, out: 1.0}
    quadratic = {(a, b): 1.0, (a, out): -2.0, (b, out): -2.0}
    return dimod.BinaryQuadraticModel(linear, quadratic, 0.0, dimod.BINARY)


# --- 2. OR gate from the dimod library -------------------------------------
#
# Same model, zero algebra. Ocean also ships or_gate / xor_gate / halfadder_gate
# / fulladder_gate - the primitives you'll compose for factorization.
def or_gate_from_dimod(a: Variable, b: Variable, out: Variable) -> BinaryQuadraticModel:
    return dimod.generators.or_gate(a, b, out)


def dump(bqm: BinaryQuadraticModel, title: str) -> None:
    print(f"== {title} ==")
    print("linear   :", dict(bqm.linear))
    print("quadratic:", dict(bqm.quadratic))
    print("offset   :", bqm.offset)


def truth_table(bqm: BinaryQuadraticModel, title: str) -> None:
    # ExactSolver brute-forces all 2^n states (fine for tiny circuits); the
    # energy-0 rows are exactly the gate's valid input/output combinations.
    print(f"\n== truth table: {title} (energy 0 == valid) ==")
    print(dimod.ExactSolver().sample(bqm).aggregate())


def usage_fix_inputs() -> None:
    # "Using" a gate: pin the inputs, then read the output the annealer settles
    # on. Fixing a=1,b=1 should force out=1 as the unique ground state.
    bqm = or_gate_from_dimod("a", "b", "out")
    bqm.fix_variable("a", 1)
    bqm.fix_variable("b", 1)
    best = dimod.ExactSolver().sample(bqm).first
    print("\n== usage: a=1, b=1 -> read out ==")
    print("out =", best.sample["out"], "(energy", best.energy, ")")


def composition_three_input_or() -> None:
    # Wire two gates by SHARING a variable name: 't' is the output of the first
    # gate and an input of the second, so  w = (a OR b) OR c.
    # Adding BQMs merges terms on shared variables; ground states satisfy both.
    bqm = or_gate_from_primitives("a", "b", "t")
    bqm += or_gate_from_primitives("t", "c", "w")
    print("\n== composition: w = a OR b OR c (two chained OR gates) ==")
    print(dimod.ExactSolver().sample(bqm).lowest())


if __name__ == "__main__":
    primitive = or_gate_from_primitives("a", "b", "out")
    library = or_gate_from_dimod("a", "b", "out")
    dump(primitive, "or_gate_from_primitives('a','b','out')")
    print()
    dump(library, "or_gate_from_dimod('a','b','out')")

    truth_table(primitive, "from primitives")
    usage_fix_inputs()
    composition_three_input_or()
