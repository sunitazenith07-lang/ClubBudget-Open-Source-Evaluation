# Testing report

## Test command and environment

- **Python version:** Python 3.14.7
- **Test framework:** pytest (configured to discover tests under `tests/`)
- **Command run:** `python -m pytest -q`
- **Actual result:** `217 passed in 0.32s`
- **Demo command:** `python -m main`
- **Demo result:** completed successfully and printed:

  ```text
  Points example: 27
  Repeat warnings: []
  ```

The demo exercises the sample points calculation and repeat-alert example; it is separate from the pytest suite.

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Purchase amount `9999` paise at one point per 100 rupees | Award zero points because the amount is below 100 rupees. | Returned `0`. | `test_integer_floor_points_calculation[9999-0]` |
| 2 | Purchase amount `19999` paise at one point per 100 rupees | Award one point using floor division; do not round up. | Returned `1`. | `test_integer_floor_points_calculation[19999-1]`; `test_points_use_floor` |
| 3 | `50000` paise, rate `2`, bonus `50%`, cap `6` | Calculate 10 base points, 15 after bonus, then cap at 6. | Returned `6`. | `test_bonus_and_cap_matrix[50000-2-50-6-6]`; `test_bonus_then_cap` |
| 4 | Same calculation with a cap of zero | The zero cap must result in zero points. | Returned `0`. | `test_bonus_and_cap_matrix[50000-2-50-0-0]`; `test_cap_zero_is_respected` |
| 5 | Refund `50000` paise on a `100000`-paise purchase that awarded 10 points | Reverse 5 points proportionally; leave a balance of 5. | Balance became `5`, and the transaction recorded `5` reversed points. | `test_partial_refund_reverses_proportionally` |
| 6 | Replay the same refund event ID after the first refund was accepted | Do not add a second refund amount, ledger entry, or balance change. | Balance remained `5`; refunded amount stayed `50000`; ledger stayed at two entries (purchase and refund). | `test_refund_event_replay_is_idempotent` |
| 7 | Refund value is zero, negative, over the purchase amount, boolean, missing, text, float, list, or dictionary | Reject the refund without changing the recorded refunded amount or purchase balance. | The refunded amount remained `0` and the balance remained `10` for the tested invalid values. | `test_invalid_or_excess_refund_does_not_change_account[<value>]`; `test_invalid_or_excess_refund_ignored` |
| 8 | Captured purchase has no event ID | Do not award points or create a transaction or ledger entry because replay cannot be tracked safely. | Balance stayed `0`; transactions and ledger stayed empty. | `test_missing_event_identifier_cannot_award_purchase` |
| 9 | Repeat threshold is `2`, with exactly two same-account/date/amount transactions | Do not alert until the group count is greater than the threshold. | Returned no alert at two rows; the threshold tests also confirm an alert appears after adding a third. | `test_repeat_alert_threshold_boundaries[2]`; `test_repeat_alert_respects_threshold[2]` |
| 10 | Repeat records have a missing account, date, or otherwise distinct grouping key | Do not combine missing or distinct keys into a false alert. | Returned no alert for the tested invalid/distinct rows. | `test_repeat_alerts_do_not_mix_distinct_keys[...]`; `test_repeat_groups_ignore_records_missing_identifiers` |
| 11 | A declined, pending, or unknown event | Do not award points or create a purchase transaction. | Balance remained `0` and transactions remained empty. | `test_unrecognized_or_declined_events_do_not_award_points[...]`; `test_declined_event_does_not_award` |
| 12 | Apply a purchase event to an account, then inspect the original account | Return an updated copy without mutating the caller's original nested account data. | Original account matched its pre-call copy. | `test_event_processing_does_not_mutate_input_account[amount]`; `test_input_account_not_mutated` |

## Regression tests added

The existing tests were retained. Three focused tests were added in `tests/test_contract.py`:

- `test_refund_event_replay_is_idempotent` protects against replaying an already-processed refund and checks the balance, cumulative refund amount, processed event IDs, and ledger length.
- `test_missing_event_identifier_cannot_award_purchase` protects against applying a captured purchase that has no event ID.
- `test_repeat_groups_ignore_records_missing_identifiers` protects against creating repeat alerts from rows without a valid account identifier.

The broader acceptance matrix also checks point boundaries, bonus/cap combinations, invalid purchase rules, duplicate purchase events, refund bounds, repeat thresholds, event types, and input-account immutability.

## Remaining failures or limitations

- The final visible test suite had no failures: **217 passed**.
- The initial starter test run failed, but its exact summary was not retained; no baseline totals are claimed here.
- Tests use the repository's synthetic, in-memory examples. They do not verify persistence, concurrent processing, or behavior under production-scale account histories.
- The account event processor expects the account mappings and nested list/dictionary fields used by `models.new_account`; arbitrary malformed account structures are outside the tested contract.
