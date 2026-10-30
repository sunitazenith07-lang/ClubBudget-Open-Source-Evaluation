# challenges.md - COMPULSORY submission

## 1. Challenge or confusing behaviour
The main issues that stood out during testing were how Python handles booleans as integers, along with how partial refunds and `cap_points=0` behave on boundary inputs:
1. In `test_invalid_or_excess_refund_does_not_change_account` (which tests 15 invalid inputs: `0, -1, -50, -1000, 100001, 150000, 200000, 999999, True, None, "100", 1.5, [], {}, False`), `True` and `False` are passed as the refund `amount_paise`. Since `bool` is a subclass of `int` in Python, a normal `isinstance(amount, int) and amount > 0` check lets `True` through as `1` paisa.
2. In `calculate_points`, the starter code had `if cap_points: points = min(points, cap_points)`. When `cap_points=0` was passed, Python treated `0` as `False` and skipped the cap completely. Also, when inspecting `data/records.json`, `REPEAT-GROUP-001` had repeat transactions with `amount_paise: 0`, whereas `test_repeat_alerts_do_not_mix_distinct_keys` also tested `amount_paise` values like `0` and `-1`.

## 2. Evidence
From the initial `py -m pytest -q` run (`67 failed, 147 passed in 0.51s`):
- `FAILED tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account[True]` -> `result["transactions"]["T"]["refunded_paise"]` became `1` instead of staying `0`.
- `FAILED tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account[None]` -> raised `TypeError: unsupported operand type(s) for +=: 'int' and 'NoneType'` (same for `"100"`, `1.5`, `[]`, `{}`).
- `FAILED tests/test_contract.py::test_cap_zero_is_respected` -> `calculate_points(50000, 1, cap_points=0)` returned `5` instead of `0`.
- `FAILED tests/test_contract.py::test_purchase_event_once` -> `b['processed_event_ids']` had `['E1', 'E1']` instead of `['E1']`.

## 3. What I tried
1. First, checked why `True` was passing the integer check in `apply_reward_event`. Tested `isinstance(True, int) and not isinstance(True, bool)` in Python and confirmed that it returns `False` for `True`/`False` while returning `True` for normal integers.
2. Next, loaded `data/records.json` to see what kind of bad inputs and repeat patterns were in the dataset. Found events with missing `event_id`, floats (`1.5`), strings (`"100"`), empty lists (`[]`), and 60 repeat groups of 3 transactions each (including `REPEAT-GROUP-001` which uses `amount_paise: 0`).
3. For partial refunds, tested what happens when a `100000` paise purchase (`10` points) gets refunded in two parts (`30000` paise then `70000` paise), replayed with the same `event_id`, and then given an extra `1` paisa refund. Checking `txn['refunded_paise'] + refund <= txn['amount_paise']` caught the extra `1` paisa refund while letting the two valid partial refunds reverse all `10` points.

## 4. Resolution
- Wrote a helper `_is_strict_int(value)` (`isinstance(value, int) and not isinstance(value, bool)`) in `service.py` and used it in all three functions.
- Changed the cap check in `calculate_points` to `if cap_points is not None:` and returned `0` if `cap_points <= 0` or not a strict int.
- In `apply_reward_event`, added upfront checks for `event_id`, `transaction_id`, and `event_id in out['processed_event_ids']`. For refunds, checked `_is_strict_int(refund) and refund > 0` and `txn['refunded_paise'] + refund <= txn['amount_paise']` before changing the transaction or balance.
- Only appended `event_id` to `processed_event_ids` when a purchase or refund event actually succeeded.

## 5. Proof and regression prevention
- All 15 cases in `test_invalid_or_excess_refund_does_not_change_account`, all 20 cases in `test_refund_amount_bounds_and_balance` (10 valid + 10 excess), and `test_cap_zero_is_respected` now pass.
- Added 4 regression tests in `tests/test_contract.py`:
  - `test_non_int_and_boolean_inputs_to_calculate_points`
  - `test_refund_event_replay_and_cumulative_partial_refunds`
  - `test_missing_identifiers_and_duplicate_transaction_capture_ignored`
  - `test_repeat_transactions_handles_empty_malformed_and_dataset`

## 6. Unresolved challenge or next step
- `processed_event_ids` is a `list` because the tests check `processed_event_ids == ['E1']`. Searching a list takes `O(N)` time per event, which is fine for normal account sizes, but if an account had tens of thousands of events, we would want to keep a set alongside the list for `O(1)` lookups.
