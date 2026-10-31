# approach.md - Required submission

Complete this file in your own words. Be concise and specific to the work you actually performed.

## 1. Baseline
- Commands run before editing:
  `python -m pip install -r requirements-dev.txt`
  `python -m pytest -q` 
  `python -m main`

- Initial test result (include the actual summary):
  Before fixes: 67 tests failed, after fixes: 0 failed

- Demo/output observed:
  Points example: 27
  Repeat warnings: []

## 2. Codebase understanding
- Important files/functions inspected:
  `service.py` (calculate_points, apply_reward_event), `models.py`, `tests/`

- Rewards calculation, refund, ledger or alert flow traced:
  I looked at how points are calculated from amount, how refunds reverse points, how idempotency works

- How you confirmed your understanding:
  By running tests, using ai tools(Cline and Gemini) and  seeing which ones failed, then fixing the bugs

## 3. Investigation and implementation strategy
For each major defect, describe the symptom, hypothesis, evidence from a test/log/example, and the fix chosen.
- Issue 1:
    Test `test_points_use_floor` failed: assert 2 == 1
    The code was using round() instead of floor()
    calculate_points(19999,1) returned 2 instead of 1
    Changed `round(amount_paise / 10000)` to `(amount_paise // 10000)`

- Issue 2:
    Test `test_cap_zero_is_respected` failed: assert 5 == 0
    cap_points=0 was being ignored because `if cap_points:` treats 0 as falsy
    calculate_points(50000,1,cap_points=0) returned 5 instead of 0
    Changed `if cap_points:` to `if cap_points is not None:`
    Assisted by Gemini to verify the diagnosis of this bug.

- Issue 3 (if applicable): N/A

## 4. Implementation decisions
- Main changes and why:
  1. Fixed calculate_points() to use floor division instead of round
  2. Fixed cap_points=0 being ignored
  3. Fixed event ID deduplication in apply_reward_event()
  4. Fixed refund validation for invalid inputs
  Why:These were the root causes of failing tests

## 5. Verification
- Tests added or changed:
  All 214 tests now pass

- Commands run and actual results:
  `python -m pytest -q` → 214 passed, 0 failed

- Edge cases verified:
  - Points floor calculation: 19999 paise → 1 point
  - Cap of zero: cap_points=0 truly means zero points
  - Invalid refund amounts are rejected

- Remaining failures or known limitations:
  None — all visible tests pass

Record actual engineering decisions and evidence. Do not claim tests or experiments you did not run.