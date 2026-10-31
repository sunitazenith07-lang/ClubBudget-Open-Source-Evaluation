# TESTING.md — Required submission

Complete this file with test evidence from your own work. Include at least five edge cases. Do not claim a test passed unless you ran it.

## Test command and environment
- Python version: Python 3.14.6
- Command run: `python -m pytest -q`
- Actual test summary:
  - Baseline (untouched starter): `67 failed, 147 passed in 0.84s` (Total 214 tests)
  - After implementation and fixes: `221 passed in 0.16s` (Total 221 tests, 0 failed, 0 errors, 0 skipped)
  - Offline demo: `python -m main` runs cleanly (Points example: 27, Repeat warnings: [])

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | `amount_paise = 19999`, `points_per_100_rupees = 1` (paise boundary below 200 rupees) | Calculate integer floor: 19999 // 10000 = 1 point awarded | Exactly 1 point awarded (previously 2 points due to `round()`) | `tests/test_contract.py::test_points_use_floor`, `tests/test_acceptance_matrix.py::test_integer_floor_points_calculation[19999-1]` |
| 2 | `amount_paise = 50000`, `points_per_100_rupees = 1`, `cap_points = 0` | Cap of 0 must strictly result in 0 points awarded | Exactly 0 points awarded (previously 5 points because `if cap_points:` treated 0 as falsy) | `tests/test_contract.py::test_cap_zero_is_respected`, `tests/test_acceptance_matrix.py::test_bonus_and_cap_matrix[50000-2-50-0-0]` |
| 3 | Replaying event `event_id = "E1"` for purchase or refund | Idempotent handling: second execution must not modify balance or duplicate ledger entry | Returned unchanged account (`points_balance == 2`, `len(ledger) == 1`, `processed_event_ids == ['E1']`) | `tests/test_contract.py::test_purchase_event_once`, `tests/test_acceptance_matrix.py::test_purchase_event_replay_is_idempotent`, `tests/test_regression.py::test_refund_replay_is_idempotent` |
| 4 | Sequential partial refunds summing to 100% of purchase amount (Rs 1000 with 50% bonus = 15 pts, two refunds of 50,000 paise) | Proportional integer calculation tracking cumulative reversals must reverse 7 pts then 8 pts without integer drift, totaling exactly 15 pts | Exactly 7 then 8 points reversed; final points balance is 0, reversed points is 15, ledger deltas: -7 and -8 | `tests/test_regression.py::test_sequential_partial_refunds_no_rounding_drift` |
| 5 | Excess and invalid refund amounts: `-1`, `0`, `150000` (exceeding 100,000 purchase), `True`, `"100"`, `1.5` | Invalid or excess refund must be rejected completely without modifying `refunded_paise`, balance, or ledger | Account unchanged; `refunded_paise == 0`, `points_balance == 10`, no ledger append | `tests/test_contract.py::test_invalid_or_excess_refund_ignored`, `tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account`, `tests/test_regression.py::test_cumulative_excess_refund_rejected` |
| 6 | Points balance non-negativity under refund reversal | If points balance is lower than theoretical reversal delta, balance must never drop below 0 | Points balance is clamped to 0 and ledger delta reflects only the deducted points | `tests/test_regression.py::test_points_balance_never_negative` |

## Regression tests added
List the defects fixed and the tests added to prevent them from returning:
1. `tests/test_regression.py::test_sequential_partial_refunds_no_rounding_drift`: Prevents integer truncation drift across multiple partial refunds; ensures full refund reverses 100% of awarded points.
2. `tests/test_regression.py::test_refund_replay_is_idempotent`: Prevents double-reversals when a refund event is replayed.
3. `tests/test_regression.py::test_points_balance_never_negative`: Guarantees points balance never becomes negative during reversals.
4. `tests/test_regression.py::test_cumulative_excess_refund_rejected`: Prevents cumulative refunds from exceeding the original transaction amount.
5. `tests/test_regression.py::test_malformed_event_fields_safe_handling`: Verifies missing identifiers, boolean values, strings, and null rule inputs are safely rejected without unhandled exceptions.
6. `tests/test_regression.py::test_full_synthetic_dataset_integration`: Integrates with all 264 reward events and 180 repeat transaction records from `data/records.json` to verify global invariants across 40 accounts.
7. `tests/test_regression.py::test_generate_account_statement_csv`: Protects the optional stretch feature for CSV ledger statement export.

## Remaining failures or limitations
- Remaining test failures: None (221 of 221 tests passing).
- Known limitations:
  - Account state is in-memory and not persisted to an external relational database.
  - Transactions assume single-currency arithmetic (paise / Indian Rupees). Currency conversions or multi-currency wallets are out of scope.
  - Repeat transaction alerts flag candidate duplicates based on exact account, date, and amount matching for human inspection; they do not automatically decline transactions to avoid false-positive customer blocking.

