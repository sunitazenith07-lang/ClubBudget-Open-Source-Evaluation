# Testing and Verification

## Environment

- Python version requirement: Python 3.10+
- Dependency installation:
  `python -m pip install -r requirements-dev.txt`

## Running tests

- Command: `python -m pytest -q`
- Final verified result: `225 passed in 2.12s`.

The earlier implementation milestone was reported as `221 passed` before the four purchase-amount regression tests were added. The final result above includes those tests.

## Running the application

- Command: `python -m main`
- Most recently verified output:

```text
Points example: 27
Repeat warnings: []
```

This is the most recently reported output from the completed verification run; it was not newly executed while writing this document.

## Edge cases

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Amount below ₹100, such as `9999` paise | The base calculation uses floor division, so it earns zero base points. | The floor-boundary cases pass with zero points. | `test_integer_floor_points_calculation` in `tests/test_acceptance_matrix.py` |
| 2 | `cap_points=0` | The zero cap is applied after the bonus and results in zero points. | The zero-cap assertion passes. | `test_cap_zero_is_respected` in `tests/test_contract.py`; `test_bonus_and_cap_matrix` in `tests/test_acceptance_matrix.py` |
| 3 | Invalid or negative reward inputs, including negative amounts and invalid rule values | Invalid inputs must not generate points or negative results. | The invalid amount and rule-value cases pass. | `test_negative_amount_gives_zero`, `test_invalid_purchase_amount_awards_zero_points`, and `test_invalid_rule_values_do_not_create_negative_points` |
| 4 | Replaying a captured purchase event with the same event ID | The replay must not award points, add a transaction, or add another purchase ledger entry. | The replay cases pass and retain one processed event ID and one ledger entry. | `test_purchase_event_once` and `test_purchase_event_replay_is_idempotent` |
| 5 | Pending and declined purchase events | They must not earn points or create purchase transactions. | The unsupported, pending, and declined event cases pass. | `test_declined_event_does_not_award` and `test_unrecognized_or_declined_events_do_not_award_points` |
| 6 | Replaying the same valid refund event | The second application must not reverse points or change transaction, ledger, or account state. | The complete account remains unchanged on replay. | `test_refund_replay_does_not_change_account` |
| 7 | Multiple partial refunds of `25000`, `25000`, and `50000` paise against a `100000`-paise purchase | Cumulative integer rounding produces incremental reversals of `2`, `3`, and `5` points, ending at ten reversed points. | The final refund total is `100000`, reversed points are `10`, and the balance is zero. | `test_multiple_partial_refunds_use_incremental_cumulative_reversals` |
| 8 | A refund exceeding the remaining refundable amount | It must be rejected without changing balance, transaction refund totals, reversed points, or the financial ledger. | The excessive-refund state remains unchanged. | `test_excessive_refund_leaves_financial_state_and_ledger_unchanged`; `test_refund_amount_bounds_and_balance` |

## Purchase validation regression coverage

The final regression additions in `tests/test_contract.py` cover:

- `test_purchase_missing_amount_is_rejected_without_financial_mutation`
- `test_purchase_none_amount_is_rejected_without_financial_mutation`
- `test_purchase_non_integer_amount_is_rejected_without_financial_mutation`
- `test_purchase_zero_amount_remains_accepted`

The first three verify unchanged balance, transactions, and financial ledger, with the valid event ID recorded as processed. The zero-amount case remains accepted, creates a zero-value transaction and ledger entry, and leaves the balance unchanged.

## Refund regression coverage

The seven added regression tests in `tests/test_contract.py` are:

1. `test_multiple_partial_refunds_use_incremental_cumulative_reversals` verifies the `2`, `3`, and `5` incremental reversals across a full refund.
2. `test_partial_refund_rounding_is_cumulative_and_bounded` verifies cumulative reversal state and that reversed points do not exceed awarded points.
3. `test_refund_replay_does_not_change_account_or_ledger` verifies that replaying a refund returns the same complete account state.
4. `test_each_accepted_refund_has_consistent_single_ledger_entry` verifies one new ledger entry per accepted refund and checks each ledger delta against the balance change.
5. `test_refund_order_preserves_cumulative_total_reversal` verifies that cumulative refunded amount determines the final reversal.
6. `test_multiple_refunds_do_not_mutate_input_account` verifies that chained refund processing does not mutate the input account.
7. `test_excessive_refund_leaves_financial_state_and_ledger_unchanged` verifies that an excessive refund leaves financial state and the ledger unchanged.

## Important implementation notes

- Point calculations use integer arithmetic. Base points use floor division: `amount_paise // 10000`.
- The bonus is calculated with integer floor division before `cap_points` is applied.
- A cap of zero is active and produces zero points.
- Refund reversal uses the cumulative refunded amount. The total reversal is calculated from cumulative refunded paise, and only the difference from the previous reversal is applied for the current refund.
- Each accepted purchase or refund records `points_delta` as the actual balance change, calculated from the balance after processing minus the balance before processing.
- A valid event ID for a rejected event is recorded in `processed_event_ids` according to the implementation, but rejected events do not create financial ledger entries.
- Missing or empty event IDs are rejected safely without processing.
- Missing or empty transaction IDs are rejected safely for purchase and refund events.
- Missing, `None`, and non-integer captured-purchase amounts are rejected without financial mutation; valid zero-amount purchases are accepted with zero balance impact.
- Unknown refund transactions are rejected safely without creating a transaction or financial ledger entry.

## Known limitations

- `data/records.json` is investigation and test material; `python -m main` does not load it. The demo uses the sample data from `fixtures.py`.
- The visible tests do not exhaustively cover malformed account containers or every possible inconsistent historical account state.
- The repeat-alert function returns advisory groups only; the demo does not process those alerts into a separate workflow.
