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

    print("=== STAKE AH-01 WALK-FORWARD DIAGNOSTIC PROBE ===")
    print(f"Matches loaded: {len(frame)}")
    print(f"Valid AH observations: {result.observations}")
    print()
    print("The model uses only matches before each fixture.")
    print("AH settlement handles wins, half-wins, pushes, half-losses and losses.")
    print("No closing price or post-match statistic is used for the decision.")
    print()
    print("GAP BUCKETS")
    print("Magnitude | Observations | Mean abs gap | Positive settle | Opening ROI")
    print("----------+--------------+--------------+-----------------+------------")
    for bucket in result.buckets:
        print(
            f"{bucket.label:>9} | {bucket.observations:12d} | "
            f"{bucket.mean_abs_gap:12.4f} | "
            f"{bucket.positive_settlement_rate:15.2%} | "
            f"{bucket.opening_roi:10.2%}"
        )

    print()
    print("MODEL-EV CANDIDATES")
    print(f"Minimum EV: 3.0%")
    print(f"Count:      {result.candidate_bets}")
    if result.candidate_roi is None:
        print("ROI:        n/a")
    else:
        print(f"ROI:        {result.candidate_roi:.2%}")

    print()
    nonempty = [b for b in result.buckets if b.observations]
    if not nonempty:
        print("VERDICT: no usable AH observations.")
        return

    if len(nonempty) >= 2 and nonempty[-1].opening_roi > nonempty[0].opening_roi:
        print("VERDICT: larger model-vs-handicap gaps are not yet falsified; inspect before continuing.")
    else:
        print("VERDICT: larger model-vs-handicap gaps do not show a positive directional signal yet.")


if __name__ == "__main__":
    main()
