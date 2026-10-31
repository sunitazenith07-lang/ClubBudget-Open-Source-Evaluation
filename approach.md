# approach.md - Required submission

Complete this file in your own words. Be concise and specific to the work you actually performed.

## 1. Baseline
- Commands run before editing:
  - `python3 -m pip install -r requirements-dev.txt`
  - `python3 -m pytest -q`
  - `python3 -m main`
- Initial test result (include the actual summary):
  - `67 failed, 147 passed in 0.50s` (total 214 tests).
  - Prominent failure categories:
    - Points rounding: `test_integer_floor_points_calculation` failed on boundary amounts (e.g. 19999 paise returned 2 instead of 1).
    - Cap zero handling: `test_cap_zero_is_respected` failed because `cap_points=0` was treated as falsy.
    - Idempotency replay: `test_purchase_event_replay_is_idempotent` and `test_purchase_event_once` failed because replaying an event appended duplicate IDs to `processed_event_ids`.
    - Refund boundary validation: `test_invalid_or_excess_refund_does_not_change_account` and `test_invalid_or_excess_refund_ignored` failed because negative, non-integer, and excess refund amounts mutated `refunded_paise` and points balances.
- Demo/output observed:
  - `Points example: 28`
  - `Repeat warnings: []`
  - (Note: 28 points was an artifact of round-half-up logic on 259900 paise; the correct integer floor calculation yields 27).

## 2. Codebase understanding
- Important files/functions inspected:
  - `service.py`: Contains `calculate_points()`, `apply_reward_event()`, and `flag_repeat_transactions()`.
  - `models.py`: Defines `new_account()` with state schema: `account_id`, `points_balance`, `processed_event_ids`, `transactions`, `ledger`.
  - `fixtures.py` & `main.py`: Offline demonstration pipeline and sample fixtures.
  - `tests/test_contract.py` & `tests/test_acceptance_matrix.py`: Visible test suite asserting core contract rules, boundary matrices, and idempotency guarantees.
  - `data/records.json`: Expanded dataset containing 40 accounts, 180 repeat-pattern records, 264 reward events, and 8 rule configurations.
- Rewards calculation, refund, ledger or alert flow traced:
  - Calculation flow: `amount_paise` -> floor division by 10000 -> multiply by `points_per_100_rupees` -> bonus percentage floor calculation -> cap constraint.
  - Event processing flow: Deep-copy input account -> validate event/txn IDs -> verify idempotency via `processed_event_ids` -> branch on event kind (`purchase_captured` vs `refund_processed`) -> apply state mutations (balances, transaction record, audit ledger) -> record processed event ID.
  - Repeat alert flow: Group transaction entries by `(account_id, date, amount_paise)` -> filter groups exceeding `threshold` -> sort keys deterministically.
- How you confirmed your understanding:
  - Traced the contract requirements in `STUDENT_PROBLEM_STATEMENT.md` against failing assertion messages in `tests/test_contract.py` and `tests/test_acceptance_matrix.py`.

## 3. Investigation and implementation strategy
For each major defect, describe the symptom, hypothesis, evidence from a test/log/example, and the fix chosen.
- Issue 1: Floating-point/Rounding defect and falsy cap handling in `calculate_points`
  - Symptom: 19999 paise awarded 2 points instead of 1; cap of 0 awarded full uncapped points.
  - Hypothesis: Starter code used Python's `round(amount_paise / 10000)` and checked `if cap_points:`, which ignores `cap_points=0` because 0 is falsy in Python.
  - Evidence: `tests/test_contract.py:5` (`assert calculate_points(19999, 1) == 1`) failed with `assert 2 == 1`. `test_cap_zero_is_respected` failed with `assert 5 == 0`.
  - Fix: Switched to integer floor arithmetic `(amount_paise // 10000) * points_per_100_rupees` and `(base_points * (100 + bonus_percent)) // 100`. Replaced falsy check with `if cap_points is not None:` and explicitly handled `cap_points <= 0` returning 0. Added defensive type and negative input checks.
- Issue 2: Missing replay protection (Idempotency violation) in `apply_reward_event`
  - Symptom: Replaying identical event IDs mutated `processed_event_ids` and created duplicate ledger entries.
  - Hypothesis: `apply_reward_event` unconditionally appended `event_id` to `processed_event_ids` without verifying if it had already been processed.
  - Evidence: `test_purchase_event_replay_is_idempotent` failed with `assert ['PURCHASE-000', 'PURCHASE-000'] == ['PURCHASE-000']`.
  - Fix: Added an early return check: `if event_id in out['processed_event_ids']: return out`. Also validated that missing or non-string/non-int event IDs are safely ignored.
- Issue 3: Unbounded and invalid refund processing in `apply_reward_event`
  - Symptom: Negative refund amounts, non-numeric payloads (`None`, `True`, `"100"`, `[]`), and refunds exceeding the original transaction amount were applied.
  - Hypothesis: Starter lacked input type validation and cumulative refund ceiling checks against `txn['amount_paise']`.
  - Evidence: `test_invalid_or_excess_refund_ignored` failed with `assert (-1 == 0)`.
  - Fix: Added strict validation: `refund` must be an integer, not a boolean, strictly positive (`refund > 0`), and `txn['refunded_paise'] + refund <= txn['amount_paise']`. Used integer arithmetic for proportional reversal, capped delta by `out['points_balance']` to prevent negative balances, and recorded the negative delta in the ledger.

## 4. Implementation decisions
- Main changes and why:
  - Standardized on pure integer arithmetic (`//`) throughout `calculate_points` and refund calculations to prevent precision bugs inherent in floating-point division.
  - Used immutable transformations via `deepcopy(account)` so callers' state is never mutated unexpectedly.
  - Enforced strict validation on event payloads and identifiers (`event_id`, `transaction_id`, `amount_paise`) so that corrupted or declined events are safely ignored without raising exceptions.
- Alternatives considered and why rejected:
  - Using `math.floor(float(amount) / 10000)`: Rejected due to potential float representation issues on large amounts; integer `//` is exact and idiomatic in Python.
  - Mutating the incoming account dictionary in place: Rejected to guarantee idempotency and avoid side effects in calling code.
- Assumptions:
  - Currency amounts are non-negative integers representing paise.
  - A promotional cap of 0 points means zero points are earned.
  - Repeat alerts are informational for operations review and must never block transactions.

## 5. Verification
- Tests added or changed:
  - Added `tests/test_regression.py` containing 8 dedicated test suites verifying:
    - Integer floor arithmetic at paise boundaries.
    - Multiple cumulative partial refunds up to 100% of purchase value.
    - Prevention of negative points balance when refund exceeds current balance.
    - Refund event replay idempotency.
    - Duplicate `transaction_id` capture prevention.
    - Safe handling of missing/empty identifiers and malformed payloads.
    - Robustness of `flag_repeat_transactions` with non-dict/null entries.
- Commands run and actual results:
  - `python3 -m pytest -q`: `222 passed in 0.10s` (100% passing; 214 baseline + 8 regression).
  - `python3 -m main`: Successfully printed `Points example: 27` and `Repeat warnings: []`.
  - Synthetic dataset test: Successfully verified all 264 reward events and 180 transactions from `data/records.json`.
- Edge cases verified:
  - Paise boundary values (9999, 10000, 19999).
  - Cap values: absent (`None`), zero (`0`), negative, and below/above awarded points.
  - Cumulative partial refunds (30% + 30% + 40% = 100%, followed by over-refund attempt).
  - Duplicate events and missing identifier resilience.
- Remaining failures or known limitations:
  - None. All test suites pass.