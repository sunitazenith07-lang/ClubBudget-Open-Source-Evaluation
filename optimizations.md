# optimizations.md

## 1. Baseline and objective
- The main need was correctness and avoiding repeated state changes rather
  than raw speed. The initial suite had `67 failed, 147 passed`, including
  calculation boundaries, replayed events, and invalid refunds.
- The implementation is small and in-memory, so no performance bottleneck
  was identified or benchmarked.

## 2. Options considered
- Keep transaction-ID checks only: rejected because a repeated event ID must
  be ignored even when transaction state is already present, while distinct
  refund events for the same transaction may be valid.
- Use floating-point currency conversion: rejected because it can introduce
  boundary rounding errors; integer division is exact for paise values.
- Track processed event IDs before dispatch: chosen because it prevents
  duplicate purchase and refund state transitions with one simple guard.
- Replace the account dictionaries with a database or custom model:
  deferred because it would change the existing API and add complexity
  unrelated to this exercise.

## 3. Changes implemented
- Change and reason: integer floor division removes floating-point-style
  rounding; explicit validation prevents invalid arithmetic; an early event
  ID check prevents repeated work and duplicate ledger history.
- Tests that protect correctness: the existing contract and acceptance tests
  cover calculation boundaries, caps, invalid inputs, event types, replay,
  refund proportions, and refund bounds.
- Measurement method and result: no speedup was claimed and no benchmark was
  necessary. The final test command completed in `0.08s` with `214 passed`,
  but this is test-run timing rather than a performance benchmark.

## 4. Trade-offs
Explicit validation adds branches and makes the function longer, but it
prevents silent balance corruption and makes business rules clear. The
processed-event list preserves the existing data shape and is easy to
understand, but membership checks are linear and the list is not durable.

## 5. Further improvements
For production, I would use a set or database uniqueness constraint for
processed event IDs, transactionally update the balance and ledger, and
benchmark large event streams before changing data structures. I would also
test concurrent delivery of events to verify idempotency under contention.

No standalone speed optimization was implemented; correctness and
maintainability were prioritized.