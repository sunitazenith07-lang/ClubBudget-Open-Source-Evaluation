from copy import deepcopy


def _is_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def calculate_points(
    amount_paise: int,
    points_per_100_rupees: int,
    bonus_percent: int = 0,
    cap_points: int | None = None,
) -> int:
    if (
        not _is_integer(amount_paise)
        or amount_paise < 0
        or not _is_integer(points_per_100_rupees)
        or points_per_100_rupees < 0
        or not _is_integer(bonus_percent)
        or bonus_percent < 0
        or (
            cap_points is not None
            and (not _is_integer(cap_points) or cap_points < 0)
        )
    ):
        return 0

    base_points = (amount_paise // 10000) * points_per_100_rupees
    points = (base_points * (100 + bonus_percent)) // 100
    if cap_points is not None:
        points = min(points, cap_points)
    return points


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    out = deepcopy(account)
    out.setdefault("points_balance", 0)
    out.setdefault("processed_event_ids", [])
    out.setdefault("transactions", {})
    out.setdefault("ledger", [])

    event_id = event.get("event_id")
    kind = event.get("type")
    transaction_id = event.get("transaction_id")
    if (
        event_id is None
        or event_id == ""
        or event_id in out["processed_event_ids"]
        or transaction_id is None
        or transaction_id == ""
    ):
        return out

    if kind == "purchase_captured":
        amount = event.get("amount_paise", 0)
        if not _is_integer(amount) or amount < 0:
            return out

        if transaction_id not in out["transactions"]:
            points = calculate_points(
                amount,
                rules.get("points_per_100_rupees", 1),
                rules.get("bonus_percent", 0),
                rules.get("cap_points"),
            )
            out["transactions"][transaction_id] = {
                "amount_paise": amount,
                "awarded_points": points,
                "reversed_points": 0,
                "refunded_paise": 0,
            }
            out["points_balance"] += points
            out["ledger"].append(
                {"event_id": event_id, "type": kind, "points_delta": points}
            )
        out["processed_event_ids"].append(event_id)
    elif kind == "refund_processed" and transaction_id in out["transactions"]:
        txn = out["transactions"][transaction_id]
        refund = event.get("amount_paise")
        purchase_amount = txn.get("amount_paise")
        refunded_paise = txn.get("refunded_paise", 0)
        awarded_points = txn.get("awarded_points")
        reversed_points = txn.get("reversed_points", 0)
        if (
            not _is_integer(refund)
            or refund <= 0
            or not _is_integer(purchase_amount)
            or purchase_amount <= 0
            or not _is_integer(refunded_paise)
            or refunded_paise < 0
            or refunded_paise + refund > purchase_amount
            or not _is_integer(awarded_points)
            or awarded_points < 0
            or not _is_integer(reversed_points)
            or reversed_points < 0
        ):
            return out

        txn["refunded_paise"] = refunded_paise + refund
        should_reverse = min(
            awarded_points,
            awarded_points * txn["refunded_paise"] // purchase_amount,
        )
        delta = max(0, should_reverse - reversed_points)
        delta = min(delta, max(0, out["points_balance"]))
        out["points_balance"] -= delta
        txn["reversed_points"] = reversed_points + delta
        out["ledger"].append(
            {"event_id": event_id, "type": kind, "points_delta": -delta}
        )
        out["processed_event_ids"].append(event_id)

    return out


def flag_repeat_transactions(
    transactions: list[dict], threshold: int = 2
) -> list[dict]:
    groups = {}
    for transaction in transactions:
        key = (
            transaction.get("account_id"),
            transaction.get("date"),
            transaction.get("amount_paise"),
        )
        groups.setdefault(key, []).append(transaction.get("transaction_id"))
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