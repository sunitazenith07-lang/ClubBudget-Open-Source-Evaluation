# REWARD_RULE_NOTES.md — Required submission

## 1. Worked points calculation
Worked example: `amount_paise = 259900`, `points_per_100_rupees = 1`, `bonus_percent = 10`, `cap_points = 100`.

- Step 1: Convert paise to 100-rupee blocks using integer floor division: `259900 // 10000 = 25`
- Step 2: Base points: `25 * 1 = 25`
- Step 3: Apply bonus: `25 * (100 + 10) // 100 = 27`
- Step 4: Cap check: `min(27, 100) = 27`
- Actual output: `calculate_points(259900, 1, 10, 100) == 27`

This matches the demo output from `python -m main`: `Points example: 27`.

## 2. Partial-refund example
Worked example: a 100,000-paise purchase with a 1-point-per-₹100 rule awards 10 points.

- Original award: `calculate_points(100000, 1) = 10`
- Refund amount: `50000` paise
- Proportional reversal formula: `min(awarded, awarded * refunded_paise // amount_paise) = min(10, 10 * 50000 // 100000) = 5`
- Resulting balance: `10 - 5 = 5`
- Related ledger entry: `{'event_id': 'R', 'type': 'refund_processed', 'points_delta': -5}`

This is verified by the refund replay and partial refund tests, which confirm the balance becomes 5 and the refunded total is tracked correctly.

## 3. Three edge cases
1. Zero-cap purchase
   - Input: `amount_paise = 50000`, `points_per_100_rupees = 2`, `bonus_percent = 50`, `cap_points = 0`
   - Expected behaviour: zero points because cap is zero
   - Actual observed result: `0`
   - Verification: `test_bonus_and_cap_matrix`

2. Duplicate purchase event replay
   - Input: same `event_id` and same `transaction_id` sent twice for a 25,000-paise purchase
   - Expected behaviour: second event is ignored; balance stays at the original award
   - Actual observed result: balance stays at `2`, `processed_event_ids == ['E1']`, ledger length remains `1`
   - Verification: `test_purchase_event_replay_is_idempotent`

3. Excess refund is ignored
   - Input: purchase of `100000` paise, then refund of `150000` paise
   - Expected behaviour: no refund applied, points balance remains `10`
   - Actual observed result: `refunded_paise == 0`, balance remains `10`
   - Verification: `test_invalid_or_excess_refund_does_not_change_account`

## 4. Assumptions and limitations
- Rounding is floor-based for each 10,000-paise block before the bonus is applied.
- Invalid or missing identifiers are ignored rather than processed.
- Repeat alerts only group rows when the same `account_id`, `date`, and `amount_paise` occur in the same threshold window; rows missing identifiers are skipped.
- The final implementation intentionally rejects malformed or out-of-range refund attempts instead of silently modifying the account state.
- No unresolved functional issues remained in the final suite; all verified tests passed.
