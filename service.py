"""RewardBook loyalty rewards service.

Handles points calculation, reward event processing, and repeat-transaction alerts.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any


def calculate_points(
    amount_paise: int,
    points_per_100_rupees: int,
    bonus_percent: int = 0,
    cap_points: int | None = None,
) -> int:
    """Calculate reward points for a purchase amount using integer arithmetic.

    Rules:
    - base_points = floor(amount_paise / 10000) * points_per_100_rupees
    - bonus_points = floor(base_points * (100 + bonus_percent) / 100)
    - optional cap_points applied last: min(points, cap_points)
    - Invalid or negative amounts/rules generate 0 points. A cap of 0 means 0 points.
    """
    # Strict validation of input types and boundaries
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

    # Step 1: Base points using integer floor division per 100 rupees (10,000 paise)
    base_points = (amount_paise // 10000) * points_per_100_rupees

    # Step 2: Bonus points using integer floor arithmetic
    points = (base_points * (100 + bonus_percent)) // 100

    # Step 3: Optional cap applied last
    if cap_points is not None:
        points = min(points, cap_points)

    return max(0, points)


def apply_reward_event(account: dict[str, Any], event: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    """Process a loyalty reward event idempotently and update account balances and ledger.

    Supported event types:
    - 'purchase_captured': Awards points for eligible purchases.
    - 'refund_processed': Reverses points proportionally for full/partial refunds.

    Declined, pending, unrecognized events or duplicate event IDs do not alter balances.
    """
    out = deepcopy(account)
    out.setdefault('points_balance', 0)
    out.setdefault('processed_event_ids', [])
    out.setdefault('transactions', {})
    out.setdefault('ledger', [])

    if not isinstance(event, dict) or not isinstance(rules, dict):
        return out

    event_id = event.get('event_id')
    kind = event.get('type')
    txn_id = event.get('transaction_id')

    # Guard against missing or invalid identifiers
    if not event_id or not isinstance(event_id, str):
        return out
    if not txn_id or not isinstance(txn_id, str):
        return out

    # Idempotency check: each event_id processed at most once
    if event_id in out['processed_event_ids']:
        return out

    if kind == 'purchase_captured':
        amount = event.get('amount_paise')
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            return out

        points_per_100 = rules.get('points_per_100_rupees', 1)
        bonus_pct = rules.get('bonus_percent', 0)
        cap = rules.get('cap_points')

        # Validate reward rules before accepting purchase
        if not isinstance(points_per_100, int) or isinstance(points_per_100, bool) or points_per_100 < 0:
            return out
        if bonus_pct is not None and (not isinstance(bonus_pct, int) or isinstance(bonus_pct, bool) or bonus_pct < 0):
            return out
        if cap is not None and (not isinstance(cap, int) or isinstance(cap, bool) or cap < 0):
            return out

        points = calculate_points(amount, points_per_100, bonus_pct, cap)

        if txn_id not in out['transactions']:
            out['transactions'][txn_id] = {
                'amount_paise': amount,
                'awarded_points': points,
                'reversed_points': 0,
                'refunded_paise': 0,
            }
            out['points_balance'] += points
            out['ledger'].append({
                'event_id': event_id,
                'type': kind,
                'points_delta': points,
            })
            out['processed_event_ids'].append(event_id)
        else:
            # Duplicate purchase capture with existing transaction_id
            out['processed_event_ids'].append(event_id)

    elif kind == 'refund_processed':
        if txn_id not in out['transactions']:
            # Unknown transaction: ignore safely
            return out

        txn = out['transactions'][txn_id]
        refund = event.get('amount_paise')

        # Validate refund amount: must be positive int and not exceed unrefunded portion
        if not isinstance(refund, int) or isinstance(refund, bool) or refund <= 0:
            return out

        already_refunded = txn.get('refunded_paise', 0)
        original_amount = txn.get('amount_paise', 0)

        if already_refunded + refund > original_amount:
            # Excess refund attempt: ignore
            return out

        new_refunded_paise = already_refunded + refund
        awarded_points = txn.get('awarded_points', 0)

        # Proportional reversal calculation using integer arithmetic
        total_should_reverse = (awarded_points * new_refunded_paise) // max(1, original_amount)
        total_should_reverse = min(awarded_points, max(0, total_should_reverse))

        reversed_so_far = txn.get('reversed_points', 0)
        delta = total_should_reverse - reversed_so_far
        if delta < 0:
            delta = 0

        # Ledger integrity: never allow negative points balance
        delta = min(delta, max(0, out['points_balance']))

        txn['refunded_paise'] = new_refunded_paise
        txn['reversed_points'] = total_should_reverse
        out['points_balance'] -= delta

        out['ledger'].append({
            'event_id': event_id,
            'type': kind,
            'points_delta': -delta,
        })
        out['processed_event_ids'].append(event_id)

    return out


def flag_repeat_transactions(transactions: list[dict[str, Any]], threshold: int = 2) -> list[dict[str, Any]]:
    """Flag possible repeat transactions by account, date, and amount.

    Alerts are generated when the number of transactions matching the same key exceeds threshold.
    Alerts are for human review only and are returned in deterministic order.
    """
    if not isinstance(transactions, list):
        return []
    if not isinstance(threshold, int) or isinstance(threshold, bool):
        threshold = 2

    groups: dict[tuple[Any, Any, Any], list[str]] = {}
    for tx in transactions:
        if not isinstance(tx, dict):
            continue
        key = (tx.get('account_id'), tx.get('date'), tx.get('amount_paise'))
        groups.setdefault(key, []).append(tx.get('transaction_id'))

    return [
        {
            'account_id': k[0],
            'date': k[1],
            'amount_paise': k[2],
            'transaction_ids': ids,
        }
        for k, ids in sorted(groups.items(), key=lambda item: str(item[0]))
        if len(ids) > threshold
    ]


def generate_account_statement_csv(account: dict[str, Any]) -> str:
    """Generate a CSV account statement from the account ledger for auditing and export.

    Returns a CSV formatted string with headers: event_id,type,points_delta.
    """
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
