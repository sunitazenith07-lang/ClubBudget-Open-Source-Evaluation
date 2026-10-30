# REWARD_RULE_NOTES.md — Required submission

## 1. Worked points calculation
Purchase: amount_paise = 259900, rules = {points_per_100_rupees: 1, bonus_percent: 10, cap_points: 100}

Step-by-step:
1. **Floor division**: `base = 259900 // 10000 = 25` (not `round(25.99) = 26`)
2. **Base points**: `25 * 1 = 25`
3. **Bonus**: `25 * (100 + 10) // 100 = 25 * 110 // 100 = 2750 // 100 = 27`
4. **Cap**: `cap_points is not None` → `min(27, 100) = 27`
5. **Final**: `max(0, 27) = 27`

Actual output from `python main.py`: `Points example: 27`

Rounding rule at each step: integer floor division (`//`) at every division step — no `round()` or floating-point rounding.

## 2. Partial-refund example
Setup: purchase of 100000 paise, rules = {points_per_100_rupees: 1}

1. **Purchase awarded**: `100000 // 10000 = 10` base points, bonus 0, cap none → `points_balance = 10`
   - Ledger entry: `{'event_id': 'E1', 'type': 'purchase_captured', 'points_delta': 10}`
   - Transaction: `{'amount_paise': 100000, 'awarded_points': 10, 'reversed_points': 0, 'refunded_paise': 0}`

2. **Partial refund**: `amount_paise = 50000` on transaction T
   - `refunded_paise` becomes 50000 (valid: 0 < 50000 <= 100000)
   - `should_reverse = 10 * 50000 // 100000 = 5`
   - `delta = 5 - 0 = 5`
   - `points_balance = 10 - 5 = 5`
   - `reversed_points = 5`
   - Ledger entry: `{'event_id': 'E2', 'type': 'refund_processed', 'points_delta': -5}`

Actual result verified by `test_partial_refund_reverses_proportionally`: `b['points_balance'] == 5` and `b['transactions']['T']['reversed_points'] == 5`

## 3. Three edge cases

**1. Cap of zero means zero points**
- Input: `calculate_points(50000, 1, cap_points=0)`
- Expected: 0 points
- Actual: 0 points
- Test: `test_cap_zero_is_respected` (test_contract.py line 11)

**2. Replayed purchase event does not double points**
- Input: Apply same event `{'event_id': 'E1', 'type': 'purchase_captured', ...}` twice
- Expected: `processed_event_ids == ['E1']`, `points_balance == 2` (not 4)
- Actual: `processed_event_ids == ['E1']`, `points_balance == 2`
- Test: `test_purchase_event_once` (test_contract.py line 13)

**3. Invalid refund type (None) does not crash or corrupt state**
- Input: refund `amount_paise = None` on a valid transaction
- Expected: `TypeError` avoided, `refunded_paise == 0`, balance unchanged at 10
- Actual: Account unchanged, `refunded_paise == 0`, balance 10
- Test: `test_invalid_or_excess_refund_does_not_change_account[None]` (test_acceptance_matrix.py line 79)

## 4. Assumptions and limitations
- **Rounding**: All division uses integer floor division (`//`). `round()` is never used. `19999 // 10000 = 1`, not 2.
- **Missing fields**: `event.get('amount_paise', 0)` defaults to 0; `event.get('event_id')` may be None but is still checked for idempotency.
- **Bool exclusion**: `isinstance(True, int)` is True in Python, so bools are explicitly excluded from valid refund amounts.
- **Repeat-alert threshold**: `flag_repeat_transactions` flags groups with `len(ids) > threshold` (strictly greater). With `threshold=2` and 3 identical transactions, an alert is raised. With `threshold=2` and exactly 2 transactions, no alert.
- **Negative balance**: Cannot occur — `calculate_points` returns `max(0, points)` and refund reversal is bounded by `awarded_points * refunded_paise // amount_paise` which never exceeds `awarded_points`.
- **No unresolved issues**: All 214 tests pass.