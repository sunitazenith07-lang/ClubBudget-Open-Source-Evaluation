from copy import deepcopy


def calculate_points(amount_paise, points_per_100_rupees, bonus_percent=0, cap_points=None) -> int:
    # Validate numeric inputs. Invalid or negative amounts/rules must not
    # generate points.
    if isinstance(amount_paise, bool) or not isinstance(amount_paise, (int, float)):
        return 0
    if isinstance(points_per_100_rupees, bool) or not isinstance(points_per_100_rupees, (int, float)):
        return 0
    if amount_paise <= 0 or points_per_100_rupees < 0:
        return 0
    if isinstance(bonus_percent, bool) or not isinstance(bonus_percent, (int, float)):
        bonus_percent = 0
    if cap_points is not None and (isinstance(cap_points, bool) or not isinstance(cap_points, (int, float))):
        cap_points = None

    base = (amount_paise // 10000) * points_per_100_rupees
    points = base * (100 + bonus_percent) // 100
    if cap_points is not None:
        points = min(points, cap_points)
    return max(0, int(points))


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    out = deepcopy(account) if isinstance(account, dict) else {}
    out.setdefault('points_balance', 0)
    out.setdefault('processed_event_ids', [])
    out.setdefault('transactions', {})
    out.setdefault('ledger', [])

    if not isinstance(event, dict):
        return out
    if not isinstance(rules, dict):
        rules = {}

    event_id = event.get('event_id')
    kind = event.get('type')
    txn_id = event.get('transaction_id')

    processed = out['processed_event_ids']
    if not isinstance(processed, list):
        processed = []
        out['processed_event_ids'] = processed

    # Idempotency: each event_id is processed at most once.
    if event_id is not None and event_id in processed:
        return out

    txns = out['transactions']
    if not isinstance(txns, dict):
        txns = {}
        out['transactions'] = txns

    if kind == 'purchase_captured':
        amount = event.get('amount_paise', 0)
        points = calculate_points(
            amount,
            rules.get('points_per_100_rupees', 1),
            rules.get('bonus_percent', 0),
            rules.get('cap_points'),
        )
        if txn_id not in txns:
            txns[txn_id] = {
                'amount_paise': amount,
                'awarded_points': points,
                'reversed_points': 0,
                'refunded_paise': 0,
            }
            out['points_balance'] = out.get('points_balance', 0) + points
            out['ledger'].append({'event_id': event_id, 'type': kind, 'points_delta': points})
        processed.append(event_id)

    elif kind == 'refund_processed' and txn_id in txns:
        txn = txns[txn_id]
        amount = event.get('amount_paise', 0)
        # Validate refund amount: positive int, not bool, within remaining balance.
        valid = (
            isinstance(amount, int)
            and not isinstance(amount, bool)
            and amount > 0
        )
        total_amount = txn.get('amount_paise', 0)
        if valid and (isinstance(total_amount, bool) or not isinstance(total_amount, int) or total_amount <= 0):
            valid = False
        refunded_so_far = txn.get('refunded_paise', 0)
        if valid and not (isinstance(refunded_so_far, int) and not isinstance(refunded_so_far, bool)):
            valid = False
        if valid and refunded_so_far + amount > total_amount:
            valid = False

        if valid:
            txn['refunded_paise'] = refunded_so_far + amount
            awarded = txn.get('awarded_points', 0)
            if isinstance(awarded, bool) or not isinstance(awarded, int):
                awarded = 0
            reversed_points = txn.get('reversed_points', 0)
            if isinstance(reversed_points, bool) or not isinstance(reversed_points, int):
                reversed_points = 0
            should_reverse = awarded * txn['refunded_paise'] // max(1, total_amount)
            delta = should_reverse - reversed_points
            if delta < 0:
                delta = 0
                should_reverse = reversed_points
            balance = out.get('points_balance', 0)
            if not isinstance(balance, int) or isinstance(balance, bool):
                balance = 0
            if delta > balance:
                delta = balance if balance > 0 else 0
                should_reverse = reversed_points + delta
            out['points_balance'] = balance - delta
            txn['reversed_points'] = should_reverse
            out['ledger'].append({'event_id': event_id, 'type': kind, 'points_delta': -delta})
            processed.append(event_id)

    return out


def flag_repeat_transactions(transactions, threshold=2) -> list[dict]:
    if not transactions:
        return []
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        threshold = 2
    if not isinstance(transactions, (list, tuple)):
        return []

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
