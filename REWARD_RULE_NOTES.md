REWARD_RULE_NOTES.md - Required submission

I am a first-year student who recently finished learning the basics of Python. These are my worked examples and notes showing how I understood the reward points and refund calculations in the project.

1. Worked points calculation

Suppose a customer makes a purchase with these values:

- amount_paise: 55000, which is ₹550
- points_per_100_rupees: 2
- bonus_percent: 25
- cap_points: 20

The calculation in calculate_points(55000, 2, 25, 20) works like this:

1. Base points

The amount is divided into complete ₹100 blocks using integer floor division.

(55000 // 10000) * 2 = 5 * 2 = 10

So the base points are 10.

2. Bonus points

The 25% bonus is applied before the cap.

(10 * (100 + 25)) // 100 = (10 * 125) // 100 = 1250 // 100 = 12

So the result after the bonus is 12 points.

3. Applying the cap

The cap is 20, so the final value is the smaller of 12 and 20.

min(12, 20) = 12

4. Final result

calculate_points(55000, 2, 25, 20) returns 12.

I also checked another example from main.py:

Input: calculate_points(259900, 1, 10, 100)

Base points:

(259900 // 10000) * 1 = 25

After the 10% bonus:

(25 * 110) // 100 = 2750 // 100 = 27

The cap is 100, so the final result stays 27.

The actual output is 27. The original code returned 28 because it used round(259900 / 10000), which rounded 25.99 up to 26 before calculating the points.

2. Partial refund example

Suppose account A has a purchase T1 worth ₹500, which is 50000 paise, and the rule gives 2 points for every ₹100.

1. Original purchase

The purchase gives:

(50000 // 10000) * 2 = 10 points

So the account has 10 points.

The transaction is stored with:

amount_paise: 50000
awarded_points: 10
reversed_points: 0
refunded_paise: 0

The purchase also creates a ledger entry with event_id E1, type purchase_captured, and points_delta 10.

2. First partial refund

Now suppose event E2 refunds 20000 paise, which is ₹200.

The total refunded amount becomes:

0 + 20000 = 20000

The number of points that should have been reversed is:

(10 * 20000) // 50000 = 4

Since no points had been reversed before, the current refund removes 4 points.

So the points balance changes from 10 to 6.

The transaction now has:

amount_paise: 50000
awarded_points: 10
reversed_points: 4
refunded_paise: 20000

The refund also creates a ledger entry with event_id E2, type refund_processed, and points_delta -4.

3. Three edge cases

1. Zero reward cap

Input:

calculate_points(50000, 1, bonus_percent=0, cap_points=0)

A cap of 0 means that no points can be awarded, so the expected result is 0.

The original code had a problem because if cap_points: treats 0 as False and therefore skipped the cap. That caused it to return 5 instead.

After the fix, the actual result is 0.

This is checked by test_cap_zero_is_respected in tests/test_contract.py and test_bonus_and_cap_matrix in tests/test_acceptance_matrix.py.

2. Duplicate event replay

I tested calling apply_reward_event twice with the same event:

event_id: E1
type: purchase_captured
transaction_id: T1
amount_paise: 25000

The rules give 1 point for every ₹100.

The first call gives 2 points and stores E1 in processed_event_ids.

When the same event is sent again, the function sees that E1 was already processed and ignores it.

The actual result is:

points_balance == 2
processed_event_ids == ['E1']
len(ledger) == 1

This is checked by test_purchase_event_once in tests/test_contract.py and test_purchase_event_replay_is_idempotent in tests/test_acceptance_matrix.py.

3. Excess or invalid refund

I tested a purchase of 100000 paise that gave 10 points, followed by an invalid refund.

For example:

amount_paise = 150000

I also checked values such as -1, None, True, and "100".

These refunds should be ignored because they are invalid or would make the total refunded amount larger than the original purchase.

The actual result was:

refunded_paise == 0
points_balance == 10

This is checked by test_invalid_or_excess_refund_ignored in tests/test_contract.py and test_invalid_or_excess_refund_does_not_change_account in tests/test_acceptance_matrix.py.

4. Assumptions and limitations

For the points calculation and refund calculation, I used integer floor division with //. This avoids using floating-point calculations or round(), which was causing the original points calculation problem.

I also made sure that True and False are not accepted as amounts. In Python, bool is a subclass of int, so simply checking isinstance(value, int) would also accept True and False. The code therefore checks both the type and whether the value is a bool.

For missing or invalid information, such as a missing event_id, transaction_id, account_id, or date, the function should ignore the invalid record instead of crashing or changing the original account data.

For repeat transaction alerts, valid positive transactions are grouped using account_id, date, and amount_paise. An alert is created only when the number of matching transactions is greater than the threshold.

With the default threshold of 2, at least 3 matching transactions are needed before an alert is created.