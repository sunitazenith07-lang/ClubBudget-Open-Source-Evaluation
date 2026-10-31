from copy import deepcopy
from numbers import Integral


def _is_int(value):
    """Return True for integer values, excluding bool (which subclasses int)."""
    return isinstance(value, Integral) and not isinstance(value, bool)


def calculate_points(amount_paise: int, points_per_100_rupees: int, bonus_percent: int = 0,
                     cap_points: int | None = None) -> int:
    """Calculate whole points using floor-based integer arithmetic."""
    if not all(_is_int(value) for value in (amount_paise, points_per_100_rupees, bonus_percent)):
        return 0
    if amount_paise <= 0 or points_per_100_rupees < 0 or bonus_percent < 0:
        return 0
    if cap_points is not None and (not _is_int(cap_points) or cap_points < 0):
        return 0

    base_points = (amount_paise // 10000) * points_per_100_rupees
    points = base_points * (100 + bonus_percent) // 100
    if cap_points is not None:
        points = min(points, cap_points)
    return max(0, points)


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    """Apply one valid reward event without mutating the caller's account."""
    out = deepcopy(account)
    out.setdefault("points_balance", 0)
    out.setdefault("processed_event_ids", [])
    out.setdefault("transactions", {})
    out.setdefault("ledger", [])

    if not isinstance(event, dict) or not isinstance(rules, dict):
        return out

    event_id = event.get("event_id")
    kind = event.get("type")
    txn_id = event.get("transaction_id")

    # An event identifier is the idempotency key. Missing IDs are not accepted.
    if not isinstance(event_id, str) or not event_id or event_id in out["processed_event_ids"]:
        return out

    if kind == "purchase_captured":
        amount = event.get("amount_paise")
        if not _is_int(amount) or amount <= 0 or not isinstance(txn_id, str) or not txn_id:
            return out
        # A transaction can only be captured once, even with a different event ID.
        if txn_id in out["transactions"]:
            return out
        points = calculate_points(
            amount,
            rules.get("points_per_100_rupees", 1),
            rules.get("bonus_percent", 0),
            rules.get("cap_points"),
        )
        out["transactions"][txn_id] = {
            "amount_paise": amount,
            "awarded_points": points,
            "reversed_points": 0,
            "refunded_paise": 0,
        }
        out["points_balance"] += points
        out["ledger"].append({"event_id": event_id, "type": kind, "points_delta": points})
        out["processed_event_ids"].append(event_id)

    elif kind == "refund_processed":
        if not isinstance(txn_id, str) or not txn_id or txn_id not in out["transactions"]:
            return out
        refund = event.get("amount_paise")
        if not _is_int(refund) or refund <= 0:
            return out
        txn = out["transactions"][txn_id]
        original_amount = txn.get("amount_paise")
        already_refunded = txn.get("refunded_paise", 0)
        if not _is_int(original_amount) or original_amount <= 0:
            return out
        if refund > original_amount - already_refunded:
            return out

        txn["refunded_paise"] += refund
        should_reverse = txn["awarded_points"] * txn["refunded_paise"] // original_amount
        should_reverse = min(txn["awarded_points"], should_reverse)
        delta = should_reverse - txn["reversed_points"]
        txn["reversed_points"] = should_reverse
        out["points_balance"] = max(0, out["points_balance"] - delta)
        out["ledger"].append({"event_id": event_id, "type": kind, "points_delta": -delta})
        out["processed_event_ids"].append(event_id)

    return out


def flag_repeat_transactions(transactions: list[dict], threshold: int = 2) -> list[dict]:
    """Group possible repeats by account, date and amount for human review."""
    if not isinstance(transactions, list):
        return []
    if not _is_int(threshold):
        threshold = 2
    threshold = max(0, threshold)
    groups = {}
    for tx in transactions:
        if not isinstance(tx, dict):
            continue
        key = (tx.get("account_id"), tx.get("date"), tx.get("amount_paise"))
        groups.setdefault(key, []).append(tx.get("transaction_id"))
    return [
        {"account_id": key[0], "date": key[1], "amount_paise": key[2], "transaction_ids": ids}
        for key, ids in sorted(groups.items(), key=lambda item: str(item[0]))
        if len(ids) > threshold
    ]
