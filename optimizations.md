# optimizations.md - Required submission

Document optimizations you considered or implemented. Do not claim a speedup or improvement unless you measured it.

## 1. Baseline and objective

- What needed improvement:
  - **Correctness** was the primary objective. The starter code had four bugs producing 67 test failures. All changes prioritized fixing incorrect behaviour over performance tuning.
  - After correctness was achieved, I examined the code for performance and maintainability concerns.
- What evidence suggested an improvement could help:
  - The `processed_event_ids` field is a Python list. The idempotency check `if event_id in out['processed_event_ids']` performs a linear scan (O(n) time complexity). I measured the cost of this scan at different account sizes to determine whether it was a real concern.

## 2. Options considered

**Option A: Change `processed_event_ids` from a list to a set**

- Expected benefit: The `in` operator on a set is O(1) average time instead of O(n) for a list. For an account with 50,000 events, this would reduce lookup from ~3.2 ms to near-instant.
- Risk: This would require modifying `models.py` (which defines the account structure) and potentially breaking JSON serialization, since JSON does not support sets natively. It would also change the data contract for any code reading `processed_event_ids` as an ordered list.
- Decision: **Rejected.** The change involves modifying an unrelated file (`models.py`) and the data model contract. The current dataset has at most ~7 events per account, where the O(n) cost is negligible (~0.01 ms). This optimization would be appropriate for production scale but is not justified for this task.

**Option B: Add early return for invalid `amount_paise` in `calculate_points`**

- Expected benefit: Avoids unnecessary arithmetic when the input is clearly invalid (negative, zero, or non-integer).
- Risk: None — the early return produces the same result (0 points) that the original `max(0, ...)` would have produced, but skips the intermediate calculations.
- Decision: **Implemented.** The `isinstance` check and `<= 0` guard at `service.py` line 5 serves both as a correctness fix (required by spec) and a minor efficiency improvement (skips division and multiplication for invalid inputs).

**Option C: Add early return for `None` event_id in `apply_reward_event`**

- Expected benefit: Avoids the `deepcopy` overhead for events that will be immediately rejected. Actually, `deepcopy` runs before the check (line 15), so the benefit is limited to skipping the remaining logic.
- Risk: None.
- Decision: **Implemented** as a correctness fix (prevents `None` collision bug). The minor performance benefit of skipping the remainder of the function is incidental.

## 3. Changes implemented

- Change and reason:
  - **Early return for invalid amounts** (`service.py` line 5–6): Added `if not isinstance(amount_paise, int) or amount_paise <= 0: return 0`. This is primarily a correctness fix, but also avoids unnecessary arithmetic for invalid inputs.
  - **Early return for `None` event_id** (`service.py` lines 17–19): Added `if event_id is None: return out`. Primarily a correctness fix to prevent the `None` collision bug.
  - **Early return for duplicate event_id** (`service.py` lines 20–22): Added `if event_id in out['processed_event_ids']: return out`. This is the idempotency guard required by the spec.
  - **Refund validation guards** (`service.py` lines 32–36): Added type check, positivity check, and bounds check. Rejects invalid refunds before they can corrupt the balance.
- Tests that protect correctness:
  - All 214 original tests pass. 9 new regression tests in `tests/test_event_id_regression.py` specifically cover the `None` event_id and idempotency logic.
- Measurement method and result:
  - Measured `apply_reward_event` call time for replaying an already-processed event at different `processed_event_ids` list sizes:
    - n=100: 0.010 ms/call
    - n=1,000: 0.070 ms/call
    - n=10,000: 0.670 ms/call
    - n=50,000: 3.194 ms/call
  - At the scale of the synthetic dataset (~7 events per account), the O(n) cost is negligible. The `deepcopy` at line 15 is the dominant cost for large accounts, not the `in` lookup.

## 4. Trade-offs

- **Correctness over performance**: All changes prioritized fixing bugs over optimization. The only performance concern identified (O(n) list lookup) was deliberately left unoptimized to avoid modifying the data model in `models.py`.
- **Minimal change over refactoring**: The code could be made more readable by reformatting the dense single-line statements (e.g., `service.py` line 15). However, this would increase the diff size and risk introducing unrelated regressions. The existing formatting was preserved.
- **Safety over flexibility**: Events with `None` event_id are rejected rather than processed without dedup. This is stricter than necessary (the spec does not explicitly address missing event IDs) but prevents the `None` collision bug and ensures every processed event can be tracked.

## 5. Further improvements

What I would do next with more time:

1. **Convert `processed_event_ids` to a set** for O(1) lookups. Would require updating `models.py` and adding a JSON serialization step (convert set ↔ list when reading/writing JSON). Would validate by re-running all 223 tests and measuring call time at n=50,000.
2. **Move the `deepcopy` after the `None`/idempotency guards** so that rejected events do not incur the copy overhead. This is a straightforward change but would need careful testing to ensure the function still never mutates its input.
3. **Add type validation for `points_per_100_rupees` and `bonus_percent`** in `calculate_points`. Currently only `amount_paise` is validated. Negative or non-integer rule values produce results clamped by `max(0, ...)` but could be caught earlier for clearer error reporting.

If you made no optimization change, state that honestly and compare at least two reasonable options. Correctness and maintainability take priority over unnecessary complexity.
