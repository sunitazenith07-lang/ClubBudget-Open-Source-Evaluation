import pytest
from models import new_account
from service import calculate_points, apply_reward_event, flag_repeat_transactions


def test_multi_step_partial_refund():
    # Make sure splitting refunds (e.g. 30% + 30% + 40%) reverses all 10 points without rounding loss
    rules = {"points_per_100_rupees": 1}
    account = new_account("A1")

    account = apply_reward_event(
        account,
        {"event_id": "P1", "type": "purchase_captured", "transaction_id": "T1", "amount_paise": 100000},
        rules,
    )
    assert account["points_balance"] == 10

    # 30% refund -> 3 points
    account = apply_reward_event(
        account,
        {"event_id": "R1", "type": "refund_processed", "transaction_id": "T1", "amount_paise": 30000},
        rules,
    )
    assert account["points_balance"] == 7

    # Another 30% refund -> 3 points
    account = apply_reward_event(
        account,
        {"event_id": "R2", "type": "refund_processed", "transaction_id": "T1", "amount_paise": 30000},
        rules,
    )
    assert account["points_balance"] == 4

    # Final 40% refund -> 4 points (total 10)
    account = apply_reward_event(
        account,
        {"event_id": "R3", "type": "refund_processed", "transaction_id": "T1", "amount_paise": 40000},
        rules,
    )
    assert account["points_balance"] == 0
    assert sum(e["points_delta"] for e in account["ledger"]) == 0


def test_refund_replay_does_not_duplicate():
    rules = {"points_per_100_rupees": 1}
    account = apply_reward_event(
        new_account("A"),
        {"event_id": "P1", "type": "purchase_captured", "transaction_id": "T1", "amount_paise": 100000},
        rules,
    )
    refund = {"event_id": "R1", "type": "refund_processed", "transaction_id": "T1", "amount_paise": 50000}
    a1 = apply_reward_event(account, refund, rules)
    assert a1["points_balance"] == 5

    # Replaying same refund event should not reverse again or add duplicate ledger entry
    a2 = apply_reward_event(a1, refund, rules)
    assert a2["points_balance"] == 5
    assert a2["processed_event_ids"] == ["P1", "R1"]
    assert len(a2["ledger"]) == 2


def test_boolean_values_rejected():
    # In Python bool is a subclass of int, so isinstance(True, int) is True
    # We need to make sure booleans are rejected
    assert calculate_points(True, 1) == 0
    assert calculate_points(False, 1) == 0
    assert calculate_points(10000, True) == 0
    assert calculate_points(10000, 1, True) == 0
    assert calculate_points(10000, 1, 0, True) == 0


def test_excess_refund_rejected_after_partial():
    rules = {"points_per_100_rupees": 1}
    account = apply_reward_event(
        new_account("A"),
        {"event_id": "P", "type": "purchase_captured", "transaction_id": "T", "amount_paise": 100000},
        rules,
    )
    # Valid 60k refund
    account = apply_reward_event(
        account,
        {"event_id": "R1", "type": "refund_processed", "transaction_id": "T", "amount_paise": 60000},
        rules,
    )
    assert account["points_balance"] == 4

    # Try to refund another 50k (60k + 50k = 110k > 100k purchase) -> should be rejected
    account2 = apply_reward_event(
        account,
        {"event_id": "R2", "type": "refund_processed", "transaction_id": "T", "amount_paise": 50000},
        rules,
    )
    assert account2["points_balance"] == 4
    assert account2["transactions"]["T"]["refunded_paise"] == 60000


def test_ledger_sum_matches_balance():
    rules = {"points_per_100_rupees": 2, "bonus_percent": 10}
    account = new_account("A")
    account = apply_reward_event(
        account,
        {"event_id": "E1", "type": "purchase_captured", "transaction_id": "T1", "amount_paise": 50000},
        rules,
    )
    account = apply_reward_event(
        account,
        {"event_id": "E2", "type": "purchase_captured", "transaction_id": "T2", "amount_paise": 100000},
        rules,
    )
    account = apply_reward_event(
        account,
        {"event_id": "E3", "type": "refund_processed", "transaction_id": "T2", "amount_paise": 50000},
        rules,
    )
    # Balance must match the sum of all ledger point deltas
    assert account["points_balance"] == sum(e["points_delta"] for e in account["ledger"])


def test_repeat_transactions_empty_and_sorting():
    assert flag_repeat_transactions([]) == []
    rows = [
        {"transaction_id": "2", "account_id": "B", "date": "D", "amount_paise": 100},
        {"transaction_id": "1", "account_id": "A", "date": "D", "amount_paise": 100},
        {"transaction_id": "3", "account_id": "A", "date": "D", "amount_paise": 100},
        {"transaction_id": "4", "account_id": "A", "date": "D", "amount_paise": 100},
    ]
    alerts = flag_repeat_transactions(rows, threshold=2)
    assert len(alerts) == 1
    assert alerts[0]["account_id"] == "A"
