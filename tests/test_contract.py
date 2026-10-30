from copy import deepcopy

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


def test_purchase_missing_amount_is_rejected_without_financial_mutation():
    account=new_account('A')
    result=apply_reward_event(account,{'event_id':'E1','type':'purchase_captured','transaction_id':'T'},{'points_per_100_rupees':1})
    assert result['points_balance']==account['points_balance']
    assert result['transactions']==account['transactions']
    assert result['ledger']==account['ledger']
    assert result['processed_event_ids']==['E1']


def test_purchase_none_amount_is_rejected_without_financial_mutation():
    account=new_account('A')
    result=apply_reward_event(account,{'event_id':'E1','type':'purchase_captured','transaction_id':'T','amount_paise':None},{'points_per_100_rupees':1})
    assert result['points_balance']==account['points_balance']
    assert result['transactions']==account['transactions']
    assert result['ledger']==account['ledger']
    assert result['processed_event_ids']==['E1']


def test_purchase_non_integer_amount_is_rejected_without_financial_mutation():
    account=new_account('A')
    result=apply_reward_event(account,{'event_id':'E1','type':'purchase_captured','transaction_id':'T','amount_paise':'25000'},{'points_per_100_rupees':1})
    assert result['points_balance']==account['points_balance']
    assert result['transactions']==account['transactions']
    assert result['ledger']==account['ledger']
    assert result['processed_event_ids']==['E1']


def test_purchase_zero_amount_remains_accepted():
    result=apply_reward_event(new_account('A'),{'event_id':'E1','type':'purchase_captured','transaction_id':'T','amount_paise':0},{'points_per_100_rupees':1})
    assert result['points_balance']==0
    assert result['transactions']['T']['amount_paise']==0
    assert len(result['ledger'])==1


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


def test_multiple_partial_refunds_use_incremental_cumulative_reversals():
    rules={'points_per_100_rupees':1}
    account=apply_reward_event(new_account('A'),{'event_id':'P','type':'purchase_captured','transaction_id':'T','amount_paise':100000},rules)
    for event_id, amount, expected_delta in [('R1',25000,-2),('R2',25000,-3),('R3',50000,-5)]:
        updated=apply_reward_event(account,{'event_id':event_id,'type':'refund_processed','transaction_id':'T','amount_paise':amount},rules)
        assert updated['ledger'][-1]['points_delta']==expected_delta
        account=updated
    assert account['transactions']['T']['refunded_paise']==100000
    assert account['transactions']['T']['reversed_points']==10
    assert account['points_balance']==0


def test_partial_refund_rounding_is_cumulative_and_bounded():
    rules={'points_per_100_rupees':1}
    account=apply_reward_event(new_account('A'),{'event_id':'P','type':'purchase_captured','transaction_id':'T','amount_paise':100000},rules)
    account=apply_reward_event(account,{'event_id':'R1','type':'refund_processed','transaction_id':'T','amount_paise':33333},rules)
    account=apply_reward_event(account,{'event_id':'R2','type':'refund_processed','transaction_id':'T','amount_paise':33333},rules)
    assert account['transactions']['T']['reversed_points']==6
    assert account['transactions']['T']['reversed_points']<=account['transactions']['T']['awarded_points']


def test_refund_replay_does_not_change_account_or_ledger():
    rules={'points_per_100_rupees':1}
    account=apply_reward_event(new_account('A'),{'event_id':'P','type':'purchase_captured','transaction_id':'T','amount_paise':100000},rules)
    once=apply_reward_event(account,{'event_id':'R','type':'refund_processed','transaction_id':'T','amount_paise':50000},rules)
    twice=apply_reward_event(once,{'event_id':'R','type':'refund_processed','transaction_id':'T','amount_paise':50000},rules)
    assert twice==once


def test_each_accepted_refund_has_consistent_single_ledger_entry():
    rules={'points_per_100_rupees':1}
    account=apply_reward_event(new_account('A'),{'event_id':'P','type':'purchase_captured','transaction_id':'T','amount_paise':100000},rules)
    previous_balance=account['points_balance']
    for event_id, amount in [('R1',25000),('R2',25000)]:
        before_ledger=len(account['ledger'])
        updated=apply_reward_event(account,{'event_id':event_id,'type':'refund_processed','transaction_id':'T','amount_paise':amount},rules)
        assert len(updated['ledger'])==before_ledger+1
        assert updated['ledger'][-1]['points_delta']==updated['points_balance']-previous_balance
        previous_balance=updated['points_balance']
        account=updated


def test_refund_order_preserves_cumulative_total_reversal():
    rules={'points_per_100_rupees':1}
    account=apply_reward_event(new_account('A'),{'event_id':'P','type':'purchase_captured','transaction_id':'T','amount_paise':100000},rules)
    for event_id, amount in [('R1',10000),('R2',40000)]:
        account=apply_reward_event(account,{'event_id':event_id,'type':'refund_processed','transaction_id':'T','amount_paise':amount},rules)
    assert account['transactions']['T']['refunded_paise']==50000
    assert account['transactions']['T']['reversed_points']==5
    assert account['points_balance']==5


def test_multiple_refunds_do_not_mutate_input_account():
    rules={'points_per_100_rupees':1}
    original=apply_reward_event(new_account('A'),{'event_id':'P','type':'purchase_captured','transaction_id':'T','amount_paise':100000},rules)
    snapshot=deepcopy(original)
    updated=apply_reward_event(original,{'event_id':'R1','type':'refund_processed','transaction_id':'T','amount_paise':25000},rules)
    apply_reward_event(updated,{'event_id':'R2','type':'refund_processed','transaction_id':'T','amount_paise':25000},rules)
    assert original==snapshot


def test_excessive_refund_leaves_financial_state_and_ledger_unchanged():
    rules={'points_per_100_rupees':1}
    account=apply_reward_event(new_account('A'),{'event_id':'P','type':'purchase_captured','transaction_id':'T','amount_paise':100000},rules)
    before_transaction=deepcopy(account['transactions']['T'])
    before_balance=account['points_balance']
    before_ledger=deepcopy(account['ledger'])
    rejected=apply_reward_event(account,{'event_id':'R','type':'refund_processed','transaction_id':'T','amount_paise':100001},rules)
    assert rejected['points_balance']==before_balance
    assert rejected['transactions']['T']==before_transaction
    assert rejected['ledger']==before_ledger
