# REWARD_RULE_NOTES.md — Required submission

Complete this file with your own actual examples and results. Do not leave prompts unanswered.

## 1. Worked points calculation
Show one purchase calculation from amount in paise through base points, bonus and cap. State the rounding rule at each step and include the actual output.

**Scenario:**
- Purchase amount: `259,900 paise` (₹2,599.00)
- Rule:
  - `points_per_100_rupees`: `1`
  - `bonus_percent`: `10%`
  - `cap_points`: `100`

**Step-by-step calculation:**
1. **Base points:**
   - Formula: `base_points = floor(amount_paise / 10000) * points_per_100_rupees`
   - Computation: `floor(259900 / 10000) * 1 = 25 * 1 = 25`
   - Rounding rule: Truncate downwards to the nearest whole ₹100 block (integer floor division `//`). The 9,900 paise remainder earns 0 points.
   - Intermediate output: `25 points`.

2. **Bonus points:**
   - Formula: `bonus_points = floor(base_points * (100 + bonus_percent) / 100)`
   - Computation: `floor(25 * (100 + 10) / 100) = floor(25 * 110 / 100) = floor(2750 / 100) = 27`
   - Rounding rule: Integer floor division `//`. Fractional bonus points (0.50 points) are truncated.
   - Intermediate output: `27 points`.

3. **Cap application:**
   - Formula: `if cap_points is not None: final_points = min(bonus_points, cap_points)`
   - Computation: `min(27, 100) = 27`
   - Rounding rule: Exact minimum comparison. If `cap_points` were 0, output would be 0.
   - **Final output:** `27 points`.

---

## 2. Partial-refund example
Show the points originally awarded, the refund amount, how the reversal is calculated, the resulting balance, and the relevant ledger entry.

**Scenario:**
- Original purchase: `100,000 paise` (₹1,000.00)
  - Awarded points: `10 points`
  - Starting account balance: `10 points`
- Partial refund request: `50,000 paise` (₹500.00, 50% refund)

**Step-by-step reversal calculation:**
1. **Cumulative refund tracking:**
   - `cumulative_refunded = txn['refunded_paise'] + refund = 0 + 50000 = 50000 paise`.
   - Bounds check: `50000 <= 100000` (valid, not in excess of original purchase amount).
2. **Proportional reversal calculation:**
   - `should_reverse = (txn['awarded_points'] * cumulative_refunded) // txn['amount_paise']`
   - `should_reverse = (10 * 50000) // 100000 = 500000 // 100000 = 5 points`.
   - `delta = should_reverse - txn['reversed_points'] = 5 - 0 = 5 points`.
3. **Balance update and clamping:**
   - Points balance before refund: `10`.
   - Reversal delta to subtract: `5`.
   - Resulting balance: `10 - 5 = 5 points` (guaranteed non-negative).
4. **Transaction record state:**
   - `txn['refunded_paise'] = 50000`
   - `txn['reversed_points'] = 5`
5. **Ledger entry appended:**
   ```json
   {
     "event_id": "EV-REFUND-001",
     "type": "refund_processed",
     "points_delta": -5
   }
   ```

---

## 3. Three edge cases
For each, provide input, expected behaviour, actual observed result, and the test that verifies it.

### Edge Case 1: Cap of zero points (`cap_points = 0`)
- **Input:** `amount_paise = 50000`, `points_per_100_rupees = 2`, `bonus_percent = 50`, `cap_points = 0`.
- **Expected behaviour:** Base points would be 10, bonus points 15. However, since the promotional cap is explicitly configured to 0, points awarded must be clamped to 0. Cap of 0 must not be treated as falsy or omitted.
- **Actual observed result:** `0 points`.
- **Test:** `tests/test_acceptance_matrix.py::test_bonus_and_cap_matrix[50000-2-50-0-0]`.

### Edge Case 2: Cumulative partial refund with fractional remainder
- **Input:** Original purchase of `100,000 paise` earning 10 points. Three partial refunds: `33,333 paise`, `33,333 paise`, and `33,334 paise` (totaling exactly 100,000 paise).
- **Expected behaviour:** Reversals must be calculated cumulatively so integer division does not discard fractional points across multiple steps. Reversals must be 3, 3, and 4 points respectively, leaving 0 points remaining and total reversed points of 10.
- **Actual observed result:** Reversals delta sequence `[-3, -3, -4]`; final points balance: `0`; cumulative reversed points: `10`.
- **Test:** `tests/test_regression_and_edge_cases.py::test_multi_step_partial_refund_no_rounding_drift`.

### Edge Case 3: Rejection of boolean values in numeric fields
- **Input:** `calculate_points(True, 1)` or refund event with `amount_paise: True`.
- **Expected behaviour:** In Python, `isinstance(True, int)` is true. However, boolean values are invalid currency/point representations. The system must reject booleans, returning 0 points or ignoring the refund without mutating state.
- **Actual observed result:** `0 points` awarded; refund event ignored; no ledger entry recorded.
- **Test:** `tests/test_regression_and_edge_cases.py::test_boolean_inputs_strictly_rejected`.

---

## 4. Assumptions and limitations
- **Rounding assumptions:** All division operations (`amount_paise // 10000`, bonus calculations, and refund reversal ratios) strictly follow integer floor arithmetic (truncating toward zero for positive numbers). Fractional paise and points are never carried over to future independent transactions.
- **Missing-field handling:** Events with missing or empty `event_id`, missing `transaction_id`, or missing/non-positive `amount_paise` are treated as invalid and safely ignored without modifying account state or ledger.
- **Repeat-alert threshold assumptions:** Alerts are triggered when the count of transactions sharing the same `(account_id, date, amount_paise)` tuple strictly exceeds the threshold (`count > threshold`). By default `threshold = 2`, flagging groups of 3 or more. Alerts are operational signals for human review and never block execution or alter transaction processing.
- **Unresolved issue / Balance depletion:** If points from a purchase are redeemed or spent before a refund occurs, the refund reverses only up to the currently available points balance (preventing negative balances). In enterprise banking, this would be tracked as a negative pending balance or liability against future earnings.
