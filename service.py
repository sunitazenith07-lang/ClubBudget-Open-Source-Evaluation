from copy import deepcopy


def calculate_points(amount_paise: int, points_per_100_rupees: int, bonus_percent: int=0, cap_points: int|None=None) -> int:
    numeric_rules = (amount_paise, points_per_100_rupees, bonus_percent)
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in numeric_rules):
        return 0
    if cap_points is not None and (
        isinstance(cap_points, bool) or not isinstance(cap_points, int) or cap_points < 0
    ):
        return 0

    base = (amount_paise // 10000) * points_per_100_rupees
    points = base * (100 + bonus_percent) // 100
    if cap_points is not None:
        points = min(points, cap_points)
    return points


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    out=deepcopy(account); out.setdefault('points_balance',0); out.setdefault('processed_event_ids',[]); out.setdefault('transactions',{}); out.setdefault('ledger',[])
    event_id=event.get('event_id'); kind=event.get('type'); txn_id=event.get('transaction_id')
    valid_event_id = isinstance(event_id, str) and bool(event_id)
    if not valid_event_id:
        return out
    if event_id in out['processed_event_ids']:
        return out

    if kind=='purchase_captured':
        amount=event.get('amount_paise')
        valid_transaction_id = isinstance(txn_id, str) and bool(txn_id)
        valid_amount = isinstance(amount, int) and not isinstance(amount, bool) and amount >= 0
        if not valid_transaction_id or not valid_amount:
            out['processed_event_ids'].append(event_id)
            return out

        points=calculate_points(amount,rules.get('points_per_100_rupees',1),rules.get('bonus_percent',0),rules.get('cap_points'))
        if txn_id not in out['transactions']:
            balance_before = out['points_balance']
            out['transactions'][txn_id]={'amount_paise':amount,'awarded_points':points,'reversed_points':0,'refunded_paise':0}
            out['points_balance'] += points
            out['ledger'].append({'event_id':event_id,'type':kind,'points_delta':out['points_balance'] - balance_before})
    elif kind=='refund_processed':
        refund=event.get('amount_paise')
        valid_transaction_id = isinstance(txn_id, str) and bool(txn_id)
        valid_refund = isinstance(refund, int) and not isinstance(refund, bool) and refund > 0
        if not valid_transaction_id or not valid_refund or txn_id not in out['transactions']:
            out['processed_event_ids'].append(event_id)
            return out

        txn=out['transactions'][txn_id]
        original_amount=txn.get('amount_paise')
        awarded_points=txn.get('awarded_points')
        previous_refunded=txn.get('refunded_paise')
        previous_reversed=txn.get('reversed_points')
        valid_transaction = (
            isinstance(original_amount, int) and not isinstance(original_amount, bool) and original_amount > 0
            and isinstance(awarded_points, int) and not isinstance(awarded_points, bool) and awarded_points >= 0
            and isinstance(previous_refunded, int) and not isinstance(previous_refunded, bool) and previous_refunded >= 0
            and isinstance(previous_reversed, int) and not isinstance(previous_reversed, bool) and previous_reversed >= 0
        )
        if not valid_transaction or refund > original_amount - previous_refunded:
            out['processed_event_ids'].append(event_id)
            return out

        cumulative_refund=previous_refunded + refund
        total_reversal=awarded_points * cumulative_refund // original_amount
        incremental_reversal=total_reversal - previous_reversed
        balance_before=out['points_balance']
        balance_after=balance_before - incremental_reversal
        if (
            total_reversal > awarded_points
            or incremental_reversal < 0
            or not isinstance(balance_before, int)
            or isinstance(balance_before, bool)
            or balance_after < 0
        ):
            out['processed_event_ids'].append(event_id)
            return out

        txn['refunded_paise']=cumulative_refund
        txn['reversed_points']=total_reversal
        out['points_balance']=balance_after
        out['ledger'].append({'event_id':event_id,'type':kind,'points_delta':balance_after - balance_before})
    out['processed_event_ids'].append(event_id)
    return out


def flag_repeat_transactions(transactions: list[dict], threshold: int=2) -> list[dict]:
    groups={}
    for tx in transactions:
        key=(tx.get('account_id'),tx.get('date'),tx.get('amount_paise')); groups.setdefault(key,[]).append(tx.get('transaction_id'))
    return [{'account_id':k[0],'date':k[1],'amount_paise':k[2],'transaction_ids':ids} for k,ids in sorted(groups.items(),key=lambda item:str(item[0])) if len(ids)>threshold]
