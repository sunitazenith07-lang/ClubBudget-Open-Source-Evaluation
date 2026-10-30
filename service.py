from copy import deepcopy

PAISE_PER_100_RUPEES = 10000
DEFAULT_REPEAT_THRESHOLD = 2


def _is_int(value) -> bool:
    # bool is a subclass of int, but True/False are never valid amounts or rule values.
    return isinstance(value, int) and not isinstance(value, bool)


def calculate_points(amount_paise: int, points_per_100_rupees: int, bonus_percent: int=0, cap_points: int|None=None) -> int:
    """Integer-only points: floor base, then bonus, then optional cap. Invalid input earns 0."""
    if not (_is_int(amount_paise) and _is_int(points_per_100_rupees) and _is_int(bonus_percent)):
        return 0
    if cap_points is not None and not _is_int(cap_points):
        return 0
    if amount_paise <= 0 or points_per_100_rupees < 0 or bonus_percent < 0:
        return 0
    if cap_points is not None and cap_points < 0:
        return 0
    base = (amount_paise // PAISE_PER_100_RUPEES) * points_per_100_rupees
    points = base * (100 + bonus_percent) // 100
    if cap_points is not None:
        points = min(points, cap_points)
    return points


def _ledger_entry(out: dict, event: dict, points_delta: int) -> dict:
    return {'event_id':event.get('event_id'),'type':event.get('type'),'transaction_id':event.get('transaction_id'),
            'amount_paise':event.get('amount_paise'),'points_delta':points_delta,'balance_after':out['points_balance']}


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    """Return a new account with the event applied. Rejected events leave the copy unchanged."""
    out=deepcopy(account); out.setdefault('points_balance',0); out.setdefault('processed_event_ids',[]); out.setdefault('transactions',{}); out.setdefault('ledger',[])
    if not isinstance(event, dict) or not isinstance(rules, dict):
        return out
    event_id=event.get('event_id'); kind=event.get('type'); txn_id=event.get('transaction_id'); amount=event.get('amount_paise')
    # Without both identifiers the event cannot be de-duplicated or linked to a purchase.
    if event_id is None or txn_id is None or event_id in out['processed_event_ids']:
        return out
    if not _is_int(amount) or amount <= 0:
        return out

    if kind=='purchase_captured':
        if txn_id in out['transactions']:
            return out  # a second capture for the same transaction must not award twice
        points=calculate_points(amount,rules.get('points_per_100_rupees',1),rules.get('bonus_percent',0),rules.get('cap_points'))
        out['transactions'][txn_id]={'amount_paise':amount,'awarded_points':points,'reversed_points':0,'refunded_paise':0}
        out['points_balance']+=points
        delta=points
    elif kind=='refund_processed':
        txn=out['transactions'].get(txn_id)
        if txn is None or txn['refunded_paise']+amount > txn['amount_paise']:
            return out  # unknown transaction, or cumulative refund would exceed the purchase
        txn['refunded_paise']+=amount
        should_reverse=txn['awarded_points']*txn['refunded_paise']//txn['amount_paise']
        delta=min(should_reverse-txn['reversed_points'], out['points_balance'])
        txn['reversed_points']+=delta
        out['points_balance']-=delta
        delta=-delta
    else:
        return out  # declined, pending and unknown events never change the account

    out['ledger'].append(_ledger_entry(out,event,delta))
    out['processed_event_ids'].append(event_id)
    return out


def repeat_threshold_from_config(config: dict|None) -> int:
    """Read `repeat_alert_threshold` from a config dict; fall back to the default if missing or invalid."""
    value = config.get('repeat_alert_threshold') if isinstance(config, dict) else None
    if not _is_int(value) or value < 1:
        return DEFAULT_REPEAT_THRESHOLD
    return value


def flag_repeat_transactions(transactions: list[dict], threshold: int=DEFAULT_REPEAT_THRESHOLD) -> list[dict]:
    """Group by account/date/amount and return groups with more than `threshold` transactions.

    Alerts are for human review only; they never block or reject a transaction.
    """
    if not _is_int(threshold) or threshold < 1:
        threshold = 1
    groups={}
    for tx in transactions or []:
        if not isinstance(tx, dict):
            continue
        key=(tx.get('account_id'),tx.get('date'),tx.get('amount_paise'))
        if key[0] is None or key[1] is None or not _is_int(key[2]) or key[2] <= 0 or tx.get('transaction_id') is None:
            continue
        groups.setdefault(key,[]).append(tx.get('transaction_id'))
    return [{'account_id':k[0],'date':k[1],'amount_paise':k[2],'transaction_ids':ids,'count':len(ids),'status':'needs_review'}
            for k,ids in sorted(groups.items(),key=lambda item:(str(item[0][0]),str(item[0][1]),item[0][2])) if len(ids)>threshold]
