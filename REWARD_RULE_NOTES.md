# REWARD_RULE_NOTES.md - Required submission

Complete this file with your own actual examples and results. Do not leave prompts unanswered.

## 1. Worked points calculation
Show one purchase calculation from amount in paise through base points, bonus and cap. State the rounding rule at each step and include the actual output.

- **Input:**
  - `amount_paise`: 259,900 paise (Rs 2,599.00)
  - `points_per_100_rupees`: 1
  - `bonus_percent`: 10
  - `cap_points`: 100
- **Step 1 - Base Points:**
  - Formula: `floor(amount_paise / 10000) * points_per_100_rupees`
  - Calculation: `floor(259900 / 10000) * 1 = 25 * 1 = 25`
  - Rounding rule: Strictly integer floor division (`259900 // 10000`), discarding fractional paise.
- **Step 2 - Bonus Points:**
  - Formula: `floor(base_points * (100 + bonus_percent) / 100)`
  - Calculation: `floor(25 * (100 + 10) / 100) = floor(25 * 110 / 100) = floor(2750 / 100) = 27`
  - Rounding rule: Strictly integer floor division (`// 100`).
- **Step 3 - Cap Application:**
  - Formula: `min(bonus_points, cap_points)`
  - Calculation: `min(27, 100) = 27`
- **Actual Output:** `27` points.

## 2. Partial-refund example
Show the points originally awarded, the refund amount, how the reversal is calculated, the resulting balance, and the relevant ledger entry.

- **Original Purchase:**
  - Transaction ID: `T-100`
  - `amount_paise`: 100,000 paise (Rs 1,000.00)
  - `awarded_points`: 10 points
  - `points_balance`: 10 points
- **Refund Event:**
  - Event ID: `REF-001`
  - `amount_paise`: 50,000 paise (Rs 500.00)
- **Reversal Calculation:**
  - `cumulative_refunded_paise`: 50,000
  - `should_reverse = min(awarded_points, awarded_points * refunded_paise // amount_paise)`
  - `should_reverse = 10 * 50000 // 100000 = 5` points
  - `delta = should_reverse - previously_reversed = 5 - 0 = 5` points
  - `points_balance = 10 - 5 = 5` points
- **Resulting Transaction State:**
  - `refunded_paise`: 50,000
  - `reversed_points`: 5
- **Ledger Entry Added:**
  `{'event_id': 'REF-001', 'type': 'refund_processed', 'points_delta': -5}`

## 3. Three edge cases
For each, provide input, expected behaviour, actual observed result, and the test that verifies it.

1. **Amount immediately below 100-rupee boundary:**
   - Input: `amount_paise = 9999`, `points_per_100_rupees = 1`
   - Expected: 0 points (99.99 rupees has zero full 100-rupee blocks).
   - Actual: 0 points.
   - Verifying test: `tests/test_acceptance_matrix.py::test_integer_floor_points_calculation[9999-0_0]`

2. **Cap explicitly set to zero:**
   - Input: `amount_paise = 50000`, `points_per_100_rupees = 1`, `cap_points = 0`
   - Expected: 0 points (cap of 0 strictly restricts points to 0).
   - Actual: 0 points.
   - Verifying test: `tests/test_contract.py::test_cap_zero_is_respected`

3. **Boolean / Non-numeric refund value:**
   - Input: `amount_paise = True` or `None`
   - Expected: Ignored; no points reversed, `refunded_paise` remains 0.
   - Actual: 0 paise refunded, points balance untouched.
   - Verifying test: `tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account[True]`

## 4. Assumptions and limitations
- **Integer arithmetic:** All monetary calculations use paise and integer arithmetic (`//`). Fractional paise and floats are treated as invalid.
- **Identifier requirements:** Events must contain non-empty `event_id` and `transaction_id` strings to be processed into the ledger or state.
- **Repeat alerts:** Alerts in `flag_repeat_transactions` flag candidate groups strictly for human review based on `(account_id, date, amount_paise)` matches exceeding `threshold`. They do not block transactions.
- **No negative balance:** Refunds never reduce account points balance below zero.
