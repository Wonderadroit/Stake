from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stake.ah_backtest import evaluate_ah_walk_forward
from stake.data import load_seasons


def main() -> None:
    paths = sorted(ROOT.joinpath("data", "raw").glob("E0_*.csv"))
    if not paths:
        raise SystemExit("No data/raw/E0_*.csv files found")

    frame = load_seasons(paths)
    result = evaluate_ah_walk_forward(frame, window=10, min_ev=0.03)

    print("=== STAKE AH-02 EXACT SETTLEMENT-PROBABILITY PROBE ===")
    print(f"Matches loaded: {len(frame)}")
    print(f"Valid AH observations: {result.observations}")
    print()
    print("The model uses only matches strictly before each fixture.")
    print("Poisson goals are converted directly into full/half/push AH outcomes.")
    print("Opening odds are used only after the model distribution is frozen.")
    print("No closing price or post-match statistic is used for the decision.")
    print()
    print("GAP BUCKETS")
    print("Magnitude | Observations | Mean abs gap | Mean model EV | Positive settle | Opening ROI")
    print("----------+--------------+--------------+---------------+-----------------+------------")
    for bucket in result.buckets:
        print(
            f"{bucket.label:>9} | {bucket.observations:12d} | "
            f"{bucket.mean_abs_gap:12.4f} | {bucket.mean_model_ev:13.2%} | "
            f"{bucket.positive_settlement_rate:15.2%} | {bucket.opening_roi:10.2%}"
        )

    print()
    print("MODEL-EV CANDIDATES")
    print("Minimum EV: 3.0%")
    print(f"Count:      {result.candidate_bets}")
    print("ROI:        n/a" if result.candidate_roi is None else f"ROI:        {result.candidate_roi:.2%}")
    print()
    print("Interpretation: the exact settlement distribution, not a directional score,")
    print("determines model EV. This experiment is still a falsification probe, not a betting rule.")


if __name__ == "__main__":
    main()
