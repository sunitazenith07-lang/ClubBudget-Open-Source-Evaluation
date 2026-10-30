# approach.md - Required submission

Complete this file in your own words. Be concise and specific to the work you actually performed.

## 1. Baseline

- Commands run before editing:
  - `python3 -m pip install -r requirements-dev.txt`
  - `python3 -m pytest -q`
  - `python3 -m main`
- Initial test result (include the actual summary):
  - **67 failed, 147 passed** out of 214 total tests. Exit code 1.
- Demo/output observed:
  - `python3 -m main` printed `Points example: 28` and `Repeat warnings: []`.
  - The points value `28` was incorrect for the sample input (259,900 paise with 10% bonus and cap of 100). The correct value using floor division is `27`.

## 2. Codebase understanding

- Important files/functions inspected:
  - `service.py` — contains the three core functions: `calculate_points`, `apply_reward_event`, and `flag_repeat_transactions`.
  - `models.py` — defines `new_account()`, which creates a fresh account dictionary with `points_balance=0`, an empty `processed_event_ids` list, empty `transactions` dict, and empty `ledger` list.
  - `fixtures.py` — provides sample data (`sample_account`, `sample_transactions`, `sample_rules`) used by `main.py`.
  - `main.py` — offline demo that calls `calculate_points` and `flag_repeat_transactions` with sample data.
  - `tests/test_contract.py` — 12 contract-level tests covering core behaviours.
  - `tests/test_acceptance_matrix.py` — 202 parameterized acceptance tests covering points calculation, event processing, refund bounds, and repeat alerts.
  - `data/records.json` and `data/README.txt` — synthetic dataset with 40 accounts, 264 reward events, and edge cases.
- Rewards calculation, refund, ledger and alert flow traced:
  - **Points flow**: `amount_paise` → divide by 10,000 (for ₹100 blocks) → multiply by `points_per_100_rupees` → apply bonus percent → apply optional cap → clamp to zero minimum.
  - **Purchase flow**: `apply_reward_event` receives an event dict. If `type == 'purchase_captured'` and the `transaction_id` is new, it calculates points, updates the balance, records the transaction, writes a ledger entry, and tracks the `event_id`.
  - **Refund flow**: If `type == 'refund_processed'` and the `transaction_id` exists, the function calculates a proportional reversal using integer arithmetic: `awarded_points * total_refunded_paise // original_amount_paise`. It deducts the delta from the balance and records a negative ledger entry.
  - **Repeat alert flow**: `flag_repeat_transactions` groups transactions by `(account_id, date, amount_paise)` and returns groups exceeding the threshold count.
- How I confirmed my understanding:
  - Read the spec (required behaviour items 1–8 in `STUDENT_PROBLEM_STATEMENT.md`).
  - Traced each failing test back to its assertion to identify which spec rule was being violated.
  - Manually calculated expected outputs (e.g., `19999 // 10000 = 1`, not `round(19999/10000) = 2`).

## 3. Investigation and implementation strategy

For each major defect, the symptom, hypothesis, evidence from a test, and the fix chosen:

- **Issue 1 — `calculate_points` uses `round()` instead of floor division**
  - Symptom: `test_integer_floor_points_calculation[9999-0]` failed — `calculate_points(9999, 1)` returned `1` instead of `0`.
  - Hypothesis: `round(9999 / 10000)` rounds `0.9999` to `1`. The spec requires `floor(amount_paise / 10000)`.
  - Evidence: All 11 boundary-value tests at amounts like 9999, 19999, 29999, 49999, 99999 failed because `round()` rounded up at .5 boundaries.
  - Fix: Replace `round(amount_paise / 10000)` with `amount_paise // 10000` (integer floor division). Also added an input guard (`isinstance` check and `<= 0` check) to reject negative or non-integer amounts.

- **Issue 2 — `cap_points=0` treated as no cap**
  - Symptom: `test_cap_zero_is_respected` failed — `calculate_points(50000, 1, cap_points=0)` returned `5` instead of `0`.
  - Hypothesis: `if cap_points:` evaluates `0` as `False` in Python, skipping the cap.
  - Evidence: The spec states "A cap of zero means zero points." The `if cap_points:` guard was falsy for `cap_points=0`.
  - Fix: Replace `if cap_points:` with `if cap_points is not None:`. This distinguishes "no cap" (`None`) from "cap at zero" (`0`).

- **Issue 3 — No event-ID idempotency and no refund validation**
  - Symptom: `test_purchase_event_replay_is_idempotent` (20 parameterized cases) all failed — replaying the same event awarded points twice. `test_invalid_or_excess_refund_does_not_change_account` (13 cases) also failed — negative and excess refunds modified the account.
  - Hypothesis: The function checked `transaction_id` for purchase dedup but never checked `event_id`. Refund amounts were not validated. `processed_event_ids.append()` ran unconditionally for all events.
  - Evidence: The original code at line 29 had `out['processed_event_ids'].append(event_id)` outside all branches, and there was no early return for already-seen `event_id` values.
  - Fix: (a) Add `if event_id is None: return out` to reject events without IDs. (b) Add `if event_id in out['processed_event_ids']: return out` for idempotency. (c) Move `append(event_id)` inside the purchase and refund branches so only accepted events are tracked. (d) Add refund validation: type check (`isinstance`, excluding `bool`), positive check, and bounds check (`refund + already_refunded <= original_amount`).

## 4. Implementation decisions

- Main changes and why:
  - All fixes are in `service.py` only. No other source files needed changes.
  - Added `tests/test_event_id_regression.py` with 9 tests covering the `None` event_id guard and idempotency behaviour.
- Alternatives considered and why rejected:
  - **Changing `processed_event_ids` from a list to a set**: Would improve lookup speed from O(n) to O(1), but would change the data model in `models.py` and could break JSON serialization. Rejected to keep changes minimal and avoid modifying unrelated files.
  - **Processing events with `None` event_id anyway (without dedup)**: Would re-introduce the original replay vulnerability for any event missing an ID. Rejected because the safer behaviour is to refuse events that cannot be tracked.
- Assumptions:
  - Amounts are in integer paise (100 paise = ₹1).
  - `None` for `cap_points` means "no cap", while `0` means "cap at zero points".
  - An event without a valid `event_id` should be safely rejected rather than processed without idempotency guarantees.

## 5. Verification

- Tests added or changed:
  - Created `tests/test_event_id_regression.py` with 9 test functions. No existing tests were modified, deleted, skipped, or weakened.
- Commands run and actual results:
  - `python3 -m pytest -v` — **223 passed in 0.11s** (214 original + 9 new). Zero failures.
  - `python3 -m main` — output: `Points example: 27`, `Repeat warnings: []`. The points value is now correct.
- Edge cases verified:
  - `amount_paise = 0` → 0 points.
  - `amount_paise = True` (bool subclass of int) → 0 points (caught by `<= 0` since `True == 1` but `1 <= 0` is False; however `True` correctly produces 0 from `1 // 10000 = 0`).
  - `cap_points = 0` → 0 points.
  - `cap_points = -5` → 0 points (negative cap produces negative via `min`, clamped by `max(0, ...)`).
  - Refund with `amount_paise = True`, `None`, `"100"`, `[]`, `{}`, `1.5` → all rejected.
  - Refund exceeding original purchase amount → rejected.
  - Multiple partial refunds summing to original → accepted; next one exceeding remainder → rejected.
  - Two events with `event_id = None` → both rejected, no collision.
- Remaining failures or known limitations:
  - None. All 223 tests pass. The `processed_event_ids` list uses O(n) lookup, which is a known performance consideration for very large accounts but does not affect correctness.

Record actual engineering decisions and evidence. Do not claim tests or experiments you did not run.
