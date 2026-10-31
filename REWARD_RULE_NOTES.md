<!-- DRAFT: resolve every [VERIFY] and [FILL] marker with your own run/edits, then delete this comment. -->
# REWARD_RULE_NOTES.md

## 1. Worked points calculation
Purchase of 259900 paise (₹2599), rules: 1 point per ₹100, 10% bonus, cap 100.
1. Base: `259900 // 10000 = 25` (25.99 floored), then `25 * 1 = 25`.
2. Bonus: `25 * (100 + 10) // 100 = 2750 // 100 = 27` (27.5 floored).
3. Cap applied last: `min(27, 100) = 27`.
Actual output: `python -m main` prints `Points example: 27` [VERIFY]. The starter printed 28 because `round()` made the base 26.

## 2. Partial-refund example
- Points awarded: 27 (purchase above, transaction `T`).
- Refund: 100000 paise.
- Reversal: `27 * 100000 // 259900 = 2700000 // 259900 = 10` (10.39 floored).
- Balance: 27 - 10 = **17**. A second refund of 159900 (total 259900) brings the cumulative reversal to exactly 27 and the balance to 0.
- Ledger entry: `{'event_id': 'R1', 'type': 'refund_processed', 'transaction_id': 'T', 'points_delta': -10}`
- Verified by `test_split_refunds_reverse_exactly_awarded` [VERIFY].

## 3. Three edge cases
1. **Input:** capture of 9999 paise. **Expected:** 0 points. **Actual:** 0. **Test:** `test_integer_floor_points_calculation[9999-0_0]`.
2. **Input:** second refund that pushes the total above the purchase. **Expected:** rejected, no state change. **Actual:** rejected. **Test:** `test_cumulative_over_refund_rejected_on_second_event`.
3. **Input:** event with a missing `event_id`. **Expected:** rejected, not stored as `None`. **Actual:** rejected. **Test:** `test_missing_event_id_is_rejected_and_not_recorded`.

## 4. Assumptions and limitations
- **Rounding:** floor at every step. Reversal is cumulative floor, so a partial refund can leave the customer a fraction of a point more, and a full refund reverses exactly what was awarded.
- **Missing fields:** events without a non-empty string `event_id` or `transaction_id` are rejected. Records missing account, date or amount are skipped by the repeat alert.
- **Repeat threshold:** an alert needs more than `threshold` matching transactions (`>`, pinned by the tests). A threshold below 1 is treated as 1. Alerts are for human review only.
- **Zero-amount purchases:** rejected by my assumption, not stated in the brief.
- **Unresolved:** refunds that arrive before their purchase are not queued.