## What did you change?
Fixed the three functions in `service.py` to meet all eight required behaviours and added 112 new tests (regression, stretch-item and randomized stress tests) in `tests/test_regressions.py`, `tests/test_threshold_config.py` and `tests/test_stress.py`.

- `calculate_points`: Fixed point calculation to use floor division, corrected bonus and cap handling, and added input validation.
- `apply_reward_event`: Added duplicate event protection, transaction validation, refund limits and cumulative refund calculations. Updated ledger entries to include transaction details and the resulting balance.
- `flag_repeat_transactions`: Added threshold validation (non-integer thresholds fall back to 2), skipped invalid records, counted each transaction ID once per group, ensured deterministic output and added `needs_review` labels to alerts.
- **Stretch item: configurable repeat threshold.** `repeat_threshold_from_config()` reads `repeat_alert_threshold` from a config dict (falls back to 2 if missing or invalid), and `python -m main --threshold N` sets it from the command line. Default behaviour is unchanged.
- **Stress-test fixes:** randomized testing found that a list or dict `transaction_id`, `account_id` or `date` crashed with `TypeError`; those events and rows are now ignored. Alert `transaction_ids` are now sorted so input order does not change the output.
- **Ambiguity fixes (repeat alerts):** a non-integer threshold (`None`, `"2"`) used to become 1 and over-alert; it now falls back to the default of 2, matching `repeat_threshold_from_config`. The same `transaction_id` sent more than once is now counted once, so a duplicated row is no longer flagged as a repeat payment.
- **Extreme-stress fixes:** a refund on an account whose balance was already negative used to *add* points; the points taken back are now never below 0. A non-dict account (`None`, `[]`, a string) crashed with `AttributeError`; it now counts as a new, empty account, the same as `{}`. Alert IDs are now collected in a set, so one group of 40,000 rows takes 0.01 s instead of 4.18 s, and alert rows whose `transaction_id` is a list or dict are skipped.

## Root cause
The original implementation had several issues:

- `round(amount / 10000)` used floating-point rounding instead of floor division, causing incorrect point calculations.
- `if cap_points:` failed to recognise 0 as a valid cap.
- Processed event IDs were stored but never checked, allowing duplicate events to affect the balance.
- Refund amounts were not properly validated, allowing invalid and oversized refunds.
- There was no input type checking. A plain `isinstance(value, int)` check isn't enough either, because `True`/`False` pass it.

## Tests
- [x] I ran `python -m pytest -q`.
- [x] I added or updated regression tests for my change.
- [x] I did not delete, skip, weaken or bypass existing tests.

Actual results:

- Before changes: 67 failed, 147 passed.
- After changes: 249 passed, 0 failed.
- After the stretch item: 264 passed, 0 failed.
- After stress-test fixes: 277 passed, 0 failed.
- After adding the stress tests: 311 passed, 0 failed.
- After handling non-list alert input: 314 passed, 0 failed.
- After the threshold-fallback and duplicate-ID fixes: 319 passed, 0 failed.
- After the extreme-stress fixes: 326 passed, 0 failed.
- Original tests: 214.
- New regression tests: 35, plus 15 for the stretch item, plus 13 from stress testing, plus 3 for non-list alert input, plus 5 for the ambiguity fixes, plus 7 from extreme stress testing, plus 34 randomized stress tests in `tests/test_stress.py`.

`python -m main` also produces the expected output: `Points example: 27`, `Repeat warnings: []`.
Environment: Python 3.14.7, pytest 9.2.0.
CI (GitHub Actions, Python 3.11, run on my fork): 326 passed, 0 failed, 0 errors, 0 skipped. Run: https://github.com/madhavmongaa/RewardBook-Open-Source-Evaluation/actions/runs/41148987600

## Required problem-solving documents (all three mandatory; 15 marks total)
- [x] `approach.md` completed (5 marks). It explains the implementation approach and connects the original test failures to the relevant issues in `service.py`.
- [x] `challenges.md` completed (COMPULSORY; 5 marks). The main insight was that partial refunds must be calculated cumulatively. Rounding each refund separately could leave 1 point after a full refund of a 156-point purchase.
- [x] `optimizations.md` completed (5 marks). It compares a list and a set for tracking processed event IDs and explains why the list was kept, and it records one measured speed-up: collecting alert IDs in a set made one 40,000-row group go from 4.18 s to 0.01 s.

## Edge cases checked
1. A purchase of 19999 paise should generate 1 point instead of 2. Actual: 1 point.
2. Replaying the same purchase event should not update the balance or ledger twice. Actual: Only one ledger entry was created.
3. Invalid refunds, including booleans, strings, decimals, zero and negative values, should be ignored. Actual: Balance remained unchanged.
4. Refunds totalling more than the original purchase should be rejected. Actual: The second refund was rejected.
5. Reaching the repeat transaction threshold exactly should not trigger an alert. Exceeding it should generate one alert. Actual: Worked as expected.
6. The same transaction row sent three times should not be flagged as a repeat. Actual: No alert.
7. A refund on an account whose balance is already negative should not add points. Actual: Balance unchanged, `points_delta` 0.

A full set of 17 cases is documented in `TESTING.md`.

## Design decisions / limitations
- Invalid reward rules return 0 points instead of being automatically corrected.
- Rejected events are not marked as processed, allowing corrected events to be submitted again.
- Zero-amount transactions are excluded from repeat alerts. This results in 48 alert groups instead of 60 in `data/records.json`.
- Numeric strings such as `"100000"` are rejected rather than automatically converted.
- Points redeemed outside this service are not tracked, so refund reversals are limited to the current account balance and never add points.
- A non-dict account (`None`, `[]`, a string) is treated as a new, empty account.

Challenge-specific notes are available in `REWARD_RULE_NOTES.md`.

## Integrity confirmation
- [x] This is my own individual work.
- [x] I have followed the evaluation's AI-use policy.
- [x] I can explain my changes and make a small live modification if asked.

AI assistance was used and is declared in `AI_USAGE.md`.
