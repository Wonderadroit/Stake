# STAKE — AGENT OPERATING RULES

This file is the operational contract for any AI agent, developer, or future ChatGPT session working on STAKE.

Read `PROJECT_BIBLE.md` first. It defines the research mission and takes precedence over convenience, speculation, or architectural enthusiasm.

---

## 1. Mission

STAKE is a **sports-betting market-behavior research engine**.

The job is to investigate observable market behavior and determine whether proposed signals survive historical testing, controls, and out-of-sample evaluation.

Do not turn STAKE into a generic betting bot, tipster, guaranteed-profit engine, or unsupported "smart money detector."

---

## 2. First Rule: Inspect Before Building

Never start by adding a new module because the next idea sounds useful.

Before changing code:

```text
1. Read PROJECT_BIBLE.md
2. Read AGENTS.md
3. Check git status
4. Check current branch
5. Inspect recent commits
6. Inspect relevant existing code
7. Inspect existing tests
8. Inspect current historical output
9. State the exact hypothesis
10. Define the control / falsification test
11. Make the smallest justified change
```

If the current evidence does not justify the proposed feature, stop and say so.

---

## 3. Preserve the Current Research Thread

The current research thread is:

```text
bookmaker movement
      ↓
temporal ordering
      ↓
leader / follower
      ↓
convergence
      ↓
persistence / reversal
      ↓
closing line
      ↓
CLV
      ↓
ROI
```

The current question is whether leader/follower information propagation contains predictive information about subsequent market behavior.

Do not replace this with a generic prediction model unless the research evidence requires it.

---

## 4. Current Checkpoint

As of 2026-09-11:

- Repository: `Wonderadroit/Stake`
- Main branch is the active working branch.
- Latest known commit: `d40b2058e94310712ddd59c349042c7e4a46e5ea`
- Latest commit message: `fix: make AH-04 V5 local events independent of T-180 coverage`
- AH-04 V5 local event primitives exist.
- V5.1 local scanning exists.
- Raw sample data is local and intentionally excluded from GitHub.
- Current local raw-data path:
  `data/raw/ah04/sample/sample/EPL/2024-2025`
- Current V5.1 result path:
  `data/ah04_v5_1_scan.csv`

### Immediate next task

**Inspect the V5.1 historical output before implementing a leader/follower V6.**

Do not skip this step.

---

## 5. Required Recovery Procedure for a New Chat

If a new ChatGPT session starts on this repository, it must recover state in this order:

```bash
cd ~/Stake
git status
git log --oneline -10
git pull origin main
pytest -q
PYTHONPATH=. python scripts/run_ah04_v5_1.py
ls -lh data/ah04_v5_1_scan.csv
```

Then inspect the V5.1 output and report:

- number of matches/events;
- event-class distribution;
- representative strong events;
- first-mover information available in the data;
- whether timestamps support propagation measurement;
- what is still missing for a valid leader/follower experiment.

Only after that should implementation begin.

---

## 6. Experimental Build Protocol

For every new research feature:

### Step 1 — State the question

Example:

> Does the first bookmaker to make a sufficiently strong local move predict subsequent cross-book convergence better than a randomly selected bookmaker?

### Step 2 — Define observables

Specify exactly what can be measured at signal time.

### Step 3 — Define the event

Specify timestamps, thresholds, bookmaker identity, direction, and invalid cases.

### Step 4 — Define controls

At minimum, consider an appropriate random or baseline comparison.

### Step 5 — Implement minimally

Prefer one small module or one small scanner modification over a new framework.

### Step 6 — Test

Run unit tests and the historical experiment.

### Step 7 — Inspect failures

Do not hide strange cases. Investigate them.

### Step 8 — Evaluate

Measure the proposed effect and the controls.

### Step 9 — Record the result

State whether the hypothesis was:

- supported provisionally;
- weakened;
- falsified;
- inconclusive;
- or requires more data.

### Step 10 — Commit only coherent work

The repository should remain understandable and reproducible after every meaningful checkpoint.

---

## 7. Do Not Manufacture Events

Never lower a threshold simply because too few events were found.

Never redefine an event after seeing which definition produces the most profitable historical results without a separate validation procedure.

Never add arbitrary fallback logic whose only purpose is to increase signal count.

Low event frequency may be the correct result.

The research question is whether the phenomenon exists, not whether the scanner can produce an impressive number of rows.

---

## 8. Do Not Call It Smart Money

Do not write claims such as:

```text
odds moved → smart money entered
```

Use cautious research terminology:

- price-discovery candidate;
- informed-money candidate;
- leader/follower event;
- persistent convergence;
- reversal;
- isolated-book movement;
- market repricing.

A causal explanation requires evidence beyond the movement itself.

---

## 9. Temporal Integrity

Never use future information to define a signal.

A signal at time `t` may only use information available at or before `t`.

Do not use:

- closing line;
- match result;
- future bookmaker movements;
- future injury/news information;
- future market consensus;

when defining an event that is claimed to predict those variables.

The close is an evaluation target, not a hidden signal input.

---

## 10. Leader Definition

A bookmaker is not a leader merely because it has the most extreme final movement.

A candidate leader should be defined using information available at the first relevant movement time.

The experiment should preserve:

- exact timestamp;
- bookmaker identity;
- pre-move quote;
- post-move quote;
- movement direction;
- movement magnitude;
- elapsed time to next bookmaker;
- number of followers;
- convergence behavior.

If timestamps do not support a reliable distinction between two bookmakers, classify them as simultaneous or ambiguous rather than inventing an ordering.

---

## 11. Controls Are Mandatory

For a leader/follower experiment, consider at least:

```text
A. detected leader
B. random bookmaker control
C. consensus movement without leader identification
D. simultaneous movement control
E. isolated-book movement control
```

The exact controls may change with the data, but a claimed edge must have a credible alternative explanation tested against it.

---

## 12. Historical Data First

STAKE is an empirical project.

Do not rely on simulated data to claim that a market phenomenon exists.

Simulation may be used to validate implementation mechanics, but historical timestamped market data is required to evaluate the real hypothesis.

Whenever possible, test across:

- multiple fixtures;
- multiple bookmakers;
- multiple dates;
- multiple market regimes;
- held-out periods.

---

## 13. Tests Before Claims

Every code change must preserve or improve test coverage.

At minimum:

```bash
pytest -q
```

For relevant experiments, also run the actual scanner and inspect its generated output.

A green unit-test suite does not prove the market hypothesis.

A profitable historical sample does not prove the market hypothesis.

Both software correctness and research validity must be checked separately.

---

## 14. Formula Changes Require Evidence

Do not change probability, odds, handicap, or settlement formulas casually.

Before changing a formula:

1. inspect raw examples;
2. establish the dataset convention;
3. explain the current formula;
4. implement tests;
5. compare historical results before/after;
6. document comparability implications.

Never silently invalidate earlier experiments.

---

## 15. Existing Code Is Evidence

Before replacing an existing component, determine why it exists.

Relevant current modules include:

- `stake/ah04.py`
- `stake/ah04_metrics.py`
- `stake/ah04_v5.py`
- `stake/ah_market_reaction.py`
- `scripts/run_ah04_v5.py`
- `scripts/run_ah04_v5_1.py`
- `tests/test_ah04.py`

Do not duplicate existing functionality without a clear reason.

Do not delete an old experiment merely because a newer experiment is preferred. Historical experiments are part of the research record unless there is a demonstrated correctness problem.

---

## 16. Repository Hygiene

Raw data remains outside Git when intentionally gitignored.

Do not commit:

- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- large raw datasets;
- generated outputs unless they are intentionally part of the repository artifact;
- secrets or credentials.

Keep experiment outputs reproducible through scripts and documentation.

---

## 17. No Architecture for Architecture's Sake

Avoid creating:

- unnecessary abstractions;
- generic frameworks before the experiment is understood;
- speculative configuration systems;
- large class hierarchies;
- unused interfaces;
- multiple layers that merely rename the same operation.

The preferred implementation is the smallest one that can answer the research question reliably.

---

## 18. How to Interpret Results

Use language proportional to evidence.

### Stronger

> "The leader/follower event showed higher subsequent closing-line movement than the specified controls in the tested sample."

### Weaker

> "The result is consistent with price discovery, but causality is not established."

### Do not say

> "We proved smart money moved the market."

Unless a future experiment genuinely establishes something stronger, STAKE should remain conservative.

---

## 19. Required Experiment Report

After a meaningful experiment, report:

```text
HYPOTHESIS:

DATASET:

SAMPLE SIZE:

EVENT DEFINITION:

CONTROL(S):

RESULT:

CLV RESULT:

ROI RESULT:

OUT-OF-SAMPLE RESULT:

FAILURE CASES:

INTERPRETATION:

DECISION:

NEXT EXPERIMENT:
```

If a metric is unavailable, say `NOT YET MEASURED`. Do not invent it.

---

## 20. When the User Says "Continue"

When instructed to continue, do not interpret that as permission to build indefinitely.

Continue the **current research thread** until the next defensible checkpoint.

The agent should stop after reaching a meaningful state such as:

- implementation complete;
- tests complete;
- historical experiment complete;
- result interpreted;
- checkpoint documented.

If the next step requires missing data or an unresolved definition, stop at the blocker and state exactly what is missing.

---

## 21. When the User Says "Do It All"

Complete all steps that can be responsibly completed without fabricating evidence.

This means:

- inspect;
- implement;
- test;
- run historical data;
- analyze;
- document.

It does **not** mean:

- invent data;
- claim unmeasured ROI;
- pretend a local sample represents the entire market;
- bypass controls;
- manufacture positive results.

---

## 22. Definition of Done

A research feature is not done merely because the code runs.

It is done when:

```text
code
 ↓
tests
 ↓
historical experiment
 ↓
controls
 ↓
result
 ↓
interpretation
 ↓
reproducible checkpoint
```

has been completed to the extent supported by available data.

---

## 23. Current Next Action

**Do not implement V6 yet.**

First inspect the actual V5.1 output generated from the local raw dataset.

Run:

```bash
cd ~/Stake
git pull origin main
pytest -q
PYTHONPATH=. python scripts/run_ah04_v5_1.py

python - <<'PY'
import pandas as pd
p = "data/ah04_v5_1_scan.csv"
df = pd.read_csv(p)
print("=== EVENT CLASSES ===")
print(df["event_class"].value_counts(dropna=False).to_string())
print("\n=== EVENTS ===")
cols = [
    "fixture", "teams", "peak_books_1m", "peak_direction_1m",
    "first_line_change", "pressure_before_line",
    "line_before_pressure", "event_class"
]
print(df[cols].to_string(index=False))
PY
```

Then inspect representative raw timestamp sequences for the strongest events.

Only after that should the leader/follower event definition be finalized.

---

## 24. Recovery Principle

If context is lost, do not guess what STAKE was doing.

Read:

1. `PROJECT_BIBLE.md`
2. `AGENTS.md`
3. recent git history
4. current tests
5. current experiment output

Then resume from the documented checkpoint.

**The repository and its evidence are the source of truth.**
