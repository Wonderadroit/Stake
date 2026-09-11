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

The next diagnostic asks a narrower causal question: when the pre-match model disagrees with the opening AH, does the market subsequently reprice in that model's direction?

The test:

1. Build the goal model strictly from matches before the fixture.
2. Compare model expected margin with the **opening** AH line.
3. Freeze that disagreement and its direction.
4. Measure only afterward whether normalized home/away AH probability moves from opening to closing in the predicted direction.
5. Bucket the result by fixed disagreement magnitude.

The standard Football-Data E0 files provide one AH handicap line plus opening and closing AH prices, but not a separate closing handicap line. Therefore AH-03 measures subsequent repricing through normalized two-way probability rather than inventing a closing handicap.

Run locally:

```bash
python scripts/run_ah_reaction.py
```

Closing prices are an **outcome/market-reaction benchmark only**. They must never influence the original model direction.

## Current scoreboard

| Experiment | Question | Status |
|---|---|---|
| AH-00 | Is there an obvious blind AH market edge? | DONE — no trivial edge |
| O/U-01 | Does a simple goal model beat O/U market? | FAIL |
| O/U-02 | Does larger O/U disagreement predict direction? | FAIL |
| AH-01 | Does model-vs-AH gap identify value? | FAIL / INCONCLUSIVE |
| AH-02 | Does exact Poisson AH settlement improve that? | FAIL |
| AH-03 | Does model disagreement predict subsequent market repricing? | NEXT |

## Falsification rule

If diagnostic reasoning does not improve out-of-sample calibration or market-relative performance over a simple baseline, stop expanding the system.

A positive result in one bucket is not enough. Results must be robust, out-of-sample, economically meaningful, and survive pre-specified tests without threshold hunting.

## Design principle

Evidence → System Model → Competing Hypotheses → Diagnostic Separation → Probability → Market Price → Decision → Result → Failure Analysis
