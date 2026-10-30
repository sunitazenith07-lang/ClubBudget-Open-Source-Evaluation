# TESTING.md — Required submission


## Test command and environment
Python version: Python 3.14

Command run: pytest -v

Actual test summary: Tests executed; results documented below.


## Edge-case evidence



Case / input

Expected behaviour

Actual result

Test name or evidence

1

Partial refund

Calculate correct refund

Verified

Partial refund test

2

Excess refund

Reject excess refund

Verified

Excess refund test

3

Zero refund

Handle safely

Verified

Zero refund test

4

Negative refund

Reject invalid amount

Verified

Negative refund test

5

Refund exceeding balance

Prevent negative balance

Verified

Balance protection test

## Regression tests added
Added tests for partial and excess refunds.

Added tests for invalid refund amounts.

Added tests to prevent negative account balances.

## Remaining failures or limitations
No known limitations reported.