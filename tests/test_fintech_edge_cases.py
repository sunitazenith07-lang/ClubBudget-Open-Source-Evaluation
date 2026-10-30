"""Comprehensive test suite for RewardBook edge cases and ledger integrity.

Covers:
- Normal purchase
- Zero and negative amounts
- Duplicate purchase (event_id replay and duplicate transaction_id)
- Partial refund (single and multi-step cumulative)
- Full refund
- Duplicate refund (replay idempotency)
- Refund rounding (proportional remainders)
- Promotional limits (bonus %, caps, cap=0, negative cap)
- Unknown transaction IDs and missing identifiers
- Ledger consistency (balance == sum of ledger deltas)
- Negative balance protection
- Dataset integration with data/records.json
"""
import json
from pathlib import Path
import pytest

from models import new_account
from service import (
    calculate_points,
    apply_reward_event,
    flag_repeat_transactions,
    generate_account_statement_csv,
)


def test_normal_purchase():
    """Verify normal purchase calculation, transaction state, and ledger entry."""
    account = new_account("ACCT-001")
    rules = {"points_per_100_rupees": 2, "bonus_percent": 10, "cap_points": 50}
    event = {
        "event_id": "EV-001",
        "type": "purchase_captured",
        "transaction_id": "TX-001",
        "amount_paise": 50000,  # Rs 500 -> 5 * 2 = 10 base -> 10 * 110 // 100 = 11 points
    }
    result = apply_reward_event(account, event, rules)

    assert result["points_balance"] == 11
    assert result["transactions"]["TX-001"]["amount_paise"] == 50000
    assert result["transactions"]["TX-001"]["awarded_points"] == 11
    assert result["transactions"]["TX-001"]["reversed_points"] == 0
    assert result["transactions"]["TX-001"]["refunded_paise"] == 0
    assert len(result["ledger"]) == 1
    assert result["ledger"][0] == {
        "event_id": "EV-001",
        "type": "purchase_captured",
        "points_delta": 11,
    }
    assert result["processed_event_ids"] == ["EV-001"]


@pytest.mark.parametrize("invalid_amount", [0, -1, -100, -50000, "50000", 500.5, True, False, None, [], {}])
def test_zero_and_negative_purchase_amounts(invalid_amount):
    """Verify non-positive and invalid purchase amounts generate no points and do not record transactions."""
    account = new_account("ACCT-001")
    rules = {"points_per_100_rupees": 1}
    event = {
        "event_id": "EV-INV",
        "type": "purchase_captured",
        "transaction_id": "TX-INV",
        "amount_paise": invalid_amount,
    }
    result = apply_reward_event(account, event, rules)
    assert result["points_balance"] == 0
    assert result["transactions"] == {}
    assert result["ledger"] == []
    assert result["processed_event_ids"] == []


def test_duplicate_purchase_replay_idempotency():
    """Verify replaying the exact same purchase event does not award points or duplicate ledger."""
    account = new_account("ACCT-001")
    rules = {"points_per_100_rupees": 1}
    event = {
        "event_id": "EV-DUP-1",
        "type": "purchase_captured",
        "transaction_id": "TX-100",
        "amount_paise": 100000,
    }
    first = apply_reward_event(account, event, rules)
    assert first["points_balance"] == 10
    assert len(first["ledger"]) == 1

    second = apply_reward_event(first, event, rules)
    assert second["points_balance"] == 10
    assert len(second["ledger"]) == 1
    assert second["processed_event_ids"] == ["EV-DUP-1"]


def test_duplicate_transaction_id_with_different_event_id():
    """Verify that a second purchase with identical transaction_id does not award duplicate points."""
    account = new_account("ACCT-001")
    rules = {"points_per_100_rupees": 1}
    event1 = {
        "event_id": "EV-P1",
        "type": "purchase_captured",
        "transaction_id": "TX-SAME",
        "amount_paise": 100000,
    }
    event2 = {
        "event_id": "EV-P2",
        "type": "purchase_captured",
        "transaction_id": "TX-SAME",
        "amount_paise": 100000,
    }
    step1 = apply_reward_event(account, event1, rules)
    step2 = apply_reward_event(step1, event2, rules)

    assert step2["points_balance"] == 10
    assert len(step2["ledger"]) == 1
    assert "EV-P2" in step2["processed_event_ids"]


def test_partial_refund_single():
    """Verify single partial refund proportional points reversal."""
    account = new_account("ACCT-001")
    rules = {"points_per_100_rupees": 1}
    # Purchase: Rs 1000 -> 10 points
    account = apply_reward_event(
        account,
        {"event_id": "E-PURCHASE", "type": "purchase_captured", "transaction_id": "TX-1", "amount_paise": 100000},
        rules,
    )
    # Refund 40% (Rs 400) -> 4 points reversed
    refund_event = {
        "event_id": "E-REFUND-1",
        "type": "refund_processed",
        "transaction_id": "TX-1",
        "amount_paise": 40000,
    }
    result = apply_reward_event(account, refund_event, rules)

    assert result["points_balance"] == 6
    assert result["transactions"]["TX-1"]["refunded_paise"] == 40000
    assert result["transactions"]["TX-1"]["reversed_points"] == 4
    assert result["ledger"][-1] == {
        "event_id": "E-REFUND-1",
        "type": "refund_processed",
        "points_delta": -4,
    }


def test_multi_step_cumulative_partial_refunds():
    """Verify multiple successive partial refunds accurately total to full refund reversal."""
    account = new_account("ACCT-001")
    rules = {"points_per_100_rupees": 1}
    account = apply_reward_event(
        account,
        {"event_id": "E-P", "type": "purchase_captured", "transaction_id": "TX-MULTI", "amount_paise": 100000},
        rules,
    )
    assert account["points_balance"] == 10

    # Step 1: refund 30,000 paise (30%) -> reverses 3 points
    account = apply_reward_event(
        account,
        {"event_id": "E-R1", "type": "refund_processed", "transaction_id": "TX-MULTI", "amount_paise": 30000},
        rules,
    )
    assert account["points_balance"] == 7
    assert account["transactions"]["TX-MULTI"]["reversed_points"] == 3

    # Step 2: refund another 30,000 paise (cumulative 60,000) -> should reverse total 6 -> delta 3
    account = apply_reward_event(
        account,
        {"event_id": "E-R2", "type": "refund_processed", "transaction_id": "TX-MULTI", "amount_paise": 30000},
        rules,
    )
    assert account["points_balance"] == 4
    assert account["transactions"]["TX-MULTI"]["reversed_points"] == 6

    # Step 3: refund remaining 40,000 paise (cumulative 100,000) -> should reverse total 10 -> delta 4
    account = apply_reward_event(
        account,
        {"event_id": "E-R3", "type": "refund_processed", "transaction_id": "TX-MULTI", "amount_paise": 40000},
        rules,
    )
    assert account["points_balance"] == 0
    assert account["transactions"]["TX-MULTI"]["reversed_points"] == 10
    assert account["transactions"]["TX-MULTI"]["refunded_paise"] == 100000

    # Step 4: attempt additional refund of 1 paise beyond 100,000 -> excess, ignored
    account = apply_reward_event(
        account,
        {"event_id": "E-R4", "type": "refund_processed", "transaction_id": "TX-MULTI", "amount_paise": 1},
        rules,
    )
    assert account["points_balance"] == 0
    assert account["transactions"]["TX-MULTI"]["reversed_points"] == 10
    assert account["transactions"]["TX-MULTI"]["refunded_paise"] == 100000


def test_full_refund_in_single_step():
    """Verify 100% refund reverses exact awarded points."""
    account = new_account("ACCT-001")
    rules = {"points_per_100_rupees": 2, "bonus_percent": 20}
    # 250,000 paise -> 25 * 2 = 50 -> 50 * 120 // 100 = 60 points
    account = apply_reward_event(
        account,
        {"event_id": "E-P", "type": "purchase_captured", "transaction_id": "TX-FULL", "amount_paise": 250000},
        rules,
    )
    assert account["points_balance"] == 60

    account = apply_reward_event(
        account,
        {"event_id": "E-R", "type": "refund_processed", "transaction_id": "TX-FULL", "amount_paise": 250000},
        rules,
    )
    assert account["points_balance"] == 0
    assert account["transactions"]["TX-FULL"]["reversed_points"] == 60
    assert account["transactions"]["TX-FULL"]["refunded_paise"] == 250000


def test_duplicate_refund_replay_idempotency():
    """Verify replaying the exact same refund event does not reverse points twice."""
    account = new_account("ACCT-001")
    rules = {"points_per_100_rupees": 1}
    account = apply_reward_event(
        account,
        {"event_id": "E-P", "type": "purchase_captured", "transaction_id": "TX-1", "amount_paise": 100000},
        rules,
    )
    refund_event = {"event_id": "E-R-DUP", "type": "refund_processed", "transaction_id": "TX-1", "amount_paise": 50000}
    first = apply_reward_event(account, refund_event, rules)
    assert first["points_balance"] == 5

    second = apply_reward_event(first, refund_event, rules)
    assert second["points_balance"] == 5
    assert len(second["ledger"]) == 2  # 1 purchase, 1 refund
    assert second["transactions"]["TX-1"]["reversed_points"] == 5


def test_refund_rounding_remainders():
    """Verify integer floor on proportional refund calculation does not lose or create points."""
    account = new_account("ACCT-001")
    rules = {"points_per_100_rupees": 1}
    # Rs 250 -> 2 base points
    account = apply_reward_event(
        account,
        {"event_id": "E-P", "type": "purchase_captured", "transaction_id": "TX-REM", "amount_paise": 25000},
        rules,
    )
    assert account["points_balance"] == 2

    # Refund Rs 100 (10,000 paise): 2 * 10000 // 25000 = 20000 // 25000 = 0 points reversed
    account = apply_reward_event(
        account,
        {"event_id": "E-R1", "type": "refund_processed", "transaction_id": "TX-REM", "amount_paise": 10000},
        rules,
    )
    assert account["points_balance"] == 2
    assert account["transactions"]["TX-REM"]["reversed_points"] == 0

    # Refund remaining Rs 150 (15,000 paise): 2 * 25000 // 25000 = 2 points reversed total -> delta 2
    account = apply_reward_event(
        account,
        {"event_id": "E-R2", "type": "refund_processed", "transaction_id": "TX-REM", "amount_paise": 15000},
        rules,
    )
    assert account["points_balance"] == 0
    assert account["transactions"]["TX-REM"]["reversed_points"] == 2


def test_promotional_limits_and_caps():
    """Verify points calculation across promotion boundaries and caps."""
    # Cap 0 gives 0
    assert calculate_points(100000, 1, 10, cap_points=0) == 0
    # Negative cap gives 0
    assert calculate_points(100000, 1, 10, cap_points=-1) == 0
    # Cap lower than base + bonus clamps
    assert calculate_points(100000, 1, 50, cap_points=12) == 12  # 10 * 1.5 = 15 -> capped to 12
    # Cap higher than points leaves points untouched
    assert calculate_points(100000, 1, 50, cap_points=20) == 15
    # Cap None leaves points untouched
    assert calculate_points(100000, 1, 50, cap_points=None) == 15
    # Cap exactly equal to points
    assert calculate_points(100000, 1, 50, cap_points=15) == 15


def test_unknown_transaction_and_missing_identifiers():
    """Verify unknown transaction IDs and missing identifiers are handled safely without exceptions."""
    account = new_account("ACCT-001")
    rules = {"points_per_100_rupees": 1}

    # Refund on non-existent transaction
    res = apply_reward_event(account, {"event_id": "E1", "type": "refund_processed", "transaction_id": "GHOST", "amount_paise": 1000}, rules)
    assert res["points_balance"] == 0
    assert res["ledger"] == []

    # Missing event_id
    res2 = apply_reward_event(account, {"type": "purchase_captured", "transaction_id": "T1", "amount_paise": 10000}, rules)
    assert res2["points_balance"] == 0
    assert res2["ledger"] == []

    # Missing transaction_id
    res3 = apply_reward_event(account, {"event_id": "E2", "type": "purchase_captured", "amount_paise": 10000}, rules)
    assert res3["points_balance"] == 0
    assert res3["ledger"] == []

    # Non-dict event
    res4 = apply_reward_event(account, "invalid_event", rules)
    assert res4 == account


def test_ledger_consistency_invariant():
    """Verify ledger invariant: points_balance equals the exact sum of all ledger points_deltas."""
    account = new_account("ACCT-AUDIT")
    rules = {"points_per_100_rupees": 1, "bonus_percent": 10}

    # Event 1: Purchase 1 (Rs 200 -> 2 base * 1.1 = 2 points)
    account = apply_reward_event(account, {"event_id": "E1", "type": "purchase_captured", "transaction_id": "T1", "amount_paise": 20000}, rules)
    # Event 2: Purchase 2 (Rs 500 -> 5 base * 1.1 = 5 points)
    account = apply_reward_event(account, {"event_id": "E2", "type": "purchase_captured", "transaction_id": "T2", "amount_paise": 50000}, rules)
    # Event 3: Partial refund on T2 (Rs 200 -> 5 * 20000 // 50000 = 2 points reversed)
    account = apply_reward_event(account, {"event_id": "E3", "type": "refund_processed", "transaction_id": "T2", "amount_paise": 20000}, rules)

    expected_sum = sum(entry["points_delta"] for entry in account["ledger"])
    assert account["points_balance"] == expected_sum
    assert account["points_balance"] == 5
    assert len(account["ledger"]) == 3


def test_ledger_negative_balance_prevention():
    """Verify points balance can never drop below zero even if reversed points exceed current balance."""
    account = new_account("ACCT-001")
    rules = {"points_per_100_rupees": 1}
    account = apply_reward_event(
        account,
        {"event_id": "E1", "type": "purchase_captured", "transaction_id": "T1", "amount_paise": 100000},
        rules,
    )
    assert account["points_balance"] == 10

    # Simulate account balance reduction (e.g. points spent/redeemed out of band)
    account["points_balance"] = 2

    # Refund that should reverse 10 points
    result = apply_reward_event(
        account,
        {"event_id": "E2", "type": "refund_processed", "transaction_id": "T1", "amount_paise": 100000},
        rules,
    )

    # Balance must be 0, never negative
    assert result["points_balance"] == 0
    assert result["transactions"]["T1"]["reversed_points"] == 10
    # Ledger records delta of -2 (the amount actually reversed)
    assert result["ledger"][-1]["points_delta"] == -2


def test_dataset_integration_records_json():
    """Integration test verifying data/records.json repeat patterns and rules cases."""
    data_path = Path("data/records.json")
    if not data_path.exists():
        pytest.skip("data/records.json not present")

    with open(data_path, "r", encoding="utf-8") as f:
        records_data = json.load(f)

    # 1. Test repeat-pattern alerts from synthetic dataset
    transactions = records_data.get("transactions", [])
    threshold = records_data.get("repeat_alert_threshold", 2)
    alerts = flag_repeat_transactions(transactions, threshold=threshold)
    assert isinstance(alerts, list)
    assert len(alerts) > 0  # Should flag repeat groups of 3
    for alert in alerts:
        assert len(alert["transaction_ids"]) > threshold
        assert "account_id" in alert
        assert "date" in alert
        assert "amount_paise" in alert

    # 2. Test rules cases without exceptions
    rules_cases = records_data.get("rules_cases", [])
    for rule in rules_cases:
        pts = calculate_points(
            100000,
            rule.get("points_per_100_rupees", 1),
            rule.get("bonus_percent", 0),
            rule.get("cap_points"),
        )
        assert isinstance(pts, int)
        assert pts >= 0


def test_generate_account_statement_csv():
    """Verify generation of CSV account statement from ledger entries."""
    account = new_account("ACCT-CSV")
    rules = {"points_per_100_rupees": 1}
    account = apply_reward_event(account, {"event_id": "EV-1", "type": "purchase_captured", "transaction_id": "TX-1", "amount_paise": 20000}, rules)
    account = apply_reward_event(account, {"event_id": "EV-2", "type": "refund_processed", "transaction_id": "TX-1", "amount_paise": 10000}, rules)

    csv_text = generate_account_statement_csv(account)
    lines = csv_text.strip().splitlines()
    assert lines[0] == "event_id,type,points_delta"
    assert lines[1] == "EV-1,purchase_captured,2"
    assert lines[2] == "EV-2,refund_processed,-1"


def test_points_per_100_rupees_zero_accepted_and_calculates_zero():
    """Verify points_per_100_rupees=0 is accepted as a valid rule yielding 0 points."""
    # Direct formula test
    assert calculate_points(50000, 0, 10, 100) == 0

    # Event processing test: accepted with 0 points
    account = new_account("ACCT-ZERO")
    rules = {"points_per_100_rupees": 0, "bonus_percent": 0, "cap_points": 0}
    result = apply_reward_event(
        account,
        {"event_id": "EV-Z", "type": "purchase_captured", "transaction_id": "TX-Z", "amount_paise": 50000},
        rules,
    )
    assert result["points_balance"] == 0
    assert result["transactions"]["TX-Z"]["awarded_points"] == 0
    assert result["transactions"]["TX-Z"]["amount_paise"] == 50000
    assert len(result["ledger"]) == 1
    assert result["ledger"][0]["points_delta"] == 0
    assert result["processed_event_ids"] == ["EV-Z"]


@pytest.mark.parametrize("invalid_rules", [
    {"points_per_100_rupees": -1},
    {"points_per_100_rupees": 1, "bonus_percent": -10},
    {"points_per_100_rupees": 1, "cap_points": -5},
    {"points_per_100_rupees": True},
    {"points_per_100_rupees": "invalid"},
])
def test_negative_reward_rules_not_accepted_as_purchases(invalid_rules):
    """Verify purchases with negative or malformed reward rules are rejected and not recorded."""
    account = new_account("ACCT-REJ")
    event = {
        "event_id": "EV-NEG-RULE",
        "type": "purchase_captured",
        "transaction_id": "TX-NEG",
        "amount_paise": 50000,
    }
    result = apply_reward_event(account, event, invalid_rules)
    assert result["points_balance"] == 0
    assert result["transactions"] == {}
    assert result["ledger"] == []
    assert result["processed_event_ids"] == []


def test_full_refund_after_awarded_points_spent_out_of_band():
    """Verify full refund after points spent records total reversal while keeping balance non-negative."""
    account = new_account("ACCT-SPENT")
    rules = {"points_per_100_rupees": 1}
    # Purchase awards 10 points
    account = apply_reward_event(
        account,
        {"event_id": "EV-P", "type": "purchase_captured", "transaction_id": "TX-1", "amount_paise": 100000},
        rules,
    )
    assert account["points_balance"] == 10

    # User spends 8 points out-of-band (e.g. external redemption), leaving 2 points in balance
    account["points_balance"] = 2

    # Full refund arrives: 100% of 100,000 paise
    result = apply_reward_event(
        account,
        {"event_id": "EV-R-FULL", "type": "refund_processed", "transaction_id": "TX-1", "amount_paise": 100000},
        rules,
    )
    # Balance must never be negative
    assert result["points_balance"] == 0
    # reversed_points preserves the full cumulative reversal required (10 points)
    assert result["transactions"]["TX-1"]["reversed_points"] == 10
    assert result["transactions"]["TX-1"]["refunded_paise"] == 100000
    # Ledger points_delta reflects actual deduction from balance (-2)
    assert result["ledger"][-1] == {
        "event_id": "EV-R-FULL",
        "type": "refund_processed",
        "points_delta": -2,
    }


def test_sequential_partial_refunds_and_reversal_tracking():
    """Verify sequential partial refunds track cumulative reversal and deduce appropriate deltas."""
    account = new_account("ACCT-SEQ")
    rules = {"points_per_100_rupees": 1}
    account = apply_reward_event(
        account,
        {"event_id": "EV-P", "type": "purchase_captured", "transaction_id": "TX-SEQ", "amount_paise": 100000},
        rules,
    )
    assert account["points_balance"] == 10

    # Partial refund 1: 30,000 paise (30%) -> reverses 3 points
    account = apply_reward_event(
        account,
        {"event_id": "EV-R1", "type": "refund_processed", "transaction_id": "TX-SEQ", "amount_paise": 30000},
        rules,
    )
    assert account["points_balance"] == 7
    assert account["transactions"]["TX-SEQ"]["reversed_points"] == 3
    assert account["ledger"][-1]["points_delta"] == -3

    # Partial refund 2: 40,000 paise (cumulative 70,000 -> 70%) -> reverses total 7 -> delta 4
    account = apply_reward_event(
        account,
        {"event_id": "EV-R2", "type": "refund_processed", "transaction_id": "TX-SEQ", "amount_paise": 40000},
        rules,
    )
    assert account["points_balance"] == 3
    assert account["transactions"]["TX-SEQ"]["reversed_points"] == 7
    assert account["ledger"][-1]["points_delta"] == -4


def test_duplicate_refund_replay_ledger_unchanged():
    """Verify replaying an identical refund event leaves the ledger and balance strictly unchanged."""
    account = new_account("ACCT-REP")
    rules = {"points_per_100_rupees": 1}
    account = apply_reward_event(
        account,
        {"event_id": "EV-P", "type": "purchase_captured", "transaction_id": "TX-REP", "amount_paise": 100000},
        rules,
    )
    refund_event = {"event_id": "EV-R", "type": "refund_processed", "transaction_id": "TX-REP", "amount_paise": 50000}
    account = apply_reward_event(account, refund_event, rules)

    ledger_snapshot = [dict(entry) for entry in account["ledger"]]
    balance_snapshot = account["points_balance"]
    tx_snapshot = dict(account["transactions"]["TX-REP"])

    # Replay identical event
    replayed = apply_reward_event(account, refund_event, rules)
    assert replayed["ledger"] == ledger_snapshot
    assert replayed["points_balance"] == balance_snapshot
    assert replayed["transactions"]["TX-REP"] == tx_snapshot


