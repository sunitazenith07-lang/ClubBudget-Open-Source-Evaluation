"""Regression tests added for the defects fixed in service.py."""
import json
from pathlib import Path

import pytest

from models import new_account
from service import apply_reward_event, calculate_points, flag_repeat_transactions

RULES = {'points_per_100_rupees': 1}
DATA = json.loads((Path(__file__).resolve().parents[1] / 'data' / 'records.json').read_text())


def buy(account, event_id='P', txn='T', amount=100000, rules=RULES):
    return apply_reward_event(account, {'event_id': event_id, 'type': 'purchase_captured',
                                        'transaction_id': txn, 'amount_paise': amount}, rules)


def refund(account, event_id, amount, txn='T', rules=RULES):
    return apply_reward_event(account, {'event_id': event_id, 'type': 'refund_processed',
                                        'transaction_id': txn, 'amount_paise': amount}, rules)


# --- Defect 1: round() instead of floor -------------------------------------
def test_floor_not_round_just_below_boundary():
    # starter: round(25.99) = 26 -> 28 points with 10% bonus; correct floor gives 25 -> 27
    assert calculate_points(259900, 1, 10, 100) == 27
    assert calculate_points(15000, 1) == 1          # round(1.5) would give 2


# --- Defect 2: cap of 0 ignored because `if cap_points:` is falsy for 0 ------
def test_cap_zero_and_cap_none_are_different():
    assert calculate_points(500000, 1, 0, 0) == 0
    assert calculate_points(500000, 1, 0, None) == 50


@pytest.mark.parametrize('per,bonus,cap', [(-1, 10, 100), (1, -100, None), (1, 0, -1),
                                           (True, 0, None), (1.5, 0, None), ('1', 0, None)])
def test_invalid_rule_values_award_zero(per, bonus, cap):
    assert calculate_points(100000, per, bonus, cap) == 0


@pytest.mark.parametrize('amount', [True, 1.5, '100000', None, [], {}])
def test_non_integer_amount_awards_zero(amount):
    assert calculate_points(amount, 1) == 0


def test_dataset_rule_cases_never_negative():
    for case in DATA['rules_cases']:
        assert calculate_points(259900, case['points_per_100_rupees'],
                                case['bonus_percent'], case['cap_points']) >= 0


# --- Defect 3: duplicate event_id was applied twice ---------------------------
def test_duplicate_refund_event_is_applied_once():
    a = buy(new_account('A'))
    b = refund(a, 'R1', 30000)
    c = refund(b, 'R1', 30000)
    assert c['points_balance'] == b['points_balance'] == 7
    assert c['transactions']['T']['refunded_paise'] == 30000
    assert len(c['ledger']) == 2


def test_same_transaction_new_event_id_does_not_award_twice():
    a = buy(new_account('A'), 'P1')
    b = buy(a, 'P2')
    assert b['points_balance'] == 10 and len(b['ledger']) == 1


@pytest.mark.parametrize('missing', ['event_id', 'transaction_id'])
def test_missing_identifiers_are_ignored(missing):
    event = {'event_id': 'E', 'type': 'purchase_captured', 'transaction_id': 'T', 'amount_paise': 100000}
    del event[missing]
    out = apply_reward_event(new_account('A'), event, RULES)
    assert out['points_balance'] == 0 and out['ledger'] == [] and out['processed_event_ids'] == []


# --- Defect 4: refunds were not bounded ---------------------------------------
def test_multiple_partial_refunds_then_over_refund():
    a = buy(new_account('A'))                       # 10 points on Rs 1000
    a = refund(a, 'R1', 25000)                       # 10*25000//100000 = 2
    a = refund(a, 'R2', 25000)                       # cumulative 5 -> +3
    assert a['points_balance'] == 5
    rejected = refund(a, 'R3', 50001)                # would exceed purchase amount
    assert rejected['points_balance'] == 5
    assert rejected['transactions']['T']['refunded_paise'] == 50000
    a = refund(a, 'R4', 50000)                       # completes full refund
    assert a['points_balance'] == 0
    assert a['transactions']['T']['reversed_points'] == 10


def test_cumulative_reversal_has_no_rounding_drift():
    a = buy(new_account('A'), amount=30000)          # 3 points
    for i in range(2):
        a = refund(a, f'R{i}', 15000)                # per-refund floor would reverse only 1 + 1
    assert a['points_balance'] == 0
    assert a['transactions']['T']['reversed_points'] == 3


def test_balance_never_negative_even_if_points_already_spent():
    a = buy(new_account('A'))
    a['points_balance'] = 2                          # simulate points spent elsewhere
    a = refund(a, 'R', 100000)
    assert a['points_balance'] == 0


def test_refund_on_zero_point_purchase():
    a = buy(new_account('A'), amount=9999)           # 0 points
    a = refund(a, 'R', 9999)
    assert a['points_balance'] == 0 and a['ledger'][-1]['points_delta'] == 0


# --- Ledger audit -------------------------------------------------------------
def test_ledger_sum_matches_balance_and_records_balance_after():
    a = buy(new_account('A'), 'P1', 'T1', 259900, {'points_per_100_rupees': 1, 'bonus_percent': 10, 'cap_points': 100})
    a = refund(a, 'R1', 100000, 'T1')
    assert sum(e['points_delta'] for e in a['ledger']) == a['points_balance']
    assert a['ledger'][-1]['balance_after'] == a['points_balance']
    assert a['ledger'][-1]['transaction_id'] == 'T1'


def test_dataset_event_replay_keeps_invariants():
    accounts = {}
    for event in DATA['reward_events']:
        acct_id = event.get('account_id')
        before = accounts.get(acct_id, new_account(acct_id))
        accounts[acct_id] = apply_reward_event(before, event, RULES)
    for acct in accounts.values():
        assert acct['points_balance'] >= 0
        assert sum(e['points_delta'] for e in acct['ledger']) == acct['points_balance']
        assert len(acct['processed_event_ids']) == len(set(acct['processed_event_ids']))
        for txn in acct['transactions'].values():
            assert 0 <= txn['reversed_points'] <= txn['awarded_points']
            assert 0 <= txn['refunded_paise'] <= txn['amount_paise']


# --- Repeat alerts --------------------------------------------------------------
def test_repeat_alerts_empty_and_malformed_input():
    assert flag_repeat_transactions([]) == []
    assert flag_repeat_transactions(None) == []
    rows = [None, {'transaction_id': '1'}, {'transaction_id': '2', 'account_id': 'A', 'date': 'D', 'amount_paise': '5'}]
    assert flag_repeat_transactions(rows, 1) == []


def test_repeat_alert_same_record_twice_is_not_a_repeat():
    row = {'transaction_id': 'X', 'account_id': 'A', 'date': 'D', 'amount_paise': 100}
    assert flag_repeat_transactions([row, dict(row), dict(row)], 2) == []


def test_repeat_alerts_dataset_groups_are_deterministic_and_review_only():
    alerts = flag_repeat_transactions(DATA['transactions'], DATA['repeat_alert_threshold'])
    assert len(alerts) == 60                         # 180 rows = 60 groups of 3
    keys = [(a['account_id'], a['date'], a['amount_paise']) for a in alerts]
    assert keys == sorted(keys)
    assert all(a['review_only'] and len(a['transaction_ids']) == 3 for a in alerts)