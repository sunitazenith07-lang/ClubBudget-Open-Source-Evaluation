from copy import deepcopy

def _is_valid_int(val) -> bool:
    return isinstance(val, int) and not isinstance(val, bool)

def calculate_points(amount_paise: int, points_per_100_rupees: int, bonus_percent: int=0, cap_points: int|None=None) -> int:
    if not _is_valid_int(amount_paise) or amount_paise <= 0: return 0
    if not _is_valid_int(points_per_100_rupees) or points_per_100_rupees <= 0: return 0
    if not _is_valid_int(bonus_percent) or bonus_percent < 0: return 0
    if cap_points is not None and (not _is_valid_int(cap_points) or cap_points <= 0): return 0
    base = (amount_paise // 10000) * points_per_100_rupees
    total = (base * (100 + bonus_percent)) // 100
    if cap_points is not None and total > cap_points: total = cap_points
    return max(0, total)

def apply_reward_event(account: dict, event: dict, rules: dict|None=None) -> dict:
    out = deepcopy(account) if isinstance(account, dict) else {}
    out.setdefault('points_balance', 0); out.setdefault('processed_event_ids', []); out.setdefault('transactions', {}); out.setdefault('ledger', [])
    if not isinstance(event, dict): return out
    event_id = event.get('event_id'); rules = rules if isinstance(rules, dict) else {}
    if not isinstance(event_id, str) or not event_id or event_id in out['processed_event_ids']: return out
    kind = event.get('type')
    if kind == 'purchase_captured':
        txn_id = event.get('transaction_id'); amount_paise = event.get('amount_paise')
        if not isinstance(txn_id, str) or not txn_id or txn_id in out['transactions'] or not _is_valid_int(amount_paise) or amount_paise <= 0:
            return out
        points = calculate_points(amount_paise, rules.get('points_per_100_rupees', 1), rules.get('bonus_percent', 0), rules.get('cap_points'))
        out['transactions'][txn_id] = {'amount_paise': amount_paise, 'awarded_points': points, 'reversed_points': 0, 'refunded_paise': 0}
        out['points_balance'] += points
        out['ledger'].append({'event_id': event_id, 'type': kind, 'points_delta': points})
        out['processed_event_ids'].append(event_id)
    elif kind == 'refund_processed':
        txn_id = event.get('transaction_id')
        txn = out['transactions'].get(txn_id) if isinstance(txn_id, str) else None
        if not txn: return out
        refund_paise = event.get('amount_paise')
        remaining_paise = txn['amount_paise'] - txn['refunded_paise']
        if not _is_valid_int(refund_paise) or refund_paise <= 0 or refund_paise > remaining_paise:
            return out
        new_refunded = txn['refunded_paise'] + refund_paise
        should_reverse = min(txn['awarded_points'], (txn['awarded_points'] * new_refunded) // txn['amount_paise'])
        delta = max(0, min(should_reverse - txn['reversed_points'], out['points_balance']))
        out['points_balance'] -= delta
        txn['reversed_points'] += delta
        txn['refunded_paise'] = new_refunded
        out['ledger'].append({'event_id': event_id, 'type': kind, 'points_delta': -delta})
        out['processed_event_ids'].append(event_id)
    return out


def flag_repeat_transactions(transactions: list[dict], threshold: int=2) -> list[dict]:
    if not isinstance(transactions, list) or not _is_valid_int(threshold) or threshold < 1:
        return []
    groups = {}
    for tx in transactions:
        if not isinstance(tx, dict): continue
        acct, date, amt, tx_id = tx.get('account_id'), tx.get('date'), tx.get('amount_paise'), tx.get('transaction_id')
        if not isinstance(acct, str) or not acct or not isinstance(date, str) or not date or not _is_valid_int(amt) or amt <= 0 or not isinstance(tx_id, str) or not tx_id:
            continue
        groups.setdefault((acct, date, amt), []).append(tx_id)
    return [
        {'account_id': k[0], 'date': k[1], 'amount_paise': k[2], 'transaction_ids': ids}
        for k, ids in sorted(groups.items(), key=lambda item: item[0])
        if len(ids) > threshold
    ]