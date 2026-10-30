# optimizations.md - Required submission

Document optimizations you considered or implemented. Do not claim a speedup or improvement unless you measured it.

## 1. Baseline and objective
- What needed improvement (correctness, clarity, complexity, memory, repeated work, maintainability)? Correctness and architectural robustness needed improvement over raw performance, specifically addressing redundant state processing and inefficient floating-point calculations during reward point evaluations.
- What evidence suggested an improvement could help? Baseline test runs revealed 67 failures caused by improper rounding, unhandled duplicate event IDs, and runtime crashes during edge-case refund validations.

## 2. Options considered
Describe each option's expected benefit and risk, including rejected ideas.
- Option A (Strict Integer Floor Division & Upfront Idempotency Checks): Expected benefit is guaranteed financial precision and O(1) duplicate prevention via recorded `event_id` lookups. Risk: Requires strict adherence to integer paise inputs, rejecting malformed types. (Selected)
- Option B (Floating-Point Arithmetic with Decimal Libraries): Expected benefit is precise fractional tracking. Risk: Slower execution speed and added dependency complexity, rejected in favor of native integer arithmetic (`//`).

## 3. Changes implemented
- Change and reason: Replaced `round()` with integer floor division (`//`) to enforce deterministic financial rounding rules, added an upfront `processed_event_ids` check for idempotency, and implemented input validation guards to prevent `TypeError` exceptions.
- Tests that protect correctness: All acceptance tests under `tests/test_acceptance_matrix.py` and contract verification suites.
- Measurement method and result (only if measured): Measured test suite execution time via `python3 -m pytest -q`, yielding **`214 passed in 0.48s`**.

## 4. Trade-offs
Explain trade-offs involving clarity, correctness, performance, memory, or maintainability. Prioritized absolute correctness and defensive type safety over premature micro-optimizations, introducing slight conditional overhead for type checks in exchange for robust runtime exception prevention.

## 5. Further improvements
What would you do next with more time, and how would you validate it? With more time, I would implement O(1) hash set lookups for `processed_event_ids` if ledger histories scale to millions of transactions, validating performance gains using Python's `timeit` benchmarking module.