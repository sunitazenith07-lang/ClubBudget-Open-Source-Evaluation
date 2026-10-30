"""RewardBook service logic: points calculation, reward event processing, and repeat alert detection."""

from copy import deepcopy


def calculate_points(
    amount_paise: int,
    points_per_100_rupees: int,
    bonus_percent: int = 0,
    cap_points: int | None = None,
) -> int:
    """Calculate reward points earned for a purchase using integer floor arithmetic.

    Formula:
      base_points = floor(amount_paise / 10000) * points_per_100_rupees
      bonus_points = floor(base_points * (100 + bonus_percent) / 100)
      apply optional cap_points last

    Negative or invalid amounts/rules award 0 points. A cap of 0 yields 0 points.
    """
    if isinstance(amount_paise, bool) or not isinstance(amount_paise, int) or amount_paise <= 0:
        return 0

    if (
        isinstance(points_per_100_rupees, bool)
        or not isinstance(points_per_100_rupees, int)
        or points_per_100_rupees <= 0
    ):
        return 0

    if (
        isinstance(bonus_percent, bool)
        or not isinstance(bonus_percent, int)
        or bonus_percent < 0
    ):
        return 0

    if cap_points is not None:
        if isinstance(cap_points, bool) or not isinstance(cap_points, int) or cap_points < 0:
            return 0
        if cap_points == 0:
            return 0

    base_points = (amount_paise // 10000) * points_per_100_rupees
    points = (base_points * (100 + bonus_percent)) // 100

    if cap_points is not None:
        points = min(points, cap_points)

    return max(0, points)


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    """Process a reward event (captured purchase or processed refund) idempotently."""
    out = deepcopy(account) if isinstance(account, dict) else {}
    out.setdefault("points_balance", 0)
    out.setdefault("processed_event_ids", [])
    out.setdefault("transactions", {})
    out.setdefault("ledger", [])

    if not isinstance(event, dict):
        return out

    event_id = event.get("event_id")
    if not event_id or not isinstance(event_id, str):
        return out

    if event_id in out["processed_event_ids"]:
        return out

    kind = event.get("type")
    txn_id = event.get("transaction_id")
    if not txn_id or not isinstance(txn_id, str):
        return out

    if not isinstance(rules, dict):
        rules = {}

    if kind == "purchase_captured":
        amount = event.get("amount_paise")
        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
            return out

        if txn_id not in out["transactions"]:
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
            out["ledger"].append({
                "event_id": event_id,
                "type": kind,
                "points_delta": points,
            })
            out["processed_event_ids"].append(event_id)

    elif kind == "refund_processed":
        if txn_id not in out["transactions"]:
            return out

        txn = out["transactions"][txn_id]
        refund = event.get("amount_paise")

        if isinstance(refund, bool) or not isinstance(refund, int) or refund <= 0:
            return out

        if txn["refunded_paise"] + refund > txn["amount_paise"]:
            return out

        txn["refunded_paise"] += refund

        original_amount = txn["amount_paise"]
        if original_amount > 0:
            should_reverse = (txn["awarded_points"] * txn["refunded_paise"]) // original_amount
        else:
            should_reverse = 0

        should_reverse = min(should_reverse, txn["awarded_points"])
        should_reverse = max(should_reverse, txn["reversed_points"])

        delta = should_reverse - txn["reversed_points"]
        delta = min(delta, out["points_balance"])
        delta = max(0, delta)

        out["points_balance"] -= delta
        txn["reversed_points"] += delta

        out["ledger"].append({
            "event_id": event_id,
            "type": kind,
            "points_delta": -delta,
        })
        out["processed_event_ids"].append(event_id)

    return out


def flag_repeat_transactions(transactions: list[dict], threshold: int = 2) -> list[dict]:
    """Flag possible repeat transactions by account, date, and amount when count > threshold."""
    if not isinstance(transactions, list):
        return []

    if isinstance(threshold, bool) or not isinstance(threshold, int):
        threshold = 2

    groups: dict[tuple, list[str]] = {}
    for tx in transactions:
        if not isinstance(tx, dict):
            continue
        key = (tx.get("account_id"), tx.get("date"), tx.get("amount_paise"))
        groups.setdefault(key, []).append(tx.get("transaction_id"))

    alerts = []
    for k, ids in sorted(groups.items(), key=lambda item: str(item[0])):
        if len(ids) > threshold:
            alerts.append({
                "account_id": k[0],
                "date": k[1],
                "amount_paise": k[2],
                "transaction_ids": ids,
            })
    return alerts


def generate_account_statement_csv(account: dict) -> str:
    """Generate a CSV account statement from the account audit ledger.

    Returns a CSV string with columns: event_id,type,points_delta
    """
    lines = ["event_id,type,points_delta"]
    if isinstance(account, dict):
        for entry in account.get("ledger", []):
            if isinstance(entry, dict):
                eid = entry.get("event_id", "")
                etype = entry.get("type", "")
                delta = entry.get("points_delta", 0)
                lines.append(f"{eid},{etype},{delta}")
    return "\n".join(lines)
