# REWARD_RULE_NOTES.md — Required submission

## 1. Worked points calculation
- **Purchase Amount:** 259,900 Paise (₹2,599.00)
- **Rules:** 1 point per ₹100, 10% bonus, 100 point cap
- **Step 1 (Base points):** `259900 // 10000 = 25` base units * 1 = 25 points.
- **Step 2 (Bonus):** `25 * (100 + 10) // 100 = 2750 // 100 = 27` points.
- **Step 3 (Cap):** `min(27, 100) = 27` points.
- **Output:** 27 points awarded.

## 2. Partial-refund example
- **Original Purchase:** 100,000 Paise (₹1,000), awarded 10 points.
- **Partial Refund:** 30,000 Paise (₹300).
- **Reversal Calculation:** `10 * 30000 // 100000 = 3` points reversed.
- **New Balance:** `10 - 3 = 7` points.
- **Ledger Entry:** `{'event_id': 'E2', 'type': 'refund_processed', 'points_delta': -3}`.
*(Verified for multi-step cumulative returns in `test_multiple_partial_refunds_cumulative_reversal` where ₹200 then ₹300 refunds deduct -4 then -6 points cleanly).*

## 3. Three edge cases
1. **Sub-100 Rupee Purchase:** Amount = 9,999 paise yields 0 base points (`test_integer_floor_points_calculation`).
2. **Zero Cap Enforcement:** `cap_points = 0` awards exactly 0 points (`test_cap_zero_is_respected`).
3. **Cumulative Excess Refund:** Total refund exceeding order amount is safely ignored without balance changes (`test_cumulative_refund_exceeding_purchase_ignored`).

## 4. Assumptions and limitations
- Financial calculations use integer paise and floor division to prevent sub-paise fractional leakage.
- Repeat-transaction detection flags alerts strictly for human auditing without interrupting payment authorization.