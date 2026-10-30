from copy import deepcopy


def calculate_points(amount_paise: int, points_per_100_rupees: int, bonus_percent: int=0, cap_points: int|None=None) -> int:
    """Calculate points using integer arithmetic:
    base_points = floor(amount_paise / 10000) * points_per_100_rupees
    bonus_points = floor(base_points * (100 + bonus_percent) / 100)
    apply optional cap_points last.
    Invalid or negative amounts/rules must not generate points. A cap of zero means zero points.
    """
    if isinstance(amount_paise, bool) or not isinstance(amount_paise, int) or amount_paise <= 0:
        return 0
    if isinstance(points_per_100_rupees, bool) or not isinstance(points_per_100_rupees, int) or points_per_100_rupees <= 0:
        return 0
    if isinstance(bonus_percent, bool) or not isinstance(bonus_percent, int) or bonus_percent < 0:
        return 0
    if cap_points is not None:
        if isinstance(cap_points, bool) or not isinstance(cap_points, int) or cap_points < 0:
            return 0

    base = (amount_paise // 10000) * points_per_100_rupees
    points = base * (100 + bonus_percent) // 100
    if cap_points is not None:
        points = min(points, cap_points)
    return max(0, points)


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    """Apply a reward event to an account with idempotency, validation and ledger tracking."""
    out = deepcopy(account) if isinstance(account, dict) else {}
    out.setdefault('points_balance', 0)
    out.setdefault('processed_event_ids', [])
    out.setdefault('transactions', {})
    out.setdefault('ledger', [])

    if not isinstance(event, dict):
        return out
    if not isinstance(rules, dict):
        rules = {}

    event_id = event.get('event_id')
    kind = event.get('type')
    txn_id = event.get('transaction_id')

    if not event_id or not isinstance(event_id, str):
        return out
    if event_id in out['processed_event_ids']:
        return out
    if not txn_id or not isinstance(txn_id, str):
        return out

    if kind == 'purchase_captured':
        amount = event.get('amount_paise')
        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
            return out
        if txn_id in out['transactions']:
            return out

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
        out['ledger'].append({
            'event_id': event_id,
            'type': kind,
            'points_delta': points
        })
        out['processed_event_ids'].append(event_id)

    elif kind == 'refund_processed':
        if txn_id not in out['transactions']:
            return out
        txn = out['transactions'][txn_id]
        refund = event.get('amount_paise')

        if isinstance(refund, bool) or not isinstance(refund, int) or refund <= 0:
            return out
        if txn['refunded_paise'] + refund > txn['amount_paise']:
            return out

        new_refunded = txn['refunded_paise'] + refund
        if txn['amount_paise'] > 0:
            should_reverse = (txn['awarded_points'] * new_refunded) // txn['amount_paise']
        else:
            should_reverse = 0

        should_reverse = min(should_reverse, txn['awarded_points'])
        delta = max(0, should_reverse - txn['reversed_points'])
        delta = min(delta, max(0, out['points_balance']))

        txn['refunded_paise'] = new_refunded
        txn['reversed_points'] += delta
        out['points_balance'] = max(0, out['points_balance'] - delta)
        out['ledger'].append({
            'event_id': event_id,
            'type': kind,
            'points_delta': -delta
        })
        out['processed_event_ids'].append(event_id)

    return out


def flag_repeat_transactions(transactions: list[dict], threshold: int=2) -> list[dict]:
    """Flag possible repeats by account, date and amount using the supplied threshold."""
    if not isinstance(transactions, list):
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
            'transaction_ids': ids
        }
        for k, ids in sorted(groups.items(), key=lambda item: str(item[0]))
        if len(ids) > threshold
    ]


def generate_account_statement_csv(account: dict) -> str:
    """Generate a CSV account statement from ledger entries. (Optional stretch feature)"""
    lines = ['event_id,type,points_delta,balance']
    running_balance = 0
    if isinstance(account, dict):
        for entry in account.get('ledger', []):
            if isinstance(entry, dict):
                delta = entry.get('points_delta', 0)
                running_balance += delta
                lines.append(f"{entry.get('event_id','')},{entry.get('type','')},{delta},{running_balance}")
    return '\n'.join(lines)

