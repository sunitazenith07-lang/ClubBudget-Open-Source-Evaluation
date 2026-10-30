# Optimizations and trade-offs

## 1. Baseline and objective

The main objective was to make the reward service correct and maintainable before trying to make it faster. The original implementation used floating-point division and `round` for point calculation, accepted invalid refund values, and did not stop duplicate refund events from being applied twice. Those are correctness issues, not performance bottlenecks.

I also considered clarity and unnecessary work in the existing flow:

- Reward amounts and thresholds are integer values, so integer arithmetic can express the specified rounding rules directly.
- A duplicate event can be recognized by its event ID before running the purchase or refund logic.
- Repeat alerts need to group each valid transaction once by account, date, and amount.

I did not run a benchmark or profile the program. Therefore, I make no claim that the changes reduce runtime or memory use.

## 2. Options considered

### Point arithmetic

- **Chosen: integer division and multiplication.** `amount_paise // 10000` implements the required floor operation without converting currency to a floating-point value. The bonus is also calculated with integer arithmetic, and the optional cap is applied afterward.
- **Rejected: keep floating-point rounding.** It is concise but does not implement the required floor rule at boundaries such as 9999 or 19999 paise.
- **Rejected: use `Decimal` or a rounding helper.** This would add a more general mechanism without helping this integer-only formula. Integer arithmetic is simpler and directly matches the requirements.

### Event replay protection

- **Chosen: check the processed event IDs before applying event effects.** This avoids repeating balance, transaction, or ledger mutations when an already-processed event is replayed.
- **Alternative: make each event type independently idempotent.** For example, each refund could be deduplicated separately during refund calculations. I did not choose this because the shared event-ID guard is smaller and protects both purchases and refunds consistently.
- **Trade-off:** The account stores processed IDs in a list, so membership checking becomes slower as the list grows. The starter account shape already uses a list, and this offline exercise does not establish a scale requirement. A persistent store with a uniqueness constraint or a set-backed index could be appropriate in a larger system, but would add complexity and is not implemented here.

### Account copying

- **Kept: deep-copy the account before processing.** This preserves the existing guarantee that applying an event does not mutate the caller's account. A shallow copy could share nested transaction dictionaries, ledger lists, or processed-ID lists and would risk mutating the input.
- **Alternative: mutate the provided account in place.** This could avoid the copy cost, but changes the existing behavior and makes call sites responsible for managing mutation. I retained the safer behavior because the tests explicitly verify input immutability.
- **Trade-off:** A deep copy consumes time and memory proportional to the account data. I did not measure that cost, and preserving behavior was more important than making an unmeasured optimization.

### Repeat grouping

- **Chosen: one pass over the transactions, accumulating IDs in a dictionary keyed by `(account_id, date, amount_paise)`.** This keeps the grouping logic direct and avoids repeatedly scanning the full input for each key.
- **Alternative: sort the entire input and process adjacent rows.** Sorting could make groups easy to iterate, but it adds sorting work and would require preserving or explicitly defining output order. For this small API, the dictionary grouping is clearer.
- **Trade-off:** The function retains each group’s transaction IDs in memory because those IDs are part of the output. This is necessary for the current result shape.

## 3. Changes implemented

- Replaced floating-point rounding with integer floor arithmetic in `calculate_points`. The change is primarily for correctness and transparent currency-boundary behavior; it was not benchmarked as a speed optimization.
- Validate point-rule values before calculating, and check `cap_points is not None` so that a cap of zero is respected.
- Added an early event-ID replay check in `apply_reward_event`. This prevents duplicate accepted purchase/refund events from adding a second ledger entry or changing the balance again.
- Validate refund amounts and cumulative bounds before updating transaction state. Calculate proportional reversals with integer arithmetic, cap reversal at the points originally awarded, and prevent the points balance from going below zero.
- Skip malformed repeat-transaction records before grouping them.
- Added regression tests in `tests/test_contract.py` for refund replay, missing event IDs, and repeat rows with missing identifiers. Existing tests also exercise boundaries, caps, refunds, and repeat thresholds.
- **Measurement:** No runtime or memory benchmark was run. Functional verification was `python -m pytest -q` (**217 passed**) and `python -m main` (completed successfully).

## 4. Trade-offs

- Integer arithmetic is slightly more explicit than a short floating-point expression, but removes ambiguity about rounding and avoids floating-point representation concerns.
- Validating data before mutation adds checks, but makes invalid refunds leave transaction refund totals and balances unchanged.
- Deep-copying provides isolation between input and output account values, but duplicates nested state in memory. I retained this because it preserves tested behavior.
- Keeping processed event IDs in a list matches the existing account model and is easy to inspect, but membership checks are linear in the number of IDs. Changing to a set would affect the account's data shape and serialization expectations, so I did not do that without a demonstrated need.
- Repeat alerts return grouped transaction IDs, which requires storing output lists. No extra sorting of transaction IDs is performed; the group order is deterministic for the input order, while groups are sorted by their key for stable output.

## 5. Further improvements

1. **Benchmark realistic account sizes.** Generate accounts with increasing transaction, ledger, and processed-ID counts; measure event processing time and peak memory for `apply_reward_event`. Compare deep-copy processing with an immutable or copy-on-write design while verifying that the input remains unchanged.
2. **Use an indexed idempotency store if scale requires it.** A database uniqueness constraint or a set/index maintained alongside persisted event records could make replay lookup efficient. Validate it with concurrent duplicate-event tests and persistence/restart tests before replacing the current list-based account contract.
3. **Measure repeat-alert scaling.** Test empty, typical, and large synthetic transaction batches, recording runtime and memory. Keep the current one-pass dictionary grouping unless measurements identify a bottleneck.
4. **Clarify invalid-input policy at the API boundary.** The current helper functions return safe outputs for malformed values to meet the challenge behavior. A production service could use typed request validation and explicit error reporting, but that would be an API behavior change and should be specified and tested before adoption.

These are proposals, not completed or measured optimizations. Correctness, existing API behavior, and readable logic were prioritized for this change.
