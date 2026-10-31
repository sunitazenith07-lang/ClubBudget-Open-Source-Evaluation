# REWARD_RULE_NOTES.md

## 1. Worked points calculation

Example purchase:

- **Purchase amount:** 25,000 paise (₹250.00)
- **Points per ₹100:** 2
- **Bonus:** 50%
- **Points cap:** 6

**Step 1 — Calculate base points**

The calculation uses integer floor division:

`base_points = (amount_paise // 10000) * points_per_100_rupees`

`base_points = (25000 // 10000) * 2`

`base_points = 2 * 2 = 4`

**Step 2 — Apply the bonus**

`bonus_points = base_points * (100 + bonus_percent) // 100`

`bonus_points = 4 * 150 // 100`

`bonus_points = 6`

The result is rounded down using integer division.

**Step 3 — Apply the cap**

`final_points = min(bonus_points, cap_points)`

`final_points = min(6, 6) = 6`

**Actual output: 6 points.**

The cap is applied after the bonus. A cap of zero is also respected and results in zero points.

## 2. Partial-refund example

Example purchase and refund:

- **Original purchase:** 100,000 paise (₹1,000.00)
- **Points per ₹100:** 1
- **Original points awarded:** 10
- **Refund amount:** 50,000 paise (₹500.00)

**Step 1 — Calculate the original award**

`100000 // 10000 = 10`

The account receives 10 points.

**Step 2 — Calculate the proportional reversal**

`should_reverse = awarded_points * total_refunded_paise // original_amount_paise`

`should_reverse = 10 * 50000 // 100000`

`should_reverse = 5`

**Step 3 — Calculate the resulting balance**

`points_balance = 10 - 5 = 5`

The account retains 5 points.

**Relevant ledger entry:**

```python
{
    'event_id': 'E2',
    'type': 'refund_processed',
    'points_delta': -5
}
```

The refund is recorded as a negative points change. Replayed event IDs are ignored, and refunds exceeding the remaining refundable amount are rejected.

## 3. Three edge cases

### Edge case 1 — Purchase amount below the next ₹100 boundary

- **Input:** 19,999 paise, with 1 point per ₹100.
- **Expected behaviour:** Award 1 point using floor division.
- **Actual observed result:** Passed; 1 point is calculated.
- **Test:** `test_points_use_floor`

### Edge case 2 — Replaying the same purchase event

- **Input:** The same purchase event with event ID `E1` is processed twice.
- **Expected behaviour:** Award points only once and keep one processed event ID.
- **Actual observed result:** Passed; the balance remains 2 points and the processed event ID appears only once.
- **Test:** `test_purchase_event_once`

### Edge case 3 — Refund exceeds the original purchase amount

- **Input:** A purchase of 100,000 paise followed by a refund of 150,000 paise.
- **Expected behaviour:** Ignore the excessive refund without changing the refunded amount or points balance.
- **Actual observed result:** Passed; the original 10-point balance remains unchanged.
- **Test:** `test_invalid_or_excess_refund_ignored`

## 4. Assumptions and limitations

- **Rounding:** Points are calculated using integer floor division. Fractional points are rounded down rather than rounded to the nearest integer.
- **Cap:** The points cap is applied after the bonus. A cap of zero is valid and results in zero points.
- **Missing purchase fields:** A purchase with a missing
