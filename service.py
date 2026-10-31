from copy import deepcopy


def calculate_points(amount_paise: int, points_per_100_rupees: int, bonus_percent: int=0, cap_points: int|None=None) -> int:
    # 1. Check that amounts and rules are valid integers and not negative
    if type(amount_paise) is not int or amount_paise <= 0:
        return 0
    if type(points_per_100_rupees) is not int or points_per_100_rupees <= 0:
        return 0
    if type(bonus_percent) is not int or bonus_percent < 0:
        return 0
    if cap_points is not None:
        if type(cap_points) is not int or cap_points <= 0:
            return 0

    # 2. Use integer floor division (//) instead of round()
    base = (amount_paise // 10000) * points_per_100_rupees
    points = (base * (100 + bonus_percent)) // 100

    # 3. Apply cap_points last if provided
    if cap_points is not None:
        points = min(points, cap_points)
    return max(0, points)


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    out = deepcopy(account)
    out.setdefault('points_balance', 0)
    out.setdefault('processed_event_ids', [])
    out.setdefault('ledger', [])
    out.setdefault('transactions', {})

    if not isinstance(event, dict) or not isinstance(rules, dict):
        return out

    event_id = event.get('event_id')
    kind = event.get('type')
    txn_id = event.get('transaction_id')

    # Ignore missing identifiers or duplicate event_id replays
    if not event_id or not txn_id:
        return out
    if event_id in out['processed_event_ids']:
        return out

    if kind == 'purchase_captured':
        amount = event.get('amount_paise', 0)
        if type(amount) is not int or amount <= 0:
            return out
        if txn_id not in out['transactions']:
            points = calculate_points(
                amount,
                rules.get('points_per_100_rupees', 1),
                rules.get('bonus_percent', 0),
                rules.get('cap_points')
            )
            out['transactions'][txn_id] = {
                'amount_paise': amount,
                'awarded_points': points,
                'reversed_points': 0,
                'refunded_paise': 0
            }
            out['points_balance'] += points
            out['ledger'].append({'event_id': event_id, 'type': kind, 'points_delta': points})
            out['processed_event_ids'].append(event_id)

    elif kind == 'refund_processed' and txn_id in out['transactions']:
        txn = out['transactions'][txn_id]
        refund = event.get('amount_paise', 0)

        # Refund must be a positive integer and total refunded cannot exceed purchase amount
        if type(refund) is not int or refund <= 0:
            return out
        if txn['refunded_paise'] + refund > txn['amount_paise']:
            return out

        txn['refunded_paise'] += refund
        should_reverse = (txn['awarded_points'] * txn['refunded_paise']) // max(1, txn['amount_paise'])
        delta = should_reverse - txn['reversed_points']
        delta = max(0, min(delta, out['points_balance']))

        out['points_balance'] -= delta
        txn['reversed_points'] += delta
        out['ledger'].append({'event_id': event_id, 'type': kind, 'points_delta': -delta})
        out['processed_event_ids'].append(event_id)

    return out


def flag_repeat_transactions(transactions: list[dict], threshold: int=2) -> list[dict]:
    if not isinstance(transactions, list) or type(threshold) is not int or threshold < 1:
        return []

    groups = {}
    for tx in transactions:
        if not isinstance(tx, dict):
            continue
        account_id = tx.get('account_id')
        date = tx.get('date')
        amount = tx.get('amount_paise')
        tx_id = tx.get('transaction_id')

        # Skip rows with missing identifiers or invalid amounts
        if not account_id or not date or not tx_id:
            continue
        if type(amount) is not int or amount <= 0:
            continue

        key = (account_id, date, amount)
        groups.setdefault(key, []).append(tx_id)

    return [
        {'account_id': k[0], 'date': k[1], 'amount_paise': k[2], 'transaction_ids': ids}
        for k, ids in sorted(groups.items(), key=lambda item: str(item[0]))
        if len(ids) > threshold
    ]