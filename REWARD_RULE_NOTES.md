# REWARD_RULE_NOTES.md — Required submission

## 1. Worked points calculation
Purchase amount: 259900 paise (2599.00 rupees equivalent in paise).
- base_points = floor(259900 / 10000) * 1 = 25 * 1 = 25
- bonus_points = floor(25 * (100 + 10) / 100) = floor(27.5) = 27
- cap_points = min(27, 100) = 27
Actual output: 27 points.

## 2. Partial-refund example
Purchase: 100000 paise awards 10 points.
Refund: 50000 paise.
- refunded_paise = 50000
- should_reverse = 10 * 50000 // 100000 = 5
- delta = 5 - 0 = 5
- resulting balance = 10 - 5 = 5
- reversed_points = 5
Ledger entry: `{"event_id": ..., "type": "refund_processed", "points_delta": -5}`.

## 3. Three edge cases
1. Floor boundary: input `calculate_points(9999, 1)`; expected 0; actual 0; verified by `test_integer_floor_points_calculation`.
2. Cap of zero: input `calculate_points(50000, 1, cap_points=0)`; expected 0; actual 0; verified by `test_cap_zero_is_respected`/`test_bonus_and_cap_matrix`.
3. Excess refund ignored: purchase 100000 paise, refund 125000 paise; expected `refunded_paise == 0` and balance 10; actual unchanged; verified by `test_invalid_or_excess_refund_does_not_change_account`.

## 4. Assumptions and limitations
- Amounts and rule values are integers in paise; non-integer or boolean values are treated as invalid.
- Refunds must be positive integers and cannot cumulatively exceed the transaction amount; invalid refunds are ignored.
- Repeat alerts are informational only and never block transactions.
- No negative points balance is allowed.
