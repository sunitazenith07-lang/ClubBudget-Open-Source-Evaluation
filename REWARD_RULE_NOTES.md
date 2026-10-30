# REWARD_RULE_NOTES.md

## 1. Worked points calculation

Consider a captured purchase of ₹500.

**Input:**

- `amount_paise = 50000`
- `points_per_100_rupees = 1`
- `bonus_percent = 20`
- `cap_points = 5`

**Step 1: Calculate base points**

The implementation uses integer floor division:

`base_points = amount_paise // 10000`

`base_points = 50000 // 10000 = 5`

So, the customer earns 5 base points.

**Step 2: Calculate bonus points**

`bonus = base_points * bonus_percent // 100`

`bonus = 5 * 20 // 100 = 1`

The bonus is 1 point.

**Step 3: Add bonus points**

`total_points = 5 + 1 = 6`

**Step 4: Apply the reward cap**

The configured cap is 5 points.

`final_points = min(6, 5) = 5`

**Final calculated output:**

```text
5
```

The rounding rule is integer floor division at each calculation stage. No floating-point rounding is used. The cap is applied after adding the bonus.

## 2. Partial-refund example

Consider the same ₹500 purchase, for which the customer originally received 5 points after applying the reward cap.

**Original purchase:**

- Purchase amount: ₹500
- Awarded points: 5
- Initial points balance after purchase: 5

Now, the customer receives a partial refund of ₹250.

**Refund calculation:**

- Original purchase amount: 50000 paise
- Refund amount: 25000 paise
- Total refunded amount: 25000 paise
- Originally awarded points: 5

The implementation calculates the proportional reversal using:

`target_reversal = awarded_points * total_refunded // original_amount`

`target_reversal = 5 * 25000 // 50000`

`target_reversal = 2`

Therefore, 2 points are reversed.

**Resulting balance:**

`balance = 5 - 2 = 3`

**Relevant ledger entries:**

```python
[
    {
        "event_id": "purchase_001",
        "type": "purchase_captured",
        "points_delta": 5
    },
    {
        "event_id": "refund_001",
        "type": "refund_processed",
        "points_delta": -2
    }
]
```

**Final result:**

- Original points awarded: 5
- Points reversed: 2
- Remaining balance: 3

The calculation uses cumulative refunded amounts, so multiple partial refunds are calculated against the original purchase rather than independently rounding each refund.

## 3. Three edge cases

### 1. Negative purchase amount

**Input:**

```python
amount_paise = -10000
```

**Expected behaviour:**

A negative purchase amount should be rejected and should not generate reward points.

**Actual observed result:**

The regression test passed. The `valid_int()` check rejects negative values.

**Test:** `test_negative_amount`

### 2. Zero reward cap

**Input:**

```python
amount_paise = 50000
points_per_100_rupees = 1
bonus_percent = 20
cap_points = 0
```

**Expected behaviour:**

Even if the calculated points are positive, the final reward should be zero because the configured cap is zero.

**Actual observed result:**

The regression test passed. The implementation correctly applies the zero cap using `cap_points is not None`.

**Test:** `test_zero_cap`

### 3. Duplicate event ID

**Input:**

Two events with the same event ID are submitted for processing.

**Expected behaviour:**

The second event should be ignored so that the same purchase or refund is not processed twice.

**Actual observed result:**

The regression test passed. The implementation checks `processed_event_ids` before processing an event.

**Test:** `test_duplicate_event`

The complete final test suite reported:

```text
221 passed in 0.46s
```

## 4. Assumptions and limitations

**Rounding assumptions**

- Purchase amounts are stored in paise.
- One reward calculation unit represents ₹100, or 10000 paise.
- Only complete ₹100 units contribute to base points.
- Integer floor division is used for base points, bonus points, and proportional refund calculations.
- The reward cap is applied after the bonus calculation.
- A cap of zero is valid.

**Missing-field handling**

- Missing or invalid event IDs and transaction IDs cause the event to be rejected.
- Missing or invalid purchase/refund amounts are rejected.
- Missing reward rule values use defaults where provided: 1 point per ₹100, 0% bonus, and no cap.
- Invalid rule values result in zero from `calculate_points()`.
- Unknown transaction refunds are ignored.

**Repeat-alert threshold assumptions**

- Transactions are grouped by account ID, date, and amount.
- The default threshold is 2.
- A group is flagged only when its transaction count is greater than the threshold.
- Therefore, with the default threshold, at least 3 matching transactions are required to generate an alert.

**Unresolved issue**

Refunds when a customer has already spent some of their awarded points still need further investigation.

The current implementation limits the reversal to the available points balance. A clear business rule is needed to decide how any remaining reversal should be handled.

Further testing should cover full refunds after points have been spent, multiple partial refunds, and the consistency of the transaction record, ledger, and account balance.