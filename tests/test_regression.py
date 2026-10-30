import pytest
from models import new_account
from service import calculate_points, apply_reward_event, flag_repeat_transactions


def test_regression_floor_boundary_values():
    """Ensure integer floor division is used instead of rounding."""
    # 9999 paise is 99.99 rupees -> 0 hundred rupees -> 0 points
    assert calculate_points(9999, 1) == 0
    # 19999 paise is 199.99 rupees -> 1 hundred rupees -> 1 point
    assert calculate_points(19999, 1) == 1
    # 29999 paise -> 2 points
    assert calculate_points(29999, 1) == 2


def test_regression_cap_zero_not_falsy():
    """Ensure cap_points=0 is treated as a cap of 0 rather than skipped as falsy."""
    assert calculate_points(50000, 1, bonus_percent=50, cap_points=0) == 0
    assert calculate_points(100000, 2, bonus_percent=0, cap_points=0) == 0


def test_regression_event_replay_idempotency_no_list_duplication():
    """Ensure replaying an event does not append duplicate event_id to processed_event_ids or ledger."""
    account = new_account("ACCT-1")
    event = {
        "event_id": "EVT-REG-001",
        "type": "purchase_captured",
        "transaction_id": "TXN-1",
        "amount_paise": 25000,
    }
    rules = {"points_per_100_rupees": 1}

    once = apply_reward_event(account, event, rules)
    twice = apply_reward_event(once, event, rules)
    thrice = apply_reward_event(twice, event, rules)

    assert once["processed_event_ids"] == ["EVT-REG-001"]
    assert twice["processed_event_ids"] == ["EVT-REG-001"]
    assert thrice["processed_event_ids"] == ["EVT-REG-001"]
    assert len(thrice["ledger"]) == 1
    assert thrice["points_balance"] == 2


def test_regression_refund_event_replay_idempotency():
    """Ensure replaying a refund event does not reverse points multiple times."""
    rules = {"points_per_100_rupees": 1}
    acc = new_account("ACCT-1")
    acc = apply_reward_event(
        acc,
        {"event_id": "E-PURCHASE", "type": "purchase_captured", "transaction_id": "TXN-1", "amount_paise": 100000},
        rules,
    )
    assert acc["points_balance"] == 10

    refund_event = {
        "event_id": "E-REFUND-1",
        "type": "refund_processed",
        "transaction_id": "TXN-1",
        "amount_paise": 40000,
    }
    once = apply_reward_event(acc, refund_event, rules)
    assert once["points_balance"] == 6
    assert once["transactions"]["TXN-1"]["reversed_points"] == 4
    assert once["processed_event_ids"] == ["E-PURCHASE", "E-REFUND-1"]

    twice = apply_reward_event(once, refund_event, rules)
    assert twice["points_balance"] == 6
    assert twice["transactions"]["TXN-1"]["reversed_points"] == 4
    assert twice["processed_event_ids"] == ["E-PURCHASE", "E-REFUND-1"]
    assert len(twice["ledger"]) == 2


def test_regression_cumulative_partial_refunds_and_excess_rejection():
    """Ensure successive partial refunds accumulate correctly and any refund exceeding original purchase is rejected."""
    rules = {"points_per_100_rupees": 1}
    acc = apply_reward_event(
        new_account("ACCT-1"),
        {"event_id": "E-P", "type": "purchase_captured", "transaction_id": "TXN-1", "amount_paise": 100000},
        rules,
    )
    # First partial refund: 40,000 paise (4 points reversed)
    acc = apply_reward_event(
        acc,
        {"event_id": "E-R1", "type": "refund_processed", "transaction_id": "TXN-1", "amount_paise": 40000},
        rules,
    )
    assert acc["points_balance"] == 6
    assert acc["transactions"]["TXN-1"]["refunded_paise"] == 40000

    # Second partial refund: 50,000 paise (cumulative 90,000 paise -> 9 points reversed)
    acc = apply_reward_event(
        acc,
        {"event_id": "E-R2", "type": "refund_processed", "transaction_id": "TXN-1", "amount_paise": 50000},
        rules,
    )
    assert acc["points_balance"] == 1
    assert acc["transactions"]["TXN-1"]["refunded_paise"] == 90000

    # Third partial refund: 20,000 paise (90,000 + 20,000 = 110,000 > 100,000) -> excess!
    acc_after_excess = apply_reward_event(
        acc,
        {"event_id": "E-R3", "type": "refund_processed", "transaction_id": "TXN-1", "amount_paise": 20000},
        rules,
    )
    assert acc_after_excess["points_balance"] == 1
    assert acc_after_excess["transactions"]["TXN-1"]["refunded_paise"] == 90000
    assert "E-R3" not in acc_after_excess["processed_event_ids"]


def test_regression_refund_cannot_make_balance_negative():
    """Ensure points balance cannot become negative if balance was lower than reversed points."""
    rules = {"points_per_100_rupees": 1}
    acc = apply_reward_event(
        new_account("ACCT-1"),
        {"event_id": "E-P", "type": "purchase_captured", "transaction_id": "TXN-1", "amount_paise": 100000},
        rules,
    )
    # Simulate balance being manually depleted or spent down to 2
    acc["points_balance"] = 2

    # Full refund of 100,000 paise would normally reverse 10 points, but balance is only 2
    acc = apply_reward_event(
        acc,
        {"event_id": "E-R", "type": "refund_processed", "transaction_id": "TXN-1", "amount_paise": 100000},
        rules,
    )
    assert acc["points_balance"] == 0
    assert acc["ledger"][-1]["points_delta"] == -2


def test_regression_boolean_inputs_not_treated_as_integers():
    """In Python, bool is a subclass of int. Ensure booleans are rejected as invalid amounts/rules."""
    assert calculate_points(True, 1) == 0
    assert calculate_points(100000, True) == 0
    assert calculate_points(100000, 1, bonus_percent=True) == 0
    assert calculate_points(100000, 1, cap_points=True) == 0


def test_regression_flag_repeats_safe_with_none_or_malformed():
    """Ensure repeat transaction detection safely handles None, empty, or malformed entries."""
    assert flag_repeat_transactions(None) == []
    assert flag_repeat_transactions([]) == []
    assert flag_repeat_transactions([None, "invalid", 123]) == []
