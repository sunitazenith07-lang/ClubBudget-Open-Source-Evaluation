# Optimization and trade-off notes

## 1. Baseline and objective

The primary objective was correctness and reliability, not a measured performance increase. The baseline had `67` failures out of `214` tests. The failures showed repeated work and unsafe state transitions in reward calculation, purchase replay, and refunds:

- Floating-point rounding was used where integer floor arithmetic was required.
- Replayed events were not stopped before event-specific handling.
- Invalid refunds could mutate state or raise errors.
- Refund calculations needed cumulative state to preserve proportional totals.
- A missing purchase amount could be defaulted to zero instead of being rejected.

No performance benchmark or speedup measurement was recorded.

## 2. Options considered

### Integer arithmetic versus floating-point arithmetic

Integer floor division was chosen because paise and points are integral and the official formula explicitly requires floor behavior. Floating-point division followed by `round()` was rejected because it produced incorrect boundary results and did not express the required calculation.

### Early idempotency check versus transaction-only deduplication

Checking `processed_event_ids` before event-specific processing was chosen because it prevents any replayed event from changing balance, transaction data, or ledger state. Checking only whether a transaction ID exists was insufficient: it stopped a second purchase award but still allowed replayed event metadata to change.

### Validate before mutation versus mutate then roll back

Validation before mutation was chosen for refunds. It keeps rejected refunds from changing cumulative refund totals, reversed points, balances, or financial ledger entries. Mutate-and-rollback would require more state management and creates more opportunities for partial updates.

### Cumulative refund calculation versus independent per-refund rounding

Cumulative calculation was chosen:

```text
total_reversal = (awarded_points * cumulative_refund) // original_amount
incremental_reversal = total_reversal - previous_reversed_points
```

Independent rounding was rejected because the total reversal could depend on how a refund is split across events rather than on the cumulative refunded amount.

### Actual balance delta versus a separately recomputed ledger delta

The ledger uses `balance_after - balance_before` for `points_delta`. This was chosen to keep the audit record tied directly to the state transition. Recomputing a separate delta from business inputs could diverge from the actual balance if validation or bounds change.

## 3. Changes implemented

- Replaced rounded point calculation with integer floor division.
- Applied the bonus before the cap and respected a zero cap.
- Added numeric validation that rejects booleans and invalid or negative values.
- Added an early event-ID idempotency check.
- Added purchase identifier and amount validation.
- Required captured purchases to provide an explicit amount while preserving valid zero amounts.
- Added refund validation before state mutation.
- Added cumulative refund reversal and balance/reversal bounds.
- Derived ledger `points_delta` from the actual balance change.
- Added seven refund regression tests.
- Added four purchase amount-validation regression tests.

An earlier implementation milestone was reported as `221 passed` before the final purchase-validation tests. The available evidence establishes correctness improvements through the final reported `225 passed in 2.12s` result. It does not establish a performance improvement or measured speedup.

## 4. Trade-offs

- Deep-copying the account preserves input immutability but uses additional memory proportional to the account structure.
- Explicit validation adds branches and code, but prevents malformed values from reaching arithmetic and financial state updates.
- Cumulative refund state adds transaction fields and arithmetic, but makes repeated partial refunds deterministic.
- An early processed-event lookup avoids unnecessary event-specific work for replays, while the list-based lookup remains linear in the number of processed IDs.
- Keeping the existing dictionary-based account structure minimizes interface changes, but provides less type safety than dedicated data classes or validated models.

## 5. Further improvements

These are proposals, not completed or measured changes:

- Replace the list of processed event IDs with an indexed set while preserving the external account contract, then benchmark lookup and copy costs on representative account sizes.
- Add explicit account and event validation helpers with focused tests for malformed outer inputs and inconsistent historical state.
- Add an integration test that compares equivalent refund partitions and orders where cumulative and independent rounding produce different results.
- Define a reconciliation workflow for inconsistent existing accounts rather than silently repairing them.
- Load selected synthetic records from `data/records.json` in a separate test harness, not in the demo path, and measure any resulting runtime or maintenance trade-offs before adopting it.
