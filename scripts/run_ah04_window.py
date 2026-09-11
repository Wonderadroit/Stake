from __future__ import annotations

import argparse

import pandas as pd

from stake.ah04 import build_ah04_windows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build strict AH-04 information-event to Asian-Handicap market windows."
    )
    parser.add_argument("information_csv")
    parser.add_argument("market_csv")
    parser.add_argument("fixtures_csv")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    information = pd.read_csv(args.information_csv)
    market = pd.read_csv(args.market_csv)
    fixtures = pd.read_csv(args.fixtures_csv)

    result = build_ah04_windows(information, market, fixtures)

    print("=== STAKE AH-04-DATA-01 ===")
    print(f"Information events: {len(information)}")
    print(f"Candidate windows:  {len(result)}")
    if not result.empty:
        print(f"With before tick:   {int(result['has_before'].sum())}")
        print(f"With after tick:    {int(result['has_after'].sum())}")
        print(f"With close tick:    {int(result['has_close'].sum())}")
        print(f"Complete windows:   {int((result['has_before'] & result['has_after'] & result['has_close']).sum())}")

    if args.output:
        result.to_csv(args.output, index=False)
        print(f"Wrote:              {args.output}")


if __name__ == "__main__":
    main()
