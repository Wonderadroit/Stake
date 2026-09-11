import pandas as pd
import pytest

from stake.provenance import audit_candidate_rows, audit_information_provenance


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "fixture_id": [1, 2, 3],
            "kickoff_timestamp": [
                "2024-01-01T15:00:00Z",
                "2024-01-02T15:00:00Z",
                "2024-01-03T15:00:00Z",
            ],
            "information_timestamp": [
                "2024-01-01T12:00:00Z",
                "2024-01-02T14:00:00Z",
                "2024-01-03T16:00:00Z",
            ],
            "decision_timestamp": [
                "2024-01-01T12:30:00Z",
                "2024-01-02T14:30:00Z",
                "2024-01-03T16:30:00Z",
            ],
            "market_timestamp": [
                "2024-01-01T12:15:00Z",
                "2024-01-02T14:15:00Z",
                "2024-01-03T16:15:00Z",
            ],
            "market_home_price": [2.0, 2.1, 1.9],
            "market_away_price": [1.8, 1.7, 2.0],
        }
    )


def test_valid_provenance_passes_only_when_all_rows_are_temporally_valid():
    frame = _frame()
    frame.loc[2, "information_timestamp"] = "2024-01-03T14:00:00Z"
    frame.loc[2, "decision_timestamp"] = "2024-01-03T14:30:00Z"
    frame.loc[2, "market_timestamp"] = "2024-01-03T14:15:00Z"

    result = audit_information_provenance(frame)

    assert result.passes
    assert result.valid_rows == 3
    assert result.invalid_rows == 0


def test_future_information_is_rejected():
    result = audit_information_provenance(_frame())

    assert not result.passes
    assert result.ordering_violation_rows == 1
    assert result.valid_rows == 2


def test_missing_timestamps_are_rejected_not_inferred():
    frame = _frame()
    frame.loc[1, "information_timestamp"] = None

    result = audit_information_provenance(frame)

    assert not result.passes
    assert result.missing_timestamp_rows == 1


def test_required_columns_are_explicit():
    frame = _frame().drop(columns=["information_timestamp"])

    with pytest.raises(ValueError, match="Missing provenance columns"):
        audit_information_provenance(frame)


def test_row_audit_exposes_eligibility():
    frame = _frame()
    audited = audit_candidate_rows(frame)

    assert audited["eligible"].tolist() == [True, True, False]
    assert audited["ordering_valid"].tolist() == [True, True, False]
