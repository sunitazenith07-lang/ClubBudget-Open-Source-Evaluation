# REWARD_RULE_NOTES.md — Required submission

Complete this file with your own actual examples and results. Do not leave prompts unanswered.

## 1. Worked points calculation
- Example parameters:
  - Purchase amount: `259,900` paise (₹2,599.00)
  - Rule: `points_per_100_rupees = 1`
  - Bonus: `bonus_percent = 10`
  - Cap: `cap_points = 100`
- Calculation steps:
  1. Base points calculation:
     $$\text{base\_points} = \lfloor \frac{\text{amount\_paise}}{10000} \rfloor \times \text{points\_per\_100\_rupees} = \lfloor \frac{259900}{10000} \rfloor \times 1 = 25 \times 1 = 25$$
     *Rounding rule:* Integer floor division (`259900 // 10000 = 25`). Any fractional paise or rupees below the full ₹100 boundary are discarded.
  2. Bonus points calculation:
     $$\text{bonus\_points} = \lfloor \frac{\text{base\_points} \times (100 + \text{bonus\_percent})}{100} \rfloor = \lfloor \frac{25 \times 110}{100} \rfloor = \lfloor \frac{2750}{100} \rfloor = 27$$
     *Rounding rule:* Integer floor division (`2750 // 100 = 27`). Fractional bonus points are discarded.
  3. Cap application:
     $$\text{final\_points} = \min(\text{bonus\_points}, \text{cap\_points}) = \min(27, 100) = 27$$
     *Rule:* Final points cannot exceed `cap_points`. Since 27 <= 100, the cap is not exceeded.
- Actual output: `27` points (as demonstrated in `python -m main`).

## 2. Partial-refund example
- Initial state:
  - Original purchase event: `amount_paise = 100000` (₹1,000.00), awarded `10` points.
  - Initial account balance: `points_balance = 10`.
  - Transaction state: `awarded_points = 10`, `refunded_paise = 0`, `reversed_points = 0`.
- Refund event:
  - `type = "refund_processed"`, `amount_paise = 50000` (₹500.00, 50% partial refund).
- Reversal calculation:
  1. Update refunded amount:
     $$\text{new\_refunded\_paise} = 0 + 50000 = 50000 \le 100000 \quad (\text{valid refund})$$
  2. Target cumulative reversed points:
     $$\text{should\_reverse} = \lfloor \frac{\text{awarded\_points} \times \text{new\_refunded\_paise}}{\text{amount\_paise}} \rfloor = \lfloor \frac{10 \times 50000}{100000} \rfloor = 5$$
  3. Incremental point deduction ($\Delta$):
     $$\Delta = \text{should\_reverse} - \text{previously\_reversed} = 5 - 0 = 5$$
  4. Balance update:
     $$\text{new\_balance} = \max(0, \text{points\_balance} - \Delta) = 10 - 5 = 5$$
     $$\text{reversed\_points} = 0 + 5 = 5$$
  5. Audit ledger entry appended:
     ```python
     {
         "event_id": "E2",
         "type": "refund_processed",
         "points_delta": -5
     }
     ```
- Resulting account state:
  - `points_balance`: `5`
  - `transactions['T']['refunded_paise']`: `50000`
  - `transactions['T']['reversed_points']`: `5`

## 3. Three edge cases
1. Boundary paise amount immediately below 100 rupees (`amount_paise = 9999`):
   - Input: `calculate_points(9999, points_per_100_rupees=1)`
   - Expected behaviour: Discard partial rupee amounts using floor division and return `0` points.
   - Actual observed result: `0`
   - Verifying test: `test_integer_floor_points_calculation[9999-0_0]`
2. Promotional cap set to zero (`cap_points = 0`):
   - Input: `calculate_points(50000, points_per_100_rupees=1, cap_points=0)`
   - Expected behaviour: A cap of 0 strictly caps total points to `0`, rather than being ignored as a falsy value.
   - Actual observed result: `0`
   - Verifying test: `test_cap_zero_is_respected`
3. Cumulative excess refund rejected:
   - Input: Account with ₹1,000 purchase receives first refund of ₹400 (accepted), second refund of ₹500 (accepted), and third refund of ₹200 (cumulative ₹1,100 > ₹1,000).
   - Expected behaviour: The third refund is rejected as excess. Transaction retains `refunded_paise = 90000` and balance remains `1`.
   - Actual observed result: `refunded_paise = 90000`, `points_balance = 1`, no third ledger entry.
   - Verifying test: `test_regression_cumulative_partial_refunds_and_excess_rejection`

## 4. Assumptions and limitations
- Rounding assumptions: All currency to point conversions use integer floor arithmetic (`//`). Fractional paise and fractional bonus points are never rounded up.
- Missing-field handling: Events missing `event_id`, `type`, or `transaction_id` are safely ignored without altering the account state or raising unhandled exceptions.
- Repeat-alert threshold assumptions: Groups are flagged only when `len(transaction_ids) > threshold` (strictly greater than). Grouping keys are formatted as strings for deterministic dictionary ordering.
- Non-negative balances: Reversals clamp point deductions to the available points balance, preventing negative balances if points were already redeemed.
