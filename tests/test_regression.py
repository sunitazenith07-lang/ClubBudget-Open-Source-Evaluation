from models import new_account
from service import calculate_points, apply_reward_event


def test_floor_not_round_at_boundaries():
    assert calculate_points(9999, 1) == 0
    assert calculate_points(19999, 1) == 1


def test_cap_zero_is_respected_for_any_amount():
    assert calculate_points(50000, 1, cap_points=0) == 0
    assert calculate_points(100000, 2, 50, 0) == 0


def test_negative_amounts_never_award():
    assert calculate_points(-1, 1) == 0
    assert calculate_points(-100000, 1) == 0


def test_replayed_purchase_event_awards_once():
    account = new_account("A")
    event = {"event_id": "E1", "type": "purchase_captured", "transaction_id": "T", "amount_paise": 25000}
    rules = {"points_per_100_rupees": 1}
    first = apply_reward_event(account, event, rules)
    second = apply_reward_event(first, event, rules)
    assert first["points_balance"] == 2
    assert second["points_balance"] == 2
    assert len(second["ledger"]) == 1
    assert second["processed_event_ids"] == ["E1"]


def test_replayed_refund_event_reverses_once():
    rules = {"points_per_100_rupees": 1}
    account = apply_reward_event(new_account("A"), {"event_id": "P", "type": "purchase_captured", "transaction_id": "T", "amount_paise": 100000}, rules)
    event = {"event_id": "R", "type": "refund_processed", "transaction_id": "T", "amount_paise": 50000}
    once = apply_reward_event(account, event, rules)
    twice = apply_reward_event(once, event, rules)
    assert once["points_balance"] == 5
    assert twice["points_balance"] == 5
    assert len(twice["ledger"]) == 2


def test_boolean_refund_rejected():
    rules = {"points_per_100_rupees": 1}
    account = apply_reward_event(new_account("A"), {"event_id": "P", "type": "purchase_captured", "transaction_id": "T", "amount_paise": 100000}, rules)
    for bad in (True, False):
        result = apply_reward_event(account, {"event_id": "R", "type": "refund_processed", "transaction_id": "T", "amount_paise": bad}, rules)
        assert result["transactions"]["T"]["refunded_paise"] == 0
        assert result["points_balance"] == 10


def test_cumulative_refunds_cannot_exceed_purchase():
    rules = {"points_per_100_rupees": 1}
    account = apply_reward_event(new_account("A"), {"event_id": "P", "type": "purchase_captured", "transaction_id": "T", "amount_paise": 100000}, rules)
    first = apply_reward_event(account, {"event_id": "R1", "type": "refund_processed", "transaction_id": "T", "amount_paise": 60000}, rules)
    assert first["points_balance"] == 4
    second = apply_reward_event(first, {"event_id": "R2", "type": "refund_processed", "transaction_id": "T", "amount_paise": 60000}, rules)
    assert second["transactions"]["T"]["refunded_paise"] == 60000
    assert second["points_balance"] == 4