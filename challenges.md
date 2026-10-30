# challenges.md - COMPULSORY submission

## 1. Challenge or confusing behaviour
The most challenging aspect was implementing fractional refund reversals with proportional integer division across multiple partial refunds while avoiding rounding drift and negative balance edge cases:
- In fractional points arithmetic, reversing points independently on each partial refund (e.g., `(awarded * refund) // total`) causes rounding errors. If an item costing 1,000 rupees (100,000 paise) awards 10 points and receives three partial refunds of 33,333 paise, 33,333 paise, and 33,334 paise: calculating `(10 * 33333) // 100000 = 3` independently for each refund would only reverse `3 + 3 + 3 = 9` points, failing to reverse the final 10th point.
- Another tricky behaviour was Python's type hierarchy where `isinstance(True, int)` evaluates to `True`. Because test matrices pass boolean values (`True`, `False`) as invalid refund amounts, standard `isinstance(val, int)` checks falsely accepted booleans.
- Furthermore, refunding transactions where the user's balance has already been partially redeemed must clamp the reversal so `points_balance` never goes negative.

## 2. Evidence
1. **Rounding drift in independent reversals:**
   - Transaction: 100,000 paise -> 10 points awarded.
   - Independent calculation:
     - Step 1: `(10 * 33333) // 100000 = 3` points reversed (7 remaining).
     - Step 2: `(10 * 33333) // 100000 = 3` points reversed (4 remaining).
     - Step 3: `(10 * 33334) // 100000 = 3` points reversed (1 remaining instead of 0!).
2. **Boolean type pollution:**
   - In `tests/test_acceptance_matrix.py`:
     `@pytest.mark.parametrize("amount", [..., True, None, "100", 1.5, [], {}, False])`
     `test_invalid_or_excess_refund_does_not_change_account(amount)`
     Running without `isinstance(amount, bool)` guard treated `True` as `1` paisa and `False` as `0`, triggering partial refund logic instead of rejecting the event.
3. **Overdraft prevention:**
   - Requirement 5: "Reverse points proportionally for refunds using integer arithmetic, never reverse more than awarded and never allow a negative balance."
   - If an account balance has dropped below the calculated points delta, a naive subtraction `balance -= delta` causes a negative balance.

## 3. What I tried
1. **Experiment 1 (Independent Delta):**
   - Calculated `delta = (awarded * refund) // amount_paise`.
   - Result: Failed on multi-stage cumulative refunds because integer truncation on each step left orphaned points when the transaction was 100% refunded.
2. **Experiment 2 (Floating-point proportional math):**
   - Attempted using floats and rounding: `round(awarded * (refund / amount_paise))`.
   - Result: Contravened Requirement 1 and 5 demanding integer arithmetic; exposed system to IEEE 754 precision issues at fractional boundaries.
3. **Experiment 3 (Cumulative Proportional Tracking):**
   - Stored cumulative `refunded_paise` and cumulative `reversed_points` in the transaction record.
   - At each refund event, computed cumulative expected reversal: `should_reverse = (awarded * cumulative_refunded) // amount_paise`.
   - Computed step delta as: `delta = should_reverse - reversed_points`.
   - Clamped delta: `delta = min(delta, out['points_balance'])`.

## 4. Resolution
- Adopted the Cumulative Proportional Tracking pattern:
  ```python
  new_refunded = txn["refunded_paise"] + refund
  should_reverse = (txn["awarded_points"] * new_refunded) // txn["amount_paise"]
  delta = should_reverse - txn["reversed_points"]
  delta = max(0, min(delta, out["points_balance"]))
  txn["refunded_paise"] = new_refunded
  txn["reversed_points"] += delta
  out["points_balance"] -= delta
  ```
- Added strict type validation:
  `if not isinstance(val, int) or isinstance(val, bool): return ...`
  This cleanly filtered `True`, `False`, `None`, floats, and complex structures while honoring pure integers.

## 5. Proof and regression prevention
- **Tests verifying the fix:**
  - `tests/test_acceptance_matrix.py::test_refund_amount_bounds_and_balance` (all 20 parameterized cases passed).
  - `tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account` (all 14 edge cases passed, including `True` and `False`).
  - `tests/test_regression_and_edge_cases.py::test_multi_step_partial_refund_no_rounding_drift`: Explicit test with 33,333 + 33,333 + 33,334 paise confirming 0 drift and final balance of 0.
  - `tests/test_regression_and_edge_cases.py::test_points_balance_never_negative`: Confirms clamping when account points balance is less than reverse delta.

## 6. Unresolved challenge or next step
- When an account points balance is depleted (e.g., points were redeemed or expired) and a refund occurs, the system clamps the balance to 0, which means not all calculated reversed points can be recovered from the balance immediately.
- In a production banking environment, an audit ledger should flag an "uncollected reversal liability" or negative uncommitted reserve line item to track unrecovered clawbacks when future points are earned.
