"""Regression and comprehensive edge case tests for RewardBook."""

import pytest
from models import new_account
from service import (
    calculate_points,
    apply_reward_event,
    flag_repeat_transactions,
    generate_account_statement_csv,
)


def test_refund_event_replay_is_idempotent():
    """Verify that replaying the same refund event multiple times does not alter points balance twice."""
    rules = {"points_per_100_rupees": 1}
    account = new_account("ACCT-REG-1")
    purchase = {
        "event_id": "EVT-P1",
        "type": "purchase_captured",
        "transaction_id": "TX-1",
        "amount_paise": 100000,
    }
    refund = {
        "event_id": "EVT-R1",
        "type": "refund_processed",
        "transaction_id": "TX-1",
        "amount_paise": 40000,
    }

    # Apply purchase
    account = apply_reward_event(account, purchase, rules)
    assert account["points_balance"] == 10

    # Apply refund once
    once = apply_reward_event(account, refund, rules)
    assert once["points_balance"] == 6
    assert once["transactions"]["TX-1"]["reversed_points"] == 4
    assert len(once["ledger"]) == 2
    assert once["processed_event_ids"] == ["EVT-P1", "EVT-R1"]

    # Replay refund
    twice = apply_reward_event(once, refund, rules)
    assert twice["points_balance"] == 6
    assert twice["transactions"]["TX-1"]["reversed_points"] == 4
    assert len(twice["ledger"]) == 2
    assert twice["processed_event_ids"] == ["EVT-P1", "EVT-R1"]


def test_sequential_partial_refunds_up_to_full_amount():
    """Verify that multiple consecutive partial refunds sum properly without rounding drift."""
    rules = {"points_per_100_rupees": 1}
    account = new_account("ACCT-REG-2")
    purchase = {
        "event_id": "EVT-P2",
        "type": "purchase_captured",
        "transaction_id": "TX-2",
        "amount_paise": 100000,  # 10 points
    }
    account = apply_reward_event(account, purchase, rules)
    assert account["points_balance"] == 10

    # Refund 1: 30000 paise (3 points)
    r1 = {
        "event_id": "EVT-R2A",
        "type": "refund_processed",
        "transaction_id": "TX-2",
        "amount_paise": 30000,
    }
    account = apply_reward_event(account, r1, rules)
    assert account["points_balance"] == 7
    assert account["transactions"]["TX-2"]["refunded_paise"] == 30000
    assert account["transactions"]["TX-2"]["reversed_points"] == 3

    # Refund 2: 30000 paise (another 3 points)
    r2 = {
        "event_id": "EVT-R2B",
        "type": "refund_processed",
        "transaction_id": "TX-2",
        "amount_paise": 30000,
    }
    account = apply_reward_event(account, r2, rules)
    assert account["points_balance"] == 4
    assert account["transactions"]["TX-2"]["refunded_paise"] == 60000
    assert account["transactions"]["TX-2"]["reversed_points"] == 6

    # Refund 3: 40000 paise (remaining 4 points -> full refund)
    r3 = {
        "event_id": "EVT-R2C",
        "type": "refund_processed",
        "transaction_id": "TX-2",
        "amount_paise": 40000,
    }
    account = apply_reward_event(account, r3, rules)
    assert account["points_balance"] == 0
    assert account["transactions"]["TX-2"]["refunded_paise"] == 100000
    assert account["transactions"]["TX-2"]["reversed_points"] == 10

    # Refund 4: Attempting any further refund (e.g., 1 paise) must be rejected
    r4 = {
        "event_id": "EVT-R2D",
        "type": "refund_processed",
        "transaction_id": "TX-2",
        "amount_paise": 1,
    }
    rejected = apply_reward_event(account, r4, rules)
    assert rejected["points_balance"] == 0
    assert rejected["transactions"]["TX-2"]["refunded_paise"] == 100000
    assert len(rejected["ledger"]) == 4  # No entry added for rejected refund


def test_zero_awarded_purchase_refund():
    """Verify that a purchase under 100 rupees (0 points) refunded does not cause negative points or errors."""
    rules = {"points_per_100_rupees": 1}
    account = new_account("ACCT-REG-3")
    purchase = {
        "event_id": "EVT-P3",
        "type": "purchase_captured",
        "transaction_id": "TX-3",
        "amount_paise": 5000,  # 50 rupees -> 0 points
    }
    account = apply_reward_event(account, purchase, rules)
    assert account["points_balance"] == 0
    assert account["transactions"]["TX-3"]["awarded_points"] == 0

    refund = {
        "event_id": "EVT-R3",
        "type": "refund_processed",
        "transaction_id": "TX-3",
        "amount_paise": 5000,
    }
    account = apply_reward_event(account, refund, rules)
    assert account["points_balance"] == 0
    assert account["transactions"]["TX-3"]["refunded_paise"] == 5000
    assert account["transactions"]["TX-3"]["reversed_points"] == 0
    assert account["ledger"][-1]["points_delta"] == 0


def test_ledger_balance_mathematical_consistency():
    """Verify that points_balance exactly matches the sum of points_delta across all ledger entries."""
    rules = {"points_per_100_rupees": 2, "bonus_percent": 10, "cap_points": 50}
    account = new_account("ACCT-REG-4")

    # Purchase 1: 150000 paise (1500 Rs) -> base = 15*2 = 30 -> bonus = 30*1.1 = 33 -> 33 points
    account = apply_reward_event(
        account,
        {"event_id": "E1", "type": "purchase_captured", "transaction_id": "T1", "amount_paise": 150000},
        rules,
    )
    # Purchase 2: 200000 paise (2000 Rs) -> base = 20*2 = 40 -> bonus = 40*1.1 = 44 -> 44 points
    account = apply_reward_event(
        account,
        {"event_id": "E2", "type": "purchase_captured", "transaction_id": "T2", "amount_paise": 200000},
        rules,
    )
    # Refund on T1: 50000 paise (one third of 150000 -> 33 * 50000 // 150000 = 11 points reversed)
    account = apply_reward_event(
        account,
        {"event_id": "E3", "type": "refund_processed", "transaction_id": "T1", "amount_paise": 50000},
        rules,
    )
    # Duplicate replay of E1 and E3
    account = apply_reward_event(
        account,
        {"event_id": "E1", "type": "purchase_captured", "transaction_id": "T1", "amount_paise": 150000},
        rules,
    )
    account = apply_reward_event(
        account,
        {"event_id": "E3", "type": "refund_processed", "transaction_id": "T1", "amount_paise": 50000},
        rules,
    )

    ledger_sum = sum(entry["points_delta"] for entry in account["ledger"])
    assert account["points_balance"] == ledger_sum
    assert account["points_balance"] == 33 + 44 - 11


def test_malformed_and_missing_inputs_safety():
    """Verify defensive handling of None, invalid structures, and missing identifiers."""
    # Non-dict inputs
    assert apply_reward_event({}, {}, {}) == {"points_balance": 0, "processed_event_ids": [], "transactions": {}, "ledger": []}
    assert calculate_points(None, 1) == 0  # type: ignore
    assert calculate_points(10000, None) == 0  # type: ignore
    assert calculate_points(True, 1) == 0
    assert calculate_points(10000, True) == 0
    assert calculate_points(10000, 1, bonus_percent=True) == 0  # type: ignore
    assert calculate_points(10000, 1, cap_points=True) == 0  # type: ignore

    # flag_repeat_transactions safety
    assert flag_repeat_transactions(None) == []  # type: ignore
    assert flag_repeat_transactions([None, "string", 123]) == []  # type: ignore
    assert flag_repeat_transactions([], threshold=None) == []  # type: ignore


def test_generate_account_statement_csv():
    """Verify that CSV statement generation correctly formats the audit ledger."""
    account = new_account("ACCT-CSV-1")
    rules = {"points_per_100_rupees": 1}
    account = apply_reward_event(
        account,
        {"event_id": "E10", "type": "purchase_captured", "transaction_id": "T10", "amount_paise": 100000},
        rules,
    )
    account = apply_reward_event(
        account,
        {"event_id": "E11", "type": "refund_processed", "transaction_id": "T10", "amount_paise": 20000},
        rules,
    )

    csv_output = generate_account_statement_csv(account)
    expected_lines = [
        "event_id,type,points_delta",
        "E10,purchase_captured,10",
        "E11,refund_processed,-2",
    ]
    assert csv_output == "\n".join(expected_lines)
