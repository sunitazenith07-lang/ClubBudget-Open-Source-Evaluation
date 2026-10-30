# Reward Rules — My Notes

## 1. How the points are calculated

The amount is given in paise, so I used integer arithmetic for the calculation.

The steps are:

1. Divide the purchase amount by 10,000 using floor division.
2. Multiply it by the points given per ₹100.
3. Apply the bonus percentage.
4. Apply the points cap at the end, if a cap is given.

The calculation used in the code is:

```python
base_points = (amount_paise // 10000) * points_per_100_rupees
bonus_points = base_points * (100 + bonus_percent) // 100

if cap_points is not None:
    final_points = min(bonus_points, cap_points)
else:
    final_points = bonus_points
```

Negative amounts and negative rule values return zero points. A cap of zero is also valid, so the final points become zero when the cap is zero.

## 2. Example of a purchase

Let's take these values:

- Purchase amount: ₹500
- Amount in paise: 50,000
- Points per ₹100: 2
- Bonus: 50%
- Points cap: 6

**Step 1: Calculate base points**

```text
50,000 // 10,000 = 5
5 × 2 = 10 base points
```

**Step 2: Apply the bonus**

```text
10 × (100 + 50) // 100
= 1,500 // 100
= 15 points
```

**Step 3: Apply the cap**

```text
min(15, 6) = 6 points
```

So the final reward is **6 points**.

## 3. Partial refund example

Suppose a customer makes a purchase of ₹1,000 and gets 10 points.

Later, the customer gets a refund of ₹500.

The refund is 50% of the original purchase:

```text
500 / 1,000 = 50%
```

So 50% of the awarded points should be reversed:

```python
should_reverse = awarded_points * cumulative_refunded_paise // original_amount_paise

should_reverse = 10 * 50000 // 100000
should_reverse = 5
```

The account will have:

```text
Original points:  10
Reversed points:   5
Remaining balance: 5
```

If there are multiple partial refunds, the code uses the total refunded amount to calculate the total points that should be reversed. It subtracts only the additional points that need to be reversed.

## 4. Edge cases to remember

1. **Amount below ₹100:** ₹99.99 (9,999 paise) gives 0 base points when the rate is 1 point per ₹100.
2. **Exactly ₹100:** 10,000 paise gives 1 base point at the same rate.
3. **Zero cap:** If the cap is 0, the final points should also be 0.
4. **Negative refund:** A negative refund should not change the refunded amount or balance.
5. **Refund greater than purchase:** It should be rejected.
6. **Same event again:** An already processed event should not give or reverse points again.
7. **Multiple partial refunds:** The total reversal should not be more than the points originally awarded.

## 5. Assumptions I followed

- Purchase and refund amounts are in integer paise.
- Only captured purchases get reward points.
- A refund should belong to an existing captured transaction.
- Refund amounts should be positive integers.
- The total refund should not be more than the original purchase amount.
- The points cap is optional and is applied after the bonus.
- Repeat-transaction alerts are only for manual checking. They do not prove fraud.
- An alert is generated when the number of matching transactions is greater than the threshold.