# TESTING.md — Required submission

Complete this file with test evidence from your own work. Include at least five edge cases. Do not claim a test passed unless you ran it.

## Test command and environment
- Python version: Python 3.14.7
- Command run: `python -m pytest -q`
- Actual test summary: 219 passed in 0.47s

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | `amount_paise = 19999`, `points_per_100_rupees = 1` | Floor division yields 1 point for ₹199.99 (no rounding up to 2) | 1 point awarded | `test_points_use_floor`, `test_regression_floor_points_boundary` |
| 2 | `amount_paise = 50000`, `cap_points = 0` | Falsy integer `0` is respected as cap, returning 0 points | 0 points awarded | `test_cap_zero_is_respected`, `test_regression_cap_zero_resets_points` |
| 3 | Replay purchase event with duplicate `event_id` | Idempotent execution; balance not incremented twice, event ID not duplicated | `points_balance = 5`, `processed_event_ids = ['EVT-REG-1']`, 1 ledger entry | `test_purchase_event_once`, `test_regression_idempotent_event_replay` |
| 4 | Excess refund `amount_paise = 150000` on a 100,000 paise purchase | Refund exceeding transaction amount rejected without mutating account | `refunded_paise = 0`, `points_balance = 10` | `test_invalid_or_excess_refund_ignored`, `test_regression_excess_refund_rejected` |
| 5 | Sequential partial refunds (40,000 paise then 60,000 paise on 100,000 purchase) | Proportionally reverses 4 then 6 points without cumulative integer drift or negative balance | `reversed_points = 10`, `points_balance = 0` | `test_partial_refund_reverses_proportionally`, `test_regression_multi_partial_refunds_cumulative` |

## Regression tests added
List the defects fixed and the tests added to prevent them from returning.
- Created `tests/test_regression.py` containing:
  - `test_regression_floor_points_boundary`: Prevents regression where boundary values near ₹100 thresholds round up rather than flooring.
  - `test_regression_cap_zero_resets_points`: Prevents regression where `cap_points = 0` evaluates falsy and fails to clamp points to zero.
  - `test_regression_idempotent_event_replay`: Prevents duplicate events from altering balances or duplicating entries in `processed_event_ids`.
  - `test_regression_excess_refund_rejected`: Prevents over-refunding beyond the original purchase amount.
  - `test_regression_multi_partial_refunds_cumulative`: Validates multi-step partial refund reversal accuracy and ledger balance integrity.

## Remaining failures or limitations
List any known failing tests or unresolved behaviours honestly.
- None. All 219 tests pass cleanly.
