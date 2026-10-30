# REWARD_RULE_NOTES.md — Required submission

## 1. Worked points calculation
Purchase of **1234567 paise** (₹12,345.67) with rules `points_per_100_rupees=5`, `bonus_percent=25`, `cap_points=500`:

| Step | How | Value |
|---|---|---|
| Full ₹100s | `1234567 // 10000` (round down; the leftover 34567 paise earns nothing) | 123 |
| Base points | `123 × 5` | 615 |
| Add bonus | `615 × (100 + 25) // 100` = `76875 // 100` (round down) | 768 |
| Apply cap (last) | `min(768, 500)` | **500** |

When I ran it: `calculate_points(1234567, 5, 25, 500)` gave `500`, and without the cap it gave `768`.

Demo check: `calculate_points(259900, 1, 10, 100)` gives `27` (25 base, then 25 × 110 // 100 = 27). The starter code printed 28, because `round(25.99)` gave 26.

## 2. Partial-refund example
Same rules (5 points per ₹100, 25% bonus, cap 500). Purchase `TX-9` of **259900 paise**: base `25 × 5 = 125`, plus bonus `125 × 125 // 100 = 156`. So **156 points**, and the balance is 156.

Refund `EV-2` of **100000 paise**:
- total refunded so far is 100000, which is not more than 259900, so it's accepted
- points that should be taken back in total: `156 × 100000 // 259900 = 60`
- already taken back: 0, so take back **60** now, and the balance becomes **96**

Ledger line (from running it):
```
{'event_id': 'EV-2', 'type': 'refund_processed', 'transaction_id': 'TX-9',
 'amount_paise': 100000, 'points_delta': -60, 'balance_after': 96}
```

A second refund, `EV-3` of 159900 paise, makes the total 259900 (the full purchase). Points that should be taken back in total: `156 × 259900 // 259900 = 156`. 60 were already taken, so take back 96 more, and the balance becomes **0**. If I had worked out each refund on its own instead, I'd get 60 + 95 = 155, and 1 point would be left over by mistake.

## 3. Three edge cases
1. **Refunding 1 paisa too much.**
   - Input: after the two refunds above, another refund `EV-4` of 1 paise.
   - Expected: rejected, because the total would be 259901, which is more than 259900.
   - Actual: the balance stays 0 and the ledger still has 3 lines.
   - Tests: `test_cumulative_refunds_cannot_exceed_purchase` and `test_invalid_or_excess_refund_does_not_change_account[100001]`.
2. **A boolean as the amount.**
   - Input: a refund with `amount_paise=True`.
   - Expected: rejected. Python treats `True` as an `int` (equal to 1), but it isn't a real amount.
   - Actual: `refunded_paise` stays 0.
   - Test: `test_invalid_or_excess_refund_does_not_change_account[True]`.
3. **Cap of 0 and negative bonus.**
   - Input: `calculate_points(50000, 1, cap_points=0)` and `calculate_points(100000, 1, -100)`.
   - Expected: 0 for both. A cap of 0 is still a cap, and a negative bonus is an invalid rule.
   - Actual: `0` and `0`.
   - Tests: `test_cap_zero_is_respected` and `test_invalid_rule_values_award_zero`.

## 4. Assumptions and limitations
- **Rounding:** always round down. That applies to the full ₹100s, the bonus, and the refund points. The cap goes on after the bonus. Refund points are worked out from the running total, so a full refund always takes back everything.
- **Missing fields:** events with no `event_id` or `transaction_id`, or an amount that isn't a positive whole number, are ignored and not marked as processed, so a fixed version can be sent again. If a rule is missing, the defaults are 1 point per ₹100, 0% bonus and no cap.
- **Event types:** only `purchase_captured` and `refund_processed` (exact spelling) change the account. Declined, pending or unknown events do nothing.
- **Repeat alerts:**
  - A group alerts when it has *more than* `threshold` transactions with the same account, date and amount. A threshold below 1 counts as 1.
  - The threshold can be changed (stretch item): the default is 2, it can come from `repeat_alert_threshold` in a config dict, or you can use `python -m main --threshold N`.
  - Rows with missing fields or amount ≤ 0 are skipped, which gives 48 alert groups on `data/records.json`.
  - Alerts are marked `needs_review` and never block a payment.
- **Not handled:** spent points aren't tracked (refunds only take back what's in the balance), and amounts sent as strings are rejected rather than converted.
