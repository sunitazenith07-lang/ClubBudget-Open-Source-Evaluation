# Challenges Faced — RewardBook

## 1. Incorrect reward-point calculation

**Challenge**

The original implementation used floating-point division and rounding to calculate reward points. This produced incorrect results near ₹100 boundaries.

**Evidence**

The baseline contract test `test_points_use_floor` failed for an amount of 19,999 paise. The expected result was 1 point, but the original implementation returned 2.

**Root cause**

Rounding was used where the reward rules required floor division.

**Resolution**

Replaced floating-point rounding with integer floor division:

```python
base = (amount_paise // 10000) * points_per_100_rupees
```

The bonus calculation also uses integer arithmetic.

## 2. Zero points cap was ignored

**Challenge**

A configured points cap of zero was not applied correctly.

**Evidence**

The baseline test `test_cap_zero_is_respected` expected zero points but received 5.

**Root cause**

A zero value can be treated as false in conditional checks. Checking whether a cap exists using truthiness incorrectly skips a zero cap.

**Resolution**

The implementation checks whether the cap is `None`:

```python
if cap_points is not None:
```

This allows zero to remain a valid cap.

## 3. Duplicate event processing

**Challenge**

Replaying the same purchase event did not award additional balance points, but the duplicate event ID was appended again to the processed-event list.

**Evidence**

The contract test `test_purchase_event_once` failed because the processed-event list contained the same ID twice.

**Root cause**

The event ID was not checked before processing the event.

**Resolution**

Added an early duplicate-event check:

```python
if event_id in out['processed_event_ids']:
    return out
```

This prevents an already processed event from being applied again.

## 4. Invalid refund amounts

**Challenge**

The original refund implementation allowed invalid refund values to modify transaction refund totals and could produce incorrect balances.

**Evidence**

Baseline failures included negative refunds, excessive refunds and malformed refund values.

**Root cause**

Refund validation did not adequately check the refund type, positivity or cumulative refund limit.

**Resolution**

Added validation to reject non-integer, non-positive and excessive refund amounts before modifying transaction state.

## 5. Verification and regression testing

**Challenge**

Changes to reward calculations and refund handling needed to be checked against existing contract and acceptance requirements.

**Resolution**

Executed the full pytest suite after implementation changes.

The verified result was:

```text
214 passed
```

The original baseline result was:

```text
147 passed, 67 failed
```

The baseline output was retained in `baseline-test-results.txt`.

## 6. Remaining challenges

The current implementation still needs stronger validation for:

- Missing or empty event IDs.
- Missing transaction IDs.
- Malformed purchase amounts.
- Malformed reward-rule values.
- Persistent storage and concurrent event processing.

These areas should be addressed with additional validation and regression tests.