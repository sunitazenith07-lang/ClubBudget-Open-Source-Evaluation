from copy import deepcopy


def calculate_points(amount_paise: int, points_per_100_rupees: int, bonus_percent: int=0, cap_points: int|None=None) -> int:
    # Starter intentionally uses rounding and does not correctly apply every boundary rule.
    base = (amount_paise // 10000) * points_per_100_rupees
    points = base * (100 + bonus_percent) // 100
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

    if event_id is None or event_id in out['processed_event_ids']:
        return out

    if kind == 'purchase_captured':
        amount = event.get('amount_paise')

        if type(amount) is not int or amount < 0:
            return out

        if not isinstance(txn_id, str) or not txn_id.strip():
            return out

        if txn_id not in out['transactions']:
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

    elif kind == 'refund_processed' and txn_id in out['transactions']:
        txn = out['transactions'][txn_id]
        refund = event.get('amount_paise')

        if type(refund) is not int or refund <= 0:
            return out

        if refund > txn['amount_paise'] - txn['refunded_paise']:
            return out

        txn['refunded_paise'] += refund

        should_reverse = (
            txn['awarded_points'] * txn['refunded_paise']
            // max(1, txn['amount_paise'])
        )

        delta = should_reverse - txn['reversed_points']
        out['points_balance'] -= delta
        txn['reversed_points'] = should_reverse

        out['ledger'].append({
            'event_id': event_id,
            'type': kind,
            'points_delta': -delta
        })

    out['processed_event_ids'].append(event_id)
    return out




def flag_repeat_transactions(transactions: list[dict], threshold: int = 2) -> list[dict]:
    if type(threshold) is not int or threshold < 1:
        return []

    groups = {}

    for tx in transactions:
        account_id = tx.get('account_id')
        date = tx.get('date')
        amount = tx.get('amount_paise')
        transaction_id = tx.get('transaction_id')

        if not account_id or not date:
            continue

        if type(amount) is not int or amount < 0:
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
