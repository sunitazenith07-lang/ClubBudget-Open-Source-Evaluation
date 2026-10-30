# Project Notes

## Requirements completed
1. Fixed `calculate_points` to use integer floor division (`//`) for base and bonus points and apply `cap_points` last.
2. Handled invalid/negative amounts and rules (including `cap_points = 0` and booleans) so they return `0` points.
3. Awarded points only on `purchase_captured` events and ignored declined, pending, and unknown event types.
4. Enforced idempotency using `processed_event_ids` so replayed purchase or refund events are only applied once.
5. Implemented proportional point reversals on refunds using cumulative `refunded_paise`, capped at `awarded_points` and `points_balance`.
6. Added ledger entries (`event_id`, `type`, `points_delta`) for accepted purchase and refund events.
7. Updated `flag_repeat_transactions` to group valid captured transactions by `(account_id, date, amount_paise)` above `threshold`.
8. Added checks for empty inputs, `None`, missing IDs, unknown transactions, and duplicate `transaction_id`s.

## Files changed
- `service.py`: Updated `calculate_points`, `apply_reward_event`, and `flag_repeat_transactions`, and added `_is_strict_int`.
- `tests/test_contract.py`: Added 4 regression tests for non-int/boolean inputs, cumulative partial refunds + duplicate event replay + excess refund rejection, missing IDs, and `data/records.json`.
- `approach.md`, `challenges.md`, `optimizations.md`, `TESTING.md`, `REWARD_RULE_NOTES.md`: Completed required submission notes.

## Decisions and assumptions
- Excluded `bool` in `_is_strict_int` because `isinstance(True, int)` is `True` in Python.
- Used cumulative `refunded_paise` when computing refund reversals so multiple partial refunds summing to 100% reverse all awarded points.
- Kept `deepcopy(account)` in `apply_reward_event` so the caller's input dict is never mutated.

## Tests and results
- Initial baseline: `py -m pytest -q` -> `67 failed, 147 passed in 0.51s`
- Final test run: `py -m pytest -q` -> `218 passed in 0.17s`
- Demo output: `py -m main` -> `Points example: 27` and `Repeat warnings: []`

## Limitations and next steps
- Account state is stored in memory in dicts and lists, and `processed_event_ids` uses a list to match the test contract.
