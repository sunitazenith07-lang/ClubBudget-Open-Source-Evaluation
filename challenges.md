# challenges.md - COMPULSORY submission

## 1. Challenge or confusing behaviour
The most subtle issue occurred in `calculate_points` with `cap_points = 0` and in `apply_reward_event` with boolean/invalid refund amounts. In Python, `isinstance(True, int)` evaluates to `True`, which caused boolean values like `True` to pass integer checks and corrupt refund calculations if not explicitly checked against `bool`.

## 2. Evidence
Running `pytest tests/test_contract.py -k test_cap_zero_is_respected` failed because `cap_points=0` was treated as falsy, returning un-capped points. Similarly, parameterized tests in `test_invalid_or_excess_refund_does_not_change_account` with `True` and `False` caused assertion errors in points balance.

## 3. What I tried
First tried `if cap_points > 0:`, but that failed when cap was 0. Then tried `if isinstance(val, int):` which allowed `True` (value 1) to pass. 

## 4. Resolution
1. Updated cap logic to `if cap_points is not None and isinstance(cap_points, int) and not isinstance(cap_points, bool): points = min(points, cap_points)`.
2. Added explicit `and not isinstance(refund, bool)` to ensure strict numerical typing.

## 5. Proof and regression prevention
- `test_cap_zero_is_respected` and `test_bonus_and_cap_matrix` verify that promotional zero-caps are strictly enforced.
- The newly added regression tests in `tests/test_contract.py` safeguard against complex regressions:
  - `test_refund_event_replay_is_idempotent` proves duplicate network retries cannot deduct points twice.
  - `test_multiple_partial_refunds_cumulative_reversal` proves multi-step partial returns calculate exact cumulative delta reversals without state drift.
  - `test_cumulative_refund_exceeding_purchase_ignored` proves excess cumulative returns are safely rejected.

## 6. Unresolved challenge or next step
The hardest deliberately tested edge case was handling sequential partial refunds where accumulated refunds equal the exact purchase amount. All proportional points reversals matched exact integers with zero residual balance.