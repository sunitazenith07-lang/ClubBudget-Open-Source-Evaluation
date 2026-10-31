from copy import deepcopy
from typing import Any

PAISE_PER_100_RUPEES = 10_000


def _is_int(value: Any) -> bool:
    """True for real ints only. bool is a subclass of int, so exclude it explicitly."""
    return isinstance(value, int) and not isinstance(value, bool)


def _is_id(value: Any) -> bool:
    return isinstance(value, str) and value != ''


def calculate_points(amount_paise: int, points_per_100_rupees: int, bonus_percent: int = 0,
                     cap_points: int | None = None) -> int:
    """Integer-only: floor(base) -> floor(bonus) -> cap last. Invalid input -> 0 points."""
    if not (_is_int(amount_paise) and _is_int(points_per_100_rupees) and _is_int(bonus_percent)):
        return 0
    if cap_points is not None and not _is_int(cap_points):
        return 0
    if amount_paise < 0 or points_per_100_rupees < 0 or bonus_percent < 0:
        return 0
    if cap_points is not None and cap_points < 0:
        return 0
    base = (amount_paise // PAISE_PER_100_RUPEES) * points_per_100_rupees
    points = base * (100 + bonus_percent) // 100
    if cap_points is not None:  # `is not None`: a cap of 0 must mean 0 points
        points = min(points, cap_points)
    return points


def _apply_purchase(out: dict, event: dict, rules: dict) -> bool:
    txn_id, amount = event['transaction_id'], event.get('amount_paise')
    if not _is_int(amount) or amount <= 0 or txn_id in out['transactions']:
        return False  # invalid amount, or duplicate capture of the same transaction
    points = calculate_points(amount, rules.get('points_per_100_rupees', 1),
                              rules.get('bonus_percent', 0), rules.get('cap_points'))
    out['transactions'][txn_id] = {'amount_paise': amount, 'awarded_points': points,
                                   'reversed_points': 0, 'refunded_paise': 0}
    out['points_balance'] += points
    out['ledger'].append({'event_id': event['event_id'], 'type': event['type'],
                          'transaction_id': txn_id, 'points_delta': points})
    return True


def _apply_refund(out: dict, event: dict) -> bool:
    txn_id, refund = event['transaction_id'], event.get('amount_paise')
    txn = out['transactions'].get(txn_id)
    if txn is None or not _is_int(refund) or refund <= 0:
        return False  # unknown transaction or invalid refund amount
    refunded = txn['refunded_paise'] + refund
    if refunded > txn['amount_paise']:
        return False  # cumulative over-refund: reject whole event, don't clamp
    should_reverse = txn['awarded_points'] * refunded // txn['amount_paise']
    delta = min(should_reverse - txn['reversed_points'], max(out['points_balance'], 0))
    txn['refunded_paise'] = refunded
    txn['reversed_points'] += delta
    out['points_balance'] -= delta
    out['ledger'].append({'event_id': event['event_id'], 'type': event['type'],
                          'transaction_id': txn_id, 'points_delta': -delta})
    return True


def apply_reward_event(account: dict, event: dict, rules: dict) -> dict:
    out = deepcopy(account)
    out.setdefault('points_balance', 0)
    out.setdefault('processed_event_ids', [])
    out.setdefault('transactions', {})
    out.setdefault('ledger', [])
    rules = rules if isinstance(rules, dict) else {}
    if not isinstance(event, dict):
        return out
    event_id, txn_id = event.get('event_id'), event.get('transaction_id')
    if not _is_id(event_id) or not _is_id(txn_id) or event_id in out['processed_event_ids']:
        return out  # missing identifiers or replayed event: no state change
    kind = event.get('type')
    if kind == 'purchase_captured':
        accepted = _apply_purchase(out, event, rules)
    elif kind == 'refund_processed':
        accepted = _apply_refund(out, event)
    else:
        accepted = False  # declined / pending / unknown never earn points
    if accepted:  # processed ids and ledger stay 1:1
        out['processed_event_ids'].append(event_id)
    return out


def flag_repeat_transactions(transactions: list[dict], threshold: int = 2) -> list[dict]:
    """Human-review signals only. Never blocks or accuses."""
    if not _is_int(threshold):
        threshold = 2
    threshold = max(threshold, 1)  # a single transaction can never be a "repeat"
    groups: dict[tuple, list] = {}
    for tx in transactions or []:
        if not isinstance(tx, dict):
            continue
        key = (tx.get('account_id'), tx.get('date'), tx.get('amount_paise'))
        if not _is_id(key[0]) or not _is_id(key[1]) or not _is_int(key[2]):
            continue  # incomplete records must not form a fake group under None
        groups.setdefault(key, []).append(tx.get('transaction_id'))
    return [{'account_id': k[0], 'date': k[1], 'amount_paise': k[2], 'transaction_ids': ids}
            for k, ids in sorted(groups.items(), key=lambda item: str(item[0]))
            if len(ids) > threshold]