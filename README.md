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

## Current experiment

The first diagnostic path is a deliberately simple O/U 2.5 model:

1. Estimate expected home and away goals from prior venue-specific results only.
2. Convert expected total goals to `P(Over 2.5)` with a transparent Poisson calculation.
3. Compare that probability with the opening market's fair probability.
4. Evaluate chronologically on historical matches.
5. Record candidate-bet ROI only when model probability implies at least 3% expected value at the opening price.

Run it locally after downloading the Football-Data season files into `data/raw/`:

```bash
python scripts/run_ou_experiment.py
```

This is intentionally a falsification experiment, not a claim of profitability.

## Falsification rule

If diagnostic reasoning does not improve out-of-sample calibration or market-relative performance over a simple baseline, stop expanding the system.

## Design principle

Evidence → System Model → Competing Hypotheses → Diagnostic Separation → Probability → Market Price → Decision → Result → Failure Analysis
