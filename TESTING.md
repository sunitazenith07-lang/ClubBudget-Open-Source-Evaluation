# TESTING.md

## Test command and environment

- **Python version:** Python 3.14.7
- **Command run:** `python -m pytest -q`
- **Actual test summary:** 218 passed, 0 failed.

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Purchase amount of 19999 paise | Award 1 point using floor division | Passed | `test_points_use_floor` |
| 2 | Cap value of 0 | Award zero points | Passed | `test_cap_zero_is_respected` |
| 3 | Replaying the same purchase event ID | Process the event only once | Passed | `test_purchase_event_once` |
| 4 | Partial refund of 50000 paise against a 100000 paise purchase | Reverse points proportionally | Passed | `test_partial_refund_reverses_proportionally` |
| 5 | Negative or excessive refund amount | Ignore the refund without changing the balance | Passed | `test_invalid_or_excess_refund_ignored` |
| 6 | Refund for an unknown transaction | Do not change the account balance | Passed | `test_unknown_refund_safe` |
| 7 | Three transactions with the same account, date and amount, threshold 2 | Flag the possible repeat group | Passed | `test_repeat_group` |
| 8 | Transactions belonging to different accounts | Do not group them together | Passed | `test_different_accounts_not_grouped` |

## Regression tests added

The following existing regression tests were run to verify the fixes:

- Corrected points calculation to use integer floor division instead of rounding.
- Corrected zero-cap handling so `cap_points=0` is respected.
- Added duplicate event-ID protection to prevent replayed events from being processed twice.
- Added refund validation to reject invalid and excessive refund amounts.
- Added purchase validation for invalid amounts and missing transaction identifiers.
- Verified proportional refund reversal and repeat-transaction grouping.
- `test_duplicate_refund_event_is_ignored`
- `test_purchase_with_blank_transaction_id_is_ignored`
- `test_purchase_with_boolean_amount_is_ignored`
- `test_invalid_repeat_threshold_returns_no_alerts`

The existing test suite was used to verify these changes. No new test functions are claimed as added.

## Remaining failures or limitations

- The complete available test suite currently passes: 218 passed, 0 failed, 0 failed.
- Additional validation of malformed reward-rule configurations and unusual input types may be useful.
- Passing the available tests does not guarantee that every possible production input has been covered.
