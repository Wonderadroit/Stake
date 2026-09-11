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

These failures are retained deliberately. The project must not tune thresholds or add features merely to rescue a failed experiment.

### AH-01 — walk-forward handicap diagnostic

The next probe asks whether a simple pre-match goal model can identify useful disagreement with the opening Asian Handicap.

1. Estimate expected home and away goals from matches strictly before each fixture.
2. Convert those estimates into an independent Poisson goal distribution.
3. Calculate expected Asian Handicap settlement for the published opening handicap, including quarter lines.
4. Compare expected settlement with the actual opening price to identify model-EV candidates.
5. Bucket model-vs-handicap expected-goal-margin gaps without optimizing the buckets from results.
6. Evaluate realized AH settlement and opening-price ROI chronologically.

Run locally after downloading the Football-Data season files into `data/raw/`:

```bash
python scripts/run_ah_experiment.py
```

AH settlement is treated correctly as win, half-win, push, half-loss, or loss. Closing prices and post-match statistics are excluded from the decision.

## Falsification rule

If diagnostic reasoning does not improve out-of-sample calibration or market-relative performance over a simple baseline, stop expanding the system.

A positive result in one bucket is not enough. Results must be robust, out-of-sample, economically meaningful, and survive pre-specified tests without threshold hunting.

## Design principle

Evidence → System Model → Competing Hypotheses → Diagnostic Separation → Probability → Market Price → Decision → Result → Failure Analysis
