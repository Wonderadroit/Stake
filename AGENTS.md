# STAKE — AGENT OPERATING RULES

This file is the operational contract for any AI agent, developer, or future ChatGPT session working on STAKE.

**Read `PROJECT_BIBLE.md` first.** It is the research authority. This file defines how to execute that doctrine without inventing evidence or building architecture ahead of the experiment.

---

## 1. Mission

STAKE is a sports-market behavior research engine.

The agent's job is to:

```text
inspect → measure → falsify → validate → document
```

Do not turn STAKE into a generic betting bot, tipster, guaranteed-profit engine, or unsupported smart-money detector.

---

## 2. Non-Negotiable Rules

1. **Evidence before explanation.**
2. **Data integrity is a gate, not a footnote.**
3. **Temporal ordering must be measurable before causal language is used.**
4. **Effect size matters, not only statistical significance.**
5. **Controls are mandatory for claimed structure.**
6. **CLV is not ROI.**
7. **ROI is not proof of durability.**
8. **Future information must never define a signal.**
9. **Raw data limitations must be reported explicitly.**
10. **Never manufacture event counts, timestamps, leaders, or economic results.**
11. **Do not optimize thresholds against the final evaluation sample.**
12. **Do not build architecture that the current experiment does not require.**
13. **Negative results are first-class research output.**
14. **When a phenomenon cannot be distinguished because of timestamp resolution, classify it as simultaneous/ambiguous.**
15. **Never call an odds movement proof of smart money.**

---

## 3. Recovery Protocol

For a new session:

```bash
cd ~/Stake
git status
git log --oneline -12
git pull origin main
pytest -q
```

Then read:

```text
PROJECT_BIBLE.md
AGENTS.md
relevant experiment code
relevant tests
current experiment outputs
```

Do not rely on memory when the repository can establish the state.

---

## 4. Research Gates

Every new market-signal branch follows this order:

```text
GATE 0  DATA INTEGRITY
  ↓
GATE 1  TEMPORAL STRUCTURE
  ↓
GATE 2  PREDICTIVE / PRICE EFFECT
  ↓
GATE 3  ECONOMIC VALUE
  ↓
GATE 4  OUT-OF-SAMPLE VALIDATION
```

A later gate cannot rescue a failed earlier gate.

If Gate 0 fails, stop and fix/replace the data source.

If Gate 1 fails, do not build a prediction or betting strategy on the supposed leader/follower structure.

If Gate 2 fails, temporal ordering may exist but is not useful for the proposed prediction.

If Gate 3 fails, retain the structure only as a research finding or redirect to a different market.

---

## 5. Phase 0 — Timestamp Audit

Before implementing V6 or any new leader/follower engine, run the timestamp audit on actual local raw data.

The audit must answer:

- What does the timestamp mean?
- What is its resolution?
- How often are timestamps duplicated within a bookmaker?
- How often do bookmakers share the same timestamp?
- What are median/p95/p99 inter-observation gaps?
- What fraction of candidate events can support 5s, 15s, 30s, 60s, 180s horizons?
- Is bookmaker ordering actually observable?
- Are there source/observation/ingestion clocks?
- Are there polling/snapshot artifacts?
- Is kickoff handling correct?

### Required interpretation

A timestamp field does **not** automatically mean the bookmaker changed its price at that exact instant.

If only an observation timestamp exists, call it observation time.

If source-event time is unavailable, record that limitation in every affected experiment.

### Minimum output

```text
ROWS
BOOKMAKERS
FIXTURES
TIMESTAMP_RESOLUTION
DUPLICATE_RATE
MEDIAN_GAP
P95_GAP
P99_GAP
SAME_TIMESTAMP_RATE
ORDERING_AMBIGUITY_RATE
HORIZON_MEASURABILITY
PROVENANCE_STATUS
```

Do not run the audit on a synthetic or guessed dataset and present it as historical evidence.

---

## 6. Phase 1 — Leader/Follower Test

Only after Phase 0 establishes adequate resolution.

Define a qualifying movement before seeing outcomes.

A candidate leader is:

> the first reliably observable bookmaker movement satisfying the fixed movement rule at time `t0`.

Never define a leader as the bookmaker that eventually moved the most.

For every candidate event retain:

```text
fixture
market
selection
leader_book
signal_time
previous_time
post_time
movement_direction
movement_size
probability_change
pre_event_dispersion
follower_count
follower_deltas
```

If two events cannot be ordered at the source resolution:

```text
SIMULTANEOUS / AMBIGUOUS
```

not `leader` and `follower`.

---

## 7. Controls

A leader/follower result is not credible without alternative explanations.

Use the smallest appropriate set, normally including:

```text
A  detected leader
B  random bookmaker control
C  consensus movement without leader identification
D  simultaneous movement control
E  isolated-book movement control
F  time/bookmaker randomized null where valid
```

Controls must be constructed without future leakage.

---

## 8. Effect Size and Decay

Every experiment must report market-unit effect size.

Do not report only:

```text
p = 0.003
```

Also report something interpretable such as:

```text
median lead-lag = X seconds
follower rate = Y%
consensus displacement = Z percentage points
CLV = Q units
```

Measure fixed horizons only when the data can resolve them.

Preferred conceptual horizons:

```text
+5s +15s +30s +60s +180s close
```

If resolution cannot support a horizon, output `NOT MEASURABLE`.

Do not select the best-looking horizon after seeing results and call it confirmatory.

---

## 9. CLV / Economics

Prepare the economic test before final Gate 2 evaluation.

The agent must distinguish:

```text
TEMPORAL STRUCTURE
PREDICTIVE EFFECT
CLV
EXECUTABILITY
ROI
```

Never use a universal arbitrary CLV kill threshold.

Economic assumptions must be tied to:

- actual market;
- price convention;
- vig/commission;
- latency;
- limits;
- slippage;
- execution probability;
- minimum practical edge.

If those inputs are unavailable, mark the economic result `NOT MEASURED`.

---

## 10. Cross-Market Protocol

Do not move to another sport simply because it sounds softer.

Once a common method is frozen, compare:

1. EPL 1X2 — benchmark/control.
2. Championship 1X2 — secondary-market candidate.
3. Men's Grand Slam match winner — two-outcome candidate.

The same core definitions must be preserved.

No sport-specific threshold tuning before the common comparison is complete.

A market may be promoted only if evidence shows better:

- timestamp quality;
- temporal structure;
- effect size;
- persistence/decay;
- CLV;
- execution feasibility.

---

## 11. "Smart Money" Language Rule

Never write:

```text
odds moved → smart money entered
```

Allowed:

- market repricing;
- price-discovery candidate;
- leader/follower event;
- informed-money candidate;
- persistent convergence;
- reversal;
- isolated-book movement.

The explanation must remain probabilistic unless independent evidence identifies information arrival or order flow.

---

## 12. Leakage Rules

A signal at time `t0` may use only information available at or before `t0`.

Forbidden signal inputs:

- closing price;
- future bookmaker movements;
- match outcome;
- post-event consensus;
- future injury/news information;
- future leader identity.

The closing line is an evaluation target.

---

## 13. Existing Code Preservation

Inspect before replacing.

Known AH-04 components:

```text
stake/ah04.py
stake/ah04_metrics.py
stake/ah04_v5.py
stake/ah_market_reaction.py
scripts/run_ah04_v5.py
scripts/run_ah04_v5_1.py
tests/test_ah04.py
```

Historical experiments must remain reproducible unless there is a demonstrated correctness issue.

Do not create duplicate abstractions merely to rename existing functions.

---

## 14. Current V5/V5.1 State

V5/V5.1 local movement primitives exist.

Current pressure threshold:

```text
0.015
```

Do not lower it to manufacture events.

Recent temporal output with overwhelmingly `OVERLAPPING` observations is treated as a resolution/data-semantics warning, not proof of causality.

The repository's raw AH-04 sample is intentionally gitignored:

```text
data/raw/ah04/sample/sample/EPL/2024-2025
```

Therefore a GitHub-only session cannot truthfully claim to have run the raw timestamp audit.

---

## 15. Current Execution Order

The immediate work sequence is now fixed:

```text
1. Timestamp/provenance audit
2. Freeze measurable resolution
3. Define leader event
4. Define controls
5. Run leader/follower structure test
6. Measure effect + decay
7. Evaluate CLV
8. Evaluate realistic economics
9. Hold out later data
10. Decide: KILL / RESEARCH FINDING / REDIRECT / PROCEED
```

Do not jump to V6 architecture before step 1.

---

## 16. Timebox

The movement-research branch is timeboxed to approximately 4–6 focused weeks.

The goal is a decision, not a giant taxonomy.

If the clean experiment fails, stop expanding that branch.

---

## 17. Build Protocol

For every implementation request:

### A. Inspect

Check status, history, relevant files, tests, and outputs.

### B. State the exact question

One sentence. If it cannot be stated clearly, do not code.

### C. Define observables

Specify what exists at signal time.

### D. Define null/control

Specify what would count as failure.

### E. Implement minimally

Prefer one script/module/test set over a framework.

### F. Test software

```bash
pytest -q
```

### G. Run the historical experiment

Use real local historical data.

### H. Inspect failures and edge cases

Do not suppress anomalies merely because they are inconvenient.

### I. Report

Use the required experiment report format.

### J. Commit coherent work

The repository should remain recoverable from Git after each checkpoint.

---

## 18. Required Experiment Report

```text
QUESTION:
HYPOTHESIS:
DATASET:
DATA INTEGRITY:
TIMESTAMP RESOLUTION:
SAMPLE SIZE:
EVENT DEFINITION:
CONTROLS:
PRIMARY EFFECT:
EFFECT SIZE:
DECAY:
CLV:
EXECUTION ASSUMPTIONS:
ROI:
OUT-OF-SAMPLE:
FAILURE CASES:
INTERPRETATION:
DECISION:
NEXT ACTION:
```

Never fill a field with an invented value.

---

## 19. "Continue" Protocol

When the user says `continue`, continue the current research thread only until the next defensible checkpoint.

Do not interpret `continue` as permission to build indefinitely.

Stop at:

- a completed implementation;
- a completed experiment;
- a decisive failure;
- a data blocker;
- or a documented checkpoint.

If data is missing, say exactly what is missing and give the shortest command needed to provide it.

---

## 20. "Do It All" Protocol

When the user says `do it all`, complete every responsible step available:

```text
inspect
implement
test
run
analyze
document
```

But never:

- invent raw data;
- fabricate timestamps;
- claim unmeasured ROI;
- bypass controls;
- turn a descriptive movement into a causal claim;
- claim a market-wide conclusion from a small sample.

---

## 21. Definition of Done

A research feature is done only when the evidence chain is complete to the extent the data permits:

```text
CODE
 ↓
TESTS
 ↓
HISTORICAL RUN
 ↓
CONTROLS
 ↓
EFFECT
 ↓
INTERPRETATION
 ↓
REPRODUCIBLE CHECKPOINT
```

A green test suite means the software is behaving as coded. It does not prove the market hypothesis.

---

## 22. Recovery Principle

If context is lost:

```text
PROJECT_BIBLE.md
↓
AGENTS.md
↓
git history
↓
current tests
↓
current data/output
↓
resume from evidence
```

**The repository and measured data are the source of truth.**
