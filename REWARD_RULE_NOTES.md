# REWARD_RULE_NOTES.md — Required submission

## 1. Worked points calculation
- Purchase amount: 259900 paise
- Base points: floor(259900 / 10000) * 1 = 25
- Bonus 10%: floor(25 * 110 / 100) = 27
- Cap: 100, final = 27
- Actual output from `main.py`: `Points example: 27`

## 2. Partial-refund example
- Original purchase: 100000 paise, awarded 10 points
- Refund amount: 50000 paise
- Reversal: 10 * 50000 // 100000 = 5
- Resulting balance: 5 points
- Ledger entry: `{'event_id': ..., 'type': 'refund_processed', 'points_delta': -5}`

## 3. Three edge cases
1. Amount below 10000 paise earns 0 points. Verified by `test_integer_floor_points_calculation`.
2. Cap of 0 forces 0 points. Verified by `test_cap_zero_is_respected`.
3. Invalid/excess refund leaves account unchanged. Verified by `test_invalid_or_excess_refund_does_not_change_account`.

## 4. Assumptions and limitations
- Amounts are in paise.
- Points use floor division at base and bonus steps.
- Refunds are accepted only as positive integers within remaining refundable amount.
- Repeat alerts are advisory and do not block transactions.
