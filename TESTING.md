# TESTING.md — Required submission

## Test command and environment
- Python version: 3.14.7 (Homebrew, macOS), pytest 9.2.0, in a virtual environment
- Command run: `python -m pytest -q` and `python -m main`
- Actual test summary:
  - Baseline (untouched starter): `67 failed, 147 passed in 0.17s`
  - After fix: `249 passed in 0.06s` (214 original + 35 new; 0 failed, 0 errors, 0 skipped)
  - After stretch item: `264 passed in 0.06s` (+15 in `tests/test_threshold_config.py`)
  - After stress-test fixes: `277 passed in 0.07s` (+13 in `tests/test_regressions.py`: list/dict IDs are ignored instead of crashing, alert IDs are sorted)
  - `python -m main --threshold 1` → one alert for TX-1/TX-2; `python -m main --threshold 0` → `error: --threshold must be 1 or more`
  - Demo after fix: `Points example: 27`, `Repeat warnings: []` (starter printed 28)

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Purchase of 19999 paise, 1 pt/₹100 | Floor to 1 point (not round to 2) | 1 | `test_points_use_floor`, `test_integer_floor_points_calculation[19999-1]` |
| 2 | `cap_points=0` on 50000 paise | 0 points (cap of zero is a real cap) | 0 | `test_cap_zero_is_respected` |
| 3 | Same purchase `event_id` applied twice | Balance and ledger change once | balance 2, 1 ledger entry, `processed_event_ids == ['E1']` | `test_purchase_event_replay_is_idempotent` |
| 4 | Refund of `True`, `"100"`, `1.5`, `0`, `-1`, or 150000 on a 100000 purchase | Ignored, balance stays 10 | `refunded_paise` 0, balance 10 | `test_invalid_or_excess_refund_does_not_change_account` |
| 5 | Refunds 60000 then 60000 on a 100000 purchase | Second refund rejected (total would exceed purchase) | `refunded_paise` 60000, balance 4 | `test_cumulative_refunds_cannot_exceed_purchase` |
| 6 | Partial refunds 10000 + 10000 + 5000 on a 25000 purchase (2 pts) | All 2 points reversed by the end, never below 0 | `reversed_points` 2, balance 0 | `test_partial_refunds_sum_to_full_reversal` |
| 7 | Event without `event_id` or `transaction_id` | Ignored, nothing recorded | balance 0, empty ledger | `test_event_missing_identifier_is_ignored` |
| 8 | Repeat threshold `0` or `-1` with one transaction | Treated as 1, no alert | `[]` | `test_non_positive_threshold_is_treated_as_one` |
| 9 | Exactly `threshold` matching transactions, then one more | No alert, then exactly one alert | `[]`, then 1 group | `test_repeat_alert_threshold_boundaries` |
| 10 | All 264 dataset reward events replayed | Balance never negative; ledger deltas sum to balance; no duplicate IDs | holds for every account | `test_dataset_reward_events_keep_ledger_consistent` |

## Regression tests added
All in `tests/test_regressions.py`:
- Float rounding / cap-zero / invalid rules → `test_invalid_rule_values_award_zero`, `test_non_integer_amount_awards_zero`, `test_bonus_over_100_percent_then_cap`
- Missing duplicate check → `test_second_capture_of_same_transaction_with_new_event_id_does_not_award_twice`, `test_duplicate_refund_event_is_applied_once`, `test_rejected_event_id_can_be_retried_with_valid_data`
- Missing identifiers / bad amounts → `test_event_missing_identifier_is_ignored`, `test_invalid_purchase_amount_creates_no_transaction`
- Unbounded refunds → `test_cumulative_refunds_cannot_exceed_purchase`, `test_partial_refunds_sum_to_full_reversal`, `test_balance_never_negative_even_if_account_already_low`
- Ledger audit fields → `test_ledger_entries_are_auditable_and_sum_to_balance`, `test_dataset_reward_events_keep_ledger_consistent`
- Repeat alerts → `test_empty_input_gives_no_alerts`, `test_non_positive_threshold_is_treated_as_one`, `test_rows_missing_keys_are_not_grouped`, `test_alert_order_is_deterministic_and_marked_for_review`, `test_dataset_repeat_groups_are_flagged`

No existing test was edited, skipped or deleted, and the CI workflow is unchanged.

Stretch item (configurable threshold), in `tests/test_threshold_config.py`: `test_threshold_read_from_config`, `test_missing_or_invalid_config_falls_back_to_default`, `test_dataset_threshold_matches_default_result`, `test_raising_threshold_reduces_alerts`, `test_cli_threshold_default_and_override`, `test_cli_threshold_one_flags_sample_pair`, `test_cli_rejects_invalid_threshold`.

## Remaining failures or limitations
- No failing tests.
- Zero-amount transactions are excluded from repeat alerts (48 groups on the dataset instead of 60). This is an assumption, not something the tests require.
- Numeric strings such as `"100000"` are rejected, not parsed.
- Points redeemed elsewhere are not modelled; a refund reversal is clamped to the current balance.
