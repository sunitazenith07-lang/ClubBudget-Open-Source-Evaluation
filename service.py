from copy import deepcopy


def calculate_points(amount_paise: int, points_per_100_rupees: int, bonus_percent: int=0, cap_points: int|None=None) -> int:
    # Use floor division (//) not round — integer arithmetic per spec
    base = (amount_paise // 10000) * points_per_100_rupees
    points = (base * (100 + bonus_percent)) // 100
    # cap_points=0 means zero points; cap_points=None means no cap
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

    # --- Idempotency: skip if event_id already processed ---
    if event_id in out['processed_event_ids']:
        return out

    # --- Unrecognized event types: award zero points, empty transactions ---
    if kind not in ('purchase_captured', 'refund_processed'):
        out['processed_event_ids'].append(event_id)
        return out

    # --- Purchase captured ---
    if kind == 'purchase_captured':
        amount = event.get('amount_paise', 0)
        # amount must be a valid positive integer; otherwise treat as 0
        if not isinstance(amount, int) or amount < 0:
            out['processed_event_ids'].append(event_id)
            return out
        points = calculate_points(
            amount,
            rules.get('points_per_100_rupees', 1),
            rules.get('bonus_percent', 0),
            rules.get('cap_points'),
        )
        # Only record if this transaction_id hasn't been recorded yet
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
        # Mark event as processed even if txn already existed
        out['processed_event_ids'].append(event_id)
        return out

    # --- Refund processed ---
    if kind == 'refund_processed' and txn_id in out['transactions']:
        txn = out['transactions'][txn_id]
        # refund amount must be a valid positive integer; invalid → reject entirely
        refund = event.get('amount_paise')
        # Use type() is int to reject booleans (True/False are instances of int)
        if type(refund) is not int or refund <= 0:
            # Invalid refund: do not change anything
            out['processed_event_ids'].append(event_id)
            return out
        # Refund exceeding the original amount is also rejected entirely
        if refund > txn['amount_paise']:
            out['processed_event_ids'].append(event_id)
            return out
        txn['refunded_paise'] += refund
        # Proportional reversal using integer arithmetic
        should_reverse = txn['awarded_points'] * txn['refunded_paise'] // max(1, txn['amount_paise'])
        delta = should_reverse - txn['reversed_points']
        # Never reverse more than awarded points remaining
        remaining = txn['awarded_points'] - txn['reversed_points']
        if delta > remaining:
            delta = remaining
        out['points_balance'] -= delta
        txn['reversed_points'] = should_reverse
        out['ledger'].append({
            'event_id': event_id,
            'type': kind,
            'points_delta': -delta,
        })
    out['processed_event_ids'].append(event_id)
    return out


def flag_repeat_transactions(transactions: list[dict], threshold: int=2) -> list[dict]:
    groups={}
    for tx in transactions:
        key=(tx.get('account_id'),tx.get('date'),tx.get('amount_paise')); groups.setdefault(key,[]).append(tx.get('transaction_id'))
    return [{'account_id':k[0],'date':k[1],'amount_paise':k[2],'transaction_ids':ids} for k,ids in sorted(groups.items(),key=lambda item:str(item[0])) if len(ids)>threshold]
