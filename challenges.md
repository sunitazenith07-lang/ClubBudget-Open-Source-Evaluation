# challenges.md - COMPULSORY submission

This file is mandatory and worth 5 marks. Describe your actual experience honestly. Do not invent difficulties to fill the page.

## 1. Challenge or confusing behaviour
Two behaviors were initially subtle: (1) `test_invalid_or_excess_refund_does_not_change_account` passed `True` and `False` as `amount_paise`, which passed basic `isinstance(x, int)` checks in Python because `bool` subclasses `int`, and (2) `flag_repeat_transactions` failed boundary tests when `count == threshold`.

## 2. Evidence
- For `amount_paise = True`, `isinstance(True, int)` evaluated to `True`, causing a 1-paise refund (`refunded_paise == 1` instead of `0`).
- In `test_repeat_alert_threshold_boundaries`, `flag_repeat_transactions(rows, threshold=threshold)` with `threshold` items asserted `== []`, whereas the starter code's `len(ids) >= threshold` returned 1 alert.

## 3. What I tried
Ran `pytest` against `tests/test_acceptance_matrix.py` and inspected each parametrized failure for `test_invalid_or_excess_refund_does_not_change_account` and `test_repeat_alert_threshold_boundaries`.

## 4. Resolution
Added `_is_valid_int(val)` (`isinstance(val, int) and not isinstance(val, bool)`) to reject booleans across all calculations and events, and updated the repeat alert condition from `len(ids) >= threshold` to `len(ids) > threshold` with `threshold >= 1`.

## 5. Proof and regression prevention
Verified by `test_invalid_or_excess_refund_does_not_change_account`, `test_repeat_alert_threshold_boundaries`, and the new `test_boolean_and_non_int_inputs_rejected` regression test in `tests/test_contract.py`.

## 6. Unresolved challenge or next step
None for the current specification; a future enhancement would be structured schema validation (e.g., dataclasses or Pydantic) at the ingestion boundary.