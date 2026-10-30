# TESTING.md — Required submission

This file records the actual validation evidence from the repository work performed and verified locally.

## Test command and environment
- Python version: 3.14.7
- Command run: `python3 -m pytest -q`
- Actual test summary: 214 passed in 0.04s

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | `calculate_points(19999, 1)` | Should floor to 1 point, not 2 | Result was `1` | `tests/test_contract.py::test_points_use_floor` |
| 2 | `calculate_points(50000, 2, 50, 6)` | Bonus should apply before cap, then cap to 6 | Result was `6` | `tests/test_contract.py::test_bonus_then_cap` |
| 3 | `calculate_points(-10000, 1)` | Negative purchase amount must award zero | Result was `0` | `tests/test_contract.py::test_negative_amount_gives_zero` |
| 4 | Replaying the same purchase event with same `event_id` | Duplicate event should not award points twice | `points_balance` stayed at 2 and `processed_event_ids` remained a single-item list | `tests/test_contract.py::test_purchase_event_once` and `tests/test_acceptance_matrix.py::test_purchase_event_replay_is_idempotent` |
| 5 | Refund amount `150000` on a `100000` purchase | Excess refund must be ignored; no additional reversal | `refunded_paise` stayed `0` and balance remained `10` | `tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account` |
| 6 | Same account + same date + same amount repeated above threshold | Repeat detection should flag grouped transactions | Returned group contained all matching IDs once only | `tests/test_contract.py::test_repeat_group` |
| 7 | Different account with same date and amount | Distinct accounts must not be mixed into the same alert group | Result was `[]` | `tests/test_contract.py::test_different_accounts_not_grouped` |

## Regression tests added
The defects were addressed by fixing the underlying logic in `service.py`, and the repository already includes regression coverage in:
- `tests/test_contract.py`
- `tests/test_acceptance_matrix.py`

These cover the core bug classes that were fixed:
- integer flooring and bonus/cap logic
- invalid negative or malformed inputs
- event idempotency and replay safety
- refund bounds and proportional reversal
- repeated transaction alert grouping and threshold handling

## Remaining failures or limitations
None observed in the current repository state.

The final verification command was run successfully:
- `python3 -m pytest -q`
- Result: `214 passed in 0.04s`
