import pytest
from copy import deepcopy
from models import new_account
from service import calculate_points, apply_reward_event, flag_repeat_transactions


@pytest.mark.parametrize("amount,expected", [
    (0,0),(1,0),(9999,0),(10000,1),(19999,1),(20000,2),
    (29999,2),(30000,3),(49999,4),(50000,5),(99999,9),(100000,10),
    (100001,10),(109999,10),(110000,11),(199999,19),(200000,20),
    (249999,24),(250000,25),(999999,99),(1000000,100),
    (12345,1),(19998,1),(20001,2),(9999,0),
])
def test_integer_floor_points_calculation(amount, expected):
    assert calculate_points(amount, 1) == expected


@pytest.mark.parametrize("amount,per,bonus,cap,expected", [
    (10000,1,0,None,1),(10000,2,0,None,2),(50000,2,0,None,10),
    (50000,2,10,None,11),(50000,2,50,None,15),(50000,2,100,None,20),
    (50000,2,50,6,6),(50000,2,50,0,0),(50000,2,50,20,15),
    (25000,3,33,None,7),(25000,3,34,None,8),(99000,1,10,None,9),
    (99000,1,0,4,4),(9999,99,99,None,0),(10000,0,100,None,0),
    (50000,1,0,1,1),(50000,1,0,2,2),(30000,1,25,None,3),
    (30000,1,50,None,4),(30000,1,99,None,5),
])
def test_bonus_and_cap_matrix(amount, per, bonus, cap, expected):
    assert calculate_points(amount, per, bonus, cap) == expected


@pytest.mark.parametrize("amount", [-1,-10,-100,-9999,-10000,-100000,0])
def test_invalid_purchase_amount_awards_zero_points(amount):
    assert calculate_points(amount, 1) == 0


@pytest.mark.parametrize("rules", [
    (-1,0,None),(1,-1,None),(1,0,-1),(1,0,-5),(0,0,0),
    (0,10,100),(1,0,0),(5,0,1),(100,0,0),(1,1,1),
])
def test_invalid_rule_values_do_not_create_negative_points(rules):
    per,bonus,cap = rules
    assert calculate_points(100000, per, bonus, cap) >= 0


@pytest.mark.parametrize("event_id", [f"PURCHASE-{i:03}" for i in range(20)])
def test_purchase_event_replay_is_idempotent(event_id):
    account = new_account("A")
    event = {"event_id":event_id,"type":"purchase_captured","transaction_id":"T","amount_paise":25000}
    rules = {"points_per_100_rupees":1}
    once = apply_reward_event(account, event, rules)
    twice = apply_reward_event(once, event, rules)
    assert twice["points_balance"] == 2
    assert twice["processed_event_ids"] == [event_id]
    assert len(twice["ledger"]) == 1


@pytest.mark.parametrize("amount", [1,9999,10000,19999,50000,99999,100000,125000,199999,200000,250000,500000,1000000,10000000,100,1000,1000001,987654,333333,777777])
def test_capture_purchase_records_consistent_transaction(amount):
    account = new_account("A")
    result = apply_reward_event(account, {"event_id":"E1","type":"purchase_captured","transaction_id":"T","amount_paise":amount}, {"points_per_100_rupees":1})
    assert result["transactions"]["T"]["amount_paise"] == amount
    assert result["transactions"]["T"]["awarded_points"] == amount // 10000
    assert result["points_balance"] == amount // 10000


@pytest.mark.parametrize("amount", [1,100,9999,10000,25000,49999,50000,75000,99999,100000,125000,150000,175000,200000,250000,300000,500000,750000,1000000,10000000])
def test_refund_amount_bounds_and_balance(amount):
    rules = {"points_per_100_rupees":1}
    account = apply_reward_event(new_account("A"), {"event_id":"P","type":"purchase_captured","transaction_id":"T","amount_paise":100000}, rules)
    result = apply_reward_event(account, {"event_id":"R","type":"refund_processed","transaction_id":"T","amount_paise":amount}, rules)
    if amount <= 100000:
        assert result["transactions"]["T"]["refunded_paise"] == amount
        assert result["points_balance"] >= 0
    else:
        assert result["transactions"]["T"]["refunded_paise"] == 0
        assert result["points_balance"] == 10


@pytest.mark.parametrize("amount", [0,-1,-50,-1000,100001,150000,200000,999999,True,None,"100",1.5,[],{},False])
def test_invalid_or_excess_refund_does_not_change_account(amount):
    rules = {"points_per_100_rupees":1}
    account = apply_reward_event(new_account("A"), {"event_id":"P","type":"purchase_captured","transaction_id":"T","amount_paise":100000}, rules)
    result = apply_reward_event(account, {"event_id":"R","type":"refund_processed","transaction_id":"T","amount_paise":amount}, rules)
    assert result["transactions"]["T"]["refunded_paise"] == 0
    assert result["points_balance"] == 10


@pytest.mark.parametrize("count", range(1,21))
def test_repeat_alert_respects_threshold(count):
    rows = [{"transaction_id":str(i),"account_id":"A","date":"D","amount_paise":1000} for i in range(count)]
    result = flag_repeat_transactions(rows, threshold=2)
    assert bool(result) == (count > 2)
    if result:
        assert len(result[0]["transaction_ids"]) == count


@pytest.mark.parametrize("threshold", [1,2,3,4,5,10,20,50,100,1000])
def test_repeat_alert_threshold_boundaries(threshold):
    rows = [{"transaction_id":str(i),"account_id":"A","date":"D","amount_paise":5000} for i in range(threshold)]
    assert flag_repeat_transactions(rows, threshold=threshold) == []
    rows.append({"transaction_id":"NEXT","account_id":"A","date":"D","amount_paise":5000})
    assert len(flag_repeat_transactions(rows, threshold=threshold)) == 1


@pytest.mark.parametrize("account_id,date,amount", [
    ("A","D1",100),("A","D2",100),("B","D1",100),("A","D1",200),
    ("B","D2",200),("C","D3",300),("A","2026-01-01",999),(None,"D",100),
    ("A",None,100),("A","D",None),("A","D",0),("A","D",-1),
    ("X","D",12345),("Y","D",12345),("X","E",12345),
])
def test_repeat_alerts_do_not_mix_distinct_keys(account_id, date, amount):
    rows = [
        {"transaction_id":"1","account_id":"A","date":"D","amount_paise":1000},
        {"transaction_id":"2","account_id":"A","date":"D","amount_paise":1000},
        {"transaction_id":"3","account_id":account_id,"date":date,"amount_paise":amount},
    ]
    result = flag_repeat_transactions(rows, threshold=2)
    if (account_id,date,amount) == ("A","D",1000):
        assert len(result) == 1
    else:
        assert result == []


@pytest.mark.parametrize("kind", ["purchase_declined","purchase_pending","unknown","refund","",None,1,"PURCHASE_CAPTURED"])
def test_unrecognized_or_declined_events_do_not_award_points(kind):
    account = new_account("A")
    result = apply_reward_event(account, {"event_id":"E","type":kind,"transaction_id":"T","amount_paise":100000}, {"points_per_100_rupees":1})
    assert result["points_balance"] == 0
    assert result["transactions"] == {}


@pytest.mark.parametrize("amount", [10000,20000,50000,100000,250000,1000000])
def test_event_processing_does_not_mutate_input_account(amount):
    account = new_account("A")
    before = deepcopy(account)
    apply_reward_event(account, {"event_id":"E","type":"purchase_captured","transaction_id":"T","amount_paise":amount}, {"points_per_100_rupees":1})
    assert account == before


@pytest.mark.parametrize("threshold", [0,-1,-5,1,2,3])
def test_repeat_alert_threshold_input_is_handled(threshold):
    rows = [{"transaction_id":str(i),"account_id":"A","date":"D","amount_paise":1000} for i in range(4)]
    result = flag_repeat_transactions(rows, threshold)
    assert isinstance(result, list)
