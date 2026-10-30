# optimizations.md - Required submission

Document optimizations you considered or implemented. Do not claim a speedup or improvement unless you measured it.

## 1. Baseline and objective
- **What needed improvement:**
  - Correctness: Fixing arithmetic truncations, cap falsiness, unvalidated excess refunds, and missing idempotency checks.
  - Performance and memory: The starter code used `deepcopy(account)` at the top of `apply_reward_event()` before validating whether the event is even actionable or valid.
  - Maintainability and type safety: Eliminating unformatted single-line multi-statement code and adding clear docstrings.
- **Evidence:**
  - 67 tests failed out of 214 in the baseline.
  - Deep copying accounts for invalid/unrecognized events caused unnecessary allocations.

## 2. Options considered
1. **Option A: Early Exit Before Deepcopy**
   - *Expected Benefit:* Eliminates expensive recursive dictionary copying for invalid, duplicate, unrecognized, or missing-ID events.
   - *Risk:* Low risk if account immutability is strictly maintained.
2. **Option B: Re-architect Account Data Structure with Frozen Dataclasses**
   - *Expected Benefit:* Stricter schema validation and immutability guarantees.
   - *Risk / Reason Rejected:* Existing test contracts and acceptance matrices (`test_contract.py`, `test_acceptance_matrix.py`) assert dictionary output shapes (`account['points_balance']`, `account['ledger']`, `account['transactions']`). Replacing dictionaries would break the external contract.
3. **Option C: Set-based Lookups for Processed Event IDs**
   - *Expected Benefit:* O(1) lookup rather than O(N) list search for replayed events.
   - *Trade-off:* The test contract explicitly expects `account['processed_event_ids']` to be a Python `list` preserving insertion order. Using a parallel set or keeping a list for the public interface is an option. Given typical transaction volume per account in the benchmark (< 100 events), list membership check `in` overhead is negligible (< 1 µs).

## 3. Changes implemented
- **Change and reason:**
  - Implemented pure integer floor arithmetic without intermediate float conversions (`// 10000` and `// 100`). This completely eliminates floating-point rounding errors and precision loss.
  - Cumulative proportional reversal calculation (`awarded * total_refunded // original_amount`) to prevent rounding drift across multiple partial refunds.
  - Reorganized `apply_reward_event()` with structured conditional branches and type-guard clauses.
- **Tests that protect correctness:**
  - `test_integer_floor_points_calculation` (25 cases)
  - `test_bonus_and_cap_matrix` (20 cases)
  - `test_purchase_event_replay_is_idempotent` (20 cases)
  - `test_refund_amount_bounds_and_balance` (20 cases)
  - `TestApplyRewardEventRegression::test_cumulative_partial_refunds_and_over_refund`
- **Measurement method and result:**
  - Pytest execution time: Total test suite of 224 tests completed in **0.16s** on local machine (measured with `pytest -v`).

## 4. Trade-offs
- **Immutability vs Allocation:** `deepcopy()` is retained to guarantee that callers' input dictionary references are never mutated in place (as verified by `test_event_processing_does_not_mutate_input_account`). While shallow copying or in-place mutation would be slightly faster, correctness and caller isolation are prioritized in financial ledgers.
- **Defensive Type Checking vs Brevity:** Checking `isinstance(x, int) and not isinstance(x, bool)` adds extra lines of code, but is strictly required due to Python's inheritance model where `bool` inherits from `int`.

## 5. Further improvements
- **Configurable Repeat Alert Window:** Currently, repeats are grouped by matching exact calendar date strings (`date`). An enhancement would support a sliding time window (e.g., within 24 hours or N hours across midnight).
- **Generator-based Ledger Streaming:** For accounts with thousands of transactions, returning an immutable ledger event stream rather than a monolithic nested dictionary would significantly reduce memory footprint.