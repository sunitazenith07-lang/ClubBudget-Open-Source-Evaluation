# challenges.md

This was a practice run completed with AI assistance.

## 1. Challenge or confusing behaviour
The main challenge was deciding how to handle invalid or excessive refunds and how to calculate point reversals across multiple partial refunds without causing rounding errors.

## 2. Evidence
In test_invalid_or_excess_refund_does_not_change_account[150000], the expected result was that the refunded amount should remain 0 and the balance should stay at 10. However, the starter code accepted the excessive refund and reduced the balance to -5 instead of rejecting it.

In test_invalid_or_excess_refund_does_not_change_account[True], Python treated True as an integer, so the code incorrectly accepted it as 1 paise.

Other invalid inputs, such as "100" and [], caused a TypeError when the code tried to add them to the existing refund amount.

## 3. What I tried
I went through the failing test cases one by one and tried to reproduce the same issues in the Python shell using the original code. For example, a refund of 150000 paise on a 100000-paise purchase reduced the balance to -5, while using True as a refund amount incorrectly counted it as 1 paise.

I considered two ways to handle refunds that exceed the original purchase amount: either limit the refund to the remaining amount or reject the entire event. Since the tests expected refunded_paise to remain 0 and the balance to stay unchanged, I went with rejecting the whole event.

While checking input validation, I found that isinstance(True, int) returns True in Python. This meant a normal integer check would still accept boolean values. I handled this by explicitly checking that the value is not a boolean.

I also tested how point reversals work when a purchase is refunded in multiple parts. For a 30000-paise purchase that earned 3 points, two refunds of 15000 paise each would reverse only 2 points if calculated separately. Using the cumulative refund formula fixes this issue and ensures all 3 points are reversed after a full refund. I verified the result in the Python shell after making the changes, where the final balance correctly became 0.

## 4. Resolution
The main problem was that the refund section had no proper input validation, and the code did not check whether an event had already been processed. I fixed this by accepting refunds only when the amount is a positive integer, the transaction exists, the event ID has not been used before, and the total refunded amount does not exceed the original purchase amount. I also changed the reversal calculation to use the cumulative refunded amount and made sure it never reduces the account balance below zero.

## 5. Proof and regression prevention
I added tests covering several important refund scenarios, including multiple partial refunds followed by an excessive refund, avoiding rounding errors during cumulative reversals, preventing duplicate refund events from being applied twice, and ensuring the account balance never becomes negative even when points have already been spent.

I also added a dataset replay test that processes all 264 events and checks important conditions, such as the balance never going below zero, the ledger total matching the account balance, reversed points never exceeding awarded points, and the total refunded amount never exceeding the original purchase amount.

## 6. Unresolved / next step
The reward rules could change between the time of purchase and the time of refund. I used the originally stored awarded_points to calculate the reversal, as this seems like the correct approach. However, I haven’t added a separate test to verify this scenario.

The dataset does not contain any category information, so generating a category-wise summary was not possible.