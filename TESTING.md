# TESTING.md — Required submission

Complete this file with test evidence from your own work. Include at least five edge cases. Do not claim a test passed unless you ran it.

## Test command and environment
- Python version: Python 3.9.6 (Darwin macOS) / Python 3.11 (CI runner)
- Command run: `python3 -m pytest -v`
- Actual test summary: Baseline had 67 failed, 147 passed (214 total). After resolving all defects, null-field edge cases, and adding regression tests, 229 passed, 0 failed in 0.17s.

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | `calculate_points(19999, 1)` (199.99 INR) | Floor division truncates paise: `floor(19999/10000) * 1 = 1` point | 1 | `test_points_use_floor` / `test_paise_boundary_rounding` |
| 2 | `calculate_points(50000, 1, cap_points=0)` | Strict cap of 0 points awards 0 points | 0 | `test_cap_zero_is_respected` |
| 3 | Replaying event `{"event_id": "E1", "type": "purchase_captured", ...}` twice | Idempotent handling: balance remains 2, ledger has 1 entry, `processed_event_ids` has `['E1']` | Balance 2, 1 ledger entry, `processed_event_ids=['E1']` | `test_purchase_event_once`, `test_purchase_event_replay_is_idempotent` |
| 4 | Excess refund `amount_paise = 150000` on 100000 purchase | Excess refund is ignored; balance remains 10, refunded paise remains 0 | `refunded_paise=0`, `points_balance=10` | `test_invalid_or_excess_refund_ignored` |
| 5 | Non-integer types `True`, `False`, `None`, `"10000"` to `calculate_points` / `apply_reward_event` | Safely rejected and yields 0 points without throwing runtime TypeError | 0 points / account unmutated | `test_non_int_types_award_zero`, `test_invalid_or_excess_refund_does_not_change_account` |
| 6 | Account with null fields `{"points_balance": None, "processed_event_ids": None, ...}` | Sanitized safely without crashing with `TypeError: argument of type 'NoneType' is not iterable` | Sanitized to valid defaults, event processed cleanly | `test_corrupted_or_null_account_fields_handled_safely` |
| 7 | Rule with null values `{"bonus_percent": None, "points_per_100_rupees": None}` | Defaults `bonus_percent` to 0% and `points_per_100_rupees` to 1, awarding base points | Base points awarded | `test_rules_with_none_values_use_proper_defaults`, `test_bonus_percent_none_defaults_to_zero` |
| 8 | Repeat alert with `threshold=None` or boolean | Defaults safely to 2 without crashing with `TypeError: '>' not supported between instances of 'int' and 'NoneType'` | Flagged correctly when count > 2 | `test_threshold_none_or_invalid_defaults_to_two` |

## Regression tests added
List the defects fixed and the tests added to prevent them from returning.
- `TestCalculatePointsRegression::test_non_int_types_award_zero`: Validates non-integer types (bool, str, None, list) return 0.
- `TestCalculatePointsRegression::test_bonus_percent_none_defaults_to_zero`: Validates `bonus_percent=None` defaults to 0% bonus rather than failing.
- `TestCalculatePointsRegression::test_invalid_rules_award_zero`: Validates negative or boolean rule arguments return 0.
- `TestCalculatePointsRegression::test_paise_boundary_rounding`: Validates floor boundary behavior at 9999, 10000, 10001, 19999, 20000.
- `TestCalculatePointsRegression::test_large_bonus_and_strict_cap`: Validates bonus > 100% and cap=0.
- `TestApplyRewardEventRegression::test_missing_event_or_transaction_id_is_safe`: Validates missing IDs safely leave account unmutated.
- `TestApplyRewardEventRegression::test_corrupted_or_null_account_fields_handled_safely`: Validates accounts with None values in keys don't throw TypeError.
- `TestApplyRewardEventRegression::test_cross_account_event_rejected`: Validates events targeting a different account ID are discarded.
- `TestApplyRewardEventRegression::test_rules_with_none_values_use_proper_defaults`: Validates rules with None keys default safely.
- `TestApplyRewardEventRegression::test_cumulative_partial_refunds_and_over_refund`: Validates multi-step partial refunds and rejection of subsequent over-refund.
- `TestApplyRewardEventRegression::test_refund_event_idempotency`: Validates replayed refund events cannot decrease points balance twice.
- `TestApplyRewardEventRegression::test_refund_balance_never_negative`: Validates that refund reversal deltas cannot drag balance below 0.
- `TestFlagRepeatTransactionsRegression::test_non_list_or_empty_transactions`: Validates safe handling of None/non-list input.
- `TestFlagRepeatTransactionsRegression::test_threshold_none_or_invalid_defaults_to_two`: Validates threshold=None defaults to 2 without TypeError.
- `TestFlagRepeatTransactionsRegression::test_deterministic_sorting`: Validates deterministic ordering by account and date.

## Remaining failures or limitations
List any known failing tests or unresolved behaviours honestly.
- None. All 214 visible tests and 15 regression tests pass (229 passed total).
