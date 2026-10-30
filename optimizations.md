# optimizations.md

## 1. Baseline and objective

The main objective was to improve correctness, code clarity, and maintainability rather than focusing on raw execution speed.

The initial implementation had some issues:

- Reward calculation used floating-point rounding.
- A zero-point cap was not handled correctly.
- Duplicate events could be processed more than once.
- Refund validation was incomplete.
- Invalid values could affect reward calculations and account balances.

The initial test result was `67 failed, 147 passed in 1.30s`, which showed that the existing implementation needed improvement.

## 2. Options considered

**Option 1: Use integer arithmetic instead of floating-point calculations**

- Expected benefit: More predictable reward calculations and fewer rounding-related errors.
- Risk: Requires careful handling of integer division and calculation order.
- Decision: Implemented because reward points are based on complete ₹100 units.

**Option 2: Add input validation using a separate helper function**

- Expected benefit: Reuse the same validation logic for amounts, reward rates, bonus percentages, and caps.
- Risk: Invalid values need a clearly defined handling behaviour.
- Decision: Implemented using `valid_int()` to accept only non-negative integers and exclude booleans.

**Option 3: Add duplicate event protection**

- Expected benefit: Prevent the same event from changing the account balance multiple times.
- Risk: Requires maintaining and checking processed event IDs.
- Decision: Implemented using `processed_event_ids`.

**Option 4: Rewrite the repeat transaction alert logic**

- Expected benefit: Potentially improve readability or performance.
- Risk: Changing the grouping logic could introduce new behaviour or break existing tests.
- Decision: Rejected for this version because the existing grouping by account ID, date, and amount already served the required purpose.

## 3. Changes implemented

- **Change and reason:**
  - Replaced floating-point rounding with integer floor division for reward calculation.
  - Used integer arithmetic for bonus and proportional refund calculations.
  - Changed cap handling to `cap_points is not None`, so a zero cap is valid.
  - Added `valid_int()` to avoid repeating input validation logic.
  - Added duplicate event checks to prevent replayed events from being processed again.
  - Added refund validation to prevent cumulative refunds from exceeding the original purchase amount.
  - Continued using `deepcopy()` so event processing works on a copied account rather than directly modifying the original input.

- **Tests that protect correctness:**
  Added seven regression tests in `tests/test_regressions.py` covering negative amounts, zero caps, duplicate events, excessive refunds, unknown transactions, partial refunds, and empty repeat transaction input.

- **Measurement method and result:**
  No dedicated performance benchmark was performed, so I am not claiming a measured speed improvement.
  
  The final test suite completed with:

  `221 passed in 0.46s`

  This confirms the recorded test result, not a measured performance improvement over the original implementation.

## 4. Trade-offs

- Integer arithmetic makes reward calculations more predictable, but the calculation order must be correct.
- The validation helper reduces repeated checks, but adds another function to maintain.
- Tracking processed event IDs improves duplicate protection, but requires storing and checking event IDs.
- Using `deepcopy()` protects the original account data, but creates an additional memory and copying cost.
- Keeping the existing repeat-alert grouping logic avoids unnecessary complexity, although it may not be the most efficient approach for very large transaction lists.

I prioritised correctness and maintainability over adding complexity for an unmeasured speed improvement.

## 5. Further improvements

With more time, I would consider:

- Investigating refund behaviour when a customer has already spent some of their awarded points.
- Testing the alert logic with larger transaction datasets to understand its performance.
- Evaluating whether a set could be used alongside `processed_event_ids` for faster duplicate event lookups, while preserving the expected account data structure.
- Adding more tests for malformed account data and invalid reward rules.
- Running proper benchmarks before making any performance-related changes.

I would validate these improvements using additional regression tests and compare execution time and memory usage on the same test datasets before claiming any measurable improvement.