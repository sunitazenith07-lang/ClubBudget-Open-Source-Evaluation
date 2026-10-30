from copy import deepcopy


def calculate_points(
    amount_paise: int,
    points_per_100_rupees: int,
    bonus_percent: int = 0,
    cap_points: int | None = None,
) -> int:
    """Calculate points using integer arithmetic with floor division, bonus, and optional cap.

    Rules:
    - base_points = floor(amount_paise / 10000) * points_per_100_rupees
    - bonus_points = floor(base_points * (100 + bonus_percent) / 100)
    - apply optional cap_points last (cap_points of 0 means 0 points)
    - invalid or negative amounts/rules generate 0 points.
    """
    # Type validation: ensure inputs are integers and not booleans
    if not isinstance(amount_paise, int) or isinstance(amount_paise, bool):
        return 0
    if not isinstance(points_per_100_rupees, int) or isinstance(points_per_100_rupees, bool):
        return 0
    if not isinstance(bonus_percent, int) or isinstance(bonus_percent, bool):
        return 0

    # Boundary and negativity checks
    if amount_paise <= 0 or points_per_100_rupees <= 0 or bonus_percent < 0:
        return 0

    if cap_points is not None:
        if not isinstance(cap_points, int) or isinstance(cap_points, bool) or cap_points < 0:
            return 0

    base_points = (amount_paise // 10000) * points_per_100_rupees
    bonus_points = (base_points * (100 + bonus_percent)) // 100

    if cap_points is not None:
        bonus_points = min(bonus_points, cap_points)

    return max(0, bonus_points)


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    """Apply a reward event (captured purchase or refund) to an account idempotently and immutably."""
    out = deepcopy(account) if account else {}
    out.setdefault("account_id", account.get("account_id", "") if isinstance(account, dict) else "")
    out.setdefault("points_balance", 0)
    out.setdefault("processed_event_ids", [])
    out.setdefault("transactions", {})
    out.setdefault("ledger", [])

    if not isinstance(event, dict):
        return out

    event_id = event.get("event_id")
    if not event_id or not isinstance(event_id, str):
        return out

    # Idempotency check: process each event_id once
    if event_id in out["processed_event_ids"]:
        return out

    kind = event.get("type")
    txn_id = event.get("transaction_id")

    if not txn_id or not isinstance(txn_id, str):
        return out

    if kind == "purchase_captured":
        amount = event.get("amount_paise")
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            return out

        rules_dict = rules if isinstance(rules, dict) else {}
        points_per_100_rupees = rules_dict.get("points_per_100_rupees", 1)
        bonus_percent = rules_dict.get("bonus_percent", 0)
        cap_points = rules_dict.get("cap_points")

        points = calculate_points(amount, points_per_100_rupees, bonus_percent, cap_points)

        if txn_id not in out["transactions"]:
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

    elif kind == "refund_processed" and txn_id in out["transactions"]:
        txn = out["transactions"][txn_id]
        refund = event.get("amount_paise")

        # Validate refund: must be positive int and not exceed purchase amount
        if not isinstance(refund, int) or isinstance(refund, bool) or refund <= 0:
            return out

        if txn["refunded_paise"] + refund > txn["amount_paise"]:
            return out

        new_refunded = txn["refunded_paise"] + refund
        # Proportional integer reversal
        if txn["amount_paise"] > 0:
            should_reverse = (txn["awarded_points"] * new_refunded) // txn["amount_paise"]
        else:
            should_reverse = 0

        delta = should_reverse - txn["reversed_points"]
        delta = max(0, delta)
        # Never allow balance to go negative
        delta = min(delta, out["points_balance"])

        txn["refunded_paise"] = new_refunded
        txn["reversed_points"] += delta
        out["points_balance"] -= delta
        out["ledger"].append({
            "event_id": event_id,
            "type": kind,
            "points_delta": -delta,
        })
        out["processed_event_ids"].append(event_id)

    return out


def flag_repeat_transactions(transactions: list[dict], threshold: int = 2) -> list[dict]:
    """Flag possible repeat transactions by (account_id, date, amount_paise) exceeding the threshold."""
    if not isinstance(transactions, list):
        return []

    if not isinstance(threshold, int) or isinstance(threshold, bool):
        threshold = 2

    groups: dict = {}
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


def generate_account_statement_csv(account: dict) -> str:
    """Generate a CSV account statement from the account ledger (optional stretch goal)."""
    lines = ["event_id,type,points_delta"]
    if isinstance(account, dict):
        for entry in account.get("ledger", []):
            if isinstance(entry, dict):
                lines.append(
                    f"{entry.get('event_id', '')},{entry.get('type', '')},{entry.get('points_delta', 0)}"
                )
    return "\n".join(lines) + "\n"
