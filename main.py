from fixtures import sample_account, sample_rules, sample_transactions
from service import (
    apply_reward_event,
    calculate_points,
    flag_repeat_transactions,
    generate_account_statement_csv,
)

if __name__ == '__main__':
    rules = sample_rules()
    print('Points example:', calculate_points(259900, rules['points_per_100_rupees'], rules['bonus_percent'], rules['cap_points']))
    print('Repeat warnings:', flag_repeat_transactions(sample_transactions()))

    # Offline demo: apply purchase and partial refund events
    account = sample_account()
    purchase = {
        'event_id': 'EVT-001',
        'type': 'purchase_captured',
        'transaction_id': 'TX-1001',
        'amount_paise': 259900,
    }
    account = apply_reward_event(account, purchase, rules)
    refund = {
        'event_id': 'EVT-002',
        'type': 'refund_processed',
        'transaction_id': 'TX-1001',
        'amount_paise': 100000,
    }
    account = apply_reward_event(account, refund, rules)
    print('Account points balance after refund:', account['points_balance'])
    print('Statement CSV preview:\n' + generate_account_statement_csv(account).strip())

