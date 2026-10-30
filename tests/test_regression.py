import pytest

from service import (
    calculate_points,
    apply_reward_event,
    flag_repeat_transactions
)


def create_account():
    return {
        "points_balance": 0,
        "processed_event_ids": [],
        "transactions": {},
        "ledger": []
    }


@pytest.mark.parametrize(
    "amount, rate, bonus, cap, expected",
    [
        (10000, 10, 0, None, 10),
        (25000, 10, 25, None, 25),
        (25000, 10, 25, 22, 22),
        (9999, 10, 0, None, 0),
        (-1000, 10, 0, None, 0)
    ]
)
def test_calculate_points(amount, rate, bonus, cap, expected):
    assert calculate_points(amount, rate, bonus, cap) == expected


def test_duplicate_event_is_not_processed_twice():
    account = create_account()

    event = {
        "event_id": "event-1",
        "type": "purchase_captured",
        "transaction_id": "txn-1",
        "amount_paise": 50000
    }

    rules = {"points_per_100_rupees": 10}

    first = apply_reward_event(account, event, rules)
    second = apply_reward_event(first, event, rules)

    assert first["points_balance"] == 50
    assert second["points_balance"] == 50
    assert len(second["ledger"]) == 1


def test_partial_refund_reverses_correct_points():
    account = create_account()
    rules = {
        "points_per_100_rupees": 10,
        "bonus_percent": 20
    }

    purchase = {
        "event_id": "event-1",
        "type": "purchase_captured",
        "transaction_id": "txn-1",
        "amount_paise": 50000
    }

    account = apply_reward_event(account, purchase, rules)

    refund = {
        "event_id": "event-2",
        "type": "refund_processed",
        "transaction_id": "txn-1",
        "amount_paise": 25000
    }

    account = apply_reward_event(account, refund, rules)

    assert account["points_balance"] == 30
    assert account["ledger"][-1]["points_delta"] == -30


def test_refund_cannot_exceed_remaining_amount():
    account = create_account()
    rules = {"points_per_100_rupees": 10}

    purchase = {
        "event_id": "event-1",
        "type": "purchase_captured",
        "transaction_id": "txn-1",
        "amount_paise": 50000
    }

    account = apply_reward_event(account, purchase, rules)

    refund = {
        "event_id": "event-2",
        "type": "refund_processed",
        "transaction_id": "txn-1",
        "amount_paise": 60000
    }

    updated = apply_reward_event(account, refund, rules)

    assert updated["points_balance"] == 50
    assert updated["transactions"]["txn-1"]["refunded_paise"] == 0


def test_repeat_transactions_threshold():
    transactions = [
        {
            "account_id": "A1",
            "date": "2026-10-31",
            "amount_paise": 10000,
            "transaction_id": "T1"
        },
        {
            "account_id": "A1",
            "date": "2026-10-31",
            "amount_paise": 10000,
            "transaction_id": "T2"
        },
        {
            "account_id": "A1",
            "date": "2026-10-31",
            "amount_paise": 10000,
            "transaction_id": "T3"
        }
    ]

    result = flag_repeat_transactions(transactions)

    assert len(result) == 1
    assert len(result[0]["transaction_ids"]) == 3
