# challenges.md

1. Challenge
When reading the brief, there were two areas that I considered challenging.
1. Over refunding: "Never give more back than was given" led me to believe that if there was an over-refund then you can only refund what is left.
2. Threshold: I took threshold 2 to mean 2 or more so the '>' in the starter code seemed like an off-by-one error.

2. Evidence
The test `test_refund_amount_bounds_and_balance` would expect a refund amount higher than 100000 when the purchase was 100000 to have a refunded_paise of 0 and a points_balance of 10. This means we have rejected the whole refund.
The test `test_repeat_alert_threshold_boundaries` would expect threshold amount of rows to give [], and threshold+1 rows to give one alert. As such the '>' was correct.
The demo correctly gives a repeat warning of [] for TX-1/TX-2 as there are 2 rows and the threshold is 2.

3. Attempt
I decided to look at the values in the parameterised tests.
I grouped similar failing tests by their names. None of the repeat alerts were failing, so the function was mostly correct.
Looking at the True refund, in Python isinstance(True, int) will return True. So if we do a basic check for int it will pass as True is 1 paise.

4. Solution
If the refund is not a positive integer, or refunded_paise + refund > amount_paise then return the account as it is.
Threshold is kept as '>'
I added a function `_is_int()` which excludes a boolean. All numbers are checked using this function.

5. Proof & Regression Prevention
Passed tests: `test_refund_amount_bounds_and_balance`, `test_invalid_or_excess_refund_does_not_change_account`, `test_repeat_alert_threshold_boundaries`.
New tests: `test_multiple_partial_refunds_never_reverse_more_than_awarded`, `test_bool_amount_is_not_treated_as_int`.
Could still be broken if the business decide to cap over refunds. The code and these tests would need to be updated.
6. To Do

If there is a refund for an unknown transaction then it is ignored however it will still be marked as processed. If the purchase comes through later then there will be no effect when the refund is replayed. Next I would want to ensure they are not marked as processed. Test this with out of order events in data/records.json.