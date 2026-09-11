# STAKE Experiment 01 — Temporal Ordering / Leader-Follower

## Status

**PREREGISTERED / NOT YET RUN ON FINAL RAW DATA**

Date: 2026-09-11

## Question

Does the first reliably observable bookmaker repricing event contain information about subsequent cross-book market movement beyond credible controls?

## Primary null

**H0-A:** After accounting for timestamp resolution, synchronized repricing, random ordering, and consensus movement, the detected first mover does not produce a reproducible increase in subsequent same-direction follower behavior or market displacement relative to controls.

## Secondary economic null

**H0-B:** Even if temporal structure exists, it does not produce economically meaningful value after realistic price availability, vig/commission, latency, limits, slippage, and execution assumptions.

## Scope

First clean implementation target:

- market: one fixed pre-match market;
- initial benchmark: EPL 1X2 where suitable timestamped data exists;
- historical period: one fixed season/data window;
- bookmakers: all eligible books with sufficient coverage;
- no sport-specific tuning during the first common test.

The same methodology may later be applied to Championship 1X2 and men's Grand Slam match winner.

## Gate 0 — Data integrity

Before the experiment, run:

```bash
python scripts/run_timestamp_audit.py
```

The audit must establish:

- timestamp semantics;
- timestamp resolution;
- duplicate timestamp rate;
- same-timestamp cross-book rate;
- inter-observation gap distribution;
- bookmaker/fixture coverage;
- ordering ambiguity;
- horizon measurability.

If the source only supplies observation timestamps, the experiment must say so explicitly. It must not claim those timestamps are true bookmaker-event timestamps.

## Signal definition

A candidate leader is the first **reliably observable** qualifying movement at time `t0` under the frozen movement rule.

A qualifying movement must specify:

- market/selection;
- bookmaker;
- previous observable quote;
- new observable quote;
- direction;
- movement magnitude;
- timestamp;
- minimum timestamp-resolution requirement.

The leader is not selected using its eventual movement, closing price, match result, or future followers.

If multiple books cannot be ordered at the available resolution, classify them as `SIMULTANEOUS` or `AMBIGUOUS`.

## Outcomes

Primary structural outcomes:

1. follower rate;
2. median/mean leader-to-follower lag;
3. number of same-direction followers;
4. cross-book dispersion change;
5. subsequent consensus displacement.

Secondary outcomes:

- persistence;
- reversal;
- closing-line displacement;
- CLV from signal-time price.

Economic outcome:

- executable value / ROI only after realistic assumptions are specified.

## Horizons

Candidate horizons are:

```text
+5s
+15s
+30s
+60s
+180s
close
```

A horizon is only evaluated if Gate 0 establishes that the data can resolve it. Otherwise report `NOT MEASURABLE`.

## Controls

At minimum:

1. detected leader;
2. random bookmaker control;
3. consensus movement without leader identification;
4. simultaneous movement control;
5. isolated-book movement control;
6. randomized ordering/null where valid.

## Leakage prevention

The signal may use only information available at or before `t0`.

Forbidden:

- future followers to define the leader;
- closing line to define the event;
- match result;
- future market consensus;
- future news/injury information.

## Effect-size requirement

Report market-unit effect sizes, not only p-values.

Examples:

- seconds of lead/lag;
- follower percentage points;
- consensus probability displacement;
- odds displacement;
- CLV units.

## Validation

Use chronological discovery/holdout where sample size permits:

```text
discovery period
    ↓
freeze definition
    ↓
held-out period
```

Do not tune the signal on the final evaluation period.

## Decision rules

The experiment can end in any of these states:

- **KILL** — no credible temporal structure;
- **RETAIN AS RESEARCH FINDING** — structure exists but no economic value is demonstrated;
- **REDIRECT TO SOFTER MARKET** — structure is weak in the benchmark but another market has a justified data-quality/structure case;
- **PROCEED TO ECONOMIC TEST** — structure and predictive price effect survive controls and are worth realistic execution testing.

A statistically significant result alone is insufficient for the final decision.

## Required final report

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
