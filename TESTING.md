# TESTING.md — Required submission

## Test command and environment
- **Python version:** Python 3.15.0 (macOS Darwin arm64)
- **Command run:** `python -m pytest -q`
- **Actual test summary:** `224 passed in 0.06s`
  - 214 baseline tests (all passing): `tests/test_contract.py` (11 tests) + `tests/test_acceptance_matrix.py` (203 tests)
  - 10 new regression tests: `tests/test_regression.py`

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | `amount_paise = 19999`, `points_per_100_rupees = 1` | Floor division: `19999 // 10000 = 1`. Must not round up to `2`. | `1` | `test_contract.py::test_points_use_floor`, `test_acceptance_matrix.py::test_integer_floor_points_calculation[19999-1]` |
| 2 | `amount_paise = 50000`, `points_per_100_rupees = 1`, `cap_points = 0` | Cap of exactly zero means zero points awarded regardless of amount. Must not be bypassed by truthiness. | `0` | `test_contract.py::test_cap_zero_is_respected`, `test_acceptance_matrix.py::test_bonus_and_cap_matrix[50000-2-50-0-0]` |
| 3 | Same `event_id = "E1"` submitted twice, `amount_paise = 25000` | Duplicate event detected; balance credited once only. `processed_event_ids` has one entry, `ledger` has one entry. | `points_balance = 2`, `processed_event_ids = ['E1']`, `len(ledger) = 1` | `test_contract.py::test_purchase_event_once`, `test_acceptance_matrix.py::test_purchase_event_replay_is_idempotent[PURCHASE-000]` |
| 4 | `refund_processed` with `amount_paise = True` (boolean) | Boolean must be rejected as invalid type. No state mutation, `refunded_paise` stays `0`. | `refunded_paise = 0`, `points_balance = 10` | `test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account[True]` |
| 5 | `purchase_captured` with `amount_paise = 150000`, then `refund_processed` with `amount_paise = 150001` | Over-refund exceeds original purchase; must be fully rejected. No balance change, no ledger entry. | `refunded_paise = 0`, `points_balance = 15` | `test_contract.py::test_invalid_or_excess_refund_ignored`, `test_acceptance_matrix.py::test_refund_amount_bounds_and_balance[150000]` |
| 6 | Purchase `100000` paise (10 pts). Refund 1: `30000` paise. Refund 2: `70000` paise. Refund 3: `1` paise. | Refunds 1+2 fully exhaust the purchase. Third refund is rejected with no state change. `reversed_points = 10`, `points_balance = 0`, R-3 not in `processed_event_ids`. | All assertions match | `test_regression.py::test_cumulative_partial_refunds_and_over_refund_rejection` |
| 7 | Event with `type = "purchase_declined"` or `type = "purchase_pending"` | Only `purchase_captured` earns points. Declined and pending events award 0, create no transaction record. | `points_balance = 0`, `transactions = {}` | `test_contract.py::test_declined_event_does_not_award`, `test_acceptance_matrix.py::test_unrecognized_or_declined_events_do_not_award_points[purchase_declined]` |
| 8 | `purchase_captured` with `amount_paise = 0` | Zero paise is not a valid purchase amount. Event rejected; no transaction recorded, no ledger entry, `points_balance = 0`. | `points_balance = 0`, `"T-0" not in transactions` | `test_regression.py::test_zero_amount_purchase_refund_branch` |
| 9 | `flag_repeat_transactions` with `threshold = -1` or `threshold = 0` | Sub-1 threshold must default to `2`. A single transaction must never be flagged as a repeat. | Returns valid list; lone transaction not flagged | `test_acceptance_matrix.py::test_repeat_alert_threshold_input_is_handled[-1]`, `test_repeat_alert_threshold_input_is_handled[0]` |
| 10 | Three sequential refunds of `10000` paise each on a `30000` paise purchase (3 points awarded) | Cumulative reversal: `(3×10000)//30000=1`, `(3×20000)//30000=2`, `(3×30000)//30000=3`. Each delta = 1. Final `reversed_points = 3`, `points_balance = 0`. | All three deltas exactly 1; final balance 0 | `test_regression.py::test_proportional_integer_truncation_across_multiple_refunds` |

## Regression tests added

New test suite: `tests/test_regression.py` (10 tests). Each test locks in a specific defect that was identified and fixed:

1. **`test_refund_event_replay_is_idempotent`** — Replaying the same `refund_processed` event must not deduct points twice or add a second ledger entry.
2. **`test_cumulative_partial_refunds_and_over_refund_rejection`** — Validates correct sequential reversal across split refunds and that a third refund after full exhaustion is completely rejected.
3. **`test_proportional_integer_truncation_across_multiple_refunds`** — Verifies exact integer reversal delta tracking across three sequential equal partial refunds (no truncation drift).
4. **`test_zero_awarded_purchase_refund_safety`** — A sub-100-rupee purchase (0 points awarded); full refund must not create negative points or corrupt ledger.
5. **`test_malformed_and_missing_identifiers_handling`** — Events missing `event_id` or `transaction_id`, and `None`/non-dict inputs, are all safely ignored.
6. **`test_cap_zero_and_negative_rules_safeguards`** — Zero/negative cap, negative bonus, negative `points_per_100_rupees`, and non-integer types all return `0` cleanly.
7. **`test_csv_account_statement_generation`** — CSV output has correct header and accurate running balance per ledger event.
8. **`test_purchase_captured_invalid_amount_safeguards`** — Boolean `True`, negative amounts, and `None` rules all handled correctly.
9. **`test_repeat_transactions_and_csv_statement_edge_cases`** — Non-dict elements in transaction list skipped; `threshold=None` defaults to 2; CSV handles malformed ledger entries.
10. **`test_zero_amount_purchase_refund_branch`** — `amount_paise=0` purchase is fully rejected (no transaction recorded); subsequent refund on the unknown transaction is also safely rejected.

## Remaining failures or limitations
- **Zero remaining test failures.** All 224 tests pass cleanly.
- *Known limitation:* The implementation is in-memory only. A concurrent multi-worker deployment would require atomic database transactions or event-queue partitioning by `account_id` to prevent race conditions on simultaneous refund processing.
