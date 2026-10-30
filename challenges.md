# challenges.md - COMPULSORY submission

This file is mandatory and worth 5 marks. Describe your actual experience honestly. Do not invent difficulties to fill the page.

## 1. Challenge or confusing behaviour
The most confusing behavior was handling invalid refund types where booleans (`True` and `False`) were being accepted as valid integers by `isinstance(val, int)`. In Python, `bool` is a subclass of `int`, causing `True` to be treated as `1` and `False` as `0`. This caused `test_invalid_or_excess_refund_does_not_change_account[True]` to modify `refunded_paise` to 1 instead of leaving the account unchanged.

## 2. Evidence
In `test_acceptance_matrix.py`:
- `assert result['transactions']['T']['refunded_paise'] == 0` failed with `assert 1 == 0` when `amount = True`.
- `TypeError: unsupported operand type(s) for +=: 'int' and 'NoneType'` occurred when `amount = None`.
- `TypeError: unsupported operand type(s) for +=: 'int' and 'str'` occurred when `amount = '100'`.

## 3. What I tried
1. First tried `if not isinstance(refund, int): return out`. This failed for `True` because `isinstance(True, int)` evaluates to `True`.
2. Considered using `try...except TypeError:` around arithmetic operations, but catching generic exceptions masked contract failures and did not cleanly protect state mutation.
3. Evaluated `type(refund) is int` to enforce strict type identity, completely excluding boolean objects, strings, floats, and container types.

## 4. Resolution
Used explicit type check:
`if type(refund) is int and 0 < refund <= txn['amount_paise'] - txn['refunded_paise']:`
This simultaneously:
- Rejects booleans (`type(True) is bool`).
- Rejects zero and negative amounts (`0 < refund`).
- Rejects refunds exceeding the remaining unrefunded portion of the purchase.
- Avoids mutating `refunded_paise`, `points_balance`, `ledger`, or `processed_event_ids` on invalid inputs.

## 5. Proof and regression prevention
- Verified through all 15 parameterized cases in `test_invalid_or_excess_refund_does_not_change_account`.
- Added regression tests `test_regression_invalid_type_amount` and `test_regression_balance_never_negative` in `tests/test_contract.py` to prevent regression.

## 6. Unresolved challenge or next step
All tests in the acceptance suite and contract suite pass. In a future production iteration, adopting strongly typed models (e.g. dataclasses or Pydantic) would validate input types before they reach the core service functions, making type errors impossible at compile/import time.
