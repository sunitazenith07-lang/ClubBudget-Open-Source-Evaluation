# challenges.md - COMPULSORY submission

This file is mandatory and worth 5 marks. Describe your actual experience honestly. Do not invent difficulties to fill the page.

## 1. Challenge or confusing behaviour
The most intricate challenge was ensuring idempotency across multiple event replays while simultaneously maintaining audit integrity between `processed_event_ids`, `transactions`, and `ledger`. Specifically:
1. Replaying an event must not append duplicate entries to `processed_event_ids` or re-apply point deltas to `ledger`.
2. Python's type system treats `bool` as an instance of `int` (`isinstance(True, int) == True`). When tests passed `True` or `False` as `amount_paise`, standard checks like `isinstance(amount, int)` evaluated to `True`, inadvertently treating `True` as `1` paise.
3. Partial refunds that cumulatively exceed the original purchase amount had to be rejected without modifying the account's existing `refunded_paise`, `reversed_points`, or `points_balance`.

## 2. Evidence
- In `test_purchase_event_replay_is_idempotent`:
  ```
  AssertionError: assert ['PURCHASE-00...PURCHASE-005'] == ['PURCHASE-005']
  Left contains one more item: 'PURCHASE-005'
  ```
- In `test_invalid_or_excess_refund_does_not_change_account`:
  Running with `amount = True` resulted in `result["transactions"]["T"]["refunded_paise"] == 1` instead of `0`.
- In `test_refund_amount_bounds_and_balance`:
  Refunds of `125000` paise on a `100000` paise purchase improperly modified `refunded_paise` to `125000`.

## 3. What I tried
- Initially, checked if simply checking `event_id not in out['processed_event_ids']` at the point of appending was sufficient. However, if the idempotency check was deferred to the end of the function, the intermediate transaction calculations and points mutations still executed.
- For type validation, tested `isinstance(amount, int)` which failed because boolean values passed through.
- For excess refunds, tested comparing `refund > txn['amount_paise']`, which worked for single refunds but failed to catch cumulative over-refunds across multiple partial refund events.

## 4. Resolution
- Early idempotency return: Placed `if event_id in out['processed_event_ids']: return out` at the very entry of `apply_reward_event`. This immediately halts execution on replayed events without cloning mutations or appending duplicate IDs.
- Robust integer validation: Applied `not isinstance(x, int) or isinstance(x, bool)` across all amount and rule checks to explicitly filter out booleans.
- Cumulative refund bound check: Verified `if txn['refunded_paise'] + refund > txn['amount_paise']: return out`. If the cumulative refund exceeds the original purchase amount, the transaction remains completely untouched.
- Proportional integer floor reversal: Calculated reversal points as `(txn['awarded_points'] * txn['refunded_paise']) // max(1, txn['amount_paise'])`, clamped to `out['points_balance']` to prevent negative point balances.

## 5. Proof and regression prevention
- Verified that all 20 parameterized test cases in `test_purchase_event_replay_is_idempotent` pass.
- Verified that all 13 test cases in `test_invalid_or_excess_refund_does_not_change_account` pass.
- Added comprehensive regression tests in `tests/test_regression.py`:
  - `test_regression_event_replay_idempotency_no_list_duplication`
  - `test_regression_refund_event_replay_idempotency`
  - `test_regression_cumulative_partial_refunds_and_excess_rejection`
  - `test_regression_boolean_inputs_not_treated_as_integers`

## 6. Unresolved challenge or next step
All 222 tests in the test suite pass cleanly without failures or regressions. A valuable future improvement in production would be adding an append-only event store or schema validation (e.g., Pydantic or dataclasses) instead of raw dictionaries, ensuring compile-time/runtime type safety for currency amounts and promotional rule definitions.
