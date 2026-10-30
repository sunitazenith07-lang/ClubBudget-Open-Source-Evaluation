# Reward Rules — Calculation Notes

## 1. Reward calculation formula

The reward calculation uses integer arithmetic and paise as the input unit.

1. Calculate base points by dividing the purchase amount in paise by 10,000 using floor division.
2. Multiply the base points by the configured points per ₹100.
3. Apply the bonus percentage using integer floor division.
4. Apply the optional points cap last.

### Formula

```python
base_points = (amount_paise // 10000) * points_per_100_rupees
bonus_points = base_points * (100 + bonus_percent) // 100

if cap_points is not None:
    final_points = min(bonus_points, cap_points)
else:
    final_points = bonus_points
```

Negative amounts and negative rule values return zero points. A cap of zero is valid and results in zero points.

## 2. Worked purchase calculation

Assume:

- Purchase amount: ₹500
- Amount in paise: 50,000
- Points per ₹100: 2
- Bonus percentage: 50%
- Maximum points cap: 6

**Step 1 — Base points**

```text
50,000 // 10,000 = 5
5 × 2 = 10 base points
```

**Step 2 — Apply bonus**

```text
10 × (100 + 50) // 100
= 1,500 // 100
= 15 points
```

**Step 3 — Apply cap**

```text
min(15, 6) = 6 points
```

**Final reward: 6 points.**

## 3. Partial refund example

Assume:

- Original captured purchase: ₹1,000
- Original awarded points: 10
- Refund amount: ₹500

The cumulative refund percentage is:

```text
500 / 1,000 = 50%
```

The proportional reversal is calculated using integer arithmetic:

```python
should_reverse = awarded_points * cumulative_refunded_paise // original_amount_paise

should_reverse = 10 * 50000 // 100000
should_reverse = 5
```

The account receives a reversal of 5 points.

```text
Original points:  10
Reversed points:   5
Remaining balance: 5
```

For multiple partial refunds, the cumulative refunded amount is used to calculate the total points that should have been reversed. Only the difference between the newly calculated reversal and the previously reversed points is deducted.

## 4. Important edge cases

1. **Amount below ₹100:** A purchase of ₹99.99 (9,999 paise) earns zero base points at one point per ₹100.
2. **Exact ₹100 boundary:** A purchase of 10,000 paise earns one base point at one point per ₹100.
3. **Zero cap:** If `cap_points` is zero, the final reward must be zero.
4. **Negative refund:** A negative refund must not modify the refunded amount or reward balance.
5. **Excess refund:** A refund greater than the original purchase amount must be rejected.
6. **Repeated event:** Processing an already accepted event ID must not award or reverse points again.
7. **Partial refund:** Multiple partial refunds must not reverse more points than the original award.

## 5. Assumptions

- Purchase amounts and refund amounts are represented in integer paise.
- Only captured purchases are eligible for rewards.
- Refunds are associated with an existing captured transaction.
- Refund amounts must be positive integers.
- A refund cannot make cumulative refunded value exceed the original purchase amount.
- The points cap is optional. When provided, it is applied after the bonus calculation.
- Repeat-transaction alerts are indicators for human review, not proof of fraud.
- The repeat-alert threshold is interpreted as the number of matching transactions that must be exceeded before an alert is generated.