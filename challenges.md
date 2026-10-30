# challenges.md — COMPULSORY submission

## 1. Challenge or confusing behaviour

The most challenging part of the project was understanding how points should be calculated and how purchase and refund events should affect an account balance.

The initial implementation had problems with rounding, zero-point caps, duplicate event processing, and invalid or excessive refunds.

Understanding how to prevent the same event from changing the balance more than once was particularly important.

## 2. Evidence

The initial test run showed:

- 147 tests passed.
- 67 tests failed.

Some failures involved:
- Incorrect points near ₹100 boundaries.
- A cap value of zero not being applied correctly.
- Replayed purchase events being processed more than once.
- Invalid and excessive refund amounts being accepted.

The demo command also ran successfully and displayed:

`Points example: 28`

## 3. What I tried

I performed the following debugging steps:

1. Ran `python -m pytest -q` to identify the failing tests.
2. Inspected `service.py` to understand the points calculation and event-processing logic.
3. Compared the implementation with the expected results in the tests.
4. Changed the points calculation to use integer floor division instead of rounding.
5. Corrected the cap condition to check whether the cap is `None`, allowing a cap of zero.
6. Added duplicate event ID protection.
7. Added validation for purchase amounts, transaction identifiers, and refund amounts.
8. Checked the refund calculation and repeat-transaction grouping against the tests.

## 4. Resolution

The main root causes were incorrect rounding, incorrect handling of a zero cap, and insufficient validation of reward events.

I corrected the points calculation using integer arithmetic, applied the cap after the bonus, and added checks to prevent duplicate events and invalid refunds from changing account balances.

These changes address the underlying business-rule problems rather than hiding failing tests.

## 5. Proof and regression prevention

The latest test run was:

`python -m pytest -q`

Actual result:

`214 passed, 0 failed`

Relevant tests include:

- `test_points_use_floor`
- `test_cap_zero_is_respected`
- `test_purchase_event_once`
- `test_partial_refund_reverses_proportionally`
- `test_invalid_or_excess_refund_ignored`
- `test_unknown_refund_safe`
- `test_repeat_group`

These tests verify the expected behaviour for the corrected cases.

## 6. Unresolved challenge or next step

The available test suite passes, but additional testing of malformed reward-rule configurations and unusual input types would improve robustness.

My next step is to add further independent regression tests, review the documentation, and verify the final changes before creating the GitHub pull request.