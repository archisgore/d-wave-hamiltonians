"""Hello-world annealer for D-Wave Ocean.

Solves a tiny 2-variable QUBO whose ground state is x0 = x1 = 1, then prints
the lowest-energy sample.

Backends (choose with DWAVE_BACKEND, default "auto"):
  qpu   - real D-Wave quantum annealer (needs a Solver API token; see README)
  sim   - local classical simulated annealer (no token, no network)
  auto  - try the QPU, fall back to the simulator if it is unavailable

Run:
  source ../ocean/bin/activate
  python hello-annealer.py            # auto
  DWAVE_BACKEND=sim python hello-annealer.py
  DWAVE_BACKEND=qpu python hello-annealer.py
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dimod import Sampler, SampleSet


# Ground state of this QUBO is x0 = x1 = 1 (energy -3): each variable
# contributes -1, and being on together earns a -1 coupling bonus.
QUBO = {
    (0, 0): -1,
    (1, 1): -1,
    (0, 1): -1,
}
NUM_READS = 100


def run_qpu() -> tuple[Sampler, SampleSet]:
    """Sample on a real D-Wave QPU. Raises if no token / no connection."""
    from dwave.system import DWaveSampler, EmbeddingComposite

    sampler = EmbeddingComposite(DWaveSampler())
    sampleset = sampler.sample_qubo(QUBO, num_reads=NUM_READS)
    return sampler, sampleset


def run_sim() -> tuple[Sampler, SampleSet]:
    """Sample locally with a classical simulated annealer. Always works."""
    from dwave.samplers import SimulatedAnnealingSampler

    sampler = SimulatedAnnealingSampler()
    sampleset = sampler.sample_qubo(QUBO, num_reads=NUM_READS)
    return sampler, sampleset


def main() -> int:
    backend = os.environ.get("DWAVE_BACKEND", "auto").lower()

    if backend == "sim":
        used, (sampler, sampleset) = "simulator", run_sim()
    elif backend == "qpu":
        used, (sampler, sampleset) = "QPU", run_qpu()
    elif backend == "auto":
        try:
            sampler, sampleset = run_qpu()
            used = "QPU"
        except Exception as exc:  # noqa: BLE001 - fall back on any QPU problem
            print(f"[auto] QPU unavailable ({exc}); using local simulator.\n")
            sampler, sampleset = run_sim()
            used = "simulator"
    else:
        print(f"Unknown DWAVE_BACKEND={backend!r} (use qpu, sim, or auto)")
        return 2

    best = sampleset.aggregate().first
    print(f"Hello, D-Wave!  (backend: {used})")
    print(f"Best sample: {dict(best.sample)}")
    print(f"Energy:      {best.energy}")
    print(f"Occurrences: {best.num_occurrences} / {NUM_READS}")

    solver = getattr(sampler, "child", sampler)
    name = getattr(getattr(solver, "solver", None), "name", None)
    if name:
        print(f"Solver:      {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
