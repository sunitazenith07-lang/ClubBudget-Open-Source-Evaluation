# approach.md - Required submission

## 1. Baseline
- **Commands run before editing:**
  - `python --version` (Python 3.13.15 on Windows)
  - `python -m pytest -q`
  - `python -m main`
- **Initial test result (include the actual summary):**
  - Baseline execution failed: `67 failed, 147 passed in 0.79s` (out of 214 tests).
  - Main points of failure observed in `tests/test_acceptance_matrix.py` and `tests/test_contract.py`:
    - Floating-point `round()` used instead of integer floor division for base points (e.g. 9,999 paise awarded 1 point instead of 0, 19,999 awarded 2 instead of 1).
    - Falsy evaluation of `cap_points` (`if cap_points:`) ignored `cap_points = 0`, failing to clamp points to 0.
    - Lack of idempotency checks on `event_id`, causing duplicate event IDs to re-execute and duplicate ledger entries.
    - Lack of bounds checking on refunds, allowing excess refunds (> transaction amount) and invalid/malformed refund values (booleans, strings, negative values).
- **Demo/output observed:**
  - `Points example: 28` (due to `round(25.99) = 26` -> `26 * 1.10 = 28` instead of integer floor `25` -> `25 * 110 // 100 = 27`).
  - `Repeat warnings: []` (under default threshold 2).

## 2. Codebase understanding
- **Important files/functions inspected:**
  - `service.py`: Contains core business logic (`calculate_points`, `apply_reward_event`, `flag_repeat_transactions`).
  - `models.py`: Account structure definition with `new_account(account_id)`.
  - `fixtures.py` and `data/records.json`: Test data and 10 catalogued edge-case scenarios.
  - `tests/test_contract.py` & `tests/test_acceptance_matrix.py`: Acceptance contracts protecting floor calculation, idempotency, refund reversibility, ledger updates, and repeat transaction threshold logic.
- **Rewards calculation, refund, ledger or alert flow traced:**
  - Purchase capture flow: `apply_reward_event` receives `account`, `event` (`purchase_captured`), and `rules`. Computes points via `calculate_points`, updates `account['transactions']`, adds points to `account['points_balance']`, logs an immutable ledger entry, and records `event_id` in `account['processed_event_ids']`.
  - Refund flow: `apply_reward_event` receives `event` (`refund_processed`). Validates transaction existence and remaining refundable paise. Computes proportional reversed points using integer arithmetic: `should_reverse = (txn['awarded_points'] * cumulative_refunded) // txn['amount_paise']`, calculates `delta = should_reverse - txn['reversed_points']`, clamps to current `points_balance` so balance never drops below zero, records negative ledger delta, and logs `event_id`.
  - Alert flow: `flag_repeat_transactions` groups transactions by `(account_id, date, amount_paise)` and flags any group where `len(transaction_ids) > threshold` with deterministic lexicographical ordering.
- **How you confirmed your understanding:**
  - Traced data flow and assertions in `tests/test_acceptance_matrix.py` lines 7-144.
  - Inspected sample synthetic records in `data/records.json` covering duplicate events, multi-step refunds, and edge cases.

## 3. Investigation and implementation strategy
For each major defect, describe the symptom, hypothesis, evidence from a test/log/example, and the fix chosen.

- **Issue 1: Inaccurate points calculation due to floating-point rounding and falsy cap check**
  - *Symptom:* `test_integer_floor_points_calculation[9999-0]`, `test_cap_zero_is_respected`, and related matrix tests failed with `assert 1 == 0` or `assert 5 == 0`.
  - *Hypothesis:* Starter code utilized `round(amount_paise / 10000)` which rounded up whenever fractional paise >= 0.50 rupees, violating the integer floor arithmetic specification. Furthermore, `if cap_points:` evaluated `0` as falsy, bypassing cap clamping when `cap_points == 0`.
  - *Evidence:* In `service.py`, `calculate_points(19999, 1)` gave 2 instead of 1; `calculate_points(50000, 1, cap_points=0)` returned 5 instead of 0.
  - *Fix:* Replaced `round()` with integer floor division `amount_paise // 10000`. Refactored cap checking to explicitly test `if cap_points is not None: bonus_points = min(bonus_points, cap_points)`. Added type safety checks ensuring inputs are valid integers and not booleans (`isinstance(x, int) and not isinstance(x, bool)`).

- **Issue 2: Non-idempotent event processing and ledger duplication**
  - *Symptom:* Replaying an event with the same `event_id` modified state twice or appended duplicate event IDs to `processed_event_ids` and `ledger`.
  - *Hypothesis:* `apply_reward_event` did not check whether `event_id` was already present in `account['processed_event_ids']` before executing mutations.
  - *Evidence:* `test_purchase_event_replay_is_idempotent` failed across 20 parameterized test cases because `twice['processed_event_ids']` contained duplicates (`['PURCHASE-000', 'PURCHASE-000']`).
  - *Fix:* Added an upfront idempotency guard: `if event_id in out['processed_event_ids']: return out`.

- **Issue 3: Missing refund validation, over-refunding, and balance overdrafts**
  - *Symptom:* `test_refund_amount_bounds_and_balance` and `test_invalid_or_excess_refund_does_not_change_account` failed for amounts > purchase amount or non-positive / invalid types.
  - *Hypothesis:* Starter code blindly added `txn['refunded_paise'] += refund` without validating against `txn['amount_paise']`, and allowed negative/non-integer amounts to alter state.
  - *Evidence:* Refunding 125,000 paise on a 100,000 paise purchase modified the account rather than being rejected.
  - *Fix:* Validated that `refund` is a positive `int` (excluding `bool`), verified `txn['refunded_paise'] + refund <= txn['amount_paise']`, computed cumulative proportional reversal, and clamped reversal `delta` to `out['points_balance']` so balance never drops below 0.

## 4. Implementation decisions
- **Main changes and why:**
  - Implemented strict integer arithmetic (`//`) throughout `calculate_points` and proportional refund reversal to prevent IEEE 754 floating-point inaccuracies.
  - Preserved immutability: deep-copied input `account` before mutation to ensure original state is never modified in-place.
  - Handled Python's boolean type inheritance (`bool` is a subclass of `int`) by explicitly excluding booleans from numeric validations.
  - Added optional stretch function `generate_account_statement_csv` for ledger exports.
- **Alternatives considered and why rejected:**
  - *Alternative 1: Decimal module.* Rejected because problem statement explicitly mandates integer arithmetic (`floor(amount_paise / 10000)` and integer floor division). Integer arithmetic in Python has arbitrary precision and zero floating-point drift.
  - *Alternative 2: Tracking event IDs in a Set.* While `O(1)` lookup is faster for large sets, the interface specification and tests expect `account['processed_event_ids']` to remain a JSON-serializable `list`.
- **Assumptions:**
  - paise values and thresholds are non-negative integers; negative or invalid values are rejected and produce 0 points.
  - Repeat alerts are for human review only and do not alter transaction execution.

## 5. Verification
- **Tests added or changed:**
  - Preserved all existing 214 tests without modifications or skipping.
  - Added new regression suite `tests/test_regression_and_edge_cases.py` (9 tests) verifying paise boundaries, multi-step partial refund consistency, cumulative excess refund rejection, type safety, idempotent refund replay, and CSV generation.
- **Commands run and actual results:**
  - `python -m pytest -q` -> `223 passed in 0.20s` (100% passing).
  - `python -m main` -> Executed successfully, producing `Points example: 27`, `Repeat warnings: []`.
- **Edge cases verified:**
  - Paise boundary values (9999 -> 0, 10000 -> 1, 19999 -> 1, 20000 -> 2).
  - Zero and negative caps (`cap_points=0` -> 0, `cap_points=-10` -> 0).
  - Multi-step partial refunds (33,333 + 33,333 + 33,334 paise on a 100,000 paise purchase reversing exactly 3 + 3 + 4 = 10 points).
  - Over-refund rejection on cumulative refunds.
  - Rejection of invalid types (`True`, `False`, `None`, strings, floats, lists).
- **Remaining failures or known limitations:**
  - Zero remaining test failures; 223/223 tests passing cleanly.
