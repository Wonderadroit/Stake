from __future__ import annotations

import argparse

import pandas as pd

from stake.provenance import audit_information_provenance


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit AH-04 information timestamp provenance")
    parser.add_argument("csv", help="CSV containing explicit provenance timestamps")
    args = parser.parse_args()

    frame = pd.read_csv(args.csv)
    result = audit_information_provenance(frame)

    print("=== STAKE AH-04-PROVENANCE-01 ===")
    print(f"Rows:                         {result.rows}")
    print(f"Valid rows:                   {result.valid_rows}")
    print(f"Invalid rows:                 {result.invalid_rows}")
    print(f"Rows missing timestamps:      {result.missing_timestamp_rows}")
    print(f"Ordering violations:          {result.ordering_violation_rows}")
    print(f"Information timestamps:       {result.information_timestamp_rows}")
    print(f"Market timestamps:            {result.market_timestamp_rows}")
    print(f"STATUS:                       {result.status}")

    if result.passes:
        print("Provenance is structurally sufficient for the next AH-04 experiment.")
    else:
        print("Provenance is NOT sufficient. No latency model should be run on this data.")


if __name__ == "__main__":
    main()
