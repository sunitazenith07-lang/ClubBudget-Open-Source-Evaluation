from models import new_account
from service import calculate_points, apply_reward_event, flag_repeat_transactions


def test_points_use_floor(): assert calculate_points(19999,1)==1

def test_bonus_then_cap(): assert calculate_points(50000,2,50,6)==6

def test_negative_amount_gives_zero(): assert calculate_points(-10000,1)==0

def test_cap_zero_is_respected(): assert calculate_points(50000,1,cap_points=0)==0

def test_purchase_event_once():
    a=new_account('A'); e={'event_id':'E1','type':'purchase_captured','transaction_id':'T1','amount_paise':25000}; rules={'points_per_100_rupees':1}
    a=apply_reward_event(a,e,rules); b=apply_reward_event(a,e,rules); assert a['points_balance']==2 and b['points_balance']==2 and b['processed_event_ids']==['E1']

def test_input_account_not_mutated():
    a=new_account('A'); out=apply_reward_event(a,{'event_id':'E1','type':'purchase_captured','transaction_id':'T1','amount_paise':25000},{'points_per_100_rupees':1}); assert a['points_balance']==0 and out['points_balance']==2

def test_declined_event_does_not_award():
    out=apply_reward_event(new_account('A'),{'event_id':'E1','type':'purchase_declined','transaction_id':'T','amount_paise':25000},{'points_per_100_rupees':1}); assert out['points_balance']==0

def test_partial_refund_reverses_proportionally():
    rules={'points_per_100_rupees':1}; a=apply_reward_event(new_account('A'),{'event_id':'E1','type':'purchase_captured','transaction_id':'T','amount_paise':100000},rules); b=apply_reward_event(a,{'event_id':'E2','type':'refund_processed','transaction_id':'T','amount_paise':50000},rules); assert b['points_balance']==5 and b['transactions']['T']['reversed_points']==5

def test_invalid_or_excess_refund_ignored():
    rules={'points_per_100_rupees':1}; a=apply_reward_event(new_account('A'),{'event_id':'E1','type':'purchase_captured','transaction_id':'T','amount_paise':100000},rules)
    for amount in [-1,150000]:
        b=apply_reward_event(a,{'event_id':'E2','type':'refund_processed','transaction_id':'T','amount_paise':amount},rules); assert b['transactions']['T']['refunded_paise']==0 and b['points_balance']==10

def test_unknown_refund_safe(): assert apply_reward_event(new_account('A'),{'event_id':'E1','type':'refund_processed','transaction_id':'X','amount_paise':1000},{'points_per_100_rupees':1})['points_balance']==0

def test_repeat_group():
    rows=[{'transaction_id':str(i),'account_id':'A','date':'D','amount_paise':1000} for i in range(3)]; assert flag_repeat_transactions(rows,2)[0]['transaction_ids']==['0','1','2']

def test_different_accounts_not_grouped():
    rows=[{'transaction_id':'1','account_id':'A','date':'D','amount_paise':1000},{'transaction_id':'2','account_id':'B','date':'D','amount_paise':1000}]; assert flag_repeat_transactions(rows,1)==[]


def test_non_int_and_boolean_inputs_to_calculate_points():
    assert calculate_points(True, 1) == 0
    assert calculate_points(10000, True) == 0
    assert calculate_points(10000, 1, bonus_percent=True) == 0
    assert calculate_points(10000, 1, cap_points=False) == 0
    assert calculate_points(10000.5, 1) == 0
    assert calculate_points("10000", 1) == 0
    assert calculate_points(None, 1) == 0
    assert calculate_points(10000, 1, bonus_percent=-10) == 0
    assert calculate_points(10000, 1, cap_points=-1) == 0


def test_refund_event_replay_and_cumulative_partial_refunds():
    rules = {'points_per_100_rupees': 1, 'bonus_percent': 0, 'cap_points': None}
    acct = new_account('ACCT-1')
    acct = apply_reward_event(acct, {'event_id': 'E1', 'type': 'purchase_captured', 'transaction_id': 'T1', 'amount_paise': 100000}, rules)
    assert acct['points_balance'] == 10

    # First partial refund of 30,000 paise -> 3 points reversed
    acct = apply_reward_event(acct, {'event_id': 'E2', 'type': 'refund_processed', 'transaction_id': 'T1', 'amount_paise': 30000}, rules)
    assert acct['points_balance'] == 7
    assert acct['transactions']['T1']['refunded_paise'] == 30000
    assert acct['transactions']['T1']['reversed_points'] == 3

    # Replay E2 -> idempotent, no change
    acct = apply_reward_event(acct, {'event_id': 'E2', 'type': 'refund_processed', 'transaction_id': 'T1', 'amount_paise': 30000}, rules)
    assert acct['points_balance'] == 7
    assert acct['processed_event_ids'] == ['E1', 'E2']
    assert len(acct['ledger']) == 2

    # Second partial refund of 70,000 paise -> cumulative 100,000 paise -> remaining 7 points reversed
    acct = apply_reward_event(acct, {'event_id': 'E3', 'type': 'refund_processed', 'transaction_id': 'T1', 'amount_paise': 70000}, rules)
    assert acct['points_balance'] == 0
    assert acct['transactions']['T1']['refunded_paise'] == 100000
    assert acct['transactions']['T1']['reversed_points'] == 10

    # Cumulative over-refund of 1 paisa -> rejected
    acct = apply_reward_event(acct, {'event_id': 'E4', 'type': 'refund_processed', 'transaction_id': 'T1', 'amount_paise': 1}, rules)
    assert acct['points_balance'] == 0
    assert acct['transactions']['T1']['refunded_paise'] == 100000
    assert len(acct['ledger']) == 3
    assert sum(entry['points_delta'] for entry in acct['ledger']) == acct['points_balance']


def test_missing_identifiers_and_duplicate_transaction_capture_ignored():
    rules = {'points_per_100_rupees': 1}
    acct = new_account('ACCT-1')
    acct = apply_reward_event(acct, {'type': 'purchase_captured', 'transaction_id': 'T1', 'amount_paise': 50000}, rules)
    acct = apply_reward_event(acct, {'event_id': 'E1', 'type': 'purchase_captured', 'amount_paise': 50000}, rules)
    assert acct['points_balance'] == 0
    assert acct['processed_event_ids'] == []

    acct = apply_reward_event(acct, {'event_id': 'E1', 'type': 'purchase_captured', 'transaction_id': 'T1', 'amount_paise': 50000}, rules)
    acct = apply_reward_event(acct, {'event_id': 'E2', 'type': 'purchase_captured', 'transaction_id': 'T1', 'amount_paise': 50000}, rules)
    assert acct['points_balance'] == 5
    assert len(acct['ledger']) == 1


def test_repeat_transactions_handles_empty_malformed_and_dataset():
    import json
    assert flag_repeat_transactions([], 2) == []
    assert flag_repeat_transactions(None, 2) == []
    dup_rows = [
        {'transaction_id': 'TX-1', 'account_id': 'A', 'date': '2026-10-01', 'amount_paise': 1000},
        {'transaction_id': 'TX-1', 'account_id': 'A', 'date': '2026-10-01', 'amount_paise': 1000},
        {'transaction_id': 'TX-2', 'account_id': 'A', 'date': '2026-10-01', 'amount_paise': 1000},
    ]
    assert flag_repeat_transactions(dup_rows, 2) == []

    with open('data/records.json', encoding='utf-8') as f:
        data = json.load(f)
    alerts = flag_repeat_transactions(data['transactions'], threshold=data['repeat_alert_threshold'])
    assert len(alerts) == 60
    acct = new_account('SYNTH')
    rules = data['rules_cases'][1]
    for ev in data['reward_events']:
        acct = apply_reward_event(acct, ev, rules)
    assert acct['points_balance'] >= 0
    assert sum(item['points_delta'] for item in acct['ledger']) == acct['points_balance']
