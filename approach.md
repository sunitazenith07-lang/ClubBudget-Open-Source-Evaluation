# approach.md - Required submission

## 1. Baseline
- Commands run before editing: `py --version` (`Python 3.14.6`), `py -m pytest -q`, and `py -m main`
- Initial test result (include the actual summary): `67 failed, 147 passed in 0.51s` (214 total tests)
- Demo/output observed: `py -m main` printed `Points example: 28` and `Repeat warnings: []`. For `259900` paise, `service.py` used `round(amount_paise / 10000)` which rounded `25.99` up to `26` base points (and `28` after the 10% bonus) instead of flooring to `25` base points (`27` after bonus).

## 2. Codebase understanding
- Important files/functions inspected:
  - `service.py`: contains `calculate_points`, `apply_reward_event`, and `flag_repeat_transactions`.
  - `models.py`: has `new_account(account_id)` which sets up the account dict (`points_balance`, `processed_event_ids`, `transactions`, `ledger`).
  - `fixtures.py` and `main.py`: sample rule and transaction data used by the demo script.
  - `data/records.json` and `data/README.txt`: larger synthetic dataset with 40 accounts, 180 repeat transactions, 264 reward events, and edge cases.
  - `tests/test_contract.py` and `tests/test_acceptance_matrix.py`: unit and parametrized tests checking points rules, refunds, idempotency, and repeat alerts.
- Rewards calculation, refund, ledger or alert flow traced:
  - `calculate_points` converts `amount_paise` into whole 100-rupee units (`amount_paise // 10000`), multiplies by `points_per_100_rupees`, applies `bonus_percent` using integer floor division, and caps the result at `cap_points` if provided.
  - `apply_reward_event` deep-copies the account dict, checks if the event is valid and hasn't been processed yet, updates `transactions` and `points_balance` for `purchase_captured` or `refund_processed`, and appends a record to `ledger` and `processed_event_ids`.
  - `flag_repeat_transactions` groups transactions by `(account_id, date, amount_paise)` and returns groups where the number of transactions is greater than `threshold`.
- How you confirmed your understanding: Read through the 67 failed pytest outputs and compared them with `service.py`, `data/records.json`, and the 8 rules in `STUDENT_PROBLEM_STATEMENT.md`.

## 3. Investigation and implementation strategy
- Issue 1: `calculate_points` used `round()` instead of floor division and ignored `cap_points=0`
  - Symptom: 22 tests failed across `test_points_use_floor`, `test_cap_zero_is_respected`, `test_integer_floor_points_calculation`, `test_bonus_and_cap_matrix`, and `test_capture_purchase_records_consistent_transaction`.
  - Hypothesis: `round(amount_paise / 10000)` rounds up when the remainder is 5000 paise or more, and `if cap_points:` treats `0` as falsy so a cap of `0` is skipped.
  - Evidence: `calculate_points(19999, 1)` returned `2` instead of `1`, and `calculate_points(50000, 1, cap_points=0)` returned `5` instead of `0`.
  - Fix chosen: Used `(amount_paise // 10000) * points_per_100_rupees` for base points, checked `if cap_points is not None:`, and added input validation so negative/zero amounts or rules (or `cap_points <= 0`) return `0`.
- Issue 2: `apply_reward_event` did not check `processed_event_ids` before processing events
  - Symptom: 21 tests failed (`test_purchase_event_once` and all 20 cases in `test_purchase_event_replay_is_idempotent`).
  - Hypothesis: `apply_reward_event` appended `event_id` to `processed_event_ids` at the end of the function without ever checking if `event_id` was already in `processed_event_ids`.
  - Evidence: Running `apply_reward_event` twice with `event_id='E1'` gave `points_balance == 4` and `processed_event_ids == ['E1', 'E1']`.
  - Fix chosen: Added a check at the start of `apply_reward_event` to verify `event_id` and `transaction_id` are non-empty strings and return early if `event_id in out['processed_event_ids']`. Also moved `out['processed_event_ids'].append(event_id)` inside the accepted purchase and refund branches.
- Issue 3: `apply_reward_event` accepted invalid, negative, boolean, and excess refund amounts
  - Symptom: 24 tests failed across `test_invalid_or_excess_refund_ignored` (1 failure), `test_refund_amount_bounds_and_balance` (10 excess-refund failures out of 20 inputs), and `test_invalid_or_excess_refund_does_not_change_account` (13 failures out of 15 invalid inputs; `0` and `False` happened to leave `refunded_paise` at `0`).
  - Hypothesis: The refund branch did not check if `refund` was a valid positive integer or if `txn['refunded_paise'] + refund` exceeded `txn['amount_paise']`.
  - Evidence: Refunding `-1` or `150000` on a `100000` paise purchase changed `refunded_paise` and `points_balance`, passing `True` treated the refund as `1` paisa, and passing `None` or `"100"` threw a `TypeError`.
  - Fix chosen: Added a helper `_is_strict_int(value)` (`isinstance(value, int) and not isinstance(value, bool)`), rejected refunds where `refund <= 0` or `txn['refunded_paise'] + refund > txn['amount_paise']`, and clamped reversed points so balances never go negative.

## 4. Implementation decisions
- Main changes and why:
  - Added `_is_strict_int` because in Python `isinstance(True, int)` is `True`, which caused `test_invalid_or_excess_refund_does_not_change_account[True]` to fail before excluding `bool`.
  - Used cumulative `refunded_paise` (`(txn['awarded_points'] * txn['refunded_paise']) // max(1, txn['amount_paise'])`) to calculate how many total points should be reversed so far, then subtracted `txn['reversed_points']`.
  - Added checks in `flag_repeat_transactions` for `None`/non-list inputs, missing fields, non-captured status values, and duplicate `transaction_id`s in the same group.
- Alternatives considered and why rejected:
  - Calculating each partial refund reversal separately as `(awarded_points * refund) // amount_paise` was rejected because if a transaction has multiple small refunds that add up to the full amount, integer floor division on each step can leave unreversed points behind. Using cumulative `refunded_paise` avoids that issue.
- Assumptions:
  - Captured purchases must have a positive integer `amount_paise > 0` (purchases under 100 rupees, like 5000 paise, are still valid purchases and get recorded with 0 awarded points).
  - Repeat alerts only trigger when the number of distinct transactions for `(account_id, date, amount_paise)` is strictly greater than `threshold`.

## 5. Verification
- Tests added or changed: Added 4 tests in `tests/test_contract.py`:
  - `test_non_int_and_boolean_inputs_to_calculate_points`
  - `test_refund_event_replay_and_cumulative_partial_refunds`
  - `test_missing_identifiers_and_duplicate_transaction_capture_ignored`
  - `test_repeat_transactions_handles_empty_malformed_and_dataset`
- Commands run and actual results:
  - `py -m pytest -q` -> `218 passed in 0.17s`
  - `py -m main` -> `Points example: 27` and `Repeat warnings: []`
- Edge cases verified: Floor boundaries (`9999`, `10000`, `19999`), `cap_points=0` and negative caps, `bool`/`float`/`str`/`None` inputs, duplicate `event_id` replays for purchases and refunds, multi-step partial refunds followed by a 1-paisa over-refund, and running `data/records.json` through the service functions.
- Remaining failures or known limitations: All 218 tests pass with 0 failures. State is kept in memory in dictionaries/lists since there is no database layer in this project.
