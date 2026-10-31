# Architecture Notes

## Project map
- models.py: account factory (new_account).
- service.py: points calculation, reward event processing, refund handling, repeat-transaction alerts.
- fixtures.py: sample account, transactions, rules.
- main.py: demo entry point.
- tests/: contract and acceptance tests.

## Data model
- Account: account_id, points_balance, processed_event_ids, transactions, ledger.
- Transaction: amount_paise, awarded_points, reversed_points, refunded_paise.
- Ledger entry: event_id, type, points_delta.
- Repeat alert: account_id, date, amount_paise, transaction_ids.

## Data flow
1. Input event → apply_reward_event.
2. Idempotency check by event_id.
3. Purchase: calculate points → create transaction → update balance/ledger.
4. Refund: validate amount → update cumulative refund → proportional reversal → update balance/ledger.
5. Repeat alerts: group transactions by account/date/amount → compare count to threshold.

## Storage design
- In-memory Python dictionaries/lists; no persistent storage.
- Account state is copied with deepcopy to avoid mutation.

## Diagram

event -> idempotency check -> purchase/refund handler -> account state + ledger
transactions -> grouping by (account,date,amount) -> repeat alerts

## Three improvements suggested
1. Add schema validation for events and rules.
2. Add persistent storage or repository layer for account state.
3. Add property-based tests for cumulative refunds and idempotency.