from copy import deepcopy


def calculate_points(
    amount_paise: int,
    points_per_100_rupees: int,
    bonus_percent: int = 0,
    cap_points: int | None = None,
) -> int:
    """Calculate points using integer arithmetic:
    base_points = floor(amount_paise / 10000) * points_per_100_rupees
    bonus_points = floor(base_points * (100 + bonus_percent) / 100)
    apply optional cap_points last.

    Invalid or negative amounts/rules must not generate points. A cap of zero means zero points.
    """
    if not isinstance(amount_paise, int) or isinstance(amount_paise, bool) or amount_paise <= 0:
        return 0
    if not isinstance(points_per_100_rupees, int) or isinstance(points_per_100_rupees, bool) or points_per_100_rupees <= 0:
        return 0
    if not isinstance(bonus_percent, int) or isinstance(bonus_percent, bool) or bonus_percent < 0:
        return 0

    base_points = (amount_paise // 10000) * points_per_100_rupees
    bonus_points = (base_points * (100 + bonus_percent)) // 100

    if cap_points is not None:
        if not isinstance(cap_points, int) or isinstance(cap_points, bool) or cap_points < 0:
            return 0
        bonus_points = min(bonus_points, cap_points)

    return max(0, bonus_points)


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    """Apply a reward event to an account.
    - Only captured purchases earn points. Declined, pending and unknown events must not.
    - Process each event_id once so replaying purchase/refund events cannot alter balances twice.
    - Reverse points proportionally for refunds using integer arithmetic, never reverse more than awarded
      and never allow a negative balance.
    - Write an auditable ledger entry for each accepted purchase/refund event.
    - Handle empty input, missing identifiers, unknown transactions and boundary values safely.
    """
    out = deepcopy(account) if isinstance(account, dict) else {}
    out.setdefault('points_balance', 0)
    out.setdefault('processed_event_ids', [])
    out.setdefault('transactions', {})
    out.setdefault('ledger', [])

    if not isinstance(event, dict):
        return out

    event_id = event.get('event_id')
    if not event_id or not isinstance(event_id, str):
        return out

    if event_id in out['processed_event_ids']:
        return out

    kind = event.get('type')
    txn_id = event.get('transaction_id')
    if not txn_id or not isinstance(txn_id, str):
        return out

    if not isinstance(rules, dict):
        rules = {}

    if kind == 'purchase_captured':
        amount = event.get('amount_paise')
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            return out

        points = calculate_points(
            amount,
            rules.get('points_per_100_rupees', 1),
            rules.get('bonus_percent', 0),
            rules.get('cap_points'),
        )

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
        if txn_id not in out['transactions']:
            return out

        txn = out['transactions'][txn_id]
        refund = event.get('amount_paise')

        # Validate refund amount: must be positive integer, and cumulative refund cannot exceed original amount
        if not isinstance(refund, int) or isinstance(refund, bool) or refund <= 0:
            return out

        if txn['refunded_paise'] + refund > txn['amount_paise']:
            return out

        new_refunded_paise = txn['refunded_paise'] + refund
        orig_amount = txn['amount_paise']
        awarded = txn['awarded_points']

        if orig_amount > 0:
            should_reverse = (awarded * new_refunded_paise) // orig_amount
        else:
            should_reverse = 0

        # Never reverse more than awarded
        should_reverse = min(should_reverse, awarded)

        delta = should_reverse - txn['reversed_points']
        if delta < 0:
            delta = 0

        # Never allow negative points balance
        delta = min(delta, out['points_balance'])

        out['points_balance'] -= delta
        txn['reversed_points'] += delta
        txn['refunded_paise'] = new_refunded_paise

        out['ledger'].append({
            'event_id': event_id,
            'type': kind,
            'points_delta': -delta,
        })
        out['processed_event_ids'].append(event_id)

    return out


def flag_repeat_transactions(transactions: list[dict], threshold: int = 2) -> list[dict]:
    """Flag possible repeats by account, date and amount using the supplied threshold.
    Alerts are for human review only; never block a transaction or automatically accuse a customer.
    """
    if not isinstance(transactions, list):
        return []
    if threshold is None or not isinstance(threshold, int) or isinstance(threshold, bool) or threshold < 1:
        threshold = 2
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


def generate_account_statement_csv(account: dict) -> str:
    """Generate a CSV account statement representing ledger events and running balance.
    Optional stretch work deliverable.
    """
    header = "event_id,type,points_delta,running_balance"
    if not isinstance(account, dict):
        return header + "\n"

    ledger = account.get('ledger', [])
    if not isinstance(ledger, list):
        return header + "\n"

    lines = [header]
    running_balance = 0
    for entry in ledger:
        if not isinstance(entry, dict):
            continue
        event_id = str(entry.get('event_id', ''))
        kind = str(entry.get('type', ''))
        delta = entry.get('points_delta', 0)
        if not isinstance(delta, int) or isinstance(delta, bool):
            delta = 0
        running_balance += delta
        lines.append(f"{event_id},{kind},{delta},{running_balance}")

    return "\n".join(lines) + "\n"


