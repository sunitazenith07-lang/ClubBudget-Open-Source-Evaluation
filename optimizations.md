# optimizations.md - Required submission

## 1. Baseline and objective
- What needed improvement: correctness of integer points, refund safety, and defensive input handling.
- Evidence: 41 failing tests in the initial `python -m pytest -q` run.

## 2. Options considered
- Option A: keep rounding and add special-case adjustments. Rejected because it would not match the required floor formula.
- Option B: cap excessive refunds to the transaction amount. Rejected because acceptance tests require excess refunds to leave the account unchanged.
- Option C: strict validation plus floor arithmetic. Selected for clarity and direct alignment with tests.

## 3. Changes implemented
- Change and reason: `calculate_points` now floors base points and bonus, applies cap last, and validates integer inputs.
- Change and reason: `apply_reward_event` validates refunds and ignores invalid/excessive ones without mutating state.
- Change and reason: `flag_repeat_transactions` guards non-list input and non-integer thresholds.
- Tests that protect correctness: all 214 tests in `tests/`.
- Measurement method and result: `python -m pytest -q` -> `214 passed in 0.13s`.

## 4. Trade-offs
Strict integer validation rejects float amounts such as `1.5`, which keeps arithmetic integer-only but means callers must convert values before calling. Defensive guards add small complexity but prevent crashes on malformed data.

## 5. Further improvements
With more time, I would add property-based tests for cumulative refunds and schema validation for event/account payloads, then validate with the same pytest suite.