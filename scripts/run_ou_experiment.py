from __future__ import annotations

import sys
from pathlib import Path

# Allow direct execution from the repository root:
#   python scripts/run_ou_experiment.py
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stake.data import load_seasons
from stake.ou_backtest import evaluate_ou_walk_forward


def main() -> None:
    paths = sorted(ROOT.joinpath("data", "raw").glob("E0_*.csv"))
    if not paths:
        raise SystemExit("No data/raw/E0_*.csv files found")

    frame = load_seasons(paths)
    result = evaluate_ou_walk_forward(frame, window=10, min_ev=0.03)

    print("=== STAKE O/U 2.5 WALK-FORWARD EXPERIMENT ===")
    print(f"Matches loaded: {len(frame)}")
    print(f"Valid model/market observations: {result.observations}")
    print()
    print("MODEL")
    print(f"Brier:   {result.model_brier:.6f}")
    print(f"LogLoss: {result.model_log_loss:.6f}")
    print()
    print("MARKET")
    print(f"Brier:   {result.market_brier:.6f}")
    print(f"LogLoss: {result.market_log_loss:.6f}")
    print()
    print("CANDIDATE BETS")
    print("Minimum EV: 3.0%")
    print(f"Count:      {result.candidate_bets}")
    if result.candidate_roi is None:
        print("ROI:        no candidates")
    else:
        print(f"ROI:        {result.candidate_roi:.2%}")

    brier_delta = result.market_brier - result.model_brier
    logloss_delta = result.market_log_loss - result.model_log_loss
    print()
    print("MODEL - MARKET")
    print(f"Brier improvement:   {brier_delta:+.6f}")
    print(f"LogLoss improvement: {logloss_delta:+.6f}")

    if brier_delta <= 0 and logloss_delta <= 0:
        print("\nVERDICT: diagnostic goal model does not beat the market baseline.")
    else:
        print("\nVERDICT: signal detected; continue to deeper out-of-sample testing.")


if __name__ == "__main__":
    main()
