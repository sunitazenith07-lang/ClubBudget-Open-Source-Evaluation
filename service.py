from copy import deepcopy

_is_int = lambda v: isinstance(v, int) and not isinstance(v, bool)
_valid_id = lambda v: (v.strip() != '') if isinstance(v, str) else _is_int(v)

def calculate_points(amount_paise, points_per_100_rupees, bonus_percent=0, cap_points=None) -> int:
    if not (_is_int(amount_paise) and amount_paise > 0 and _is_int(points_per_100_rupees) and points_per_100_rupees >= 0 and _is_int(bonus_percent) and bonus_percent >= 0):
        return 0
    if cap_points is not None and not (_is_int(cap_points) and cap_points >= 0):
        return 0
    pts = ((amount_paise // 10000) * points_per_100_rupees * (100 + bonus_percent)) // 100
    return max(0, min(pts, cap_points) if cap_points is not None else pts)

def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    out = deepcopy(account) if isinstance(account, dict) else {}
    if not _is_int(out.get('points_balance')) or out['points_balance'] < 0: out['points_balance'] = 0
    for k, t in (('processed_event_ids', list), ('transactions', dict), ('ledger', list)):
        if not isinstance(out.get(k), t): out[k] = t()
    if not isinstance(event, dict) or not _valid_id(eid := event.get('event_id')) or not _valid_id(tid := event.get('transaction_id')) or eid in out['processed_event_ids']:
        return out
    rules, txns, kind, amt = (rules if isinstance(rules, dict) else {}), out['transactions'], event.get('type'), event.get('amount_paise')
    if kind == 'purchase_captured' and _is_int(amt) and amt > 0 and tid not in txns:
        pts = calculate_points(amt, rules.get('points_per_100_rupees'), rules.get('bonus_percent', 0), rules.get('cap_points'))
        txns[tid] = {'amount_paise': amt, 'awarded_points': pts, 'reversed_points': 0, 'refunded_paise': 0}
        out['points_balance'] += pts
        out['ledger'].append({'event_id': eid, 'type': kind, 'transaction_id': tid, 'amount_paise': amt, 'points_delta': pts, 'balance_after': out['points_balance']})
        out['processed_event_ids'].append(eid)
    elif kind == 'refund_processed' and tid in txns and _is_int(amt) and amt > 0:
        tx = txns[tid]
        tot, ref, awd, rev = tx.get('amount_paise'), tx.get('refunded_paise', 0), tx.get('awarded_points', 0), tx.get('reversed_points', 0)
        if all(_is_int(v) and v >= 0 for v in (tot, ref, awd, rev)) and tot > 0 and ref + amt <= tot:
            delta = max(0, min(awd, awd * (ref + amt) // tot) - rev)
            app = min(delta, out['points_balance'])
            tx.update(refunded_paise=ref + amt, reversed_points=rev + app)
            out['points_balance'] -= app
            out['ledger'].append({'event_id': eid, 'type': kind, 'transaction_id': tid, 'amount_paise': amt, 'points_delta': -app, 'shortfall_points': delta - app, 'balance_after': out['points_balance']})
            out['processed_event_ids'].append(eid)
    return out

def flag_repeat_transactions(transactions, threshold=2) -> list[dict]:
    if not isinstance(transactions, (list, tuple)): return []
    threshold = threshold if (_is_int(threshold) and threshold >= 0) else 2
    groups = {}
    for tx in (t for t in transactions if isinstance(t, dict)):
        aid, dt, amt, tid = tx.get('account_id'), tx.get('date'), tx.get('amount_paise'), tx.get('transaction_id')
        if _valid_id(aid) and _valid_id(dt) and _valid_id(tid) and _is_int(amt) and amt > 0 and tid not in (ids := groups.setdefault((aid, dt, amt), [])):
            ids.append(tid)
    return [{'account_id': k[0], 'date': k[1], 'amount_paise': k[2], 'transaction_ids': ids, 'status': 'needs_review', 'note': 'Possible repeat for human review only; no action taken.'} for k, ids in sorted(groups.items(), key=lambda x: str(x[0])) if len(ids) > threshold]