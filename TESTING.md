# TESTING.md — Required submission

Complete this file with test evidence from your own work. Include at least five edge cases. Do not claim a test passed unless you ran it.

## Test command and environment
- Python version: Python 3.14.2
- Command run: `python3 -m pytest -q`
- Actual test summary: `222 passed in 0.10s` (0 failed, 0 errors, 0 skipped)

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | `amount_paise = 19999`, `points_per_100_rupees = 1` | Floor divide: 19999 // 10000 = 1 base point, not rounded up to 2 | Returned `1` | `tests/test_contract.py::test_points_use_floor` |
| 2 | `cap_points = 0`, `amount_paise = 50000`, `points_per_100_rupees = 1` | Cap of 0 must strictly result in 0 points awarded | Returned `0` | `tests/test_contract.py::test_cap_zero_is_respected` |
| 3 | Replay purchase event `event_id = 'E1'` twice on same account | Replayed event is ignored: balance remains unchanged, `processed_event_ids` contains single `'E1'` | Balance remained `2`, `processed_event_ids == ['E1']` | `tests/test_contract.py::test_purchase_event_once` |
| 4 | Refund with negative amount `amount_paise = -1` or excess `150000` on a `100000` purchase | Invalid/excess refund rejected: account balance and `refunded_paise` remain unaltered | `refunded_paise == 0`, `points_balance == 10` | `tests/test_contract.py::test_invalid_or_excess_refund_ignored` |
| 5 | Non-integer refund payload: `amount_paise = True` or `"100"` or `[]` | Invalid types rejected without throwing exceptions; account unchanged | Account unmutated, `refunded_paise == 0` | `tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account` |
| 6 | Sequential partial refunds: ₹300 (3 pts) + ₹300 (3 pts) + ₹400 (4 pts) on ₹1000 purchase | Proportional integer points reversal at each step, exactly totaling 10 pts reversed with balance = 0 | Balance decremented 10 -> 7 -> 4 -> 0; cumulative reversed = 10 | `tests/test_regression.py::test_cumulative_multiple_partial_refunds` |
| 7 | Full refund on account with insufficient balance (`points_balance = 2`, reversal needed = 10) | Reversal capped at available balance (`delta = 2`); points balance never becomes negative | Balance reached `0`, `reversed_points == 2`, `ledger[-1]['points_delta'] == -2` | `tests/test_regression.py::test_refund_never_results_in_negative_points_balance` |

## Regression tests added
Defects fixed and the corresponding regression tests added in `tests/test_regression.py`:
1. **Integer Floor & Bonus Rounding:** Added `test_points_integer_arithmetic_floor_rounding` verifying ₹25.99 with 10% bonus yields 27 points.
2. **Negative/Invalid Input Protection:** Added `test_points_negative_or_invalid_inputs` checking negative per-rupee, negative bonus, negative cap, and boolean/string inputs.
3. **Cumulative Partial Refunds:** Added `test_cumulative_multiple_partial_refunds` verifying sequential partial refunds and subsequent over-refund rejection.
4. **Refund Replay Idempotency:** Added `test_refund_replay_is_idempotent` ensuring replaying a refund event does not reverse points a second time.
5. **Negative Balance Guard:** Added `test_refund_never_results_in_negative_points_balance` protecting against negative balances when refunding accounts with low balances.
6. **Missing Identifier Safety:** Added `test_missing_or_empty_identifiers_safe` asserting graceful handling of missing `event_id`, missing `transaction_id`, and empty dicts.
7. **Duplicate Transaction Capture Protection:** Added `test_duplicate_purchase_transaction_id_rejected` verifying that an already captured transaction ID is not credited twice even under a new event ID.
8. **Repeat Alert Input Safety:** Added `test_flag_repeat_transactions_edge_cases` verifying resilience against non-list inputs and non-dict records.

## Remaining failures or limitations
- None. All 214 baseline tests and 8 regression tests pass cleanly (`222 passed in 0.10s`).
