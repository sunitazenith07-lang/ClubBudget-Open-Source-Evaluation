# TESTING.md — Required submission

Complete this file with test evidence from your own work. Include at least five edge cases. Do not claim a test passed unless you ran it.

## Test command and environment
- Python version: Python 3.11+
- Command run: `python -m pytest -q`
- Actual test summary: `218 passed` (0 failed)

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | `amount_paise = 19999, per = 1`| Floors to 1 to complete ₹100 block (`1` point) | `1` | `test_points_use_floor` |
| 2 | `cap_points = 0` on `amount_paise = 50000`| Cap of zero yields `0` points | `0` | `test_cap_zero_is_respected` |
| 3 | Duplicate `event_id` replay on `purchase_captured` | Processed once; balance and ledger unchanged on replay | `points_balance == 2, len(ledger) == 1` | `test_purchase_event_once` |
| 4 | Excess refund (`150000` on `100000` purchase) or `True`/`None` | Ignored completely; `refunded_paise` stays `0` | `refunded_paise == 0, points_balance == 10` | `test_invalid_or_excess_refund_does_not_change_account` |
| 5 | Repeat alert with `count == threshold` vs `count == threshold + 1` | Returns `[]` at `threshold` and flags 1 group at `threshold + 1` | Matches expected boundary | `test_repeat_alert_threshold_boundaries` |

## Regression tests added
- `test_boolean_and_non_int_inputs_rejected`: Prevents `bool` values (`True`/`False`) from being accepted as `1`/`0` integer amounts or rule multipliers.
- `test_cumulative_partial_refunds_and_over_refund_rejected`: Verifies sequential partial refunds and ensures a subsequent refund exceeding the remaining unrefunded paise is rejected.
- `test_refund_event_replay_is_idempotent`: Verifies replaying the same `refund_processed` event ID does not deduct points twice.
- `test_repeat_transactions_skips_missing_fields`: Ensures rows with empty `transaction_id` are ignored when grouping repeats.

## Remaining failures or limitations
None. All 218 tests in `tests/test_contract.py` and `tests/test_acceptance_matrix.py` pass cleanly.