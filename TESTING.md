# TESTING.md - Required submission

Complete this file with test evidence from your own work. Include at least five edge cases. Do not claim a test passed unless you ran it.

## Test command and environment
- Python version: Python 3.14.5
- Command run: `python -m pytest -q`
- Actual test summary: `220 passed, 1 warning in 0.49s`

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | `amount_paise = 9999`, rate = 1 | Awards 0 points (floor below 100-rupee boundary) | 0 points awarded | `test_integer_floor_points_calculation[9999-0_0]` |
| 2 | `cap_points = 0`, amount = 50000 | Awards 0 points (cap of 0 is strictly respected) | 0 points awarded | `test_cap_zero_is_respected` |
| 3 | Replay event with existing `event_id` | Idempotent: balance unchanged, event ID recorded once | `points_balance == 2`, single ID in `processed_event_ids` | `test_purchase_event_replay_is_idempotent[PURCHASE-000]` |
| 4 | Refund `amount_paise = True` or `None` | Invalid types rejected without modifying transaction | `refunded_paise == 0`, balance unchanged | `test_invalid_or_excess_refund_does_not_change_account[True]` |
| 5 | Excess refund (`125000` paise on `100000` purchase) | Rejected; cumulative refund does not exceed purchase amount | `refunded_paise == 0`, `points_balance == 10` | `test_refund_amount_bounds_and_balance[125000]` |

## Regression tests added
List the defects fixed and the tests added to prevent them from returning:
1. `test_regression_invalid_type_amount`: Ensures `calculate_points(None, 1)` and `calculate_points('10000', 1)` return 0 points without throwing `TypeError`.
2. `test_regression_fractional_amount`: Ensures fractional amounts (`10000.5`) return 0 points.
3. `test_regression_negative_rule_values`: Ensures negative rates or bonus percentages (`-1`, `-10`) return 0 points.
4. `test_regression_missing_event_id`: Ensures events without an `event_id` are safely ignored.
5. `test_regression_missing_txn_id`: Ensures events without a `transaction_id` are safely ignored.
6. `test_regression_balance_never_negative`: Ensures that partial/full refunds never cause `points_balance` to drop below zero.

## Remaining failures or limitations
There are zero remaining failures. All 220 test cases pass cleanly.
