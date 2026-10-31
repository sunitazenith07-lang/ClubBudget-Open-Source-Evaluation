# TESTING.md — Required submission

## Test command and environment
- Python version: 3.10+
- Command run: `python -m pytest -q`
- Actual test summary: `221 passed in 0.79s`
- Demo command: `python main.py` -> successful output

## Edge-case evidence
| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Replay same purchase event | No double points, one event ID | Passed | `test_purchase_event_replay_is_idempotent` |
| 2 | Invalid refund amount (`True`, `"100"`, `1.5`, excess) | Account unchanged | Passed | `test_invalid_or_excess_refund_does_not_change_account` |
| 3 | Boundary refund amounts | Proportional reversal and non-negative balance | Passed | `test_refund_amount_bounds_and_balance` |
| 4 | Negative/invalid points rules | No negative points | Passed | `test_invalid_rule_values_do_not_create_negative_points` |
| 5 | Empty/malformed repeat inputs | Safe list result, no crash | Passed | `test_repeat_alert_threshold_input_is_handled` |

## Regression tests added
- Added `tests/test_regression.py` with 7 regression tests covering replay idempotency, invalid refunds, partial refunds, points calculation, repeat threshold boundaries, input non-mutation, and unrecognized events.

## Remaining failures or limitations
No code-test failures remain. Documentation should be reviewed for submission completeness.
