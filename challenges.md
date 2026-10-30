# challenges.md

## 1. Challenge or confusing behaviour

The most challenging part was understanding how partial refunds should affect reward points.

For example, if a customer makes a purchase of ₹100 and earns 10 points, a refund of ₹50 should reverse 5 points. I had to understand how this calculation should work when multiple partial refunds are processed.

I also found duplicate event handling and refund validation important because processing the same event more than once could incorrectly change the points balance.

## 2. Evidence

The initial test run showed:

`67 failed, 147 passed in 1.30s`

While inspecting the starter implementation, I found a few issues:

- `round()` was being used for reward calculation instead of calculating points for complete ₹100 units.
- A zero-point cap was ignored because the code used `if cap_points`.
- Duplicate event IDs were not checked before processing.
- Refund amounts were added without properly checking whether the total refund exceeded the original purchase amount.

These cases showed that the problems were not limited to the reward formula. Event validation and transaction consistency also needed attention.

## 3. What I tried

- Inspected `calculate_points()` to understand how the base reward, bonus, and cap were calculated.
- Traced `apply_reward_event()` to understand how purchases and refunds changed the account balance and ledger.
- Checked `flag_repeat_transactions()` to understand how transactions were grouped for repeat alerts.
- Replaced floating-point rounding with integer floor division to make reward calculations predictable.
- Added validation for non-negative integer values and checked how zero caps were handled.
- Added regression tests for negative amounts, duplicate events, excessive refunds, unknown transactions, partial refunds, zero caps, and empty repeat transaction input.
- Ran the test suite again after making the changes.

## 4. Resolution

The main causes were incorrect rounding, incomplete input validation, and missing event and refund checks.

I changed the reward calculation to use integer arithmetic:

- Base points are calculated using `amount_paise // 10000`.
- Bonus points are calculated using integer division.
- The reward cap is applied after the bonus calculation.
- A zero cap is now handled correctly using `cap_points is not None`.

For event processing, I added duplicate event ID checks and validation before accepting purchases or refunds.

For refunds, I used cumulative refunded amounts to calculate the proportional points reversal. This makes multiple partial refunds work against the original purchase instead of treating each refund independently.

These changes address the underlying calculation and validation problems rather than simply changing the expected test results.

## 5. Proof and regression prevention

I added seven tests in `tests/test_regressions.py`:

1. `test_negative_amount`
2. `test_zero_cap`
3. `test_duplicate_event`
4. `test_refund_greater_than_purchase`
5. `test_unknown_transaction_refund`
6. `test_partial_refund`
7. `test_empty_repeat_transactions`

After the changes, the final test result was:

`221 passed in 0.46s`

These tests help prevent the identified issues from returning during future changes.

A related case that still needs more attention is a refund when the customer has already spent some of their earned points.

## 6. Unresolved challenge or next step

The main unresolved question is how to handle refunds when the customer's available points balance is lower than the points that need to be reversed.

Currently, the implementation limits the reversal to the available balance. However, the exact business behaviour for this situation needs to be defined.

My next step would be to clarify the expected business rule and test different cases, such as a full refund after spending points and multiple partial refunds after spending some of the balance.

This would help ensure that the transaction record, ledger, and account balance remain consistent in all situations.