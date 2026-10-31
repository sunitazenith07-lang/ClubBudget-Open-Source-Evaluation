# Correctness and maintainability notes

> **AI-use disclosure:** AI assistance was used with evaluator permission, as confirmed by the requester. See [AI_USAGE.md](AI_USAGE.md) for details.

## 1. Baseline and objective

The objective was correctness and safe handling of event data, not a measured speed improvement. Baseline tests reported **67 failed, 147 passed**. Failures covered floor rounding, zero caps, duplicate events, and refund bounds.

## 2. Options considered

- Integer arithmetic for points and proportional refunds: chosen because the business rules specify floor behavior and values are integral paise/points.
- Floating-point arithmetic with rounding: rejected because it disagreed with the specified floor semantics and can introduce boundary errors.
- Central validation helpers: chosen for repeated integer and identifier checks without adding a dependency.
- Silently coercing strings/floats to integers: rejected because malformed financial amounts should not be reinterpreted as valid values.

## 3. Changes and evidence

- Implemented integer-floor point calculations, explicit optional-cap handling, input validation, replay protection, bounded cumulative refunds, and safer repeat grouping.
- Added focused regression tests in `tests/test_acceptance_matrix.py`.
- Final suite: **221 passed**. No before/after performance benchmark was run, so no speedup is claimed.

## 4. Trade-offs

Input validation adds branches, but keeps malformed values from affecting balances. Returning zero for invalid points and ignoring invalid events follows the existing function style; a production system could instead return structured errors or emit monitoring events. The deep copy preserves the existing non-mutation behavior but copies the full account for each event.

## 5. Further work

With a clarified API contract, consider structured validation results and observability for rejected events. Benchmark the current deep-copy approach against an immutable or transactionally updated representation using realistic account sizes before changing it. Clarify whether invalid events should consume their event ID, then test the agreed replay policy.
