from copy import deepcopy


def calculate_points(amount_paise: int, points_per_100_rupees: int, bonus_percent: int=0, cap_points: int|None=None) -> int:
    if amount_paise <= 0: return 0
    base = (amount_paise // 10000) * points_per_100_rupees
    points = base * (100 + bonus_percent) // 100
    if cap_points is not None:
        points = min(points, cap_points)
    return max(0, points)


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    out=deepcopy(account); out.setdefault('points_balance',0); out.setdefault('processed_event_ids',[]); out.setdefault('transactions',{}); out.setdefault('ledger',[])
    event_id=event.get('event_id'); kind=event.get('type'); txn_id=event.get('transaction_id')
    if event_id in out['processed_event_ids']:
        return out
    if kind=='purchase_captured':
        amount=event.get('amount_paise',0)
        points=calculate_points(amount,rules.get('points_per_100_rupees',1),rules.get('bonus_percent',0),rules.get('cap_points'))
        if txn_id not in out['transactions']:
            out['transactions'][txn_id]={'amount_paise':amount,'awarded_points':points,'reversed_points':0,'refunded_paise':0}
            out['points_balance']+=points; out['ledger'].append({'event_id':event_id,'type':kind,'points_delta':points})
    elif kind=='refund_processed' and txn_id in out['transactions']:
        txn=out['transactions'][txn_id]; refund=event.get('amount_paise',0)
        if type(refund) is int and refund > 0 and (txn['refunded_paise'] + refund) <= txn['amount_paise']:
            txn['refunded_paise']+=refund
            should_reverse=txn['awarded_points']*txn['refunded_paise']//max(1,txn['amount_paise'])
            delta=should_reverse-txn['reversed_points']; out['points_balance']-=delta; txn['reversed_points']=should_reverse
            out['ledger'].append({'event_id':event_id,'type':kind,'points_delta':-delta})
    out['processed_event_ids'].append(event_id)
    return out


def flag_repeat_transactions(transactions: list[dict], threshold: int=2) -> list[dict]:
    groups={}
    for tx in transactions:
        key=(tx.get('account_id'),tx.get('date'),tx.get('amount_paise')); groups.setdefault(key,[]).append(tx.get('transaction_id'))
    return [{'account_id':k[0],'date':k[1],'amount_paise':k[2],'transaction_ids':ids} for k,ids in sorted(groups.items(),key=lambda item:str(item[0])) if len(ids)>threshold]