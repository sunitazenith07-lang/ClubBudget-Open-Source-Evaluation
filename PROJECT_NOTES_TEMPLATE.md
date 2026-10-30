# Project Notes

## Requirements completed
- Fixed `calculate_points`: Replaced floating-point rounding with integer floor division (`// 10000`), handled promotional bonuses and caps properly (especially respecting `cap_points = 0`), and added input type and boundary checks.
- Fixed `apply_reward_event`: Added idempotency checks on `event_id`, validated refund amounts (rejecting negative, boolean, and excess amounts), ensured proportional integer refund reversals, prevented negative points balances, and wrote ledger entries only for valid events.
- Updated `flag_repeat_transactions` to group transactions by account, date, and amount, returning alerts sorted by account ID when the count exceeds the threshold.
- Confirmed all 214 baseline tests pass, plus 5 new regression tests.

## Files changed
- `service.py`: Core bug fixes for points calculation, event idempotency, refund processing, and repeat alerts.
- `tests/test_regression.py`: Added 5 regression tests covering floor points, cap of 0, event deduplication, and partial refunds.
- `approach.md`: Documented baseline test run, code flow, defect investigation, and implementation decisions.
- `challenges.md`: Documented debugging of boolean refund inputs and multi-step partial refund reversals.
- `optimizations.md`: Documented performance trade-offs, integer math, and early return guards.
- `TESTING.md`: Recorded test environment, summary, and 5 edge cases.
- `REWARD_RULE_NOTES.md`: Worked points calculation, partial refund example, and edge cases.

## Decisions and assumptions
- All monetary amounts are kept in paise and calculated using integer arithmetic.
- Boolean values are explicitly rejected for numerical amounts.
- Points balance is never allowed to go below 0.
- Duplicate events are ignored and do not alter balances or duplicate ledger entries.

## Tests and results
- Baseline: `67 failed, 147 passed, 1 warning in 1.46s`
- Post-fix: `219 passed in 0.47s` (100% passing across `test_contract.py`, `test_acceptance_matrix.py`, and `test_regression.py`).

## Limitations and next steps
- State is held in-memory in Python dicts. In a real multi-worker setup, we would use database transactions or locks on the account to prevent duplicate events from being processed concurrently.
