# SI2002 Formal Languages - Assignment 2

## Students

- Matías Mora Posada
- Salomé Naomi García Tabares

**Class:** Lenguajes Formales (Clase 4369) - 11

## Project description

This program implements the **subset construction algorithm** described in Kozen (1997), Lecture 6. It reads one or more nondeterministic finite automata (NFAs), constructs an equivalent deterministic finite automaton (DFA) for every case, and prints each resulting DFA as a table.

The implementation explores only reachable subsets. It also includes an optional diagram feature that can generate both the original NFA and the resulting DFA as DOT, SVG, PNG, or PDF files.

## Environment and tools

- Operating system used for development and testing: Ubuntu 24.04.3 LTS
- Programming language: Python 3.12.14
- Required Python packages: none; the program uses only the Python standard library
- Optional diagram renderer: Graphviz (`dot`) for SVG, PNG, and PDF export

The core conversion and DOT diagram generation work on any platform with Python 3.10 or later. Graphviz is not required for the normal assignment output.

## Files

```text
SubsetConstruction/
├── main.py
└── README.md
```

## Input format

The program reads from standard input by default.

1. A positive integer `c`: the number of cases.
2. For each case:
   1. A positive integer `n`: the number of NFA states. The states are `1, 2, ..., n`.
   2. The initial states, separated by spaces.
   3. The alphabet symbols, separated by spaces.
   4. The final states, separated by spaces.
   5. Exactly `n` transition rows. Each row starts with its source state and is followed by one destination set for every alphabet symbol, in the same order as the alphabet.

The empty set is written as `0`. A nonempty transition set is enclosed in braces, and its elements are separated by spaces, for example `{1 3 5}`.

Example input:

```text
1
5
3 5
a b
1 4
1 {1 5} 0
2 {1} 0
3 {2 4} 0
4 0 {5}
5 {1 5} {4}
```

## Output format

For every case, the program prints one DFA table. DFA states are named `D0`, `D1`, and so on, in breadth-first discovery order. The `Subset` column shows which NFA-state subset each name represents.

The `Type` column uses these markers:

- `->`: initial state
- `*`: final state
- `->*`: both initial and final state
- `-`: neither initial nor final

For the example above, the output is:

```text
Case 1
Type  State  Subset     a   b
->    D0     {3 5}      D1  D2
*     D1     {1 2 4 5}  D3  D4
*     D2     {4}        D5  D6
*     D3     {1 5}      D3  D2
*     D4     {4 5}      D3  D4
-     D5     0          D5  D5
-     D6     {5}        D3  D2
```

The program sends normal results only to standard output. Input errors are sent to standard error and cause a nonzero exit status.

## How to run the program

Open a terminal in the `SubsetConstruction` directory.

### Standard assignment execution

```bash
python3 main.py < input.txt
```

On Windows, if the `python3` command is unavailable, use:

```powershell
py main.py < input.txt
```

To save the output:

```bash
python3 main.py < input.txt > output.txt
```

The equivalent explicit file options are:

```bash
python3 main.py --input input.txt --output output.txt
```

### Generate automata diagrams

DOT files require no external Python package:

```bash
python3 main.py --input input.txt --diagram-dir diagrams --diagram-format dot
```

This creates two diagrams for every case:

```text
diagrams/case_1_nfa.dot
diagrams/case_1_dfa.dot
```

To create directly rendered SVG, PNG, or PDF diagrams, install Graphviz first.

macOS with Homebrew:

```bash
brew install graphviz
```

Ubuntu/Debian:

```bash
sudo apt install graphviz
```

Windows with Winget:

```powershell
winget install Graphviz.Graphviz
```

Then select the desired format. SVG is recommended because it stays sharp at any size:

```bash
python3 main.py --input input.txt --diagram-dir diagrams --diagram-format svg
```

The diagram option does not add anything to the DFA tables. Therefore, the required standard output remains clean and follows the assignment specification.

## Algorithm explanation

Let the input NFA be `N = (Q, Σ, Δ, S, F)`.

1. Use the NFA initial-state set `S` as the DFA initial state.
2. Place `S` in a queue of unprocessed DFA states.
3. Remove one subset `T` from the queue.
4. For every symbol `a` in `Σ`, compute the union of all NFA transitions from states in `T`:

   ```text
   move(T, a) = union of Δ(q, a), for every q in T
   ```

5. Record a DFA transition from `T` to `move(T, a)`.
6. If the destination subset has not been discovered before, add it to the DFA and to the queue.
7. Continue until the queue is empty.
8. Mark a DFA subset as final exactly when it contains at least one NFA final state; that is, when `T ∩ F` is not empty.

The empty subset is included when it is reachable. It behaves as a dead state because every transition from it returns to the empty subset.

The queue gives a deterministic breadth-first order, so identical input always receives identical names (`D0`, `D1`, ...).

## Correctness argument

Each DFA state represents exactly the set of NFA states that can be reached after reading the same input prefix. This is true initially because `D0` represents `S`. If a DFA subset `T` correctly represents all NFA states reachable after a prefix `w`, the construction sends it on symbol `a` to the union of `Δ(q, a)` for all `q` in `T`. That union is exactly the set of NFA states reachable after `wa`. By induction on the input length, the DFA and NFA reach corresponding state sets for every word. Finally, a word is accepted by the DFA exactly when its subset contains an NFA final state, which is exactly when the NFA has an accepting computation. Therefore, both automata recognize the same language.

## Complexity

An NFA with `n` states can produce at most `2^n` DFA states. If `r` reachable subsets are actually discovered and the alphabet has `k` symbols, the program processes `r × k` DFA transitions. The subset-union work depends on the number of NFA states and transition targets, while memory is proportional to the reachable DFA states and their transitions.

## Input validation

The program checks that:

- the case and state counts are positive integers;
- referenced states exist;
- alphabet symbols are unique lowercase letters from `a` to `z`;
- each transition row appears in state order;
- every row has exactly one transition set per alphabet symbol;
- there is no unexpected content after the final case.

If validation fails, the program prints a concise error message to standard error and returns exit code `1`.

## Reference

Kozen, Dexter C. (1997). *Automata and Computability*. Springer-Verlag. Lecture 6. <https://doi.org/10.1007/978-1-4612-1844-9>
