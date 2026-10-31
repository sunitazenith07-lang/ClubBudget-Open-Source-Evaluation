# Reward rule notes

Prepared with Codex assistance; examples were executed during submission preparation.

## Worked points calculation
For 50,000 paise (500 rupees), rate 2, bonus 50%, cap 6:
- Base: `(50000 // 10000) * 2 = 10`.
- After bonus: `(10 * 150) // 100 = 15`.
- Apply cap last: `min(15, 6) = 6`.
Observed output: **6**, also protected by `test_bonus_then_cap`.

The demo uses 259,900 paise, rate 1, bonus 10%, cap 100: base 25, bonus-adjusted points 27, capped result **27**. Both amount and bonus use floor division.

## Partial refund
Capture event E1 for T1, 100,000 paise at rate 1, awards 10 points. Refund E2 for 50,000 paise gives cumulative reversal `(10 * 50000) // 100000 = 5`. Observed balance **5**, refunded paise **50,000**, reversed points **5**. Ledger: `{'event_id': 'E1', 'type': 'purchase_captured', 'points_delta': 10}` followed by `{'event_id': 'E2', 'type': 'refund_processed', 'points_delta': -5}`. Replaying E2 changes nothing.

## Edge cases
| Input | Expected and observed | Test |
|---|---|---|
| 19,999 paise at rate 1 | 1 point | `test_points_use_floor` |
| Cap 0 on a 50,000-paise purchase | 0 points | `test_cap_zero_is_respected` |
| Negative or excessive refund | Ignore; no refund total/balance change | `test_invalid_or_excess_refund_ignored` |
| Three same-key purchases, threshold 2 | One warning listing three IDs | `test_repeat_group` |

## Assumptions and limits
Only positive integer monetary inputs are accepted; booleans are rejected. Missing event/transaction identifiers are ignored. Only captured purchases award points. Invalid rules yield zero points, but a valid capture can still be recorded with a zero delta. Refund reversal uses cumulative refunded paise, subtracts already reversed points and is clamped to the available account balance. A second event for an existing purchase transaction is ignored. Repeat groups use exact account/date/amount equality and alert only when count is strictly greater than threshold; warnings do not block transactions. Account state is assumed to follow `new_account`; storage/concurrency are not implemented.
