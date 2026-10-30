## What did you change?
- Updated `calculate_points` in `service.py` to use floor division (`amount_paise // 10000`), handle `cap_points = 0`, and return `0` for negative, zero, boolean, or non-integer inputs.
- Updated `apply_reward_event` in `service.py` to skip duplicate `event_id`s, check that `event_id` and `transaction_id` are non-empty strings, reject invalid or excess refunds (`refunded_paise + refund > amount_paise`), reverse points proportionally without letting the balance go negative, and only record accepted events in `ledger` and `processed_event_ids`.
- Updated `flag_repeat_transactions` in `service.py` to handle `None`/empty lists, ignore invalid or non-captured rows, deduplicate `transaction_id`s, and sort groups by `(account_id, date, amount_paise)`.
- Added 4 regression tests in `tests/test_contract.py` and filled out `approach.md`, `challenges.md`, `optimizations.md`, `TESTING.md`, and `REWARD_RULE_NOTES.md`.

## Root cause
- `calculate_points` used `round(amount_paise / 10000)` instead of integer floor division (`//`) and checked `if cap_points:`, which skipped `cap_points = 0` because `0` is falsy.
- `apply_reward_event` never checked if `event_id` was already in `processed_event_ids`, always appended `event_id` at the end of the function, and did not validate refund types or check if `refunded_paise + refund` exceeded `amount_paise`.

## Tests
- [x] I ran `py -m pytest -q` (the Python launcher command on this Windows environment, equivalent to `python -m pytest -q`).
- [x] I added or updated regression tests for my change.
- [x] I did not delete, skip, weaken or bypass existing tests.

Actual test summary:
- Baseline before changes (`py -m pytest -q`): `67 failed, 147 passed in 0.51s` (214 tests)
- Final after fixes and new tests (`py -m pytest -q`): `218 passed in 0.17s` (Total: 218, Passed: 218, Failed: 0, Errors: 0, Skipped: 0)

## Required problem-solving documents (all three mandatory; 15 marks total)
- [x] `approach.md` completed (5 marks) - covers the baseline failure summary (`22` points calculation failures, `21` idempotency failures, and `24` refund validation failures = `67` total), root causes in `service.py`, cumulative refund calculation, and verification.
- [x] `challenges.md` completed (COMPULSORY; 5 marks) - explains why `True` passed `isinstance(..., int)` in `test_invalid_or_excess_refund_does_not_change_account`, why `cap_points=0` failed, and how cumulative partial refunds were handled.
- [x] `optimizations.md` completed (5 marks) - covers early validation guards, direct tuple sorting, why `deepcopy` and `list` for `processed_event_ids` were kept, and before/after pytest timings.

## Edge cases checked
1. **Amount just below 100 rupees (`19999` paise, `1` point per 100 rupees)**: Expected `1` point using floor division; got `1` (`test_points_use_floor`).
2. **Zero cap (`cap_points = 0` on `50000` paise with `2` pts/100 rupees and `50%` bonus)**: Expected `0` points; got `0` (`test_cap_zero_is_respected`).
3. **Invalid or excess refunds (15 invalid inputs in `test_invalid_or_excess_refund_does_not_change_account`: `0, -1, -50, -1000, 100001, 150000, 200000, 999999, True, None, "100", 1.5, [], {}, False`, plus 10 excess-refund inputs `> 100000` in `test_refund_amount_bounds_and_balance`)**: Expected `refunded_paise` to stay `0` and `points_balance` to stay `10`; verified across all 15 invalid inputs and 10 excess-bound inputs.
4. **Cumulative partial refunds (`30000` + `70000` paise), duplicate `event_id` replay (`E2`), and `1` paisa excess refund (`E4`)**: Expected balance to go `10 -> 7 -> 7 (replay ignored) -> 0 -> 0 (excess ignored)`; verified in `test_refund_event_replay_and_cumulative_partial_refunds`.

## Design decisions / limitations
- Added `_is_strict_int(value)` (`isinstance(value, int) and not isinstance(value, bool)`) so `True` and `False` are rejected instead of being treated as `1` and `0`.
- Calculated refund reversals from cumulative `refunded_paise` so partial refunds that add up to 100% reverse all awarded points.
- Completed `REWARD_RULE_NOTES.md`, `TESTING.md`, and `AI_USAGE_TEMPLATE.md`. State is stored in memory per account dictionary.

## Integrity confirmation
- [ ] This is my own individual work. *(Note: AI assistance is declared in `AI_USAGE_TEMPLATE.md`; check only the boxes that apply to your submission rules.)*
- [ ] I have followed the evaluation's AI-use policy.
- [x] I can explain my changes and make a small live modification if asked.
