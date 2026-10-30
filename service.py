from copy import deepcopy


def is_valid_int(value):
    # bool is a subclass of int in Python, so isinstance(True, int) is True.
    # A bool must never be treated as 0 or 1 points.
    return isinstance(value, int) and not isinstance(value, bool)


def calculate_points(amount_paise: int, points_per_100_rupees: int, bonus_percent: int=0, cap_points: int|None=None) -> int:
    # FIX 1: Invalid or negative rules/amounts must not generate points.
    if not (is_valid_int(amount_paise) and amount_paise>=0 and is_valid_int(points_per_100_rupees) and points_per_100_rupees>=0 and is_valid_int(bonus_percent) and bonus_percent>=0):
        return 0
    if cap_points is not None and not (is_valid_int(cap_points) and cap_points>=0):
        return 0
    base = (amount_paise // 10000) * points_per_100_rupees
    points = base * (100 + bonus_percent) // 100
    # FIX 2: Zero is also a valid cap.
    if cap_points is not None:
        points = min(points, cap_points)
    return max(0, points)


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    # A non-dict account has no identity to award to: return a blank safe account, do not crash.
    if not isinstance(account, dict):
        return {'account_id':None,'points_balance':0,'processed_event_ids':[],'transactions':{},'ledger':[]}
    out=deepcopy(account); out.setdefault('points_balance',0); out.setdefault('processed_event_ids',[]); out.setdefault('transactions',{}); out.setdefault('ledger',[])
    # Malformed event or rules: return unchanged, without consuming an event id.
    if not isinstance(event, dict) or not isinstance(rules, dict):
        return out
    event_id=event.get('event_id'); kind=event.get('type'); txn_id=event.get('transaction_id')
    # FIX 3: Prevent missing and duplicate events.
    if event_id is None or event_id in out['processed_event_ids']:
        return out
    if kind=='purchase_captured':
        amount=event.get('amount_paise',0)
        # FIX 4: Validate purchase amount and transaction ID.
        if is_valid_int(amount) and amount>=0 and txn_id is not None and txn_id not in out['transactions']:
            points=calculate_points(amount,rules.get('points_per_100_rupees',1),rules.get('bonus_percent',0),rules.get('cap_points'))
            out['transactions'][txn_id]={'amount_paise':amount,'awarded_points':points,'reversed_points':0,'refunded_paise':0}
            out['points_balance']+=points; out['ledger'].append({'event_id':event_id,'type':kind,'points_delta':points})
    elif kind=='refund_processed' and txn_id in out['transactions']:
        txn=out['transactions'][txn_id]; refund=event.get('amount_paise',0)
        # FIX 5: Validate refund and prevent excessive refunds.
        if is_valid_int(refund) and refund>=0 and txn['refunded_paise']+refund<=txn['amount_paise']:
            txn['refunded_paise']+=refund
            should_reverse=min(txn['awarded_points'],txn['awarded_points']*txn['refunded_paise']//max(1,txn['amount_paise']))
            delta=max(0,should_reverse-txn['reversed_points']); delta=min(delta,max(0,out['points_balance']))
            out['points_balance']-=delta; txn['reversed_points']+=delta
            out['ledger'].append({'event_id':event_id,'type':kind,'points_delta':-delta})
    # FIX 6: Remember the event to prevent replay.
    out['processed_event_ids'].append(event_id)
    return out


def flag_repeat_transactions(transactions: list[dict], threshold: int=2) -> list[dict]:
    # A None or non-iterable list, or an unusable threshold, returns [] instead of crashing.
    if transactions is None:
        return []
    try:
        transactions=list(transactions)
    except TypeError:
        return []
    groups={}
    for tx in transactions:
        if not isinstance(tx,dict) or any(tx.get(k) is None for k in ('account_id','date','amount_paise','transaction_id')):
            continue
        key=(tx.get('account_id'),tx.get('date'),tx.get('amount_paise')); groups.setdefault(key,[]).append(tx.get('transaction_id'))
    try:
        return [{'account_id':k[0],'date':k[1],'amount_paise':k[2],'transaction_ids':ids} for k,ids in sorted(groups.items(),key=lambda item:str(item[0])) if len(ids)>threshold]
    except TypeError:
        return []
