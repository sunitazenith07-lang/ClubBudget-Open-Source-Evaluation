# approach.md — Required submission

Complete this file in your own words. Be concise and specific to the work actually performed.

## 1. Baseline

- **Commands run before editing:** `python -m pytest -q`, `python -m main`
- **Initial test result:** 147 passed, 67 failed.
- **Demo/output observed:** `Points example: 28` and `Repeat warnings: []`.

## 2. Codebase understanding

- **Important files/functions inspected:** `service.py`, `models.py`, `main.py`, and the tests under `tests/`.
- **Rewards calculation, refund, ledger or alert flow traced:** `calculate_points()` calculates purchase points; `apply_reward_event()` processes purchase and refund events and updates the account ledger; `flag_repeat_transactions()` groups possible repeat transactions.
- **How understanding was confirmed:** Ran the provided test suite, inspected failing tests, and compared expected behaviour with the implementation.

## 3. Investigation and implementation strategy

- **Issue 1 — Incorrect points rounding:** The original calculation used `round()`, which could award incorrect points near ₹100 boundaries. Replaced it with integer floor division.
- **Issue 2 — Incorrect cap handling:** The original truthiness check ignored `cap_points=0`. Changed the check to `cap_points is not None`.
- **Issue 3 — Duplicate and invalid events:** Added checks for duplicate event IDs, invalid purchase amounts, missing transaction IDs, and invalid or excessive refunds.
- **Additional issue — Repeat alerts:** Added validation for repeat-transaction inputs and threshold before grouping records.

## 4. Implementation decisions

- **Main changes and why:** Used integer arithmetic for points and proportional refunds, checked event IDs before processing, validated purchase and refund inputs, and kept ledger entries for accepted purchase and refund events.
- **Alternatives considered and why rejected:** Floating-point rounding was avoided because integer arithmetic is more predictable for money and points. Refunds are calculated proportionally rather than reversing the entire award for every partial refund.
- **Assumptions:** Amounts are supplied in paise as integers. Repeat transactions are grouped by account ID, date, and amount. The default repeat threshold is 2, and a group is flagged when its size is greater than the threshold.

## 5. Verification

- **Tests added or changed:** The supplied regression and acceptance tests were run. New test functions have not yet been added separately.
- **Commands run and actual results:** `python -m pytest -q` — 214 passed, 0 failed. `python -m main` — `Points example: 28`, `Repeat warnings: []`.
- **Remaining failures or limitations:** The available test suite passes. Additional validation of malformed reward-rule configurations and unusual input types may still be useful.