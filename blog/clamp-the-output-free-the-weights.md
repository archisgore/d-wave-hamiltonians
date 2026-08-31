# Clamp the Output, Free the Weights

I started where everyone starts: Shor's algorithm. If you want to understand why
quantum computing matters, factoring large numbers in polynomial time is the
headline act — the thing that breaks RSA and launched a thousand grant proposals.
So I read up on gate-based quantum computing, the qubits and Hadamards and the
quantum Fourier transform that makes Shor tick.

Then I tried to get my hands on one. That's where the story bends.

## You can't buy a gate-based quantum computer

You can *rent time* on IBM's or others' gate machines through the cloud, but the
only quantum computer you could actually **purchase and put in a room** was a
D-Wave. So I went to learn what a D-Wave even is — and it turns out it doesn't run
Shor's algorithm at all. It doesn't run circuits. It's a **quantum annealer**: it
finds the lowest-energy state of an Ising/QUBO model. You hand it an energy
function over binary variables, and it settles into the minimum.

My first reaction was disappointment. No Shor, no clean factoring headline. My
second reaction — the one that turned into a weekend rabbit hole — was: *then how
would you factor a number on the one quantum computer you can actually buy?*

## Factoring, backwards

The answer is delightfully sneaky. You don't factor. You **un-multiply**.

Build a binary multiplication circuit — the same AND/OR/XOR gates and adders you'd
etch into silicon — but express each gate as an energy penalty that is zero when
the gate's truth table is satisfied and positive when it's violated. Chain the
gates by sharing variables as wires, sum the penalties, and you get one big energy
function whose ground state is *any* valid run of the multiplier: `a * b = p`.

Now the trick. Normally you'd clamp `a` and `b` and read `p`. Instead you **clamp
`p`** to the number you want to factor and leave `a` and `b` free. The annealer,
minimizing energy, has no choice but to settle into an `a` and `b` that multiply
to your target. Factoring becomes multiplication run in reverse.

I built the gates by hand to feel this — deriving the AND penalty
`E = a·b − 2a·z − 2b·z + 3z` from scratch, then the OR, checking each truth table
against D-Wave's own `dimod` generators. (I got the OR sign wrong the first time;
the annealer cheerfully told me "1 OR 1 = 0" was the lowest-energy answer, which is
a very humbling way to find a bug.)

## The realization that outgrew factoring

Somewhere in wiring gates together it hit me: **the annealer doesn't care which
variables you clamp.** Inputs, outputs, anything. Clamp the inputs → forward
inference. Clamp the output → inversion, i.e. factoring. The direction is a choice
you make at solve time, not a property of the machine.

So I asked the crazy question: what if the *free* variables weren't the factors,
but the **weights of a neural network**? Clamp the inputs *and* the outputs — the
whole training set — and let the weights anneal. Wouldn't the ground state be a set
of weights that reproduces the data? Wouldn't that be... learning?

## It works (at one layer)

It does. I wrote a single bipolar perceptron `y = sign(w₀ + w₁x₁ + w₂x₂)`, clamped
each gate's full truth table, left the three weights as free spins, and annealed.

```
AND : weights={w0:-1, w1:1, w2:1}   energy=+4.0   correct=4/4  -> learned perfectly
OR  : weights={w0: 1, w1:1, w2:1}   energy=+4.0   correct=4/4  -> learned perfectly
XOR : weights={w0:-1, w1:-1,w2:-1}  energy=+28.0  correct=1/4  -> cannot fit at 1 layer
```

No gradients. No backprop. The annealer recovered the exact AND weights I'd derived
by hand — it *learned the gate* from its truth table alone.

There's a structural reason this is clean: when you clamp the inputs, every `wᵢ·xᵢ`
term has a **constant** `xᵢ`, so it's linear in the weight. A single layer with
clamped I/O stays a well-behaved quadratic model — exactly what an annealer wants.

And XOR is the punchline. Its energy floor is stuck at 28 versus 4 for the others,
and no weights can close the gap. That's the annealer *proving* XOR isn't linearly
separable — the precise moment classical ML says "add a hidden layer."

## The wall, stated honestly

Which is also where the magic stops. Add a hidden layer and the hidden activations
become variables, so `w·h` turns into variable-times-variable — and stacking deeper
gives products of three or more variables. Now you're in HUBO territory, not QUBO,
and you have to reduce the order with auxiliary qubits and stiff penalties that
choke the anneal. Training threshold networks is NP-hard regardless, and today's
sparse qubit connectivity means anything interesting barely embeds.

So the honest scorecard: **efficient and real at one layer; conceivable but not
efficient beyond it.**

## What I actually came away with

I went looking for Shor's algorithm and a machine to run it on. I found a different
machine that can't run Shor at all — and in working around that limitation, I
stumbled into a much older, deeper idea: **inference and learning are the same
energy landscape, minimized over different variables.** That's the Boltzmann-machine
worldview, and I got there sideways, from a factoring circuit run backwards.

The only quantum computer I could buy turned out to teach me something the famous
algorithm never would have.
