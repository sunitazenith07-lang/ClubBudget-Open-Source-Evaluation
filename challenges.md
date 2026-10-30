# challenges.md - COMPULSORY submission

This file is mandatory and worth 5 marks. Describe your actual experience honestly. Do not invent difficulties to fill the page.

## 1. Challenge or confusing behaviour
The most subtle and critical challenge was properly handling proportional refund reversals across multiple sequential partial refunds while guaranteeing that points balances never become negative and that invalid refunds leave the account state untouched.

Specifically:
- In Python, `isinstance(True, int)` evaluates to `True`, meaning boolean values pass naive `isinstance(v, int)` checks.
- When an account undergoes multiple partial refunds on the same transaction (e.g. 30%, then another 30%, then 40%), each reversal must be calculated against cumulative refunded paise using integer arithmetic rather than naively multiplying the individual refund increment, which would introduce cumulative rounding errors.
- If an account has fewer points in `points_balance` than the proportional reversal requires (e.g. if points were previously redeemed or adjusted), deducting the full reversal would result in an illegal negative points balance.

## 2. Evidence
1. **Assertion failure on invalid refund types:**
   `test_invalid_or_excess_refund_does_not_change_account[True]` and `test_invalid_or_excess_refund_does_not_change_account[-1]` failed because the starter code executed:
   ```python
   txn['refunded_paise'] += refund
   ```
   Without type and boundary checks, `True` was added as `1`, `-1` was added directly, and excess refunds (e.g. 150000 on a 100000 purchase) mutated the transaction's `refunded_paise` and corrupted the audit ledger.
2. **Cap zero truthiness defect:**
   In `test_cap_zero_is_respected`:
   ```python
   calculate_points(50000, 1, cap_points=0)
   ```
   returned `5` instead of `0` because `if cap_points:` evaluates to `False` when `cap_points == 0`.

## 3. What I tried
1. **Initial check on `isinstance(amount, int)`:**
   Initially, checking `isinstance(amount, int) and amount > 0` allowed `amount = True` to slip through because in Python `bool` is a subclass of `int` (`True == 1`). This caused `test_invalid_or_excess_refund_does_not_change_account[True]` to treat `True` as a 1-paise refund.
   *Resolution:* Added explicit `not isinstance(..., bool)` guards across all numeric validation checks.
2. **Incremental vs Cumulative Refund Calculation:**
   Experimented with calculating `delta` directly from `event['amount_paise']`. For fractional divisions, rounding each increment separately accumulates rounding drift compared to evaluating total proportional entitlement from cumulative paise:
   `should_reverse = (txn['awarded_points'] * txn['refunded_paise']) // txn['amount_paise']`.
   *Resolution:* Adopted the cumulative entitlement approach, computing `delta = should_reverse - txn['reversed_points']`. This guarantees that the sum of all reversed points across all partial refunds exactly equals `awarded_points` upon a full refund.
3. **Negative Balance Guard:**
   Evaluated whether an excess points deduction should raise an exception or clamp to zero. The requirements specify: "never reverse more than awarded and never allow a negative balance."
   *Resolution:* Clamped `delta = min(delta, out['points_balance'])` and recorded the exact applied `delta` in both `txn['reversed_points']` and the ledger entry `points_delta: -delta`.

## 4. Resolution
The underlying root cause was a combination of loose type checking, lack of bounds verification before mutating state, and relying on truthy checks for numeric boundaries.

The fix resolves the root cause by:
1. Validating that `amount_paise` and `refund` are strict integers (`isinstance(x, int) and not isinstance(x, bool)`).
2. Verifying `txn['refunded_paise'] + refund <= txn['amount_paise']` before applying any state modification. If invalid or excess, the event is rejected and the account is returned completely untouched.
3. Checking `if cap_points is not None:` and returning 0 if `cap_points <= 0`.
4. Clamping reversal `delta` to `min(delta, out['points_balance'])` to mathematically enforce non-negative balances.

## 5. Proof and regression prevention
- **Proof:**
  Running `python3 -m pytest -q` passes all 214 baseline tests and all 8 newly added regression suites.
  Specifically, `test_refund_amount_bounds_and_balance`, `test_invalid_or_excess_refund_does_not_change_account`, and `test_cap_zero_is_respected` now pass completely.
- **Regression prevention:**
  Added `test_cumulative_multiple_partial_refunds` in `tests/test_regression.py` which executes a multi-step sequence: ₹300 refund (3 pts) -> ₹300 refund (3 pts) -> ₹400 refund (4 pts) -> ₹1 over-refund (rejected), asserting account balance and ledger consistency at every step.
  Added `test_refund_never_results_in_negative_points_balance` to explicitly test an account with insufficient balance facing a large refund.

## 6. Unresolved challenge or next step
All requirements and edge cases in the test suite and problem statement are fully solved and verified. A potential future enhancement would be adding support for formal event schema validation using dataclasses or Pydantic if external dependencies were permitted, which would standardize validation across the ingestion boundary.