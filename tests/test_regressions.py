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


def create_rules():
    return {
        "points_per_100_rupees": 10,
        "bonus_percent": 0
    }


def test_negative_amount():
    assert calculate_points(-10000, 10) == 0


def test_zero_cap():
    assert calculate_points(10000, 10, cap_points=0) == 0


def test_duplicate_event():
    account = create_account()
    event = {
        "event_id": "E001",
        "type": "purchase_captured",
        "transaction_id": "T001",
        "amount_paise": 10000
    }

    first = apply_reward_event(account, event, create_rules())
    second = apply_reward_event(first, event, create_rules())

    assert second["points_balance"] == 10
    assert len(second["ledger"]) == 1


def test_refund_greater_than_purchase():
    account = create_account()

    purchase = {
        "event_id": "E001",
        "type": "purchase_captured",
        "transaction_id": "T001",
        "amount_paise": 10000
    }

    account = apply_reward_event(account, purchase, create_rules())

    refund = {
        "event_id": "E002",
        "type": "refund_processed",
        "transaction_id": "T001",
        "amount_paise": 15000
    }

    result = apply_reward_event(account, refund, create_rules())

    assert result["points_balance"] == 10
    assert len(result["ledger"]) == 1


def test_unknown_transaction_refund():
    account = create_account()

    refund = {
        "event_id": "E001",
        "type": "refund_processed",
        "transaction_id": "UNKNOWN",
        "amount_paise": 5000
    }

    result = apply_reward_event(account, refund, create_rules())

    assert result["points_balance"] == 0
    assert len(result["ledger"]) == 0


def test_partial_refund():
    account = create_account()

    purchase = {
        "event_id": "E001",
        "type": "purchase_captured",
        "transaction_id": "T001",
        "amount_paise": 10000
    }

    account = apply_reward_event(account, purchase, create_rules())

    refund = {
        "event_id": "E002",
        "type": "refund_processed",
        "transaction_id": "T001",
        "amount_paise": 5000
    }

    result = apply_reward_event(account, refund, create_rules())

    assert result["points_balance"] == 5
    assert result["transactions"]["T001"]["reversed_points"] == 5


def test_empty_repeat_transactions():
    assert flag_repeat_transactions([]) == []