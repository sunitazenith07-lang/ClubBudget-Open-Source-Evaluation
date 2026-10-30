from copy import deepcopy


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def calculate_points(amount_paise: int, points_per_100_rupees: int, bonus_percent: int = 0, cap_points: int | None = None) -> int:
    if not _is_int(amount_paise) or amount_paise <= 0:
        return 0
    if not _is_int(points_per_100_rupees) or points_per_100_rupees <= 0:
        return 0
    if not _is_int(bonus_percent) or bonus_percent < 0:
        return 0

    points = (amount_paise // 10000) * points_per_100_rupees
    points = (points * (100 + bonus_percent)) // 100
    if cap_points is not None:
        if not _is_int(cap_points) or cap_points < 0:
            return 0
        points = min(points, cap_points)
    return max(0, points)


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    out = deepcopy(account) if isinstance(account, dict) else {}
    out.setdefault('points_balance', 0)
    out.setdefault('processed_event_ids', [])
    out.setdefault('transactions', {})
    out.setdefault('ledger', [])

    if not isinstance(event, dict):
        return out

    event_id = event.get('event_id')
    if not isinstance(event_id, str) or not event_id or event_id in out['processed_event_ids']:
        return out

    txn_id = event.get('transaction_id')
    if not isinstance(txn_id, str) or not txn_id:
        return out

    rules = rules if isinstance(rules, dict) else {}
    kind = event.get('type')

    if kind == 'purchase_captured':
        amount = event.get('amount_paise')
        if not _is_int(amount) or amount <= 0:
            return out
        if txn_id in out['transactions']:
            return out
        points = calculate_points(amount, rules.get('points_per_100_rupees', 1), rules.get('bonus_percent', 0), rules.get('cap_points'))
        out['transactions'][txn_id] = {'amount_paise': amount, 'awarded_points': points, 'reversed_points': 0, 'refunded_paise': 0}
        out['points_balance'] += points
        out['ledger'].append({'event_id': event_id, 'type': kind, 'points_delta': points})
        out['processed_event_ids'].append(event_id)
        return out

    if kind == 'refund_processed':
        txn = out['transactions'].get(txn_id)
        if not isinstance(txn, dict):
            return out
        refund = event.get('amount_paise')
        if not _is_int(refund) or refund <= 0 or txn['refunded_paise'] + refund > txn['amount_paise']:
            return out

        total_refunded = txn['refunded_paise'] + refund
        should_reverse = min(txn['awarded_points'], (txn['awarded_points'] * total_refunded) // txn['amount_paise'])
        delta = min(max(should_reverse - txn['reversed_points'], 0), out['points_balance'])
        out['points_balance'] -= delta
        txn['reversed_points'] += delta
        txn['refunded_paise'] = total_refunded
        out['ledger'].append({'event_id': event_id, 'type': kind, 'points_delta': -delta})
        out['processed_event_ids'].append(event_id)

    return out


def flag_repeat_transactions(transactions: list[dict], threshold: int = 2) -> list[dict]:
    if not isinstance(transactions, list):
        return []
    if threshold is None or not _is_int(threshold) or threshold < 1:
        threshold = 2

    groups = {}
    for tx in transactions:
        if not isinstance(tx, dict):
            continue
        key = (tx.get('account_id'), tx.get('date'), tx.get('amount_paise'))
        groups.setdefault(key, []).append(tx.get('transaction_id'))
    return [
        {'account_id': k[0], 'date': k[1], 'amount_paise': k[2], 'transaction_ids': ids}
        for k, ids in sorted(groups.items(), key=lambda item: str(item[0]))
        if len(ids) > threshold
    ]


def generate_account_statement_csv(account: dict) -> str:
    header = 'event_id,type,points_delta,running_balance'
    if not isinstance(account, dict):
        return header + '\n'

    ledger = account.get('ledger', [])
    if not isinstance(ledger, list):
        return header + '\n'

    rows = [header]
    running = 0
    for entry in ledger:
        if not isinstance(entry, dict):
            continue
        delta = entry.get('points_delta', 0)
        if not _is_int(delta):
            delta = 0
        running += delta
        rows.append(f"{entry.get('event_id', '')},{entry.get('type', '')},{delta},{running}")
    return '\n'.join(rows) + '\n'


