from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stake.data import load_seasons
from stake.ou_disagreement import evaluate_ou_disagreement


def main() -> None:
    paths = sorted(ROOT.joinpath("data", "raw").glob("E0_*.csv"))
    if not paths:
        raise SystemExit("No data/raw/E0_*.csv files found")

    frame = load_seasons(paths)
    result = evaluate_ou_disagreement(frame, window=10)

    print("=== STAKE O/U-02 MARKET DISAGREEMENT PROBE ===")
    print(f"Matches loaded: {len(frame)}")
    print(f"Valid disagreement observations: {result.observations}")
    print()
    print("The direction is chosen only from the walk-forward model minus the")
    print("opening market probability. No result or closing price is used.")
    print()
    print("BUCKETS")
    print("Magnitude | Observations | Mean abs gap | Win rate | Opening ROI")
    print("----------+--------------+--------------+----------+------------")
    for bucket in result.buckets:
        print(
            f"{bucket.label:>9} | {bucket.observations:12d} | "
            f"{bucket.mean_gap:12.4%} | {bucket.win_rate:8.2%} | "
            f"{bucket.realized_roi:10.2%}"
        )

    print()
    if not result.buckets:
        print("VERDICT: no usable disagreement observations.")
        return

    first = result.buckets[0]
    largest = result.buckets[-1]
    if largest.realized_roi > first.realized_roi:
        print("VERDICT: larger disagreement is directionally more promising; continue testing.")
    else:
        print("VERDICT: larger disagreement does not show a positive directional signal yet.")


if __name__ == "__main__":
    main()
