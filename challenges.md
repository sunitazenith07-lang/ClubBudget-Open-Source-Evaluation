# Challenges and debugging

This file is mandatory and worth 5 marks. Describe your actual experience honestly. Do not invent difficulties to fill the page.

## 1. Challenge or confusing behaviour
The most confusing bug I encountered was during refund validation in `test_acceptance_matrix.py`. A test was passing `True` as `amount_paise`, and my code was accepting it and treating it as 1 paise instead of ignoring the invalid event. I had assumed checking `isinstance(amount, int)` was enough to ensure a number, but in Python `bool` is actually a subclass of `int`.

Another tricky issue was handling multiple partial refunds on the same purchase. Calculating reversed points per-refund caused rounding discrepancies, and I had to make sure repeated partial refunds didn't accidentally reverse more points than originally awarded or drop the account balance below zero.

## 2. Evidence
When running pytest on the initial fix, the acceptance matrix failed on non-integer and boolean inputs:
```
FAILED tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account[True]
FAILED tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account[None]
FAILED tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account[100]
```
And in `test_contract.py`:
```
FAILED tests/test_contract.py::test_invalid_or_excess_refund_ignored - assert -1 == 0
```

## 3. What I tried
1. At first I just checked `if refund > 0:`. That immediately crashed with a `TypeError` when pytest passed `'100'` (strings cannot be compared to ints with `>`).
2. Next I tried `if isinstance(refund, int) and refund > 0:`. That fixed strings and `None`, but `True` still slipped through because `isinstance(True, int)` evaluates to `True` and `True > 0` is true in Python.
3. For partial refunds, I initially tried calculating the points delta directly from the refund chunk: `awarded_points * refund // total`. But when a customer makes multiple partial refunds (like ₹300, then ₹300, then ₹400 on a ₹1,000 purchase), calculating each chunk separately lost points to floor division and didn't add up to the total awarded points.

## 4. Resolution
- For input validation, I updated the check to `type(refund) is not int or refund <= 0`. Using `type(...) is int` avoids the boolean inheritance quirk entirely and cleanly rejects booleans, strings, floats, and empty values.
- For partial refunds, I changed the logic to calculate reversal against the cumulative refunded amount:
  ```python
  should_reverse = txn['awarded_points'] * txn['refunded_paise'] // max(1, txn['amount_paise'])
  should_reverse = min(txn['awarded_points'], max(0, should_reverse))
  delta = should_reverse - txn['reversed_points']
  delta = max(0, min(delta, out['points_balance']))
  ```
  This tracks cumulative refunds, takes the difference from points already reversed, and clamps `delta` so the balance never drops below zero.

## 5. Proof and regression prevention
- All 14 cases in `test_invalid_or_excess_refund_does_not_change_account` pass cleanly (including `True`, `False`, `None`, and excess values).
- I added `test_regression_multi_partial_refunds_cumulative` in `tests/test_regression.py` to test two consecutive partial refunds (40% then 60%) on a ₹1,000 purchase, confirming that 4 points and then 6 points are reversed, leaving the points balance at exactly 0.

## 6. Unresolved challenge or next step
Right now the service runs in-memory with simple dictionaries. If this were a multi-threaded web service or worker processing events concurrently, two workers receiving the same `event_id` at the same time could both read `processed_event_ids` before either writes to it, causing duplicate points. In a real application, we would back this with an SQL database using a unique constraint on `event_id` or an atomic transaction per account.
