# approach.md - Required submission

Complete this file in your own words. Be concise and specific to the work you actually performed.

## 1. Baseline
- Commands run before editing: `python3 -m venv .venv`, `source .venv/bin/activate`, `pip install --upgrade pip`, `pip install -r requirements-dev.txt`, `python3 -m pytest -q`
- Initial test result (include the actual summary): `67 failed, 147 passed` (total 214 tests evaluated)
- Demo/output observed: Baseline pytest run revealed 67 intentional starter failures related to rounding vs. floor division, missing idempotency guards, zero-cap handling, and refund type safety crashes (`TypeError`).

## 2. Codebase understanding
- Important files/functions inspected: `STUDENT_START_HERE.md` and `STUDENT_PROBLEM_STATEMENT.md` for business rules and constraints; `service.py` (`calculate_points`, `apply_reward_event`, and `flag_repeat_transactions`); acceptance and contract test suites under `tests/`.
- Rewards calculation, refund, ledger or alert flow traced: Traced how purchase events calculate points via paise conversion, check event uniqueness against processed IDs, update ledger entries, and how refund events proportionally reverse points with boundary controls.
- How you confirmed your understanding: Mapped test failure tracebacks back to specific logic gaps in `service.py` and cross-referenced expected behaviors in the test assertions.

## 3. Investigation and implementation strategy
For each major defect, describe the symptom, hypothesis, evidence from a test/log/example, and the fix chosen.
- Issue 1 (Points Calculation & Floor Division): Tests failed when checking exact integer floor division bounds, caused by starter code using `round()` instead of strict integer truncation (`//`). Fixed by replacing `round()` with explicit integer floor division (`// 10000`) and ensuring cap checks evaluate `is not None` so zero-caps are respected.
- Issue 2 (Idempotency Replay): Replaying the same `event_id` duplicated transactions and points because of a missing upfront check for already processed event IDs. Fixed by adding an idempotency guard at the start of `apply_reward_event` to immediately return unmodified account state if an event ID is already recorded in `processed_event_ids`.
- Issue 3 (Refund Type Safety & Bounding): Malformed refund inputs (`None`, strings, lists, negative values) raised `TypeError` due to a lack of input type validation and boundary checks before arithmetic operations (`+=`). Fixed by adding type guards (`isinstance(..., int) and not isinstance(..., bool)`) and bounding logic to safely ignore invalid or excess refunds.

## 4. Implementation decisions
- Main changes and why: Implemented strict type checking and integer arithmetic to ensure absolute financial precision and prevent runtime exceptions.
- Alternatives considered and why rejected: Considered floating-point division for bonuses, but rejected it to eliminate floating-point precision errors.
- Assumptions: All monetary amounts are provided as integers in paise, and incoming event payloads follow standard dictionary structures.

## 5. Verification
- Tests added or changed: Retained all original acceptance tests without modification; verified robust edge case handling.
- Commands run and actual results: `python3 -m pytest -q` -> **`214 passed in 0.48s`**
- Edge cases verified: Zero-amount purchases, zero caps, duplicate event replays, excess refunds, and malformed data inputs (`None`, strings, lists, booleans).
- Remaining failures or known limitations: None; all 214 tests pass successfully.