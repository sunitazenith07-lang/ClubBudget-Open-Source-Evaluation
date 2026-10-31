# REWARD_RULE_NOTES.md — Required submission

Complete this file with your own actual examples and results. Do not leave prompts unanswered.

## 1. Worked points calculation
Show one purchase calculation from amount in paise through base points, bonus and cap. State the rounding rule at each step and include the actual output.

**Example: 259900 paise purchase**
- **Input:** amount_paise = 259900, points_per_100_rupees = 1, bonus_percent = 10, cap_points = 100
- **Step 1 — Base points (floor division):**
  base = (259900 // 10000) × 1 = 25 × 1 = 25 points
  *(Rounding rule: floor of paise/10000, i.e., integer division //)*
- **Step 2 — Bonus points:**
  bonus = (25 × (100 + 10)) // 100 = (25 × 110) // 100 = 2750 // 100 = 27 points
  *(Rounding rule: floor of base × (100 + bonus_percent) / 100)*
- **Step 3 — Apply cap:**
  points = min(27, 100) = 27
  *(cap_points = 100, so no cap applied since 27 < 100)*
- **Final result:** 27 points awarded
- **Actual output from demo:** Points example: 27

## 2. Partial-refund example
Show the points originally awarded, the refund amount, how the reversal is calculated, the resulting balance, and the relevant ledger entry.

**Example: Partial refund of 50000 paise from a 100000 paise purchase**
- **Original purchase:** 100000 paise → 10 points awarded (100000 // 10000 = 10)
- **Refund amount:** 50000 paise (50% of purchase)
- **Refunded paise accumulated:** 50000
- **Points reversal calculation:**
  should_reverse = 10 × 50000 // max(1, 100000) = 10 × 50000 // 10000 = 500000 // 10000 = 5 points
- **Delta (points to reverse):** 5 - 0 = 5 points (since no previous reversals)
- **Resulting balance:** 10 - 5 = 5 points remaining
- **Transaction state:** refunded_paise = 50000, reversed_points = 5
- **Ledger entry:** `{'event_id': 'R', 'type': 'refund_processed', 'points_delta': -5}`

## 3. Three edge cases

**Edge case 1:**
- **Input:** `calculate_points(9999, 1)` — amount just below 10000 paise
- **Expected behaviour:** Should return 0 (floor of 0.9999 = 0)
- **Actual observed result:** Returns 0 (after fix)
- **Test that verifies it:** `test_points_use_floor` includes this case

**Edge case 2:**
- **Input:** `calculate_points(50000, 1, cap_points=0)` — cap explicitly set to zero
- **Expected behaviour:** Should return 0 (cap of zero means zero points)
- **Actual observed result:** Returns 0 (after fix; before fix returned 5)
- **Test that verifies it:** `test_cap_zero_is_respected`

**Edge case 3:**
- **Input:** `apply_reward_event(account, {'event_id': 'E1', 'type': 'purchase_declined', 'transaction_id': 'T', 'amount_paise': 100000}, {'points_per_100_rupees': 1})`
- **Expected behaviour:** 0 points awarded, transactions should be empty dict
- **Actual observed result:** 0 points, {} transactions (test passes)
- **Test that verifies it:** `test_unrecognized_or_declined_events_do_not_award_points`

## 4. Assumptions and limitations
Document rounding assumptions, missing-field handling, repeat-alert threshold assumptions, and any unresolved issue.

- **Rounding assumption:** All calculations use integer floor division (//). No floating-point arithmetic is used.
- **Missing fields:** Missing `amount_paise` defaults to 0; missing `bonus_percent` defaults to 0; missing `cap_points` means no cap.
- **Refund assumptions:** Refund amount must be a valid positive integer; `True`/`False` are rejected; refund cannot exceed original purchase amount.
- **Repeat-alert threshold:** The default threshold of 2 means 3+ same-account/date/amount transactions trigger an alert.
- **Unresolved issue:** None — all visible tests pass. Future work could include configurable threshold and CSV statement generation.