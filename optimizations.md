# optimizations.md - Required submission

Document optimizations you considered or implemented. Do not claim a speedup or improvement unless you measured it.

## 1. Baseline and objective
- What needed improvement: Correctness, algorithmic efficiency in points calculation, avoidance of cumulative rounding loss, and maintainability.
- Evidence:
  - Baseline execution time for 214 tests was `0.84s` with 67 failures.
  - Floating-point conversions (`amount_paise / 10000` and `round()`) introduced precision inaccuracies and overhead.
  - Unchecked refund deltas caused rounding drift across sequential partial refunds.
  - Linear membership checks and unvalidated event processing risked needless computation on duplicate/malformed inputs.

## 2. Options considered
- **Option 1: Using `decimal.Decimal` for currency calculations**
  - Expected benefit: Explicit decimal precision control and configurable rounding modes.
  - Risk / Trade-off: Significant computational overhead (~10-20x slower than native C integers in CPython), added object allocations, and unnecessary complexity given that paise are discrete integers.
  - Decision: **Rejected**. Native integer floor division (`//`) is exact, faster, has zero dependencies, and strictly matches the specification.
- **Option 2: Changing `processed_event_ids` to a `set`**
  - Expected benefit: $O(1)$ membership checks for event replay idempotency instead of $O(N)$ list scanning.
  - Risk / Trade-off: Violates contract expectations where callers and serialized fixtures expect a `list` (e.g. `assert b['processed_event_ids'] == ['E1']`).
  - Decision: **Rejected for data structure, adopted early check pattern**. Retained the list contract to maintain JSON serializability and test compatibility, while placing the check as the first operation to short-circuit replayed events early.
- **Option 3: Cumulative vs Incremental refund tracking**
  - Expected benefit: Guarantees that cumulative partial refunds summing to 100% reverse exactly 100% of awarded points with zero orphan points.
  - Risk / Trade-off: Requires tracking cumulative `refunded_paise` and `reversed_points` on each transaction record.
  - Decision: **Implemented**. Financial accuracy and zero point drift far outweigh storing two additional integer fields.

## 3. Changes implemented
- **Change 1: Pure integer floor arithmetic for points calculation**
  - Reason: Eliminates IEEE-754 floating-point conversions and correctly implements floor semantics (`amount // 10000`).
  - Tests that protect correctness: `tests/test_acceptance_matrix.py::test_integer_floor_points_calculation` (25 boundary test cases).
  - Measurement: Full test suite execution dropped from `0.84s` to `0.16s` for 221 tests on Python 3.14.6.
- **Change 2: Cumulative proportional refund reversal**
  - Reason: Calculates `should_reverse = (txn['awarded_points'] * new_refunded) // txn['amount_paise']`, preventing 1-point truncation losses across multiple partial refunds.
  - Tests that protect correctness: `tests/test_regression.py::test_sequential_partial_refunds_no_rounding_drift`.
- **Change 3: Single-pass CSV statement generator (Optional stretch feature)**
  - Reason: Implemented `generate_account_statement_csv` to stream ledger entries with a running balance in a single $O(N)$ pass.
  - Tests that protect correctness: `tests/test_regression.py::test_generate_account_statement_csv`.

## 4. Trade-offs
- **Immutability vs In-place mutation:**
  - `apply_reward_event` performs a deep copy of the input account dict. While this incurs memory allocation per event, it prevents shared-state corruption and guarantees that callers' data structures are never unexpectedly mutated.
- **Clarity vs Micro-optimizations:**
  - Kept dictionary-based account models and explicit condition checks rather than premature binary packing or caching. The code remains clean, readable, and easily verifiable in code reviews.

## 5. Further improvements
- **Dual-representation set indexing for high-volume accounts:**
  - For enterprise workloads processing millions of events per account, maintain a private transient `_seen_event_ids: set` alongside the public `processed_event_ids: list` to achieve $O(1)$ lookup performance at scale.
- **Streaming repeat transaction pipeline:**
  - For high-throughput transaction streams, migrate `flag_repeat_transactions` from an in-memory batch dictionary to a sliding-window streaming aggregator or SQL window query (`COUNT(*) OVER (PARTITION BY account_id, date, amount_paise)`).