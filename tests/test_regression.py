from copy import deepcopy
from models import new_account
from service import calculate_points, apply_reward_event, flag_repeat_transactions


def test_regression_purchase_replay_is_idempotent():
    account = new_account("A")
    event = {"event_id": "E1", "type": "purchase_captured", "transaction_id": "T", "amount_paise": 25000}
    rules = {"points_per_100_rupees": 1}
    once = apply_reward_event(account, event, rules)
    twice = apply_reward_event(once, event, rules)
    assert twice["points_balance"] == 2
    assert twice["processed_event_ids"] == ["E1"]
    assert len(twice["ledger"]) == 1


def test_regression_invalid_refund_does_not_change_account():
    rules = {"points_per_100_rupees": 1}
    account = apply_reward_event(new_account("A"), {"event_id": "P", "type": "purchase_captured", "transaction_id": "T", "amount_paise": 100000}, rules)
    before = deepcopy(account)
    for amount in [True, "100", 1.5, -1, 150000]:
        result = apply_reward_event(account, {"event_id": "R", "type": "refund_processed", "transaction_id": "T", "amount_paise": amount}, rules)
        assert result == before


def test_regression_partial_refund_reverses_proportionally():
    rules = {"points_per_100_rupees": 1}
    account = apply_reward_event(new_account("A"), {"event_id": "P", "type": "purchase_captured", "transaction_id": "T", "amount_paise": 100000}, rules)
    result = apply_reward_event(account, {"event_id": "R", "type": "refund_processed", "transaction_id": "T", "amount_paise": 50000}, rules)
    assert result["points_balance"] == 5
    assert result["transactions"]["T"]["reversed_points"] == 5


def test_regression_calculate_points_invalid_and_cap():
    assert calculate_points(-10000, 1) == 0
    assert calculate_points(50000, 1, cap_points=0) == 0
    assert calculate_points(50000, 2, 50, 6) == 6


def test_regression_repeat_threshold_boundary():
    rows = [{"transaction_id": str(i), "account_id": "A", "date": "D", "amount_paise": 1000} for i in range(2)]
    assert flag_repeat_transactions(rows, threshold=2) == []
    rows.append({"transaction_id": "NEXT", "account_id": "A", "date": "D", "amount_paise": 1000})
    assert len(flag_repeat_transactions(rows, threshold=2)) == 1


def test_regression_input_account_not_mutated():
    account = new_account("A")
    before = deepcopy(account)
    apply_reward_event(account, {"event_id": "E", "type": "purchase_captured", "transaction_id": "T", "amount_paise": 10000}, {"points_per_100_rupees": 1})
    assert account == before


def test_regression_unrecognized_event_does_not_award():
    result = apply_reward_event(new_account("A"), {"event_id": "E", "type": "purchase_declined", "transaction_id": "T", "amount_paise": 100000}, {"points_per_100_rupees": 1})
    assert result["points_balance"] == 0
    assert result["transactions"] == {}