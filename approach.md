# approach.md - Required submission

Complete this file in your own words. Be concise and specific to the work you actually performed.

## 1. Baseline
- Commands run before editing: `python -m pytest -q` and `python -m main`
- Initial test result (include the actual summary): `133 failed, 81 passed` (out of 214 total tests across `test_contract.py` and `test_acceptance_matrix.py`).
- Demo/output observed: `Points example: 100` and `Repeat warnings: [{'account_id': 'ACCT-1001', 'date': '2026-10-21', 'amount_paise': 259900, 'transaction_ids': ['TX-1', 'TX-2']}]`

## 2. Codebase understanding
- Important files/functions inspected: `service.py` (`calculate_points`, `apply_reward_event`, `flag_repeat_transactions`), `models.py` (`new_account`), `fixtures.py`, `tests/test_contract.py`, and `tests/test_acceptance_matrix.py`.
- Rewards calculation, refund, ledger or alert flow traced: Purchases award points per complete ₹100 (`10000` paise) block, update `points_balance`, record transaction state, and append to `ledger`. Refunds proportionally reverse awarded points using integer division. Repeat alerts group transactions by `(account_id, date, amount_paise)`.
- How you confirmed your understanding: Cross-checked `STUDENT_PROBLEM_STATEMENT.md` requirements against parametrized cases in `tests/test_acceptance_matrix.py`.

## 3. Investigation and implementation strategy
- Issue 1: `calculate_points` divided `amount_paise // 100` (1 rupee) instead of `amount_paise // 10000` (₹100), inflating base points by 100× (`calculate_points(19999, 1)` returned `199` instead of `1`). Fixed by flooring with `amount_paise // 10000` and validating integer inputs.
- Issue 2: `apply_reward_event` used `min(event.get('amount_paise', 0), remaining)` on refunds, which clamped excess refunds to a full refund instead of rejecting them and raised `TypeError` on `None`/strings/containers or accepted `True` as `1`. Fixed by validating `_is_valid_int(refund_paise)` and `0 < refund_paise <= remaining_paise`, and switching to integer division `//`.
- Issue 3 (if applicable): `flag_repeat_transactions` used `len(ids) >= threshold` instead of `len(ids) > threshold` and lacked validation for `threshold < 1` or missing fields. Fixed by filtering invalid records and requiring `len(ids) > threshold`.

## 4. Implementation decisions
- Main changes and why: Added `_is_valid_int` (`isinstance(val, int) and not isinstance(val, bool)`), fixed ₹100 unit conversion (`10000` paise), enforced strict bounds on refunds, and only recorded `event_id` for accepted events.
- Alternatives considered and why rejected: Clamping over-refunds was rejected because `test_invalid_or_excess_refund_ignored` requires excess refunds to leave `refunded_paise` at `0`.
- Assumptions: Only accepted `purchase_captured` and `refund_processed` events append to `ledger` and `processed_event_ids`.

## 5. Verification
- Tests added or changed: Added `test_boolean_and_non_int_inputs_rejected` and `test_cumulative_partial_refunds_and_over_refund_rejected` in `tests/test_contract.py`.
- Commands run and actual results: `python -m pytest -q` (`218 passed`) and `python -m main` (`Points example: 27`, `Repeat warnings: []`).
- Edge cases verified: Sub-₹100 amounts, `cap_points = 0`, boolean/null/container refund inputs, cumulative partial refunds, and threshold boundaries.
- Remaining failures or known limitations: None.