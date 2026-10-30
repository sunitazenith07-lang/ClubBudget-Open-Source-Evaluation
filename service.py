from copy import deepcopy

def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)

def calculate_points(amount_paise: int, points_per_100_rupees: int, bonus_percent: int=0, cap_points: int|None=None) -> int:
    if not _is_int(amount_paise) or amount_paise <= 0:
        return 0
    if not _is_int(points_per_100_rupees) or points_per_100_rupees <= 0:
        return 0
    if not _is_int(bonus_percent) or bonus_percent < 0:
        return 0
    if cap_points is not None and (not _is_int(cap_points) or cap_points < 0):
        return 0
    base = (amount_paise // 10000) * points_per_100_rupees
    points = base * (100 + bonus_percent) // 100
    if cap_points is not None:
        points = min(points, cap_points)
    return max(0, points)


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    out=deepcopy(account); out.setdefault('points_balance',0); out.setdefault('processed_event_ids',[]); out.setdefault('transactions',{}); out.setdefault('ledger',[])
    event_id=event.get('event_id'); kind=event.get('type'); txn_id=event.get('transaction_id')
    if not event_id or not txn_id:
        return out  
    if event_id in out['processed_event_ids']:
        return out  
    if kind=='purchase_captured':
        amount=event.get('amount_paise',0)
        if not _is_int(amount) or amount < 0:
            return out
        points=calculate_points(amount,rules.get('points_per_100_rupees',1),rules.get('bonus_percent',0),rules.get('cap_points'))
        if txn_id not in out['transactions']:
            out['transactions'][txn_id]={'amount_paise':amount,'awarded_points':points,'reversed_points':0,'refunded_paise':0}
            out['points_balance']+=points; out['ledger'].append({'event_id':event_id,'type':kind,'points_delta':points})
        else:
            return out
    elif kind=='refund_processed' and txn_id in out['transactions']:
        txn=out['transactions'][txn_id]; refund=event.get('amount_paise',0)
        if not _is_int(refund) or refund <= 0 or txn['refunded_paise'] + refund > txn['amount_paise']:
            return out
        txn['refunded_paise']+=refund
        should_reverse=txn['awarded_points']*txn['refunded_paise']//txn['amount_paise']
        delta=should_reverse-txn['reversed_points']
        delta=max(0, min(delta, out['points_balance']))
        out['points_balance']-=delta; txn['reversed_points']+= delta
        out['ledger'].append({'event_id':event_id,'type':kind,'transaction_id':txn_id,'points_delta':-delta,'balance_after':out['points_balance']})
    else:
        return out
    out['processed_event_ids'].append(event_id)
    return out


def flag_repeat_transactions(transactions: list[dict], threshold: int=2) -> list[dict]:
    if not _is_int(threshold) or threshold < 1:
        threshold = 1
    groups={}
    for tx in transactions or []:
        if not isinstance(tx, dict) or not tx.get('account_id') or not tx.get('date') or not _is_int(tx.get('amount_paise')):
            continue
        key=(tx.get('account_id'),tx.get('date'),tx.get('amount_paise')); ids=groups.setdefault(key,[])
        if tx.get('transaction_id') not in ids:
            ids.append(tx.get('transaction_id'))
    return [{'account_id':k[0],'date':k[1],'amount_paise':k[2],'transaction_ids':ids,'review_only':True} for k,ids in sorted(groups.items(),key=lambda item:str(item[0])) if len(ids)>threshold]
