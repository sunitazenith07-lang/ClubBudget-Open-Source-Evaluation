# challenges.md - COMPULSORY submission

## 1. Challenge or confusing behaviour
The refund handling was the most confusing part: an excessive refund had to leave the account completely unchanged, including `refunded_paise`, `reversed_points`, balance, and ledger length.

## 2. Evidence
Example from the suite: purchase of 100000 paise (10 points), then refund of 125000 paise. Expected `refunded_paise == 0` and `points_balance == 10`. The old code capped the refund to 100000 and reversed all 10 points.

## 3. What I tried
- Ran `python -m pytest -q` to establish the 173 passed / 41 failed baseline.
- Inspected `calculate_points` and found `round(amount_paise / 10000)` instead of floor.
- Traced refund failures and found `max(0, ...)` coercion plus `min(...)` capping.
- Checked `data/records.json` rule cases for negative `per`, bonus, and cap values.

## 4. Resolution
The root cause was treating invalid/excessive refunds as partial valid refunds. I replaced coercion/capping with strict validation: refund must be a positive integer and `refunded_paise + refund <= transaction amount`. Invalid refunds now leave state unchanged but are still marked processed for idempotency. Points calculation now uses floor and integer-only validation.

## 5. Proof and regression prevention
- `test_integer_floor_points_calculation`
- `test_bonus_and_cap_matrix`
- `test_refund_amount_bounds_and_balance`
- `test_invalid_or_excess_refund_does_not_change_account`
- `test_invalid_or_excess_refund_ignored`
Final run: `214 passed in 0.13s`.

## 6. Unresolved challenge or next step
No visible failures remain. A future improvement would be stricter account/event schema validation and property-based tests for cumulative refund sequences.