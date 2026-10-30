from copy import deepcopy

def valid_int(value):
    return type(value) is int and value >= 0


def calculate_points(amount_paise, points_per_100_rupees, bonus_percent=0, cap_points=None):

    if (not valid_int(amount_paise) or not valid_int(bonus_percent) or not valid_int(points_per_100_rupees) or (cap_points is not None and not valid_int(cap_points))) :
        return 0

    points = (amount_paise // 10000) * points_per_100_rupees

    bonus = points * bonus_percent // 100
    points += bonus

    if cap_points is not None and points > cap_points:
        points = cap_points

    return points


def apply_reward_event(account, event, rules):
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
    amount = event.get("amount_paise")

    if (
        not isinstance(event_id, str) or not event_id.strip()
        or not isinstance(txn_id, str) or not txn_id.strip()
        or event_id in out["processed_event_ids"]
        or kind not in ("purchase_captured", "refund_processed")
        or not valid_int(amount)
        or not valid_int(out["points_balance"])
    ):
        return out

    transactions = out["transactions"]
    balance = out["points_balance"]

    if kind == "purchase_captured":
        if txn_id in transactions:
            return out

        points = calculate_points(
            amount,
            rules.get("points_per_100_rupees", 1),
            rules.get("bonus_percent", 0),
            rules.get("cap_points")
        )

        transactions[txn_id] = {
            "amount_paise": amount,
            "awarded_points": points,
            "reversed_points": 0,
            "refunded_paise": 0
        }

        delta = points
        out["points_balance"] = balance + delta

    else:
        txn = transactions.get(txn_id)

        if not isinstance(txn, dict) or amount == 0:
            return out

        original, awarded, reversed_points, refunded = (
            txn.get("amount_paise"),
            txn.get("awarded_points"),
            txn.get("reversed_points"),
            txn.get("refunded_paise")
        )

        if (
            not all(valid_int(v) for v in (
                original, awarded, reversed_points, refunded
            ))
            or original == 0
            or reversed_points > awarded
            or refunded > original
            or amount > original - refunded
        ):
            return out

        total_refunded = refunded + amount
        target = min(awarded, awarded * total_refunded // original)
        delta = min(target - reversed_points, balance)

        txn["refunded_paise"] = total_refunded
        txn["reversed_points"] = reversed_points + delta
        out["points_balance"] = balance - delta
        delta = -delta

    out["ledger"].append({
        "event_id": event_id,
        "type": kind,
        "points_delta": delta
    })

    out["processed_event_ids"].append(event_id)

    return out
def flag_repeat_transactions(transactions: list[dict], threshold: int=2) -> list[dict]:
    groups={}
    for tx in transactions:
        key=(tx.get('account_id'),tx.get('date'),tx.get('amount_paise'));groups.setdefault(key,[]).append(tx.get('transaction_id'))
    return [{'account_id':k[0],'date':k[1],'amount_paise':k[2],'transaction_ids':ids} for k,ids in sorted(groups.items(),key=lambda item:str(item[0])) if len(ids)>threshold]
