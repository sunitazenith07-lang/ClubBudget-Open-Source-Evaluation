# TESTING.md

## Test command and environment
- Python version: Python 3.14.7
- Command run: `python3 -m pytest -q`
- Actual test summary: `214 passed in 0.12s`

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | `calculate_points(19999, 1)` | Floor the amount to one whole ₹100 unit | Returned `1` | `test_points_use_floor`; acceptance calculation matrix |
| 2 | `calculate_points(50000, 1, cap_points=0)` | A zero cap produces zero points | Returned `0` | `test_cap_zero_is_respected`; `test_bonus_and_cap_matrix` |
| 3 | Replay the same `purchase_captured` event | Do not award points or append a duplicate event/ledger entry | Balance remained `2`; processed IDs were `['P1']`; one ledger entry | `test_purchase_event_replay_is_idempotent`; focused runtime check |
| 4 | Refund `50000` paise from a `100000` paise purchase | Reverse five of ten points proportionally | Balance became `5`; `reversed_points` became `5` | `test_partial_refund_reverses_proportionally` |
| 5 | Refund `-1`, `100001`, `None`, `True`, or `1.5` paise | Ignore invalid or excessive refunds | Balance remained `10`; refunded amount remained `0` | `test_invalid_or_excess_refund_does_not_change_account` |
| 6 | Declined, pending, and unknown event types | Do not award points or create transactions | Balance remained `0`; transactions remained empty | `test_unrecognized_or_declined_events_do_not_award_points` |

## Regression tests added
The existing contract and acceptance tests cover integer flooring, zero caps,
invalid values, captured-event filtering, event replay, proportional refunds,
and refund bounds. No test files were changed.

## Remaining failures or limitations
No known local test failures. The service is in-memory, so durable storage and
cross-process idempotency are outside the current exercise.
