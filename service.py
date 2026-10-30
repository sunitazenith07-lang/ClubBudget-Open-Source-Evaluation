from copy import deepcopy


def calculate_points(amount_paise: int, points_per_100_rupees: int, bonus_percent: int=0, cap_points: int|None=None) -> int:
    if type(amount_paise) is not int or amount_paise <= 0: return 0
    if type(points_per_100_rupees) is not int or points_per_100_rupees <= 0: return 0
    if type(bonus_percent) is not int or bonus_percent < 0: return 0
    base = (amount_paise // 10000) * points_per_100_rupees
    points = base * (100 + bonus_percent) // 100
    if cap_points is not None:
        if type(cap_points) is not int or cap_points <= 0: return 0
        points = min(points, cap_points)
    return max(0, points)


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    out = deepcopy(account) if isinstance(account, dict) else {}
    out.setdefault('points_balance', 0); out.setdefault('processed_event_ids', []); out.setdefault('transactions', {}); out.setdefault('ledger', [])
    if not isinstance(event, dict): return out
    rules = rules if isinstance(rules, dict) else {}
    event_id = event.get('event_id'); kind = event.get('type'); txn_id = event.get('transaction_id')
    if not event_id or not txn_id: return out
    if event_id in out['processed_event_ids']: return out
    if kind == 'purchase_captured':
        amount = event.get('amount_paise')
        points = calculate_points(amount, rules.get('points_per_100_rupees', 1), rules.get('bonus_percent', 0), rules.get('cap_points'))
        if txn_id not in out['transactions']:
            out['transactions'][txn_id] = {'amount_paise': amount if type(amount) is int else 0, 'awarded_points': points, 'reversed_points': 0, 'refunded_paise': 0}
            out['points_balance'] += points; out['ledger'].append({'event_id': event_id, 'type': kind, 'points_delta': points})
        out['processed_event_ids'].append(event_id)
    elif kind == 'refund_processed' and txn_id in out['transactions']:
        txn = out['transactions'][txn_id]; refund = event.get('amount_paise')
        if type(refund) is int and 0 < refund <= txn['amount_paise'] - txn['refunded_paise']:
            txn['refunded_paise'] += refund
            should_reverse = min(txn['awarded_points'], txn['awarded_points'] * txn['refunded_paise'] // max(1, txn['amount_paise']))
            delta = min(max(0, should_reverse - txn['reversed_points']), out['points_balance'])
            out['points_balance'] -= delta; txn['reversed_points'] += delta
            out['ledger'].append({'event_id': event_id, 'type': kind, 'points_delta': -delta})
            out['processed_event_ids'].append(event_id)
    return out


def flag_repeat_transactions(transactions: list[dict], threshold: int=2) -> list[dict]:
    groups = {}
    if not isinstance(transactions, list): return []
    for tx in transactions:
        if not isinstance(tx, dict): continue
        key = (tx.get('account_id'), tx.get('date'), tx.get('amount_paise')); groups.setdefault(key, []).append(tx.get('transaction_id'))
    return [{'account_id': k[0], 'date': k[1], 'amount_paise': k[2], 'transaction_ids': ids} for k, ids in sorted(groups.items(), key=lambda item: str(item[0])) if len(ids) > threshold]