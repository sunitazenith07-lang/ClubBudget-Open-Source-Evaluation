# REWARD_RULE_NOTES.md — Required submission

Complete this file with your own actual examples and results. Do not leave prompts unanswered.

## 1. Worked points calculation
Show one purchase calculation from amount in paise through base points, bonus and cap. State the rounding rule at each step and include the actual output.

- Input:
  - `amount_paise = 259900` (₹2,599.00)
  - `points_per_100_rupees = 1`
  - `bonus_percent = 10`
  - `cap_points = 100`

- Step 1 — Base Points:
  - Formula: `(amount_paise // 10000) * points_per_100_rupees`
  - Calculation: `(259900 // 10000) * 1 = 25 * 1 = 25`
  - Rule: Integer floor division. Remaining 9,900 paise (₹99.00) do not earn points.

- Step 2 — Bonus Points:
  - Formula: `base_points * (100 + bonus_percent) // 100`
  - Calculation: `25 * (100 + 10) // 100 = 25 * 110 // 100 = 2750 // 100 = 27`
  - Rule: Integer floor division on promotional bonus percentage.

- Step 3 — Promotional Cap:
  - Formula: `min(points, cap_points)` if cap is provided
  - Calculation: `min(27, 100) = 27`
  - Rule: The cap limits maximum points awarded. Since 27 <= 100, 27 points remain.

- Step 4 — Non-Negative Check:
  - Formula: `max(0, points)`
  - Calculation: `max(0, 27) = 27`

- Final Output: **27 points** awarded.

---

## 2. Partial-refund example
Show the points originally awarded, the refund amount, how the reversal is calculated, the resulting balance, and the relevant ledger entry.

- Original purchase:
  - `amount_paise = 100000` (₹1,000.00), awarded 10 points.
  - Starting account `points_balance = 10`.

- Refund event:
  - Partial refund of `amount_paise = 40000` (₹400.00, 40% of original purchase).

- Reversal calculation:
  - Cumulative refund: `40000` paise.
  - Total points to reverse: `awarded_points * cumulative_refund // original_amount = 10 * 40000 // 100000 = 4`.
  - Incremental reversal delta: `should_reverse - already_reversed = 4 - 0 = 4`.
  - Account points balance update: `10 - 4 = 6`.
  - Transaction state: `refunded_paise = 40000`, `reversed_points = 4`.

- Resulting ledger entry appended:
  ```python
  {'event_id': 'E_REF', 'type': 'refund_processed', 'points_delta': -4}
  ```

---

## 3. Three edge cases
For each, provide input, expected behaviour, actual observed result, and the test that verifies it.

1. **Edge Case 1: Amount just below 100-rupee threshold**
   - Input: `amount_paise = 9999` (₹99.99), `points_per_100_rupees = 1`.
   - Expected Behaviour: 0 points awarded (does not round up to 1 point).
   - Actual Result: 0 points awarded.
   - Verifying Test: `test_integer_floor_points_calculation[9999-0_0]`.

2. **Edge Case 2: Cap explicitly set to 0**
   - Input: `amount_paise = 50000`, `points_per_100_rupees = 2`, `bonus_percent = 50`, `cap_points = 0`.
   - Expected Behaviour: 0 points awarded (cap of 0 is respected and not treated as absent).
   - Actual Result: 0 points awarded.
   - Verifying Test: `test_cap_zero_is_respected`.

3. **Edge Case 3: Boolean value passed as refund amount**
   - Input: Event with `type = "refund_processed"` and `amount_paise = True`.
   - Expected Behaviour: Event is safely ignored; boolean is rejected and not coerced to integer 1; account balance and transaction records remain unchanged.
   - Actual Result: `refunded_paise` remains 0, `points_balance` unchanged at 10.
   - Verifying Test: `test_invalid_or_excess_refund_does_not_change_account[True]`.

---

## 4. Assumptions and limitations
- All currency calculations use paise and integer floor arithmetic (`//`). No floating point rounding is used.
- Account points balance cannot drop below 0. If a reversal delta exceeds the current points balance, the balance stops at 0.
- Total refunded paise cannot exceed the original purchase amount. Any excess or negative refund is rejected.
- Events are idempotent by `event_id`. Replayed events are ignored without modifying balances or adding duplicate ledger entries.
- Repeat alerts are operational warnings for human review only and do not automatically alter balances or block transactions.
