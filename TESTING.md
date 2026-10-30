# TESTING.md — Required submission

Complete this file with test evidence from your own work. Include at least five edge cases. Do not claim a test passed unless you ran it.

## Test command and environment
- **Python version:** Python 3.13.15 (Windows)
- **Command run:** `python -m pytest -q`
- **Actual test summary:** `223 passed in 0.20s`

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | `amount_paise = 19999`, `points_per_100_rupees = 1` | Floor division at 10,000 paise (100 INR): 19,999 paise awards 1 point, NOT 2 points from rounding. | `1` | `tests/test_regression_and_edge_cases.py::test_paise_boundary_floor_arithmetic` |
| 2 | `amount_paise = 50000`, `points_per_100_rupees = 2`, `bonus_percent = 50`, `cap_points = 0` | Cap of 0 must strictly override calculated bonus points (15) and return 0 points. | `0` | `tests/test_acceptance_matrix.py::test_bonus_and_cap_matrix[50000-2-50-0-0]` |
| 3 | Cumulative partial refunds: 100,000 paise purchase (10 points awarded) refunded in three parts: 33,333 paise, 33,333 paise, and 33,334 paise. | Proportional reversals must reverse 3 points, then 3 points, then 4 points, totaling exactly 10 points reversed with 0 drift and final balance 0. | Final points balance: `0`, total reversed: `10` | `tests/test_regression_and_edge_cases.py::test_multi_step_partial_refund_no_rounding_drift` |
| 4 | Attempted excess refund: 100,000 paise purchase with 60,000 paise already refunded; second refund of 50,000 paise attempted. | Excess refund exceeds total transaction amount (60k + 50k = 110k > 100k); event must be ignored without altering state. | Refund ignored; `refunded_paise` stays at `60000`, balance remains unchanged | `tests/test_regression_and_edge_cases.py::test_cumulative_excess_refund_rejected` |
| 5 | Non-integer boolean input: `calculate_points(True, 1)` or `refund_amount = True` | Because `bool` is a subclass of `int` in Python, booleans must be strictly rejected and yield 0 points / ignored refund. | Points: `0`; refund ignored | `tests/test_regression_and_edge_cases.py::test_boolean_inputs_strictly_rejected` |
| 6 | Event replay: duplicate `event_id` sent to `apply_reward_event` | Replayed event must be idempotent; balance and ledger must not be updated twice. | Second call returns unchanged account state; ledger length unchanged | `tests/test_acceptance_matrix.py::test_purchase_event_replay_is_idempotent` |
| 7 | Refund when points balance is low: account balance is 2 points, but refund calculates reverse delta of 10 points | Balance must never drop below zero; delta clamped to available balance (2 points reversed, balance 0). | Balance: `0`; points_delta: `-2` | `tests/test_regression_and_edge_cases.py::test_points_balance_never_negative` |

## Regression tests added
List the defects fixed and the tests added to prevent them from returning:
1. **Integer Floor Arithmetic Regression:** Added `test_paise_boundary_floor_arithmetic` to verify 9999, 10000, 19999, and 20000 paise boundaries.
2. **Cap Zero & Negative Clamping:** Added `test_zero_and_negative_cap_points` to verify `cap_points=0` and `cap_points=-10`.
3. **Cumulative Rounding Drift Prevention:** Added `test_multi_step_partial_refund_no_rounding_drift` to test multi-installment refunds summing to the original amount.
4. **Cumulative Excess Refund Guard:** Added `test_cumulative_excess_refund_rejected` to test that partial refunds followed by over-refunding are rejected.
5. **Strict Type Safety & Boolean Rejection:** Added `test_boolean_inputs_strictly_rejected` verifying that `True`/`False` cannot pose as valid integer amounts or rules.
6. **Refund Idempotency Replay:** Added `test_event_replay_idempotency_for_refund` ensuring replayed refund events do not subtract points repeatedly.
7. **Negative Balance Guard:** Added `test_points_balance_never_negative` ensuring account balance floor is strictly 0.
8. **Repeat Alerts Robustness & Determinism:** Added `test_repeat_transactions_deterministic_ordering_and_filtering` verifying handling of invalid items and deterministic sort order.
9. **CSV Account Statement:** Added `test_generate_account_statement_csv` for the optional statement export.

## Remaining failures or limitations
- **Remaining failures:** None. All 223 tests pass cleanly.
- **Known limitations:**
  - If points have already been redeemed externally and a refund occurs, points reversal is clamped to available points balance (preventing negative balance), which could leave an unrecovered liability if the account is never funded again.
