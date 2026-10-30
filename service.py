from copy import deepcopy


def _is_strict_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def calculate_points(
    amount_paise: int,
    points_per_100_rupees: int,
    bonus_percent: int = 0,
    cap_points: int | None = None,
) -> int:
    if not _is_strict_int(amount_paise) or amount_paise <= 0:
        return 0
    if not _is_strict_int(points_per_100_rupees) or points_per_100_rupees <= 0:
        return 0
    if not _is_strict_int(bonus_percent) or bonus_percent < 0:
        return 0
    if cap_points is not None:
        if not _is_strict_int(cap_points) or cap_points <= 0:
            return 0

    base = (amount_paise // 10000) * points_per_100_rupees
    points = (base * (100 + bonus_percent)) // 100
    if cap_points is not None:
        points = min(points, cap_points)
    return max(0, points)


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    out = deepcopy(account) if isinstance(account, dict) else {}
    out.setdefault('points_balance', 0)
    out.setdefault('processed_event_ids', [])
    out.setdefault('transactions', {})
    out.setdefault('ledger', [])

    if not isinstance(event, dict) or not isinstance(rules, dict):
        return out

    event_id = event.get('event_id')
    kind = event.get('type')
    txn_id = event.get('transaction_id')

    if not isinstance(event_id, str) or not event_id:
        return out
    if not isinstance(txn_id, str) or not txn_id:
        return out
    if event_id in out['processed_event_ids']:
        return out

    if kind == 'purchase_captured':
        amount = event.get('amount_paise')
        if not _is_strict_int(amount) or amount <= 0:
            return out
        if txn_id in out['transactions']:
            return out
        points = calculate_points(
            amount,
            rules.get('points_per_100_rupees', 1),
            rules.get('bonus_percent', 0),
            rules.get('cap_points'),
        )
        out['transactions'][txn_id] = {
            'amount_paise': amount,
            'awarded_points': points,
            'reversed_points': 0,
            'refunded_paise': 0,
        }
        out['points_balance'] += points
        out['ledger'].append({'event_id': event_id, 'type': kind, 'points_delta': points})
        out['processed_event_ids'].append(event_id)
    elif kind == 'refund_processed':
        if txn_id not in out['transactions']:
            return out
        txn = out['transactions'][txn_id]
        refund = event.get('amount_paise')
        if not _is_strict_int(refund) or refund <= 0:
            return out
        if txn['refunded_paise'] + refund > txn['amount_paise']:
            return out
        txn['refunded_paise'] += refund
        should_reverse = min(
            txn['awarded_points'],
            (txn['awarded_points'] * txn['refunded_paise']) // max(1, txn['amount_paise']),
        )
        delta = max(0, should_reverse - txn['reversed_points'])
        delta = min(delta, out['points_balance'])
        out['points_balance'] -= delta
        txn['reversed_points'] += delta
        out['ledger'].append({'event_id': event_id, 'type': kind, 'points_delta': -delta})
        out['processed_event_ids'].append(event_id)

    return out


def flag_repeat_transactions(transactions: list[dict], threshold: int = 2) -> list[dict]:
    if not isinstance(transactions, list):
        return []
    if not _is_strict_int(threshold) or threshold < 1:
        return []
    groups: dict[tuple[str, str, int], list[str]] = {}
    for tx in transactions:
        if not isinstance(tx, dict):
            continue
        tx_id = tx.get('transaction_id')
        account_id = tx.get('account_id')
        date = tx.get('date')
        amount = tx.get('amount_paise')
        if not isinstance(tx_id, str) or not tx_id:
            continue
        if not isinstance(account_id, str) or not account_id:
            continue
        if not isinstance(date, str) or not date:
            continue
        if not _is_strict_int(amount) or amount < 0:
            continue
        status = tx.get('status')
        if status is not None and status != 'CAPTURED':
            continue
        key = (account_id, date, amount)
        ids = groups.setdefault(key, [])
        if tx_id not in ids:
            ids.append(tx_id)
    return [
        {
            'account_id': k[0],
            'date': k[1],
            'amount_paise': k[2],
            'transaction_ids': ids,
        }
        for k, ids in sorted(groups.items(), key=lambda item: item[0])
        if len(ids) > threshold
    ]

