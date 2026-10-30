## What did you change?
- Replaced floating-point rounding with integer floor division (`//`) in `calculate_points`.
- Fixed `cap_points = 0` being ignored due to Python's truthiness check.
- Added event-level idempotency to prevent duplicate ledger entries when events are replayed.
- Added input validation for refunds (positive ints, non-bool, not exceeding transaction amount) and implemented cumulative proportional reversals to avoid remainder drift.
- Added regression tests in `tests/test_regression.py`.
- Completed all required documentation files (`approach.md`, `challenges.md`, `optimizations.md`, `TESTING.md`, `REWARD_RULE_NOTES.md`).

## Root cause
1. Using `round()` instead of integer floor caused 9999 paise to round up to 100 rupees and earn points.
2. `if cap_points:` treated 0 as falsy and skipped the cap.
3. `processed_event_ids.append(event_id)` was run unconditionally, so replayed events duplicated ledger rows.
4. Refunds were not checked against the original purchase amount, and calculating reversals on isolated chunks lost points to integer truncation.

## Tests
- [x] I ran `python -m pytest -q`.
- [x] I added or updated regression tests for my change.
- [x] I did not delete, skip, weaken or bypass existing tests.

Actual test summary:
`220 passed in 0.35s` (all 214 baseline tests pass, plus 6 new regression tests).

## Required problem-solving documents (all three mandatory; 15 marks total)
- [x] `approach.md` completed (5 marks).
- [x] `challenges.md` completed (COMPULSORY; 5 marks).
- [x] `optimizations.md` completed (5 marks).

## Edge cases checked
1. `amount_paise = 9999`: awards 0 points.
2. `cap_points = 0`: awards 0 points.
3. Multi-step partial refund (30% + 30% + 40%): reverses all 10 awarded points without truncation drift.
4. Boolean amounts (`True`/`False`): rejected as non-numeric amounts.
5. Duplicate event replay: recognized and ignored without mutating balance or ledger.

## Design decisions / limitations
- Used native integer division (`//`) for performance and exactness without needing `decimal.Decimal`.
- Used `deepcopy` to ensure account dictionaries passed to `apply_reward_event` are never modified in-place.
- Service is currently in-memory; production deployment would need database transaction locks.

## Integrity confirmation
- [x] This is my own individual work.
- [x] I have followed the evaluation's AI-use policy.
- [x] I can explain my changes and make a small live modification if asked.
