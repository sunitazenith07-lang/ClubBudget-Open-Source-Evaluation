
"""RewardBook service for calculating points and handling reward events."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def calculate_points(
    amount_paise: int,
    points_per_100_rupees: int,
    bonus_percent: int = 0,
    cap_points: int | None = None,
) -> int:
    """Calculate the points earned on a purchase."""

    # Ignore invalid values instead of awarding points by mistake.
    if not isinstance(amount_paise, int) or isinstance(amount_paise, bool) or amount_paise <= 0:
        return 0

    if not isinstance(points_per_100_rupees, int) or isinstance(points_per_100_rupees, bool) or points_per_100_rupees < 0:
        return 0

    if bonus_percent is None:
        bonus_percent = 0
    elif not isinstance(bonus_percent, int) or isinstance(bonus_percent, bool) or bonus_percent < 0:
        return 0

    if cap_points is not None:
        if not isinstance(cap_points, int) or isinstance(cap_points, bool) or cap_points < 0:
            return 0

    # 10,000 paise = 100 rupees. Integer division avoids rounding issues.
    base_points = (amount_paise // 10000) * points_per_100_rupees

    # Add the bonus and round down as required by the reward rules.
    points = (base_points * (100 + bonus_percent)) // 100

    # Apply the cap after calculating the bonus.
    if cap_points is not None:
        points = min(points, cap_points)

    return max(0, points)


def apply_reward_event(
    account: dict[str, Any],
    event: dict[str, Any],
    rules: dict[str, Any],
) -> dict[str, Any]:
    """Apply a purchase or refund event and return the updated account."""

    # Work on a copy so the original account is not changed.
    account = deepcopy(account)
    account.setdefault("points_balance", 0)
    account.setdefault("processed_event_ids", [])
    account.setdefault("transactions", {})
    account.setdefault("ledger", [])

    if not isinstance(event, dict) or not isinstance(rules, dict):
        return account

    event_id = event.get("event_id")
    event_type = event.get("type")
    transaction_id = event.get("transaction_id")

    if not isinstance(event_id, str) or not event_id:
        return account
    if not isinstance(transaction_id, str) or not transaction_id:
        return account

    # An event should never be applied more than once.
    if event_id in account["processed_event_ids"]:
        return account

    if event_type == "purchase_captured":
        amount = event.get("amount_paise")

        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            return account

        points_rate = rules.get("points_per_100_rupees", 1)
        bonus = rules.get("bonus_percent", 0)
        cap = rules.get("cap_points")

        # Check the rules before processing the purchase.
        if not isinstance(points_rate, int) or isinstance(points_rate, bool) or points_rate < 0:
            return account
        if bonus is not None and (
            not isinstance(bonus, int) or isinstance(bonus, bool) or bonus < 0
        ):
            return account
        if cap is not None and (
            not isinstance(cap, int) or isinstance(cap, bool) or cap < 0
        ):
            return account

        points = calculate_points(amount, points_rate, bonus, cap)

        if transaction_id not in account["transactions"]:
            account["transactions"][transaction_id] = {
                "amount_paise": amount,
                "awarded_points": points,
                "reversed_points": 0,
                "refunded_paise": 0,
            }

            account["points_balance"] += points
            account["ledger"].append({
                "event_id": event_id,
                "type": event_type,
                "points_delta": points,
            })

        # Even if this transaction was already recorded, remember this event
        # so that the same event ID cannot be processed again.
        account["processed_event_ids"].append(event_id)

    elif event_type == "refund_processed":
        if transaction_id not in account["transactions"]:
            return account

        transaction = account["transactions"][transaction_id]
        refund_amount = event.get("amount_paise")

        if (
            not isinstance(refund_amount, int)
            or isinstance(refund_amount, bool)
            or refund_amount <= 0
        ):
            return account

        refunded_so_far = transaction.get("refunded_paise", 0)
        original_amount = transaction.get("amount_paise", 0)

        # A refund cannot be larger than the remaining purchase amount.
        if refunded_so_far + refund_amount > original_amount:
            return account

        new_refunded_amount = refunded_so_far + refund_amount
        awarded_points = transaction.get("awarded_points", 0)

        # Calculate the total points that should have been reversed by now.
        # Using the cumulative refund amount avoids losing points to rounding.
        points_to_reverse = (
            awarded_points * new_refunded_amount
        ) // max(1, original_amount)

        points_to_reverse = min(awarded_points, max(0, points_to_reverse))

        already_reversed = transaction.get("reversed_points", 0)
        points_to_deduct = max(0, points_to_reverse - already_reversed)

        # Don't let a refund push the account balance below zero.
        points_to_deduct = min(
            points_to_deduct,
            max(0, account["points_balance"]),
        )

        transaction["refunded_paise"] = new_refunded_amount
        transaction["reversed_points"] = points_to_reverse

        account["points_balance"] -= points_to_deduct
        account["ledger"].append({
            "event_id": event_id,
            "type": event_type,
            "points_delta": -points_to_deduct,
        })
        account["processed_event_ids"].append(event_id)

    return account


def flag_repeat_transactions(
    transactions: list[dict[str, Any]],
    threshold: int = 2,
) -> list[dict[str, Any]]:
    """Find transactions that may need a manual review."""

    if not isinstance(transactions, list):
        return []

    if not isinstance(threshold, int) or isinstance(threshold, bool):
        threshold = 2

    groups: dict[tuple[Any, Any, Any], list[str]] = {}

    for transaction in transactions:
        if not isinstance(transaction, dict):
            continue

        key = (
            transaction.get("account_id"),
            transaction.get("date"),
            transaction.get("amount_paise"),
        )
        groups.setdefault(key, []).append(transaction.get("transaction_id"))

    # Return only groups with more transactions than the given threshold.
    return [
        {
            "account_id": key[0],
            "date": key[1],
            "amount_paise": key[2],
            "transaction_ids": ids,
        }
        for key, ids in sorted(groups.items(), key=lambda item: str(item[0]))
        if len(ids) > threshold
    ]


def generate_account_statement_csv(account: dict[str, Any]) -> str:
    """Export the account ledger as a CSV statement."""

    import csv
    import io

    if not isinstance(account, dict):
        return "event_id,type,points_delta\r\n"

    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\r\n")
    writer.writerow(["event_id", "type", "points_delta"])

    for entry in account.get("ledger", []):
        if isinstance(entry, dict):
            writer.writerow([
                entry.get("event_id", ""),
                entry.get("type", ""),
                entry.get("points_delta", 0),
            ])

    return output.getvalue()
