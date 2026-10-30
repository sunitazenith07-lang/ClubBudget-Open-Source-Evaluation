# REWARD_RULE_NOTES.md — Required submission

## 1. Worked points calculation
Purchase of **1234567 paise** (₹12,345.67) with rules `points_per_100_rupees=5`, `bonus_percent=25`, `cap_points=500`:

| Step | Formula (integer arithmetic) | Value |
|---|---|---|
| Whole ₹100 units | `1234567 // 10000` (floor; the 34567-paise remainder earns nothing) | 123 |
| Base points | `123 × 5` | 615 |
| Bonus | `615 × (100 + 25) // 100` = `76875 // 100` (floor) | 768 |
| Cap (applied last) | `min(768, 500)` | **500** |

Actual output: `calculate_points(1234567, 5, 25, 500)` → `500`; without the cap → `768`.

Demo check: `calculate_points(259900, 1, 10, 100)` → `27` (25 base, 25 × 110 // 100 = 27). The starter printed 28 because `round(25.99)` gave 26.

## 2. Partial-refund example
Rules `5 / 25% / cap 500`. Purchase `TX-9` of **259900 paise**: base `25 × 5 = 125`, bonus `125 × 125 // 100 = 156` → **156 points awarded**, balance 156.

Refund `EV-2` of **100000 paise**:
- cumulative refunded = 100000 (≤ 259900, so accepted)
- should have reversed = `156 × 100000 // 259900 = 60`
- reverse now = 60 − 0 already reversed = **60** → balance **96**

Ledger entry (actual):
```
{'event_id': 'EV-2', 'type': 'refund_processed', 'transaction_id': 'TX-9',
 'amount_paise': 100000, 'points_delta': -60, 'balance_after': 96}
```

A second refund `EV-3` of 159900 paise brings the total to 259900. Should have reversed = `156 × 259900 // 259900 = 156`, so it reverses 156 − 60 = **96** → balance **0**. Rounding each refund on its own would have given 60 + 95 = 155 and left 1 point.

## 3. Three edge cases
1. **Over-refund by 1 paisa.** Input: after the two refunds above, refund `EV-4` of 1 paise. Expected: rejected (total would be 259901 > 259900). Actual: balance stays 0, ledger still has 3 entries. Verified by `test_cumulative_refunds_cannot_exceed_purchase` and `test_invalid_or_excess_refund_does_not_change_account[100001]` (one paisa over a 100000 purchase).
2. **Boolean amount.** Input: refund with `amount_paise=True`. Expected: rejected; `True` is an `int` in Python but is not an amount. Actual: `refunded_paise` stays 0. Verified by `test_invalid_or_excess_refund_does_not_change_account[True]`.
3. **Cap of zero / negative bonus.** Input: `calculate_points(50000, 1, cap_points=0)` and `calculate_points(100000, 1, -100)`. Expected: 0 in both cases (zero cap is a real cap; a negative bonus is an invalid rule). Actual: `0` and `0`. Verified by `test_cap_zero_is_respected` and `test_invalid_rule_values_award_zero`.

## 4. Assumptions and limitations
- **Rounding:** floor at every step: whole ₹100 units, the bonus, and the refund reversal. The cap is applied after the bonus. Reversal is recomputed from the cumulative refund so a full refund always reverses everything awarded.
- **Missing fields:** events with no `event_id` or `transaction_id`, or with a non-integer / non-positive amount, are ignored and not marked as processed, so they can be resent once corrected. Missing rule keys default to 1 point per ₹100, 0% bonus and no cap.
- **Event types:** only `purchase_captured` and `refund_processed` (exact spelling) change an account; declined, pending and unknown types do nothing.
- **Repeat alerts:** a group alerts when it has *more than* `threshold` transactions with the same account, date and amount. A threshold below 1 is treated as 1. The threshold is configurable (stretch item): default 2, read from `repeat_alert_threshold` in a config dict, or set with `python -m main --threshold N`. Rows with missing keys or amount ≤ 0 are skipped, giving 48 alert groups on `data/records.json`. Alerts are labelled `needs_review` and never block a transaction.
- **Unresolved:** redeemed points are not modelled (reversal is clamped to the current balance); numeric strings are rejected rather than parsed.
