import json
import time
from pathlib import Path

import pytest
from models import new_account
from service import calculate_points, apply_reward_event, flag_repeat_transactions

RULES = {"points_per_100_rupees": 1}
DATA = json.loads((Path(__file__).resolve().parent.parent / "data" / "records.json").read_text())


def purchase(event_id="P", txn="T", amount=100000):
    return {"event_id": event_id, "type": "purchase_captured", "transaction_id": txn, "amount_paise": amount}


def refund(event_id="R", txn="T", amount=50000):
    return {"event_id": event_id, "type": "refund_processed", "transaction_id": txn, "amount_paise": amount}


# --- points calculation ---------------------------------------------------

@pytest.mark.parametrize("per,bonus,cap", [(-1, 10, 100), (1, -100, None), (1, 0, -1), (True, 0, None), (1, "10", None), (1, 0, 1.5)])
def test_invalid_rule_values_award_zero(per, bonus, cap):
    assert calculate_points(100000, per, bonus, cap) == 0


@pytest.mark.parametrize("amount", [None, "100000", 1.5, True, [], {}])
def test_non_integer_amount_awards_zero(amount):
    assert calculate_points(amount, 1) == 0


def test_bonus_over_100_percent_then_cap():
    # 30*3=90 -> 90*250//100=225
    assert calculate_points(300000, 3, 150, 300) == 225
    assert calculate_points(300000, 3, 150, 20) == 20


# --- purchases and idempotency --------------------------------------------

def test_second_capture_of_same_transaction_with_new_event_id_does_not_award_twice():
    a = apply_reward_event(new_account("A"), purchase("P1"), RULES)
    b = apply_reward_event(a, purchase("P2"), RULES)
    assert b["points_balance"] == 10 and len(b["ledger"]) == 1


@pytest.mark.parametrize("missing", ["event_id", "transaction_id"])
def test_event_missing_identifier_is_ignored(missing):
    event = purchase()
    del event[missing]
    out = apply_reward_event(new_account("A"), event, RULES)
    assert out["points_balance"] == 0 and out["ledger"] == [] and out["processed_event_ids"] == []


@pytest.mark.parametrize("field", ["event_id", "transaction_id"])
@pytest.mark.parametrize("bad", [[], {}, ["T"]])
def test_unhashable_identifier_is_ignored_not_crashing(field, bad):
    event = purchase()
    event[field] = bad
    out = apply_reward_event(new_account("A"), event, RULES)
    assert out["points_balance"] == 0 and out["ledger"] == [] and out["transactions"] == {}


@pytest.mark.parametrize("amount", [None, 0, -100, "25000", 1.5, True])
def test_invalid_purchase_amount_creates_no_transaction(amount):
    out = apply_reward_event(new_account("A"), purchase(amount=amount), RULES)
    assert out["transactions"] == {} and out["ledger"] == []


@pytest.mark.parametrize("account", [None, [], "A", 5])
def test_non_dict_account_is_treated_as_empty(account):
    out = apply_reward_event(account, purchase(), RULES)
    assert out == apply_reward_event({}, purchase(), RULES)
    assert out["points_balance"] == 10 and len(out["ledger"]) == 1


def test_rejected_event_id_can_be_retried_with_valid_data():
    a = apply_reward_event(new_account("A"), purchase(amount=None), RULES)
    b = apply_reward_event(a, purchase(), RULES)
    assert b["points_balance"] == 10


# --- refunds ---------------------------------------------------------------

def test_duplicate_refund_event_is_applied_once():
    a = apply_reward_event(new_account("A"), purchase(), RULES)
    b = apply_reward_event(a, refund("R1", amount=30000), RULES)
    c = apply_reward_event(b, refund("R1", amount=30000), RULES)
    assert c["points_balance"] == 7 and c["transactions"]["T"]["refunded_paise"] == 30000


def test_cumulative_refunds_cannot_exceed_purchase():
    a = apply_reward_event(new_account("A"), purchase(), RULES)
    b = apply_reward_event(a, refund("R1", amount=60000), RULES)
    c = apply_reward_event(b, refund("R2", amount=60000), RULES)  # total 120000 > 100000
    assert c["transactions"]["T"]["refunded_paise"] == 60000 and c["points_balance"] == 4


def test_partial_refunds_sum_to_full_reversal():
    a = apply_reward_event(new_account("A"), purchase(amount=25000), RULES)
    for i, amount in enumerate([10000, 10000, 5000]):
        a = apply_reward_event(a, refund(f"R{i}", amount=amount), RULES)
    assert a["points_balance"] == 0 and a["transactions"]["T"]["reversed_points"] == 2


def test_balance_never_negative_even_if_account_already_low():
    a = apply_reward_event(new_account("A"), purchase(), RULES)
    a["points_balance"] = 3  # points spent elsewhere
    b = apply_reward_event(a, refund(amount=100000), RULES)
    assert b["points_balance"] == 0 and b["transactions"]["T"]["reversed_points"] == 3


def test_refund_never_adds_points_to_a_negative_balance():
    a = apply_reward_event(new_account("A"), purchase(), RULES)
    a["points_balance"] = -5  # overdrawn elsewhere
    b = apply_reward_event(a, refund(amount=50000), RULES)
    assert b["points_balance"] == -5 and b["transactions"]["T"]["reversed_points"] == 0
    assert b["ledger"][-1]["points_delta"] == 0


# --- ledger ------------------------------------------------------------------

def test_ledger_entries_are_auditable_and_sum_to_balance():
    a = apply_reward_event(new_account("A"), purchase(), RULES)
    a = apply_reward_event(a, refund(), RULES)
    assert [e["points_delta"] for e in a["ledger"]] == [10, -5]
    assert [e["balance_after"] for e in a["ledger"]] == [10, 5]
    assert all(e["transaction_id"] == "T" and e["event_id"] for e in a["ledger"])
    assert sum(e["points_delta"] for e in a["ledger"]) == a["points_balance"]


def test_dataset_reward_events_keep_ledger_consistent():
    accounts = {}
    for event in DATA["reward_events"]:
        acct = accounts.setdefault(event["account_id"], new_account(event["account_id"]))
        accounts[event["account_id"]] = apply_reward_event(acct, event, DATA["rules_cases"][0])
    for acct in accounts.values():
        assert acct["points_balance"] >= 0
        assert sum(e["points_delta"] for e in acct["ledger"]) == acct["points_balance"]
        assert len(acct["processed_event_ids"]) == len(set(acct["processed_event_ids"]))


# --- repeat alerts -----------------------------------------------------------

def test_empty_input_gives_no_alerts():
    assert flag_repeat_transactions([]) == [] and flag_repeat_transactions(None) == []


@pytest.mark.parametrize("bad_input", [5, "abc", {"account_id": "A"}])
def test_non_list_alert_input_gives_no_alerts(bad_input):
    assert flag_repeat_transactions(bad_input) == []


@pytest.mark.parametrize("threshold", [0, -1])
def test_non_positive_threshold_is_treated_as_one(threshold):
    rows = [{"transaction_id": "1", "account_id": "A", "date": "D", "amount_paise": 1000}]
    assert flag_repeat_transactions(rows, threshold) == []


@pytest.mark.parametrize("threshold", [None, "2", 1.5, True])
def test_invalid_threshold_falls_back_to_default(threshold):
    rows = [{"transaction_id": str(i), "account_id": "A", "date": "D", "amount_paise": 1000} for i in range(3)]
    assert flag_repeat_transactions(rows[:2], threshold) == []
    assert len(flag_repeat_transactions(rows, threshold)) == 1


def test_same_transaction_id_is_not_counted_as_a_repeat():
    row = {"transaction_id": "T1", "account_id": "A", "date": "D", "amount_paise": 1000}
    assert flag_repeat_transactions([row, dict(row), dict(row)], 2) == []
    rows = [row, dict(row), {**row, "transaction_id": "T2"}, {**row, "transaction_id": "T3"}]
    assert flag_repeat_transactions(rows, 2)[0]["transaction_ids"] == ["T1", "T2", "T3"]


def test_rows_missing_keys_are_not_grouped():
    rows = [{"transaction_id": str(i), "account_id": None, "date": "D", "amount_paise": 1000} for i in range(5)]
    assert flag_repeat_transactions(rows, 2) == []


def test_alert_order_is_deterministic_and_marked_for_review():
    rows = [{"transaction_id": f"{acct}{i}", "account_id": acct, "date": "D", "amount_paise": 1000} for acct in ["B", "A"] for i in range(3)]
    result = flag_repeat_transactions(rows, 2)
    assert [r["account_id"] for r in result] == ["A", "B"]
    assert all(r["status"] == "needs_review" and r["count"] == 3 for r in result)


def test_alert_transaction_ids_do_not_depend_on_input_order():
    rows = [{"transaction_id": f"TX{i}", "account_id": "A", "date": "D", "amount_paise": 1000} for i in range(4)]
    result = flag_repeat_transactions(rows, 2)
    assert result == flag_repeat_transactions(list(reversed(rows)), 2)
    assert result[0]["transaction_ids"] == ["TX0", "TX1", "TX2", "TX3"]


@pytest.mark.parametrize("field", ["account_id", "date"])
@pytest.mark.parametrize("bad", [[], {}, ["A"]])
def test_unhashable_alert_keys_are_skipped_not_crashing(field, bad):
    rows = [{"transaction_id": str(i), "account_id": "A", "date": "D", "amount_paise": 1000} for i in range(3)]
    rows[0][field] = bad
    assert flag_repeat_transactions(rows, 1) == [{"account_id": "A", "date": "D", "amount_paise": 1000,
                                                  "transaction_ids": ["1", "2"], "count": 2, "status": "needs_review"}]


def test_unhashable_transaction_id_rows_are_skipped_in_alerts():
    rows = [{"transaction_id": tid, "account_id": "A", "date": "D", "amount_paise": 1000} for tid in ["1", "2", "3", [], {}]]
    result = flag_repeat_transactions(rows, 2)
    assert result[0]["transaction_ids"] == ["1", "2", "3"] and result[0]["count"] == 3


def test_one_huge_repeat_group_stays_fast():
    rows = [{"transaction_id": f"TX{i}", "account_id": "A", "date": "D", "amount_paise": 1000} for i in range(100_000)]
    start = time.perf_counter()
    result = flag_repeat_transactions(rows + rows[:1000], 2)
    assert time.perf_counter() - start < 2  # a list-based id check took 4.2 s for 40,000 rows
    assert result[0]["count"] == 100_000


def test_dataset_repeat_groups_are_flagged():
    result = flag_repeat_transactions(DATA["transactions"], DATA["repeat_alert_threshold"])
    expected = {t["source_group"] for t in DATA["transactions"] if t["amount_paise"] > 0}
    assert len(result) == len(expected)
    assert all(r["count"] == 3 for r in result)
