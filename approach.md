# approach.md - Required submission

## 1. Baseline
- Commands run before editing:
  - `python3 -m pytest -q`
- Initial test result:
  - The starter project failed with multiple assertions in refund and replay logic; the actual result before the fix was a failing suite with several refund and grouping errors.
- Demo/output observed:
  - The failing cases were primarily around over-refunds, duplicate event reprocessing, and incorrect point-floor arithmetic.

## 2. Codebase understanding
- Important files/functions inspected:
  - `service.py` for `calculate_points()`, `apply_reward_event()`, and `flag_repeat_transactions()`
  - `models.py` for the account shape
  - `tests/test_contract.py` and `tests/test_acceptance_matrix.py` for the contract and acceptance expectations
- Rewards calculation, refund, ledger or alert flow traced:
  - The reward flow begins with purchase amounts, converts them into integer blocks, applies bonus/cap logic, and stores the original transaction metadata.
  - Refunds then inspect the transaction record, compute proportional reversal, and reduce the account balance without going below zero.
  - Repeat alerts group records by `(account_id, date, amount_paise)` and return only groups above the threshold.
- How I confirmed my understanding:
  - I read the repository contract, traced the failing assertions, and matched the logic to the actual test expectations rather than guessing from the starter implementation.

## 3. Investigation and implementation strategy
- Issue 1: Wrong point rounding and input validation
  - Symptom: values like `19999` and negative inputs did not satisfy the expected floor-based logic.
  - Hypothesis: the starter code used `round()` instead of integer floor division and did not reject invalid values.
  - Evidence: failing assertions in the reward calculation tests and invalid-input tests.
  - Fix chosen: use `//` floor division and reject invalid inputs early.

- Issue 2: Refund logic allowed invalid or excess refunds
  - Symptom: refund amounts above the original purchase amount were being accepted and points were reduced incorrectly.
  - Hypothesis: the refund branch ignored upper bounds and type validation.
  - Evidence: the refund-amount acceptance tests failed for values beyond the allowed range.
  - Fix chosen: ignore invalid values, cap the refund to the remaining amount, and prevent negative balances.

- Issue 3: Replay events could award points twice
  - Symptom: the same `event_id` processed twice changed the account balance again.
  - Hypothesis: `processed_event_ids` was being updated without checking for duplicates before processing.
  - Evidence: replay/idempotency tests failed when the same event was applied repeatedly.
  - Fix chosen: reject any event whose `event_id` has already been processed.

## 4. Implementation decisions
- Main changes and why:
  - Added explicit validation to `calculate_points()` for negative, boolean, and malformed values.
  - Switched to floor division and enforced caps after bonus calculation.
  - Added idempotency checks in `apply_reward_event()`.
  - Restricted refunds to the allowed remaining amount and proportional reversal.
  - Hardened `flag_repeat_transactions()` to ignore invalid rows and group only valid same-account/same-date/same-amount records.
- Alternatives considered and why rejected:
  - A more abstract refactor with helper functions was considered, but it would add complexity without improving correctness for this small codebase.
  - A broader rewrite of the data model was rejected because the issue was isolated to validation and arithmetic rules.
- Assumptions:
  - The contract requires integer floor arithmetic, not rounding.
  - Account balances should never go negative.
  - Repeat alerts are advisory only; they are not blocking logic.

## 5. Verification
- Tests added or changed:
  - I relied on the repository tests already covering the required contract.
  - No tests were weakened or skipped.
- Commands run and actual results:
  - `python3 -m pytest -q`
  - Result: `214 passed in 0.04s`
- Edge cases verified:
  - negative purchase amounts
  - excessive refunds
  - duplicate event replay
  - same-account/same-date/same-amount repeat grouping
  - invalid threshold and malformed values
- Remaining failures or known limitations:
  - None observed in the current repository state.
  - The implementation remains intentionally conservative and safe around malformed input values.