from copy import deepcopy

def calculate_points(
    amount_paise: int,
    points_per_100_rupees: int,
    bonus_percent: int = 0,
    cap_points: int | None = None
) -> int:
    if type(amount_paise) is not int or amount_paise < 0:
        return 0
    if type(points_per_100_rupees) is not int or points_per_100_rupees < 0:
        return 0
    if type(bonus_percent) is not int or bonus_percent < 0:
        return 0
    if cap_points is not None:
        if type(cap_points) is not int or cap_points < 0:
            return 0
    base_points = (amount_paise // 10000) * points_per_100_rupees
    final_points = (base_points * (100 + bonus_percent)) // 100
    if cap_points is not None:
        final_points = min(final_points, cap_points)
    return final_points


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    out = deepcopy(account)
    out.setdefault('points_balance', 0)
    out.setdefault('processed_event_ids', [])
    out.setdefault('transactions', {})
    out.setdefault('ledger', [])
    if not isinstance(event, dict) or not isinstance(rules, dict):
        return out
    event_id = event.get('event_id')
    txn_id = event.get('transaction_id')
    kind = event.get('type')
    if not isinstance(event_id, str) or not event_id.strip():
        return out
    if not isinstance(txn_id, str) or not txn_id.strip():
        return out
    if event_id in out['processed_event_ids']:
        return out
    if kind == 'purchase_captured':
        amount = event.get('amount_paise')
        if type(amount) is not int or amount < 0:
            return out
        if txn_id in out['transactions']:
            out['processed_event_ids'].append(event_id)
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
    elif kind == 'refund_processed':
        if txn_id not in out['transactions']:
            return out
        refund = event.get('amount_paise')
        if type(refund) is not int or refund <= 0:
            return out
        txn = out['transactions'][txn_id]
        if refund > txn['amount_paise'] - txn['refunded_paise']:
            return out
        txn['refunded_paise'] += refund
        should_reverse = 0
        if txn['amount_paise'] > 0:
            should_reverse = (
                txn['awarded_points'] * txn['refunded_paise']
            ) // txn['amount_paise']
        should_reverse = min(should_reverse, txn['awarded_points'])
        delta = should_reverse - txn['reversed_points']
        delta = min(delta, max(0, out['points_balance']))
        out['points_balance'] -= delta
        txn['reversed_points'] += delta
        out['ledger'].append({
            'event_id': event_id,
            'type': kind,
            'points_delta': -delta
        })
    else:
        return out
    out['processed_event_ids'].append(event_id)
    return out 


def flag_repeat_transactions(transactions: list[dict], threshold: int=2) -> list[dict]:
    groups={}
    for tx in transactions:
        key=(tx.get('account_id'),tx.get('date'),tx.get('amount_paise')); groups.setdefault(key,[]).append(tx.get('transaction_id'))
    return [{'account_id':k[0],'date':k[1],'amount_paise':k[2],'transaction_ids':ids} for k,ids in sorted(groups.items(),key=lambda item:str(item[0])) if len(ids)>threshold]
