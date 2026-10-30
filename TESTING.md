# TESTING.md

## Test command and environment
Python version: [Add the version shown by running python --version] (CI uses Python 3.11).

Test command: python -m pytest -q

Initial results: Before making any changes, the starter code had 67 failed tests and 147 passed tests.

Final results: After applying the fixes, all 242 tests passed successfully. This includes 214 original tests and 28 additional regression tests in tests/test_regressions.py.


## Edge-case evidence
Here is the same information in paragraph form, ready to paste into your approach.md file.

I tested the main issues using different inputs and compared the results with the expected behaviour.

First, I checked the points calculation using calculate_points(19999, 1). It correctly returned 1 point using floor division, whereas the starter code returned 2 because of rounding. This was verified through test_points_use_floor and test_floor_not_round_just_below_boundary.

I also tested the zero-point cap using calculate_points(50000, 1, cap_points=0). The function correctly returned 0 instead of 5, which was the result from the original code. The tests test_cap_zero_is_respected and test_cap_zero_and_cap_none_are_different verified this behaviour.

For duplicate events, I applied the same purchase event (E1) twice. The balance remained 2, the event ID appeared only once in processed_event_ids, and only one ledger entry was created. This confirmed that duplicate purchase events are not processed again. I verified this using test_purchase_event_replay_is_idempotent.

I tested refund validation by trying to refund 150000 paise on a purchase of 100000 paise. The refund was correctly rejected, and the account balance remained 10 instead of becoming -5, as it did in the starter code. I also tried invalid refund values such as True, "100", 1.5, [], and None. All were safely rejected without changing the account or causing errors. These cases were covered by test_invalid_or_excess_refund_ignored and test_invalid_or_excess_refund_does_not_change_account.

To check partial refunds, I used a purchase of 30000 paise that awarded 3 points and then applied two refunds of 15000 paise each. The cumulative calculation correctly reversed all 3 points and brought the balance to 0 without any rounding errors. This was verified using test_cumulative_reversal_has_no_rounding_drift.

I also checked how the system handles events with a missing event_id or transaction_id. Such events were safely ignored without changing the account balance, ledger, or processed event IDs. The test test_missing_identifiers_are_ignored confirmed this.

For repeat transaction alerts, I tested thresholds of 0 and -1, along with empty and None inputs. The function handled these cases without crashing, treated invalid thresholds as 1, and returned an empty list when there were no valid records. These behaviours were checked using test_repeat_alert_threshold_input_is_handled and test_repeat_alerts_empty_and_malformed_input.

Finally, I replayed all 264 events from data/records.json to check whether the account remained consistent throughout the process. The balance never went below zero, the ledger total matched the account balance, and the reversed points never exceeded the awarded points. All these conditions passed in test_dataset_event_replay_keeps_invariants.

## Regression tests added
I added tests/test_regressions.py with 28 additional tests covering floor rounding, zero versus no points cap, invalid input types (including booleans), duplicate events, missing IDs, and refund validation. The tests also check multiple partial refunds, excessive and full refunds, cumulative rounding accuracy, non-negative balances, and ledger entries. Additionally, I tested dataset replay consistency, malformed repeat-alert inputs, duplicate transactions within repeat groups, and deterministic repeat alerts across all 60 groups.

## Remaining failures or limitations
All tests are passing. The only scenario I haven’t tested yet is whether refunds are handled correctly if the reward rules change between the original purchase and the refund.