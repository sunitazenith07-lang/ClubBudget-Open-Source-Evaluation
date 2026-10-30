# optimizations.md - Required submission

## 1. Baseline and objective
- What needed improvement (correctness, clarity, complexity, memory, repeated work, maintainability)? Correctness and readability of `service.py`, plus avoiding unnecessary work when inputs or events are invalid.
- What evidence suggested an improvement could help? The starter code put multiple statements on single lines, used float division `int(... / ...)` for refunds, and sorted tuple keys by converting them to strings (`key=lambda item: str(item[0])`).

## 2. Options considered
- For sorting repeat alerts: keep `key=lambda item: str(item[0])` vs. filter out `None`/invalid keys while looping so the tuple `(account_id, date, amount_paise)` can be sorted directly.
- Sorting via `str()` can sort amounts alphabetically (e.g. `100000` before `20000`), whereas filtering bad rows first lets Python compare `(str, str, int)` tuples cleanly and skips invalid rows early.

## 3. Changes implemented
- Change and reason: Added early return checks for invalid inputs, switched refund reversal from `int(a * b / c)` to integer floor division `(a * b) // c`, and cleaned up key validation and sorting in `flag_repeat_transactions`.
- Tests that protect correctness: All 216 tests in `tests/test_contract.py` and `tests/test_acceptance_matrix.py`.
- Measurement method and result (only if measured): Not benchmarked for speed since the dataset is small; the full test suite finishes in about 0.1s.

## 4. Trade-offs
Adding input validation checks adds a few extra `if` statements per call, which has negligible cost and makes the functions safe against bad data.

## 5. Further improvements
Right now `event_id in out['processed_event_ids']` scans a list (`O(n)`). If an account had thousands of events, keeping a set of seen event IDs would make duplicate checks `O(1)`.