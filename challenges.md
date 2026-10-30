# challenges.md - COMPULSORY submission

This file is mandatory and worth 5 marks. Describe your actual experience honestly. Do not invent difficulties to fill the page.

## 1. Challenge or confusing behaviour
The most demanding challenge was designing the proportional refund reversal algorithm using pure integer arithmetic without causing integer truncation drift across sequential partial refunds, while also handling Python's subtle boolean-as-integer type hierarchy.

Specifically:
1. **Integer truncation drift in partial refunds:** If a customer makes a purchase of Rs 1,000 (100,000 paise) earning 15 points (base 10 + 50% bonus), and later receives two consecutive 50% refunds (50,000 paise each), calculating each refund incrementally using `(awarded * refund) // total` yields `(15 * 50000) // 100000 = 7` points for each refund. Total reversed would be `7 + 7 = 14`, leaving 1 point incorrectly orphaned on a transaction that has been 100% refunded.
2. **Boolean type leakage:** In Python, `isinstance(True, int)` evaluates to `True` because `bool` inherits from `int`. Consequently, passing `amount_paise=True` or `cap_points=False` into integer validators bypasses typical `isinstance(x, int)` guards unless `not isinstance(x, bool)` is explicitly checked.

## 2. Evidence
- In `tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account`, the test matrix includes `[0, -1, -50, -1000, 100001, 150000, 200000, 999999, True, None, "100", 1.5, [], {}, False]`.
- Without boolean guards, `True` was interpreted as `1` paise, allowing invalid events to pass validation and modify account state.
- In sequential refunds, incremental calculation resulted in `points_balance != 0` after 100% cumulative refund.

## 3. What I tried
1. **Incremental proportional formula:**
   - Attempted: `delta = (txn['awarded_points'] * refund) // txn['amount_paise']`.
   - Result: Produced 1-point truncation loss across multiple partial refunds; failed to guarantee that total reversed points equaled awarded points on full refund.
2. **Floating-point rounding:**
   - Attempted: Considered `round()` for deltas.
   - Result: Rejected immediately because it violates the specification's strict mandate for integer arithmetic and introduces IEEE-754 floating-point inaccuracies.
3. **Cumulative tracking approach:**
   - Maintained cumulative `refunded_paise` and cumulative `reversed_points` on each transaction record.
   - Calculated total target reversed points from cumulative refunded paise:
     `should_reverse = (txn['awarded_points'] * new_refunded) // txn['amount_paise']`
   - Delta for the current event: `delta = should_reverse - txn['reversed_points']`.

## 4. Resolution
- The cumulative tracking formula ensures mathematical convergence: when cumulative `refunded_paise == amount_paise`, `should_reverse` evaluates to `(awarded * amount) // amount == awarded`, guaranteeing 100% point reversal upon 100% refund.
- For the 15-point purchase:
  - Refund 1 (50%): `should_reverse = (15 * 50000) // 100000 = 7`; `delta = 7 - 0 = 7`.
  - Refund 2 (50%): `should_reverse = (15 * 100000) // 100000 = 15`; `delta = 15 - 7 = 8`.
  - Total reversed: `7 + 8 = 15`. Exact balance: `0`.
- Added explicit type guards across all numeric inputs:
  `if isinstance(val, bool) or not isinstance(val, int): return ...`
- Clamped reversal deltas to available points balance:
  `delta = min(delta, max(0, out['points_balance']))`
  ensuring the account points balance cannot drop below zero.

## 5. Proof and regression prevention
- Added `tests/test_regression.py::test_sequential_partial_refunds_no_rounding_drift` to assert that two 50% partial refunds reverse exactly 7 and 8 points, leaving 0 balance and 15 total reversed points.
- Added `tests/test_regression.py::test_malformed_event_fields_safe_handling` testing `True`, `False`, strings, and null inputs.
- All 221 tests pass cleanly (`python -m pytest -q`).

## 6. Unresolved challenge or next step
- In an expanded production system where points can be redeemed/spent across external reward partners, an account's balance could be 0 when a refund arrives for a previously awarded transaction.
- While our code safely clamps deduction to available balance so `points_balance` never goes negative, production operations would benefit from an "unrecovered points deficit" tracking ledger to recoup points on future purchases.