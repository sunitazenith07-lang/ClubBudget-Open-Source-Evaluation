# approach.md - Required submission

## 1. Baseline
- Commands run before editing: first I made a virtual environment (Homebrew Python 3.14.7 wouldn't let me `pip install` globally), then `python -m pip install -r requirements-dev.txt`, `python -m pytest -q` and `python -m main`. I ran the baseline on a clean copy of the starter code (`git archive HEAD`) so my own edits couldn't affect it.
- Initial test result (include the actual summary): `67 failed, 147 passed in 0.17s` (Python 3.14.7, pytest 9.2.0). Most failures were in `test_purchase_event_replay_is_idempotent` (20), `test_invalid_or_excess_refund_does_not_change_account` (13), `test_integer_floor_points_calculation` (11) and `test_refund_amount_bounds_and_balance` (10).
- Demo/output observed: `Points example: 28` and `Repeat warnings: []`. 28 is wrong. 259900 paise is ₹2599, which is 25 full ₹100s, so 25 points, and with the 10% bonus 25 × 110 // 100 = 27. The old code did `round(25.99)` = 26, which gave 28.

## 2. Codebase understanding
- Important files/functions inspected: almost everything happens in `service.py`, which has three functions: `calculate_points`, `apply_reward_event` and `flag_repeat_transactions`. I also looked at `models.py` (what an account looks like: balance, processed event IDs, transactions, ledger), `main.py`/`fixtures.py` (the demo), the two test files, the CI workflow, and `data/records.json`.
- Rewards calculation, refund, ledger or alert flow traced:
  - An event comes in and gets applied to a copy of the account, so the original isn't changed.
  - For a `purchase_captured` event, the code works out the points, saves the transaction, adds the points to the balance and writes a ledger line.
  - For a `refund_processed` event, it finds the original purchase, works out how many points to take back, subtracts them and writes a ledger line.
  - Repeat alerts group transactions by account + date + amount and flag any group bigger than the threshold.
- How you confirmed your understanding: I matched each failing test to the line in `service.py` that caused it. I also wrote a small script to count what's in `data/records.json`:
  - 264 reward events: 9 have no `event_id`, 12 reuse an `event_id` that already appeared (duplicates), and 152 have no `amount_paise` (all of those are declined, pending or unknown events)
  - amounts that are `None`, `"100"`, `1.5`, `True`, `[]` and `{}`
  - 180 repeat records, in 60 groups of 3 (12 groups have amount 0)

## 3. Investigation and implementation strategy
- **Issue 1: points rounding and caps.**
  - Symptom: `test_points_use_floor` failed, because 19999 paise gave 2 points instead of 1.
  - Cause: the code used `round(amount / 10000)`, which rounds to the nearest number, but the rule says only *full* ₹100s count. Also, `if cap_points:` treats a cap of `0` as "no cap", because 0 counts as False in Python.
  - Fix: `amount // 10000 * rate`, then the bonus with `base * (100 + bonus) // 100`, then the cap using `is not None`. Bad inputs (negative, not a whole number, or a boolean) give 0 points.
- **Issue 2: the same event counted twice.**
  - Symptom: `test_purchase_event_replay_is_idempotent` failed. The code saved each `event_id` but never checked the list, so sending the same event again added points again.
  - Fix: skip events that are already processed or have no `event_id`/`transaction_id`; skip amounts that aren't positive whole numbers; only purchases and refunds change the account; a second capture of the same `transaction_id` is ignored.
- **Issue 3: refunds had no limits.**
  - Symptom: negative, zero and too-big refunds were accepted (`test_invalid_or_excess_refund_does_not_change_account`).
  - Fix: reject a refund if the total refunded would go over the purchase amount. The points to take back are worked out from the *total* refunded so far, not each refund on its own (more on this in `challenges.md`), and the balance can't go below 0.
- **Issue 4: repeat alerts.**
  - Problem: a threshold of 0 or less, and rows with missing fields, weren't handled.
  - Fix: a threshold below 1 counts as 1; bad rows are skipped; results are sorted so they come out the same every time, and each alert is marked `needs_review`.
- **Issue 5 (ambiguity fix): surprising alert behaviour.**
  - Symptom: in a final review against the problem statement, a threshold of `None` or `"2"` raised alerts for just 2 matching rows (it was treated as 1), and one row sent 3 times alerted as `['T1', 'T1', 'T1']`.
  - Fix: a non-integer threshold falls back to the default of 2, the same as `repeat_threshold_from_config`; 0 or negative still counts as 1. Each `transaction_id` counts once per group. Tests: `test_invalid_threshold_falls_back_to_default`, `test_same_transaction_id_is_not_counted_as_a_repeat`.

## 4. Implementation decisions
- Main changes and why: I kept all the fixes inside `service.py` so the function names and account shape that the tests use didn't change. I added a small helper, `_is_int`, because in Python `True` is technically an `int` (it equals 1), so without the helper `True` would be accepted as 1 paise. Ledger lines now also store `transaction_id`, `amount_paise` and `balance_after`, so you can follow every change to the balance.
- Alternatives considered and why rejected:
  - *Fixing bad rules automatically (e.g. a negative bonus becomes 0%).* I didn't do this: the requirement says bad rules shouldn't give points, and quietly fixing them would hide a mistake.
  - *Marking rejected events as processed.* I didn't do this, because then a broken event could never be resent with the right data.
  - *Working out each refund separately.* I didn't do this, because rounding down each time can leave a point behind after a full refund.
  - *Raising errors on bad input.* I didn't do this, because the tests expect the account to come back unchanged.
- Assumptions: amounts are whole paise; only `purchase_captured` (exact spelling) earns points; transactions with amount 0 aren't real purchases, so they don't trigger alerts (the dataset gives 48 alert groups instead of 60).

## 5. Verification
- Tests added or changed: I added `tests/test_regressions.py`. It covers bad rules and amounts, duplicate events, missing IDs, retrying after a rejection, refund limits, partial refunds, the balance never going negative, ledger fields, alert edge cases, and replaying the whole dataset. I didn't edit, skip or delete any existing tests.
- Stretch item (configurable threshold): the alert threshold can now be changed. `repeat_threshold_from_config()` reads `repeat_alert_threshold` from a config dict (it falls back to 2 if the value is missing or bad), and `python -m main --threshold N` sets it from the command line. The default behaviour is the same as before. Tests are in `tests/test_threshold_config.py`.
- Stress testing: I added `tests/test_stress.py`, which runs a few thousand random inputs against the code. That found a crash when an ID was a list or dict, which I fixed (see `challenges.md`).
- Commands run and actual results: `python -m pytest -q` gave:
  - `249 passed` after the main fix (214 original + 35 new)
  - `264 passed` after the stretch item
  - `277 passed in 0.07s` after the stress-test fixes
  - `311 passed in 0.62s` after adding the stress tests to `tests/test_stress.py`
  - `314 passed in 0.64s` after making `flag_repeat_transactions` return `[]` for non-list input
  - `319 passed in 0.64s` after making junk thresholds fall back to the default and counting each transaction ID once per group

  `python -m main` gives `Points example: 27` and `Repeat warnings: []`.
- Edge cases verified: 9999 / 10000 / 19999 paise, cap 0, bonus over 100%, `True`/`"100"`/`1.5` amounts, a refund equal to the purchase, a refund 1 paisa too big, a repeated refund, and a threshold exactly reached vs. exceeded.
- Remaining failures or known limitations: no failing tests. The duplicate check searches a list, and the whole account is copied for every event, so it gets slow with thousands of events (see `optimizations.md`). Nothing is saved to a database.
