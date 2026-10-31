from copy import deepcopy


def calculate_points(
    amount_paise: int,
    points_per_100_rupees: int,
    bonus_percent: int = 0,
    cap_points: int | None = None,
) -> int:
    values = (amount_paise, points_per_100_rupees, bonus_percent)
    if any(type(value) is not int or value < 0 for value in values):
        return 0
    if cap_points is not None and (type(cap_points) is not int or cap_points < 0):
        return 0

    base_points = (amount_paise // 10000) * points_per_100_rupees
    points = base_points * (100 + bonus_percent) // 100
    if cap_points is not None:
        points = min(points, cap_points)
    return points


def _valid_identifier(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    out = deepcopy(account)
    out.setdefault("points_balance", 0)
    out.setdefault("processed_event_ids", [])
    out.setdefault("transactions", {})
    out.setdefault("ledger", [])

    event_id = event.get("event_id")
    if not _valid_identifier(event_id):
        return out

    if event_id in out["processed_event_ids"]:
        return out
    out["processed_event_ids"].append(event_id)

    kind = event.get("type")
    txn_id = event.get("transaction_id")
    if not _valid_identifier(txn_id):
        return out

    if kind == "purchase_captured":
        amount = event.get("amount_paise")
        if type(amount) is not int or amount < 0 or txn_id in out["transactions"]:
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
        out["ledger"].append(
            {"event_id": event_id, "type": kind, "points_delta": points}
        )
    elif kind == "refund_processed" and txn_id in out["transactions"]:
        txn = out["transactions"][txn_id]
        refund = event.get("amount_paise")
        amount = txn.get("amount_paise")
        awarded_points = txn.get("awarded_points")
        refunded_paise = txn.get("refunded_paise")
        reversed_points = txn.get("reversed_points")
        if (
            type(refund) is not int
            or refund <= 0
            or type(amount) is not int
            or amount <= 0
            or type(awarded_points) is not int
            or type(refunded_paise) is not int
            or type(reversed_points) is not int
            or refunded_paise + refund > amount
        ):
            return out

        txn["refunded_paise"] = refunded_paise + refund
        should_reverse = min(
            awarded_points,
            awarded_points * txn["refunded_paise"] // amount,
        )
        points_to_reverse = max(0, should_reverse - reversed_points)
        balance_before = max(0, out["points_balance"])
        balance_after = max(0, balance_before - points_to_reverse)
        applied_reversal = balance_before - balance_after
        out["points_balance"] = balance_after
        txn["reversed_points"] = should_reverse
        out["ledger"].append(
            {
                "event_id": event_id,
                "type": kind,
                "points_delta": -applied_reversal,
            }
        )

    return out


def flag_repeat_transactions(
    transactions: list[dict], threshold: int = 2
) -> list[dict]:
    if type(threshold) is not int:
        threshold = 2

    groups = {}
    for tx in transactions:
        if not isinstance(tx, dict):
            continue
        account_id = tx.get("account_id")
        date = tx.get("date")
        amount_paise = tx.get("amount_paise")
        transaction_id = tx.get("transaction_id")
        if (
            not _valid_identifier(account_id)
            or not _valid_identifier(date)
            or not _valid_identifier(transaction_id)
            or type(amount_paise) is not int
            or amount_paise < 0
        ):
            continue

        key = (account_id, date, amount_paise)
        groups.setdefault(key, []).append(transaction_id)

    return [
        {
            "account_id": key[0],
            "date": key[1],
            "amount_paise": key[2],
            "transaction_ids": transaction_ids,
        }
        for key, transaction_ids in sorted(
            groups.items(), key=lambda item: str(item[0])
        )
        if len(transaction_ids) > threshold
    ]
