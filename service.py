from copy import deepcopy

DEFAULT_REPEAT_THRESHOLD = 2


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _valid_id(v) -> bool:
    """Identifiers must be hashable scalars: non-empty str or int (not bool)."""
    if isinstance(v, str):
        return v.strip() != ''
    return _is_int(v)


def calculate_points(amount_paise, points_per_100_rupees, bonus_percent=0, cap_points=None) -> int:
    """Integer-only points calculation. Any invalid input or rule -> 0 points."""
    if not _is_int(amount_paise) or amount_paise <= 0:
        return 0
    if not _is_int(points_per_100_rupees) or points_per_100_rupees < 0:
        return 0
    if not _is_int(bonus_percent) or bonus_percent < 0:
        return 0
    if cap_points is not None and (not _is_int(cap_points) or cap_points < 0):
        return 0

    base_points = (amount_paise // 10000) * points_per_100_rupees
    points = (base_points * (100 + bonus_percent)) // 100
    if cap_points is not None:
        points = min(points, cap_points)  # cap of 0 -> 0 points
    return max(0, points)


def _normalise_account(account) -> dict:
    out = deepcopy(account) if isinstance(account, dict) else {}
    if not _is_int(out.get('points_balance')) or out['points_balance'] < 0:
        out['points_balance'] = 0
    if not isinstance(out.get('processed_event_ids'), list):
        out['processed_event_ids'] = []
    if not isinstance(out.get('transactions'), dict):
        out['transactions'] = {}
    if not isinstance(out.get('ledger'), list):
        out['ledger'] = []
    return out


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    """Returns a new account dict. Rejected events leave the account unchanged
    (they are not marked processed and not written to the ledger)."""
    out = _normalise_account(account)

    if not isinstance(event, dict):
        return out
    if not isinstance(rules, dict):
        rules = {}

    event_id = event.get('event_id')
    kind = event.get('type')
    txn_id = event.get('transaction_id')

    # Missing/unusable identifiers: reject (cannot guarantee idempotency or audit).
    if not _valid_id(event_id) or not _valid_id(txn_id):
        return out

    processed = out['processed_event_ids']
    if event_id in processed:          # idempotency
        return out

    txns = out['transactions']

    if kind == 'purchase_captured':
        amount = event.get('amount_paise')
        if not _is_int(amount) or amount <= 0:
            return out                  # invalid purchase: not accepted
        if txn_id in txns:
            return out                  # duplicate transaction: not accepted

        # Rules are required; a missing points rate means no points, not a default.
        points = calculate_points(
            amount,
            rules.get('points_per_100_rupees'),
            rules.get('bonus_percent', 0),
            rules.get('cap_points'),
        )
        txns[txn_id] = {
            'amount_paise': amount,
            'awarded_points': points,
            'reversed_points': 0,
            'refunded_paise': 0,
        }
        out['points_balance'] += points
        out['ledger'].append({
            'event_id': event_id,
            'type': kind,
            'transaction_id': txn_id,
            'amount_paise': amount,
            'points_delta': points,
            'balance_after': out['points_balance'],
        })
        processed.append(event_id)

    elif kind == 'refund_processed' and txn_id in txns:
        txn = txns[txn_id]
        amount = event.get('amount_paise')
        total_amount = txn.get('amount_paise')
        refunded_so_far = txn.get('refunded_paise', 0)
        awarded = txn.get('awarded_points', 0)
        reversed_points = txn.get('reversed_points', 0)

        if not all(_is_int(v) for v in (amount, total_amount, refunded_so_far, awarded, reversed_points)):
            return out
        if amount <= 0 or total_amount <= 0 or refunded_so_far < 0:
            return out
        if awarded < 0 or reversed_points < 0 or refunded_so_far + amount > total_amount:
            return out

        new_refunded = refunded_so_far + amount
        should_reverse = min(awarded, awarded * new_refunded // total_amount)
        delta = max(0, should_reverse - reversed_points)

        # Never go negative. Any shortfall stays unreversed (recorded in the ledger)
        # and is picked up by a later refund on the same transaction.
        balance = out['points_balance']
        applied = min(delta, balance)
        shortfall = delta - applied

        txn['refunded_paise'] = new_refunded
        txn['reversed_points'] = reversed_points + applied
        out['points_balance'] = balance - applied
        out['ledger'].append({
            'event_id': event_id,
            'type': kind,
            'transaction_id': txn_id,
            'amount_paise': amount,
            'points_delta': -applied,
            'shortfall_points': shortfall,
            'balance_after': out['points_balance'],
        })
        processed.append(event_id)

    # Any other type (declined, pending, unknown) or refund for unknown txn: ignored.
    return out


def flag_repeat_transactions(transactions, threshold=DEFAULT_REPEAT_THRESHOLD) -> list[dict]:
    """Group by (account_id, date, amount_paise) and flag groups with MORE than
    `threshold` DISTINCT transactions. For human review only; blocks nothing."""
    if not isinstance(transactions, (list, tuple)) or not transactions:
        return []
    if not _is_int(threshold) or threshold < 0:
        threshold = DEFAULT_REPEAT_THRESHOLD

    groups = {}
    for tx in transactions:
        if not isinstance(tx, dict):
            continue
        account_id = tx.get('account_id')
        date = tx.get('date')
        amount = tx.get('amount_paise')
        tx_id = tx.get('transaction_id')
        # Skip incomplete records instead of grouping them together under None.
        if not (_valid_id(account_id) and _valid_id(tx_id) and _valid_id(date)):
            continue
        if not _is_int(amount) or amount <= 0:
            continue
        ids = groups.setdefault((account_id, date, amount), [])
        if tx_id not in ids:                   # a replayed record is not a repeat
            ids.append(tx_id)

    return [
        {
            'account_id': k[0],
            'date': k[1],
            'amount_paise': k[2],
            'transaction_ids': ids,
            'status': 'needs_review',
            'note': 'Possible repeat for human review only; no action taken.',
        }
        for k, ids in sorted(groups.items(), key=lambda item: str(item[0]))
        if len(ids) > threshold
    ]