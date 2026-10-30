from copy import deepcopy


def is_int(value):
    return type(value) is int


def calculate_points(amount_paise: int, points_per_100_rupees: int, bonus_percent: int = 0, cap_points: int | None = None) -> int:
    if not is_int(amount_paise) or amount_paise <= 0:
        return 0
    if not is_int(points_per_100_rupees) or points_per_100_rupees <= 0:
        return 0
    if not is_int(bonus_percent) or bonus_percent < 0:
        return 0
    if cap_points is not None and not is_int(cap_points):
        return 0
    base = (amount_paise // 10000) * points_per_100_rupees
    points = (base * (100 + bonus_percent)) // 100
    if cap_points is not None:
        if cap_points <= 0:
            return 0
        if points > cap_points:
            points = cap_points
    if points < 0:
        return 0
    return points


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    if type(account) is not dict:
        account = {}
    out = deepcopy(account)
    out.setdefault('points_balance', 0)
    out.setdefault('processed_event_ids', [])
    out.setdefault('transactions', {})
    out.setdefault('ledger', [])
    if type(event) is not dict:
        return out
    if type(rules) is not dict:
        rules = {}
    event_id = event.get('event_id')
    if not event_id or event_id in out['processed_event_ids']:
        return out
    kind = event.get('type')
    txn_id = event.get('transaction_id')
    if kind == 'purchase_captured':
        if not txn_id:
            return out
        amount = event.get('amount_paise', 0)
        if not is_int(amount) or amount <= 0:
            return out
        rate = rules.get('points_per_100_rupees', 1)
        bonus = rules.get('bonus_percent', 0)
        cap = rules.get('cap_points')
        points = calculate_points(amount, rate, bonus, cap)
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
    elif kind == 'refund_processed':
        if not txn_id or txn_id not in out['transactions']:
            return out
        txn = out['transactions'][txn_id]
        refund = event.get('amount_paise', 0)
        if not is_int(refund) or refund <= 0:
            return out
        if txn['refunded_paise'] + refund > txn['amount_paise']:
            return out
        txn['refunded_paise'] += refund
        awarded = txn['awarded_points']
        total_refunded = txn['refunded_paise']
        orig_amount = txn['amount_paise']
        if orig_amount <= 0:
            orig_amount = 1
        should_reverse = (awarded * total_refunded) // orig_amount
        if should_reverse > awarded:
            should_reverse = awarded
        delta = should_reverse - txn['reversed_points']
        if delta < 0:
            delta = 0
        if delta > out['points_balance']:
            delta = out['points_balance']
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
    if type(transactions) is not list:
        return []
    if not is_int(threshold) or threshold < 1:
        return []
    groups = {}
    for tx in transactions:
        if type(tx) is not dict:
            continue
        account_id = tx.get('account_id')
        date = tx.get('date')
        amount_paise = tx.get('amount_paise')
        txn_id = tx.get('transaction_id')
        if not account_id or not date or txn_id is None:
            continue
        if not is_int(amount_paise) or amount_paise <= 0:
            continue
        key = (account_id, date, amount_paise)
        if key not in groups:
            groups[key] = []
        groups[key].append(txn_id)
    alerts = []
    for key, ids in sorted(groups.items(), key=lambda item: str(item[0])):
        if len(ids) > threshold:
            alerts.append({
                'account_id': key[0],
                'date': key[1],
                'amount_paise': key[2],
                'transaction_ids': ids,
            })
    return alerts