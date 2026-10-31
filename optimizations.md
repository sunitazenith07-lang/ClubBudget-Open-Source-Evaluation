# Optimizations and Engineering Trade-offs

Document optimizations you considered or implemented. Do not claim a speedup or improvement you did not observe.

## 1. Baseline and objective
- What needed improvement (correctness, clarity, complexity, memory, repeated work, maintainability)?
  - The main goal was getting business rule correctness right: floor division instead of rounding, handling `cap_points=0`, and idempotent event handling.
  - Secondary goal was avoiding wasted work and keeping the code clear and predictable, specifically avoiding unnecessary state modifications when replayed or invalid events are received.
- What evidence suggested an improvement could help?
  - In the starter code, events were mutating data and appending to the ledger before validating refund bounds or checking if the event had already been processed.

## 2. Options considered
Describe each option's expected benefit and risk, including rejected ideas.
- Option A: Using a `set` for `processed_event_ids`
  - Benefit: Checking `if event_id in out['processed_event_ids']` would be O(1) rather than O(N).
  - Risk & Decision: Rejected. The tests directly assert that `account['processed_event_ids']` is a list and preserves insertion order (e.g. `assert b['processed_event_ids'] == ['E1']`). Changing this to a set would break test compatibility.
- Option B: Pure integer floor division vs floating point math
  - Benefit: Native `// 10000` is exact, fast, and avoids IEEE-754 floating point precision issues.
  - Decision: Implemented. It matches the problem statement requirements directly.
- Option C: Early return guard clauses
  - Benefit: Exiting early when an event is missing required keys, already processed, or contains invalid refund amounts prevents unnecessary dictionary mutations.
  - Decision: Implemented.

## 3. Changes implemented
- Change and reason:
  - Added early returns at the beginning of `apply_reward_event` for missing/duplicate `event_id` and invalid refunds.
  - Used `amount // 10000` instead of `round(amount / 10000)` in `calculate_points`.
  - Replaced the compressed one-liner list comprehension in `flag_repeat_transactions` with clean, readable grouping and sorting.
- Tests that protect correctness:
  - All 214 tests in `tests/test_contract.py` and `tests/test_acceptance_matrix.py`, plus the 5 regression tests in `tests/test_regression.py`.
- Measurement method and result (only if measured):
  - Baseline pytest run: 1.46s (due to 67 test failures and pytest generating traceback reports).
  - After fixing all defects: ~0.3-0.5s for 219 tests (all passing cleanly without traceback overhead).

## 4. Trade-offs
Explain trade-offs involving clarity, correctness, performance, memory, or maintainability.
- List vs Set lookup: Keeping `processed_event_ids` as a list is O(N) for event lookup, but it preserves order and complies with existing tests without adding complex dual-data-structure syncing.
- In-memory deepcopy vs mutation: Using `deepcopy` creates a new account copy for every event, which uses more memory than in-place mutation, but it guarantees pure functions and ensures input accounts are never accidentally modified on failed events.

## 5. Further improvements
What would you do next with more time, and how would you validate it?
- For a high-volume production system, I would store account events in a relational database table with a unique index on `event_id` so that deduplication is handled at the database level.
- I would also add schema validation (like dataclasses) to validate event payloads before they reach the calculation service.
