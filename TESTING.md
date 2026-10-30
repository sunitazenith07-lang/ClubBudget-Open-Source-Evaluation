# TESTING.md — Required submission

## Test command and environment
- Python version: `Python 3.14.6`
- Command run: `py -m pytest -q`
- Actual test summary: `218 passed in 0.17s` (Total: 218, Passed: 218, Failed: 0, Errors: 0, Skipped: 0; baseline before fixes was `67 failed, 147 passed in 0.51s`)

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Purchase amount just below 100 rupees: `calculate_points(19999, 1)` | Floors `19999 // 10000` to `1` point instead of rounding up to `2` | Returns `1` | `tests/test_contract.py::test_points_use_floor` |
| 2 | Zero cap: `calculate_points(50000, 2, 50, cap_points=0)` | Cap of `0` returns `0` points even though base + bonus is `15` | Returns `0` | `tests/test_contract.py::test_cap_zero_is_respected` |
| 3 | Replaying the same purchase or refund `event_id` (`E1`, `E2`) | Second call with the same `event_id` is ignored; balance and ledger do not change | `points_balance` and `ledger` unchanged; `processed_event_ids` has each ID once | `tests/test_contract.py::test_purchase_event_once` & `test_refund_event_replay_and_cumulative_partial_refunds` |
| 4 | All 15 invalid or excess refund inputs (`0, -1, -50, -1000, 100001, 150000, 200000, 999999, True, None, "100", 1.5, [], {}, False`) on a `100000` paise purchase (plus 10 excess inputs in `test_refund_amount_bounds_and_balance`) | Refund is ignored without throwing an error; `refunded_paise` stays `0` and `points_balance` stays `10` | `refunded_paise == 0` and `points_balance == 10` across all 15 cases | `tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account` |
| 5 | Cumulative partial refunds (`30000` + `70000` paise), duplicate refund replay (`E2`), and `1` paisa excess refund (`E4`) on a `100000` paise purchase (`10` points) | First reverses `3` pts (balance `7`), replay of `E2` is ignored (balance `7`), second reverses `7` pts (balance `0`), excess `1` paisa is ignored | Balance goes `10 -> 7 -> 7 -> 0 -> 0`; `refunded_paise == 100000`; `len(ledger) == 3` | `tests/test_contract.py::test_refund_event_replay_and_cumulative_partial_refunds` |
| 6 | Empty/`None` input, duplicate `transaction_id` rows, and `data/records.json` repeat transactions (`180` rows, `threshold=2`) | Empty/`None` returns `[]`; duplicate `transaction_id` is counted once; 180 dataset rows return 60 repeat groups | `flag_repeat_transactions(dup_rows, 2) == []` and `len(alerts) == 60` | `tests/test_contract.py::test_repeat_transactions_handles_empty_malformed_and_dataset` |

## Regression tests added
1. `test_non_int_and_boolean_inputs_to_calculate_points` (`tests/test_contract.py`): checks that `calculate_points` returns `0` for `True`, `False`, floats, strings, `None`, negative `bonus_percent`, and negative `cap_points`.
2. `test_refund_event_replay_and_cumulative_partial_refunds` (`tests/test_contract.py`): checks cumulative partial refunds (`30000` + `70000` paise reversing all `10` points), duplicate refund `event_id` replay (`E2`), rejection of a `1` paisa excess refund (`E4`), and ledger delta sum matching `points_balance`.
3. `test_missing_identifiers_and_duplicate_transaction_capture_ignored` (`tests/test_contract.py`): checks that events missing `event_id` or `transaction_id` or reusing an already captured `transaction_id` are ignored.
4. `test_repeat_transactions_handles_empty_malformed_and_dataset` (`tests/test_contract.py`): checks `[]` and `None` inputs, duplicate `transaction_id` rows, and running the full `data/records.json` dataset.

## Remaining failures or limitations
- No failing tests remain (`218 passed, 0 failed`). Account state is kept in-memory in dictionaries and lists.
