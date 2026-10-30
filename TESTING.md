# TESTING.md — Required submission

Complete this file with test evidence from your own work. Include at least five edge cases. Do not claim a test passed unless you ran it.

## Test command and environment
- Python version: Python 3.14.5 (win32)
- Command run: `pytest` / `python -m pytest -q`
- Actual test summary: `222 passed, 1 warning in 0.33s` (214 baseline tests + 8 regression tests)

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | `amount_paise = 9999`, `points_per_100_rupees = 1` | 0 points awarded (integer floor division `9999 // 10000 = 0`, not rounded to 1) | `0` | `test_integer_floor_points_calculation[9999-0_0]` & `test_regression_floor_boundary_values` |
| 2 | `cap_points = 0`, `amount_paise = 50000`, `points_per_100_rupees = 1` | 0 points awarded (cap of zero is respected, not skipped as falsy) | `0` | `test_cap_zero_is_respected` & `test_regression_cap_zero_not_falsy` |
| 3 | Replay same event `event_id = "PURCHASE-000"` multiple times | Exactly 1 entry in `processed_event_ids`, 1 entry in `ledger`, and unchanged `points_balance` | Balance = 2, `processed_event_ids = ['PURCHASE-000']`, ledger len = 1 | `test_purchase_event_replay_is_idempotent[PURCHASE-000]` & `test_regression_event_replay_idempotency_no_list_duplication` |
| 4 | Excess refund `amount_paise = 150000` on a `100000` purchase | Refund rejected, account remains unchanged (`refunded_paise = 0`, `points_balance = 10`) | `refunded_paise = 0`, `points_balance = 10` | `test_invalid_or_excess_refund_does_not_change_account[150000]` & `test_regression_cumulative_partial_refunds_and_excess_rejection` |
| 5 | Boolean input `amount_paise = True` or `amount_paise = False` | Treated as invalid type (not coerced to integer `1` or `0`), awards 0 points or rejected refund | 0 points awarded, no refund processed | `test_invalid_or_excess_refund_does_not_change_account[True]` & `test_regression_boolean_inputs_not_treated_as_integers` |
| 6 | Refund reversal exceeding current account balance (e.g. balance = 2, refund reversal = 10) | Balance clamped to 0, never negative; delta recorded as -2 | `points_balance = 0`, `points_delta = -2` | `test_regression_refund_cannot_make_balance_negative` |

## Regression tests added
List the defects fixed and the tests added to prevent them from returning:
1. Fixed boundary rounding defect in `calculate_points`:
   - Added `test_regression_floor_boundary_values` to verify floor division on 9999, 19999, 29999 paise.
2. Fixed falsy evaluation of `cap_points = 0`:
   - Added `test_regression_cap_zero_not_falsy` to verify that `cap_points = 0` produces 0 points.
3. Fixed event replay list duplication and audit log pollution:
   - Added `test_regression_event_replay_idempotency_no_list_duplication` to verify that repeated calls with the same `event_id` do not append duplicates to `processed_event_ids` or `ledger`.
4. Fixed duplicate refund point reversal:
   - Added `test_regression_refund_event_replay_idempotency` to verify that replaying refund events does not reverse points a second time.
5. Fixed acceptance of excess and cumulative excess refunds:
   - Added `test_regression_cumulative_partial_refunds_and_excess_rejection` to verify multi-step partial refunds and rejection of cumulative over-refunds.
6. Fixed negative points balance on refund reversal:
   - Added `test_regression_refund_cannot_make_balance_negative` to verify that reversal deltas cannot drive account point balances below zero.
7. Fixed Python boolean type coercion:
   - Added `test_regression_boolean_inputs_not_treated_as_integers` to prevent `bool` values from being evaluated as integers.
8. Fixed repeat transaction alert crash on null/malformed entries:
   - Added `test_regression_flag_repeats_safe_with_none_or_malformed` to ensure stability when given `None`, empty lists, or malformed records.

## Remaining failures or limitations
- Remaining failing tests: 0 (all 222 tests pass).
- Known limitations: In-memory dictionary state is not persistent across process restarts without an external backing database or event store.
