"""Test the hypothesis: fix inputs + outputs, ANNEAL THE WEIGHTS -> learning.

A single bipolar perceptron:   y = sign(w0 + w1*x1 + w2*x2),  x,w,y in {-1,+1}.

Normal inference clamps the weights and reads y. We do the opposite: clamp the
whole truth table (inputs AND outputs) and leave the WEIGHTS free, then anneal.
The ground state is the weight vector that reproduces the target gate.

Key trick that keeps this a clean QUBO/Ising: because the inputs are clamped
CONSTANTS, each term  w_i * x_i  is LINEAR in the (free) weight w_i. So the
per-example pre-activation  s_k = sum_i w_i * c_ki  is linear in the weights,
and the squared-error energy  sum_k (s_k - M*y_k)^2  is exactly quadratic in
the weights -> an Ising model an annealer can minimize directly.

This is the ONE-LAYER case. A hidden layer would make activations variables,
turning w * h into variable*variable (and deeper, 3+ way) products -> HUBO,
which is where "efficiently" breaks down.

Run:  source ../ocean/bin/activate && python learn-weights-by-annealing.py
"""

from __future__ import annotations

import itertools
from collections.abc import Callable

import dimod

# Bipolar truth tables (x1, x2) -> y, with 0/1 mapped to -1/+1.
BIPOLAR = {0: -1, 1: 1}
GATES: dict[str, Callable[[int, int], int]] = {
    "AND": lambda a, b: a & b,
    "OR": lambda a, b: a | b,
    "XOR": lambda a, b: a ^ b,
}
WEIGHTS = ["w0", "w1", "w2"]  # w0 is the bias (its input is always +1)
M = 2  # target pre-activation magnitude: we want s_k ~= M * y_k


def training_set(gate: str) -> list[tuple[list[int], int]]:
    """Clamped examples: each is (feature_vector [1, x1, x2], label), bipolar."""
    fn = GATES[gate]
    rows = []
    for a, b in itertools.product((0, 1), repeat=2):
        features = [1, BIPOLAR[a], BIPOLAR[b]]  # bias input is constant +1
        label = BIPOLAR[fn(a, b)]
        rows.append((features, label))
    return rows


def build_ising(rows: list[tuple[list[int], int]]) -> dimod.BinaryQuadraticModel:
    """Energy = sum_k (sum_i w_i*c_ki - M*y_k)^2, expanded over spin weights.

    For SPIN variables w_i^2 == 1, so the diagonal (w_i*c_ki)^2 terms are
    constants and fold into the offset; only linear h_i and coupler J_ij remain.
    """
    n = len(WEIGHTS)
    h = {WEIGHTS[i]: 0.0 for i in range(n)}
    j: dict[tuple[str, str], float] = {}
    offset = 0.0
    for features, y in rows:
        target = M * y
        # cross terms: sum_{i<j} 2*c_i*c_j * w_i*w_j
        for i in range(n):
            for k in range(i + 1, n):
                key = (WEIGHTS[i], WEIGHTS[k])
                j[key] = j.get(key, 0.0) + 2.0 * features[i] * features[k]
        # linear terms: -2*target*c_i * w_i
        for i in range(n):
            h[WEIGHTS[i]] += -2.0 * target * features[i]
        # constants: diagonal c_i^2 (==c_i^2*w_i^2, w^2=1) plus target^2
        offset += sum(c * c for c in features) + target * target
    return dimod.BinaryQuadraticModel(h, j, offset, dimod.SPIN)


def classify(weights: dict[str, int], rows: list[tuple[list[int], int]]) -> int:
    """Count correctly reproduced examples under the learned weights."""
    correct = 0
    for features, y in rows:
        s = sum(weights[WEIGHTS[i]] * features[i] for i in range(len(WEIGHTS)))
        pred = 1 if s >= 0 else -1
        correct += pred == y
    return correct


def learn(gate: str) -> None:
    rows = training_set(gate)
    bqm = build_ising(rows)
    # ExactSolver enumerates all 2^3 weight vectors; swap in
    # SimulatedAnnealingSampler (or a QPU) once the weight count grows.
    best = dimod.ExactSolver().sample(bqm).first
    weights = {k: int(v) for k, v in best.sample.items()}
    got = classify(weights, rows)
    # The honest signal is the ENERGY FLOOR: a perfect linear separator drives
    # the squared error to its minimum; a non-separable gate cannot get near it.
    verdict = "learned perfectly" if got == len(rows) else "cannot fit at 1 layer"
    print(f"{gate:4}: weights={weights}  energy={best.energy:+.1f}  "
          f"correct={got}/{len(rows)}  -> {verdict}")


if __name__ == "__main__":
    print("Annealing the WEIGHTS (inputs + outputs clamped) to learn each gate:\n")
    for name in GATES:
        learn(name)
    print(
        "\nAND/OR are linearly separable -> one perceptron suffices and the energy\n"
        "hits its floor (4.0). XOR is not -> its minimum energy (28.0) is stuck far\n"
        "above the floor no matter which weights win, the annealer's proof that no\n"
        "single-layer fit exists. That's exactly when you'd add a hidden layer --\n"
        "and pay the HUBO price described in the module docstring."
    )
