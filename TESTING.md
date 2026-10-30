# TESTING.md — Required submission

Complete this file with test evidence from your own work. Include at least five edge cases. Do not claim a test passed unless you ran it.

## Test command and environment
- Python version: 3.14.7 (from conda)
- Command run: `python -m pytest -q`
- Actual test summary: 214 passed, 0 failed

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | `calculate_points(19999, 1)` | Should return 1 (floor of 1.9999) | Returned 1 | `test_points_use_floor` |
| 2 | `calculate_points(50000, 1, cap_points=0)` | Should return 0 (cap of zero means zero points) | Returned 0 | `test_cap_zero_is_respected` |
| 3 | `calculate_points(50000, 2, 50, 6)` | Should return 15 (50000 paise × 2 × 150 / 100, capped at 6) | Returned 6 | `test_bonus_and_cap_matrix` |
| 4 | `apply_reward_event` with `purchase_declined` event | Should award 0 points, empty transactions | 0 points, {} transactions | `test_unrecognized_or_declined_events_do_not_award_points` |
| 5 | `apply_reward_event` with `True` as refund amount | Should reject entirely, no changes to account | Rejected, account unchanged | `test_invalid_or_excess_refund_does_not_change_account[True]` |

## Regression tests added
List the defects fixed and the tests added to prevent them from returning.

- Fixed `calculate_points()` floor division: test `test_points_use_floor` now passes
- Fixed `cap_points=0` handling: test `test_cap_zero_is_respected` now passes
- Fixed event ID deduplication: test `test_purchase_event_once` now passes
- Fixed refund validation: tests `test_invalid_or_excess_refund_does_not_change_account` all pass

## Remaining failures or limitations
List any known failing tests or unresolved behaviours honestly.

- None — all 214 visible tests pass after fixes
- No known limitations at this time