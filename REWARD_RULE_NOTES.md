# REWARD_RULE_NOTES.md — Required submission

Complete this file with your own actual examples and results. Do not leave prompts unanswered.

## 1. Worked points calculation
Show one purchase calculation from amount in paise through base points, bonus and cap. State the rounding rule at each step and include the actual output.

- **Input:** `amount_paise = 259900` (₹2,599.00), `points_per_100_rupees = 1`, `bonus_percent = 10`, `cap_points = 100`
- **Step 1 (Complete ₹100 blocks via integer floor):** `259900 // 10000 = 25` (the remaining `9900` paise is floored off).
- **Step 2 (Base points):** `25 * 1 = 25` points.
- **Step 3 (Bonus points via integer floor):** `(25 * (100 + 10)) // 100 = 2750 // 100 = 27` points.
- **Step 4 (Apply cap):** `min(27, 100) = 27` points.
- **Actual output:** `27` (verified via `python -m main`).


## 2. Partial-refund example

- **Original purchase (`event_id = "E1"`, `transaction_id = "T"`):** `amount_paise = 100000` (₹1,000.00) with `points_per_100_rupees = 1` awards `10` points (`points_balance = 10`).
- **Partial refund (`event_id = "E2"`, `transaction_id = "T"`):** `amount_paise = 50000` (₹500.00).
- **Proportional reversal calculation:** `(10 * 50000) // 100000 = 5` points reversed (`delta = 5 - 0 = 5`).
- **Resulting state:** `points_balance = 5`, `reversed_points = 5`, `refunded_paise = 50000`.
- **Ledger entry appended:** `{'event_id': 'E2', 'type': 'refund_processed', 'points_delta': -5}`.

## 3. Three edge cases
1. **Sub-₹100 boundary (`amount_paise = 9999`):** Expected `0` points because `9999 // 10000 == 0`. Observed `0` (`test_integer_floor_points_calculation`).
2. **Cumulative over-refund (`60000` followed by `50000` on a `100000` purchase):** Second refund exceeds remaining `40000` paise and must be ignored without altering balance (`4`) or `refunded_paise` (`60000`). Observed `points_balance == 4` (`test_cumulative_partial_refunds_and_over_refund_rejected`).
3. **Boolean inputs (`amount_paise = True`):** Since `bool` subclasses `int` in Python, `True` must be explicitly rejected rather than treated as `1` paise. Observed `0` points and `0` refunded paise (`test_boolean_and_non_int_inputs_rejected`).

## 4. Assumptions and limitations
- All points and refund reversals use strict integer floor division (`//`).
- Events missing `event_id`, `transaction_id`, or valid positive integer `amount_paise` are ignored without mutating account state.
- Repeat transaction alerts trigger strictly above `threshold` (`len(ids) > threshold`) for valid transactions with `threshold >= 1`.