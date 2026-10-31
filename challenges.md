# challenges.md - COMPULSORY submission

This file is mandatory and worth 5 marks. Describe your actual experience honestly. Do not invent difficulties to fill the page.

## 1. Challenge or confusing behaviour
The main challenge was handling partial and excess refunds while ensuring that the account balance never became negative. The starter code did not properly validate refund amounts, which allowed invalid refunds to affect transactions and points.


## 2. Evidence
The failure was directly reproducible across both unit tests and parameterized matrix tests:

test_invalid_or_excess_refund_ignored failed because an excessive refund reduced the balance below zero.

Negative refund amounts could incorrectly increase points.

Boolean values like True were accepted as integers.

Invalid inputs such as strings, floats, None, lists, and dictionaries were not rejected.

## 3. What I tried
During investigation and debugging, I tested three approaches:

Used max(0, points) to prevent a negative balance, but invalid transaction data could still be updated.

Checked refunds against the purchase amount, but this did not handle multiple partial refunds correctly.

Used isinstance(refund, int), but it also accepted Boolean values.


## 4. Resolution
I added validation in apply_reward_event in service.py:

if type(refund) is not int or refund <= 0 or txn['refunded_paise'] + refund > txn['amount_paise']:
    return out

This rejects invalid, negative, zero, Boolean, and excessive refunds before changing the transaction or account balance.

## 5. Proof and regression prevention
The relevant refund tests passed, including partial refund and invalid refund cases.

The complete test suite passed: 214 passed in 0.18s.


-
## 6. Unresolved challenge or next step
The current implementation does not handle simultaneous refund requests using database locking. A future improvement would be to add database transactions, row-level locking, and warning logs for rejected refunds.

