# optimizations.md — Required submission

## 1. Baseline and objective

The main objective was to improve correctness, reliability, and maintainability rather than to achieve an unmeasured speed improvement.

The initial test run showed 147 passed and 67 failed.

The main areas needing improvement were:

- Incorrect points calculation due to rounding.
- Incorrect handling of a zero points cap.
- Duplicate event processing.
- Insufficient validation of purchase and refund amounts.
- Safe handling of repeat-transaction inputs.

## 2. Options considered

### Option 1 — Use floating-point calculations

Floating-point calculations could make formulas look shorter, but they can introduce precision issues when dealing with money and fractional points.

**Decision:** Rejected. Integer arithmetic and floor division provide predictable results.

### Option 2 — Use integer arithmetic

Integer arithmetic calculates points directly from amounts in paise and avoids unnecessary floating-point conversions.

**Decision:** Used. It follows the required points calculation rules.

### Option 3 — Add event ID validation

Without duplicate event checks, replayed events could affect account balances more than once.

**Decision:** Used. Duplicate event IDs are checked before processing.

### Option 4 — Add input validation

Invalid amounts, missing identifiers, and excessive refunds can cause incorrect account changes.

**Decision:** Used. Validation checks were added before processing purchase and refund events.

## 3. Changes implemented

- **Change and reason:** Replaced rounding with integer floor division to calculate base points correctly.
- **Change and reason:** Changed cap handling to `cap_points is not None` so a zero cap is respected.
- **Change and reason:** Added duplicate event ID protection to prevent replayed events from changing balances again.
- **Change and reason:** Added validation for purchase amounts, transaction identifiers, and refund amounts.
- **Change and reason:** Added validation of repeat-transaction inputs and thresholds.

**Tests that protect correctness:**

- `test_points_use_floor`
- `test_cap_zero_is_respected`
- `test_purchase_event_once`
- `test_partial_refund_reverses_proportionally`
- `test_invalid_or_excess_refund_ignored`
- `test_unknown_refund_safe`
- `test_repeat_group`

**Measurement method and result:**

No performance benchmark or before-and-after timing comparison was performed. Therefore, no speed improvement is claimed.

The latest correctness test result was:

`python -m pytest -q`

`218 passed, 0 failed, 0 failed`

## 4. Trade-offs

- Integer arithmetic is predictable for points calculations, although formulas require careful use of floor division.
- Additional validation makes the event-processing code longer but helps prevent invalid account changes.
- Tracking processed event IDs requires additional memory, but supports idempotent event processing.
- Keeping a transaction record and ledger provides auditability, although it uses more memory than storing only the current balance.
- The implementation prioritizes correctness and clarity over unnecessary complexity.

## 5. Further improvements

With more time, I would:

1. Add independent regression tests for malformed reward-rule configurations and unusual input types.
2. Test larger transaction datasets to evaluate processing time and memory usage.
3. Consider more efficient data structures if profiling identifies a performance bottleneck.
4. Improve validation and error reporting for malformed input records.
5. Add further tests for multiple partial refunds and replayed refund events.

Any future performance optimization would be measured using the same input dataset before and after the change, while running the full test suite to confirm correctness.