from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import pandas as pd


REQUIRED_COLUMNS = (
    "fixture_id",
    "kickoff_timestamp",
    "information_timestamp",
    "decision_timestamp",
    "market_timestamp",
    "market_home_price",
    "market_away_price",
)


@dataclass(frozen=True)
class ProvenanceAudit:
    rows: int
    valid_rows: int
    invalid_rows: int
    missing_timestamp_rows: int
    ordering_violation_rows: int
    market_timestamp_rows: int
    information_timestamp_rows: int
    status: str

    @property
    def passes(self) -> bool:
        return self.status == "PASS"


def _timestamp_series(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_datetime(frame[column], utc=True, errors="coerce")


def audit_information_provenance(frame: pd.DataFrame) -> ProvenanceAudit:
    """Audit whether a dataset can support an information-latency experiment.

    This function deliberately does not infer publication times. A row passes
    only when the dataset explicitly supplies all required timestamps and the
    causal ordering is:

        information_timestamp <= decision_timestamp < kickoff_timestamp

    The market timestamp must also be present and no later than kickoff. The
    function is a feasibility gate, not a betting model.
    """
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing provenance columns: {missing}")

    rows = len(frame)
    if rows == 0:
        return ProvenanceAudit(0, 0, 0, 0, 0, 0, 0, "FAIL")

    parsed = {
        column: _timestamp_series(frame, column)
        for column in (
            "kickoff_timestamp",
            "information_timestamp",
            "decision_timestamp",
            "market_timestamp",
        )
    }
    timestamps = pd.DataFrame(parsed)
    missing_mask = timestamps.isna().any(axis=1)

    ordering_ok = (
        (timestamps["information_timestamp"] <= timestamps["decision_timestamp"])
        & (timestamps["decision_timestamp"] < timestamps["kickoff_timestamp"])
        & (timestamps["market_timestamp"] <= timestamps["kickoff_timestamp"])
    )
    valid_mask = (~missing_mask) & ordering_ok

    missing_count = int(missing_mask.sum())
    violation_count = int((~missing_mask & ~ordering_ok).sum())
    valid_count = int(valid_mask.sum())

    status = "PASS" if valid_count == rows else "FAIL"
    return ProvenanceAudit(
        rows=rows,
        valid_rows=valid_count,
        invalid_rows=rows - valid_count,
        missing_timestamp_rows=missing_count,
        ordering_violation_rows=violation_count,
        market_timestamp_rows=int(timestamps["market_timestamp"].notna().sum()),
        information_timestamp_rows=int(timestamps["information_timestamp"].notna().sum()),
        status=status,
    )


def audit_candidate_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """Return row-level provenance decisions for inspection and evidence logs."""
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing provenance columns: {missing}")

    result = frame[["fixture_id"]].copy()
    for column in (
        "kickoff_timestamp",
        "information_timestamp",
        "decision_timestamp",
        "market_timestamp",
    ):
        result[column] = _timestamp_series(frame, column)

    result["missing_timestamp"] = result[
        [
            "kickoff_timestamp",
            "information_timestamp",
            "decision_timestamp",
            "market_timestamp",
        ]
    ].isna().any(axis=1)
    result["ordering_valid"] = (
        ~result["missing_timestamp"]
        & (result["information_timestamp"] <= result["decision_timestamp"])
        & (result["decision_timestamp"] < result["kickoff_timestamp"])
        & (result["market_timestamp"] <= result["kickoff_timestamp"])
    )
    result["eligible"] = result["ordering_valid"]
    return result
