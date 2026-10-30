# Challenges I Faced

## 1. Reward points were not calculating correctly

When I first ran the tests, I found that some reward points were getting calculated incorrectly near the ₹100 limit.

For example, for 19,999 paise, the expected points were 1, but the old code was returning 2.

The issue was that the old code was using floating-point calculation and rounding. But according to the reward rule, I needed to use floor division.

I changed the calculation to use integer division:

```python
base = (amount_paise // 10000) * points_per_100_rupees
```

I also kept the bonus calculation in integer arithmetic.

## 2. Zero points cap was not working

Another issue was with `cap_points = 0`.

The old code was not applying the cap properly, and the test expected 0 points but got 5.

This happened because zero can be treated as `False` in Python conditions. So I changed the check to:

```python
if cap_points is not None:
```

Now zero is also treated as a valid cap.

## 3. Duplicate events

I also found an issue when the same event was processed again.

The balance was not getting extra points, but the same event ID was being added again to the processed event list. This was causing the test to fail.

I added a check before processing the event:

```python
if event_id in out['processed_event_ids']:
    return out
```

Now, if the event was already processed, it returns the account without processing it again.

## 4. Refund validation

Refund handling was another area where multiple tests were failing.

The old code was not properly checking negative refunds, refunds greater than the original purchase, and invalid refund values.

I added checks so that a refund is rejected if it is not an integer, is zero or negative, or exceeds the remaining refundable amount.

## 5. Running the tests again

After making the changes, I ran the full test suite again.

Before the changes:

```text
147 passed, 67 failed
```

After the changes:

```text
214 passed
```

I also saved the original test output in `baseline-test-results.txt` so that the initial failures can be checked.

## 6. Things that still need improvement

There are still some cases that need more validation and testing:

- Missing or empty event IDs.
- Missing transaction IDs.
- Invalid purchase amount values.
- Invalid reward-rule values.
- Saving data permanently and handling events running at the same time.

These are areas I would work on next.