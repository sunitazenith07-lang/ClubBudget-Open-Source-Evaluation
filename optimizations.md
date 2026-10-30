# optimizations.md - Required submission

## 1. Baseline and objective
- Needed improvement: correctness of points, idempotency, refund bounds, ledger integrity, and input safety.
- Evidence: 45 failing tests in `test_acceptance_matrix.py` and `test_contract.py`.

## 2. Options considered
- Keep starter structure and patch only obvious lines: lower risk but left validation gaps.
- Rewrite control flow with explicit validation: more code but clearer and safer.
- Rejected keeping all event IDs appended because it violated idempotency and account-unchanged expectations.

## 3. Changes implemented
- Added early type and range validation in `calculate_points`.
- Added event-id idempotency before mutation.
- Added refund validation and cumulative proportional reversal.
- Added safe guards in `flag_repeat_transactions`.
- Tests that protect correctness: all 214 tests, especially replay and refund boundary tests.
- No performance benchmark was measured; changes focus on correctness.

## 4. Trade-offs
- More validation improves robustness but increases code size.
- Strict integer validation may reject non-integer numeric inputs; acceptable for the integer-arithmetic contract.

## 5. Further improvements
- Add property-based tests for cumulative refunds and idempotency.
- Add schema validation for events if the service API expands.