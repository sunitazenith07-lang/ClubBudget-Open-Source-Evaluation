import pytest
from models import new_account
from service import calculate_points, apply_reward_event, flag_repeat_transactions

RULES = {'points_per_100_rupees': 1}


def buy(acct, eid='P', tid='T', amt=100000, rules=RULES):
    return apply_reward_event(acct, {'event_id': eid, 'type': 'purchase_captured',
                                     'transaction_id': tid, 'amount_paise': amt}, rules)


def refund(acct, eid, amt, tid='T'):
    return apply_reward_event(acct, {'event_id': eid, 'type': 'refund_processed',
                                     'transaction_id': tid, 'amount_paise': amt}, RULES)


def test_bool_amount_and_rules_give_zero():
    assert calculate_points(True, 1) == 0
    assert calculate_points(100000, True) == 0


def test_demo_example_floors_bonus_to_27():
    assert calculate_points(259900, 1, 10, 100) == 27


@pytest.mark.parametrize('eid', [None, '', 5])
def test_missing_event_id_is_rejected_and_not_recorded(eid):
    out = buy(new_account('A'), eid=eid)
    assert out['points_balance'] == 0 and out['processed_event_ids'] == [] and out['ledger'] == []


def test_duplicate_capture_with_new_event_id_awards_once():
    a = buy(new_account('A'))
    b = buy(a, eid='P2')
    assert b['points_balance'] == 10 and len(b['ledger']) == 1


def test_cumulative_over_refund_rejected_on_second_event():
    a = refund(buy(new_account('A')), 'R1', 60000)
    b = refund(a, 'R2', 60000)
    assert b == a


def test_split_refunds_reverse_exactly_awarded():
    a = buy(new_account('A'), amt=259900, rules={'points_per_100_rupees': 1, 'bonus_percent': 10, 'cap_points': 100})
    a = refund(a, 'R1', 100000)
    assert a['points_balance'] == 17
    a = refund(a, 'R2', 159900)
    assert a['points_balance'] == 0 and a['transactions']['T']['reversed_points'] == 27


def test_tiny_refund_reverses_zero_but_is_ledgered():
    a = refund(buy(new_account('A')), 'R1', 1)
    assert a['points_balance'] == 10 and a['ledger'][-1]['points_delta'] == 0


def test_refund_replay_is_idempotent():
    a = refund(buy(new_account('A')), 'R1', 50000)
    assert refund(a, 'R1', 50000) == a


def test_ledger_sums_to_balance():
    a = refund(buy(new_account('A')), 'R1', 30000)
    assert sum(l['points_delta'] for l in a['ledger']) == a['points_balance']


def test_incomplete_records_do_not_form_repeat_group():
    rows = [{'transaction_id': str(i), 'account_id': None, 'date': 'D', 'amount_paise': 1000} for i in range(3)]
    assert flag_repeat_transactions(rows, 2) == []