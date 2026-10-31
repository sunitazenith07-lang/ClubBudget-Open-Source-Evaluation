# TESTING.md — Required submission

Complete this file with test evidence from your own work. Include at least five edge cases. Do not claim a test passed unless you ran it.

## Test command and environment
- Python version: 3.14.7 (from conda)
- Command run: `python -m pytest -q`
- Actual test summary: 221 passed, 0 failed

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | `calculate_points(19999, 1)` | Should return 1 (floor of 1.9999) | Returned 1 | `test_points_use_floor` |
| 2 | `calculate_points(50000, 1, cap_points=0)` | Should return 0 (cap of zero means zero points) | Returned 0 | `test_cap_zero_is_respected` |
| 3 | `calculate_points(50000, 2, 50, 6)` | Should return 15 (50000 paise × 2 × 150 / 100, capped at 6) | Returned 6 | `test_bonus_and_cap_matrix` |
| 4 | `apply_reward_event` with `purchase_declined` event | Should award 0 points, empty transactions | 0 points, {} transactions | `test_unrecognized_or_declined_events_do_not_award_points` |
| 5 | `apply_reward_event` with `True` as refund amount | Should reject entirely, no changes to account | Rejected, account unchanged | `test_invalid_or_excess_refund_does_not_change_account[True]` |
| 6 | Applying the same refund `event_id` twice | Reversal should happen once, balance unchanged on replay | First: balance 5, replay: still 5, ledger still 2 entries | `test_regression.py::test_replayed_refund_event_reverses_once` |
| 7 | Partial refund of 60000 on a 100000 purchase, then another 60000 | Second refund must be rejected (cumulative > purchase) | First: balance 4, refunded 60000; second rejected, balance still 4 | `test_regression.py::test_cumulative_refunds_cannot_exceed_purchase` |

## Regression tests added
List the defects fixed and the tests added to prevent them from returning.

- Fixed `calculate_points()` floor division: `test_regression.py::test_floor_not_round_at_boundaries` added along with `test_points_use_floor`
- Fixed `cap_points=0` handling: `test_regression.py::test_cap_zero_is_respected_for_any_amount` added along with `test_cap_zero_is_respected`
- Fixed event ID deduplication: `test_regression.py::test_replayed_purchase_event_awards_once` and `test_replayed_refund_event_reverses_once` added along with `test_purchase_event_once`
- Fixed refund validation: `test_regression.py::test_boolean_refund_rejected` and `test_cumulative_refunds_cannot_exceed_purchase` added along with `test_invalid_or_excess_refund_does_not_change_account`
- Fixed negative amounts awarding points: `test_regression.py::test_negative_amounts_never_award` added

## Remaining failures or limitations
List any known failing tests or unresolved behaviours honestly.

- None — all 221 tests pass after fixes (214 original + 7 regression)
- No known limitations at this time