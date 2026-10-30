# TESTING.md — Required submission

Complete this file with test evidence from your own work. Include at least five edge cases. Do not claim a test passed unless you ran it.

## Test command and environment

- Python version: Python 3.14.5
- Command run: `python3 -m pytest -v`
- Actual test summary: **223 passed in 0.11s**
  - `tests/test_acceptance_matrix.py` — 202 passed
  - `tests/test_contract.py` — 12 passed
  - `tests/test_event_id_regression.py` — 9 passed (newly added)

Baseline (before fixes): 67 failed, 147 passed out of 214 tests.

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | `calculate_points(9999, 1)` — amount just below ₹100 (one paise short) | 0 points (9999 paise is less than one complete ₹100 block) | 0 points ✅ | `test_integer_floor_points_calculation[9999-0_0]` |
| 2 | `calculate_points(50000, 1, cap_points=0)` — cap set to zero | 0 points (a cap of zero means no points awarded, per spec item 2) | 0 points ✅ | `test_cap_zero_is_respected` and `test_bonus_and_cap_matrix[50000-2-50-0-0]` |
| 3 | Refund with `amount_paise=True` (Python boolean) | Account unchanged (boolean is not a valid monetary amount) | Account unchanged ✅ | `test_invalid_or_excess_refund_does_not_change_account[True]` |
| 4 | Two different purchases both missing `event_id` | Both rejected safely without collision; balance stays 0 | Both rejected, balance=0 ✅ | `test_two_different_purchases_with_none_event_id_both_rejected` |
| 5 | Replay same `event_id` twice for a purchase | Points awarded once only; second replay is a no-op | Balance=5 after both calls ✅ | `test_valid_event_id_duplicate_purchase_is_idempotent` |
| 6 | Refund amount exceeding original purchase (e.g., refund 150,000 paise on a 100,000 paise purchase) | Account unchanged (excess refund rejected) | Account unchanged, balance=10 ✅ | `test_refund_amount_bounds_and_balance[150000]` and `test_invalid_or_excess_refund_does_not_change_account[150000]` |
| 7 | Refund with `amount_paise=None` | Account unchanged (None is not a valid integer) | Account unchanged ✅ | `test_invalid_or_excess_refund_does_not_change_account[None]` |
| 8 | Event with `type='purchase_declined'` | Zero points awarded; no transaction or ledger entry | Balance=0, transactions={} ✅ | `test_unrecognized_or_declined_events_do_not_award_points[purchase_declined]` |

## Regression tests added

Created `tests/test_event_id_regression.py` with 9 test functions to prevent the fixed bugs from returning:

| # | Test function | Defect it prevents |
|---|---|---|
| 1 | `test_none_event_id_purchase_is_rejected` | Ensures purchases with `event_id=None` do not modify the account |
| 2 | `test_missing_event_id_key_purchase_is_rejected` | Ensures a completely missing `event_id` key (no key in dict at all) is handled the same as explicit `None` |
| 3 | `test_two_different_purchases_with_none_event_id_both_rejected` | Prevents the None-to-None collision bug where the second legitimate event was silently dropped |
| 4 | `test_none_event_id_refund_is_rejected` | Ensures refunds with `event_id=None` do not reverse points |
| 5 | `test_valid_event_id_duplicate_purchase_is_idempotent` | Ensures replaying the same purchase event_id does not double-award points |
| 6 | `test_valid_event_id_duplicate_refund_is_idempotent` | Ensures replaying the same refund event_id does not double-reverse points |
| 7 | `test_distinct_valid_event_ids_both_processed` | Verifies that two different valid events are both processed normally (guards did not over-block) |
| 8 | `test_purchase_then_refund_with_valid_event_ids` | Verifies the full purchase → partial refund lifecycle works end-to-end |
| 9 | `test_input_account_not_mutated_by_none_event_id` | Ensures the original account dict is not mutated even when an event is rejected |

## Remaining failures or limitations

- **No remaining test failures.** All 223 tests pass with zero failures, zero errors, and zero skipped.
- **Known limitation:** The `processed_event_ids` list uses O(n) linear search for the `in` operator. This is acceptable for the current dataset scale but would need optimization (e.g., using a set) for production accounts with thousands of events.
- **No existing tests were deleted, skipped, weakened, or bypassed.**
