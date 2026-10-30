from __future__ import annotations

from copy import deepcopy


def calculate_points(
    amount_paise: int,
    points_per_100_rupees: int,
    bonus_percent: int = 0,
    cap_points: int | None = None,
) -> int:
    """Calculate loyalty reward points using integer floor arithmetic.

    Formula:
    base_points = floor(amount_paise / 10000) * points_per_100_rupees
    bonus_points = floor(base_points * (100 + bonus_percent) / 100)
    Apply optional cap_points last. A cap of zero means zero points.
    Negative or invalid inputs yield zero points.
    """
    if not isinstance(amount_paise, int) or isinstance(amount_paise, bool):
        return 0
    if not isinstance(points_per_100_rupees, int) or isinstance(points_per_100_rupees, bool):
        return 0

    if bonus_percent is None:
        bonus_percent = 0
    elif not isinstance(bonus_percent, int) or isinstance(bonus_percent, bool):
        return 0

    if amount_paise <= 0 or points_per_100_rupees <= 0 or bonus_percent < 0:
        return 0

    if cap_points is not None:
        if not isinstance(cap_points, int) or isinstance(cap_points, bool) or cap_points < 0:
            return 0

    base_points = (amount_paise // 10000) * points_per_100_rupees
    bonus_points = (base_points * (100 + bonus_percent)) // 100
    points = bonus_points
    if cap_points is not None:
        points = min(points, cap_points)
    return max(0, points)


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    """Process a loyalty reward event idempotently and update ledger and transactions."""
    out = deepcopy(account) if isinstance(account, dict) else {}

    # Sanitize account fields against null, missing, negative, or wrong container types
    if not isinstance(out.get("points_balance"), int) or isinstance(out.get("points_balance"), bool) or out["points_balance"] < 0:
        out["points_balance"] = 0

    if not isinstance(out.get("processed_event_ids"), list):
        out["processed_event_ids"] = []

    if not isinstance(out.get("transactions"), dict):
        out["transactions"] = {}

    if not isinstance(out.get("ledger"), list):
        out["ledger"] = []

    if not isinstance(event, dict):
        return out

    event_id = event.get("event_id")
    kind = event.get("type")
    txn_id = event.get("transaction_id")

    if not event_id or not isinstance(event_id, str) or not event_id.strip():
        return out
    if event_id in out["processed_event_ids"]:
        return out
    if not txn_id or not isinstance(txn_id, str) or not txn_id.strip():
        return out

    # Guard against cross-account event mismatch if both account_ids are present
    event_account_id = event.get("account_id")
    account_id = out.get("account_id")
    if event_account_id and account_id and str(event_account_id) != str(account_id):
        return out

    rules = rules if isinstance(rules, dict) else {}
    per = rules.get("points_per_100_rupees")
    if per is None:
        per = 1
    bonus = rules.get("bonus_percent")
    if bonus is None:
        bonus = 0
    cap = rules.get("cap_points")

    if kind == "purchase_captured":
        amount = event.get("amount_paise")
        if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
            return out
        if txn_id in out["transactions"]:
            return out

        points = calculate_points(amount, per, bonus, cap)
        out["transactions"][txn_id] = {
            "amount_paise": amount,
            "awarded_points": points,
            "reversed_points": 0,
            "refunded_paise": 0,
        }
        out["points_balance"] += points
        out["ledger"].append({
            "event_id": event_id,
            "type": kind,
            "points_delta": points,
        })
        out["processed_event_ids"].append(event_id)

    elif kind == "refund_processed":
        if txn_id not in out["transactions"]:
            return out
        txn = out["transactions"].get(txn_id)
        if not isinstance(txn, dict):
            return out

        # Sanitize transaction records against malformed internal states
        amount_paise = txn.get("amount_paise", 0)
        awarded_points = txn.get("awarded_points", 0)
        reversed_points = txn.get("reversed_points", 0)
        refunded_paise = txn.get("refunded_paise", 0)

        if not isinstance(amount_paise, int) or isinstance(amount_paise, bool) or amount_paise <= 0:
            return out
        if not isinstance(awarded_points, int) or isinstance(awarded_points, bool) or awarded_points < 0:
            awarded_points = 0
        if not isinstance(reversed_points, int) or isinstance(reversed_points, bool) or reversed_points < 0:
            reversed_points = 0
        if not isinstance(refunded_paise, int) or isinstance(refunded_paise, bool) or refunded_paise < 0:
            refunded_paise = 0

        refund = event.get("amount_paise")
        if not isinstance(refund, int) or isinstance(refund, bool) or refund <= 0:
            return out
        if refunded_paise + refund > amount_paise:
            return out

        new_refunded = refunded_paise + refund
        should_reverse = (awarded_points * new_refunded) // amount_paise
        should_reverse = min(should_reverse, awarded_points)
        delta = should_reverse - reversed_points
        delta = max(0, delta)
        delta = min(delta, max(0, out["points_balance"]))

        out["points_balance"] -= delta
        txn["refunded_paise"] = new_refunded
        txn["reversed_points"] = reversed_points + delta
        out["ledger"].append({
            "event_id": event_id,
            "type": kind,
            "points_delta": -delta,
        })
        out["processed_event_ids"].append(event_id)

    return out


def flag_repeat_transactions(transactions: list[dict], threshold: int = 2) -> list[dict]:
    """Group transactions by (account_id, date, amount_paise) and flag groups exceeding threshold."""
    if not isinstance(transactions, list):
        return []
    if threshold is None or not isinstance(threshold, int) or isinstance(threshold, bool):
        threshold = 2

    groups = {}
    for tx in transactions:
        if not isinstance(tx, dict):
            continue
        key = (tx.get("account_id"), tx.get("date"), tx.get("amount_paise"))
        groups.setdefault(key, []).append(tx.get("transaction_id"))

    return [
        {
            "account_id": k[0],
            "date": k[1],
            "amount_paise": k[2],
            "transaction_ids": ids,
        }
        for k, ids in sorted(groups.items(), key=lambda item: str(item[0]))
        if len(ids) > threshold
    ]
