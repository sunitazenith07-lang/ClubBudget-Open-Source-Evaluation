# approach.md - Required submission

## 1. Baseline
- Commands run before editing:
  - `python -m pip install -r requirements-dev.txt`
  - `python -m pytest -q`
  - `python -m main`
- Initial test result (include the actual summary):
  - `67 failed, 147 passed in 1.18s` (total 214 tests).
  - Main test failures were in `test_acceptance_matrix.py` (floor calculation, cap of 0, refund limits, event replay idempotency).
- Demo/output observed:
  - `Points example: 28`
  - `Repeat warnings: []`

## 2. Codebase understanding
- Important files/functions inspected:
  - `service.py`: Contains `calculate_points`, `apply_reward_event`, and `flag_repeat_transactions`.
  - `models.py`: Initializes an empty account dictionary (`new_account`).
  - `fixtures.py` and `data/records.json`: Synthetic datasets for rules, transactions, and event streams.
  - `tests/`: Contains `test_contract.py` and `test_acceptance_matrix.py`.
- Rewards calculation, refund, ledger or alert flow traced:
  - `calculate_points` is called when a purchase is captured to compute points.
  - `apply_reward_event` receives an event and rules, checks whether it's a purchase or refund, updates the account points balance, updates transaction metadata, and logs an entry to the ledger.
  - `flag_repeat_transactions` groups transactions by account, date, and amount to flag repeats exceeding the threshold.
- How you confirmed your understanding:
  - Looked at failing test traces to see where actual output differed from expected assertions.
  - For example, `calculate_points(9999, 1)` gave 1 instead of 0, which immediately showed me that `round()` was being used instead of integer floor.

## 3. Investigation and implementation strategy
- Issue 1: Points rounding instead of integer floor
  - Symptom: `calculate_points(9999, 1)` returned 1 instead of 0.
  - Hypothesis: The code was using `round(amount_paise / 10000)`, which rounds 99.99 rupees up to 100.
  - Evidence: `test_integer_floor_points_calculation` had 13 failures at boundary numbers like 9999, 19999, 29999.
  - Fix: Changed to integer floor division using `amount_paise // 10000`.
- Issue 2: Cap of zero ignored
  - Symptom: `test_cap_zero_is_respected` failed with `assert 5 == 0`.
  - Hypothesis: The code did `if cap_points:`, which in Python evaluates `0` as False, skipping the cap.
  - Evidence: Passing `cap_points=0` completely bypassed the cap block.
  - Fix: Changed to `if cap_points is not None:`. If `cap_points <= 0`, return 0 points directly.
- Issue 3: Replaying events duplicate ledger entries and event IDs
  - Symptom: `test_purchase_event_replay_is_idempotent` failed across 20 event test cases.
  - Hypothesis: `event_id` was being appended to `processed_event_ids` on every call, even if the event had already been seen.
  - Evidence: `twice['processed_event_ids']` had `['PURCHASE-000', 'PURCHASE-000']`.
  - Fix: Added an early check at the top of `apply_reward_event`: if `event_id in out['processed_event_ids']`, return immediately without touching anything.
- Issue 4: Refunds not validated and partial refunds losing points
  - Symptom: Tests failed on negative refunds, refunds exceeding purchase amount, and non-integer amounts.
  - Hypothesis: Starter had no bounds checking on `refund` and didn't prevent cumulative refunds from exceeding the purchase amount.
  - Evidence: Excess refunds and negative numbers modified the account.
  - Fix: Added checks for `refund > 0`, `not isinstance(refund, bool)`, and ensured `refunded_paise + refund <= original_amount`. For proportional point reversals, I calculated the reversal based on cumulative refunded paise so that rounding remains exact.

## 4. Implementation decisions
- Main changes and why:
  - Used standard integer math (`//`) throughout to avoid floating-point inaccuracies.
  - Checked `not isinstance(x, bool)` because in Python `bool` inherits from `int` (`isinstance(True, int)` is True).
  - Used `deepcopy` on the account to keep functions pure and avoid mutating the caller's dictionary.
- Alternatives considered and why rejected:
  - Looked at `decimal.Decimal`, but rejected it because paise is already an integer unit. Standard integer arithmetic in Python is exact and faster.
  - Thought about calculating refund deltas independently, but realized multiple partial refunds would lose points due to rounding down each time.
- Assumptions:
  - All currency amounts are positive integers in paise.
  - Unknown or declined events should be safely ignored and not change balances or ledger.

## 5. Verification
- Tests added or changed:
  - Kept all original tests untouched in `test_contract.py` and `test_acceptance_matrix.py`.
  - Added `tests/test_regression.py` covering multi-step partial refunds, refund replay idempotency, booleans, and ledger delta consistency.
- Commands run and actual results:
  - `python -m pytest -q` -> `220 passed in 0.40s` (0 failures).
  - `python -m main` -> `Points example: 27`, `Repeat warnings: []`.
- Edge cases verified:
  - 9999 paise (0 points).
  - Cap of 0 (0 points).
  - Three partial refunds summing to 100% reversing exactly all awarded points.
  - Duplicate event IDs ignored.
- Remaining failures or known limitations:
  - None in the visible tests.
  - The implementation is in-memory; in a real production system, we'd need database transactions to handle concurrent requests.
