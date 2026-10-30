## 1. Worked points calculation

For `amount_paise=259900`, `points_per_100_rupees=1`,
`bonus_percent=10`, and `cap_points=100`:

1. `259900 // 10000 = 25` whole units of ₹100; the remaining ₹99 is
   discarded.
2. `base_points = 25 * 1 = 25`.
3. `bonus_points = 25 * (100 + 10) // 100 = 27`.
4. The cap is applied last: `min(27, 100) = 27`.

The observed output from `calculate_points` is `27`.

## 2. Partial-refund example

For a `100000` paise purchase with one point per ₹100:

- Original award: `100000 // 10000 = 10` points.
- Refund: `50000` paise.
- Reversal: `10 * 50000 // 100000 = 5` points.
- Resulting balance: `5` points.
- Ledger entry:

```python
{'event_id': 'R1', 'type': 'refund_processed', 'points_delta': -5}
```

## 3. Three edge cases

1. `calculate_points(19999, 1)` is expected to floor the amount and returns
   `1`. Verified by `test_points_use_floor`.
2. `calculate_points(50000, 1, cap_points=0)` is expected to return `0` and
   does return `0`. Verified by `test_cap_zero_is_respected`.
3. Replaying a purchase with the same `event_id` is expected not to change
   the account twice. The observed balance is `2`, with one processed event
   ID and one ledger entry. Verified by
   `test_purchase_event_replay_is_idempotent`.

## 4. Assumptions and limitations

- Monetary calculations use integer paise and floor division; partial ₹100
  units do not earn points.
- Amounts and rules must be non-negative integers. Invalid values produce
  zero points; `cap_points=0` is a valid zero cap.
- Only `purchase_captured` events award points. Declined, pending, and
  unknown event types do not.
- Missing purchase amounts use the existing event default of zero.
- Refunds must be positive integer paise and cannot exceed the remaining
  refundable purchase amount.
- Repeat alerts are emitted only when the group size is greater than the
  supplied threshold.
- Event replay protection is held in the in-memory account state; durable
  persistence and concurrent processing are outside this exercise.
