from copy import deepcopy


def calculate_points(amount_paise: int, points_per_100_rupees: int, bonus_percent: int = 0, cap_points: int | None = None) -> int:
    if amount_paise is None or not isinstance(amount_paise, int) or isinstance(amount_paise, bool) or amount_paise < 0:
        return 0
    if not isinstance(points_per_100_rupees, int) or isinstance(points_per_100_rupees, bool) or points_per_100_rupees < 0:
        return 0
    if not isinstance(bonus_percent, int) or isinstance(bonus_percent, bool):
        bonus_percent = 0
    if bonus_percent < 0:
        bonus_percent = 0
    if cap_points is not None and (not isinstance(cap_points, int) or isinstance(cap_points, bool) or cap_points < 0):
        cap_points = None

    base = (amount_paise // 10000) * points_per_100_rupees
    points = (base * (100 + bonus_percent)) // 100

    if cap_points is not None:
        points = min(points, cap_points)

    return max(0, points)


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    out = deepcopy(account)
    out.setdefault('points_balance', 0)
    out.setdefault('processed_event_ids', [])
    out.setdefault('transactions', {})
    out.setdefault('ledger', [])

    event_id = event.get('event_id')
    kind = event.get('type')
    txn_id = event.get('transaction_id')

    if event_id in out['processed_event_ids']:
        return out

    if kind == 'purchase_captured':
        amount = event.get('amount_paise', 0)
        if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
            amount = 0

        points = calculate_points(
            amount,
            rules.get('points_per_100_rupees', 1),
            rules.get('bonus_percent', 0),
            rules.get('cap_points')
        )

        if txn_id not in out['transactions']:
            out['transactions'][txn_id] = {
                'amount_paise': amount,
                'awarded_points': points,
                'reversed_points': 0,
                'refunded_paise': 0
            }
            out['points_balance'] += points
            out['ledger'].append({
                'event_id': event_id,
                'type': kind,
                'points_delta': points
            })

    elif kind == 'refund_processed' and txn_id in out['transactions']:
        txn = out['transactions'][txn_id]
        refund = event.get('amount_paise', 0)

        if not isinstance(refund, int) or isinstance(refund, bool) or refund < 0:
            refund = 0

        max_allowable_refund = txn['amount_paise'] - txn['refunded_paise']
        if refund <= 0 or refund > max_allowable_refund:
            refund = 0

        if refund > 0:
            txn['refunded_paise'] += refund
            should_reverse = (txn['awarded_points'] * txn['refunded_paise']) // max(1, txn['amount_paise'])
            delta = should_reverse - txn['reversed_points']

            out['points_balance'] = max(0, out['points_balance'] - delta)
            txn['reversed_points'] = should_reverse

            out['ledger'].append({
                'event_id': event_id,
                'type': kind,
                'points_delta': -delta
            })

    if event_id:
        out['processed_event_ids'].append(event_id)

    return out


def flag_repeat_transactions(transactions: list[dict], threshold: int = 2) -> list[dict]:
    if not isinstance(transactions, list):
        return []

    try:
        threshold_value = int(threshold)
    except (TypeError, ValueError):
        return []

    if threshold_value < 0:
        threshold_value = 0

    groups: dict[tuple, list] = {}
    for tx in transactions:
        if not isinstance(tx, dict):
            continue

        account_id = tx.get('account_id')
        date = tx.get('date')
        amount = tx.get('amount_paise')

        if account_id is None or date is None:
            continue
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            continue

        key = (account_id, date, amount)
        groups.setdefault(key, []).append(tx.get('transaction_id'))

    return [
        {
            'account_id': key[0],
            'date': key[1],
            'amount_paise': key[2],
            'transaction_ids': ids,
        }
        for key, ids in sorted(groups.items(), key=lambda item: str(item[0]))
        if len(ids) > threshold_value
    ]