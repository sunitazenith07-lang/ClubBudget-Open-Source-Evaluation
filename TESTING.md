# TESTING.md — Required submission

## Test command and environment
- Python version: 3.14.7 (Homebrew on macOS), pytest 9.2.0, inside a virtual environment
- Command run: `python -m pytest -q` and `python -m main`
- Actual test summary:
  - Before my changes (starter code): `67 failed, 147 passed in 0.17s`
  - After the main fix: `249 passed in 0.06s` (214 original + 35 new; nothing failed or skipped)
  - After the stretch item: `264 passed in 0.06s` (+15 in `tests/test_threshold_config.py`)
  - After the stress-test fixes: `277 passed in 0.07s` (+13 in `tests/test_regressions.py`)
  - Demo: `Points example: 27`, `Repeat warnings: []` (the starter printed 28)
  - `python -m main --threshold 1` shows one alert for TX-1/TX-2, and `python -m main --threshold 0` gives `error: --threshold must be 1 or more`

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Purchase of 19999 paise, 1 pt per ₹100 | 1 point (round down, not up to 2) | 1 | `test_points_use_floor`, `test_integer_floor_points_calculation[19999-1]` |
| 2 | `cap_points=0` on 50000 paise | 0 points (a cap of 0 is still a cap) | 0 | `test_cap_zero_is_respected` |
| 3 | Same purchase `event_id` sent twice | Balance and ledger only change once | balance 2, 1 ledger line, `processed_event_ids == ['E1']` | `test_purchase_event_replay_is_idempotent` |
| 4 | Refund of `True`, `"100"`, `1.5`, `0`, `-1`, or 150000 on a 100000 purchase | Ignored, balance stays 10 | `refunded_paise` 0, balance 10 | `test_invalid_or_excess_refund_does_not_change_account` |
| 5 | Two refunds of 60000 on a 100000 purchase | Second one rejected (the total would be too much) | `refunded_paise` 60000, balance 4 | `test_cumulative_refunds_cannot_exceed_purchase` |
| 6 | Refunds of 10000 + 10000 + 5000 on a 25000 purchase (2 pts) | All 2 points taken back by the end, never below 0 | `reversed_points` 2, balance 0 | `test_partial_refunds_sum_to_full_reversal` |
| 7 | Event with no `event_id` or no `transaction_id` | Ignored | balance 0, empty ledger | `test_event_missing_identifier_is_ignored` |
| 8 | Repeat threshold `0` or `-1` with one transaction | Treated as 1, so no alert | `[]` | `test_non_positive_threshold_is_treated_as_one` |
| 9 | Exactly `threshold` matching transactions, then one more | No alert, then one alert | `[]`, then 1 group | `test_repeat_alert_threshold_boundaries` |
| 10 | `transaction_id` is a list `[]` or dict `{}` | Ignored, no crash | balance 0, no transactions | `test_unhashable_identifier_is_ignored_not_crashing` |
| 11 | All 264 dataset events replayed | Balance never negative, ledger adds up to the balance, no duplicate IDs | true for every account | `test_dataset_reward_events_keep_ledger_consistent` |

## Regression tests added
All of these are in `tests/test_regressions.py`:
- Rounding / cap 0 / bad rules: `test_invalid_rule_values_award_zero`, `test_non_integer_amount_awards_zero`, `test_bonus_over_100_percent_then_cap`
- Duplicates: `test_second_capture_of_same_transaction_with_new_event_id_does_not_award_twice`, `test_duplicate_refund_event_is_applied_once`, `test_rejected_event_id_can_be_retried_with_valid_data`
- Missing IDs / bad amounts: `test_event_missing_identifier_is_ignored`, `test_unhashable_identifier_is_ignored_not_crashing`, `test_invalid_purchase_amount_creates_no_transaction`
- Refund limits: `test_cumulative_refunds_cannot_exceed_purchase`, `test_partial_refunds_sum_to_full_reversal`, `test_balance_never_negative_even_if_account_already_low`
- Ledger: `test_ledger_entries_are_auditable_and_sum_to_balance`, `test_dataset_reward_events_keep_ledger_consistent`
- Repeat alerts: `test_empty_input_gives_no_alerts`, `test_non_positive_threshold_is_treated_as_one`, `test_rows_missing_keys_are_not_grouped`, `test_unhashable_alert_keys_are_skipped_not_crashing`, `test_alert_order_is_deterministic_and_marked_for_review`, `test_alert_transaction_ids_do_not_depend_on_input_order`, `test_dataset_repeat_groups_are_flagged`

Stretch item tests, in `tests/test_threshold_config.py`: `test_threshold_read_from_config`, `test_missing_or_invalid_config_falls_back_to_default`, `test_dataset_threshold_matches_default_result`, `test_raising_threshold_reduces_alerts`, `test_cli_threshold_default_and_override`, `test_cli_threshold_one_flags_sample_pair`, `test_cli_rejects_invalid_threshold`.

I didn't edit, skip or delete any existing test, and I didn't change the CI workflow.

I also ran a separate random stress test (thousands of generated inputs, not part of the submission). That's what found the list/dict crash and the ID-order issue that tests 10 and above now cover.

## Remaining failures or limitations
- No failing tests.
- Amount-0 transactions are left out of repeat alerts (48 groups on the dataset instead of 60). That's my assumption, not something the tests require.
- Numbers sent as strings, like `"100000"`, are rejected, not converted.
- If points were already spent, a refund only takes back what's left in the balance.
