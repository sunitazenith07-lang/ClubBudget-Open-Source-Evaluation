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
    out=apply_reward_event(new_account('A'),{'event_id':'E1','type':'purchase_declined','transaction_id':'T','amount_paise':100000},{'points_per_100_rupees':1}); assert out['points_balance']==0

def test_partial_refund_reverses_proportionally():
    rules={'points_per_100_rupees':1}; a=apply_reward_event(new_account('A'),{'event_id':'E1','type':'purchase_captured','transaction_id':'T1','amount_paise':100000},rules); b=apply_reward_event(a,{'event_id':'E2','type':'refund_processed','transaction_id':'T1','amount_paise':50000},rules); assert b['points_balance']==5

def test_invalid_or_excess_refund_ignored():
    rules={'points_per_100_rupees':1}; a=apply_reward_event(new_account('A'),{'event_id':'E1','type':'purchase_captured','transaction_id':'T','amount_paise':100000},rules)
    for amount in [-1,150000]:
        b=apply_reward_event(a,{'event_id':'E2','type':'refund_processed','transaction_id':'T','amount_paise':amount},rules); assert b['transactions']['T']['refunded_paise']==0 and b['points_balance']==10

def test_unknown_refund_safe(): assert apply_reward_event(new_account('A'),{'event_id':'E1','type':'refund_processed','transaction_id':'X','amount_paise':1000},{'points_per_100_rupees':1})['points_balance']==0

def test_repeat_group():
    rows=[{'transaction_id':str(i),'account_id':'A','date':'D','amount_paise':1000} for i in range(3)]; assert flag_repeat_transactions(rows,2)[0]['transaction_ids']==['0','1','2']

def test_different_accounts_not_grouped():
    rows=[{'transaction_id':'1','account_id':'A','date':'D','amount_paise':1000},{'transaction_id':'2','account_id':'B','date':'D','amount_paise':1000}]; assert flag_repeat_transactions(rows,1)==[]


# --- Added Regression Tests for Edge Cases ---

def test_refund_event_once():
    rules = {'points_per_100_rupees': 1}
    a = apply_reward_event(new_account('A'), {'event_id': 'E1', 'type': 'purchase_captured', 'transaction_id': 'T1', 'amount_paise': 100000}, rules)
    r = {'event_id': 'R1', 'type': 'refund_processed', 'transaction_id': 'T1', 'amount_paise': 50000}
    b = apply_reward_event(a, r, rules)
    c = apply_reward_event(b, r, rules)
    assert c['points_balance'] == 5
    assert c['processed_event_ids'] == ['E1', 'R1']


def test_multiple_partial_refunds_cannot_exceed_purchase():
    rules = {'points_per_100_rupees': 1}
    a = apply_reward_event(new_account('A'), {'event_id': 'E1', 'type': 'purchase_captured', 'transaction_id': 'T1', 'amount_paise': 100000}, rules)
    b = apply_reward_event(a, {'event_id': 'R1', 'type': 'refund_processed', 'transaction_id': 'T1', 'amount_paise': 60000}, rules)
    c = apply_reward_event(b, {'event_id': 'R2', 'type': 'refund_processed', 'transaction_id': 'T1', 'amount_paise': 50000}, rules)
    assert b['points_balance'] == 4
    assert c['points_balance'] == 4
    assert c['transactions']['T1']['refunded_paise'] == 60000


def test_duplicate_transaction_id_not_awarded_twice():
    rules = {'points_per_100_rupees': 1}
    a = apply_reward_event(new_account('A'), {'event_id': 'E1', 'type': 'purchase_captured', 'transaction_id': 'T1', 'amount_paise': 50000}, rules)
    b = apply_reward_event(a, {'event_id': 'E2', 'type': 'purchase_captured', 'transaction_id': 'T1', 'amount_paise': 50000}, rules)
    assert b['points_balance'] == 5
    assert len(b['ledger']) == 1


def test_missing_ids_and_empty_event_ignored():
    rules = {'points_per_100_rupees': 1}
    a = new_account('A')
    b = apply_reward_event(a, {}, rules)
    c = apply_reward_event(a, {'event_id': '', 'type': 'purchase_captured', 'transaction_id': 'T1', 'amount_paise': 50000}, rules)
    assert b['points_balance'] == 0
    assert c['points_balance'] == 0


def test_boolean_and_negative_rules_return_zero():
    assert calculate_points(True, 1) == 0
    assert calculate_points(100000, -1) == 0
    assert calculate_points(100000, 1, bonus_percent=-10) == 0
    assert calculate_points(100000, 1, cap_points=-5) == 0