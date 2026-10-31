# approach.md - Required submission

Complete this file in your own words. Be concise and specific to the work you actually performed.

## 1. Baseline
- Commands run before editing:
  - `python --version` (Confirmed environment: Python 3.14.6)
  - `python -m pip install -r requirements-dev.txt` (Installed pytest-9.2.0 and dependencies)
  - `python -m pytest -q` (Baseline test suite run)
  - `python -m main` (Baseline offline execution)
- Initial test result (include the actual summary):
  - `67 failed, 147 passed in 0.84s` (Total: 214 tests)
- Demo/output observed:
  - `Points example: 28`
  - `Repeat warnings: []`

## 2. Codebase understanding
- Important files/functions inspected:
  - `service.py`: `calculate_points()`, `apply_reward_event()`, `flag_repeat_transactions()`.
  - `models.py`: `new_account()` dictionary structure.
  - `fixtures.py` & `main.py`: Sample data and entry point.
  - `tests/test_contract.py` & `tests/test_acceptance_matrix.py`: Visible test suite.
  - `data/records.json` & `data/README.txt`: Synthetic dataset of 40 accounts, 264 reward events, and 180 repeat-pattern records.
  - `.github/workflows/tests.yml`: CI workflow validating test report generation and failure gating.
- Rewards calculation, refund, ledger or alert flow traced:
  - Points computation: amount in paise is divided by 10,000 to determine eligible 100-rupee blocks, multiplied by rule points, adjusted for bonus percentage, and optionally capped.
  - Event processing: creates a deep copy of account state, extracts event identifiers, validates against idempotency records, processes purchase or refund operations, updates transaction tables, appends auditable ledger deltas, and records processed event IDs.
  - Refund reversal: checks transaction existence, validates refund bounds, calculates proportional point reversal, ensures points balance cannot drop below zero, and logs negative ledger delta.
  - Repeat alert detection: groups transactions by `(account_id, date, amount_paise)` and flags instances exceeding the configured threshold.
- How you confirmed your understanding:
  - Traced failure tracebacks from pytest to specific lines in `service.py` (e.g. `round()` vs `//`, `if cap_points:` evaluating `0` as falsy, unvalidated event replays, and unbounded refund additions).

## 3. Investigation and implementation strategy
For each major defect, describe the symptom, hypothesis, evidence from a test/log/example, and the fix chosen.
- Issue 1: Floating-point rounding and cap-zero omission in points calculation
  - Symptom: `calculate_points(19999, 1)` returned `2` instead of `1`; `calculate_points(50000, 1, cap_points=0)` returned `5` instead of `0`.
  - Hypothesis: The starter code used `round(amount_paise / 10000)`, causing values like 1.9999 to round up to 2. Furthermore, `if cap_points:` treated `cap_points=0` as falsy, bypassing cap enforcement.
  - Evidence: `tests/test_contract.py::test_points_use_floor` and `test_cap_zero_is_respected` failed directly.
  - Fix: Implemented integer floor division `(amount_paise // 10000) * points_per_100_rupees` and `base * (100 + bonus_percent) // 100`. Checked `if cap_points is not None:` to explicitly respect `cap_points = 0`. Added type and non-negative guards for all input parameters.
- Issue 2: Missing event replay idempotency in `apply_reward_event`
  - Symptom: Replaying an event appended duplicate IDs (`['E1', 'E1']`) and repeated ledger additions.
  - Hypothesis: `apply_reward_event` lacked an early return check against `out['processed_event_ids']` and unconditionally appended `event_id` at the end.
  - Evidence: `tests/test_contract.py::test_purchase_event_once` and all 20 parameterized cases in `test_purchase_event_replay_is_idempotent` failed.
  - Fix: Added an idempotency check at the start of event processing: `if not event_id or event_id in out['processed_event_ids']: return out`.
- Issue 3: Unvalidated refund amounts and over-refund drift
  - Symptom: Negative, zero, excess, and non-integer refund amounts mutated account balances and transaction records.
  - Hypothesis: `apply_reward_event` lacked validation on `refund` type and bounds, and did not check `txn['refunded_paise'] + refund <= txn['amount_paise']`.
  - Evidence: `tests/test_contract.py::test_invalid_or_excess_refund_ignored` and 23 parameterized refund tests failed.
  - Fix: Added validation rejecting non-positive, non-integer, boolean, and excess refund amounts. Reversal is calculated cumulatively using `(txn['awarded_points'] * new_refunded) // txn['amount_paise']` to eliminate integer drift across sequential partial refunds. Clamped reversal delta to available points balance.

## 4. Implementation decisions
- Main changes and why:
  - Replaced all floating-point math with pure integer arithmetic (`//`) to prevent binary floating-point representation artifacts.
  - Implemented cumulative reversal tracking so that multiple partial refunds summing to 100% cleanly reverse 100% of awarded points without drift.
  - Guarded against Python's `bool` subclassing `int` (`isinstance(True, int) == True`) by adding explicit `not isinstance(val, bool)` checks.
- Alternatives considered and why rejected:
  - `Decimal` module: Considered for monetary calculations, but rejected because pure integer arithmetic in paise (`int`) is faster, has zero external dependencies, and satisfies the problem contract precisely.
  - Modifying account in-place: Rejected because contract and tests require immutable semantics where input account is not mutated.
- Assumptions:
  - Currency is tracked in integer paise (1 INR = 100 paise).
  - Repeat alerts are advisory signals for operations and human review; transactions are not rejected automatically.

## 5. Verification
- Tests added or changed:
  - Added `tests/test_regression.py` containing 7 test cases covering sequential partial refunds, refund replay idempotency, balance non-negativity, cumulative excess refund rejection, malformed inputs, full synthetic dataset integration, and CSV statement export.
  - Existing visible tests were left intact and unaltered.
- Commands run and actual results:
  - `python -m pytest -q` -> `221 passed in 0.16s` (100% pass rate).
  - `python -m main` -> Executed successfully (`Points example: 27`, `Repeat warnings: []`).
- Edge cases verified:
  - Boundaries immediately below and at 10,000 paise (Rs 100).
  - Zero and negative rules / bonus / cap values.
  - Replay of purchases and refunds.
  - Sequential partial refunds summing to 100%.
  - Clamping when reversal exceeds current balance.
  - Full invariant verification across all 40 accounts in `data/records.json`.
- Remaining failures or known limitations:
  - Zero remaining test failures.
  - Account state remains in-memory dictionaries; database persistence is left for future productionization.