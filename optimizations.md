# optimizations.md - Required submission

## 1. Baseline and objective
- What needed improvement (correctness, clarity, complexity, memory, repeated work, maintainability)? In the starter `service.py`, `apply_reward_event` was calling `calculate_points` before checking if the event was a duplicate or if the transaction already existed, and it was appending `event_id` to `processed_event_ids` even when the event was invalid. Also, `flag_repeat_transactions` sorted groups using `key=lambda item: str(item[0])`, which converts every `(account_id, date, amount_paise)` tuple into a string on each comparison.
- What evidence suggested an improvement could help? In the baseline run (`py -m pytest -q`), 67 of 214 tests failed (`0.51s`), and invalid events in `data/records.json` caused `TypeError` crashes because there were no early validation checks.

## 2. Options considered
- **Option A: Early return guards, `_is_strict_int` helper, and direct tuple sorting (Implemented)**
  - Expected benefit: Skips `calculate_points` and state updates immediately when `event_id`, `transaction_id`, or `amount_paise` is invalid or already processed. Sorting by `item[0]` directly compares `(account_id, date, amount_paise)` tuples without creating temporary strings.
  - Risk: Low risk since it keeps the exact function signatures and dictionary keys expected by all tests.
- **Option B: Shallow copy instead of `deepcopy(account)` (Rejected)**
  - Expected benefit: Faster when an account has a large `transactions` or `ledger` history.
  - Risk: If we only shallow-copy the account dict, mutating nested dicts like `out['transactions'][txn_id]` would also mutate the input `account` dict passed by the caller, which breaks `test_input_account_not_mutated` and `test_event_processing_does_not_mutate_input_account`.
- **Option C: Change `processed_event_ids` from a `list` to a `set` (Rejected)**
  - Expected benefit: `O(1)` lookup when checking if `event_id` was already processed.
  - Risk: Breaks existing tests (`test_purchase_event_once` and `test_purchase_event_replay_is_idempotent`) that assert `processed_event_ids == ['E1']` as a list.

## 3. Changes implemented
- Change and reason: Added `_is_strict_int(value)` for fast type checks, placed early return guards at the top of `apply_reward_event` before doing point calculations, deduplicated `transaction_id`s in `flag_repeat_transactions`, and changed the sort key from `str(item[0])` to `item[0]`.
- Tests that protect correctness: All 218 tests across `tests/test_contract.py` and `tests/test_acceptance_matrix.py`.
- Measurement method and result (only if measured): Ran `py -m pytest -q` before and after:
  - Baseline: `67 failed, 147 passed in 0.51s`
  - After changes (with 4 extra tests): `218 passed in 0.17s`

## 4. Trade-offs
Keeping `deepcopy(account)` means every call to `apply_reward_event` copies the account structure (`O(N)` in the number of transactions/ledger entries). For the dataset sizes in this project, all 218 tests and the 264 events in `data/records.json` run in `0.17s`, so avoiding accidental mutation bugs is much more important than saving a few microseconds on copying.

## 5. Further improvements
If we had to support accounts with 100,000+ events, replacing the full `deepcopy(account)` with copy-on-write (only copying the top-level dict, the `ledger`/`processed_event_ids` lists, and the specific transaction dict being updated) could be benchmarked while making sure `test_event_processing_does_not_mutate_input_account` still passes.
