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


def test_duplicate_refund_event_is_ignored():
    rules = {'points_per_100_rupees': 1}
    account = new_account('A')

    purchase = {
        'event_id': 'E1',
        'type': 'purchase_captured',
        'transaction_id': 'T1',
        'amount_paise': 100000
    }
    refund = {
        'event_id': 'E2',
        'type': 'refund_processed',
        'transaction_id': 'T1',
        'amount_paise': 50000
    }

    account = apply_reward_event(account, purchase, rules)
    account = apply_reward_event(account, refund, rules)
    account = apply_reward_event(account, refund, rules)

    assert account['points_balance'] == 5
    assert account['transactions']['T1']['refunded_paise'] == 50000
    assert account['transactions']['T1']['reversed_points'] == 5
    assert len(account['ledger']) == 2


def test_purchase_with_blank_transaction_id_is_ignored():
    event = {
        'event_id': 'E1',
        'type': 'purchase_captured',
        'transaction_id': ' ',
        'amount_paise': 50000
    }

    account = apply_reward_event(
        new_account('A'), event, {'points_per_100_rupees': 1}
    )

    assert account['points_balance'] == 0
    assert account['transactions'] == {}
    assert account['ledger'] == []


def test_purchase_with_boolean_amount_is_ignored():
    event = {
        'event_id': 'E1',
        'type': 'purchase_captured',
        'transaction_id': 'T1',
        'amount_paise': True
    }

    account = apply_reward_event(
        new_account('A'), event, {'points_per_100_rupees': 1}
    )

    assert account['points_balance'] == 0
    assert account['transactions'] == {}
    assert account['ledger'] == []


def test_invalid_repeat_threshold_returns_no_alerts():
    transactions = [
        {
            'transaction_id': str(i),
            'account_id': 'A',
            'date': '2026-10-30',
            'amount_paise': 10000
        }
        for i in range(3)
    ]

    assert flag_repeat_transactions(transactions, threshold=-1) == []
