# approach.md - Required submission

Complete this file in your own words. Be concise and specific to the work you actually performed.

## 1. Baseline
- Commands run before editing:
  - `python -m pip install -r requirements-dev.txt`
  - `python -m pytest`
  - `python -m main`
- Initial test result (include the actual summary):
  - `67 failed, 147 passed, 1 warning in 2.11s` (out of 214 collected tests in `tests/test_acceptance_matrix.py` and `tests/test_contract.py`).
- Demo/output observed:
  - `python -m main` produced:
    `Points example: 29`
    `Repeat warnings: []`

## 2. Codebase understanding
- Important files/functions inspected:
  - `service.py`: Contains core business logic (`calculate_points`, `apply_reward_event`, `flag_repeat_transactions`).
  - `models.py`: Defines `new_account(account_id)` initializing the account dictionary schema (`points_balance`, `processed_event_ids`, `transactions`, `ledger`).
  - `fixtures.py` and `data/records.json`: Synthetic datasets containing test accounts, rules, and edge cases.
  - `tests/test_acceptance_matrix.py` and `tests/test_contract.py`: Test suites defining the business contract for loyalty point awards, idempotency, refund reversals, and repeat transaction detection.
- Rewards calculation, refund, ledger or alert flow traced:
  - `calculate_points`: Converts amount in paise to base points via integer floor division by 10,000 multiplied by `points_per_100_rupees`. Applies bonus percentage using integer floor division, and finally caps with `cap_points` if provided. Invalid/negative rules or amounts return 0.
  - `apply_reward_event`: Receives an immutable account dictionary, event, and rules. Checks if `event_id` was already processed to guarantee idempotency. For `purchase_captured`, records transaction metadata and awards points with a ledger entry. For `refund_processed`, validates refund amount bounds (cannot exceed original purchase), proportionally calculates points to reverse, ensures balance never goes negative, and writes an audit ledger entry.
  - `flag_repeat_transactions`: Groups transactions by `(account_id, date, amount_paise)` and flags groups whose count strictly exceeds the configured threshold in a deterministic sort order.
- How you confirmed your understanding:
  - Read `STUDENT_PROBLEM_STATEMENT.md` specifications and compared them against the failure messages in pytest.

## 3. Investigation and implementation strategy
For each major defect, describe the symptom, hypothesis, evidence from a test/log/example, and the fix chosen.
- Issue 1: `calculate_points` rounding error and cap zero ignored
  - Symptom: 9999 paise awarded 1 point instead of 0 points; cap of 0 points failed to cap points to 0.
  - Hypothesis: Starter implementation used floating-point `round(amount_paise / 10000)` instead of integer floor `amount_paise // 10000`. In addition, `if cap_points:` treated `cap_points=0` as falsy, skipping the cap.
  - Evidence: `test_integer_floor_points_calculation[9999-0_0]` failed (`assert 1 == 0`), and `test_cap_zero_is_respected` failed (`assert 5 == 0`).
  - Fix: Changed formula to `(amount_paise // 10000) * points_per_100_rupees` and `points * (100 + bonus_percent) // 100`. Explicitly checked `if cap_points is not None: points = min(points, cap_points)` and validated that negative amounts or rules return 0.
- Issue 2: Replay idempotency failure and `processed_event_ids` corruption
  - Symptom: Replaying an event added duplicate event IDs to `processed_event_ids` and created duplicate ledger entries.
  - Hypothesis: `apply_reward_event` had no early return guard for already processed event IDs, and unconditionally appended `event_id` to `processed_event_ids` at the end of the function.
  - Evidence: `test_purchase_event_replay_is_idempotent` failed with `AssertionError: assert ['PURCHASE-00...PURCHASE-000'] == ['PURCHASE-000']` (Left contains one more item).
  - Fix: Added an idempotency guard at the start: `if event_id in out['processed_event_ids']: return out`. Only appended `event_id` to `processed_event_ids` when an accepted purchase or refund event was actually processed.
- Issue 3: Excess, negative, and invalid refunds accepted
  - Symptom: Negative refund amounts, excess refunds exceeding original purchase, and non-integer types (e.g. `None`, `bool`, `1.5`, `"100"`) mutated `refunded_paise` and altered `points_balance`.
  - Hypothesis: Starter did not validate the type or positivity of `refund`, nor did it check if `txn['refunded_paise'] + refund > txn['amount_paise']`.
  - Evidence: `test_invalid_or_excess_refund_does_not_change_account` failed for 13 test cases, and `test_refund_amount_bounds_and_balance` failed when `amount > 100000`.
  - Fix: Added strict type and value checks: `not isinstance(refund, int) or isinstance(refund, bool) or refund <= 0`. Checked `txn['refunded_paise'] + refund > txn['amount_paise']` and returned `out` without modifications. Enforced `delta = min(delta, out['points_balance'])` so reversals never produce negative balances.

## 4. Implementation decisions
- Main changes and why:
  - Cleanly separated calculation rules and type checks in `calculate_points`.
  - Guarded against Python's `bool` subclassing `int` (`isinstance(True, int)` is True) across all numeric checks.
  - Maintained full immutability using `deepcopy(account)` and returning copies.
  - Safely handled missing identifiers (`event_id`, `transaction_id`) and non-dict inputs.
- Alternatives considered and why rejected:
  - Mutating input account in-place: Rejected because contract tests mandate that input accounts remain untouched.
  - Raising exceptions on invalid refund amounts: Rejected because the domain specification requires invalid/excess events to be ignored safely without corrupting account state.
- Assumptions:
  - Unrecognized event kinds and invalid events must not alter balances, transactions, or create ledger entries.
  - Threshold in repeat alerts is strictly greater than (`len(ids) > threshold`).

## 5. Verification
- Tests added or changed:
  - Added `tests/test_regression.py` containing 8 dedicated regression tests covering paise boundaries, cap zero, event replay idempotency, refund idempotency, cumulative partial refunds, negative balance prevention, boolean rejection, and malformed repeat transaction inputs.
- Commands run and actual results:
  - `python -m pytest`: 222 passed, 1 warning (deprecation warning in anyio pytest plugin) in 0.33s.
  - `python -m main`: Ran clean and produced `Points example: 27` and `Repeat warnings: []`.
- Edge cases verified:
  - Boundary amounts: 9,999 paise (0 pts), 10,000 paise (1 pt), 19,999 paise (1 pt), 20,000 paise (2 pts).
  - Cap zero: `cap_points=0` resulting in 0 points.
  - Duplicate replay: `PURCHASE-000` replayed multiple times retaining exactly one ledger entry and one entry in `processed_event_ids`.
  - Cumulative refund boundary: Purchase of 100,000 paise refunded with 40,000 paise then 50,000 paise accepted; subsequent 20,000 paise refund rejected as excess.
  - Reversal balance protection: Account points balance prevented from dropping below 0 upon refund reversal.
- Remaining failures or known limitations:
  - None. All 222 tests pass.
