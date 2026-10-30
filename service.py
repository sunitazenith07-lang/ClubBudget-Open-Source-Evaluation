from copy import deepcopy


def _is_non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_identifier(value: object) -> bool:
    return (
        isinstance(value, (str, int))
        and not isinstance(value, bool)
        and value != ""
    )


def calculate_points(amount_paise: int, points_per_100_rupees: int, bonus_percent: int=0, cap_points: int|None=None) -> int:
    if not all(
        _is_non_negative_int(value)
        for value in (amount_paise, points_per_100_rupees, bonus_percent)
    ):
        return 0
    if cap_points is not None and not _is_non_negative_int(cap_points):
        return 0

    base = (amount_paise // 10000) * points_per_100_rupees
    points = base * (100 + bonus_percent) // 100
    if cap_points is not None:
        points = min(points, cap_points)
    return points


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    out=deepcopy(account); out.setdefault('points_balance',0); out.setdefault('processed_event_ids',[]); out.setdefault('transactions',{}); out.setdefault('ledger',[])
    event_id=event.get('event_id'); kind=event.get('type'); txn_id=event.get('transaction_id')
    if not _is_identifier(event_id) or event_id in out['processed_event_ids']:
        return out

    if kind=='purchase_captured':
        amount=event.get('amount_paise',0)
        if _is_identifier(txn_id) and _is_non_negative_int(amount) and txn_id not in out['transactions']:
            points=calculate_points(amount,rules.get('points_per_100_rupees',1),rules.get('bonus_percent',0),rules.get('cap_points'))
            out['transactions'][txn_id]={'amount_paise':amount,'awarded_points':points,'reversed_points':0,'refunded_paise':0}
            out['points_balance']+=points; out['ledger'].append({'event_id':event_id,'type':kind,'points_delta':points})
    elif kind=='refund_processed' and _is_identifier(txn_id) and txn_id in out['transactions']:
        txn=out['transactions'][txn_id]; refund=event.get('amount_paise',0)
        amount=txn.get('amount_paise')
        awarded=txn.get('awarded_points')
        already_refunded=txn.get('refunded_paise')
        already_reversed=txn.get('reversed_points')
        if (
            _is_non_negative_int(refund)
            and refund > 0
            and _is_non_negative_int(amount)
            and amount > 0
            and _is_non_negative_int(awarded)
            and _is_non_negative_int(already_refunded)
            and _is_non_negative_int(already_reversed)
            and refund <= amount - already_refunded
        ):
            txn['refunded_paise'] += refund
            should_reverse=min(awarded, awarded * txn['refunded_paise'] // amount)
            delta=max(0, should_reverse - already_reversed)
            balance=out['points_balance']
            actual_delta=min(delta, max(0, balance))
            out['points_balance']=max(0, balance - actual_delta)
            txn['reversed_points']=should_reverse
            out['ledger'].append({'event_id':event_id,'type':kind,'points_delta':-actual_delta})
    out['processed_event_ids'].append(event_id)
    return out


def flag_repeat_transactions(transactions: list[dict], threshold: int=2) -> list[dict]:
    groups={}
    for tx in transactions:
        if (
            not _is_identifier(tx.get('transaction_id'))
            or not _is_identifier(tx.get('account_id'))
            or not _is_identifier(tx.get('date'))
            or not _is_non_negative_int(tx.get('amount_paise'))
        ):
            continue
        key=(tx.get('account_id'),tx.get('date'),tx.get('amount_paise')); groups.setdefault(key,[]).append(tx.get('transaction_id'))
    return [{'account_id':k[0],'date':k[1],'amount_paise':k[2],'transaction_ids':ids} for k,ids in sorted(groups.items(),key=lambda item:str(item[0])) if len(ids)>threshold]
