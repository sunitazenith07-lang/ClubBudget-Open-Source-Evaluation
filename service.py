from copy import deepcopy


def calculate_points(
    amount_paise: int,
    points_per_100_rupees: int,
    bonus_percent: int = 0,
    cap_points: int | None = None,
) -> int:
    if not isinstance(amount_paise, int) or isinstance(amount_paise, bool) or amount_paise <= 0:
        return 0
    if not isinstance(points_per_100_rupees, int) or isinstance(points_per_100_rupees, bool) or points_per_100_rupees <= 0:
        return 0
    if bonus_percent is None:
        bonus_percent = 0
    elif not isinstance(bonus_percent, int) or isinstance(bonus_percent, bool) or bonus_percent < 0:
        return 0
    if cap_points is not None:
        if not isinstance(cap_points, int) or isinstance(cap_points, bool) or cap_points <= 0:
            return 0

    base_points = (amount_paise // 10000) * points_per_100_rupees
    points = (base_points * (100 + bonus_percent)) // 100
    if cap_points is not None:
        points = min(points, cap_points)
    return max(0, points)


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    if not isinstance(account, dict):
        return {}
    out = deepcopy(account)
    out.setdefault('points_balance', 0)
    out.setdefault('processed_event_ids', [])
    out.setdefault('transactions', {})
    out.setdefault('ledger', [])

    if not isinstance(event, dict):
        return out

    event_id = event.get('event_id')
    kind = event.get('type')
    txn_id = event.get('transaction_id')

    if not event_id or not isinstance(event_id, str):
        return out
    if event_id in out['processed_event_ids']:
        return out

    if not txn_id or not isinstance(txn_id, str):
        return out

    if not isinstance(rules, dict):
        rules = {}

    if kind == 'purchase_captured':
        if txn_id in out['transactions']:
            return out
        amount = event.get('amount_paise', 0)
        if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
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
        out['ledger'].append({
            'event_id': event_id,
            'type': kind,
            'points_delta': points,
        })
        out['processed_event_ids'].append(event_id)

    elif kind == 'refund_processed':
        if txn_id not in out['transactions']:
            return out
        txn = out['transactions'][txn_id]
        refund = event.get('amount_paise', 0)
        if not isinstance(refund, int) or isinstance(refund, bool) or refund <= 0:
            return out
        if txn['refunded_paise'] + refund > txn['amount_paise']:
            return out

        txn['refunded_paise'] += refund
        should_reverse = (txn['awarded_points'] * txn['refunded_paise']) // max(1, txn['amount_paise'])
        should_reverse = min(should_reverse, txn['awarded_points'])
        delta = should_reverse - txn['reversed_points']
        delta = max(0, delta)
        delta = min(delta, out['points_balance'])
        out['points_balance'] -= delta
        txn['reversed_points'] += delta
        out['ledger'].append({
            'event_id': event_id,
            'type': kind,
            'points_delta': -delta,
        })
        out['processed_event_ids'].append(event_id)

    return out


def flag_repeat_transactions(transactions: list[dict], threshold: int = 2) -> list[dict]:
    if not transactions or not isinstance(transactions, list):
        return []
    groups = {}
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
