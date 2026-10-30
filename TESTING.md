TESTING.md - Required submission

I am a first-year student who recently finished learning the basics of Python. Below is what I tested after making the changes and how I checked the important edge cases.

Test command and environment

Python version: Python 3.11.2

Command used: python -m pytest -q

The final result was 205 passed. This includes 12 original contract tests, 4 new regression tests in tests/test_contract.py, and 189 parameterized test cases across 11 test functions in tests/test_acceptance_matrix.py.

Before I fixed service.py, the test result was 92 failed and 109 passed.

Edge-case testing

1. Points calculation with 19999 paise

Input: calculate_points(19999, 1)

The expected result was 1 point because 19999 // 10000 gives 1. It should not round the value up to 2.

Actual result: 1 point.

Tested with test_points_use_floor and test_integer_floor_points_calculation.

2. Points calculation with cap_points set to 0

Input: calculate_points(50000, 1, cap_points=0)

The expected result was 0 because a cap of 0 should still be treated as a valid cap.

Actual result: 0 points.

Tested with test_cap_zero_is_respected and test_bonus_and_cap_matrix.

3. Duplicate purchase and refund events

I tested what happens when the same purchase_captured or refund_processed event is sent again with an event_id that was already processed.

The expected behaviour was that the second event should be ignored. The points balance, processed event IDs, and ledger should not be changed again.

The actual result was correct. The balance stayed the same, each event ID appeared only once, and only one ledger entry was created for each unique event.

Tested with test_purchase_event_once, test_purchase_event_replay_is_idempotent, and test_refund_event_replay_is_idempotent.

4. Invalid and excess refunds

I tested refunds with values such as -1, 150000 on a 100000 paise purchase, True, None, and "100".

These values should be ignored because they are invalid or larger than the original purchase amount.

The actual result was that refunded_paise stayed at 0 and the points balance stayed at 10.

Tested with test_invalid_or_excess_refund_ignored and test_invalid_or_excess_refund_does_not_change_account.

5. Multiple partial refunds

I tested two partial refunds on a 50000 paise purchase where 10 points had originally been awarded.

The first refund was 20000 paise, which should remove 4 points. The second refund was 30000 paise, which should remove the remaining 6 points.

The actual result was correct. After the first refund the balance became 6, and after the second refund it became 0. Any further refund that would go over the original purchase amount was ignored.

Tested with test_multiple_partial_refunds_cumulative_reversal and test_cumulative_refund_exceeding_purchase_ignored.

6. Repeat transaction checking

I also tested repeat transactions with different accounts and with invalid values such as None, 0, and -1.

The expected behaviour was to group only valid transactions that have the same account_id, date, and amount_paise. An alert should only be created when the number of matching transactions is greater than the threshold.

The actual result was correct. Different accounts were not grouped together, invalid rows were ignored, and a group was returned only when its count went above the threshold.

Tested with test_different_accounts_not_grouped, test_repeat_alert_threshold_boundaries, and test_repeat_alerts_do_not_mix_distinct_keys.

Regression tests added

test_multiple_partial_refunds_cumulative_reversal

This checks that two partial refunds of 20000 paise and 30000 paise on a 50000 paise purchase remove the correct number of points and create the correct ledger entries.

test_refund_event_replay_is_idempotent

This checks that sending the same refund event again does not remove the points a second time.

test_cumulative_refund_exceeding_purchase_ignored

This checks that a second refund of 50000 paise is rejected when 60000 paise has already been refunded from a 100000 paise purchase, because the total would become more than the original purchase amount.

test_missing_identifiers_and_empty_inputs_handled_safely

This checks that events with an empty event_id or transaction_id and empty transaction lists are handled without causing errors.

Remaining failures or limitations

There are currently 0 failing tests, with 205 tests passing.

The account data is stored in normal Python dictionaries in memory instead of a database. Because of this, handling simultaneous updates from multiple processes is outside the scope of this project.