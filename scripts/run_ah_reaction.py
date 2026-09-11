from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stake.ah_market_reaction import evaluate_ah_market_reaction
from stake.data import load_seasons


def main() -> None:
    paths = sorted(ROOT.joinpath("data", "raw").glob("E0_*.csv"))
    if not paths:
        raise SystemExit("No data/raw/E0_*.csv files found")

    frame = load_seasons(paths)
    result = evaluate_ah_market_reaction(frame, window=10)

    print("=== STAKE AH-03 OPENING -> CLOSING MARKET REACTION ===")
    print(f"Matches loaded: {len(frame)}")
    print(f"Valid AH opening/closing observations: {result.observations}")
    print(f"Directional observations: {result.directional_observations}")
    print()
    print("The model uses only matches strictly before each fixture.")
    print("Opening AH line/prices define the model disagreement.")
    print("Closing AH prices are used only as the subsequent market-reaction outcome.")
    print("No closing price is used to choose the model direction.")
    print()
    print("MARKET REACTION")
    print(f"Model-direction accuracy:       {result.direction_accuracy:.2%}")
    print(f"Mean home probability movement: {result.mean_home_probability_move:+.3%}")
    print()
    print("GAP BUCKETS")
    print("Magnitude | Observations | Mean abs gap | Direction accuracy | Mean home prob move")
    print("----------+--------------+--------------+--------------------+--------------------")
    for bucket in result.buckets:
        print(
            f"{bucket.label:>9} | {bucket.observations:12d} | "
            f"{bucket.mean_abs_gap:12.4f} | {bucket.model_direction_rate:18.2%} | "
            f"{bucket.mean_home_probability_move:+18.3%}"
        )

    print()
    print("Interpretation: this is a market-information test, not a betting rule.")
    print("If disagreement does not predict subsequent repricing, do not treat it as an edge.")


if __name__ == "__main__":
    main()
