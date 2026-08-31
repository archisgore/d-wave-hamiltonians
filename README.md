# d-wave-hamiltonians

Experiments with solving annealing problems using D-Wave APIs and libraries.

## Repository layout

```
d-wave-hamiltonians/
├── hello-world/                      # annealing building blocks, smallest first
│   ├── hello-annealer.py             # tiny QUBO on QPU, auto-fallback to simulator
│   ├── and-gate.py                   # AND gate from primitives AND via dimod
│   ├── or-gate.py                    # OR gate, same two ways
│   └── learn-weights-by-annealing.py # anneal a perceptron's WEIGHTS to learn a gate
├── prime-factorization/
│   └── factorize-using-annealing.py  # scaffold: multiplier run backwards (WIP)
├── blog/
│   └── clamp-the-output-free-the-weights.md  # the write-up of this exploration
├── ocean/                            # Python virtualenv (git-ignored)
├── requirements.txt                  # Ocean SDK + dev tooling, pinned
└── pyproject.toml                    # ruff + mypy config
```

The `hello-world/` scripts are ordered as a learning path: run a solver, express a
logic gate as an energy penalty, compose gates by sharing variables as wires, then
flip the annealer around — clamp inputs *and* outputs and let the **weights** anneal,
which turns inference into learning. Each script is self-contained and prints a
verifiable truth table via `dimod.ExactSolver`.

- **`hello-world/hello-annealer.py`** — minimal "hello annealer": a 2-variable QUBO
  on a real D-Wave QPU, with automatic fallback to a local classical simulator.
- **`hello-world/and-gate.py`** / **`or-gate.py`** — each logic gate built two ways:
  the penalty QUBO derived by hand, and the equivalent `dimod.generators` model
  (verified byte-for-byte identical). Includes a composition demo that wires two
  gates together — the pattern for building adders and multipliers.
- **`hello-world/learn-weights-by-annealing.py`** — the payoff experiment: a single
  bipolar perceptron whose weights are annealed (inputs + outputs clamped) to learn
  AND/OR perfectly, while XOR provably can't fit at one layer.
- **`prime-factorization/`** — scaffold for factoring an integer by annealing a
  binary multiplication circuit with the product clamped (implementation left as WIP).

## Setup

Everything runs inside a Python virtualenv named `ocean` (git-ignored). It is
already created in this checkout; to recreate it from scratch:

```bash
python -m venv ocean
source ocean/bin/activate
pip install -r requirements.txt
```

Then, for every session:

```bash
source ocean/bin/activate
```

## Logging in to D-Wave (Leap)

D-Wave Leap uses two different credentials. You need to understand both.

1. **Leap OAuth token** — how the `dwave` CLI authenticates *you* to the Leap
   web API (project info, account management). Obtained by browser login.
2. **Solver API (SAPI) token** — what actually authorizes *jobs* against a QPU.
   This is what `DWaveSampler()` needs. It lives in the config file as `token`.

### Step 1 — OAuth login (browser)

```bash
dwave auth login          # opens a browser, authorizes Ocean
dwave auth get            # shows the current Leap access token + expiry
dwave auth refresh        # renew when it expires (~daily)
```

### Step 2 — get a Solver API token into the config

If your account has a **paid / full** Leap plan, the CLI can pull the SAPI
token for you automatically after `dwave auth login`:

```bash
dwave config create --auto-token
dwave ping                # verifies end-to-end QPU connectivity
```

> ⚠️ **Trial-access accounts** (this one, currently): D-Wave does **not** expose
> the SAPI token through the API for trial users, so `--auto-token` fails with
> *"Solver API token not available for users with trial access to the Leap
> service."* You have two options:
>
> - Copy the token manually from the Leap dashboard
>   (<https://cloud.dwavesys.com/leap/> → your profile → **API Token**) and add it
>   to the config:
>   ```bash
>   dwave config create --full     # paste token when prompted
>   # or set it inline for one run:
>   DWAVE_API_TOKEN=<your-token> dwave ping
>   ```
> - Otherwise just use the local simulator (below) — no token required.

The config file lives at:
`~/Library/Application Support/dwave/dwave.conf` (macOS). Current contents set
only `region = na-west-1`; the `token` line gets added by the steps above.

## Running the hello-world annealer

```bash
cd hello-world
python hello-annealer.py                     # auto: QPU if available, else simulator
DWAVE_BACKEND=sim python hello-annealer.py   # force local simulator (no token)
DWAVE_BACKEND=qpu python hello-annealer.py   # force real QPU (needs SAPI token)
```

Expected output (simulator or QPU):

```
Hello, D-Wave!  (backend: simulator)
Best sample: {0: 1, 1: 1}
Energy:      -3.0
Occurrences: 100 / 100
```

The problem is a 2-variable QUBO whose ground state is `x0 = x1 = 1`.

## Development (lint & types)

Config lives in `pyproject.toml`. With the venv active:

```bash
ruff check .   # lint + import sorting
mypy           # strict type checking (files listed in pyproject.toml)
```

The D-Wave Ocean libraries ship no type information, so mypy is configured to
skip following their sources rather than scattering per-line ignores through our
own code.
