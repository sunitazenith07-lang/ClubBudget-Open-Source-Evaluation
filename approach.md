<!-- DRAFT: resolve every [VERIFY] and [FILL] marker with your own run/edits, then delete this comment. -->
# approach.md

## 1. Baseline
- Commands run before editing: `python -m pip install -r requirements-dev.txt`, `python -m pytest -q`, `python -m main`
- Initial test result: `67 failed, 147 passed` [VERIFY: paste your own summary line]
- Demo output: `Points example: 28` and `Repeat warnings: []` [VERIFY]. 28 looked wrong to me: ₹2599 with a 10% bonus should not give 28 under a floor rule (see issue 1).

## 2. Codebase understanding
- Files read: `service.py` (all logic), `models.py` (account dict shape), `fixtures.py` and `main.py` (demo), both test files, `data/records.json`, `tests.yml`.
- Flow traced: `apply_reward_event` copies the account, then branches on `type`. Purchase calls `calculate_points` and records a transaction. Refund updates `refunded_paise` and reverses points. Alerts are a separate function that groups by (account, date, amount).
- How I confirmed it: grouped the 67 failures by test name to see which behaviours were broken, probed edge inputs (unknown refund, missing event_id) in a Python shell, and ran all 264 events in `records.json` through the service to check balances and the ledger.

## 3. Investigation and implementation strategy
- **Issue 1, points maths.** Symptom: 9999 paise gave 1 point, and a cap of 0 gave 5 points. Cause: `round()` rounds to nearest, and `if cap_points:` treats 0 as "no cap". Fix: `//` floor division and `cap_points is not None`, plus one validation helper that rejects bools, negatives and non-ints.
- **Issue 2, idempotency and event acceptance.** Symptom: replaying one event doubled the balance, and events with no `event_id` were stored as `None`. Cause: `processed_event_ids` was written but never checked. Fix: an early return for missing or already-processed IDs, and the ID is appended only when the event is accepted.
- **Issue 3, refunds.** Symptom: refunds of `True`, strings, floats, negatives and amounts above the purchase were all accepted. Cause: no validation and no cumulative bound. Fix: positive int only, reject the whole event if total refunded would exceed the purchase, and reverse points with cumulative floor maths so a full refund reverses exactly what was awarded.
- **Issue 4, repeat alerts (minor).** The `>` threshold comparison was already correct, because the tests pin it. The only change: records missing account, date or amount are skipped so they cannot form a fake group under `None`.

## 4. Implementation decisions
- Main changes: split `apply_reward_event` into `_apply_purchase` and `_apply_refund`, added `_is_int`, and added `transaction_id` to ledger entries.
- Alternatives rejected:
  - Clamping an over-refund instead of rejecting it. The tests require `refunded_paise == 0` for over-refunds.
  - Marking rejected events as processed. That breaks the 1:1 link between processed IDs and the ledger, and it would block a corrected retry.
- Assumptions: purchases with amount ≤ 0 are rejected; event and transaction IDs must be non-empty strings; a repeat threshold below 1 is treated as 1.

## 5. Verification
- Tests added: `tests/test_regressions.py` (12 tests, listed in TESTING.md).
- Command and result: `python -m pytest -q` gives `226 passed` [VERIFY]. `python -m main` now prints `Points example: 27` [VERIFY].
- Edge cases verified: see TESTING.md.
- Dataset check: after running all of `records.json`, no balance is negative, the ledger sums to the balance on every account, and no `None` is in `processed_event_ids` [VERIFY].
- Known limitations: see challenges.md and optimizations.md.

AI use: I used Claude for this task, as the organiser permitted. The details and what I checked myself are in AI_USAGE.md.