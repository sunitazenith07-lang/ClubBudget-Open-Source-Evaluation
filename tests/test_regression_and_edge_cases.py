"""Regression and edge case test suite for RewardBook.

Protects against:
- Rounding drift in base points and bonus calculations.
- Over-refunding and cumulative refund boundary violations.
- Event replay / duplicate event ID processing (idempotency).
- Non-negative points balance guarantees.
- Non-integer / boolean type confusion.
- Edge cases in repeat transaction alerts.
- CSV statement generation (optional stretch goal).
"""

import pytest
from models import new_account
from service import (
    calculate_points,
    apply_reward_event,
    flag_repeat_transactions,
    generate_account_statement_csv,
)


def test_paise_boundary_floor_arithmetic():
    """Edge Case 1: Base points calculation uses floor division at 100-rupee (10,000 paise) boundaries."""
    assert calculate_points(9999, 1) == 0
    assert calculate_points(10000, 1) == 1
    assert calculate_points(19999, 1) == 1
    assert calculate_points(20000, 1) == 2


def test_zero_and_negative_cap_points():
    """Edge Case 2: Cap of zero or negative points must clamp awarded points to zero."""
    assert calculate_points(50000, 2, 50, cap_points=0) == 0
    assert calculate_points(50000, 2, 50, cap_points=-10) == 0


def test_multi_step_partial_refund_no_rounding_drift():
    """Edge Case 3: Multiple partial refunds summing to the original amount reverse exactly the awarded points without drift."""
    rules = {"points_per_100_rupees": 1}
    # 100,000 paise (Rs 1,000) -> 10 points
    account = new_account("ACC-MULTI")
    account = apply_reward_event(
        account,
        {"event_id": "EV-P1", "type": "purchase_captured", "transaction_id": "TX-M1", "amount_paise": 100000},
        rules,
    )
    assert account["points_balance"] == 10
    assert account["transactions"]["TX-M1"]["awarded_points"] == 10

    # Refund 1: 33,333 paise -> floor(10 * 33333 / 100000) = 3 points reversed
    account = apply_reward_event(
        account,
        {"event_id": "EV-R1", "type": "refund_processed", "transaction_id": "TX-M1", "amount_paise": 33333},
        rules,
    )
    assert account["points_balance"] == 7
    assert account["transactions"]["TX-M1"]["reversed_points"] == 3
    assert account["transactions"]["TX-M1"]["refunded_paise"] == 33333

    # Refund 2: 33,333 paise -> cumulative 66,666 paise -> floor(10 * 66666 / 100000) = 6 points reversed
    account = apply_reward_event(
        account,
        {"event_id": "EV-R2", "type": "refund_processed", "transaction_id": "TX-M1", "amount_paise": 33333},
        rules,
    )
    assert account["points_balance"] == 4
    assert account["transactions"]["TX-M1"]["reversed_points"] == 6
    assert account["transactions"]["TX-M1"]["refunded_paise"] == 66666

    # Refund 3: 33,334 paise -> cumulative 100,000 paise -> floor(10 * 100000 / 100000) = 10 points reversed
    account = apply_reward_event(
        account,
        {"event_id": "EV-R3", "type": "refund_processed", "transaction_id": "TX-M1", "amount_paise": 33334},
        rules,
    )
    assert account["points_balance"] == 0
    assert account["transactions"]["TX-M1"]["reversed_points"] == 10
    assert account["transactions"]["TX-M1"]["refunded_paise"] == 100000
    assert len(account["ledger"]) == 4


def test_cumulative_excess_refund_rejected():
    """Edge Case 4: A second refund that causes cumulative refunded amount to exceed purchase amount is rejected."""
    rules = {"points_per_100_rupees": 1}
    account = new_account("ACC-EXCESS")
    account = apply_reward_event(
        account,
        {"event_id": "EV-P1", "type": "purchase_captured", "transaction_id": "TX-E1", "amount_paise": 100000},
        rules,
    )
    # First refund 60,000 paise is accepted
    account = apply_reward_event(
        account,
        {"event_id": "EV-R1", "type": "refund_processed", "transaction_id": "TX-E1", "amount_paise": 60000},
        rules,
    )
    assert account["transactions"]["TX-E1"]["refunded_paise"] == 60000
    assert account["points_balance"] == 4

    # Second refund for 50,000 paise exceeds remaining 40,000 paise and must be ignored
    rejected = apply_reward_event(
        account,
        {"event_id": "EV-R2", "type": "refund_processed", "transaction_id": "TX-E1", "amount_paise": 50000},
        rules,
    )
    assert rejected["transactions"]["TX-E1"]["refunded_paise"] == 60000
    assert rejected["points_balance"] == 4
    assert len(rejected["ledger"]) == 2
    assert "EV-R2" not in rejected["processed_event_ids"]


def test_boolean_inputs_strictly_rejected():
    """Edge Case 5: Python bool values (subclass of int) are rejected and return 0 points."""
    assert calculate_points(True, 1) == 0
    assert calculate_points(False, 1) == 0
    assert calculate_points(10000, True) == 0
    assert calculate_points(10000, 1, bonus_percent=True) == 0
    assert calculate_points(10000, 1, cap_points=True) == 0


def test_event_replay_idempotency_for_refund():
    """Edge Case 6: Refund event replay is idempotent and does not reverse points twice."""
    rules = {"points_per_100_rupees": 1}
    account = new_account("ACC-IDEMP")
    account = apply_reward_event(
        account,
        {"event_id": "EV-P1", "type": "purchase_captured", "transaction_id": "TX-1", "amount_paise": 100000},
        rules,
    )
    refund_event = {
        "event_id": "EV-R1",
        "type": "refund_processed",
        "transaction_id": "TX-1",
        "amount_paise": 50000,
    }
    after_refund = apply_reward_event(account, refund_event, rules)
    assert after_refund["points_balance"] == 5
    assert len(after_refund["ledger"]) == 2

    # Replay same refund event
    replayed = apply_reward_event(after_refund, refund_event, rules)
    assert replayed["points_balance"] == 5
    assert len(replayed["ledger"]) == 2
    assert replayed["processed_event_ids"] == ["EV-P1", "EV-R1"]


def test_points_balance_never_negative():
    """Edge Case 7: Points balance is clamped at zero and never goes negative."""
    rules = {"points_per_100_rupees": 1}
    account = new_account("ACC-CLAMP")
    account = apply_reward_event(
        account,
        {"event_id": "EV-P1", "type": "purchase_captured", "transaction_id": "TX-1", "amount_paise": 100000},
        rules,
    )
    # Manually simulate balance reduction (e.g. points spent elsewhere)
    account["points_balance"] = 2

    # Full refund would reverse 10 points, but only 2 points are available
    account = apply_reward_event(
        account,
        {"event_id": "EV-R1", "type": "refund_processed", "transaction_id": "TX-1", "amount_paise": 100000},
        rules,
    )
    assert account["points_balance"] == 0
    assert account["ledger"][-1]["points_delta"] == -2


def test_generate_account_statement_csv():
    """Test optional stretch feature: account ledger statement in CSV format."""
    rules = {"points_per_100_rupees": 1}
    account = new_account("ACC-CSV")
    account = apply_reward_event(
        account,
        {"event_id": "EV-P1", "type": "purchase_captured", "transaction_id": "TX-1", "amount_paise": 250000},
        rules,
    )
    account = apply_reward_event(
        account,
        {"event_id": "EV-R1", "type": "refund_processed", "transaction_id": "TX-1", "amount_paise": 100000},
        rules,
    )
    csv_output = generate_account_statement_csv(account)
    expected_csv = (
        "event_id,type,points_delta\n"
        "EV-P1,purchase_captured,25\n"
        "EV-R1,refund_processed,-10\n"
    )
    assert csv_output == expected_csv


def test_repeat_transactions_deterministic_ordering_and_filtering():
    """Edge Case 8: Repeat alerts handle empty inputs, malformed records, and maintain deterministic ordering."""
    txns = [
        {"transaction_id": "T3", "account_id": "B", "date": "2026-10-21", "amount_paise": 500},
        {"transaction_id": "T2", "account_id": "A", "date": "2026-10-21", "amount_paise": 1000},
        {"transaction_id": "T1", "account_id": "A", "date": "2026-10-21", "amount_paise": 1000},
        "not a dict",
        None,
    ]
    alerts = flag_repeat_transactions(txns, threshold=1)
    assert len(alerts) == 1
    assert alerts[0]["account_id"] == "A"
    assert alerts[0]["transaction_ids"] == ["T2", "T1"]

