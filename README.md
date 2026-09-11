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

## Falsification rule

If diagnostic reasoning does not improve out-of-sample calibration or market-relative performance over a simple baseline, stop expanding the system.

## Design principle

Evidence → System Model → Competing Hypotheses → Diagnostic Separation → Probability → Market Price → Decision → Result → Failure Analysis
