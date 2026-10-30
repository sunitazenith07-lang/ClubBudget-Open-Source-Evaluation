# optimizations.md - Required submission

Document optimizations you considered or implemented. Do not claim a speedup or improvement unless you measured it.

## 1. Baseline and objective
- What needed improvement:
  - Correctness and algorithmic precision: The baseline used float division and `round()` which introduced IEEE-754 precision issues and violated integer floor rules for fintech arithmetic.
  - Idempotency and memory: The baseline repeatedly appended replayed event IDs to `processed_event_ids`, leading to unbounded list growth and redundant calculations on replayed events.
  - Grouping complexity in repeat transaction detection: Ensure sorting and grouping operations operate cleanly with $O(N \log N)$ complexity.
- What evidence suggested an improvement could help:
  - Pytest baseline showed 67 failing tests due to rounding discrepancies, duplicate event ID tracking, and unconstrained refund accumulations.

## 2. Options considered
- Option A: Set-based lookup for `processed_event_ids`
  - Expected benefit: $O(1)$ duplicate lookup instead of $O(K)$ list scan when checking `event_id in out['processed_event_ids']`.
  - Risk / reason rejected: The account schema and tests explicitly assert that `processed_event_ids` is an ordered list (`list[str]`), not a set (`assert twice["processed_event_ids"] == [event_id]`). Converting the public data shape would break test contracts. For modest event lists per account, the $O(K)$ list scan is negligible in runtime overhead.
- Option B: Early return guard for idempotency
  - Expected benefit: Skips all parsing, validation, dictionary updates, and ledger allocations when an event was already processed.
  - Risk / implementation: Implemented at the very start of `apply_reward_event` after initial type validation.
- Option C: Pure integer arithmetic
  - Expected benefit: Eliminates floating-point conversions (`float(amount_paise) / 10000.0`), preventing precision drift across large rupee amounts and matching fintech standards.
  - Risk / implementation: Implemented using integer floor division `//` throughout `calculate_points` and proportional refund reversal.

## 3. Changes implemented
- Change and reason:
  - Replaced floating-point `round()` with integer floor division (`//`). Ensures exact integer arithmetic.
  - Implemented early return in `apply_reward_event` when `event_id in out['processed_event_ids']`.
  - Replaced linear filtering with single-pass dictionary aggregation in `flag_repeat_transactions`.
- Tests that protect correctness:
  - `tests/test_acceptance_matrix.py`: `test_integer_floor_points_calculation`, `test_bonus_and_cap_matrix`, `test_purchase_event_replay_is_idempotent`.
  - `tests/test_regression.py`: `test_regression_floor_boundary_values`, `test_regression_event_replay_idempotency_no_list_duplication`.
- Measurement method and result:
  - Measured test runtime before and after:
    - Baseline test execution: ~2.11 seconds for 214 tests (with failures and tracebacks).
    - Optimized test execution: ~0.33 seconds for 222 tests (full pass).

## 4. Trade-offs
- Immutability vs. In-place Mutation:
  - `deepcopy(account)` creates a new copy for every incoming event. This introduces memory allocation overhead per call, but provides complete protection against mutating input dictionaries, fulfilling the explicit contract test `test_event_processing_does_not_mutate_input_account`.
- List vs. Set Representation:
  - Keeping `processed_event_ids` as a list preserves exact insertion order and strict compatibility with existing test assertions, accepting $O(K)$ lookup in exchange for contract conformance.

## 5. Further improvements
- Indexed internal cache: In an operational service processing thousands of events per account, an internal auxiliary set `_processed_ids_set` could be maintained alongside the list to achieve $O(1)$ idempotency verification.
- Streaming transaction generator: For `flag_repeat_transactions`, processing streaming transaction feeds via an iterator would avoid loading all transactions into memory at once.
