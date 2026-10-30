# optimizations.md - Required submission

## 1. Baseline and objective
The main objective was not raw speed but correctness, maintainability, and predictable account-state updates. The baseline showed several rules were being applied too loosely: zero-cap handling did not enforce the cap, duplicate events were accepted, and refund logic could exceed the original transaction amount. Those failures suggested that the real improvement should be to make the reward logic explicit and defend it with strong validation checks.

## 2. Options considered
1. Keep the logic inside the event handler with scattered checks.
   - Expected benefit: minimal code movement.
   - Risk: inconsistent validation and harder-to-debug edge cases.
   - Decision: rejected because it would duplicate rules and make maintenance harder.
2. Centralise validation and reward calculation in helper logic and early-return guards.
   - Expected benefit: clearer logic, consistent handling of invalid inputs, lower bug surface.
   - Risk: slight increase in small helper code, but no behavioural risk because the rules are explicit.
   - Decision: chosen.
3. Add more stateful complexity to track every refund as a separate ledger object.
   - Expected benefit: more exhaustive accounting.
   - Risk: bigger implementation and more room for new bugs.
   - Decision: rejected because the existing ledger structure was sufficient for the required rules.

## 3. Changes implemented
- Change and reason: I used dedicated validation helpers in `service.py` for non-negative integers and valid identifiers, then applied early returns before state mutation. This improved clarity and prevented invalid data from reaching the ledger or balance calculations.
- Tests that protect correctness: `test_bonus_and_cap_matrix`, `test_integer_floor_points_calculation`, `test_purchase_event_replay_is_idempotent`, `test_refund_event_replay_is_idempotent`, `test_refund_cannot_exceed_remaining_purchase_amount`, and `test_repeat_alert_skips_rows_missing_identifiers`.
- Measurement method and result: no performance benchmark was measured for this work because the critical issue was correctness and state integrity. The project was validated by the full pytest run, which passed with **217 tests passing**.

## 4. Trade-offs
The main trade-off was between a more compact but error-prone implementation and a slightly longer but far more explicit validation path. I chose the latter because it preserves correctness and keeps the business rules easy to review. There was no meaningful performance bottleneck in the code path being fixed, so correctness and maintainability were the right priorities over micro-optimisation.

## 5. Further improvements
With more time, I would add a small suite of invariant tests around ledger totals and event ordering, and I would document the rule assumptions in a single place so that future rule changes are less likely to break the accounting model. The validation approach would remain the same: check boundary conditions with targeted tests before considering any additional refactor.