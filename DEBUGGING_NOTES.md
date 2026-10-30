# Debugging Notes

This document records the defects found in the starter implementation, the
observed symptoms, the root causes, the solutions, and the verification
performed.

## Summary

The initial test run reported:

```text
67 failed, 147 passed in 0.35s
```

After the fixes:

```text
214 passed in 0.12s
```

The fixes are implemented in [`service.py`](service.py).

## 1. Amount calculation used rounding instead of flooring

### Error

The implementation used:

```python
round(amount_paise / 10000)
```

This awarded points for a partial ₹100 unit. For example:

```python
calculate_points(19999, 1)
```

returned `2`, while the required result was `1`.

### Root cause

Floating-point division followed by `round()` rounds the amount to the
nearest unit. The reward rule requires complete ₹100 units only.

### Solution

The calculation now uses integer floor division:

```python
base = (amount_paise // 10000) * points_per_100_rupees
```

This discards the incomplete remainder without introducing floating-point
rounding behavior.

### Verification

- `test_points_use_floor`
- `test_integer_floor_points_calculation`
- Full suite: passed

## 2. A zero cap was ignored

### Error

The implementation used:

```python
if cap_points:
```

Therefore, `cap_points=0` was treated as if no cap had been supplied:

```python
calculate_points(50000, 1, cap_points=0)
```

returned `5`, instead of `0`.

### Root cause

Zero is a false value in Python, but it is a valid business-rule value that
means no points may be awarded.

### Solution

The cap is now checked explicitly against `None`:

```python
if cap_points is not None:
    points = min(points, cap_points)
```

This distinguishes “no cap provided” from “cap the result at zero.”

### Verification

- `test_cap_zero_is_respected`
- `test_bonus_and_cap_matrix`
- Full suite: passed

## 3. Invalid amounts and rules could generate points

### Error

Negative or invalid values were allowed to reach the arithmetic. The
calculation did not explicitly reject negative amounts, negative rule values,
booleans, floats, strings, or other invalid types.

### Root cause

The starter function relied on arithmetic and `max(0, points)` as a final
guard. That did not validate the inputs or consistently enforce the business
rules.

### Solution

`calculate_points` now returns zero when any of these values is invalid:

- `amount_paise`
- `points_per_100_rupees`
- `bonus_percent`
- `cap_points`

Values must be non-negative integers. Booleans are rejected separately
because Python treats `bool` as a subclass of `int`.

### Verification

- `test_negative_amount_gives_zero`
- `test_invalid_purchase_amount_awards_zero_points`
- `test_invalid_rule_values_do_not_create_negative_points`
- `test_bonus_and_cap_matrix`
- Full suite: passed

## 4. Non-captured events could affect processing state

### Error

The requirement is that only `purchase_captured` events earn points.
Declined, pending, and unknown event types must not award points or create
purchase transactions.

### Root cause

The event dispatcher only had a positive branch for captured purchases and a
refund branch, but did not make the event-processing policy explicit at the
boundary.

### Solution

The implementation only creates a transaction and awards points inside the
`purchase_captured` branch. Other event types do not create transactions or
change the points balance.

### Verification

- `test_declined_event_does_not_award`
- `test_unrecognized_or_declined_events_do_not_award_points`
- Full suite: passed

## 5. Replaying an event changed account history

### Error

Applying the same purchase twice produced duplicate processed event IDs:

```text
['P1', 'P1']
```

Although the transaction check prevented a second award, the replay still
altered account state by appending the event ID again.

### Root cause

The starter checked whether a transaction already existed, but did not check
whether the specific `event_id` had already been processed.

### Solution

The event handler now returns the copied account immediately when the event
ID is missing or already present:

```python
if event_id is None or event_id in out['processed_event_ids']:
    return out
```

This protects purchase and refund events from replaying their state changes.

### Verification

- `test_purchase_event_once`
- `test_purchase_event_replay_is_idempotent`
- Focused runtime check: one processed ID and one ledger entry after replay
- Full suite: passed

## 6. Invalid and excessive refunds mutated transactions

### Error

The starter added every refund amount directly to the transaction. Observed
examples included:

```text
refund -1      => refunded_paise=-1, balance=11
refund 150000  => refunded_paise=150000, balance=-5
refund None    => TypeError
```

### Root cause

Refund amounts were not validated before changing `refunded_paise` or
calculating the reversal. The code also used a fallback denominator rather
than validating the purchase state.

### Solution

Refunds are accepted only when they are positive integers and do not exceed
the remaining refundable amount:

```python
refund > 0
refund <= txn['amount_paise'] - txn['refunded_paise']
```

Invalid or excessive refunds are ignored without changing the transaction
balance or refund total. Valid refunds reverse points proportionally:

```python
should_reverse = (
    txn['awarded_points'] * txn['refunded_paise'] // txn['amount_paise']
    if txn['amount_paise'] else 0
)
```

### Verification

- `test_partial_refund_reverses_proportionally`
- `test_invalid_or_excess_refund_ignored`
- `test_refund_amount_bounds_and_balance`
- `test_invalid_or_excess_refund_does_not_change_account`
- Full suite: passed

## Final verification

Commands run:

```text
python3 -m pytest -q
python3 -m main
```

Results:

```text
214 passed in 0.12s
Points example: 27
Repeat warnings: []
```

The implementation remains in-memory. Durable persistence, concurrent event
processing, and cross-process idempotency are outside the scope of this
exercise.
