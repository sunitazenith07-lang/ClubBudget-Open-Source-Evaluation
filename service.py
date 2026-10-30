from copy import deepcopy


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def calculate_points(amount_paise, points_per_100_rupees, bonus_percent=0, cap_points=None) -> int:
    if not _is_int(amount_paise) or not _is_int(points_per_100_rupees):
        return 0
    if bonus_percent is None or not _is_int(bonus_percent):
        return 0
    if cap_points is not None and not _is_int(cap_points):
        return 0

    if amount_paise <= 0:
        return 0
    if points_per_100_rupees <= 0:
        return 0

    base = (amount_paise // 10000) * points_per_100_rupees
    points = base * (100 + bonus_percent) // 100

    if cap_points is not None:
        points = min(points, cap_points)

    return max(0, points)


def apply_reward_event(account, event, rules):
    out = deepcopy(account)
    out.setdefault('points_balance', 0)
    out.setdefault('processed_event_ids', [])
    out.setdefault('transactions', {})
    out.setdefault('ledger', [])

    if not isinstance(event, dict):
        return out
    if not isinstance(rules, dict):
        rules = {}

    event_id = event.get('event_id')
    if event_id in out['processed_event_ids']:
        return out

    kind = event.get('type')
    txn_id = event.get('transaction_id')

    if kind == 'purchase_captured':
        amount = event.get('amount_paise',0)
        points=calculate_points(
            amount,
            rules.get('points_per_100_rupees',1),
            rules.get('bonus_percent',0),
            rules.get('cap_points')
        )
        if txn_id and txn_id not in out['transactions']:
            out['transactions'][txn_id]={
                'amount_paise':amount,
                'awarded_points':points,
                'reversed_points':0,
                'refunded_paise':0
            }
            out['points_balance'] += points
            out['ledger'].append({
                'event_id':event_id,
                'type':kind,
                'points_delta':points
            })
    elif kind == 'refund_processed' and txn_id in out['transactions']:
        txn = out['transactions'][txn_id]
        refund = event.get('amount_paise', 0)

        is_valid_refund = (
            _is_int(refund)
            and refund > 0
            and _is_int(txn.get('amount_paise'))
            and txn['refunded_paise'] + refund <= txn['amount_paise']
        )

        if is_valid_refund:
            txn['refunded_paise'] += refund
            should_reverse = txn['awarded_points'] * txn['refunded_paise'] // max(1, txn['amount_paise'])
            delta = should_reverse - txn['reversed_points']

            out['points_balance'] -= delta
            if out['points_balance'] < 0:
                out['points_balance'] = 0
            txn['reversed_points'] = should_reverse

            out['ledger'].append({
                'event_id': event_id,
                'type': kind,
                'points_delta': -delta,
            })
    if event_id:
        out['processed_event_ids'].append(event_id)

    return out


def flag_repeat_transactions(transactions, threshold=2):
    if not isinstance(transactions, list):
        return []

    if isinstance(threshold, bool) or not isinstance(threshold, int):
        try:
            threshold = int(threshold)
        except (TypeError, ValueError):
            threshold = 0
    if threshold < 0:
        threshold = 0

    groups = {}
    for tx in transactions:
        if not isinstance(tx, dict):
            continue
        key = (tx.get('account_id'), tx.get('date'), tx.get('amount_paise'))
        groups.setdefault(key, []).append(tx.get('transaction_id'))

    sorted_groups = sorted(
        groups.items(),
        key=lambda item: tuple(str(v) if v is not None else '' for v in item[0])
    )

    return [
        {
            'account_id': k[0],
            'date': k[1],
            'amount_paise': k[2],
            'transaction_ids': ids,
        }
        for k, ids in sorted_groups
        if len(ids) > threshold
    ]
