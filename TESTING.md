# TESTING.md — Required submission

## Test command and environment
- Python version: 3.14.8
- Command run: `python -m pytest -q`
- Actual test summary: `214 passed in 0.13s`

## Edge-case evidence
| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | `calculate_points(9999, 1)` | 0 points (floor boundary) | 0 | `test_integer_floor_points_calculation` |
| 2 | `calculate_points(50000, 2, 50, 6)` | 6 points after cap | 6 | `test_bonus_and_cap_matrix` |
| 3 | Purchase 100000 paise then refund 125000 paise | No change: `refunded_paise == 0`, balance 10 | No change | `test_invalid_or_excess_refund_does_not_change_account` |
| 4 | Replay same purchase event twice | Balance stays 2, one ledger entry | Balance stays 2, one ledger entry | `test_purchase_event_replay_is_idempotent` |
| 5 | 4 identical transactions with threshold 2 | One alert with 4 transaction IDs | One alert with 4 transaction IDs | `test_repeat_alert_respects_threshold` |
| 6 | Mixed account/date/amount rows | No alert for distinct keys | `[]` | `test_repeat_alerts_do_not_mix_distinct_keys` |

## Regression tests added
No new test files were added; the existing 214 tests were used as the acceptance contract. Defects fixed: floor rounding, bonus/cap ordering, invalid refund handling, and defensive repeat-alert input handling.

## Remaining failures or limitations
None. All 214 tests pass. Float or boolean inputs are treated as invalid and produce zero points/no refund change.
