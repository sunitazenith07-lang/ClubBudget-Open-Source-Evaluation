# optimizations.md - Required submission

Document optimizations you considered or implemented. Do not claim a speedup or improvement unless you measured it.

## 1. Baseline and objective
The main goal was to improve code correctness and maintainability.

The refund logic was not handling invalid and excessive refunds properly.

## 2. Options considered
Tried using max(0, points), but it did not fix invalid transaction updates.

Considered adding refund validation, which was the simplest and safest option.

Avoided unnecessary complex logic.

## 3. Changes implemented
Change and reason: Added refund validation to prevent invalid refunds.

Tests: Ran contract tests and acceptance matrix tests.

Measurement: No performance benchmark was done. All 214 tests passed.


## 4. Trade-offs
The validation adds a small amount of code but makes refund handling safer and easier to maintain. No speed improvement is claimed.

## 5. Further improvements
I would add database locking for simultaneous refunds and warning logs for invalid refund requests.