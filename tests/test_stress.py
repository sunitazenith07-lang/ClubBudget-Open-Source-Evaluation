"""Random inputs from fixed seeds, checked against rules that must always hold."""
import json
import random
from copy import deepcopy
from pathlib import Path

import pytest
from service import apply_reward_event, calculate_points, flag_repeat_transactions

SEEDS = range(5)
RULES = {"points_per_100_rupees": 5, "bonus_percent": 25, "cap_points": 500}
DATA = json.loads((Path(__file__).resolve().parent.parent / "data" / "records.json").read_text())
JUNK = [None, True, False, -1, 0, 1.5, float("nan"), float("inf"), "100", "", [], {}, (), b"x", object()]


# --- points calculation ---------------------------------------------------

def reference_points(amount, rate, bonus, cap):
    # different method on purpose
    units = 0
    while amount >= 10000:
        amount -= 10000
        units += 1
    total = units * rate * (100 + bonus) // 100
    return total if cap is None else min(total, cap)


@pytest.mark.parametrize("seed", SEEDS)
def test_points_match_reference_on_random_inputs(seed):
    rng = random.Random(seed)
    for _ in range(1000):
        amount = rng.choice([rng.randint(1, 10**6), rng.randint(9990, 10010), rng.randint(19990, 20010)])
        rate, bonus = rng.randint(0, 50), rng.randint(0, 400)
        cap = rng.choice([None, 0, rng.randint(0, 2000)])
        points = calculate_points(amount, rate, bonus, cap)
        assert points == reference_points(amount, rate, bonus, cap), (amount, rate, bonus, cap)
        assert type(points) is int and points >= 0
        assert cap is None or points <= cap


@pytest.mark.parametrize("seed", SEEDS)
def test_spending_more_never_earns_fewer_points(seed):
    rng = random.Random(seed)
    rate, bonus, cap = rng.randint(1, 10), rng.randint(0, 100), rng.choice([None, 300])
    previous = 0
    for amount in sorted(rng.randint(1, 5 * 10**6) for _ in range(300)):
        points = calculate_points(amount, rate, bonus, cap)
        assert points >= previous
        previous = points


def test_junk_points_inputs_return_zero_without_crashing():
    for junk in JUNK:
        assert calculate_points(junk, 1) == 0
        assert calculate_points(100000, junk) == 0
        if junk != 0 or junk is False:  # 0 is a valid bonus
            assert calculate_points(100000, 1, junk) == 0
        if junk is not None:  # None = no cap
            assert calculate_points(100000, 1, 0, junk) == 0


# --- reward events --------------------------------------------------------

def random_event(rng):
    return {"event_id": f"E{rng.randint(0, 800)}",
            "type": rng.choice(["purchase_captured"] * 4 + ["refund_processed"] * 4 + ["purchase_declined", "other"]),
            "transaction_id": f"T{rng.randint(0, 15)}",
            "amount_paise": rng.choice([rng.randint(1, 500000), rng.randint(1, 50000), 0, -5, True, "1", 1.0])}


def assert_account_is_consistent(account):
    ledger = account["ledger"]
    assert account["points_balance"] >= 0
    assert account["points_balance"] == sum(e["points_delta"] for e in ledger)
    running = 0
    for entry in ledger:
        running += entry["points_delta"]
        assert entry["balance_after"] == running
    assert len(ledger) == len(account["processed_event_ids"]) == len(set(account["processed_event_ids"]))
    for txn in account["transactions"].values():
        assert 0 <= txn["refunded_paise"] <= txn["amount_paise"]
        assert 0 <= txn["reversed_points"] <= txn["awarded_points"]


@pytest.mark.parametrize("seed", SEEDS)
def test_random_event_streams_keep_account_consistent(seed):
    rng = random.Random(seed)
    account = {}
    for _ in range(1000):
        event = random_event(rng)
        before = deepcopy(account)
        updated = apply_reward_event(account, event, RULES)
        assert account == before, "the input account must not be changed"
        assert apply_reward_event(updated, event, RULES) == updated, "sending the same event again must do nothing"
        assert_account_is_consistent(updated)
        account = updated


@pytest.mark.parametrize("seed", SEEDS)
def test_random_partial_refunds_always_end_at_zero(seed):
    rng = random.Random(seed)
    for _ in range(100):
        amount = rng.randint(2, 10**6)
        account = apply_reward_event({}, {"event_id": "P", "type": "purchase_captured", "transaction_id": "T",
                                          "amount_paise": amount}, RULES)
        awarded = account["points_balance"]
        cuts = sorted(rng.sample(range(1, amount), min(amount - 1, rng.randint(0, 8))))
        pieces = [b - a for a, b in zip([0] + cuts, cuts + [amount])]
        for i, piece in enumerate(pieces):
            account = apply_reward_event(account, {"event_id": f"R{i}", "type": "refund_processed",
                                                   "transaction_id": "T", "amount_paise": piece}, RULES)
            txn = account["transactions"]["T"]
            assert txn["reversed_points"] == awarded * txn["refunded_paise"] // amount
        assert account["points_balance"] == 0, (amount, pieces)
        one_more = apply_reward_event(account, {"event_id": "X", "type": "refund_processed",
                                                "transaction_id": "T", "amount_paise": 1}, RULES)
        assert one_more == account


def test_junk_events_and_rules_never_crash():
    account = apply_reward_event({}, {"event_id": "P", "type": "purchase_captured", "transaction_id": "T",
                                      "amount_paise": 100000}, RULES)
    for junk in JUNK + [["list"], {"d": 1}]:
        apply_reward_event(account, junk, RULES)
        for field in ["event_id", "type", "transaction_id", "amount_paise"]:
            event = {"event_id": "N", "type": "refund_processed", "transaction_id": "T", "amount_paise": 100}
            event[field] = junk
            assert_account_is_consistent(apply_reward_event(account, event, RULES))
        for rules in [junk, {"points_per_100_rupees": junk}, {"bonus_percent": junk}, {"cap_points": junk}]:
            assert_account_is_consistent(apply_reward_event({}, {"event_id": "P", "type": "purchase_captured",
                                                                 "transaction_id": "T", "amount_paise": 100000}, rules))


def test_replaying_whole_dataset_twice_in_random_order_changes_nothing():
    account = {}
    for event in DATA["reward_events"]:
        account = apply_reward_event(account, event, RULES)
    assert_account_is_consistent(account)
    again = account
    for event in random.Random(1).sample(DATA["reward_events"], len(DATA["reward_events"])):
        again = apply_reward_event(again, event, RULES)
    assert again == account


# --- repeat alerts --------------------------------------------------------

def reference_alerts(transactions, threshold):
    groups = {}
    for tx in transactions:
        key = (tx.get("account_id"), tx.get("date"), tx.get("amount_paise"))
        if None in key[:2] or tx.get("transaction_id") is None or type(key[2]) is not int or key[2] <= 0:
            continue
        groups.setdefault(key, []).append(tx["transaction_id"])
    return {k: sorted(v) for k, v in groups.items() if len(v) > max(threshold, 1)}


def random_transaction(rng, i):
    return {"transaction_id": f"TX{i}", "account_id": rng.choice(["A", "B", "C", None]),
            "date": rng.choice(["2026-01-01", "2026-01-02", None]),
            "amount_paise": rng.choice([100, 200, 0, -1, True, "100", 100.0])}


@pytest.mark.parametrize("seed", SEEDS)
def test_alerts_match_reference_on_random_inputs(seed):
    rng = random.Random(seed)
    transactions = [random_transaction(rng, i) for i in range(rng.randint(0, 300))]
    threshold = rng.randint(-2, 6)
    alerts = flag_repeat_transactions(transactions, threshold)
    assert {(a["account_id"], a["date"], a["amount_paise"]): a["transaction_ids"] for a in alerts} \
        == reference_alerts(transactions, threshold)
    assert all(a["status"] == "needs_review" and a["count"] == len(a["transaction_ids"]) for a in alerts)


@pytest.mark.parametrize("seed", SEEDS)
def test_shuffling_transactions_gives_the_same_alerts(seed):
    rng = random.Random(seed)
    transactions = [random_transaction(rng, i) for i in range(200)]
    shuffled = rng.sample(transactions, len(transactions))
    assert flag_repeat_transactions(transactions, 2) == flag_repeat_transactions(shuffled, 2)


def test_junk_transactions_never_crash():
    for junk in JUNK + [["list"], {"d": 1}]:
        flag_repeat_transactions([junk], junk)
        for field in ["account_id", "date", "amount_paise", "transaction_id"]:
            tx = {"transaction_id": "T", "account_id": "A", "date": "D", "amount_paise": 100}
            tx[field] = junk
            flag_repeat_transactions([tx, dict(tx), dict(tx)], 1)
