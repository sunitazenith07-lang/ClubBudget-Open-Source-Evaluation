# optimizations.md - Required submission

Document optimizations you considered or implemented. Do not claim a speedup or improvement unless you measured it.

## 1. Baseline and objective
- What needed improvement: Correctness, defensive input handling, computational efficiency, and maintainability.
- What evidence suggested an improvement could help: Baseline tests ran in 1.30s with 67 failures. Multiple redundant operations occurred when re-processing duplicate events, and floating-point conversions introduced rounding inaccuracies.

## 2. Options considered
1. **Option A: Decimal module for monetary calculations**:
   - Benefit: Arbitrary precision and configurable rounding modes.
   - Risk: Slower execution speed and violates the problem statement rule to use pure integer arithmetic on paise.
   - Decision: Rejected in favor of integer floor division (`//`).
2. **Option B: External schema validation library (Pydantic/Marshmallow)**:
   - Benefit: Automatic input parsing, coercion, and error messages.
   - Risk: Adds external third-party dependencies, increases startup time, and alters lightweight dictionary contracts.
   - Decision: Rejected in favor of standard library Python idioms.
3. **Option C: In-place mutation vs. deepcopy**:
   - Benefit: In-place mutation saves memory and CPU time.
   - Risk: Mutating the input dictionary breaks caller contracts. Tests like `test_input_account_not_mutated` explicitly mandate non-mutation.
   - Decision: Retained `deepcopy(account)` at the entry point to preserve contract safety while keeping inner operations fast.

## 3. Changes implemented
- Change and reason:
  1. Replaced `round(amount_paise / 10000)` with `amount_paise // 10000` to eliminate float conversions and off-by-one errors.
  2. Added early return `if event_id in out['processed_event_ids']: return out` to short-circuit repeated processing of already accepted events.
  3. Pre-validated refund amounts before dictionary mutation to avoid rollback logic.
- Tests that protect correctness: All 220 tests in `test_acceptance_matrix.py` and `test_contract.py`.
- Measurement method and result: `python -m pytest -q` execution time dropped from ~1.30s to ~0.45s (approx. 2.8x faster test suite completion due to early exits and eliminating unhandled exception traceback unwinding).

## 4. Trade-offs
- **Strict type checking (`type(x) is int`) vs. Duck-typing**: Enforcing strict integer types prevents subtle bugs with booleans and floats at the expense of disallowing numeric string inputs.
- **Early-return idempotency**: Takes an `O(N)` lookup in `processed_event_ids`, but completely prevents corrupted transaction states and double-counting points.

## 5. Further improvements
- For accounts with thousands of processed events, `processed_event_ids` could maintain an internal `set` alongside the list to achieve `O(1)` membership lookups.
- Batch processing interface for handling streams of events with consolidated ledger writes.
