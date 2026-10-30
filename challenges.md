# Challenges

## 1. Main Challenge

One of the main challenges I faced was handling multiple partial refunds correctly.

At first, I thought calculating the points to reverse for every refund separately would be enough. But while testing different refund amounts, I found that this could cause rounding problems.

For example, suppose a customer earns 10 points on a purchase of ₹1,000. Later, the customer gets three partial refunds of ₹333.33, ₹333.33 and ₹333.34.

If I calculate the points to reverse separately for each refund using integer division, the result becomes:

```python
r1 = (10 * 33333) // 100000  # 3
r2 = (10 * 33333) // 100000  # 3
r3 = (10 * 33334) // 100000  # 3
```

The total is only 9 points, even though the customer has received a full refund. One point is left unreversed because of rounding.

I also found another issue with Python's type checking. In Python, `bool` is a subclass of `int`. This means `isinstance(True, int)` returns `True`.

Because of this, a simple integer check could accept `True` as a valid refund amount.

## 2. Evidence

I found these problems while running the existing tests:

- `test_invalid_or_excess_refund_does_not_change_account[True]` failed because `True` was accepted as an integer.
- `test_invalid_or_excess_refund_does_not_change_account[False]` also failed because `False` passed the integer type check.
- `test_invalid_or_excess_refund_ignored` failed because refunds greater than the original purchase amount were not rejected.

I also created a small example to understand the partial refund rounding problem. It showed that calculating every refund separately could leave some points unreversed even after a full refund.

## 3. What I Tried

I tried a few approaches before deciding how to handle these problems.

### Experiment 1: Calculating every refund separately

I first calculated the points reversal using only the current refund amount.

```python
delta = (awarded_points * refund) // original_amount
```

**Result:** This caused rounding differences when a transaction had multiple partial refunds. The total reversed points could be less than the original awarded points.

### Experiment 2: Using only `isinstance(x, int)`

I tried checking whether the refund amount was an integer.

```python
if not isinstance(refund, int):
    return out
```

**Result:** This did not reject `True` and `False`, because Python considers boolean values to be integers for this check.

### Experiment 3: Tracking the total refunded amount

I changed the approach so that the program keeps track of the total refunded amount for each transaction.

Instead of calculating each refund independently, it calculates how many points should have been reversed in total after every refund.

I also added a separate check to reject boolean values.

**Result:** The cumulative calculation handled partial refunds correctly, and the invalid input tests passed.

## 4. How I Fixed the Problems

I made three main changes.

**1. Added better input validation**

Refund amounts must be positive integers. Boolean values, negative numbers and invalid types are rejected.

```python
if not isinstance(refund, int) or isinstance(refund, bool) or refund <= 0:
    return out
```

**2. Prevented refunds from exceeding the purchase amount**

Before accepting a refund, the program checks whether the new total refund would be greater than the original transaction amount.

```python
if already_refunded + refund > original_amount:
    return out
```

**3. Used cumulative refund calculation**

The program first calculates the total points that should be reversed based on the total refunded amount.

```python
new_refunded_paise = already_refunded + refund

total_should_reverse = (
    awarded_points * new_refunded_paise
) // original_amount
```

Then it calculates the difference between the total reversal required and the points already reversed.

This avoids losing points because of separate rounding in every refund event.

I also added a balance check so that the account balance cannot become negative.

## 5. Testing and Regression Prevention

After making these changes, I ran the tests again.

The following cases passed:

- Boolean refund values (`True` and `False`) are rejected.
- Refunds greater than the original purchase amount are rejected.
- Multiple partial refunds are calculated correctly.
- A full refund reverses all 10 awarded points when the full balance is available.
- Refund rounding cases are handled correctly.

I added regression tests in `tests/test_fintech_edge_cases.py` so that these problems can be checked again if the code changes in the future.

The latest complete test run showed:

```text
248 passed in 0.27s
```

## 6. Remaining Limitation

One issue still needs a separate business rule.

Suppose a customer receives 10 points but spends 8 points before requesting a full refund. Only 2 points are left in the account.

The current implementation deducts those 2 available points and prevents the balance from becoming negative. It records the full calculated reversal in the transaction, but the remaining 8 points are not recovered.

For a production system, this could be handled using a separate pending liability record or an administrative review process. However, this would require additional business rules and changes to the existing account structure.

I have kept the current implementation within the existing project structure instead of adding an unrequested feature.