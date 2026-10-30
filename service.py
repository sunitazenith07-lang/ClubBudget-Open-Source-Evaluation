from copy import deepcopy


def calculate_points(amount_paise: int, points_per_100_rupees: int, bonus_percent: int=0, cap_points: int|None=None) -> int:

    if type(amount_paise) is not int or amount_paise < 0:
        return 0

    if type(points_per_100_rupees) is not int or points_per_100_rupees < 0:
        return 0

    if type(bonus_percent) is not int or bonus_percent < 0:
        return 0

    if cap_points is not None:
        if type(cap_points) is not int or cap_points < 0:
            return 0

    # Calculate base points using complete 100-rupee units.
    base_points = (amount_paise // 10000) * points_per_100_rupees

    # Apply the bonus using integer arithmetic.
    points = base_points * (100 + bonus_percent) // 100

    # Apply the optional cap after calculating the bonus.
    if cap_points is not None:
        points = min(points, cap_points)

    return points


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    out = deepcopy(account)
    out.setdefault('points_balance', 0)
    out.setdefault('processed_event_ids', [])
    out.setdefault('transactions', {})
    out.setdefault('ledger', [])

    event_id = event.get('event_id')
    kind = event.get('type')
    txn_id = event.get('transaction_id')

    # Reject events without valid identifiers.
    if not isinstance(event_id, str) or not event_id.strip():
        return out

    if not isinstance(txn_id, str) or not txn_id.strip():
        return out

    # Prevent the same event from being processed twice.
    if event_id in out['processed_event_ids']:
        return out

    if kind == 'purchase_captured':
        amount = event.get('amount_paise', 0)

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
        refund = event.get('amount_paise')

        if type(refund) is not int or refund <= 0:
            return out

        remaining_refundable = (
            txn['amount_paise'] - txn['refunded_paise']
        )

        if refund > remaining_refundable:
            return out

        txn['refunded_paise'] += refund

        should_reverse = (
            txn['awarded_points']
            * txn['refunded_paise']
            // max(1, txn['amount_paise'])
        )

        delta = should_reverse - txn['reversed_points']

        delta = min(delta, out['points_balance'])

        out['points_balance'] -= delta
        txn['reversed_points'] += delta

        out['ledger'].append({
            'event_id': event_id,
            'type': kind,
            'points_delta': -delta
        })

    out['processed_event_ids'].append(event_id)

    return out


def flag_repeat_transactions(transactions: list[dict], threshold: int = 2) -> list[dict]:
    groups = {}

    if not isinstance(transactions, list):
        return []

    if type(threshold) is not int or threshold < 1:
        return []

    for tx in transactions:
        # Ignore records that are not dictionaries.
        if not isinstance(tx, dict):
            continue

        account_id = tx.get('account_id')
        date = tx.get('date')
        amount = tx.get('amount_paise')
        transaction_id = tx.get('transaction_id')

        # Ignore records with missing or invalid fields.
        if not isinstance(account_id, str) or not account_id.strip():
            continue

        if not isinstance(date, str) or not date.strip():
            continue

        if type(amount) is not int or amount <= 0:
            continue

        if not isinstance(transaction_id, str) or not transaction_id.strip():
            continue

        key = (account_id, date, amount)
        groups.setdefault(key, []).append(transaction_id)

    return [
        {
            'account_id': key[0],
            'date': key[1],
            'amount_paise': key[2],
            'transaction_ids': ids
        }
        for key, ids in sorted(groups.items(), key=lambda item: str(item[0]))
        if len(ids) > threshold
    ]