# approach.md - Required submission

Complete this file in your own words. Be concise and specific to the work you actually performed.

## 1. Baseline
- Commands run before editing: `python3 -m pytest -v`, `python3 -m main`
- Initial test result (include the actual summary):
  - 67 failed, 147 passed in 0.46s (214 total tests).
  - Main test failures centered around: `test_integer_floor_points_calculation` (rounding vs floor), `test_cap_zero_is_respected` (`cap_points=0` falsy check), `test_purchase_event_replay_is_idempotent` (duplicate event processing), and `test_invalid_or_excess_refund_does_not_change_account` (unbounded refunds and type leaks).
- Demo/output observed:
  - `Points example: 28`
  - `Repeat warnings: []`

## 2. Codebase understanding
- Important files/functions inspected:
  - `service.py`: `calculate_points()`, `apply_reward_event()`, `flag_repeat_transactions()`
  - `models.py`: `new_account()` schema builder
  - `fixtures.py` and `main.py`: sample accounts, rules, transactions, and execution script
  - `tests/test_contract.py` & `tests/test_acceptance_matrix.py`: test suites defining the business contract
  - `data/records.json`: synthetic accounts, transactions, rules cases, and edge-case catalog
- Rewards calculation, refund, ledger or alert flow traced:
  - Points formula: `base_points = floor(amount_paise / 10000) * points_per_100_rupees`, `bonus_points = floor(base_points * (100 + bonus_percent) / 100)`, with optional `cap_points` applied at the end.
  - Event application: accounts transition state only on `purchase_captured` and `refund_processed`. Each `event_id` must be processed at most once. Cumulative partial refunds reverse awarded points proportionally, ensuring balance never drops below zero and refunds never exceed purchase amount.
  - Repeat alerts: transactions are grouped by `(account_id, date, amount_paise)`. If group size exceeds `threshold`, human-review warning records are emitted.
- How you confirmed your understanding:
  - Traced exact failure assertions against `STUDENT_PROBLEM_STATEMENT.md` specifications, verified arithmetic properties using Python interactive shell, and validated against sample edge cases in `data/records.json`.

## 3. Investigation and implementation strategy
For each major defect, describe the symptom, hypothesis, evidence from a test/log/example, and the fix chosen.
- Issue 1: Rounding and Cap-Zero Defect in `calculate_points()`
  - **Symptom:** `calculate_points(19999, 1)` returned 2 instead of 1; `calculate_points(50000, 1, cap_points=0)` returned 5 instead of 0.
  - **Hypothesis:** Starter code used `round(amount_paise / 10000)` which rounds up for fractional values >= 0.5; and used `if cap_points:` which evaluates to `False` when `cap_points == 0`.
  - **Evidence:** `assert 2 == 1` failure in `test_points_use_floor` and `assert 5 == 0` failure in `test_cap_zero_is_respected`.
  - **Fix:** Switched to integer floor division `amount_paise // 10000` and checked `if cap_points is not None:`. Added checks rejecting negative amounts or rules.
- Issue 2: Idempotency Defect in `apply_reward_event()`
  - **Symptom:** Replaying an already processed event resulted in duplicated `processed_event_ids` and duplicate points modifications.
  - **Hypothesis:** The function never verified whether `event_id` was already present in `account['processed_event_ids']` before updating ledger or balance.
  - **Evidence:** `test_purchase_event_once` failed with `['E1', 'E1'] == ['E1']`.
  - **Fix:** Added immediate guard `if event_id in out['processed_event_ids']: return out`. Also guarded against missing or non-string `event_id` / `transaction_id`.
- Issue 3: Unbounded and Type-Unsafe Refund Processing
  - **Symptom:** Negative refund amounts, excess refund amounts (> original purchase amount), and boolean inputs altered account balances.
  - **Hypothesis:** `apply_reward_event()` did not validate whether `refunded_paise + refund > amount_paise` and did not distinguish `bool` from `int`.
  - **Evidence:** `test_invalid_or_excess_refund_ignored` failed with `assert -1 == 0`.
  - **Fix:** Validated `isinstance(refund, int) and not isinstance(refund, bool)` and checked `txn['refunded_paise'] + refund <= txn['amount_paise']`. Applied proportional cumulative reversal formula: `should_reverse = (txn['awarded_points'] * new_refunded) // txn['amount_paise']`.

## 4. Implementation decisions
- Main changes and why:
  - Added strict type and boundary validations to make all domain functions robust against malformed or adversary inputs.
  - Adopted cumulative proportional refund calculation to eliminate rounding drift across multiple partial refunds.
  - Added `from __future__ import annotations` at the top of `service.py` so that modern union annotations (`int | None`) remain valid across Python 3.9+ environments.
- Alternatives considered and why rejected:
  - Reversing points using individual per-refund step ratios: Rejected because repeated integer division of small partial refunds causes cumulative points discrepancies compared to total refunded amount.
- Assumptions:
  - Malformed events (missing ID, negative amounts, unknown event types) are ignored without mutating existing account balances or polluting the ledger.

## 5. Verification
- Tests added or changed:
  - Created `tests/test_regression.py` containing 10 targeted test cases testing: non-integer type rejection, rule validation, floor boundary values, large bonuses with zero cap, missing ID safety, multi-stage partial refunds, excess refund prevention, refund idempotency, balance non-negativity floor, and deterministic repeat alert ordering.
- Commands run and actual results:
  - `python3 -m pytest -v`: 224 passed, 0 failed in 0.16s.
  - `python3 -m main`: executed successfully, outputting `Points example: 27` and `Repeat warnings: []`.
- Edge cases verified:
  - Strict cap at 0, boundary amounts (9999 vs 10000 paise), replayed event IDs, full and partial refunds, excess refunds, spent balance floor.
- Remaining failures or known limitations:
  - None. 100% of tests pass.