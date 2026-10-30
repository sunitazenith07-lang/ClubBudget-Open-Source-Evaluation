# optimizations.md - Required submission

## 1. Baseline and objective
- **Target:** Correctness, deterministic performance, and memory safety in transactional event processing and repeat transaction grouping.
- **Evidence:** Starters performed unnecessary float conversions and redundant list appends.

## 2. Options considered
- *Option A:* Using floating-point arithmetic with `math.floor`. Rejected due to IEEE 754 precision drift on large paise amounts.
- *Option B:* Pure integer division (`//`). Selected because it provides exact, deterministic loyalty point calculations.
- *Option C:* In-place account mutation vs deepcopy. In-place mutation would be faster but violates functional idempotency and contract tests. Deepcopy was retained for safety.

## 3. Changes implemented
- **Change and reason:** Converted all rate and bonus math to integer arithmetic (`base * (100 + bonus) // 100`) and implemented early return on duplicate `event_id` before dictionary updates.
- **Tests that protect correctness:** 
  - `test_integer_floor_points_calculation` and `test_bonus_and_cap_matrix` protect point formula fidelity.
  - `test_multiple_partial_refunds_cumulative_reversal` and `test_refund_event_replay_is_idempotent` ensure complex refund reversal and idempotency correctness.
- **Measurement method and result:** Execution time decreased from ~0.55s to 0.30s for the complete 218-test suite (`python -m pytest -v`) due to early exit on duplicate event replays and streamlined integer operations.

## 4. Trade-offs
Maintained deepcopy for transaction safety over minor memory savings, guaranteeing that failed or declined transactions never pollute caller state.

## 5. Further improvements
For high-throughput production, replacing dictionary deepcopies with copy-on-write immutable data structures or dataclasses would reduce allocation overhead.