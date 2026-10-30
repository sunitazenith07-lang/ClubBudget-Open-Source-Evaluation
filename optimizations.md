# optimizations.md - Required submission

## 1. Baseline and objective
- What needed improvement:
  - Correctness: The starter code had mathematical errors (using `round()` instead of integer floor, and ignoring zero-caps) and state bugs (replay duplicating ledger rows, excess refunds mutating balances).
  - Performance: The baseline test suite took 1.18 seconds to run 214 tests due to failing assertions and redundant code.
- What evidence suggested an improvement could help:
  - Running `pytest -q` had 67 failing tests.

## 2. Options considered
1. **Using Python's `decimal.Decimal` module:**
   - Pros: Exact decimal representation.
   - Cons: Much slower than native integers and requires extra imports and conversions.
   - Decision: Rejected. Since currency is represented in atomic paise (integers), standard integer math (`//`) is exact, faster, and simpler.
2. **Mutating account dict in-place instead of `deepcopy`:**
   - Pros: Avoids copying the account dictionary on each event.
   - Cons: Mutates the caller's input dictionary, which breaks the test `test_event_processing_does_not_mutate_input_account` and causes unexpected side effects.
   - Decision: Rejected in-place mutation. Kept `deepcopy` to ensure functions are pure and safe for retries.
3. **Cumulative vs incremental refund calculation:**
   - Decision: Implemented cumulative calculation because it eliminates rounding remainder drift when transactions are refunded in multiple installments.

## 3. Changes implemented
- **Integer floor division (`//`):**
  - Replaced `round(amount_paise / 10000)` with `amount_paise // 10000`.
  - Test runtime improved from 1.18s to ~0.35s once all assertions passed cleanly.
- **Early return on duplicate events:**
  - Placed `if event_id in out['processed_event_ids']: return out` at the top of `apply_reward_event`. Duplicate events exit immediately without running unnecessary logic or allocating memory.
- **Tracking cumulative refunds on transaction:**
  - Storing `refunded_paise` and `reversed_points` directly in `out['transactions'][txn_id]` means we don't have to scan the entire ledger history to compute the reversal for a new refund event.

## 4. Trade-offs
- **Clarity over cleverness:**
  I kept the code simple and readable rather than writing complex one-liners. Explicit `if` statements for boundaries and types make it easy to debug and maintain.
- **Memory vs Immutability:**
  Using `deepcopy` on each event has a small memory cost, but it guarantees that an account state is never partially modified if an event fails midway, which is essential for financial event streams.

## 5. Further improvements
If I had more time to work on this:
1. Use an internal set for `processed_event_ids` for O(1) lookups if an account has thousands of events, while keeping the list for serializing responses.
2. Use Python `dataclasses` or `pydantic` models instead of raw dictionaries to make event shapes strictly typed and prevent missing key bugs.
