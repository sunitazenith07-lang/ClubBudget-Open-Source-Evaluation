# REWARD_RULE_NOTES.md — Required submission

## 1. Worked points calculation

**Example purchase:**

- Purchase amount: `259900` paise (₹2,599)
- `points_per_100_rupees = 1`
- `bonus_percent = 10`
- `cap_points = 100`

**Step 1: Calculate base points**

Every ₹100 equals 10,000 paise.

`259900 // 10000 = 25`

`base_points = 25 * 1 = 25`

The remaining 9,900 paise are ignored. The calculation uses floor division, not rounding to the nearest integer.

**Step 2: Calculate bonus points**

`bonus_points = (25 * (100 + 10)) // 100`

`bonus_points = 2750 // 100 = 27`

Any fractional point is discarded using integer floor division.

**Step 3: Apply the cap**

`final_points = min(27, 100) = 27`

**Final result: 27 points awarded.**

The earlier implementation used `round()` for the base calculation. That could incorrectly increase the points. The updated implementation uses integer floor division.

## 2. Partial-refund example

**Original purchase:**

- Purchase amount: `100000` paise (₹1,000)
- Points awarded: 10
- Initial account balance: 10 points
- `refunded_paise = 0`
- `reversed_points = 0`

**Refund event:**

- `event_id`: `EV-REF-40`
- `type`: `refund_processed`
- `transaction_id`: `TX-1001`
- Refund amount: `40000` paise (₹400)

**Calculation:**

1. The refund is positive and does not exceed the original purchase amount.
2. New cumulative refunded amount:

   `0 + 40000 = 40000` paise

3. Calculate the total points that should be reversed:

   `total_should_reverse = (10 * 40000) // 100000 = 4`

4. Calculate the new reversal:

   `delta = 4 - 0 = 4` points

5. Check the available balance:

   `actual_delta = min(4, 10) = 4`

6. Updated balance:

   `10 - 4 = 6` points

**Ledger entry:**

```json
{
  "event_id": "EV-REF-40",
  "type": "refund_processed",
  "points_delta": -4
}
```

**Updated transaction:**

- `refunded_paise = 40000`
- `reversed_points = 4`

The account now has 6 points.

## 3. Three edge cases

### Edge case 1: Purchase below ₹100

- **Input:** `amount_paise = 9999`, `points_per_100_rupees = 1`
- **Expected:** 0 points because the purchase is below 10,000 paise.
- **Actual:** `calculate_points(9999, 1)` returned 0.
- **Test:** `tests/test_acceptance_matrix.py::test_integer_floor_points_calculation[9999-0_0]`

### Edge case 2: Zero promotional cap

- **Input:** `amount_paise = 50000`, `points_per_100_rupees = 1`, `bonus_percent = 50`, `cap_points = 0`
- **Expected:** 0 points because the cap is zero.
- **Actual:** `calculate_points(50000, 1, 50, 0)` returned 0.
- **Test:** `tests/test_contract.py::test_cap_zero_is_respected`

### Edge case 3: Replayed purchase event

- **Input:** Apply the same captured purchase event twice, with `event_id = EV-IDEMP-01` and `amount_paise = 25000`.
- **Expected:** The first event awards 2 points. Replaying it must not add points or create another ledger entry.
- **Actual:** Balance remained 2 points, with one ledger entry and one processed event ID.
- **Test:** `tests/test_acceptance_matrix.py::test_purchase_event_replay_is_idempotent`

## 4. Assumptions and limitations

### Rounding assumptions

- Base points use integer floor division by 10,000 paise.
- Bonus points also use integer floor division.
- Refund reversals use cumulative proportional calculation, so multiple partial refunds do not independently lose fractional remainders.
- No floating-point arithmetic is used for points calculations.

### Missing and invalid fields

- Events need valid identifiers to be processed.
- Invalid amounts, including negative values, floats, strings and booleans, are rejected.
- Unknown transactions are not refunded.
- Invalid events should not change the account balance or ledger.

### Repeat-alert threshold

- Transactions are grouped by account, date and amount.
- An alert is generated when the matching count is greater than the configured threshold.
- Alerts are only for human review. They do not block transactions or automatically label anyone as fraudulent.

### Known limitation: Insufficient points during refunds

If a customer has already spent some awarded points outside this service, a refund may require reversing more points than the current balance.

The implementation prevents a negative balance. It records the full calculated reversal in `reversed_points`, but the ledger records only the points actually deducted from the available balance.

For example, if 10 points need to be reversed but only 2 remain, the balance becomes 0 and the ledger records `points_delta = -2`. The remaining 8 points are not automatically recovered.

A production system would need a clear business rule for handling this remaining amount.