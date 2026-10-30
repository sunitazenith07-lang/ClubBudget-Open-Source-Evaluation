# TESTING.md — Required submission

## Test command and environment
- Python version: Python 3.14.7 (64-bit)
- Command run: `python -m pytest -q`
- Actual test summary: `220 passed in 0.35s` (214 baseline tests + 6 new regression tests, 0 failures).

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | `amount_paise = 9999` (Rs 99.99), rate = 1 pt/Rs 100 | Returns 0 points because it has not completed a full Rs 100 unit. | 0 | `test_acceptance_matrix.py::test_integer_floor_points_calculation[9999-0_0]` |
| 2 | `cap_points = 0`, `amount_paise = 50000`, rate = 1 | Returns 0 points because a cap of 0 limits points to 0. | 0 | `test_contract.py::test_cap_zero_is_respected` |
| 3 | Replaying event `PURCHASE-001` on an account | Event is recognized as already processed; no balance change and no duplicate ledger row. | `points_balance == 2`, `len(ledger) == 1` | `test_acceptance_matrix.py::test_purchase_event_replay_is_idempotent[PURCHASE-001]` |
| 4 | `amount_paise = True` | Rejected because booleans should not be treated as 1 paisa. | 0 points awarded, account unchanged | `test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account[True]` |
| 5 | Refund of 150,000 paise on a 100,000 paise purchase | Refund exceeds original purchase amount; rejected without modifying account. | `refunded_paise == 0`, `points_balance == 10` | `test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account[150000]` |
| 6 | 3-step partial refund: Rs 300, Rs 300, Rs 400 on Rs 1,000 purchase (10 points awarded) | Reverses 3 points, then 3 points, then 4 points, reversing all 10 points with zero remainder loss. | Points balance goes from 10 -> 7 -> 4 -> 0 | `test_regression.py::test_multi_step_partial_refund` |

## Regression tests added
I added `tests/test_regression.py` with tests for:
1. `test_multi_step_partial_refund`: Verifies that multiple partial refunds cumulatively reverse all awarded points when reaching 100%.
2. `test_refund_replay_does_not_duplicate`: Verifies that replaying a refund event does not double-reverse points or duplicate ledger records.
3. `test_boolean_values_rejected`: Tests that `True` and `False` values are rejected as amounts or rules.
4. `test_excess_refund_rejected_after_partial`: Verifies that an invalid refund following a valid partial refund is rejected.
5. `test_ledger_sum_matches_balance`: Ensures the sum of `points_delta` in the ledger always matches the final points balance.
6. `test_repeat_transactions_empty_and_sorting`: Verifies that empty lists return empty lists and repeat alerts are sorted deterministically by account ID.

## Remaining failures or limitations
- No failing tests remaining (220 passed).
- The state is stored in Python dictionaries in memory; a production system would need a persistent database with transaction locks to prevent concurrency issues.
