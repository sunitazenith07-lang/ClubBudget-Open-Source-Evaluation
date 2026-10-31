# Architecture Notes

## Project map
- `service.py`: Main logic for points calculation (`calculate_points`), event handling (`apply_reward_event`), and repeat alerts (`flag_repeat_transactions`).
- `models.py`: Helper to initialize an empty account dictionary (`new_account`).
- `main.py`: Demo script running sample calculations.
- `fixtures.py` & `data/`: Sample test data and records.
- `tests/`: Test suite containing `test_contract.py`, `test_acceptance_matrix.py`, and regression tests in `test_regression.py`.

## Data model
- Account dictionary:
  - `account_id`: String identifier for the customer account.
  - `points_balance`: Integer total points available (cannot drop below 0).
  - `processed_event_ids`: List of processed event ID strings to prevent duplicate processing.
  - `transactions`: Dictionary mapping `transaction_id` to its state:
    - `amount_paise`: Original purchase amount in paise.
    - `awarded_points`: Points earned from the purchase.
    - `reversed_points`: Cumulative points reversed by refunds.
    - `refunded_paise`: Cumulative paise refunded.
  - `ledger`: List of event entries tracking points deltas.

## Data flow
1. Event comes in with `event_id`, `type`, `transaction_id`, and `amount_paise`.
2. Check if `event_id` is already in `processed_event_ids`. If so, exit immediately and return the account.
3. If it's a `purchase_captured` event:
   - Calculate points using floor division per 100 rupees, add bonus %, and apply cap.
   - Record the transaction, update points balance, append to ledger, and record event ID.
4. If it's a `refund_processed` event:
   - Find transaction by ID.
   - Validate refund amount (must be positive integer, not exceeding remaining purchase amount).
   - Calculate proportional points to reverse, deduct from balance (flooring at 0), append to ledger, and record event ID.
5. If event is unrecognized, declined, or invalid, return the account unchanged.

## Storage design
All state is currently kept in-memory using standard Python dictionaries. Functions use `deepcopy` to return updated copies without mutating the input object.

## Diagram
```
[Reward Event]
      │
      ▼
[Already processed?] ── Yes ──> [Return unchanged account]
      │ No
      ▼
[Event Type]
   ├── purchase_captured ──> [Calculate points] ──> [Update account & ledger] ──> [Record event ID]
   └── refund_processed  ──> [Validate refund]  ──> [Reverse points]         ──> [Record event ID]
```

## Three improvements suggested
1. **Persistent database**: Store accounts and events in SQLite or PostgreSQL so state is saved across application restarts.
2. **Schema validation**: Use dataclasses or lightweight validation helpers to check event structure before passing them to `apply_reward_event`.
3. **Batch processing**: Add a helper function to process a list of events sequentially and return the final account state along with any rejected events.
