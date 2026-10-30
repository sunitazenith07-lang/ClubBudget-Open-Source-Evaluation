import json
from pathlib import Path
import pytest
from models import new_account
from service import calculate_points, apply_reward_event, flag_repeat_transactions, generate_account_statement_csv


def test_sequential_partial_refunds_no_rounding_drift():
    """Verify that multiple partial refunds summing to 100% reverse exactly 100% of awarded points."""
    rules = {'points_per_100_rupees': 1, 'bonus_percent': 50}
    # Amount: Rs 1000 (100,000 paise) -> Base: 10, Bonus 50% -> 15 points awarded
    account = new_account('ACCT-SEQ')
    purchase_event = {
        'event_id': 'E-PURCHASE-1',
        'type': 'purchase_captured',
        'transaction_id': 'TX-SEQ',
        'amount_paise': 100000
    }
    account = apply_reward_event(account, purchase_event, rules)
    assert account['points_balance'] == 15
    assert account['transactions']['TX-SEQ']['awarded_points'] == 15

    # Refund 1: 50% (50,000 paise) -> 15 * 50000 // 100000 = 7 points reversed
    refund_1 = {
        'event_id': 'E-REFUND-1',
        'type': 'refund_processed',
        'transaction_id': 'TX-SEQ',
        'amount_paise': 50000
    }
    account = apply_reward_event(account, refund_1, rules)
    assert account['points_balance'] == 8
    assert account['transactions']['TX-SEQ']['reversed_points'] == 7
    assert account['transactions']['TX-SEQ']['refunded_paise'] == 50000

    # Refund 2: remaining 50% (50,000 paise) -> cumulative 100% -> should reverse total 15 points
    refund_2 = {
        'event_id': 'E-REFUND-2',
        'type': 'refund_processed',
        'transaction_id': 'TX-SEQ',
        'amount_paise': 50000
    }
    account = apply_reward_event(account, refund_2, rules)
    assert account['points_balance'] == 0
    assert account['transactions']['TX-SEQ']['reversed_points'] == 15
    assert account['transactions']['TX-SEQ']['refunded_paise'] == 100000

    # Exactly 3 ledger entries: 1 purchase (+15), 2 refunds (-7, -8)
    assert len(account['ledger']) == 3
    assert account['ledger'][0]['points_delta'] == 15
    assert account['ledger'][1]['points_delta'] == -7
    assert account['ledger'][2]['points_delta'] == -8


def test_refund_replay_is_idempotent():
    """Verify that replaying a refund event does not reverse points twice or duplicate ledger entries."""
    rules = {'points_per_100_rupees': 1}
    account = new_account('ACCT-IDEMP')
    account = apply_reward_event(account, {
        'event_id': 'E-BUY',
        'type': 'purchase_captured',
        'transaction_id': 'TX-1',
        'amount_paise': 100000
    }, rules)
    assert account['points_balance'] == 10

    refund_event = {
        'event_id': 'E-REF',
        'type': 'refund_processed',
        'transaction_id': 'TX-1',
        'amount_paise': 40000
    }
    after_first_refund = apply_reward_event(account, refund_event, rules)
    assert after_first_refund['points_balance'] == 6
    assert len(after_first_refund['ledger']) == 2
    assert after_first_refund['processed_event_ids'] == ['E-BUY', 'E-REF']

    # Replay same refund event
    after_replay = apply_reward_event(after_first_refund, refund_event, rules)
    assert after_replay['points_balance'] == 6
    assert after_replay['transactions']['TX-1']['refunded_paise'] == 40000
    assert after_replay['transactions']['TX-1']['reversed_points'] == 4
    assert len(after_replay['ledger']) == 2
    assert after_replay['processed_event_ids'] == ['E-BUY', 'E-REF']


def test_points_balance_never_negative():
    """Verify points balance is never allowed to become negative even under edge reversal conditions."""
    rules = {'points_per_100_rupees': 1}
    account = new_account('ACCT-NONEG')
    # Manually simulate balance lower than awarded points
    account['points_balance'] = 2
    account['transactions']['TX-Z'] = {
        'amount_paise': 100000,
        'awarded_points': 10,
        'reversed_points': 0,
        'refunded_paise': 0
    }
    # Refund would normally reverse 10 points, but available balance is only 2
    refund_event = {
        'event_id': 'E-REF-MAX',
        'type': 'refund_processed',
        'transaction_id': 'TX-Z',
        'amount_paise': 100000
    }
    result = apply_reward_event(account, refund_event, rules)
    assert result['points_balance'] == 0
    assert result['ledger'][-1]['points_delta'] == -2


def test_cumulative_excess_refund_rejected():
    """Verify that after a valid partial refund, a subsequent refund exceeding total purchase amount is rejected."""
    rules = {'points_per_100_rupees': 1}
    account = new_account('ACCT-OVER')
    account = apply_reward_event(account, {
        'event_id': 'E-BUY',
        'type': 'purchase_captured',
        'transaction_id': 'TX-OVER',
        'amount_paise': 100000
    }, rules)

    # Valid refund of 60,000 paise
    account = apply_reward_event(account, {
        'event_id': 'E-REF1',
        'type': 'refund_processed',
        'transaction_id': 'TX-OVER',
        'amount_paise': 60000
    }, rules)
    assert account['points_balance'] == 4
    assert account['transactions']['TX-OVER']['refunded_paise'] == 60000

    # Attempting refund of 50,000 paise (60000 + 50000 = 110000 > 100000)
    rejected_account = apply_reward_event(account, {
        'event_id': 'E-REF2',
        'type': 'refund_processed',
        'transaction_id': 'TX-OVER',
        'amount_paise': 50000
    }, rules)
    assert rejected_account['points_balance'] == 4
    assert rejected_account['transactions']['TX-OVER']['refunded_paise'] == 60000
    assert len(rejected_account['ledger']) == 2
    assert 'E-REF2' not in rejected_account['processed_event_ids']


def test_malformed_event_fields_safe_handling():
    """Verify missing identifiers and invalid types in events are safely handled without throwing exceptions."""
    rules = {'points_per_100_rupees': 1}
    account = new_account('ACCT-MAL')

    # Missing event_id
    res1 = apply_reward_event(account, {'type': 'purchase_captured', 'transaction_id': 'TX-1', 'amount_paise': 100000}, rules)
    assert res1['points_balance'] == 0

    # Missing transaction_id
    res2 = apply_reward_event(account, {'event_id': 'E-1', 'type': 'purchase_captured', 'amount_paise': 100000}, rules)
    assert res2['points_balance'] == 0

    # Boolean amount_paise (in Python bool is subclass of int)
    res3 = apply_reward_event(account, {'event_id': 'E-2', 'type': 'purchase_captured', 'transaction_id': 'TX-2', 'amount_paise': True}, rules)
    assert res3['points_balance'] == 0

    # String amount_paise
    res4 = apply_reward_event(account, {'event_id': 'E-3', 'type': 'purchase_captured', 'transaction_id': 'TX-3', 'amount_paise': '50000'}, rules)
    assert res4['points_balance'] == 0

    # None and empty rules
    res5 = apply_reward_event(account, {'event_id': 'E-4', 'type': 'purchase_captured', 'transaction_id': 'TX-4', 'amount_paise': 50000}, None)
    assert res5['points_balance'] == 5


def test_full_synthetic_dataset_integration():
    """Process all events from data/records.json and verify data invariants across all accounts."""
    records_file = Path('data/records.json')
    if not records_file.exists():
        pytest.skip('data/records.json not found')

    with open(records_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. Verify repeat transaction flagging on synthetic dataset
    threshold = data.get('repeat_alert_threshold', 2)
    alerts = flag_repeat_transactions(data['transactions'], threshold=threshold)
    assert isinstance(alerts, list)
    assert len(alerts) > 0
    for alert in alerts:
        assert len(alert['transaction_ids']) > threshold
        assert 'account_id' in alert
        assert 'date' in alert
        assert 'amount_paise' in alert

    # 2. Verify account processing with reward events
    accounts = {acc['account_id']: new_account(acc['account_id']) for acc in data['accounts']}
    rule = {'points_per_100_rupees': 1, 'bonus_percent': 10, 'cap_points': 500}

    for event in data['reward_events']:
        acc_id = event.get('account_id')
        if acc_id in accounts:
            accounts[acc_id] = apply_reward_event(accounts[acc_id], event, rule)

    # Verify invariants on all accounts
    for acc_id, acc in accounts.items():
        assert acc['points_balance'] >= 0, f"Account {acc_id} has negative points balance"
        # Ledger sum must equal points_balance
        ledger_sum = sum(entry['points_delta'] for entry in acc['ledger'])
        assert ledger_sum == acc['points_balance'], f"Ledger mismatch for {acc_id}: {ledger_sum} vs {acc['points_balance']}"
        # Processed event ids count must equal ledger length
        assert len(acc['processed_event_ids']) == len(acc['ledger'])


def test_generate_account_statement_csv():
    """Verify the optional stretch feature for CSV statement generation."""
    rules = {'points_per_100_rupees': 1}
    account = new_account('ACCT-CSV')
    account = apply_reward_event(account, {
        'event_id': 'EV-101',
        'type': 'purchase_captured',
        'transaction_id': 'TX-101',
        'amount_paise': 200000
    }, rules)
    account = apply_reward_event(account, {
        'event_id': 'EV-102',
        'type': 'refund_processed',
        'transaction_id': 'TX-101',
        'amount_paise': 50000
    }, rules)

    csv_output = generate_account_statement_csv(account)
    lines = csv_output.strip().split('\n')
    assert lines[0] == 'event_id,type,points_delta,balance'
    assert lines[1] == 'EV-101,purchase_captured,20,20'
    assert lines[2] == 'EV-102,refund_processed,-5,15'
