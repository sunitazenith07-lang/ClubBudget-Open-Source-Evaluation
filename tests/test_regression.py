import pytest
from copy import deepcopy
from models import new_account
from service import calculate_points, apply_reward_event, flag_repeat_transactions


def test_points_integer_arithmetic_floor_rounding():
    # 259900 paise = 25.99 rupees -> floor to 25 base points
    # With 10% bonus: floor(25 * 110 / 100) = floor(2750 / 100) = 27
    assert calculate_points(259900, 1, 10, 100) == 27
    # 9999 paise is less than 100 rupees (10000 paise) -> 0 base points
    assert calculate_points(9999, 1, 50, None) == 0


def test_points_negative_or_invalid_inputs():
    assert calculate_points(100000, -1, 10, 100) == 0
    assert calculate_points(100000, 1, -10, 100) == 0
    assert calculate_points(100000, 1, 10, -5) == 0
    assert calculate_points(100000, 1, 10, 0) == 0
    assert calculate_points(True, 1, 10, 100) == 0  # bool is not treated as int
    assert calculate_points(100000, True, 10, 100) == 0
    assert calculate_points(100000, 1, False, 100) == 0
    assert calculate_points("100000", 1, 0, None) == 0


def test_cumulative_multiple_partial_refunds():
    rules = {"points_per_100_rupees": 1}
    account = new_account("ACCT-1")
    # Purchase ₹1000 (100000 paise) -> 10 points
    account = apply_reward_event(
        account,
        {"event_id": "EV-P1", "type": "purchase_captured", "transaction_id": "TX-1", "amount_paise": 100000},
        rules,
    )
    assert account["points_balance"] == 10

    # Partial refund 1: ₹300 (30000 paise) -> 3 points reversed
    account = apply_reward_event(
        account,
        {"event_id": "EV-R1", "type": "refund_processed", "transaction_id": "TX-1", "amount_paise": 30000},
        rules,
    )
    assert account["points_balance"] == 7
    assert account["transactions"]["TX-1"]["refunded_paise"] == 30000
    assert account["transactions"]["TX-1"]["reversed_points"] == 3

    # Partial refund 2: ₹300 (30000 paise) -> cumulative 60000 paise -> 6 points total reversed (delta = 3)
    account = apply_reward_event(
        account,
        {"event_id": "EV-R2", "type": "refund_processed", "transaction_id": "TX-1", "amount_paise": 30000},
        rules,
    )
    assert account["points_balance"] == 4
    assert account["transactions"]["TX-1"]["refunded_paise"] == 60000
    assert account["transactions"]["TX-1"]["reversed_points"] == 6

    # Partial refund 3: ₹400 (40000 paise) -> cumulative 100000 paise -> 10 points total reversed (delta = 4)
    account = apply_reward_event(
        account,
        {"event_id": "EV-R3", "type": "refund_processed", "transaction_id": "TX-1", "amount_paise": 40000},
        rules,
    )
    assert account["points_balance"] == 0
    assert account["transactions"]["TX-1"]["refunded_paise"] == 100000
    assert account["transactions"]["TX-1"]["reversed_points"] == 10

    # Over-refund attempt: ₹1 (1 paise) -> exceeds total purchase amount -> ignored
    account_before = deepcopy(account)
    account = apply_reward_event(
        account,
        {"event_id": "EV-R4", "type": "refund_processed", "transaction_id": "TX-1", "amount_paise": 1},
        rules,
    )
    assert account == account_before


def test_refund_replay_is_idempotent():
    rules = {"points_per_100_rupees": 1}
    account = new_account("ACCT-1")
    account = apply_reward_event(
        account,
        {"event_id": "EV-P1", "type": "purchase_captured", "transaction_id": "TX-1", "amount_paise": 100000},
        rules,
    )
    refund_event = {"event_id": "EV-R1", "type": "refund_processed", "transaction_id": "TX-1", "amount_paise": 50000}
    account = apply_reward_event(account, refund_event, rules)
    assert account["points_balance"] == 5
    assert len(account["ledger"]) == 2

    # Replay same refund event
    account_replayed = apply_reward_event(account, refund_event, rules)
    assert account_replayed["points_balance"] == 5
    assert len(account_replayed["ledger"]) == 2
    assert account_replayed["processed_event_ids"] == ["EV-P1", "EV-R1"]


def test_refund_never_results_in_negative_points_balance():
    rules = {"points_per_100_rupees": 1}
    # Account starts with manual balance of 2 points (or points spent)
    account = new_account("ACCT-1")
    account["points_balance"] = 2
    account["transactions"]["TX-1"] = {
        "amount_paise": 100000,
        "awarded_points": 10,
        "reversed_points": 0,
        "refunded_paise": 0,
    }

    # Refund full ₹1000 (100000 paise) which normally reverses 10 points
    account = apply_reward_event(
        account,
        {"event_id": "EV-R1", "type": "refund_processed", "transaction_id": "TX-1", "amount_paise": 100000},
        rules,
    )
    # Balance must never drop below 0
    assert account["points_balance"] == 0
    assert account["transactions"]["TX-1"]["reversed_points"] == 2
    assert account["ledger"][-1]["points_delta"] == -2


def test_missing_or_empty_identifiers_safe():
    rules = {"points_per_100_rupees": 1}
    account = new_account("ACCT-1")

    # Missing event_id
    res = apply_reward_event(account, {"type": "purchase_captured", "transaction_id": "TX-1", "amount_paise": 50000}, rules)
    assert res["points_balance"] == 0
    assert len(res["processed_event_ids"]) == 0

    # Empty string event_id
    res = apply_reward_event(account, {"event_id": "", "type": "purchase_captured", "transaction_id": "TX-1", "amount_paise": 50000}, rules)
    assert res["points_balance"] == 0

    # Missing transaction_id
    res = apply_reward_event(account, {"event_id": "E1", "type": "purchase_captured", "amount_paise": 50000}, rules)
    assert res["points_balance"] == 0

    # Empty event or account
    res = apply_reward_event({}, {}, rules)
    assert res["points_balance"] == 0


def test_duplicate_purchase_transaction_id_rejected():
    rules = {"points_per_100_rupees": 1}
    account = new_account("ACCT-1")
    account = apply_reward_event(
        account,
        {"event_id": "E1", "type": "purchase_captured", "transaction_id": "TX-1", "amount_paise": 50000},
        rules,
    )
    assert account["points_balance"] == 5

    # New event_id but duplicate transaction_id
    account_dup = apply_reward_event(
        account,
        {"event_id": "E2", "type": "purchase_captured", "transaction_id": "TX-1", "amount_paise": 50000},
        rules,
    )
    assert account_dup["points_balance"] == 5
    assert len(account_dup["ledger"]) == 1
    assert "E2" not in account_dup["processed_event_ids"]


def test_flag_repeat_transactions_edge_cases():
    # Empty or non-list input
    assert flag_repeat_transactions(None) == []
    assert flag_repeat_transactions([]) == []
    assert flag_repeat_transactions("invalid") == []

    # Non-dict elements ignored
    rows = [
        {"transaction_id": "1", "account_id": "A", "date": "2026-10-01", "amount_paise": 1000},
        "not-a-dict",
        None,
        {"transaction_id": "2", "account_id": "A", "date": "2026-10-01", "amount_paise": 1000},
        {"transaction_id": "3", "account_id": "A", "date": "2026-10-01", "amount_paise": 1000},
    ]
    alerts = flag_repeat_transactions(rows, threshold=2)
    assert len(alerts) == 1
    assert alerts[0]["transaction_ids"] == ["1", "2", "3"]
