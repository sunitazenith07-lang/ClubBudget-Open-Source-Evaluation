import pytest
from models import new_account
from service import calculate_points, apply_reward_event, flag_repeat_transactions


def test_regression_floor_points_boundary():
    """Verify 9999 paise (Rs 99.99) yields 0 points and 19999 paise (Rs 199.99) yields 1 point."""
    assert calculate_points(9999, 1) == 0
    assert calculate_points(19999, 1) == 1
    assert calculate_points(20000, 1) == 2


def test_regression_cap_zero_resets_points():
    """Verify that a cap of 0 returns 0 points even with large purchases and bonus."""
    assert calculate_points(1000000, 2, bonus_percent=100, cap_points=0) == 0


def test_regression_idempotent_event_replay():
    """Verify that replaying a captured purchase event does not award points twice or duplicate event ID."""
    account = new_account("ACC-1")
    event = {"event_id": "EVT-REG-1", "type": "purchase_captured", "transaction_id": "TX-1", "amount_paise": 50000}
    rules = {"points_per_100_rupees": 1}

    out1 = apply_reward_event(account, event, rules)
    out2 = apply_reward_event(out1, event, rules)

    assert out1["points_balance"] == 5
    assert out2["points_balance"] == 5
    assert out2["processed_event_ids"] == ["EVT-REG-1"]
    assert len(out2["ledger"]) == 1


def test_regression_excess_refund_rejected():
    """Verify that a refund exceeding the original transaction amount is rejected without mutating state."""
    account = new_account("ACC-2")
    rules = {"points_per_100_rupees": 1}
    captured = apply_reward_event(
        account,
        {"event_id": "EVT-P1", "type": "purchase_captured", "transaction_id": "TX-P1", "amount_paise": 100000},
        rules,
    )
    refunded = apply_reward_event(
        captured,
        {"event_id": "EVT-R1", "type": "refund_processed", "transaction_id": "TX-P1", "amount_paise": 150000},
        rules,
    )
    assert refunded["transactions"]["TX-P1"]["refunded_paise"] == 0
    assert refunded["transactions"]["TX-P1"]["reversed_points"] == 0
    assert refunded["points_balance"] == 10
    assert len(refunded["ledger"]) == 1


def test_regression_multi_partial_refunds_cumulative():
    """Verify multiple partial refunds accumulate correctly and reverse points proportionally without going negative."""
    account = new_account("ACC-3")
    rules = {"points_per_100_rupees": 1}
    s0 = apply_reward_event(
        account,
        {"event_id": "E-BUY", "type": "purchase_captured", "transaction_id": "TX-BUY", "amount_paise": 100000},
        rules,
    )
    assert s0["points_balance"] == 10

    # First partial refund: 40000 paise (40%) -> 4 points reversed
    s1 = apply_reward_event(
        s0,
        {"event_id": "E-REF-1", "type": "refund_processed", "transaction_id": "TX-BUY", "amount_paise": 40000},
        rules,
    )
    assert s1["transactions"]["TX-BUY"]["refunded_paise"] == 40000
    assert s1["transactions"]["TX-BUY"]["reversed_points"] == 4
    assert s1["points_balance"] == 6

    # Second partial refund: 60000 paise (cumulatively 100000 paise, 100%) -> 6 more points reversed
    s2 = apply_reward_event(
        s1,
        {"event_id": "E-REF-2", "type": "refund_processed", "transaction_id": "TX-BUY", "amount_paise": 60000},
        rules,
    )
    assert s2["transactions"]["TX-BUY"]["refunded_paise"] == 100000
    assert s2["transactions"]["TX-BUY"]["reversed_points"] == 10
    assert s2["points_balance"] == 0
    assert len(s2["ledger"]) == 3
