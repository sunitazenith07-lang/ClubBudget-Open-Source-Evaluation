# TESTING.md — Required submission

Complete this file with test evidence from your own work. Include at least five edge cases. Do not claim a test passed unless you ran it.

## Test command and environment
- **Python version**: Python 3.14.7 (Windows x64)
- **Command run**: `python -m pytest -q`
- **Actual test summary**: `220 passed in 0.21s` (214 existing acceptance/contract tests + 6 new regression/edge-case tests)

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | `amount_paise = 9999`, `points_per_100_rupees = 1` | Floor division yields 0 base points (`9999 // 10000 = 0`), resulting in 0 points | Returned `0` points (fixed initial bug where `round()` produced `1`) | `test_integer_floor_points_calculation[9999-0_0]` |
| 2 | `amount_paise = 50000`, `points_per_100_rupees = 1`, `cap_points = 0` | Cap of 0 must strictly cap earned points to 0 | Returned `0` points (fixed initial bug where `if cap_points:` treated 0 as falsy) | `test_cap_zero_is_respected` |
| 3 | Duplicate event replay: `{"event_id": "PURCHASE-001", "type": "purchase_captured", "transaction_id": "T", "amount_paise": 25000}` applied twice | Idempotent execution: balance remains 2, event ID recorded once, ledger contains single entry | `points_balance == 2`, `processed_event_ids == ["PURCHASE-001"]`, `len(ledger) == 1` | `test_purchase_event_replay_is_idempotent[PURCHASE-001]` |
| 4 | Non-integer and excess refunds on 100,000 paise purchase: `amount_paise` values `[-1, 150000, True, None, "100", 1.5, [], {}]` | Rejected as invalid or excess: account balance remains 10, refunded paise remains 0, no ledger entries added | `points_balance == 10`, `refunded_paise == 0` for all invalid types and excess values | `test_invalid_or_excess_refund_does_not_change_account` |
| 5 | Three successive partial refunds on 100,000 paise purchase (10 pts awarded): 30,000 paise, 30,000 paise, and 40,000 paise | Reversals calculated cumulatively without integer truncation drift: reverses 3, 3, and 4 pts; final balance 0 | `points_balance == 0`, `reversed_points == 10`, `refunded_paise == 100000` | `test_sequential_partial_refunds_up_to_full_amount` |
| 6 | Refund of a purchase that originally earned 0 points: `amount_paise = 5000` (50 Rs) refunded for 5,000 paise | Balance remains 0, reversed points 0, ledger records 0 points delta | `points_balance == 0`, `reversed_points == 0`, ledger delta `0` | `test_zero_awarded_purchase_refund` |

## Regression tests added
List the defects fixed and the tests added to prevent them from returning:

1. **`test_refund_event_replay_is_idempotent`** (`tests/test_regression_and_edge_cases.py`):
   - *Defect fixed*: Starter code permitted refund events to be applied multiple times if replayed, continuously decrementing the points balance and appending duplicate ledger entries.
   - *Protection*: Ensures replaying a processed refund event returns the existing account state without mutating points, ledger, or event lists.

2. **`test_sequential_partial_refunds_up_to_full_amount`** (`tests/test_regression_and_edge_cases.py`):
   - *Defect fixed*: Prevented truncation loss across sequential partial refunds and ensured attempts to refund beyond 100% of the original purchase amount are rejected.
   - *Protection*: Validates cumulative state updates across multiple partial refund calls and blocks excess refunds.

3. **`test_zero_awarded_purchase_refund`** (`tests/test_regression_and_edge_cases.py`):
   - *Defect fixed*: Guarded against division by zero or negative point calculations when refunding transactions that earned zero points.
   - *Protection*: Confirms zero-point transactions can be safely refunded without generating negative points or errors.

4. **`test_ledger_balance_mathematical_consistency`** (`tests/test_regression_and_edge_cases.py`):
   - *Defect fixed*: Starter code allowed discrepancies between `points_balance` and the sum of `points_delta` in the audit ledger under replay conditions.
   - *Protection*: Validates that across arbitrary sequences of purchases, refunds, and duplicate retries, `account["points_balance"] == sum(e["points_delta"] for e in account["ledger"])`.

5. **`test_malformed_and_missing_inputs_safety`** (`tests/test_regression_and_edge_cases.py`):
   - *Defect fixed*: Filtered out `bool` types (which inherit from `int` in Python) and `None`/malformed inputs from generating erroneous calculations.
   - *Protection*: Tests edge cases including boolean flags, empty structures, and None values across all public functions.

6. **`test_generate_account_statement_csv`** (`tests/test_regression_and_edge_cases.py`):
   - *Feature*: Validates CSV statement export functionality from the audit ledger.

## Remaining failures or limitations
- **Remaining failures**: None. All 220 tests pass.
- **Known limitations**: Repeat transaction alerts group transactions on exact matches of `(account_id, date, amount_paise)`. Near-repeat transactions occurring across midnight boundaries (e.g. 23:59:59 and 00:00:01) fall into distinct date buckets by design, adhering strictly to the calendar date grouping specification.
