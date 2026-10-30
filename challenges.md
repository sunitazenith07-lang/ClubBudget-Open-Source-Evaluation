# Challenges and resolutions

## 1. Challenge or confusing behaviour

The first challenge was distinguishing floor-based reward calculation from the starter's use of `round()`. Amounts immediately below a ₹100 boundary were being treated as if they had crossed the boundary. A related issue was that a zero cap was treated as if no cap had been supplied because the starter used a truthiness check.

The second challenge was refund state management. Refunds can arrive in multiple partial events, so the implementation must preserve the cumulative refunded amount and cumulative reversed points. It must also reject excessive refunds before changing transaction state and must prevent the balance from becoming negative.

A final audit identified a third, narrower challenge: a missing captured-purchase amount was being defaulted to zero, which allowed a malformed event to create a zero-point transaction and ledger entry.

## 2. Evidence

The initial visible-test result was `147 passed, 67 failed` out of `214` tests.

The baseline failures included:

- Floor-boundary assertions where values such as `19999` paise received too many points.
- A zero-cap assertion where points were awarded despite `cap_points=0`.
- Purchase replay assertions where the same event ID appeared more than once.
- Refund assertions where negative or excessive amounts changed `refunded_paise`.
- Refund cases with malformed values that raised arithmetic errors.
- A missing purchase amount being accepted through the `event.get('amount_paise', 0)` default.

The refund requirements and added regression tests use a `100000`-paise purchase with `10` points. Refunds of `25000`, `25000`, and `50000` paise must produce incremental reversals of `2`, `3`, and `5`.

## 3. What I tried

The implementation history isolated the issues by comparing the failing assertions with the formulas and event-state fields in `service.py`, then addressing the work in stages:

1. Corrected the point formula and input validation.
2. Added an early processed-event check and purchase identifier validation.
3. Validated refunds before mutation and changed reversal calculation to use cumulative refund state.
4. Added seven refund regression tests covering partial refunds, rounding, replay, ledger deltas, immutability, and excessive refunds.
5. Removed the missing-amount default and added four purchase-validation regression tests for missing, `None`, non-integer, and explicit zero amounts.

No performance experiment or speed measurement was used; the investigation was focused on correctness and state transitions.

## 4. Resolution

The point defect was resolved by replacing floating-point rounding with integer floor division and by checking `cap_points is not None`, so zero is respected. Invalid and negative numeric inputs return zero points.

Purchase replay was resolved by checking a valid event ID before event-specific processing. A replay returns the deep-copied account without another financial mutation. Existing transaction IDs do not receive another award or purchase ledger entry.

Refunds were resolved by validating the event ID, transaction ID, refund amount, stored transaction state, refund limit, reversal bound, and resulting balance before updating state. The accepted transition then updates cumulative refund and reversal values and records the actual balance delta in one ledger entry.

The missing-amount defect was resolved by reading `amount_paise` without a zero fallback. Missing, `None`, and malformed non-integer amounts are rejected before financial mutation, while explicit zero remains accepted.

## 5. Proof and regression prevention

The seven added tests are:

- `test_multiple_partial_refunds_use_incremental_cumulative_reversals`
- `test_partial_refund_rounding_is_cumulative_and_bounded`
- `test_refund_replay_does_not_change_account_or_ledger`
- `test_each_accepted_refund_has_consistent_single_ledger_entry`
- `test_refund_order_preserves_cumulative_total_reversal`
- `test_multiple_refunds_do_not_mutate_input_account`
- `test_excessive_refund_leaves_financial_state_and_ledger_unchanged`

The final purchase-validation tests are:

- `test_purchase_missing_amount_is_rejected_without_financial_mutation`
- `test_purchase_none_amount_is_rejected_without_financial_mutation`
- `test_purchase_non_integer_amount_is_rejected_without_financial_mutation`
- `test_purchase_zero_amount_remains_accepted`

The earlier implementation milestone was `221 passed` before these four purchase-validation tests. Together with the existing contract and acceptance tests, the final reported result was `225 passed in 2.12s`.

One remaining coverage limitation is that not every possible malformed account container or inconsistent historical state is exercised by the visible tests.

## 6. Unresolved challenge or next step

The implementation intentionally does not silently repair an already inconsistent account. A future reconciliation design would need to define how to report or repair inconsistencies without creating unexplained ledger entries.

The visible tests also do not fully define behavior for every malformed outer input, such as a non-dictionary event or malformed account collection. Those cases should be specified before adding broader validation.
