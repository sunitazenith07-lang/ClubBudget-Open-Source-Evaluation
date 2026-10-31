from copy import deepcopy


def _is_non_negative_integer(value: object) -> bool:
    return type(value) is int and value >= 0


def _is_identifier(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def calculate_points(
    amount_paise: int,
    points_per_100_rupees: int,
    bonus_percent: int = 0,
    cap_points: int | None = None,
) -> int:
    if not _is_non_negative_integer(amount_paise):
        return 0
    if not _is_non_negative_integer(points_per_100_rupees):
        return 0
    if not _is_non_negative_integer(bonus_percent):
        return 0
    if cap_points is not None and not _is_non_negative_integer(cap_points):
        return 0

    base_points = (amount_paise // 10000) * points_per_100_rupees
    points = base_points * (100 + bonus_percent) // 100
    if cap_points is not None:
        points = min(points, cap_points)
    return points


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    out = deepcopy(account)
    out.setdefault('points_balance', 0)
    out.setdefault('processed_event_ids', [])
    out.setdefault('transactions', {})
    out.setdefault('ledger', [])

    if not isinstance(event, dict):
        return out

    event_id = event.get('event_id')
    if not _is_identifier(event_id) or event_id in out['processed_event_ids']:
        return out
    out['processed_event_ids'].append(event_id)

    kind = event.get('type')
    txn_id = event.get('transaction_id')
    if not _is_identifier(txn_id):
        return out

    if kind == 'purchase_captured':
        amount = event.get('amount_paise')
        if not _is_non_negative_integer(amount) or txn_id in out['transactions']:
            return out

        points = calculate_points(
            amount,
            rules.get('points_per_100_rupees', 1),
            rules.get('bonus_percent', 0),
            rules.get('cap_points'),
        )
        out['transactions'][txn_id] = {
            'amount_paise': amount,
            'awarded_points': points,
            'reversed_points': 0,
            'refunded_paise': 0,
        }
        balance = out['points_balance']
        if not _is_non_negative_integer(balance):
            balance = 0
        out['points_balance'] = balance + points
        out['ledger'].append({
            'event_id': event_id,
            'type': kind,
            'points_delta': points,
        })
    elif kind == 'refund_processed' and txn_id in out['transactions']:
        txn = out['transactions'][txn_id]
        refund = event.get('amount_paise')
        amount = txn.get('amount_paise')
        awarded_points = txn.get('awarded_points')
        refunded_paise = txn.get('refunded_paise')
        reversed_points = txn.get('reversed_points')
        if (
            not _is_non_negative_integer(refund)
            or refund == 0
            or not _is_non_negative_integer(amount)
            or amount == 0
            or not _is_non_negative_integer(awarded_points)
            or not _is_non_negative_integer(refunded_paise)
            or not _is_non_negative_integer(reversed_points)
            or refund > amount - refunded_paise
        ):
            return out

        txn['refunded_paise'] += refund
        should_reverse = min(
            awarded_points,
            awarded_points * txn['refunded_paise'] // amount,
        )
        delta = max(0, should_reverse - reversed_points)
        balance = out['points_balance']
        if not _is_non_negative_integer(balance):
            balance = 0
        delta = min(delta, balance)
        out['points_balance'] = balance - delta
        txn['reversed_points'] = reversed_points + delta
        out['ledger'].append({
            'event_id': event_id,
            'type': kind,
            'points_delta': -delta,
        })
    return out


def flag_repeat_transactions(transactions: list[dict], threshold: int=2) -> list[dict]:
    if not isinstance(transactions, list) or type(threshold) is not int or threshold < 0:
        return []

    groups = {}
    for tx in transactions:
        if not isinstance(tx, dict):
            continue
        account_id = tx.get('account_id')
        date = tx.get('date')
        amount = tx.get('amount_paise')
        transaction_id = tx.get('transaction_id')
        if (
            not _is_identifier(account_id)
            or not _is_identifier(date)
            or not _is_non_negative_integer(amount)
            or not _is_identifier(transaction_id)
        ):
            continue

        key = (account_id, date, amount)
        transaction_ids = groups.setdefault(key, [])
        if transaction_id not in transaction_ids:
            transaction_ids.append(transaction_id)

    return [
        {
            'account_id': key[0],
            'date': key[1],
            'amount_paise': key[2],
            'transaction_ids': transaction_ids,
        }
        for key, transaction_ids in sorted(groups.items(), key=lambda item: str(item[0]))
        if len(transaction_ids) > threshold
    ]
