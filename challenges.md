challenges.md - COMPULSORY submission

I am a first-year student who recently finished learning the basics of Python. While working on this project, I faced a few technical issues that were confusing at first. The main challenges were related to Python's handling of boolean values and understanding the threshold logic for repeat transactions.

1. Challenge or confusing behaviour

Two things were tricky at first:

1. In apply_reward_event, invalid refund amounts were not always being rejected. In particular, passing True as the refund amount was getting through a simple isinstance(refund, int) check.

2. In flag_repeat_transactions, I initially misunderstood the threshold condition. Tests such as test_different_accounts_not_grouped and test_repeat_alert_threshold_boundaries were failing even though I was grouping transactions using (account_id, date, amount_paise).

2. Evidence

In test_invalid_or_excess_refund_does_not_change_account[True], the refund value was True. Python considers bool as a subclass of int, so isinstance(True, int) returns True. Also, True > 0 is True. Because of this, True was treated like the integer 1 and changed refunded_paise from 0 to 1. This caused the assertion to fail.

For the repeat transaction issue, test_repeat_alert_threshold_boundaries helped me understand the expected behaviour. The test creates exactly threshold matching transactions and expects no alert. Then it adds one more transaction and expects an alert. The starter code used len(ids) >= threshold, so it created an alert when the count was exactly equal to the threshold.

3. What I tried

First, I tested Python's behaviour directly by checking isinstance(True, int) in the terminal. It returned True, which explained why my original validation was not enough.

I then checked the related tests in tests/test_contract.py and tests/test_acceptance_matrix.py.

The important cases were:

- test_different_accounts_not_grouped has one transaction for account A and one for account B, uses threshold=1, and expects no alert.
- test_repeat_alert_respects_threshold checks that an alert only happens when the count is greater than the threshold.
- test_repeat_alerts_do_not_mix_distinct_keys checks that transactions are only grouped when account_id, date, and amount_paise all match.

4. Resolution

For the boolean problem, I created a helper function called is_valid_int(value). It checks:

isinstance(value, int) and not isinstance(value, bool)

I used this helper in calculate_points, apply_reward_event, and flag_repeat_transactions so that True and False are not treated as valid integer inputs.

For flag_repeat_transactions, I changed the condition from len(ids) >= threshold to len(ids) > threshold. I also added validation to ignore transactions when account_id, date, or transaction_id is missing, or when amount_paise is not a positive integer. I also made the function return [] when threshold is less than 1.

5. Proof and regression prevention

All 15 invalid refund cases in test_invalid_or_excess_refund_does_not_change_account now pass. This includes values such as True, False, None, "100", 1.5, [], and {}.

The repeat transaction tests also pass, including:

- test_repeat_group
- test_different_accounts_not_grouped
- test_repeat_alert_respects_threshold
- test_repeat_alert_threshold_boundaries
- test_repeat_alerts_do_not_mix_distinct_keys
- test_repeat_alert_threshold_input_is_handled

I also added test_cumulative_refund_exceeding_purchase_ignored and test_multiple_partial_refunds_cumulative_reversal in tests/test_contract.py. These tests help make sure that multiple refunds cannot reverse more points than the original purchase awarded.

6. Unresolved challenge or next step

One thing I would improve in the future is handling two purchase_captured events that have different event_id values but reuse the same transaction_id. Currently, the second event is ignored so the existing transaction record is not overwritten. If I had more time, I would add a warning or flag for this situation so it can be reviewed instead of being silently ignored.