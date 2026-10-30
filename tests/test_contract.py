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

import pytest


@pytest.mark.parametrize("amount", [None, "10000", 1.5, True, [], {}])
def test_invalid_purchase_amount_returns_zero(amount):
    assert calculate_points(amount, 1) == 0


@pytest.mark.parametrize("per", [-1, None, "1", 1.5, True])
def test_invalid_points_multiplier_returns_zero(per):
    assert calculate_points(100000, per) == 0


@pytest.mark.parametrize("bonus", [-1, None, "10", 1.5, True])
def test_invalid_bonus_returns_zero(bonus):
    assert calculate_points(100000, 1, bonus) == 0


@pytest.mark.parametrize("cap", [-1, "10", 1.5, True])
def test_invalid_cap_returns_zero(cap):
    assert calculate_points(100000, 1, cap_points=cap) == 0

@pytest.mark.parametrize("event_id", [None, "", 123, True])
def test_invalid_purchase_event_id_does_not_award(event_id):
    account = new_account("A")
    event = {
        "event_id": event_id,
        "type": "purchase_captured",
        "transaction_id": "T1",
        "amount_paise": 100000
    }

    result = apply_reward_event(
        account, event, {"points_per_100_rupees": 1}
    )

    assert result["points_balance"] == 0
    assert result["transactions"] == {}
    assert result["ledger"] == []


@pytest.mark.parametrize("txn_id", [None, "", 123, True])
def test_invalid_purchase_transaction_id_does_not_award(txn_id):
    account = new_account("A")
    event = {
        "event_id": "E1",
        "type": "purchase_captured",
        "transaction_id": txn_id,
        "amount_paise": 100000
    }

    result = apply_reward_event(
        account, event, {"points_per_100_rupees": 1}
    )

    assert result["points_balance"] == 0
    assert result["transactions"] == {}
    assert result["ledger"] == []

def test_refund_does_not_make_balance_negative():
    account = new_account("A")

    account["transactions"]["T1"] = {
        "amount_paise": 10000,
        "awarded_points": 1,
        "reversed_points": 0,
        "refunded_paise": 0
    }

    account["points_balance"] = 0

    event = {
        "event_id": "E1",
        "type": "refund_processed",
        "transaction_id": "T1",
        "amount_paise": 10000
    }

    result = apply_reward_event(
        account, event, {"points_per_100_rupees": 1}
    )

    assert result["points_balance"] >= 0

def test_repeat_alert_empty_input():
    assert flag_repeat_transactions([]) == []


def test_repeat_alert_does_not_flag_single_transaction():
    transactions = [
        {
            "transaction_id": "T1",
            "account_id": "A",
            "date": "2026-10-30",
            "amount_paise": 10000
        }
    ]

    assert flag_repeat_transactions(transactions) == []

def test_repeat_alert_handles_missing_fields():
    transactions = [
        {"transaction_id": "T1"},
        {"transaction_id": "T2"},
        {}
    ]

    assert flag_repeat_transactions(transactions) == []


def test_repeat_alert_ignores_non_dictionary_records():
    transactions = [
        None,
        "invalid",
        123
    ]

    assert flag_repeat_transactions(transactions) == []