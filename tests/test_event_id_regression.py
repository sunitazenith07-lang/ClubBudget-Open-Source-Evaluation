"""Regression tests for event_id handling: None guard and idempotency."""
from models import new_account
from service import apply_reward_event


RULES = {"points_per_100_rupees": 1}


# --- None event_id: two different purchases must both be safely rejected ---

def test_none_event_id_purchase_is_rejected():
    """A purchase with event_id=None must not change balance or ledger."""
    a = apply_reward_event(
        new_account("A"),
        {"event_id": None, "type": "purchase_captured", "transaction_id": "T1", "amount_paise": 50000},
        RULES,
    )
    assert a["points_balance"] == 0
    assert a["transactions"] == {}
    assert a["ledger"] == []
    assert a["processed_event_ids"] == []


def test_missing_event_id_key_purchase_is_rejected():
    """A purchase dict with no event_id key at all must not change balance."""
    a = apply_reward_event(
        new_account("A"),
        {"type": "purchase_captured", "transaction_id": "T1", "amount_paise": 50000},
        RULES,
    )
    assert a["points_balance"] == 0
    assert a["transactions"] == {}
    assert a["processed_event_ids"] == []


def test_two_different_purchases_with_none_event_id_both_rejected():
    """Two unrelated purchases both missing event_id must both be rejected,
    not silently drop the second via a None-to-None collision."""
    a = new_account("A")
    e1 = {"type": "purchase_captured", "transaction_id": "T1", "amount_paise": 50000}
    e2 = {"type": "purchase_captured", "transaction_id": "T2", "amount_paise": 80000}
    a = apply_reward_event(a, e1, RULES)
    a = apply_reward_event(a, e2, RULES)
    assert a["points_balance"] == 0
    assert "T1" not in a["transactions"]
    assert "T2" not in a["transactions"]
    assert a["processed_event_ids"] == []


def test_none_event_id_refund_is_rejected():
    """A refund with event_id=None must not reverse points."""
    a = apply_reward_event(
        new_account("A"),
        {"event_id": "E1", "type": "purchase_captured", "transaction_id": "T1", "amount_paise": 100000},
        RULES,
    )
    assert a["points_balance"] == 10
    b = apply_reward_event(
        a,
        {"event_id": None, "type": "refund_processed", "transaction_id": "T1", "amount_paise": 50000},
        RULES,
    )
    assert b["points_balance"] == 10
    assert b["transactions"]["T1"]["refunded_paise"] == 0


# --- Valid event_id idempotency must still work ---

def test_valid_event_id_duplicate_purchase_is_idempotent():
    """Replaying the same event_id must not award points twice."""
    a = new_account("A")
    event = {"event_id": "E1", "type": "purchase_captured", "transaction_id": "T1", "amount_paise": 50000}
    a = apply_reward_event(a, event, RULES)
    b = apply_reward_event(a, event, RULES)
    assert a["points_balance"] == 5
    assert b["points_balance"] == 5
    assert b["processed_event_ids"] == ["E1"]
    assert len(b["ledger"]) == 1


def test_valid_event_id_duplicate_refund_is_idempotent():
    """Replaying the same refund event_id must not reverse points twice."""
    a = new_account("A")
    a = apply_reward_event(a, {"event_id": "E1", "type": "purchase_captured", "transaction_id": "T1", "amount_paise": 100000}, RULES)
    a = apply_reward_event(a, {"event_id": "E2", "type": "refund_processed", "transaction_id": "T1", "amount_paise": 50000}, RULES)
    b = apply_reward_event(a, {"event_id": "E2", "type": "refund_processed", "transaction_id": "T1", "amount_paise": 50000}, RULES)
    assert a["points_balance"] == 5
    assert b["points_balance"] == 5
    assert b["transactions"]["T1"]["refunded_paise"] == 50000


# --- Existing event processing behaviour preserved ---

def test_distinct_valid_event_ids_both_processed():
    """Two purchases with different valid event_ids and different txn_ids
    must both be processed normally."""
    a = new_account("A")
    a = apply_reward_event(a, {"event_id": "E1", "type": "purchase_captured", "transaction_id": "T1", "amount_paise": 50000}, RULES)
    a = apply_reward_event(a, {"event_id": "E2", "type": "purchase_captured", "transaction_id": "T2", "amount_paise": 80000}, RULES)
    assert a["points_balance"] == 5 + 8
    assert "T1" in a["transactions"]
    assert "T2" in a["transactions"]
    assert a["processed_event_ids"] == ["E1", "E2"]
    assert len(a["ledger"]) == 2


def test_purchase_then_refund_with_valid_event_ids():
    """A normal purchase followed by a valid partial refund must work."""
    a = new_account("A")
    a = apply_reward_event(a, {"event_id": "E1", "type": "purchase_captured", "transaction_id": "T1", "amount_paise": 100000}, RULES)
    a = apply_reward_event(a, {"event_id": "E2", "type": "refund_processed", "transaction_id": "T1", "amount_paise": 50000}, RULES)
    assert a["points_balance"] == 5
    assert a["transactions"]["T1"]["reversed_points"] == 5
    assert a["transactions"]["T1"]["refunded_paise"] == 50000
    assert a["processed_event_ids"] == ["E1", "E2"]


def test_input_account_not_mutated_by_none_event_id():
    """Even when event_id is None, the original account must not be mutated."""
    a = new_account("A")
    original_balance = a["points_balance"]
    apply_reward_event(a, {"type": "purchase_captured", "transaction_id": "T1", "amount_paise": 50000}, RULES)
    assert a["points_balance"] == original_balance
    assert a["transactions"] == {}
