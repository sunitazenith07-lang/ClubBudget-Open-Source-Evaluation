from copy import deepcopy


def calculate_points(amount_paise: int, points_per_100_rupees: int, bonus_percent: int = 0, cap_points: int | None = None) -> int:
    # Validate input types and boundary conditions
    if type(amount_paise) is not int or amount_paise <= 0:
        return 0
    if type(points_per_100_rupees) is not int or points_per_100_rupees <= 0:
        return 0

    # Calculate base points using integer floor division (1 point per 100 rupees = 10,000 paise)
    base = (amount_paise // 10000) * points_per_100_rupees

    # Apply bonus percentage if valid
    bonus = 0
    if type(bonus_percent) in (int, float) and bonus_percent > 0:
        bonus = int(bonus_percent)

    points = base * (100 + bonus) // 100

    # Apply cap if provided (cap_points=0 means 0 points)
    if cap_points is not None:
        if type(cap_points) is not int or cap_points <= 0:
            return 0
        points = min(points, cap_points)

    return max(0, points)


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    out = deepcopy(account)
    out.setdefault('points_balance', 0)
    out.setdefault('processed_event_ids', [])
    out.setdefault('transactions', {})
    out.setdefault('ledger', [])

    if not isinstance(event, dict):
        return out

    event_id = event.get('event_id')
    # Process each event only once (idempotent)
    if not event_id or event_id in out['processed_event_ids']:
        return out

    kind = event.get('type')
    txn_id = event.get('transaction_id')
    if not txn_id:
        return out

    if kind == 'purchase_captured':
        amount = event.get('amount_paise', 0)
        if type(amount) is not int or amount < 0:
            return out

        points = calculate_points(
            amount,
            rules.get('points_per_100_rupees', 1),
            rules.get('bonus_percent', 0),
            rules.get('cap_points'),
        )

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

    elif kind == 'refund_processed' and txn_id in out['transactions']:
        txn = out['transactions'][txn_id]
        refund = event.get('amount_paise')

        # Reject invalid, non-integer, negative, or excess refund amounts
        if type(refund) is not int or refund <= 0:
            return out
        if txn['refunded_paise'] + refund > txn['amount_paise']:
            return out

        txn['refunded_paise'] += refund
        # Proportional reversal calculation based on cumulative refund
        should_reverse = txn['awarded_points'] * txn['refunded_paise'] // max(1, txn['amount_paise'])
        should_reverse = min(txn['awarded_points'], max(0, should_reverse))

        delta = should_reverse - txn['reversed_points']
        # Prevent points balance from going below zero
        delta = max(0, min(delta, out['points_balance']))

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
    if not isinstance(transactions, list):
        return []

    groups = {}
    for tx in transactions:
        if not isinstance(tx, dict):
            continue
        key = (tx.get('account_id'), tx.get('date'), tx.get('amount_paise'))
        groups.setdefault(key, []).append(tx.get('transaction_id'))

    result = []
    for (acc, dt, amt), ids in sorted(groups.items(), key=lambda item: str(item[0])):
        if len(ids) > threshold:
            result.append({
                'account_id': acc,
                'date': dt,
                'amount_paise': amt,
                'transaction_ids': ids,
            })
    return result
