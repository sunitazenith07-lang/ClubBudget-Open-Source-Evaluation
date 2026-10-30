# Challenges and Debugging

## 1. Challenge or confusing behaviour

The most challenging parts of the implementation were handling invalid reward inputs, ensuring event identifiers were valid, preventing refunds from making balances negative, and handling malformed repeat-transaction records.

One particularly useful edge case was a refund against an account with zero available points, even though the original transaction had awarded points. Another was repeat detection when transaction records had missing fields or were not dictionaries.

## 2. Evidence

I added regression tests in `tests/test_contract.py` to reproduce these cases.

- Invalid calculation inputs initially caused contract test failures.
- Missing, empty, numeric, and boolean event or transaction identifiers initially failed their regression tests.
- A refund test initially produced a balance of `-1` when the available balance was zero.
- Missing fields in repeat-transaction records could produce a false alert.
- A non-dictionary record such as `None` caused an `AttributeError`.

These failures helped identify specific gaps in input validation and event processing.

## 3. What I tried

I used the following debugging steps:

1. Ran the original test suite to understand the baseline: 67 failed and 147 passed.
2. Added parametrized tests for invalid amounts, reward multipliers, bonus percentages, and caps.
3. Tested missing, empty, numeric, and boolean event IDs and transaction IDs.
4. Created a refund test with one awarded point and a zero account balance. The test exposed a negative balance of `-1`.
5. Tested repeat detection with missing fields and non-dictionary records.
6. Re-ran the focused contract tests and then the complete test suite after making the fixes.

## 4. Resolution

I addressed the issues at the relevant validation and calculation points:

- Added strict integer validation in `calculate_points()` so invalid inputs return zero.
- Added event ID and transaction ID validation before processing events.
- Added duplicate-event protection using `processed_event_ids`.
- Added refund validation and limited deductions to the available account balance.
- Added validation in `flag_repeat_transactions()` to ignore malformed records before grouping them.

These changes address the causes of the failures instead of simply changing or skipping the failing tests.

## 5. Proof and regression prevention

The regression tests in `tests/test_contract.py` cover the identified issues.

**Final verification results:**

- Contract tests: `45 passed`
- Full test suite: `247 passed in 0.93s`
- `git diff --check`: no errors reported.

The tests also cover related edge cases such as zero caps, empty repeat-alert input, a single transaction, and invalid refund amounts.

A related case that may need further attention is a refund when the account has already spent some of its awarded points.

## 6. Unresolved challenge or next step

The current refund implementation prevents the account balance from becoming negative. However, the specification does not define what should happen when a customer has already spent points that need to be reversed after a refund.

The current implementation limits the deduction to the available balance. It does not track the remaining reversal as a pending deduction.

As a next step, I would clarify the expected business rule with the project mentor and, if required, introduce a deferred-reversal mechanism with dedicated tests for partial refunds, multiple refunds, and insufficient point balances.