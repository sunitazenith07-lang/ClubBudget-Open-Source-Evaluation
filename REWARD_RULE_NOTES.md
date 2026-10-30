# REWARD_RULE_NOTES.md — Required submission

These notes reflect the actual behavior implemented and verified in the code and test suite.

## 1. Worked points calculation
Example purchase:
- amount_paise = 50000
- points_per_100_rupees = 2
- bonus_percent = 50
- cap_points = 6

Step-by-step:
1. Calculate base points from whole 10000-paise blocks:
   - floor(50000 / 10000) = 5
   - base_points = 5 * 2 = 10
2. Apply promotion bonus using integer arithmetic:
   - bonus_points = floor(10 * (100 + 50) / 100) = floor(1500 / 100) = 15
3. Apply cap last:
   - capped_points = min(15, 6) = 6

Actual output:
- `calculate_points(50000, 2, 50, 6) == 6`
- This is also verified by `tests/test_contract.py::test_bonus_then_cap`

Rounding rule: all calculations use integer floor division, and the cap is applied only after the bonus step.

## 2. Partial-refund example
Purchase event:
- purchase amount = 100000 paise
- rules = {"points_per_100_rupees": 1}
- awarded points = floor(100000 / 10000) * 1 = 10

Refund event:
- refund amount = 50000 paise
- reversal formula = (awarded_points * refunded_paise) // original_amount_paise
- reversal = (10 * 50000) // 100000 = 5

Result:
- `refunded_paise` becomes 50000
- `reversed_points` becomes 5
- `points_balance` becomes 5
- ledger entry is a negative delta of `-5` for the refund event

Observed verification:
- `tests/test_contract.py::test_partial_refund_reverses_proportionally`
- actual result: `b['points_balance'] == 5` and `b['transactions']['T']['reversed_points'] == 5`

## 3. Three edge cases

### Edge case 1: negative purchase amount
- Input: `calculate_points(-10000, 1)`
- Expected: zero points
- Actual result: `0`
- Verified by: `tests/test_contract.py::test_negative_amount_gives_zero`

### Edge case 2: invalid or excessive refund
- Input: purchase of `100000` paise, then refund of `150000` paise
- Expected: refund is ignored and balance remains unchanged at the original 10 points
- Actual result: `refunded_paise == 0` and `points_balance == 10`
- Verified by: `tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account`

### Edge case 3: duplicate event replay
- Input: same `event_id` for the same purchase event processed twice
- Expected: second processing is ignored; no double award
- Actual result: balance remains `2`, and `processed_event_ids` contains only one entry
- Verified by: `tests/test_contract.py::test_purchase_event_once` and `tests/test_acceptance_matrix.py::test_purchase_event_replay_is_idempotent`

## 4. Assumptions and limitations
- Integer rounding is always floor-based for point calculation and proportional reversal.
- Missing or invalid fields are treated safely: negative amounts, booleans, and malformed values do not generate points and do not mutate the account.
- Terminal/ledger entries are written only for accepted purchase or refund events.
- Repeat-alert logic uses the supplied threshold and groups by `(account_id, date, amount_paise)`; it is a human-review signal only, not a blocking rule.
- The current implementation assumes a valid transaction record only if the amount is an integer greater than zero for repeat detection.
- No unresolved failing tests remain at the current repository state; the verified suite result is 214 passed in 0.04s.
