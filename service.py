from copy import deepcopy


def _is_non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_identifier(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def calculate_points(amount_paise: int, points_per_100_rupees: int, bonus_percent: int=0, cap_points: int|None=None) -> int:
    if not _is_non_negative_int(amount_paise):
        return 0
    if not _is_non_negative_int(points_per_100_rupees) or not _is_non_negative_int(bonus_percent):
        return 0
    if cap_points is not None and not _is_non_negative_int(cap_points):
        return 0

    base = (amount_paise // 10000) * points_per_100_rupees
    points = base * (100 + bonus_percent) // 100
    return min(points, cap_points) if cap_points is not None else points


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    out = deepcopy(account) if isinstance(account, dict) else {}
    out.setdefault('points_balance', 0)
    out.setdefault('processed_event_ids', [])
    out.setdefault('transactions', {})
    out.setdefault('ledger', [])
    if not _is_non_negative_int(out['points_balance']):
        out['points_balance'] = 0
    if not isinstance(out['processed_event_ids'], list):
        out['processed_event_ids'] = []
    if not isinstance(out['transactions'], dict):
        out['transactions'] = {}
    if not isinstance(out['ledger'], list):
        out['ledger'] = []
    if not isinstance(event, dict) or not _is_identifier(out.get('account_id')):
        return out

    event_id = event.get('event_id')
    kind = event.get('type')
    txn_id = event.get('transaction_id')
    if not _is_identifier(event_id) or event_id in out['processed_event_ids']:
        return out
    event_account_id = event.get('account_id')
    if event_account_id is not None and event_account_id != out['account_id']:
        return out

    amount = event.get('amount_paise')
    if kind == 'purchase_captured' and _is_identifier(txn_id) and _is_non_negative_int(amount):
        if txn_id not in out['transactions']:
            if isinstance(rules, dict):
                points = calculate_points(
                    amount,
                    rules.get('points_per_100_rupees', 1),
                    rules.get('bonus_percent', 0),
                    rules.get('cap_points'),
                )
            else:
                points = 0
            out['transactions'][txn_id] = {
                'amount_paise': amount,
                'awarded_points': points,
                'reversed_points': 0,
                'refunded_paise': 0,
            }
            out['points_balance'] += points
            out['ledger'].append({
                'event_id': event_id,
                'transaction_id': txn_id,
                'account_id': out['account_id'],
                'type': kind,
                'amount_paise': amount,
                'points_delta': points,
                'balance_after': out['points_balance'],
            })
    elif kind == 'refund_processed' and _is_identifier(txn_id) and _is_non_negative_int(amount) and amount > 0:
        txn = out['transactions'].get(txn_id)
        if isinstance(txn, dict):
            original_amount = txn.get('amount_paise')
            awarded_points = txn.get('awarded_points')
            refunded_paise = txn.get('refunded_paise', 0)
            reversed_points = txn.get('reversed_points', 0)
            if (
                _is_non_negative_int(original_amount)
                and _is_non_negative_int(awarded_points)
                and _is_non_negative_int(refunded_paise)
                and _is_non_negative_int(reversed_points)
                and amount <= original_amount - refunded_paise
            ):
                total_refunded = refunded_paise + amount
                target_reversed = awarded_points * total_refunded // original_amount if original_amount else 0
                points_to_reverse = min(target_reversed - reversed_points, out['points_balance'])
                if points_to_reverse >= 0:
                    txn['refunded_paise'] = total_refunded
                    txn['reversed_points'] = reversed_points + points_to_reverse
                    out['points_balance'] -= points_to_reverse
                    out['ledger'].append({
                        'event_id': event_id,
                        'transaction_id': txn_id,
                        'account_id': out['account_id'],
                        'type': kind,
                        'amount_paise': amount,
                        'points_delta': -points_to_reverse,
                        'balance_after': out['points_balance'],
                    })

    out['processed_event_ids'].append(event_id)
    return out


def flag_repeat_transactions(transactions: list[dict], threshold: int=2) -> list[dict]:
    if not _is_non_negative_int(threshold) or not isinstance(transactions, list):
        return []
    groups = {}
    for tx in transactions:
        if not isinstance(tx, dict):
            continue
        account_id = tx.get('account_id')
        date = tx.get('date')
        amount = tx.get('amount_paise')
        transaction_id = tx.get('transaction_id')
        if not _is_identifier(account_id) or not _is_identifier(date) or not _is_identifier(transaction_id) or not _is_non_negative_int(amount):
            continue
        key = (account_id, date, amount)
        ids = groups.setdefault(key, [])
        if transaction_id not in ids:
            ids.append(transaction_id)
    return [
        {'account_id': key[0], 'date': key[1], 'amount_paise': key[2], 'transaction_ids': ids}
        for key, ids in sorted(groups.items(), key=lambda item: str(item[0]))
        if len(ids) > threshold
    ]
