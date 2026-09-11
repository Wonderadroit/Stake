# Stake — Sports Diagnostic Falsification Lab

This repository is an experiment, not a betting bot.

## Objective

Test whether CYDRA-style causal/diagnostic reasoning can identify information that is not already reflected in sports betting prices.

The project must be willing to conclude that the idea does **not** work.

## V0.1 scope

- Historical pre-match data only
- Soccer first
- Asian Handicap and goal totals
- Chronological/out-of-sample validation
- Market-implied probability baseline
- Transparent diagnostic features
- Explicit competing hypotheses
- PASS decisions when evidence is insufficient
- ROI, calibration and closing-line analysis
- No automated wagering
- No fabricated historical data

## Experiment status

### O/U-01 — simple goal model

A walk-forward expected-goals model was compared with the opening O/U 2.5 market.

Result: **failed**. The model had worse Brier score and log loss than the market baseline, and model-EV candidates at a 3% threshold returned negative ROI.

### O/U-02 — model/market disagreement

The same walk-forward model was used only to choose direction from the gap between model probability and opening market probability. Disagreement was tested in fixed magnitude buckets.

Result: **failed to show a useful directional relationship**. The largest disagreement bucket was materially worse than the smallest bucket, so disagreement magnitude was not treated as evidence of edge.

### AH-00 — market baseline

The opening AH market was measured before adding any diagnostic model. Across the five-season sample, the market showed the expected bookmaker drag and near-zero average AH closing-value movement. This is the reference point for all AH diagnostics.

### AH-01 — walk-forward handicap gap probe

A simple pre-match goal model was compared with the opening Asian Handicap using model expected-margin minus the published handicap.

Result: **failed/inconclusive as an edge generator**. Large disagreement did not translate into better realized ROI, and the initial proxy was not accepted as a probability model.

### AH-02 — exact settlement distribution

AH-01 was hardened by replacing the directional proxy with an exact Poisson scoreline distribution mapped into full-win, half-win, push, half-loss and full-loss settlement probabilities.

Result: **failed**. The largest model-vs-handicap gap bucket had strongly negative model EV, and the broad 3% model-EV candidate set was not profitable enough to establish an edge. No threshold tuning or ML rescue was performed.

### AH-03 — opening → closing market reaction

The diagnostic asked whether opening AH disagreement predicted subsequent market repricing.

The test used only pre-fixture information for model direction, then measured normalized home/away AH probability movement from opening to closing. The standard Football-Data E0 files provide one AH handicap line plus opening and closing AH prices, not a separate closing handicap line, so no closing handicap was invented.

Result: **failed**. Direction accuracy was only 51.77% across 1,835 directional observations, with no robust monotonic relationship across fixed disagreement buckets. The simple team-history → Poisson → AH pathway was therefore frozen.

### AH-04-PROVENANCE-01 — information timestamp feasibility

Before attempting an information-latency model, Stake now has a hard provenance gate. A candidate dataset must explicitly provide:

- fixture ID
- kickoff timestamp
- information-event timestamp
- decision timestamp
- market timestamp
- market prices

A row is eligible only when:

```text
information_timestamp <= decision_timestamp < kickoff_timestamp
market_timestamp <= kickoff_timestamp
```

Stake does **not** infer or invent publication times. Missing timestamps and temporal violations are rejected.

Run against a candidate CSV with explicit timestamps:

```bash
python scripts/run_provenance_audit.py path/to/candidate.csv
```

This is a feasibility audit, not a prediction model. A PASS means the dataset is structurally capable of supporting AH-04; it does not establish that a market inefficiency exists.

## Current scoreboard

| Experiment | Question | Status |
|---|---|---|
| AH-00 | Is there an obvious blind AH market edge? | DONE — no trivial edge |
| O/U-01 | Does a simple goal model beat O/U market? | FAIL |
| O/U-02 | Does larger O/U disagreement predict direction? | FAIL |
| AH-01 | Does model-vs-AH gap identify value? | FAIL / INCONCLUSIVE |
| AH-02 | Does exact Poisson AH settlement improve that? | FAIL |
| AH-03 | Does model disagreement predict subsequent market repricing? | FAIL |
| AH-04-PROVENANCE-01 | Can information timing be proven without look-ahead? | IN PROGRESS — gate implemented |

## Falsification rule

If diagnostic reasoning does not improve out-of-sample calibration or market-relative performance over a simple baseline, stop expanding the system.

A positive result in one bucket is not enough. Results must be robust, out-of-sample, economically meaningful, and survive pre-specified tests without threshold hunting.

## Design principle

Evidence → System Model → Competing Hypotheses → Diagnostic Separation → Probability → Market Price → Decision → Result → Failure Analysis
